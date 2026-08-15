import sys
import os
import time
import socket
import threading
import queue
import datetime
import traceback


HOST = '127.0.0.1'
PORT = 59120


#------------------------------------------------------------------------------
class AutoTcpClient(object):

    def __init__(self):
        '''Construction.'''
        self.sock = None
        self.commif = None

        # Human polling time in msec.
        # self.loop_time = 50

        # # Server must reply to client in msec or it's considered dead.
        # self.server_response_time = 200  # 100?

        # # User command read queue.
        # self.cmd_queue = queue.Queue()

        # # Last command time. Non zero implies waiting for a response.
        # self.sendts = 0

        # plog.debug(f'Constructing client')

    def tell(self, msg):
        sys.stdout.write(f'{msg}\n')

    def go(self):
        '''Run the sequence.'''
        capture = []
        try:
            self.tell(f'Starting client on {HOST}:{PORT}')

            # TCP socket client
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Block with timeout.
            self.sock.settimeout(5)

            self.sock.connect((HOST, PORT))

            # Didn't fault so must be success.
            self.commif = self.sock.makefile('rw')
            self.tell('Connected to server')

            # Anything to send? Check for user input.
            commands = ['w', 'l', 'n']
            while len(commands) > 0:

                smsg = commands.pop(0)
                self.commif.write(smsg)# + MDEL)
                self.commif.flush()
                capture.append(f'S {smsg}')

                # Get any server responses.
                self.sock.settimeout(1)
                sresp = ''
                rcving = True
                while rcving:
                    try:
                        s = self.commif.read(100)
                        # Got something.
                        # plog.debug(f'worker received [[[{s}]]]')
                        sresp += s

                    except TimeoutError:
                        # Nothing more to read.
                        rcving = False

                # Process any capture.
                for s in sresp.splitlines():
                    capture.append(f'R {s}')

                # Delay a bit.
                time.sleep(0.1)

        except TimeoutError:
            self.tell('TimeoutError')

        except ConnectionError as e:
            # BrokenPipeError, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError.
            self.tell(f'ConnectionError: {type(e)}')

        except KeyboardInterrupt:
            # Hard shutdown, ignore and quit.
            self.tell('KeyboardInterrupt')

        except Exception as e:
            # Other unexpected error.
            self.tell(f'Other Error: {type(e)}')

        finally:
            if self.commif is not None:
                self.commif.close()
                self.commif = None

            if self.sock is not None:
                self.sock.close()
                self.sock = None

            self.tell('Capture:')
            for s in capture:
                self.tell(s)

            sys.exit(0)


#------------------------------------------------------------------------------
if __name__ == '__main__':
    client = AutoTcpClient()
    client.go()
