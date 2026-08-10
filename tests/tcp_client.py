import sys
import os
import time
import socket
import threading
import queue
import datetime
import traceback

# Add path to logger.
npath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if npath not in sys.path:
    sys.path.insert(0, npath)
import plog


# TCP client that is pbot_pdb.py aware.

# Fancy Client
# Optionally you can use the smarter `pbot_pdb_client.py` script which does all of the above plus:
# - Automatically connects to the server. This means that you can edit/run your code
#   without having to restart the client.
# - Detects unresponsive server by requiring a response for each command sent.
# - Provides some extra system status information, indicated by `!` (or marker of your choosing).
# - Workflow is similar to the above except you can now reload/run the code as part of your dev/edit cycle.
# - Optionally edit the configuration block in this file.
# - Use ctrl-C to exit the client. The server will also stop/unblock.
# ![Fancy Client](cli2.png)

# Where to log. Usually same as the server log. None indicates no logging.
LOG_FN = os.path.join(os.path.dirname(__file__), '..', 'log', 'tcp_client.log')

# TCP host.
HOST = '127.0.0.1'

# TCP port
PORT = 59120

# Delimiter for socket message lines.
MDEL = '\u000A' # NL


#------------------------------------------------------------------------------
class PbotPdbClient(object):
    '''The remote pdb client.'''

    def __init__(self):
        '''Construction.'''
        plog.init('TCPC', LOG_FN, readable=True)
        plog.setEnable(True)

        self.sock = None
        self.commif = None

        # Human polling time in msec.
        self.loop_time = 50

        # Server must reply to client in msec or it's considered dead.
        self.server_response_time = 200  # 100?

        # User command read queue.
        self.cmd_queue = queue.Queue()

        # Last command time. Non zero implies waiting for a response.
        self.sendts = 0

        plog.debug(f'Constructing client')

    def go(self):
        '''Run the main loop.'''

        try:
            plog.info(f'Starting client on {HOST}:{PORT}')
            run = True

            ##### Run user cli input in a thread.
            def worker():
                while run:
                    self.cmd_queue.put_nowait(sys.stdin.readline().replace(MDEL, ''))
            threading.Thread(target=worker, daemon=True).start()

            ##### Forever loop #####
            while run:
                timed_out = False

                ##### Try (re)connecting? #####
                if self.commif is None:
                    # TCP socket client
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    # Block with timeout.
                    self.sock.settimeout(float(self.server_response_time) / 1000.0)

                    try:
                        self.sock.connect((HOST, PORT))

                        # Didn't fault so must be success.
                        self.commif = self.sock.makefile('rw')
                        plog.info('Connected to server')

                    except TimeoutError:
                        # Server is not running or not listening right now. Normal operation.
                        timed_out = True
                        self.reset()

                    except ConnectionError as e:
                        # BrokenPipeError, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError.
                        # Ignore and retry later.
                        plog.debug(f'ConnectionError: {type(e)}')
                        self.reset()

                    except Exception as e:
                        # Other unexpected error.
                        plog.error('unexpected', e)

                ##### Check for server not responding but still connected. #####
                if self.commif is not None and self.sendts > 0:
                    dur = self.get_msec() - self.sendts
                    if dur > self.server_response_time:
                        plog.info('Server not listening')
                        self.reset()

                ##### Anything to send? Check for user input. #####
                while not self.cmd_queue.empty():
                    s = self.cmd_queue.get()

                    if self.commif is not None:
                        # self.do_debug(f'Send command: {self.make_readable(s)}')
                        self.commif.write(s + MDEL)
                        self.commif.flush()
                        # Measure round trip for timeout.
                        self.sendts = self.get_msec()
                    else:
                        plog.info('Execute command failed - not connected')

                ##### Get any server responses. #####
                if self.commif is not None:
                    try:
                        # Don't block.
                        self.sock.settimeout(0)  # pyright: ignore

                        done = False
                        while not done:
                            s = self.commif.read(100)

                            if s == '':
                                done = True
                            else:
                                sys.stdout.write(s)
                                sys.stdout.flush()
                                # self.do_debug(self.make_readable(s))
                                # Reset watchdog.
                                self.sendts = 0

                    except TimeoutError:
                        # Nothing to read.
                        timed_out = True
                        self.reset()

                    except ConnectionError:
                        # Server disconnected.
                        self.reset()

                    except Exception as e:
                        plog.error('wtf', e)

                ##### If there was no timeout, delay a bit. #####
                slp = (float(self.loop_time) / 1000.0) if timed_out else 0
                time.sleep(slp)

            plog.debug('go() run ended')

        except KeyboardInterrupt:
            # Hard shutdown, ignore and quit.
            pass

        except Exception as e:
            # Other unexpected errors.
            plog.error('other', e)

        self.quit(0)

    def get_msec(self):
        '''Get current msec.'''
        return time.perf_counter_ns() / 1000000

    def reset(self):
        '''Reset comms, resource management.'''

        if self.commif is not None:
            self.commif.close()
            self.commif = None

        if self.sock is not None:
            self.sock.close()
        #     self.sock = None

        # Reset watchdog.
        self.sendts = 0
        # Clear queue.
        while not self.cmd_queue.empty():
            self.cmd_queue.get()

    def quit(self, code):
        '''Clean up and go home.'''
        self.reset()
        if self.sock is not None:
            self.sock.close()
            self.sock = None
        sys.exit(code)


#------------------------------------------------------------------------------
if __name__ == '__main__':
    client = PbotPdbClient()
    client.go()
