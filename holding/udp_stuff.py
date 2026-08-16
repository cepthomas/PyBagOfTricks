import sys
import socket
import pdb
import os
import datetime
import traceback
import shutil
import threading
import time
import pbot_pdb
import plog


# Some experiments with using UDP for the remote pdb protocol.

### Required
PORT = -1

### Optional.
HOST = '127.0.0.1'

# Where to log or None.
LOG_FN = None

# Translate non-ascii content.
XLAT = {}

# Ansi color (https://en.wikipedia.org/wiki/ANSI_escape_code)
USE_COLOR = False
CURRENT_LINE_COLOR = 93 # yellow
EXCEPTION_LINE_COLOR = 92 # green
STACK_LOCATION_COLOR = 96 # cyan
PROMPT_COLOR = 94 # blue
ERROR_COLOR = 91 # red

# Simple failure detection.
SEQ_NUM = True


### pbot_pdb.py implementation.
class CommIfUdp(object):
    '''
    Read/write interface to socket. Makes socket look like a file object.
    Also handles encoding, color, line endings etc.
    '''

    def __init__(self):
        '''Construction.'''
        self._last_cmd = None
        # Collected parts of pdb write.
        self._pdbBuff = ''
        # Simple packet loss detection.
        self._seq_num = 0;
        self._encoding = 'utf-8'


    def close(self):
        pass

    # --------------- Required interface ---------------
    # per https://docs.python.org/3/library/io.html#io.TextIOBase

    @property
    def encoding(self):
        return self._encoding

    def readline(self, size=1):
        '''Core pdb calls this to read from cli/client. Returns the valid user command.'''
        del size
        msg = None
        exit = False

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((HOST, PORT))
            sock.settimeout(5)  # Seconds.
            self.debug(f'UDP on {HOST}:{PORT}')

            while msg is None and not exit:
                try:
                    data, _ = sock.recvfrom(4096) # blocks
                    msg = data.decode(self._encoding)
                    self.debug(f'Received message: {msg}')

                    if SEQ_NUM:
                        pass
                        # TODO strip seq number from front '[99]' and check if it's expected

                    self._last_cmd = msg
                    return msg

                except KeyboardInterrupt as e:
                    self.debug(f'KeyboardInterrupt')
                    self._pdbBuff = ''
                    exit = True # orderly shutdown

                except (ConnectionError, socket.timeout) as e:
                    self.debug(f'ConnectionError timeout')

                except Exception as e:
                    self.debug(f'UdpIf.readline() other exception: {str(e)}')
                    self._pdbBuff = ''
                    raise # hard fail

                # finally:
                #     sock.close()

    def write(self, line):
        '''Core pdb calls this to write to cli/client. This adjusts and sends to socket.'''
        try:
            # pdb writes lines piecemeal but we want full proper lines. Presumes core is handling NLs.
            # Easiest is to accumulate in a buffer until we see the prompt then slice and write. TODO some common with TCP.
            if '(Pdb)' in line:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                    for s in self._pdbBuff.splitlines():
                        # sc.self.debug(f'DBG Send response: {s}')
                        color = None

                        if USE_COLOR:
                            if s.startswith('-> '): color = CURRENT_LINE_COLOR
                            elif ' ->' in s: color = CURRENT_LINE_COLOR
                            elif s.startswith('>> '): color = EXCEPTION_LINE_COLOR
                            elif '***' in s: color = ERROR_COLOR
                            elif 'Error:' in s: color = ERROR_COLOR
                            elif s.startswith('> '): color = STACK_LOCATION_COLOR

                        msg = f'{s}' if color is None else f'\u001b[{color}m{s}\u001b[0m'
                        if SEQ_NUM:
                            self.seq_num = self._seq_num + 1
                            msg = f'[{self._seq_num}]{msg}'
                        udp_socket.sendto(msg.encode(self._encoding), (HOST, PORT))
                        self.debug(f'write(): {msg}')
                        print('---', f'write(): {msg}')

                    # Write prompt.
                    msg = f'\u001b[{PROMPT_COLOR}m(Pdb)\u001b[0m\n' if USE_COLOR else '(Pdb)\n'
                    udp_socket.sendto(msg.encode(self._encoding), (HOST, PORT))
                    self.debug(f'write(): {msg}')
                    print('---', f'write(): {msg}')

                    # Reset buffer.
                    self._pdbBuff = ''
            else:
                # Just collect.
                self._pdbBuff += line

        except Exception as e:
            # ?? (ConnectionError, socket.timeout)
            self.debug(f'UdpIf.write() other exception: {str(e)}')
            self._pdbBuff = ''
            raise

    # read(size=-1, /) not needed?
    #     Read and return at most size characters as str. If size is negative or None, reads until EOF.

    def flush(self):
        pass

    def debug(self, msg):
        pass



### test_ppdb.py implementation.

def test_udp(self):
    print('>>>', 'test_udp() enter')
    plog.info('test_udp() enter')

    ### Configure ppdb. ###
    # pbot_pdb.MODE = 'UDP'
    pbot_pdb.PORT = 59140
    pbot_pdb.LOG_FN = os.path.join(os.path.join(os.path.dirname(__file__), 'out', 'pbot_pdb.log'))

    ### Run simulated remote client in a thread. ###
    def worker():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp_socket.bind((pbot_pdb.HOST, pbot_pdb.PORT))
            udp_socket.settimeout(0.1)  # Seconds.
    
            print('>>>', 'worker start')

            commands = ['w', 'l', 'n']
            cind = 0
            run = True
            send_next = True # state
            while run:
                try:
                    if send_next: # ppdb is waiting for next client/user command.
                        smsg = commands[cind]
                        plog.debug(f'worker send message: {smsg}')
                        print('>>>', f'worker send message: {smsg}')
                        udp_socket.sendto(smsg.encode('utf-8'), (pbot_pdb.HOST, pbot_pdb.PORT))
                        cind += 1
                        send_next = False
                    else:
                        # Listening for something ppdb sends.
                        rdata, _ = udp_socket.recvfrom(4096) # blocks
                        rmsg = rdata.decode('utf-8')
                        plog.debug(f'worker received message: {rmsg}')
                        print('>>>', f'worker received message: {rmsg}')

                        if rmsg.startswith('(Pdb)'):
                            # ppdb is waiting for next client/user command.
                            if cind < len(commands):
                                send_next = True
                            else:
                                # all done
                                run = False

                except (ConnectionError, socket.timeout) as e:
                    # Just try again.
                    time.sleep(5)

                except Exception as e:
                    plog.error('Unexpected', e)
                    print('>>>', 'worker Unexpected', e)
                    # self._debug(f'CommIf.readline() exception: {str(e)}')
                    raise # hard fail
        print('>>>', 'worker end')
    threading.Thread(target=worker, daemon=True).start()

    ### Run the test code. ###
    plog.info('Run the test code')
    print('>>>', 'Run the test code')
    # Target to taste:
    # t = MyTestClass()
    # t.go()

    ### Examine generated contents. ###
    plog.info('Examine generated contents')
    print('>>>', 'Examine generated contents')
    plog.stop()
    lines = []
    with open(self.log_fn) as f:
        lines = f.readlines()
    self.assertEqual(len(lines), 42)
    # plog.info('exit')
