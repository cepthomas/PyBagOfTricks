import sys
import os
import bdb
import unittest
import subprocess
import socket
import threading
import helpers as h
h.add_path_to_parent()
import pbot_pdb
import plog

__unittest = True


#-----------------------------------------------------------------------------------
class TestPbotPdb(unittest.TestCase):

    def setUp(self):
        # Logging.
        self.log_fn = h.init_log(h.my_dir(), 'out', 'test_ppdb.log', clean=True)
        self.ppdb_log_fn = h.init_log(h.my_dir(), 'out', 'pbot_pdb.log', clean=True)
        plog.init('PTST', self.log_fn)
        plog.enable(True)

    def tearDown(self):
        plog.stop()

    #------------------------------------------------------------------
    # Target test code below.
    def function2(self, arg):
        x = 111
        y = 22
        return arg + x + y

    def function1(self, arg):
        # Set a breakpoint here then step through and examine the code.
        pbot_pdb.breakpoint(59120, self.log_fn)
        return self.function2(len(arg))

    def go(self, edit):
        del edit

        # Benign reload in case of edited.
        # importlib.reload(pbot_pdb)

        # Run some test code.
        self.function1('ABCD')


    #------------------------------------------------------------------
    def test_ppdb_tcp(self):

        commif = None
        # capture = []

        # Run the c-u-t.
        try:
            self.go(None)
        except Exception as e:
            pass

        fc = os.path.join(h.my_dir(), 'auto_client.py')
        cp = subprocess.run(['py', fc, '59120', 'w', 'l', 'n'], universal_newlines=True, capture_output=True, text=True, shell=True)
        # cp = subprocess.run(['py', fc, 59120, 'w', 'l', 'n'], universal_newlines=True, capture_output=True, text=True, shell=True)

        # Examine generated contents
        plog.info('Examine generated contents')
        plog.info(f'\n[{cp.stdout}]')

        # for sc in capture: print('***', sc)
        # self.assertEqual(len(capture), 42)
        # lines = []
        # with open(self.log_fn) as f:
        #     lines = f.readlines()
        # self.assertEqual(len(lines), 42)

        # Stop
        plog.info('exit')
        plog.stop()

        if commif is not None:
            commif.close()
            commif = None


    #------------------------------------------------------------------
    @unittest.skip('TODO A unit test with the client running in a thread. Has issues, needs more debugging.')
    def test_ppdb_threaded(self):
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
                            tcp_socket.connect(('127.0.0.1', 59120))
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
                                # debug(f'worker received [[[{s}]]]')
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
        # t = MyTestClass()
        # t.go()

        ### Examine generated contents ###
        plog.info('Examine generated contents')

#        for sc in capture: print('***', sc)
        self.assertEqual(len(capture), 9999)

        ### Stop ###
        plog.info('exit')
        plog.stop()

        if commif is not None:
            commif.close()
            commif = None


#------------------------------------------------------------------------------
if __name__ == '__main__':
    print('Error! Use python -m unittest <testfile.py>')
    sys.exit(1)


#------------------------------------------------------------------------------
# Other test code that may be useful

#-----------------------------------------------------------------------------------
# class MyTestClass():
#     def go(self):
#         # Set a breakpoint here then step through and examine the code.
#         pbot_pdb.breakpoint()
#         ret = self.klass_function_1(911, 'abcd')
#         # Unhandled exceptions actually go to sys.__excepthook__. Capture these in the code under test.
#         # self.klass_function_boom()
#         ret = self.klass_function_2([33, 'thanks', 3.56], {'aaa': 111, 'bbb': 222, 'ccc': 333})
#         # Run the code under debug.
#         # ret = do_it(number=911, alpha='abcd')
#     def klass_function_1(self, a1: int, a2: str):
#         '''A simple function.'''
#         ret = f'answer is:{a1 * len(a2)}'
#         return ret
#     def klass_function_2(self, a_list, a_dict):
#         '''A simple function.'''
#         return len(a_list) + len(a_dict)
#     def klass_function_boom(self):
#         '''A function that causes an unhandled exception.'''
#         return 1 / 0

# #----------------------------------------------------------
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
