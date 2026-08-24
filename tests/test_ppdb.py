import sys
import os
import bdb
import unittest
import subprocess
import queue
import socket
import threading
import time
import helpers as h
h.add_parent_to_path()
import plog


_host = '127.0.0.1'
_port = 59120


#-----------------------------------------------------------------------------------
class TestPbotPdb(unittest.TestCase):

    def setUp(self):
        # Logging.
        self.log_fn = h.init_log(h.my_dir(), 'out', 'test_ppdb.log', clean=True)
        self.l = plog.Plog('TEST', self.log_fn)
        self.l.enable(True)

        self.q = queue.Queue()

    def tearDown(self):
        self.l.stop()


    #------------------------------------------------------------------
    def test_ppdb_tcp(self):
        '''Tests the tcp cmd/resp protocol.'''
        self.q.empty()
        self.l.info('test_ppdb_tcp() enter')

        # Run the target code which executes breakpoint() and waits.
        fc = os.path.join(h.my_dir(), 'target.py')
        args = ['python', fc]
        with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc: #, cwd=working_dir)
            self.killed = False
            t = threading.Thread(target=self.read_handle, args=(proc.stdout,))
            t.start()

            self.l.info('--- target running')

            # Send some commands.



# commands = ['w', 'l', 'n']
# cind = 0
# run = True
# send_next = True # state
# while run:
#     try:
#         if send_next: # ppdb is waiting for next client/user command.
#             smsg = commands[cind]

# commands = ['w', 'l', 'n']
# while len(commands) > 0:
#     try:
#         scmd = commands.pop(0)
#         sresp = do_one(scmd)
#         time.sleep(0.2) # Delay a bit
#     except (KeyboardInterrupt) as e:
#         l.info(f'Keyboard => EXIT')
#         sys.exit(0)
#     except (Exception) as e:
#         l.info(f'{type(e)} [{e}] => EXIT')
#         sys.exit(1)
#     finally:
#         l.info(f'finally => EXIT')








            sresp = self.send_cmd('w')

            sresp = self.send_cmd('l')

            sresp = self.send_cmd('s')

        # Exit the debugger.
        sresp4 = self.send_cmd('q')
        time.sleep(0.2)
        self.killed = True
        # time.sleep(0.2)
        # proc.kill()

        # Examine generated contents
        while not self.q.empty():
            self.l.debug(f'QUE [{self.q.get().decode()}]', readable=True)

        # Stop
        self.l.info('exit')
        self.l.stop()

    #------------------------------------------------------------------
    def send_cmd(self, scmd, timeout=1):
        '''Send one command and return response string; None if timed out or broken conn; Exception if other.'''
        self.l.debug(f'CMD [{scmd}]')

        resp = None

        # Connect socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

            try:
                sock.settimeout(timeout)
                sock.connect((_host, _port))
                # Didn't raise so connect was successful.
                self.l.debug('--- Connected to server')
                with sock.makefile('rw') as commif:
                    # Send cmd.
                    commif.write(scmd)
                    commif.flush()
                    # Get server response.
                    sock.settimeout(1) # adjust to taste
                    sresp = commif.read(8096) # Known to be > max resp
                    commif.close()

            except TimeoutError:
                resp = None
                # self.l.debug(f'--- 210 TimeoutError')

            except ConnectionError as e:
                resp = None
                # self.l.debug(f'--- 220 {type(e)} Shouldnt happen')
                # <class 'ConnectionRefusedError'> [[WinError 10061] No connection could be made because the target machine actively refused it]

            except Exception as e:
                self.l.debug(f'Other exception [{type(e)}] [{e}]')
                resp = e

            sock.close()

        self.l.debug(f'RSP [{resp}]')
        return resp


    #------------------------------------------------------------------
    def send_cmd_orig(self, scmd, timeout=1):
        '''Send one command and return response string or None if fail.'''

        sock = None
        commif = None
        sresp = None

        try:
            self.l.info(f'CMD [{scmd}]') #1

            # Connect socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((_host, _port))

            # Didn't raise so connect was successful.
            commif = sock.makefile('rw')
            self.l.info('--- Connected to server')

            commif.write(scmd)
            commif.flush()

            # Get server response.
            sock.settimeout(1) # adjust to taste

            self.l.info(f'--- 100')
            sresp = commif.read(8096) # Known to be > max resp
            self.l.info(f'--- 200 [{sresp}]')

        except TimeoutError: # Shouldn't happen.
            self.l.info(f'--- 210 TimeoutError Shouldnt happen')

        except ConnectionError as e:
            self.l.info(f'--- 220 {type(e)} Shouldnt happen')
            # <class 'ConnectionRefusedError'> [[WinError 10061] No connection could be made because the target machine actively refused it]

        except Exception as e:
            self.l.info(f'Other exception [{type(e)}] [{e}]')
            # sresp = f'ERR {type(e)}'

        finally:
            # Explicit close connection.
            self.l.info(f'finally => EXIT')
            if commif is not None: commif.close()
            if sock is not None: sock.close()
            self.l.info(f'RSP [{sresp}]')
            return sresp

    #------------------------------------------------------------------
    def read_handle(self, out_pipe):
        '''Read process output stream.'''

        for line in iter(out_pipe.readline, b''):
            self.q.put(line) #line.decode())
        #?? out_pipe.close()


#------------------------------------------------------------------------------
if __name__ == '__main__':
    print('Bad! Use python -m unittest test_ppdb.py')
    sys.exit(1)
