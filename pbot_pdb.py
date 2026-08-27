import sys
import socket
import pdb
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

        # socket.close()
        # Mark the socket closed. The underlying system resource (e.g. a file descriptor) is also closed when
        # all file objects from makefile() are closed. Once that happens, all future operations on the socket
        # object will fail. The remote end will receive no more data (after queued data is flushed).
        # Sockets are automatically closed when they are garbage-collected, but it is recommended to close() them explicitly,
        self.sock = None
        self.conn = None
        self.commif = None

        # Logging.
        self.l = plog.Plog('PPDB', log_fn, keep_open=False)
        self.l.enable(True)
        self.l.info(f'Starting client on {self.host}:{self.port}')

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.sock.settimeout(5)  # Seconds.
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            self.sock.bind((self.host, self.port))
            self.l.info(f'Server started on {self.host}:{self.port} - waiting for connection.')

            # Try to connect. conn is a new socket for R/W.
            self.sock.listen(1)
            self.conn, address = self.sock.accept()

            # Connected.
            chost, cport = address
            self.l.info(f'Server accepted connection from {chost}:{cport}')

            self.commif = CommIf(self.conn, self.l, self.use_color)
            self.l.info(f'Server init commif begin')
            # Init base.
            super().__init__(stdin=self.commif, stdout=self.commif)  # pyright: ignore
            # super().__init__(stdin=commif, stdout=commif, skip=['unittest.*', 'pbot_pdb.py'])  # pyright: ignore
            # TODO 3.14+ Pdb can color code - see the docs.
            self.valid = True
            self.l.info(f'Server init commif end')

        except Exception as e:
            # Any errors are considered fatal.
            self.l.error(f'Init failed [{e}]', e.__traceback__)
            self.do_quit()

    # --------------- Go! ---------------------
    def breakpoint(self, frame):
        ''' Starts the debugger.'''
        self.l.debug('breakpoint() entry')
        if not self.valid:
            raise RuntimeError('Breakpoint hit without ppdb initialization')

        # Run pdb. This blocks until pdb says done.
        # Note that exceptions in the code under test go to sys.excepthook so try/except is pointless.
        super().set_trace(frame)

        self.l.debug('breakpoint() exit')
        self.do_quit()

    # --------------- Custom user cmds ---------------
    def do_quit(self, arg=None):
        ''' Stopping debugging, clean up resources, exit application. '''
        self.l.info('Server quitting.')

        if self.commif is not None:
            self.commif.close()
            self.commif = None

        if self.sock is not None:
            self.sock.close()
            self.sock = None

        if self.conn is not None:
            self.conn.close()
            self.conn = None

        try:
            return super().do_quit(arg)
        except Exception as e:
            self.l.error(f'do_quit() failed [{e}]', e.__traceback__)
            # self.l.debug('do_quit() exit')
    do_q = do_quit # alias

# ---------------------- Socket I/F -------------------------------------
class CommIf(object):
    '''
    Pdb flavored read/write interface to socket. Makes socket look like a file object.
    Also handles encoding, color, line endings etc.
    Catches exceptions for the purpose of logging only. They are re-raised.
    '''
# Min:
# line = self.stdin.readline()
# self.stdout.write(str(self.intro)+"\n")
# self.stdout.flush()


    def __init__(self, conn, logger, use_color):
        self.conn = conn
        self.l = logger
        self.use_color = use_color
        self.last_cmd = None
        self.buff = ''

        self.l.debug('CommIf __init__ in')

        # Return a file object associated with the socket.
        self.stream = self.conn.makefile('rw')
        # fh = self.conn.makefile('rw')
        self.l.debug('CommIf __init__ out')
        # self.stream = fh
        # self.read = self.stream.read
        # self.readline = self.stream.readline
        # self.readlines = self.stream.readlines

    def __iter__(self):
        return self.stream.__iter__()

    def _send(self, msg):
        self.l.debug(f'CommIf _send [{msg}]', readable=True)
        self.conn.sendall(msg.encode())

    # --------------- Required interface ---------------
    # per https://docs.python.org/3/library/io.html#io.TextIOBase

    # @property
    # def encoding(self):
    #     '''Required'''
    #     return self.stream.encoding

    def readline(self, size=1):
        '''Core pdb calls this to read from user/client. Captures the last user command.'''
        del size
        # Reset.
        self.buff = ''

        self.l.debug(f'readline() entry')

        try:
            msg = self.stream.readline() # blocks, throws if timeout
            self.last_cmd = msg
            self.l.debug(f'Received command [{msg}]')
            return msg

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
