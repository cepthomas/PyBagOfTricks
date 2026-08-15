import sys
import os
import bdb
import unittest
import subprocess
# Insert path to parent dir.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pbot_pdb
import plog

# __unittest = True  # Tells unittest to completely ignore frames in this module

print('100')

#-----------------------------------------------------------------------------------
class TestPbotPdb2(unittest.TestCase):

    def setUp(self):
        print('200')
        self.log_fn = os.path.join(os.path.join(os.path.dirname(__file__), 'out', 'test_ppdb.log'))
        try: os.remove(self.log_fn)
        except: pass
        plog.init('PTST', self.log_fn, readable=False) #True)
        plog.enable(True)

    def tearDown(self):
        plog.stop()

    def function2(self, arg):
        x = 111
        y = 22
        return arg + x + y

    def function1(self, arg):
        # Set a breakpoint here then step through and examine the code.
        pbot_pdb.breakpoint()
        return self.function2(len(arg))

    def go(self, edit):
        print('300')
        del edit

        # Benign reload in case of edited.
        # importlib.reload(pbot_pdb)

        # Run some fake code.
        self.function1('ABCD')


    #------------------------------------------------------------------
    def test_ppdb2_tcp(self):
        print('400')

        ### Configure ppdb. ###
        pbot_pdb.PORT = 59120
        # pbot_pdb.USE_COLOR = True
        pbot_pdb.XLAT = {'\n': '<NL>', '\r': '<CR>', '\u001b': '<ESC>'}
        pbot_pdb.LOG_FN = os.path.join(os.path.join(os.path.dirname(__file__), 'out', 'pbot_ppdb.log'))
        try: os.remove(pbot_pdb.LOG_FN)
        except: pass

        commif = None
        # capture = []

        # Run the cut.
        self.go(None)
        # t = MyTestClass()
        # t.go()

        # Run the client.
        # subprocess.run(args, *, stdin=None, input=None, stdout=None, stderr=None, capture_output=False,
        # shell=False, cwd=None, timeout=None, check=False, encoding=None, errors=None, text=None,
        # env=None, universal_newlines=None, **other_popen_kwargs)

        fc = R'C:\Dev\Libs\PyBagOfTricks\tests\tcp_client_auto.py'
        # cmd = f'git status "{dir}"'
        # C:\Dev\Libs\PyBagOfTricks\tests\tcp_client_auto.py

        # cp = subprocess.run(cmd, cwd=dir, universal_newlines=True, capture_output=True, text=True, shell=True)
        cp = subprocess.run(['py', fc], universal_newlines=True, capture_output=True, text=True, shell=True)
        ''' Common process output handling  cp: the CompletedProcess, Note git writes some non-error stuff to stderr. '''
        # text = []
        # text.append(f'args:{cp.args}')
        # text.append('')

        # if cp.returncode != 0:
        #     text.append(f'GIT returncode:{cp.returncode}')
        # if len(cp.stdout) > 0:
        #     text.append('GIT stdout')
        #     text.append(f'{cp.stdout}')
        # if len(cp.stderr) > 0:
        #     text.append('GIT stderr')
        #     text.append(f'{cp.stderr}')

        ### Examine generated contents ###
        plog.info('Examine generated contents')
        plog.info(cp.stdout)

#        for sc in capture: print('***', sc)
        # self.assertEqual(len(capture), 42)
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





# ============= Copied from sbot_dev.py ===========================

# #-----------------------------------------------------------------------------------
# # Setup for running pbot_pdb in this file
# # This way:
# #  - Copy pbot_pdb.py to this dir and edit to taste.
# #    from . import pbot_pdb
# # That way:
# #  - Clone PyBagOfTricks and add its path to sys.path.
# pbot_path = R'C:\Dev\Libs\PyBagOfTricks'
# if pbot_path not in sys.path: sys.path.append(pbot_path)
# import pbot_pdb

# #-----------------------------------------------------------------------------------
# class RunPdbCommand():  #(sublime_plugin.TextCommand):
#     ''' '''

#     def function2(self, arg):
#         x = 111
#         y = 22
#         return arg + x + y

#     def function1(self, arg):
#         # Set a breakpoint here then step through and examine the code.
#         pbot_pdb.breakpoint()
#         return self.function2(len(arg))

#     def run(self, edit):
#         del edit

#         # Benign reload in case of edited.
#         # importlib.reload(pbot_pdb)

#         # Configure ppdb.
#         pbot_pdb.PORT = 59120
#         pbot_pdb.USE_COLOR = True
#         pbot_pdb.XLAT = {'\n': '<NL>', '\r': '<CR>', '\u001b': '<ESC>'}
#         pbot_pdb.LOG_FN = os.path.join(os.path.join(os.path.dirname(__file__), 'out', 'pbot_ppdb.log'))
#         try: os.remove(pbot_pdb.LOG_FN)
#         except: pass

#         # Run some fake code.
#         self.function1('ABCD')


# #-----------------------------------------------------------------------------------
# def excepthook(type, value, tb):

#     # This happens with hard shutdown of SbotPdb: BrokenPipeError, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError.
#     if issubclass(type, bdb.BdbQuit) or issubclass(type, ConnectionError):
#         return

#     # Otherwise revert to original hook.
#     sys.__excepthook__(type, value, tb)

# # Connect the last chance hook.
# sys.excepthook = excepthook

# cmd = RunPdbCommand()

# cmd.run(None)
