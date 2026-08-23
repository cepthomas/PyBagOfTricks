import sys
import os
import bdb
import unittest
import subprocess
import queue
import socket
import threading
import helpers as h
h.add_parent_to_path()
import pbot_pdb
import plog


#-----------------------------------------------------------------------------------
class TestPbotPdb(unittest.TestCase):

    def setUp(self):
        # Logging.
        self.log_fn = h.init_log(h.my_dir(), 'out', 'test_ppdb.log', clean=True)
        self.ppdb_log_fn = h.init_log(h.my_dir(), 'out', 'pbot_pdb.log', clean=True)
        plog.init('PTST', self.log_fn)
        plog.enable(True)

        # self.captured = []
        self.q = queue.Queue()

    def tearDown(self):
        plog.stop()

    #---------------- Breakpoint test code ----------------------------
    # Target test code below.
    def function2(self, arg):
        x = 111
        y = 22
        return arg + x + y

    def function1(self, arg):
        # Set a breakpoint here then step through and examine the code.
        plog.info('function1 set bp')
        pbot_pdb.breakpoint(59120, log_fn=self.ppdb_log_fn, use_color=False) # turn off color for unit test
        plog.info('function1 done bp')
        return self.function2(len(arg))

    # def go(self, edit):
    #     del edit
    def go(self):
        plog.info('go() enter')

        # Benign reload in case of edited.
        # importlib.reload(pbot_pdb)

        # Run some test code.
        self.function1('ABCD')
        plog.info('go() exit')


    #------------------------------------------------------------------
    def test_ppdb_tcp(self):
        '''Tests the basic tcp cmd/resp protocol.'''

        commif = None
        self.q.empty()

        plog.info('test_ppdb_tcp() enter')

        # Run the simulated client. It waits until breakpoint is hit.
        fc = os.path.join(h.my_dir(), 'sim_client.py')
        args = ['python', fc]  # ['python', fc, '59120', 'w', 'l', 'n']

        # TODO1 with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:#, cwd=working_dir)
        self.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)#, cwd=working_dir)
        self.killed = False
        t = threading.Thread(target=self.read_handle, args=(self.proc.stdout,))
        t.start()

        plog.info('--- client running')

        # Run the code under test which executes breakpoint().
        plog.info('try go')
        try:
            self.go()
        except Exception as e:
            plog.info(f'exception [{e}]')

        # Examine generated contents
        while not self.q.empty():
            plog.info(f'SIM said [{self.q.get()}]')

        # Stop
        plog.info('exit')
        plog.stop()

        if commif is not None:
            commif.close()
            commif = None


    #------------------------------------------------------------------
    # 2) Read process output stream
    def read_handle(self, handle):
        chunk_size = 256
        # chunk_size = 2 ** 13 # 8192
        out = b'' # bytes objects actually behave like immutable sequences of integers

        while True:
            try:
                # Save the received data.
                data = os.read(handle.fileno(), chunk_size)
                out += data

                # Full buffer read. Go around.
                if len(data) == chunk_size:
                    continue

                # No data received. Standard timeout.
                if data == b'' and out == b'':
                    raise IOError('EOF')

                # Message complete. Save message received.
                smsg = out.decode() # default = utf8 self.encoding)
                # self.captured.append(smsg)
                self.q.put(smsg)

                # Message complete?
                if data == b'':
                    raise IOError('EOF')

                # Not yet.
                out = b''

                # # We pass out to a function to ensure the timeout gets the value of out right now,
                # # rather than a future (mutated) version
                # self.queue_write(out.decode(self.encoding))
                # if data == b'':
                #     raise IOError('EOF')
                # out = b''

            # except (UnicodeDecodeError) as e:
            #     msg = 'Error decoding output using %s - %s'
            #     self.queue_write(msg  % (self.encoding, str(e)))
            #     break

            except (IOError):
                if self.killed: # ???
                    msg = 'Cancelled'
                else:
                    msg = 'Finished'
                # self.queue_write('\n[%s]' % msg)
                break



# ###### TODO1 or like this?
# q = queue.Queue()

# def enqueue_output(out_pipe, q):
#     for line in iter(out_pipe.readline, b''):
#         q.put(line)
#     out_pipe.close()

# # Launch process + thread.
# proc = subprocess.Popen(['ping', '127.0.0.1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# t = threading.Thread(target=enqueue_output, args=(proc.stdout, q))
# # t.daemon = True
# t.start()

# # Read non-blocking data from the queue elsewhere in your app
# try:
#     while True:
#         line = q.get_nowait()
#         print(line.decode('utf-8').strip())
# except queue.Empty:
#     pass




#------------------------------------------------------------------------------
if __name__ == '__main__':
    print('Error! Use python -m unittest <testfile.py>')
    sys.exit(1)
