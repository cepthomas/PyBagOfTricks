import sys
import socket
import pdb
import os
import datetime
import traceback
import shutil
import pbot_common as com


# ---------------------- Internals ----------------------------------

_log_fn = None


# ---------------------- Socket I/F -------------------------------------
class CommIf(object):
    '''
    Read/write interface to socket. Makes socket look like a file object.
    Also handles encoding, color, line endings etc.
    Catches exceptions for the purpose of logging only. They are re-raised.
    '''

    def __init__(self, conn, use_color):
        self.conn = conn
        self.use_color = use_color
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
            debug(f'Other exception: {str(e)}')
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

                    if self.use_color:
                        if s.startswith('-> '): color = com.current_line_color
                        elif ' ->' in s: color = com.current_line_color
                        elif s.startswith('>> '): color = com.exception_line_color
                        elif '***' in s: color = com.error_color
                        elif 'Error:' in s: color = com.error_color
                        elif s.startswith('> '): color = com.stack_location_color

                    self._send(f'{s}\n' if color is None else f'\033[{color}m{s}\033[0m\n')

                # Write prompt.
                self._send(f'\u001b[{com.prompt_color}m(Pdb)\u001b[0m ' if self.use_color else '(Pdb)')
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
            debug(f'Other exception: {str(e)}')
            self.buff = ''
            raise


#------------------------------------------------------------------------------
class PbotPdb(pdb.Pdb):
    '''Custom pdb using TCP.'''

    # --------------- Construction ---------------
    def __init__(self, port, log_fn, use_color=True):
        '''Construction.'''
        self.host = '127.0.0.1'
        self.port = port
        self.use_color = use_color
        _log_fn = log_fn

        self.sock = None
        self.commif = None

        try:
            # Initialize logging. Maybe roll over log now.
            if _log_fn and os.path.exists(_log_fn) and os.path.getsize(_log_fn) > 50000:
                bup = _log_fn.replace('.log', '_old.log')
                shutil.copyfile(_log_fn, bup)
                # Clear current log file.
                with open(_log_fn, 'w'):
                    pass

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)  # Seconds.
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            self.sock.bind((self.host, self.port))
            info(f'Server started on {self.host}:{self.port} - waiting for connection.')

            # Blocks until client connect or timeout.
            self.sock.listen(1)
            conn, address = self.sock.accept()

            # Connected.
            info(f'Server accepted connection from {repr(address)}.')
            self.commif = CommIf(conn, self.use_color)

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
    if not _log_fn: return

    tb = None if not e else e.__traceback__

    message = com.make_readable(message)

    # Get caller info.
    frame = sys._getframe(2)
    fn = os.path.basename(frame.f_code.co_filename)
    line = frame.f_lineno

    time_str = f'{str(datetime.datetime.now())}'[0:-3]

    # Write the record. TODO1 need thread sync?
    with open(_log_fn, 'a') as log:
        out_line = f'{time_str} {level} PPDB {fn}({line}) {message}'
        log.write(out_line + '\n')
        if tb is not None:
            for tbline in traceback.format_tb(tb):
                for s in tbline.splitlines():
                    log.write(s + '\n')
        log.flush()


#------------------------------ Start here -------------------------------------
def breakpoint(port, log_fn=None, use_color=True):
    '''Opens a remote PDB.'''
    ppdb = PbotPdb(port, log_fn, use_color)
    ppdb.breakpoint(sys._getframe().f_back)
