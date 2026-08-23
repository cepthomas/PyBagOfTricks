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

_host = '127.0.0.1'
_port = 59120

# Logging.
_log_fn = h.init_log(h.my_dir(), 'out', 'sim_client.log', clean=True)
plog.init('SIMC', _log_fn)
plog.enable(True)

# for a in sys.argv: plog.info(f'arg [{a}]')


plog.info(f'Starting client on {_host}:{_port}')

def do_one(scmd):

    sock = None
    commif = None
    sresp = None

    try:
        plog.info(f'CMD [{scmd}]')

        # Connect socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((_host, _port))
        # Didn't fault so must be success.
        commif = sock.makefile('rw')
        plog.info('Connected to server')

        commif.write(scmd)
        commif.flush()
        plog.info(f'--- 100')

        # Get server response.
        plog.info(f'--- 110')
        sock.settimeout(1) # adjust to taste
        rcving = True
        while rcving:
            try:
                s = commif.read(256)
                plog.info(f'--- 200 [{s}]')
                if sresp is None: sresp = s
                else: sresp += s
            except TimeoutError: # Nothing more to read.
                plog.info(f'--- 210')
                rcving = False

    except Exception as e:
        plog.info(f'{type(e)} [{e}]')
        # sresp = f'ERR {type(e)}'

    finally:
        plog.info(f'finally => EXIT')
        if commif is not None: commif.close()
        if sock is not None: sock.close()
        plog.info(f'RSP [{sresp}]')
        return sresp


# Start loop here.
commands = ['w', 'l', 'n']

while len(commands) > 0:
    try:
        scmd = commands.pop(0)
        sresp = do_one(scmd)
        time.sleep(0.2) # Delay a bit

    except (KeyboardInterrupt) as e:
        plog.info(f'Keyboard => EXIT')
        sys.exit(0)

    except (Exception) as e:
        plog.info(f'{type(e)} [{e}] => EXIT')
        sys.exit(1)

    finally:
        plog.info(f'finally => EXIT')


sys.exit(0)
# if commif is not None: commif.close()
# if sock is not None: sock.close()

# plog.info(f'RSP [{sresp}]')

# # # Process any capture.
# # for s in sresp.splitlines():
# #     plog.info(f'RSP [{s}]')



# #======================================================
# retries = 0

# while True:
#     sock = None
#     commif = None

#     try:
#         # Anything to send? TODO? pass as args + port
#         commands = ['w', 'l', 'n']
#         while len(commands) > 0:
#             scmd = commands.pop(0)
#             plog.info(f'CMD [{scmd}]')

#             # Connect socket
#             sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             # Block with timeout.
#             sock.settimeout(5)
#             sock.connect((_host, _port))
#             # Didn't fault so must be success.
#             commif = sock.makefile('rw')
#             plog.info('Connected to server')

#             commif.write(scmd)
#             commif.flush()
#             plog.info(f'--- 100')

#             # Get server response.
#             sock.settimeout(1) # adjust to taste
#             plog.info(f'--- 110')
#             sresp = ''
#             rcving = True
#             while rcving:
#                 try:
#                     s = commif.read(256)
#                     plog.info(f'--- 200')
#                     sresp += s
#                 except TimeoutError: # Nothing more to read.
#                     plog.info(f'--- 210')
#                     rcving = False

#             plog.info(f'RSP [{sresp}]')

#             # # Process any capture.
#             # for s in sresp.splitlines():
#             #     plog.info(f'RSP [{s}]')

#             # Delay a bit.
#             time.sleep(0.1)
#         run = False

#     except (TimeoutError, ConnectionError) as e:
#         plog.info(f'{type(e)} [{e}]')
#         retries += 1
#         if retries >= 10:
#             plog.info(f'Too many retries => EXIT')
#             sys.exit(1)
#         # else continue

#     # except (OSError) as e:
#     #     plog.info(f'{type(e)} [{e}]')
#     #     run = False

#     except (KeyboardInterrupt) as e:
#         plog.info(f'Keyboard => EXIT')
#         sys.exit(0)

#     except (Exception) as e:
#         plog.info(f'{type(e)} [{e}] => EXIT')
#         sys.exit(2)

#     finally:
#         plog.info(f'finally => EXIT')
#         if commif is not None: commif.close()
#         if sock is not None: sock.close()
