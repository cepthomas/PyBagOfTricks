import sys
import socket
import pdb
import os
import datetime
import traceback
import shutil



# ---------------------- Configuration ----------------------------------
# TODO Make configurable by client cmd line?

### REQUIRED ###
MODE = 'UDP' # OR 'TCP'
HOST = '127.0.0.1'  
PORT = 59140 # typ UDP  59120 for TCP

### OPTIONAL ###
# Where to log. None indicates no logging.
LOG_FN = os.path.join(os.path.dirname(__file__), 'log', 'pbot_pdb.log')

# Timeout. Means different things depending on TCP/UDP.
TIMEOUT = 1 # UDP
# TIMEOUT = 5 # TCP

# Add sequence number to UDP messages. Simple loss detection.
SEQ_NUM = True

# Show non-ascii content.
READABLE = True

# Ansi color (https://en.wikipedia.org/wiki/ANSI_escape_code)
USE_COLOR = False
CURRENT_LINE_COLOR = 93 # yellow
EXCEPTION_LINE_COLOR = 92 # green
STACK_LOCATION_COLOR = 96 # cyan
PROMPT_COLOR = 94 # blue
ERROR_COLOR = 91 # red


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

            if MODE.upper() == 'UDP': self.init_udp()
            elif MODE.upper() == 'TCP': self.init_tcp()
            else: error('Invalid MODE')

            # Init base.
            super().__init__(stdin=self.commif, stdout=self.commif, skip=None)  # pyright: ignore
            # TODO 3.14+ colorize=True  mode=???   lse - enable colorized output in the debugger, if color is supported.

        except Exception as e:
            # Error handler. ?? ConnectionError, socket.timeout
            error('init failed', e)

    def init_udp(self):
        '''Create UDP.'''
        self.commif = UdpIf()

    def init_tcp(self):
        '''Create TCP. TODO needs clean and test.'''
        try:
            self.sock = None
            self.commif = None
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if TIMEOUT > 0:
                self.sock.settimeout(TIMEOUT)  # Seconds.
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            self.sock.bind((HOST, PORT))
            info(f'Server started on {HOST}:{PORT} - waiting for connection.')
            # Blocks until client connect or timeout.
            self.sock.listen(1)
            conn, address = self.sock.accept()
            # Connected.
            info(f'Server accepted connection from {repr(address)}.')
            self.commif = TcpIf(conn)
        except (ConnectionError, socket.timeout) as e:
            info(f'Server connection timed out, try again: {str(e)}')
            # not?! self.do_quit()
        except Exception as e:
            # Other error handler.
            error('init fail', e)

    # --------------- Go! ---------------------
    def breakpoint(self, frame):
        ''' Starts the debugger.'''
        debug('breakpoint() entry')
        if self.commif is not None:
            try:
                # This blocks until user says done.
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

        # TCP only.
        if self.sock is not None:
            self.sock.close()
            self.sock = None

        try:
            super().do_quit(arg)
        except:
            pass
            # debug('do_quit() exit')
    do_q = do_quit # alias

# ---------------------- UDP flavor -------------------------------------
class UdpIf(object):
    '''
    Read/write interface to socket. Makes socket look like a file object.
    Also handles encoding, color, line endings etc.
    '''

    def __init__(self):
        '''Construction.'''
        self._last_cmd = None
        # Collected parts of pdb write.
        self._pdbBuff = ''
        # Simple packet loss detection.
        self._seq_num = 0;
        self._encoding = 'utf-8'


    def close(self):
        pass

    # --------------- Required interface ---------------
    # per https://docs.python.org/3/library/io.html#io.TextIOBase

    @property
    def encoding(self):
        return self._encoding

    def readline(self, size=1):
        '''Core pdb calls this to read from cli/client. Returns the valid user command.'''
        del size
        msg = None
        exit = False

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((HOST, PORT))
            if TIMEOUT > 0:
                sock.settimeout(TIMEOUT)  # Seconds.
            debug(f'UDP on {HOST}:{PORT} [{TIMEOUT}]')

            while msg is None and not exit:
                try:
                    data, _ = sock.recvfrom(4096) # blocks
                    msg = data.decode(self._encoding)
                    debug(f'Received message: {msg}')

                    if SEQ_NUM:
                        pass
                        # TODO strip seq number from front '[99]' and check if it's expected

                    self._last_cmd = msg
                    return msg

                except KeyboardInterrupt as e:
                    debug(f'KeyboardInterrupt')
                    self._pdbBuff = ''
                    exit = True # orderly shutdown

                except (ConnectionError, socket.timeout) as e:
                    # debug(f'ConnectionError timeout')
                    pass

                except Exception as e:
                    debug(f'UdpIf.readline() other exception: {str(e)}')
                    self._pdbBuff = ''
                    raise # hard fail

                # finally:
                #     sock.close()

    def write(self, line):
        '''Core pdb calls this to write to cli/client. This adjusts and sends to socket.'''
        try:
            # pdb writes lines piecemeal but we want full proper lines. Presumes core is handling NLs.
            # Easiest is to accumulate in a buffer until we see the prompt then slice and write. TODO some common with TCP.
            if '(Pdb)' in line:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                    for s in self._pdbBuff.splitlines():
                        # sc.debug(f'DBG Send response: {s}')
                        color = None

                        if USE_COLOR:
                            if s.startswith('-> '): color = CURRENT_LINE_COLOR
                            elif ' ->' in s: color = CURRENT_LINE_COLOR
                            elif s.startswith('>> '): color = EXCEPTION_LINE_COLOR
                            elif '***' in s: color = ERROR_COLOR
                            elif 'Error:' in s: color = ERROR_COLOR
                            elif s.startswith('> '): color = STACK_LOCATION_COLOR

                        msg = f'{s}' if color is None else f'\u001b[{color}m{s}\u001b[0m'
                        if SEQ_NUM:
                            self.seq_num = self._seq_num + 1
                            msg = f'[{self._seq_num}]{msg}'
                        udp_socket.sendto(msg.encode(self._encoding), (HOST, PORT))
                        debug(f'write(): {msg}')

                    # Write prompt.
                    msg = f'\u001b[{PROMPT_COLOR}m(Pdb)\u001b[0m\n' if USE_COLOR else '(Pdb)\n'
                    udp_socket.sendto(msg.encode(self._encoding), (HOST, PORT))
                    debug(f'write(): {msg}')

                    # Reset buffer.
                    self._pdbBuff = ''
            else:
                # Just collect.
                self._pdbBuff += line

        except Exception as e:
            # ?? (ConnectionError, socket.timeout)
            debug(f'UdpIf.write() other exception: {str(e)}')
            self._pdbBuff = ''
            raise

    # read(size=-1, /) not needed?
    #     Read and return at most size characters as str. If size is negative or None, reads until EOF.

    def flush(self):
        pass


# ---------------------- TCP flavor -------------------------------------
class TcpIf(object):
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

# The line terminator is always b'\n' for binary files; for text files, the newline argument to open() can be used to select the line terminator(s) recognized.

    def __iter__(self):
        return self.stream.__iter__()

    def send(self, msg):
        msg += '\n'
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
            msg = self.stream.readline()
            self.last_cmd = msg
            # debug(f'Received command: {makeREADABLE(msg)}')
            return self.last_cmd

        except (ConnectionError, socket.timeout) as e:
            debug(f'Disconnected: {type(e)}')
            raise

        except Exception as e:
            debug(f'TcpIf.readline() other exception: {str(e)}')
            self.buff = ''
            raise

    def write(self, line):
        '''Core pdb calls this to write to cli/client. This adjusts and sends to socket.'''
        try:
            # pdb writes lines piecemeal but we want full proper lines.
            # Easiest is to accumulate in a buffer until we see the prompt then slice and write.
            if '(Pdb)' in line:
                for s in self.buff.splitlines():
                    # sc.debug(f'DBG Send response: {s}')
                    color = None

                    if USE_COLOR:
                        if s.startswith('-> '): color = CURRENT_LINE_COLOR
                        elif ' ->' in s: color = CURRENT_LINE_COLOR
                        elif s.startswith('>> '): color = EXCEPTION_LINE_COLOR
                        elif '***' in s: color = ERROR_COLOR
                        elif 'Error:' in s: color = ERROR_COLOR
                        elif s.startswith('> '): color = STACK_LOCATION_COLOR

                    self.send(f'{s}' if color is None else f'\u001b[{color}m{s}\u001b[0m')

                # Write prompt.
                self.send(f'\u001b[{PROMPT_COLOR}m(Pdb)\u001b[0m ' if USE_COLOR else '(Pdb)')
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
            debug(f'TcpIf.write() other exception: {str(e)}')
            self.buff = ''
            raise


# ---------------------- Common -------------------------------------
def error(message, tb=None): _write_log('ERR', message, tb) # TODO Show the user some info?
def warn(message): _write_log('WRN', message)
def info(message): _write_log('INF', message)
def debug(message): _write_log('DBG', message)

def _write_log(level, message, tb=None):
    '''Format a standard message with caller info and log it.'''
    if not LOG_FN: return

    if READABLE:
        '''So we can see things like LF, CR, ESC in log. TODO user-supplied list.'''
        message = message.replace('\n', '_N').replace('\r', '_R').replace('\u001b', '_E')

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

