import sys
import os
import bdb
import unittest
import subprocess
# Insert path to parent dir.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pbot_pdb
import plog


# python -m unittest test_ppdb.py

# __unittest = True  # Tells unittest to completely ignore frames in this module


#-----------------------------------------------------------------------------------
class TestPbotPdb(unittest.TestCase):

    def setUp(self):
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
        del edit

        # Benign reload in case of edited.
        # importlib.reload(pbot_pdb)

        # Run some fake code.
        self.function1('ABCD')


    #------------------------------------------------------------------
    def test_ppdb_tcp(self):

        # Configure ppdb.
        pbot_pdb.PORT = 59120
        # pbot_pdb.USE_COLOR = True
        pbot_pdb.XLAT = {'\n': '<NL>', '\r': '<CR>', '\u001b': '<ESC>'}
        pbot_pdb.LOG_FN = os.path.join(os.path.join(os.path.dirname(__file__), 'out', 'pbot_ppdb.log'))
        try: os.remove(pbot_pdb.LOG_FN)
        except: pass

        commif = None
        # capture = []

        # Run the c-u-t.
        try:
            self.go(None)
        except Exception as e:
            pass

        fc = R'C:\Dev\Libs\PyBagOfTricks\tests\auto_client.py'
        cp = subprocess.run(['py', fc], universal_newlines=True, capture_output=True, text=True, shell=True)

        # Examine generated contents
        plog.info('Examine generated contents')
        plog.info(f'\n[{cp.stdout}]')

#        for sc in capture: print('***', sc)
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
