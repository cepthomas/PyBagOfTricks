import sys
import socket
import pdb
import os
import datetime
import traceback


#############################################################################
# UDP for embedding in python scripts for debugging purposes.
# Basically creates a remote pdb debugging interface.
#############################################################################



#------------------------------------------------------------------------------
#------------------------- Configuration start --------------------------------
#------------------------------------------------------------------------------

# Where to log. Usually same as the client log. None indicates no logging.
LOG_FN = os.path.join(os.path.dirname(__file__), 'ppdb.log')

HOST = '127.0.0.1'
PORT = 59120

# Client connect seconds after breakpoint() called 0=forever. TODO1 any timeout on read()?
TIMEOUT = 5

# Indicate internal message (not pdb)
MSG_IND = '!'

# Server provides ansi color (https://en.wikipedia.org/wiki/ANSI_escape_code)
USE_COLOR = False
CURRENT_LINE_COLOR = 93 # yellow
EXCEPTION_LINE_COLOR = 92 # green
STACK_LOCATION_COLOR = 96 # cyan
PROMPT_COLOR = 94 # blue
ERROR_COLOR = 91 # red

# Delimiter for socket message lines.
MDEL = '' # '\n'


SEQ_NUM = True
ENCODING = 'utf-8'

#------------------------------------------------------------------------------
#------------------------- Configuration end ----------------------------------
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
class CommIf(object):
    '''
    Read/write interface to socket. Makes socket look like a file.
    Also handles encoding, color, line endings etc.
    '''

    _last_cmd = None
    _buff = ''
    _seq_num = 0;

    # def __init__(self):
        # '''Construction.'''


    # --------------- Required interface ---------------
    # per https://docs.python.org/3/library/io.html#io.TextIOBase

    @property
    def encoding(self):
        return ENCODING

    # read(size=-1, /) ??
    #     Read and return at most size characters as str. If size is negative or None, reads until EOF.

    def flush(self):
        pass

    def readline(self, size=1):
        del size
        '''Core pdb calls this to read from cli/client. Captures the last user command.'''


        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        # if TIMEOUT > 0:
        #     sock.settimeout(TIMEOUT)  # Seconds.
        self._debug(f'UDP on {HOST}:{PORT} [{TIMEOUT}]')

        try:
            data, _ = sock.recvfrom(4096)
            msg = data.decode(ENCODING)
            self._debug(f'Received command: {self._make_readable(msg)}')

            if SEQ_NUM:
                pass
                # strip seq number from front '[99]'
                # check if it's expected

            self._last_cmd = msg
            return msg

        except Exception as e:
            # KeyboardInterrupt, ConnectionError, socket.timeout
            self._debug(f'CommIf.readline() exception: {str(e)}')
            self._buff = ''
            raise

        finally:
            sock.close()

    def write(self, line):
        '''Core pdb calls this to write to cli/client. This adjusts and sends to socket.'''
        try:
            # pdb writes lines piecemeal but we want full proper lines.
            # Easiest is to accumulate in a buffer until we see the prompt then slice and write.
            if '(Pdb)' in line:
                for s in self._buff.splitlines():
                    # sc.debug(f'DBG Send response: {s}')
                    color = None

                    if USE_COLOR:
                        if s.startswith('-> '): color = CURRENT_LINE_COLOR
                        elif ' ->' in s: color = CURRENT_LINE_COLOR
                        elif s.startswith('>> '): color = EXCEPTION_LINE_COLOR
                        elif '***' in s: color = ERROR_COLOR
                        elif 'Error:' in s: color = ERROR_COLOR
                        elif s.startswith('> '): color = STACK_LOCATION_COLOR

                    self._send(f'{s}{MDEL}' if color is None else f'\u001b[{color}m{s}\u001b[0m{MDEL}')

                # self._prompt()
                s = f'\u001b[{PROMPT_COLOR}m(Pdb)\u001b[0m ' if USE_COLOR else '(Pdb)'
                self._send(s)

                # Reset buffer.
                self._buff = ''
            else:
                # Just collect.
                self._buff += line

        except Exception as e:
            # ?? (ConnectionError, socket.timeout)
            self._debug(f'CommIf.write() other exception: {str(e)}')
            self._buff = ''
            raise

    # --------------- Internals ---------------

    def _send(self, msg):
        # Send a UDP message. Caller handles errors.
        if SEQ_NUM:
            self.seq_num = self._seq_num + 1
            msg = f'[{self._seq_num}]{msg}{MDEL}'

        self._debug(f'_send(): {self._make_readable(msg)}')

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.sendto(msg.encode(ENCODING), (HOST, PORT))

    def _make_readable(self, s):
        '''So we can see things like LF, CR, ESC in log.'''
        s = s.replace('\n', '_N').replace('\r', '_R').replace('\u001b', '_E')
        return s

    def _debug(self, msg):
        '''Log only.'''
        _write_log('COM', msg)


#------------------------------------------------------------------------------
class PbotPdb(pdb.Pdb):
    '''Custom pdb using UDP.'''

    def __init__(self):
        '''Construction.'''
        try:
            self.commif = CommIf()
            super().__init__(stdin=self.commif, stdout=self.commif)  # pyright: ignore
            # TODO1 colorize=False - enable colorized output in the debugger, if color is supported. This will highlight source code displayed in pdb
            # mode=None - specifies how the debugger was invoked. It impacts the workings of some debugger commands. Valid values are 'inline' (used by the breakpoint() builtin), 'cli' (used by the command line invocation) or None (for backwards compatible behaviour, as before the mode argument was added).
            # skip=None - iterable of glob-style module name patterns. The debugger will not step into frames that originate in a module that matches one of these patterns.

        except Exception as e:
            # Error handler. ?? ConnectionError, socket.timeout
            self._error(e)

    def breakpoint(self, frame):
        ''' Starts the debugger.'''
        self._debug('breakpoint() entry')
        if self.commif is not None:
            try:
                # This blocks until user says done.
                super().set_trace(frame)

            except Exception as e:
                # Exceptions in the code under test go to sys.excepthook so this doesn't do anything.
                self._error(e)

        self._debug('breakpoint() exit')
        self.do_quit()


    # --------------- Custom user cmds ---------------
    def do_quit(self, arg=None):
        ''' Stopping debugging, clean up resources, exit application. '''
        self._info('Server quitting.')

        if self.commif is not None:
            self.commif = None

        try:
            super().do_quit(arg)
        except:
            pass
            # self._debug('do_quit() exit')
    do_q = do_quit # alias


    # --------------- Internals ---------------
    def _error(self, e):
        '''Log, tell, exit. All are considered fatal. Exit the application. User needs to restart debugger.'''
        _write_log('ERR', str(e), e.__traceback__)
        sys.stdout.write(f'{MSG_IND} Server Error: {e}\n')
        sys.stdout.flush()
        self.do_quit()

    def _info(self, msg):
        '''Log, tell.'''
        _write_log('INF', msg)
        sys.stdout.write(f'{MSG_IND} {msg}\n')
        sys.stdout.flush()

    def _debug(self, msg):
        '''Log only.'''
        _write_log('DBG', msg)


#------------------------------------------------------------------------------
def _write_log(level, msg, tb=None):
    '''Format a standard message with caller info and log it. Optional trace.'''
    if LOG_FN is None:
        return
    frame = sys._getframe(2)
    time_str = f'{str(datetime.datetime.now())}'[0:-3]
    with open(LOG_FN, 'a') as log:
        out_line = f'{time_str} {level} SRV {frame.f_lineno} {msg}'
        log.write(out_line + '\n')
        if tb is not None:
            log.write('\n'.join(traceback.format_tb(tb)) + '\n')
        log.flush()


#------------------------------------------------------------------------------
def breakpoint():
    '''Opens a remote PDB. See test_pdb.py.'''
    ppdb = PbotPdb()
    ppdb.breakpoint(sys._getframe().f_back)
