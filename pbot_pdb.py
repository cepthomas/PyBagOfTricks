import sys
import socket
import pdb
import os
import datetime
import traceback
import plog # TODO1 fights with sbot logging.


# UDP or TCP server for embedding in python scripts for debugging purposes.
# Basically creates a remote pdb debugging interface.
# TODO1 finesse two flavors in same file? Maybe not if UDP works ok. PbotPdbTcp


# ---------------------- Configuration ----------------------------------
# TODO1 Make configurable?

# Where to log. Usually same as the client log. None indicates no logging.
LOG_FN = os.path.join(os.path.dirname(__file__), 'log', 'pbot_pdb.log')

HOST = '127.0.0.1'
PORT = 59140 # UDP
# PORT = 59120 # TCP

# Probably UDP only.
ENCODING = 'utf-8'
# Delimiter for socket message lines.
MDEL = '\u000A' # NL
# Timeout. Means different things depending on TCP/UDP.
TIMEOUT = 5
# Add sequence number to all UDP messages. Simple loss detection.
SEQ_NUM = True

# Ansi color (https://en.wikipedia.org/wiki/ANSI_escape_code)
USE_COLOR = False
CURRENT_LINE_COLOR = 93 # yellow
EXCEPTION_LINE_COLOR = 92 # green
STACK_LOCATION_COLOR = 96 # cyan
PROMPT_COLOR = 94 # blue
ERROR_COLOR = 91 # red


#------------------------------------------------------------------------------
class UdpIf(object):
    '''
    Read/write interface to socket. Makes socket look like a file.
    Also handles encoding, color, line endings etc.
    '''

    _last_cmd = None

    # Collected parts of pdb write.
    _pdbBuff = ''

    # Simple packet loss detection.
    _seq_num = 0;

    def __init__(self):
        '''Construction.'''
        pass


    # --------------- Required interface ---------------
    # per https://docs.python.org/3/library/io.html#io.TextIOBase

    @property
    def encoding(self):
        return ENCODING

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
            plog.debug(f'UDP on {HOST}:{PORT} [{TIMEOUT}]')

            while msg is None and not exit:
                try:
                    data, _ = sock.recvfrom(4096) # blocks
                    msg = data.decode(ENCODING)
                    plog.debug(f'Received message: {msg}')

                    if SEQ_NUM:
                        pass
                        # strip seq number from front '[99]'
                        # check if it's expected

                    self._last_cmd = msg
                    return msg

                except KeyboardInterrupt as e:
                    plog.debug(f'KeyboardInterrupt')
                    self._pdbBuff = ''
                    exit = True # orderly shutdown

                except (ConnectionError, socket.timeout) as e:
                    pass
                    # plog.debug(f'ConnectionError timeout')
                    # future use

                except Exception as e:
                    plog.debug(f'UdpIf.readline() exception: {str(e)}')
                    self._pdbBuff = ''
                    raise # hard fail

                # finally:
                #     sock.close()

    def write(self, line):
        '''Core pdb calls this to write to cli/client. This adjusts and sends to socket.'''
        try:
            # pdb writes lines piecemeal but we want full proper lines.
            # Easiest is to accumulate in a buffer until we see the prompt then slice and write.
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

                        msg = f'{s}{MDEL}' if color is None else f'\u001b[{color}m{s}\u001b[0m{MDEL}'
                        if SEQ_NUM:
                            self.seq_num = self._seq_num + 1
                            msg = f'[{self._seq_num}]{msg}{MDEL}'
                        udp_socket.sendto(msg.encode(ENCODING), (HOST, PORT))
                        plog.debug(f'write(): {msg}')

                    # Write prompt.
                    msg = f'\u001b[{PROMPT_COLOR}m(Pdb)\u001b[0m ' if USE_COLOR else '(Pdb)'
                    udp_socket.sendto(msg.encode(ENCODING), (HOST, PORT))
                    plog.debug(f'write(): {msg}')

                    # Reset buffer.
                    self._pdbBuff = ''
            else:
                # Just collect.
                self._pdbBuff += line

        except Exception as e:
            # ?? (ConnectionError, socket.timeout)
            plog.debug(f'UdpIf.write() other exception: {str(e)}')
            self._pdbBuff = ''
            raise

    # read(size=-1, /) not needed?
    #     Read and return at most size characters as str. If size is negative or None, reads until EOF.

    def flush(self):
        pass


#------------------------------------------------------------------------------
class PbotPdb(pdb.Pdb):
    '''Custom pdb using UDP.'''

    def __init__(self):
        '''Construction.'''
        try:
            plog.init('PPBD', LOG_FN, readable=True)
            plog.setEnable(True)

            self.commif = UdpIf()
            super().__init__(stdin=self.commif, stdout=self.commif, skip=None)  # pyright: ignore
            # TODO 3.14+ colorize=True  mode=???   lse - enable colorized output in the debugger, if color is supported.

        except Exception as e:
            # Error handler. ?? ConnectionError, socket.timeout
            plog.error('init failed', e)

    def breakpoint(self, frame):
        ''' Starts the debugger.'''
        plog.debug('breakpoint() entry')
        if self.commif is not None:
            try:
                # This blocks until user says done.
                super().set_trace(frame)

            except Exception as e:
                # Exceptions in the code under test go to sys.excepthook so this doesn't do anything.
                plog.error('breakpoint fail', e)

        plog.debug('breakpoint() exit')
        self.do_quit()


    # --------------- Custom user cmds ---------------
    def do_quit(self, arg=None):
        ''' Stopping debugging, clean up resources, exit application. '''
        plog.info('Server quitting.')

        if self.commif is not None:
            self.commif = None

        try:
            super().do_quit(arg)
        except:
            pass
            # plog.debug('do_quit() exit')
    do_q = do_quit # alias


#------------------------------------------------------------------------------
class TcpIf(object):
    '''
    Read/write interface to socket. Makes server socket look like a file object.
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
        # self.read = fh.read
        # self.readlines = fh.readlines
        self.close = fh.close
        self.flush = fh.flush
        self.fileno = fh.fileno

    # --------------- Required interface ---------------
    # per https://docs.python.org/3/library/io.html#io.TextIOBase

    @property
    def encoding(self):
        return self.stream.encoding

    def send(self, msg):
        # plog.debug(f'send(): {make_readable(msg)}')
        self.conn.sendall(msg.encode())

    def readline(self, size=1):
        del size
        '''Core pdb calls this to read from cli/client. Captures the last user command.'''
        try:
            msg = self.stream.readline()
            self.last_cmd = msg
            # plog.debug(f'Received command: {make_readable(msg)}')
            return self.last_cmd

        except (ConnectionError, socket.timeout) as e:
            plog.debug(f'Disconnected: {type(e)}')
            raise

        except Exception as e:
            plog.debug(f'TcpIf.readline() other exception: {str(e)}')
            self.buff = ''
            raise

    def __iter__(self):
        return self.stream.__iter__()

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

                    self.send(f'{s}{MDEL}' if color is None else f'\u001b[{color}m{s}\u001b[0m{MDEL}')

                # Write prompt.
                self.send(f'\u001b[{PROMPT_COLOR}m(Pdb)\u001b[0m ' if USE_COLOR else '(Pdb)')
                # plog.debug(f'write(): {msg}')

                # Reset buffer.
                self.buff = ''
            else:
                # Just collect.
                self.buff += line

        except (ConnectionError, socket.timeout) as e:
            plog.debug(f'Disconnected: {type(e)}')
            raise

        except Exception as e:
            plog.debug(f'TcpIf.write() other exception: {str(e)}')
            self.buff = ''
            raise


#------------------------------------------------------------------------------
class PbotPdbTcp(pdb.Pdb):
    '''Run pdb behind a blocking tcp server.'''

    def __init__(self):
        '''Construction.'''
        try:
            plog.init('PPBD', LOG_FN, readable=True)
            plog.setEnable(True)

            self.sock = None
            self.commif = None
            self.active_instance = None

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if TIMEOUT > 0:
                self.sock.settimeout(TIMEOUT)  # Seconds.
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            self.sock.bind((HOST, PORT))
            plog.info(f'Server started on {HOST}:{PORT} - waiting for connection.')

            # Blocks until client connect or timeout.
            self.sock.listen(1)
            conn, address = self.sock.accept()

            # Connected.
            plog.info(f'Server accepted connection from {repr(address)}.')
            self.commif = TcpIf(conn)
            super().__init__(completekey='tab', stdin=self.commif, stdout=self.commif)  # pyright: ignore
            PbotPdb.active_instance = self

        except (ConnectionError, socket.timeout) as e:
            plog.info(f'Server connection timed out, try again: {str(e)}')
            self.do_quit()

        except Exception as e:
            # Other error handler.
            plog.error('init fail', e)

    def breakpoint(self, frame):
        '''Starts the debugger.'''
        plog.debug('breakpoint() entry')
        if self.commif is not None:
            try:
                # This blocks until user says done.
                super().set_trace(frame)

            except Exception as e:
                # Exceptions in the code under test go to sys.excepthook so this doesn't do anything.
                plog.error('breakpoint fail', e)

        plog.debug('breakpoint() exit')
        self.do_quit()

    # --------------- Custom user cmds ---------------
    def do_quit(self, arg=None):
        '''Stopping debugging, clean up resources, exit application.'''
        plog.info('Server quitting.')

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
            # do_debug('do_quit() exit')
    do_q = do_quit # alias


#------------------------------------------------------------------------------
def breakpoint():
    '''Opens a remote PDB. See test_pdb.py.'''
    ppdb = PbotPdb()
    ppdb.breakpoint(sys._getframe().f_back)
