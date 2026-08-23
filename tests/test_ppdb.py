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
        # self.ppdb_log_fn = h.init_log(h.my_dir(), 'out', 'pbot_pdb.log', clean=True)
        self.l = plog.Plog('TEST', self.log_fn)
        self.l.enable(True)

        # self.captured = []
        self.q = queue.Queue()

    def tearDown(self):
        self.l.stop()


    #------------------------------------------------------------------
    def test_ppdb_tcp(self):
        '''Tests the .... tcp cmd/resp protocol.'''

        # commif = None
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

        # if commif is not None:
        #     commif.close()
        #     commif = None

    #------------------------------------------------------------------
    def send_cmd(self, scmd):
        '''Send one command and return response or None if failed.'''

        sock = None
        commif = None
        sresp = None

        try:
            self.l.info(f'CMD [{scmd}]') #1

            # Connect socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((_host, _port))

            # Didn't fault so connect was successful.
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
    # Read process output stream
    def read_handle(self, out_pipe):

        for line in iter(out_pipe.readline, b''):
            self.q.put(line) #line.decode())
        #?? out_pipe.close()

    # #------------------------------------------------------------------
    # def read_handle_s(self, handle):
    #     ''' Read process output stream'''
    #     chunk_size = 256
    #     # chunk_size = 2 ** 13 # 8192
    #     out = b'' # bytes objects actually behave like immutable sequences of integers
    #     while not self.killed:
    #         try:
    #             # Save the received data.
    #             data = os.read(handle.fileno(), chunk_size)
    #             out += data
    #             # Full buffer read. Go around.
    #             if len(data) == chunk_size:
    #                 continue
    #             # No data received. Standard timeout.
    #             if data == b'' and out == b'':
    #                 raise IOError('EOF')
    #             # Message complete. Save message received.
    #             smsg = out.decode() # default = utf8 self.encoding)
    #             # self.captured.append(smsg)
    #             self.q.put(smsg)
    #             # Message complete?
    #             if data == b'':
    #                 raise IOError('EOF')
    #             # Not yet.
    #             out = b''
    #         except (IOError):
    #             if self.killed: # ???
    #                 msg = 'Cancelled'
    #             else:
    #                 msg = 'Finished'
    #             self.q.put(msg)
    #             break


#------------------------------------------------------------------------------
if __name__ == '__main__':
    print('Bad! Use python -m unittest test_ppdb.py')
    sys.exit(1)
