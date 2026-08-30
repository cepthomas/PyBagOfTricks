import sys
import os
import socket
import pdb

# import plog # TODO1 remove dependency? Integrate/coexist with sbot (see sbotlog.py).
from plog import Plog

# ---------------------- Internals ----------------------------------

# Colors - https://gist.github.com/JBlond/2fea43a3049b38287e5e9cefc87b2124
CURRENT_LINE_COLOR = 93 # yellow
EXCEPTION_LINE_COLOR = 92 # green
STACK_LOCATION_COLOR = 96 # cyan
PROMPT_COLOR = 95 # magenta
ERROR_COLOR = 91 # red


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
        self.host = '127.0.0.1'
        self.port = port
        self.use_color = use_color
        self.valid = False

        self.sock = None
        self.conn = None
        self.commif = None

        # Logging. Option to keep log file or open/close per entry.
        self.l = Plog('PPDB', log_fn, keep_open=False)
        self.l.enable(True)

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.sock.settimeout(5)  # Seconds.
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            self.sock.bind((self.host, self.port))
            self.l.debug(f'Server started on {self.host}:{self.port} - waiting for connection.')

            # Try to connect. conn is a new socket for R/W.
            self.sock.listen(1)
            self.conn, address = self.sock.accept()

            # Connected.
            chost, cport = address
            self.l.debug(f'Server accepted connection from {chost}:{cport}')

            self.commif = CommIf(self.conn, self.l, self.use_color)
            # Init base.
            super().__init__(stdin=self.commif, stdout=self.commif)  # pyright: ignore
            # TODO1? skip=['unittest.*', 'pbot_pdb.py'])
            # Note: 3.14+ Pdb can syntax color code - see the docs.
            self.valid = True

        except Exception as e:
            # Any errors are considered fatal.
            self.l.error(f'Init failed [{e}]', e.__traceback__)
            self._cleanup()

    # --------------- Custom user cmds ---------------
    def do_quit(self, arg=None):
        ''' Stopping debugging, clean up resources, exit application. '''
        self.l.debug('Server quitting.')
        self._cleanup()

        try:
            return super().do_quit(arg)
        except Exception as e:
            self.l.error(f'do_quit() failed [{e}]', e.__traceback__)
    do_q = do_quit # alias

    # --------------- Go! ---------------------
    def _set_bp(self, frame):
        ''' Starts the debugger.'''
        self.l.debug('breakpoint() entry')
        # self.l.debug(f'>>> frame [{frame}]')
        if not self.valid:
            raise RuntimeError('Breakpoint hit without ppdb initialization')

        # Run pdb. This blocks until pdb says done.
        # Note that exceptions in the code under test go to sys.excepthook so try/except is pointless.
        super().set_trace(frame)

    # ----------------------------------
    def _cleanup(self):
        ''' Clean up resources. '''
        self.l.debug('_cleanup()')

        if self.commif is not None:
            self.commif.close()
            self.commif = None

        if self.sock is not None:
            self.sock.close()
            self.sock = None

        if self.conn is not None:
            self.conn.close()
            self.conn = None


# ---------------------- Socket I/F -------------------------------------
class CommIf(object):
    '''
    Pdb flavored read/write interface to socket. Makes socket look like a file object.
    Also handles encoding, color, line endings etc.
    Catches exceptions for the purpose of logging only. They are re-raised.
    '''

    def __init__(self, conn, logger, use_color):
        self.conn = conn
        self.l = logger
        self.use_color = use_color
        self.buff = ''

        # Return a file object associated with the socket.
        self.stream = self.conn.makefile('rw')

    def __iter__(self):
        return self.stream.__iter__()

    def _send(self, msg):
        self.l.debug(f'CommIf _send [{msg}]', readable=True)
        self.conn.sendall(msg.encode())

    # --------------- Required interface ---------------
    # per https://docs.python.org/3/library/io.html#io.TextIOBase
    # Min: readline()  write()  flush()

    @property
    def encoding(self):
        '''Required'''
        return self.stream.encoding

    def readline(self, size=1):
        '''Core pdb calls this to read from user/client. Captures the last user command.'''
        del size
        # Reset.
        self.buff = ''

        try:
            msg = self.stream.readline() # blocks, throws if timeout
            self.l.debug(f'Received command [{msg}]', readable=True)
            return msg

            # TODO1 first command has extra junk in msg but not on the wire.
            # 2026-08-29 11:57:26.949.373 DBG PPDB pbot_pdb.py(162) Received command:
            # [<0xC3><0xBF><0xC3><0xBB><0x1F><0xC3><0xBF><0xC3><0xBB> <0xC3><0xBF><0xC3><0xBB><0x18><0xC3><0xBF><0xC3><0xBB>'<0xC3><0xBF><0xC3><0xBD><0x01><0xC3><0xBF><0xC3><0xBB><0x03><0xC3><0xBF><0xC3><0xBD><0x03>l<LF>]

            # # TODO Check/handle ansi codes. e.g. up/down/history -> <ESC>[A<LF>
            # if len(msg) > 0 and msg[0] == '\0x1B':
            #     self.l.debug(f'ANSI [{msg}]', readable=True)
            #     return ''
            # else:
            #     self.l.debug(f'Received command [{msg}]', readable=True)
            #     return msg

        except (ConnectionError, socket.timeout) as e:
            '''These can happen, ignore.'''
            self.l.debug(f'read() Disconnected [{type(e)}]')
            self.buff = ''
            return ''

        except Exception as e:
            '''Unexpected error, shut dowwn.'''
            self.l.error(f'read() Other exception [{str(e)}]', e.__traceback__)
            self.buff = ''
            raise

    def write(self, line):
        '''Core pdb calls this to write to user/client. This adjusts and sends to socket.'''
        # self.l.debug(f'pdb said [{line}]', readable=True)

        try:
            # pdb writes lines piecemeal but we want full proper lines.
            # Easiest is to accumulate in a buffer until we see the prompt then slice and write.
            if '(Pdb)' in line:
                for s in self.buff.splitlines():
                    color = None

                    if self.use_color:
                        if s.startswith('-> '): color = CURRENT_LINE_COLOR
                        elif ' ->' in s: color = CURRENT_LINE_COLOR
                        elif s.startswith('>> '): color = EXCEPTION_LINE_COLOR
                        elif '***' in s: color = ERROR_COLOR
                        elif 'Error:' in s: color = ERROR_COLOR
                        elif s.startswith('> '): color = STACK_LOCATION_COLOR

                    self._send(f'{s}{os.linesep}' if color is None else f'\033[{color}m{s}\033[0m{os.linesep}')

                # Write prompt.
                self._send(f'\033[{PROMPT_COLOR}m(Pdb)\033[0m' if self.use_color else f'(Pdb)')

                # Reset buffer.
                self.buff = ''
            else:
                # Just collect.
                self.buff += line

        except (ConnectionError, socket.timeout) as e:
            '''These can happen, go back to default state.'''
            self.l.debug(f'write() Disconnected [{type(e)}]')
            self.buff = ''

        except Exception as e:
            '''Unexpected error, shut dowwn.'''
            self.l.error(f'write() Unexpected exception [{type(e)}]', e.__traceback__)
            self.buff = ''
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

#------------------------------Client starts here -------------------------------------
def breakpoint(port, log_fn=None, use_color=True):
    '''Opens a remote pdb session.'''
    ppdb = PbotPdb(port, log_fn, use_color)
    ppdb._set_bp(sys._getframe().f_back)
