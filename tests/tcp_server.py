import sys
import os
import datetime
import socketserver

# Simple echoing tcp server for test purposes.


# Configure. Edit for specific test scenarios.
HOST = 'localhost'  # '127.0.0.1'
PORT = 59120
MAX_MSG = 10000
# Delimiter for message lines. LF=10  CR=13  NUL=0
MDEL = '\u000A'

# Colors
ERR  = '\u001b[91m'
INFO = '\u001b[96m'
ENDC = '\u001b[0m'


# Handle one request.
# Uses file-like object - rfile and wfile. Socket will be auto closed.
class LineHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.data = self.rfile.readline(MAX_MSG).rstrip()
        ## >>> customize here
        received = self.data.decode('utf-8')
        print(f'Client sent [{received}]')
        response = f'You sent [{received}]{MDEL}'
        self.wfile.write(response.encode('utf-8'))

# Custom server.
class MyServer(socketserver.TCPServer):
    ## >>> Custom error handling for application errors.
    def handle_error(self, request, client_address):
        print(f'{ERR}Error in application:')
        import traceback
        traceback.print_exc()
        print(ENDC)

    def server_close(self):
        print(f'server_close()')

# Run the server.
with MyServer((HOST, PORT), LineHandler) as server:
    # print(f'Server start')
    try:
        server.serve_forever() # polls at 0.5 sec. timeout not used.

    except Exception as e1: # should never happen
        print(f'{ERR}WTF!!! Error in application: {type(e1)}{ENDC}')

    except BaseException as e2: # normal exits: SystemExit, KeyboardInterrupt, GeneratorExit
        print(f'{ERR}Exception: {type(e2)}{ENDC}')

    finally:
        server.server_close()
        print(f'TCP Goodbye')
