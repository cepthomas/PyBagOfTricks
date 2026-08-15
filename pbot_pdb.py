import sys
import socket
import pdb
import os
import datetime
import traceback
import shutil


# ---------------------- Configuration ----------------------------------
# TODO1 Make some/all configurable by client cmd line?

### Required
PORT = -1

### Optional.
HOST = '127.0.0.1'

# Where to log or None.
LOG_FN = None

# Translate non-ascii content.
XLAT = {}

# Ansi color (https://en.wikipedia.org/wiki/ANSI_escape_code)
USE_COLOR = False
CURRENT_LINE_COLOR = 93 # yellow
EXCEPTION_LINE_COLOR = 92 # green
STACK_LOCATION_COLOR = 96 # cyan
PROMPT_COLOR = 94 # blue
ERROR_COLOR = 91 # red


# ---------------------- Vars ----------------------------------



# ---------------------- TCP flavor -------------------------------------
class CommIf(object):
    '''
    Read/write interface to socket. Makes socket look like a file object.
    Also handles encoding, color, line endings etc.
    Catches exceptions for the purpose of logging only. They are re-raised.
    '''

    def __init__(self, conn):
        self.conn = conn
        self.last_cmd = None
        self.buff = ''

        # Return a file object associated with the socket. https://docs.python.org/3.8/library/socket.html
        fh = conn.makefile('rw')
        self.stream = fh
        self.close = fh.close
        self.flush = fh.flush
        self.fileno = fh.fileno

    def __iter__(self):
        return self.stream.__iter__()

    def _send(self, msg):
        # msg += '\n'
        self.conn.sendall(msg.encode())

    # --------------- Required interface ---------------
    # per https://docs.python.org/3/library/io.html#io.TextIOBase

    @property
    def encoding(self):
        return self.stream.encoding

    def readline(self, size=1):
        del size
        '''Core pdb calls this to read from cli/client. Captures the last user command.'''
        try:
            msg = self.stream.readline() # blocks, throws if timeout
            self.last_cmd = msg
            # debug(f'Received command: {msg}')
            return msg

        except (ConnectionError, socket.timeout) as e:
            debug(f'Disconnected: {type(e)}')
            raise

        except Exception as e:
            debug(f'CommIf.readline() other exception: {str(e)}')
            self.buff = ''
            raise

    def write(self, line):
        '''Core pdb calls this to write to cli/client. This adjusts and sends to socket.'''
        # debug(f'write [{line}]')
        try:
            # pdb writes lines piecemeal but we want full proper lines.
            # Easiest is to accumulate in a buffer until we see the prompt then slice and write.
            if '(Pdb)' in line:
                for s in self.buff.splitlines():
                    # debug(f'DBG Send response: {s}')
                    color = None

                    if USE_COLOR:
                        if s.startswith('-> '): color = CURRENT_LINE_COLOR
                        elif ' ->' in s: color = CURRENT_LINE_COLOR
                        elif s.startswith('>> '): color = EXCEPTION_LINE_COLOR
                        elif '***' in s: color = ERROR_COLOR
                        elif 'Error:' in s: color = ERROR_COLOR
                        elif s.startswith('> '): color = STACK_LOCATION_COLOR

                    self._send(f'{s}\n' if color is None else f'\033[{color}m{s}\033[0m\n')

                # Write prompt.
                self._send(f'\u001b[{PROMPT_COLOR}m(Pdb)\u001b[0m ' if USE_COLOR else '(Pdb)')
                # debug(f'write(): {msg}')

                # Reset buffer.
                self.buff = ''
            else:
                # Just collect.
                self.buff += line

        except (ConnectionError, socket.timeout) as e:
            debug(f'Disconnected: {type(e)}')
            raise

        except Exception as e:
            debug(f'CommIf.write() other exception: {str(e)}')
            self.buff = ''
            raise


#------------------------------------------------------------------------------
class PbotPdb(pdb.Pdb):
    '''Custom pdb using UDP.'''

    # --------------- Construction ---------------
    def __init__(self):
        '''Construction.'''
        
        try:
            # Initialize logging. Maybe roll over log now.
            if LOG_FN and os.path.exists(LOG_FN) and os.path.getsize(LOG_FN) > 50000:
                bup = LOG_FN.replace('.log', '_old.log')
                shutil.copyfile(LOG_FN, bup)
                # Clear current log file.
                with open(LOG_FN, 'w'):
                    pass

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)  # Seconds.
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            self.sock.bind((HOST, PORT))
            info(f'Server started on {HOST}:{PORT} - waiting for connection.')

            # Blocks until client connect or timeout.
            self.sock.listen(1)
            conn, address = self.sock.accept()

            # Connected.
            info(f'Server accepted connection from {repr(address)}.')
            self.commif = CommIf(conn)

            # Init base.
            super().__init__(stdin=self.commif, stdout=self.commif, skip=['unittest.*', 'pbot_pdb.py'])  # pyright: ignore
            # TODO 3.14+ colorize=True  mode=???   lse - enable colorized output in the debugger, if color is supported.

        except (ConnectionError, socket.timeout) as e:
            info(f'Server connection timed out, try again: {str(e)}')
            self.do_quit() # TODO1 correct?

        except Exception as e:
            # Other error handler. ?? ConnectionError, socket.timeout
            error('init failed', e)


    # --------------- Go! ---------------------
    def breakpoint(self, frame):
        ''' Starts the debugger.'''
        debug('breakpoint() entry')
        if self.commif is not None:
            try:
                # This blocks until user says done. Note this messes with the stack so things get weird after.
                super().set_trace(frame)

            except Exception as e:
                # Exceptions in the code under test go to sys.excepthook so this doesn't do anything.
                error('breakpoint fail', e)

        debug('breakpoint() exit')
        self.do_quit()

    # --------------- Custom user cmds ---------------
    def do_quit(self, arg=None):
        ''' Stopping debugging, clean up resources, exit application. '''
        info('Server quitting.')

        if self.commif is not None:
            self.commif.close()
            self.commif = None

        if self.sock is not None:
            self.sock.close()
            self.sock = None

        try:
            super().do_quit(arg)
        except:
            pass
            # debug('do_quit() exit')
    do_q = do_quit # alias


# ---------------------- Infrastructure ----------------------------
def error(message, e=None): _write_log('ERR', message, e) # TODO Show the user some info?
def warn(message): _write_log('WRN', message)
def info(message): _write_log('INF', message)
def debug(message): _write_log('DBG', message)

def _write_log(level, message, e=None):
    '''Format a standard message with caller info and log it.'''
    if not LOG_FN: return

    tb = None if not e else e.__traceback__

    for k, v in XLAT.items():
        message = message.replace(k, v)

    # Get caller info.
    frame = sys._getframe(2)
    fn = os.path.basename(frame.f_code.co_filename)
    line = frame.f_lineno

    time_str = f'{str(datetime.datetime.now())}'[0:-3]

    # Write the record. TODO need thread sync?
    with open(LOG_FN, 'a') as log:
        out_line = f'{time_str} {level} PPDB {fn}({line}) {message}'
        log.write(out_line + '\n')
        if tb is not None:
            for tbline in traceback.format_tb(tb):
                for s in tbline.splitlines():
                    log.write(s + '\n')
        log.flush()


#------------------------------ Start here -------------------------------------
def breakpoint():
    '''Opens a remote PDB.'''
    ppdb = PbotPdb()
    ppdb.breakpoint(sys._getframe().f_back)
