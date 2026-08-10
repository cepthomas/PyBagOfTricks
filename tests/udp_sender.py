import sys
import socket
import os
import importlib
import random
import time

# Add path to logger.
npath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if npath not in sys.path:
    sys.path.insert(0, npath)
import plog

# Where to log. Usually same as the server log. None indicates no logging.
LOG_FN = os.path.join(os.path.dirname(__file__), '..', 'log', 'tcp_client.log')

HOST = '127.0.0.1' # 'localhost'
PORT = 59140
# Delimiter for message lines. LF=10  CR=13  NUL=0
MDEL = '\u000A'
TIMEOUT = 5

seq_num = 0


lines = []
with open('ross_1.txt') as f:
    lines = f.readlines()



# Send function.
def send(msg):
    global seq_num
    seq_num = seq_num + 1
    msg = f'[{seq_num}]{msg}'

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            msg = f'{msg}{MDEL}'
            udp_socket.sendto(msg.encode('utf-8'), (HOST, PORT))

    except Exception as e:
        plog.error("An error occurred", e)


# Wait until we are told to go.
exit = False
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    if TIMEOUT > 0:
        sock.settimeout(TIMEOUT)  # Seconds.
    plog.debug(f'UDP on {HOST}:{PORT} [{TIMEOUT}]')

    while not exit:
        try:
            data, _ = sock.recvfrom(4096) # blocks
            msg = data.decode('utf-8')
            plog.debug(f'Received message: {msg}')

            if msg == 'GO':
                # outer loop
                for i in range(5):
                    # inner loop
                    for j in range(5):
                        r =  random.randrange(0, len(lines))
                        send(lines[r].rstrip())
                        time.sleep(0.05)
                    time.sleep(0.2)
                exit = True

        except (ConnectionError, socket.timeout) as e:
            plog.debug(f'ConnectionError timeout')
            # future use
            time.sleep(5)

        except Exception as e:
            plog.debug(f'CommIf.readline() exception: {str(e)}')
            raise # hard fail
