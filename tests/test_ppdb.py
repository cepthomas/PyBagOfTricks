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
        code = 0
        with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
            # Capture output from new process.
            t = threading.Thread(target=self.read_handle, args=(proc.stdout,))
            t.start()

            self.l.debug('--> target running')

            # Send some commands.
            commands = ['w', 'l', 'n']
            # icmd = 0
            retries = 5
            scmd = commands.pop(0)

            while len(commands) > 0 and retries > 0 and code == 0:
                self.l.debug(f'send_cmd() {scmd} {len(commands)} {retries}')
                resp = self.send_cmd(scmd)
                # t = type(resp)
                t = resp
                self.l.debug(f'send_cmd() resp [{resp}] [{t}]')
                if t is str:
                    # Good response. Save and do next cmd.
                    self.q.put(resp)
                    if len(commands) > 0:
                        scmd = commands.pop(0)
                elif t is None:
                    # Failed/timeout.
                    retries -= 1
                    time.sleep(0.2) # Delay a bit
                elif t is KeyboardInterrupt:
                    # User ended.
                    self.l.debug(f'Keyboard => EXIT')
                else:
                    self.l.error(f'Unknown type [{resp}]')
                    code = 1
                    # sys.exit(1)

        # Try normal exit the debugger.
        resp = self.send_cmd('q')
        self.q.put(resp or 'Exit failed')
        # time.sleep(0.2)
        # proc.kill()

        # Examine generated contents
        while not self.q.empty():
            self.l.debug(f'QUE [{self.q.get()}]', readable=True)

        # Stop
        self.l.info('exit')
        self.l.stop()

    #------------------------------------------------------------------
    def send_cmd(self, scmd, timeout=1):
        '''Send one command and return response. Normal is string; None if timed out or broken conn; Exception if error.'''
        self.l.debug(f'CMD [{scmd}]')

        resp = None

        # Connect socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                # sock.settimeout(timeout)
                sock.connect((_host, _port))
                # Didn't raise so connect was successful.
                self.l.debug('--- Connected to server')
                with sock.makefile('rw') as commif:
                    # Send cmd.
                    self.l.debug(f'--- send [{scmd}]')
                    commif.write(scmd)
                    commif.flush()
                    # Get server response.
                    self.l.debug(f'--- before read')
                    resp = commif.read(8096) # Known to be > max resp
                    self.l.debug(f'--- after read [{resp}]')
                    commif.close()

            except TimeoutError:
                resp = None
                self.l.debug(f'--- 210 TimeoutError')

            except ConnectionError as e:
                resp = None
                self.l.debug(f'--- 220 {type(e)}')
                # <class 'ConnectionRefusedError'> [[WinError 10061] No connection could be made because the target machine actively refused it]

            except Exception as e:
                self.l.debug(f'Other exception [{type(e)}] [{e}]')
                resp = e

            sock.close()

        self.l.debug(f'RSP [{resp}]')
        return resp

    #------------------------------------------------------------------
    def read_handle(self, out_pipe):
        '''Read process output stream.'''
        for line in iter(out_pipe.readline, b''):
            self.q.put(line.decode())
        #?? out_pipe.close()


#------------------------------------------------------------------------------
if __name__ == '__main__':
    print('Bad! Use python -m unittest test_ppdb.py')
    sys.exit(1)
