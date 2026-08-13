import sys
import os
import importlib
import unittest
import threading
import socket
import time
import queue
# Insert path to parent dir.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pbot_pdb
import plog

print('>>>', 'load test_ppdb')


MDEL = '\n'


#-----------------------------------------------------------------------------------
class TestPbotPdb(unittest.TestCase):

    def setUp(self):
        print('>>>', 'setUp')
        self.log_fn = os.path.join(os.path.join(os.path.dirname(__file__), 'out', 'test_ppdb.log'))
        try: os.remove(self.log_fn)
        except: pass
        plog.init('PTST', self.log_fn, readable=True)
        plog.enable(True)
        plog.info('=====================================')

        self.sock = None
        self.commif = None

        # Human polling time in msec.
        self.loop_time = 50

        # Server must reply to client in msec or it's considered dead.
        self.server_response_time = 200  # 100?

        # User command read queue.
        self.cmd_queue = queue.Queue()

        # Last command time. Non zero implies waiting for a response.
        self.sendts = 0


    def tearDown(self):
        print('>>>', 'tearDown')
        plog.stop()

    #------------------------------------------------------------------
    def test_tcp(self): # >>>> steal from test_udp
        # Configure ppdb.
        pbot_pdb.PORT = 59120
        pbot_pdb.LOG_FN = os.path.join(os.path.join(os.path.dirname(__file__), 'out', 'pbot_ppdb.log'))

        # Run the main loop.
        try:
            s = f'Starting client on {pbot_pdb.HOST}:{pbot_pdb.PORT}'
            plog.info(s)
            # self.tell_user(s)
            run = True

            ##### Run user cli input in a thread.
            def worker():
                while run:
                    self.cmd_queue.put_nowait(sys.stdin.readline().replace(MDEL, ''))
            threading.Thread(target=worker, daemon=True).start()

            ##### Forever loop #####
            while run:
                timed_out = False

                ##### Try (re)connecting? #####
                if self.commif is None:
                    # TCP socket client
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    # Block with timeout.
                    self.sock.settimeout(float(self.server_response_time) / 1000.0)

                    try:
                        self.sock.connect((pbot_pdb.HOST, pbot_pdb.PORT))

                        # Didn't fault so must be success.
                        self.commif = self.sock.makefile('rw')
                        s = 'Connected to server'
                        plog.info(s)
                        # self.tell_user(s)

                    except TimeoutError:
                        # Server is not running or not listening right now. Normal operation.
                        timed_out = True
                        self.reset()

                    except ConnectionError as e:
                        # BrokenPipeError, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError.
                        # Ignore and retry later.
                        plog.debug(f'ConnectionError: {type(e)}')
                        self.reset()

                    except Exception as e:
                        # Other unexpected error.
                        s = f'unexpected'
                        plog.error(s, e)
                        # self.tell_user(s)

                ##### Check for server not responding but still connected. #####
                if self.commif is not None and self.sendts > 0:
                    dur = self.get_msec() - self.sendts
                    if dur > self.server_response_time:
                        s = 'Server not listening'
                        plog.info(s)
                        # self.tell_user(s)
                        self.reset()

                ##### Anything to send? Check for user input. #####
                while not self.cmd_queue.empty():
                    s = self.cmd_queue.get()

                    if self.commif is not None:
                        # self.do_debug(f'Send command: {self.make_readable(s)}')
                        self.commif.write(s + MDEL)
                        self.commif.flush()
                        # Measure round trip for timeout.
                        self.sendts = self.get_msec()
                    else:
                        s = 'Execute command failed - not connected'
                        plog.info(s)
                        # self.tell_user(s)

                ##### Get any server responses. #####
                if self.commif is not None:
                    try:
                        # Don't block.
                        self.sock.settimeout(0)  # pyright: ignore

                        done = False
                        while not done:
                            s = self.commif.read(100)

                            if s == '':
                                done = True
                            else:
                                sys.stdout.write(s)
                                sys.stdout.flush()
                                # self.do_debug(self.make_readable(s))
                                # Reset watchdog.
                                self.sendts = 0

                    except TimeoutError:
                        # Nothing to read.
                        timed_out = True
                        self.reset()

                    except ConnectionError:
                        # Server disconnected.
                        self.reset()

                    except Exception as e:
                        s = f'wtf'
                        plog.error(s, e)
                        # self.tell_user(s)

                ##### If there was no timeout, delay a bit. #####
                slp = (float(self.loop_time) / 1000.0) if timed_out else 0
                time.sleep(slp)

            plog.debug('go() run ended')

        except KeyboardInterrupt:
            # Hard shutdown, ignore and quit.
            pass

        except Exception as e:
            # Other unexpected errors.
            s = f'other'
            plog.error(s, e)
            # self.tell_user(s)

        self.quit(0)


    def get_msec(self):
        '''Get current msec.'''
        return time.perf_counter_ns() / 1000000

    def reset(self):
        '''Reset comms, resource management.'''

        if self.commif is not None:
            self.commif.close()
            self.commif = None

        if self.sock is not None:
            self.sock.close()
        #     self.sock = None

        # Reset watchdog.
        self.sendts = 0
        # Clear queue.
        while not self.cmd_queue.empty():
            self.cmd_queue.get()

    def quit(self, code):
        '''Clean up and go home.'''
        self.reset()
        if self.sock is not None:
            self.sock.close()
            self.sock = None
        sys.exit(code)







    #------------------------------------------------------------------
    def test_udp(self):
        print('>>>', 'test_udp() enter')
        plog.info('test_udp() enter')

        ### Configure ppdb. ###
        # pbot_pdb.MODE = 'UDP'
        pbot_pdb.PORT = 59140
        pbot_pdb.LOG_FN = os.path.join(os.path.join(os.path.dirname(__file__), 'out', 'pbot_ppdb.log'))

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
        t = MyTestClass()
        t.go()

        ### Examine generated contents. ###
        plog.info('Examine generated contents')
        print('>>>', 'Examine generated contents')
        plog.stop()
        lines = []
        with open(self.log_fn) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 42)
        # plog.info('exit')





#-----------------------------------------------------------------------------------
class MyTestClass():

    def go(self):
        # Set a breakpoint here then step through and examine the code.
        pbot_pdb.breakpoint()

        ret = self.klass_function_1(911, 'abcd')
        # print('ret:', ret)

        # Unhandled exceptions actually go to sys.__excepthook__. Capture these in the code under test.
        # self.klass_function_boom()

        ret = self.klass_function_2([33, 'thanks', 3.56], {'aaa': 111, 'bbb': 222, 'ccc': 333})
        # print('ret:', ret)

        # Run the code under debug.
        # ret = do_it(number=911, alpha='abcd')
        # print('ret:', ret)

    def klass_function_1(self, a1: int, a2: str):
        '''A simple function.'''
        ret = f'answer is:{a1 * len(a2)}'
        return ret

    def klass_function_2(self, a_list, a_dict):
        '''A simple function.'''
        return len(a_list) + len(a_dict)

    def klass_function_boom(self):
        '''A function that causes an unhandled exception.'''
        return 1 / 0


#-----------------------------------------------------------------------------------
# Other test code that may be useful TODO1
#-----------------------------------------------------------------------------------


# #-----------------------------------------------------------------------------------
# class MyClassA(object):
#     '''A simple debug target.'''

#     def __init__(self, name, tags, arg):
#         self._name = name
#         self._tags = tags
#         self._arg = arg

#     def do_something(self, arg):
#         res = f'{self._arg}-user-{arg}'
#         return res

#     def do_boom(self):
#         # Cause unhandled exception.
#         return 1 / 0

# #----------------------------------------------------------
# def function_1(a1: int, a2: float):
#     '''A simple function.'''
#     cl1 = MyClassA('number 1', [45, 78, 23], a1)
#     cl2 = MyClassA('number 2', [100, 101, 102], a2)
#     ret = f'answer is cl1:{cl1.do_something(a1)}...cl2:{cl2.do_something(a2)}'

#     # Play with exception handling.
#     # ret = f'{cl1.do_boom()}'

#     return ret

# #----------------------------------------------------------
# def function_2(a_list, a_dict):
#     '''A simple function.'''
#     return len(a_list) + len(a_dict)

# #----------------------------------------------------------
# def function_boom():
#     '''A function that causes an unhandled exception.'''
#     return 1 / 0

# #----------------------------------------------------------
# def do_it(alpha, number):
#     '''Main code.'''

#     # Benign reload in case of being edited.
#     # importlib.reload(pbot_pdb)

#     # Set a breakpoint here then step through and examine the code.
#     pbot_pdb.breakpoint()

#     ret = function_1(number, len(alpha))

#     # Unhandled exception actually goes to sys.__excepthook__.
#     function_boom()

#     ret = function_2([33, 'thanks', 3.56], {'aaa': 111, 'bbb': 222, 'ccc': 333})

#     return ret
