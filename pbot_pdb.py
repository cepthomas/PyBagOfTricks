import sys
import socket
import pdb
import os
# import datetime
# import traceback
# import shutil
import plog


# ---------------------- Internals ----------------------------------

CURRENT_LINE_COLOR = 93 # yellow
EXCEPTION_LINE_COLOR = 92 # green
STACK_LOCATION_COLOR = 96 # cyan
PROMPT_COLOR = 94 # blue
ERROR_COLOR = 91 # red

# https://docs.python.org/3.8/library/socket.html

#------------------------------------------------------------------------------
class PbotPdb(pdb.Pdb):
    '''Custom pdb using TCP.'''

    # --------------- Construction ---------------
    def __init__(self, port, log_fn, use_color=True):
        '''Construction.'''
        self.host = '127.0.0.1'
        self.port = port
        self.use_color = use_color
        self.valid = False

        # Logging.
        self.l = plog.Plog('PPDB', log_fn)
        self.l.enable(True)
        self.l.info(f'Starting client on {self.host}:{self.port}')

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)  # Seconds.
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
                sock.bind((self.host, self.port))
                self.l.info(f'Server started on {self.host}:{self.port} - waiting for connection.')

                # Try to connect. conn is a new socket for R/W.
                sock.listen(1)
                conn, address = sock.accept()

                # Connected.
                with conn:
                    chost, cport = address
                    self.l.info(f'Server accepted connection from {chost}:{cport}')

                    with CommIf(conn, self.l, self.use_color) as commif:
                        self.l.info(f'Server init commif')
                        # Init base.
                        super().__init__(stdin=commif, stdout=commif)  # pyright: ignore
                        # TODO1 super().__init__(stdin=commif, stdout=commif, skip=['unittest.*', 'pbot_pdb.py'])  # pyright: ignore
                        # TODO1 3.14+ colorize=True  mode=???   lse - enable colorized output in the debugger, if color is supported.
                        self.valid = True
                        self.l.info(f'Server init commif done')

        except Exception as e:
            # TODO1 Other error handler, considered fatal.
            self.l.error('Init failed', e.__traceback__)
            self.do_quit()

    # --------------- Go! ---------------------
    def breakpoint(self, frame):
        ''' Starts the debugger.'''
        self.l.debug('breakpoint() entry')
        if not self.valid:
            raise RuntimeError('Breakpoint hit without ppdb initialization')

        # This blocks until client says done. Note this messes with the stack so things get weird after.
        # Note - Exceptions in the code under test go to sys.excepthook so try/except is pointless.
        super().set_trace(frame)

        self.l.debug('breakpoint() exit')
        self.do_quit()

    # --------------- Custom user cmds ---------------
    def do_quit(self, arg=None):
        ''' Stopping debugging, clean up resources, exit application. '''
        self.l.info('Server quitting.')

        try:
            return super().do_quit(arg)
        except:
            self.l.debug('do_quit() exit')
    do_q = do_quit # alias


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
        self.last_cmd = None
        self.buff = ''

    def __enter__(self):
        '''For with usage.'''
        fh = self.conn.makefile('rw')
        self.stream = fh
        return self  # the 'as' variable

    def __exit__(self, exc_type, exc_val, exc_tb):
        '''For with usage.'''
        self.conn.close()
        if exc_type is not None:
            self.l.error(f"An error occurred: {exc_val}", exc_tb)
        return True  # Returns True to suppress the exception and keep running

    def __iter__(self):
        return self.stream.__iter__()

    def _send(self, msg):
        self.conn.sendall(msg.encode())

    # --------------- Required interface ---------------
    # per https://docs.python.org/3/library/io.html#io.TextIOBase

    @property
    def encoding(self):
        '''Required'''
        return self.stream.encoding

    def readline(self, size=1):
        '''Core pdb calls this to read from cli/client. Captures the last user command.'''
        del size
        # Reset.
        self.buff = ''

        try:
            msg = self.stream.readline() # blocks, throws if timeout
            self.last_cmd = msg
            self.l.debug(f'Received command [{msg}]')
            return msg

        except (ConnectionError, socket.timeout) as e:
            '''These can happen, ignore.'''
            self.l.debug(f'Disconnected: {type(e)}')
            self.buff = ''
            return ''

        except Exception as e:
            '''Unexpected error, shut dowwn.'''
            self.l.error(f'Other exception [{str(e)}]', e.__traceback__)
            self.buff = ''
            raise

    def write(self, line):
        '''Core pdb calls this to write to cli/client. This adjusts and sends to socket.'''
        self.l.debug(f'pdb said [{line}]', readable=True)
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

                    self._send(f'{s}' if color is None else f'\033[{color}m{s}\033[0m')

                # Write prompt.
                self._send(f'\u001b[{PROMPT_COLOR}m(Pdb)\u001b[0m ' if self.use_color else '(Pdb)')

                # Reset buffer.
                self.buff = ''
            else:
                # Just collect.
                self.buff += line

        except (ConnectionError, socket.timeout) as e:
            '''These can happen, go back to default state.'''
            self.l.debug(f'Disconnected [{type(e)}]')
            self.buff = ''

        except Exception as e:
            '''Unexpected error, shut dowwn.'''
            self.l.error(f'Unexpected exception [{type(e)}]', e.__traceback__)
            self.buff = ''
            raise

    def writelines(self, lines):
        '''Required'''
        for line in lines:
            self.write(line)

    def close(self):
        '''Override'''
        self.stream.close()
        self.stream = None

    def flush(self):
        '''Override'''
        self.stream.flush()


#------------------------------Client starts here -------------------------------------
def breakpoint(port, log_fn=None, use_color=True):
    '''Opens a remote pdb session.'''
    ppdb = PbotPdb(port, log_fn, use_color)
    ppdb.breakpoint(sys._getframe().f_back)
    ppdb.do_quit()
