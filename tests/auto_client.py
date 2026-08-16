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

for a in sys.argv:
    print('a:', a)

#------------------------------------------------------------------------------
class AutoTcpClient(object):

    def __init__(self):
        '''Construction.'''
        self.sock = None
        self.commif = None

    def go(self):

        print('===== Capture')
        run = True

        while run:
            try:
                print(f'Starting client on {HOST}:{PORT}')

                # Connect socket
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Block with timeout.
                self.sock.settimeout(5)
                self.sock.connect((HOST, PORT))

                # Didn't fault so must be success.
                self.commif = self.sock.makefile('rw')
                print('Connected to server')

                # Anything to send? Check for user input.
                commands = ['w', 'l', 'n'] # TODO1? pass as args + port
                while len(commands) > 0:

                    smsg = commands.pop(0)
                    self.commif.write(smsg)
                    self.commif.flush()
                    print(f'CMD [{smsg}]')

                    # Get any server responses.
                    self.sock.settimeout(1)
                    sresp = ''
                    rcving = True
                    while rcving:
                        try:
                            s = self.commif.read(100)
                            # Got something.
                            sresp += s

                        except TimeoutError:
                            # Nothing more to read.
                            rcving = False

                    # Process any capture.
                    for s in sresp.splitlines():
                        print(f'RSP [{s}]')

                    # Delay a bit.
                    time.sleep(0.1)

                    run = False

            except TimeoutError:
                print('TimeoutError')

            except ConnectionError as e:
                # BrokenPipeError, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError.
                print(f'ConnectionError: {type(e)}')

            except KeyboardInterrupt:
                # Hard shutdown, ignore and quit.
                print('KeyboardInterrupt')

            except Exception as e:
                # Other unexpected error.
                print(f'Other Error: {type(e)}')

        if self.commif is not None:
            self.commif.close()
            self.commif = None

        if self.sock is not None:
            self.sock.close()
            self.sock = None

        print(f'=====')

        sys.exit(0)


#------------------------------------------------------------------------------
if __name__ == '__main__':
    client = AutoTcpClient()
    client.go()
