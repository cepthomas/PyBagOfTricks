import sys
import os
import bdb
import unittest
import subprocess
# Insert path to parent dir.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pbot_pdb
import plog

__unittest = True

xlat = {'\n': '<NL>', '\r': '<CR>', '\u001b': '<ESC>'}

#-----------------------------------------------------------------------------------
class TestPbotPdb(unittest.TestCase):

    def setUp(self):
        self.log_fn = os.path.abspath(os.path.join(os.path.dirname(__file__), 'out', 'test_ppdb.log'))
        try: os.remove(self.log_fn)
        except: pass

        plog.init('PTST', self.log_fn, xlat=xlat)
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

        # Run some test code.
        self.function1('ABCD')


    #------------------------------------------------------------------
    def test_ppdb_tcp(self):

        # Configure ppdb. ???      def __init__(self, port, log_fn, host=None, xlat=None, color=True):

        pbot_pdb.set_port(59120)
        pbot_pdb.set_color(True)
        pbot_pdb.set_xlat({'\n': '<NL>', '\r': '<CR>', '\u001b': '<ESC>'})
        ppdb_log_fn = os.path.abspath(os.path.join(os.path.dirname(__file__), 'out', 'pbot_pdb.log'))
        pbot_pdb.set_log_fn(ppdb_log_fn)
        try: os.remove(ppdb_log_fn)
        except: pass

        commif = None
        # capture = []

        # Run the c-u-t.
        try:
            self.go(None)
        except Exception as e:
            pass

        fc = os.path.abspath(os.path.join(os.path.dirname(__file__), 'auto_client.py'))
        cp = subprocess.run(['py', fc, '59120', 'w', 'l', 'n'], universal_newlines=True, capture_output=True, text=True, shell=True)
        # cp = subprocess.run(['py', fc, 59120, 'w', 'l', 'n'], universal_newlines=True, capture_output=True, text=True, shell=True)

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

#------------------------------------------------------------------------------
if __name__ == '__main__':
    print('Error! Use python -m unittest <testfile.py>')
    sys.exit(1)
