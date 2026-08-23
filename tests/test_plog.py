import sys
import os
import datetime
import time
import unittest
import helpers as h
h.add_parent_to_path()
import plog


#-----------------------------------------------------------------------------------
class TestPlog(unittest.TestCase):

    def setUp(self):
        self.log_fn = h.init_log(h.my_dir(), 'out', 'test_plog.log', clean=True)
        self.log_fn_old = h.init_log(h.my_dir(), 'out', 'test_plog_old.log', clean=True)

        try: os.remove(self.log_fn)
        except: pass
        try: os.remove(self.log_fn_old)
        except: pass

    def tearDown(self):
        pass

    def test_basic(self):

        l = plog.Plog('Log555', self.log_fn, max=100)

        l.enable(True)

        l.info(f'================= START {l.name} =======================')
        for i in range(20):
            l.info(f'Info message {i}')
            l.warn(f'Warning message {i}')
            l.debug(f'Debug message {i}')
            l.error(f'Error message {i}')
            try:
                raise ValueError('I am very bad')
            except Exception as e:
                l.error(f'Error message exc {i}', e)
        l.info(f'================= STOP {l.name} =======================')

        # Examine generated contents.
        l.stop()
        lines = []
        with open(self.log_fn) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 42)

        with open(self.log_fn_old) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 100)

    def test_overwrite(self):
        #print('>>> test_overwrite')

        # def test_overwrite(self):
        l = plog.Plog('Log666', self.log_fn, append=False)
        l.enable(True)

        l.info(f'================= START {l.name} =======================')
        time.sleep(0.123)
        l.info(f'Info message only')
        time.sleep(0.123)
        l.warn(f'Warning message only')
        time.sleep(0.123)
        l.debug(f'Debug message only')
        time.sleep(0.123)
        l.info(f'================= STOP {l.name} =======================')

        # Examine generated contents.
        l.stop()
        lines = []
        with open(self.log_fn) as f:  # pyright: ignore
            lines = f.readlines()
        self.assertEqual(len(lines), 5)

    def test_readable(self):
        #print('>>> test_readable TODO1')
        pass

#------------------------------------------------------------------------------
if __name__ == '__main__':
    print('Error! Use python -m unittest <test_yourcode.py>')
    sys.exit(1)
