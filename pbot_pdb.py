import sys
import os
import socket
import traceback
import datetime
import shutil
import pdb


# --------------------------- Internals ---------------------------------------

# Colors - https://gist.github.com/JBlond/2fea43a3049b38287e5e9cefc87b2124
CURRENT_LINE_COLOR = 93 # yellow
EXCEPTION_LINE_COLOR = 92 # green
STACK_LOCATION_COLOR = 96 # cyan
PROMPT_COLOR = 95 # magenta
ERROR_COLOR = 91 # red

# Options for making bin readable.
XLAT_TBL = { 0:'NUL', 10:'LF', 13:'CR', 9:'TAB', 27:'ESC' }
LEFT_DELIM = '<'
RIGHT_DELIM = '>'

HOST = '127.0.0.1'
TERM = os.linesep # '\n'

# Logging
LOG_FN = None
LOG_NAME = 'PPDB'
LOG_SIZE = 50000
LOG_OVERWRITE = True # else append
def error(message, tb=None, readable=False): _write_log('ERR', message, tb=tb, readable=readable)
def debug(message, readable=False): _write_log('DBG', message, readable=readable)


#------------------------------------------------------------------------------
class PbotPdb(pdb.Pdb):
    '''Custom pdb using TCP.'''

    # --------------- Construction ---------------
    def __init__(self, port, log_fn=None, use_color=True):
        '''
            - port number - req
            - log file name or None if not used
            - optionally colorize pdb output
        '''
        global LOG_FN
        LOG_FN = log_fn

        self.port = port
        self.use_color = use_color
        self.valid = False

        self.sock = None
        self.conn = None
        self.commif = None

        # Maybe roll over log now.
        if LOG_FN and os.path.exists(LOG_FN) and os.path.getsize(LOG_FN) > LOG_SIZE:
            bup = LOG_FN.replace('.log', '_old.log')
            shutil.copyfile(LOG_FN, bup)
            # Clear current log file.
            with open(LOG_FN, 'w'):
                pass

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.sock.settimeout(5)  # Seconds.
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            self.sock.bind((HOST, self.port))
            debug(f'Server started on {HOST}:{self.port} - waiting for connection.')

            # Try to connect. conn is a new socket for R/W.
            self.sock.listen(1)
            self.conn, address = self.sock.accept()

            # Connected.
            chost, cport = address
            debug(f'Server accepted connection from {chost}:{cport}')

            self.commif = CommIf(self.conn, self.use_color)
            # Init base.
            super().__init__(stdin=self.commif, stdout=self.commif, skip=['unittest.*', 'pbot_pdb.py'])  # pyright: ignore
            # 3.14+ Pdb can syntax color code - see the docs.
            self.valid = True

        except Exception as e:
            # Any errors are considered fatal.
            error(f'Init failed [{e}]', e.__traceback__)
            self._cleanup()

    # --------------- Custom user cmds ---------------
    def do_quit(self, arg=None):
        ''' Stopping debugging, clean up resources, exit application. '''
        debug('Server quitting.')
        self._cleanup()

        try:
            return super().do_quit(arg)
        except Exception as e:
            error(f'do_quit() failed [{e}]', e.__traceback__)
    do_q = do_quit # alias

    # --------------- Go! ---------------------
    def _set_bp(self, frame):
        ''' Starts the debugger.'''
        debug('breakpoint() entry')
        if not self.valid:
            raise RuntimeError('Breakpoint hit without ppdb initialization')

        # Run pdb. This blocks until pdb says done.
        # Note that exceptions in the code under test go to sys.excepthook so try/except is pointless.
        super().set_trace(frame)

    # ----------------------------------
    def _cleanup(self):
        ''' Clean up resources. '''
        debug('_cleanup()')

        if self.commif is not None:
            self.commif.close()
            self.commif = None

        if self.sock is not None:
            self.sock.close()
            self.sock = None

        if self.conn is not None:
            self.conn.close()
            self.conn = None

# --------------------------- Socket I/F --------------------------------------
class CommIf(object):
    '''
    Pdb flavored read/write interface to socket. Makes socket look like a file object.
    Also handles encoding, color, line endings etc.
    Catches exceptions for the purpose of logging only. They are re-raised.
    '''

    def __init__(self, conn, use_color):
        self.conn = conn
        self.use_color = use_color
        # pdb writes lines piecemeal but we want full proper lines.
        # Easiest is to accumulate in a buffer until we see the prompt then slice and write.
        self.write_buff = ''

        # Return a file object associated with the socket -> https://docs.python.org/3/library/io.html#io.TextIOWrapper
        self.stream = self.conn.makefile('rw')

    def __iter__(self):
        return self.stream.__iter__()

    def _send(self, msg):
        debug(f'CommIf _send [{msg}]', readable=True)
        self.conn.sendall(msg.encode())

    # --------------- Required interface ---------------
    #   -> https://docs.python.org/3/library/io.html#io.TextIOBase
    # Min: readline()  write()  flush()

    @property
    def encoding(self):
        return self.stream.encoding

    def readline(self, size=1):
        ''' Required. Core pdb calls this to read from user/client. Captures the last user command.'''
        del size

        try:
            msg = self.stream.readline() # blocks, throws if timeout
            # TODO first command has extra junk in msg but not on the wire. Tried everything, it's a mystery.
            # -> [<0xC3><0xBF><0xC3><0xBB><0x1F><0xC3><0xBF><0xC3><0xBB> <0xC3><0xBF><0xC3><0xBB><0x18><0xC3><0xBF><0xC3><0xBB>'<0xC3><0xBF><0xC3><0xBD><0x01><0xC3><0xBF><0xC3><0xBB><0x03><0xC3><0xBF><0xC3><0xBD><0x03>l<LF>]
            # TODO Handle ansi codes for e.g. up/down/history -> <ESC>[A<LF>
            return msg

        except (ConnectionError, socket.timeout) as e:
            ''' These can happen, ignore. '''
            debug(f'read() Disconnected [{type(e)}]')
            return ''

        except Exception as e:
            ''' Unexpected error, shut dowwn. '''
            error(f'read() Other exception [{str(e)}]', e.__traceback__)
            raise

    def write(self, line):
        ''' Required. Core pdb calls this to write to user/client. This adjusts and sends to socket. '''
        try:
            if '(Pdb)' in line:
                for s in self.write_buff.splitlines():
                    color = None

                    if self.use_color:
                        if s.startswith('-> '): color = CURRENT_LINE_COLOR
                        elif ' ->' in s: color = CURRENT_LINE_COLOR
                        elif s.startswith('>> '): color = EXCEPTION_LINE_COLOR
                        elif '***' in s: color = ERROR_COLOR
                        elif 'Error:' in s: color = ERROR_COLOR
                        elif s.startswith('> '): color = STACK_LOCATION_COLOR
                    self._send(f'{s}{TERM}' if color is None else f'\033[{color}m{s}\033[0m{TERM}')

                # Write prompt.
                self._send(f'\033[{PROMPT_COLOR}m(Pdb)\033[0m' if self.use_color else f'(Pdb)')

                # Reset buffer.
                self.write_buff = ''
            else:
                # Just collect.
                self.write_buff += line

        except (ConnectionError, socket.timeout) as e:
            '''These can happen, go back to default state.'''
            debug(f'write() Disconnected [{type(e)}]')
            self.write_buff = ''

        except Exception as e:
            '''Unexpected error, shut dowwn.'''
            error(f'write() Unexpected exception [{type(e)}]', e.__traceback__)
            self.write_buff = ''
            raise

    def writelines(self, lines):
        '''Required'''
        for line in lines:
            self.write(line)

    def close(self):
        '''Override'''
        if self.stream is not None:
            self.stream.close()
            self.stream = None

    def flush(self):
        '''Override'''
        if self.stream is not None:
            self.stream.flush()

#------------------------------------------------------------------------------
def _write_log(slevel, message, tb=None, readable=False):
    '''Format a standard message with caller info and log it.'''
    if not LOG_FN: return

    if readable:
        # Make non-printables visible.
        buff = []
        bytes = message.encode("utf-8")

        for b in bytes:
            if b >= ord(' ') and b <= ord('~'): # ascii printable
                buff.append(chr(b))
            elif b in XLAT_TBL:
                sxlat = XLAT_TBL[b]
                buff.append(LEFT_DELIM)
                buff.append(sxlat)
                buff.append(RIGHT_DELIM)
            else: # Everything else is binary.
                buff.append(LEFT_DELIM)
                buff.append(f'0x{b:02X}')
                buff.append(RIGHT_DELIM)
        message = ''.join(buff) 

    # Get caller info.
    frame = sys._getframe(2)
    fn = os.path.basename(frame.f_code.co_filename)
    line = frame.f_lineno

    dt = datetime.datetime.now()
    sdate = f'{dt.year:04d}-{dt.month:02d}-{dt.day:02d}'
    stime = f'{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}.{dt.microsecond//1000:03d}.{dt.microsecond%1000:03d}'
    out_line = f'{sdate} {stime} {slevel} {LOG_NAME} {fn}({line}) {message}'

    with open(LOG_FN, 'a', encoding='utf-8') as flog:
        flog.write(out_line + '\n')
        # traceback?
        if tb is not None:
            for tbline in traceback.format_tb(tb):
                for s in tbline.splitlines():
                    flog.write(s + '\n')


#---------------------------- Client starts here ------------------------------
def breakpoint(port, log_fn=None, use_color=True):
    '''Opens a remote pdb session.'''
    ppdb = PbotPdb(port, log_fn, use_color)
    ppdb._set_bp(sys._getframe().f_back)
