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


##### Dumb test client.


_host = '127.0.0.1'
_port = 59120

# Logging.
log_fn = h.init_log(h.my_dir(), 'out', 'sim_client.log', clean=True)
l = plog.Plog('SIMC', log_fn)
l.enable(True)
l.info(f'Starting client on {_host}:{_port}')
# for a in sys.argv: l.info(f'arg [{a}]')


def do_one(scmd):

    sock = None
    commif = None
    sresp = None

    try:
        l.info(f'CMD [{scmd}]')

        # Connect socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((_host, _port))
        # Didn't fault so must be success.
        commif = sock.makefile('rw')
        l.info('Connected to server')

        commif.write(scmd)
        commif.flush()
        l.info(f'--- 100')

        # Get server response.
        l.info(f'--- 110')
        sock.settimeout(1) # adjust to taste
        receiving = True
        while receiving:
            try:
                s = commif.read(256)
                l.info(f'--- 200 [{s}]')
                if sresp is None: sresp = s
                else: sresp += s
            except TimeoutError: # Nothing more to read.
                l.info(f'--- 210')
                receiving = False

    except Exception as e:
        l.info(f'{type(e)} [{e}]')
        # sresp = f'ERR {type(e)}'

    finally:
        l.info(f'finally => EXIT')
        if commif is not None: commif.close()
        if sock is not None: sock.close()
        l.info(f'RSP [{sresp}]')
        return sresp


# Start loop here.
commands = ['w', 'l', 'n']

while len(commands) > 0:
    try:
        scmd = commands.pop(0)
        sresp = do_one(scmd)
        time.sleep(0.2) # Delay a bit

    except (KeyboardInterrupt) as e:
        l.info(f'Keyboard => EXIT')
        sys.exit(0)

    except (Exception) as e:
        l.info(f'{type(e)} [{e}] => EXIT')
        sys.exit(1)

    finally:
        l.info(f'finally => EXIT')


sys.exit(0)
