from nt import error
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


# A unit test with the client running in a thread. Needs more debugging.
# Also other possible test code.


#-----------------------------------------------------------------------------------
class TestPbotExtra(unittest.TestCase):

    def setUp(self):
        self.log_fn = os.path.abspath(os.path.join(os.path.dirname(__file__), 'out', 'test_ppdb_threaded.log'))
        try: os.remove(self.log_fn)
        except: pass
        plog.init('PTST', self.log_fn, readable=False) #True)
        plog.enable(True)

    def tearDown(self):
        plog.stop()


    #------------------------------------------------------------------
    def test_ppdb_extra(self):

        ### Configure ppdb. ###
        pbot_pdb.PORT = 59120
        pbot_pdb.XLAT = {'\n': '<NL>', '\r': '<CR>', '\u001b': '<ESC>'}
        pbot_pdb.LOG_FN = os.path.abspath(os.path.join(os.path.dirname(__file__), 'out', 'pbot_pdb.log'))
        try: os.remove(pbot_pdb.LOG_FN)
        except: pass

        commif = None
        capture = []

        ### Run simulated remote client in a thread ###
        def worker():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:

                ### Send some commands ###
                commands = ['w', 'l', 'n']
                while len(commands) > 0:
                    try:
                        ### Try connecting ###
                        tcp_socket.settimeout(1) # enough time to start ppdb server
                        try:
                            tcp_socket.connect((pbot_pdb.HOST, pbot_pdb.PORT))
                            # Didn't fault so must be success.
                            commif = tcp_socket.makefile('rw')
                            # plog.info('Connected to server')

                        except Exception as e:
                            # plog.error('Failed to connect', e)
                            return

                        ### Next command ###
                        smsg = commands.pop(0)
                        plog.debug(f'Send [[[{smsg}]]]')
                        commif.write(smsg + '\n')
                        commif.flush()
                        capture.append(f'S {smsg}')

                        ### Listen for response(s) ###
                        tcp_socket.settimeout(0.2)
                        sresp = ''
                        rcving = True

                        while rcving:
                            try:
                                s = commif.read(100)
                                # Got something.
                                # plog.debug(f'worker received [[[{s}]]]')
                                sresp += s

                            except TimeoutError:
                                # Nothing more to read.
                                rcving = False

                        # Process any capture.
                        plog.debug(f'Receive [[[{sresp}]]]')
                        for s in sresp.splitlines():
                            capture.append(f'R {s}')

                    except Exception as e:
                        plog.error('Unexpected', e)
                        capture.append(f'! {e}')
                        # self._debug(f'CommIf.readline() exception: {str(e)}')
                        raise # hard fail

                plog.debug(f'worker loop exit')

        threading.Thread(target=worker, daemon=True).start()

        ### Now we can run the test code. ###
        plog.info('Run the test code')
        t = MyTestClass()
        t.go()

        ### Examine generated contents ###
        plog.info('Examine generated contents')

#        for sc in capture: print('***', sc)
        self.assertEqual(len(capture), 42)
        # lines = []
        # with open(self.log_fn) as f:
        #     lines = f.readlines()
        # self.assertEqual(len(lines), 42)

        ### Stop ###
        plog.info('exit')
        plog.stop()

        if commif is not None:
            commif.close()
            commif = None


#-----------------------------------------------------------------------------------
class MyTestClass():

    def go(self):
        # Set a breakpoint here then step through and examine the code.
        pbot_pdb.breakpoint()

        ret = self.klass_function_1(911, 'abcd')

        # Unhandled exceptions actually go to sys.__excepthook__. Capture these in the code under test.
        # self.klass_function_boom()

        ret = self.klass_function_2([33, 'thanks', 3.56], {'aaa': 111, 'bbb': 222, 'ccc': 333})

        # Run the code under debug.
        # ret = do_it(number=911, alpha='abcd')

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
# Other test code that may be useful
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
