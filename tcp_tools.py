import sys
import os
import datetime
import traceback
import socket
import socketserver


# Configure.
HOST = 'localhost'
PORT = 59120
MAX_MSG = 10000
ERR = '\u001b[91m'
INFO = '\u001b[96m'
ENDC = '\u001b[0m'


########## TCP Server ##########
# Uses file-like object - rfile and wfile. Socket will be auto closed.
class LineHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.data = self.rfile.readline(MAX_MSG).rstrip()
        ###### customize here ######
        print(f'{INFO}RCV [{self.data.decode('utf-8')}] from {self.client_address[0]}{ENDC}')
        self.wfile.write(self.data.upper())

# Custom server.
class MyServer(socketserver.TCPServer):

    ## Custom error handling for application errors.
    def handle_error(self, request, client_address):
        print(f'{ERR}Error in application:')
        import traceback
        traceback.print_exc()
        print(ENDC)

    def server_close(self):
        print(f"Server closing")

##### Run the server. #####
if __name__ == '__main__':
    with MyServer((HOST, PORT), LineHandler) as server:
        print(f'Server start')
        try:
            server.serve_forever() # polls at 0.5 sec. timeout not used.

        except Exception as e1: # should never happen
            print(f'{ERR}Error in application: {type(e1)}{ENDC}')

        except BaseException as e2: # normal exit: SystemExit, KeyboardInterrupt, GeneratorExit
            print(f'Exit: {type(e2)}')


########## TCP Client ##########
def write_remote(msg):
    # Create a TCP client socket.
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    MDEL = '\n'

    try:
        # Connect to the server
        client_socket.connect((HOST, PORT))
        print(f"Connected to server at {HOST}:{PORT}")

        # Send it.
        msg = f'{msg}{MDEL}'
        client_socket.sendall(msg.encode('utf-8'))

    except ConnectionRefusedError:
        # print(f"Error: Connection refused. Is the server running on {HOST}:{PORT}?")
        pass

    except Exception as e:
        # print(f"An error occurred: {e}")
        pass

    finally:
        # Close the socket
        client_socket.close()
        # print("Connection closed.")

