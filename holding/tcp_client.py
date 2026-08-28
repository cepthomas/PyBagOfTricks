import sys
import os
import time
import socket
import threading
import queue
import datetime
import traceback
import helpers as h
h.add_parent_to_path()
import plog


##### Generic TCP Client
# - Automatically connects to the server. This means that you can edit/run your code
#   without having to restart the client.
# - Detects unresponsive server by requiring a response for each command sent.
# - Provides some extra system status information, indicated by `!`.
# - Optionally edit the configuration block in this file.


# TCP host.
_host = '127.0.0.1'

# TCP port
_port = 59120


#------------------------------------------------------------------------------
class GenericTcpClient(object):

    def __init__(self):
        '''Construction.'''

        # Where to log. None indicates no logging.
        log_fn = h.init_log(h.my_dir(), '..', 'log', 'tcp_client.log')
        self.l = plog.Plog('TCPC', log_fn, keep_open=False)
        self.l.enable(True)

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

        self.l.debug(f'Constructing client')

    def go(self):
        '''Run the main loop.'''
        try:
            s = f'Starting client on {_host}:{_port}'
            self.l.info(s)
            self.tell_user(s)
            run = True

            ##### Run user cli input in a thread.
            def worker():
                while run:
                    self.cmd_queue.put_nowait(sys.stdin.readline().replace('\n', ''))
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
                        self.sock.connect((_host, _port))

                        # Didn't fault so must be success.
                        self.commif = self.sock.makefile('rw')
                        s = 'Connected to server'
                        self.l.info(s)
                        self.tell_user(s)

                    except TimeoutError:
                        # Server is not running or not listening right now. Normal operation.
                        timed_out = True
                        self.reset()

                    except ConnectionError as e:
                        # BrokenPipeError, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError.
                        # Ignore and retry later.
                        self.l.debug(f'ConnectionError: {type(e)}')
                        self.reset()

                    except Exception as e:
                        # Other unexpected error.
                        s = f'unexpected'
                        self.l.error(s, e)
                        self.tell_user(s)

                ##### Check for server not responding but still connected. #####
                if self.commif is not None and self.sendts > 0:
                    dur = self.get_msec() - self.sendts
                    if dur > self.server_response_time:
                        s = 'Server not listening'
                        self.l.info(s)
                        self.tell_user(s)
                        self.reset()

                ##### Anything to send? Check for user input. #####
                while not self.cmd_queue.empty():
                    s = self.cmd_queue.get()

                    if self.commif is not None:
                        # self.do_debug(f'Send command: {self.make_readable(s)}')
                        self.commif.write(s + '\n')
                        self.commif.flush()
                        # Measure round trip for timeout.
                        self.sendts = self.get_msec()
                    else:
                        s = 'Execute command failed - not connected'
                        self.l.info(s)
                        self.tell_user(s)

                ##### Get any server responses. #####
                if self.commif is not None:
                    try:
                        # Don't block.
                        self.sock.settimeout(0)

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
                        s = f'wtf'
                        self.l.error(s, e)
                        self.tell_user(s)

                ##### If there was no timeout, delay a bit. #####
                slp = (float(self.loop_time) / 1000.0) if timed_out else 0
                time.sleep(slp)

            self.l.debug('go() run ended')

        except KeyboardInterrupt:
            # Hard shutdown, ignore and quit.
            pass

        except Exception as e:
            # Other unexpected errors.
            s = f'other'
            self.l.error(s, e)
            self.tell_user(s)

        self.quit(0)

    def tell_user(self, msg):
        '''Tell user something.'''
        sys.stdout.write(f'! {msg}\n')

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
    client = GenericTcpClient()
    client.go()
