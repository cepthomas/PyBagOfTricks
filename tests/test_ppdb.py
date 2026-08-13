import sys
import os
import importlib
import unittest
import threading
import socket
import time
# Insert path to parent dir.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pbot_pdb
import plog


#-----------------------------------------------------------------------------------
class TestPbotPdb(unittest.TestCase):

    def setUp(self):

        self.log_fn = os.path.join(os.path.join(os.path.dirname(__file__), 'out', 'test_ppdb.log'))
        try: os.remove(self.log_fn)
        except: pass
        plog.init('PTST', self.log_fn, readable=True)
        plog.enable(True)

    def tearDown(self):
        pass

    def test_udp(self):
        ### Configure ppdb. ###
        pbot_pdb.MODE = 'UDP'
        pbot_pdb.PORT = 59140

        ### Run simulated remote client in a thread. ###
        def worker():
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                udp_socket.bind((pbot_pdb.HOST, pbot_pdb.PORT))
                udp_socket.settimeout(0.1)  # Seconds.

                commands = ['w', 'l', 'n']
                cind = 0
                run = True
                send_next = True # state
                while run:
                    try:
                        if send_next: # ppdb is waiting for next client/user command.
                            smsg = commands[cind]
                            plog.debug(f'Send message: {smsg}')
                            udp_socket.sendto(smsg.encode('utf-8'), (pbot_pdb.HOST, pbot_pdb.PORT))
                            cind += 1
                            send_next = False
                        else:
                            # Listening for something ppdb sends.
                            rdata, _ = udp_socket.recvfrom(4096) # blocks
                            rmsg = rdata.decode('utf-8')
                            plog.debug(f'Received message: {rmsg}')

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
                        # self._debug(f'CommIf.readline() exception: {str(e)}')
                        raise # hard fail
        threading.Thread(target=worker, daemon=True).start()

        ### Run the test code. ###
        t = MyTestClass()
        t.go()

        ### Examine generated contents. ###
        plog.stop()
        lines = []
        with open(self.log_fn) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 42)

    def test_tcp(self):
        # Configure ppdb.
        pbot_pdb.MODE = 'TCP'
        pbot_pdb.PORT = 59120


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


#-----------------------------------------------------------------------------------
class MyClassA(object):
    '''A simple debug target.'''

    def __init__(self, name, tags, arg):
        self._name = name
        self._tags = tags
        self._arg = arg

    def do_something(self, arg):
        res = f'{self._arg}-user-{arg}'
        return res

    def do_boom(self):
        # Cause unhandled exception.
        return 1 / 0

#----------------------------------------------------------
def function_1(a1: int, a2: float):
    '''A simple function.'''
    cl1 = MyClassA('number 1', [45, 78, 23], a1)
    cl2 = MyClassA('number 2', [100, 101, 102], a2)
    ret = f'answer is cl1:{cl1.do_something(a1)}...cl2:{cl2.do_something(a2)}'

    # Play with exception handling.
    # ret = f'{cl1.do_boom()}'

    return ret

#----------------------------------------------------------
def function_2(a_list, a_dict):
    '''A simple function.'''
    return len(a_list) + len(a_dict)

#----------------------------------------------------------
def function_boom():
    '''A function that causes an unhandled exception.'''
    return 1 / 0

#----------------------------------------------------------
def do_it(alpha, number):
    '''Main code.'''

    # Benign reload in case of being edited.
    # importlib.reload(pbot_pdb)

    # Set a breakpoint here then step through and examine the code.
    pbot_pdb.breakpoint()

    ret = function_1(number, len(alpha))

    # Unhandled exception actually goes to sys.__excepthook__.
    function_boom()

    ret = function_2([33, 'thanks', 3.56], {'aaa': 111, 'bbb': 222, 'ccc': 333})

    return ret
