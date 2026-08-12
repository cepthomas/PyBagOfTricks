import sys
import os
import datetime
import unittest

# Insert path to parent dir.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import plog


#-----------------------------------------------------------------------------------
class TestPlog(unittest.TestCase):

    def setUp(self):
        self.log_fn = os.path.join(os.path.join(os.path.dirname(__file__), 'out', 'plog_test.log'))
        
    def tearDown(self):
        pass

    def test_success(self):
        try: os.remove(self.log_fn)
        except: pass
        plog.init('PLOG1', self.log_fn, max=100)
        plog.enable(True)

        plog.info(f'================= START PLOG1 =======================')
        for i in range(20):
            plog.info(f'Info message {i}')
            plog.warn(f'Warning message {i}')
            plog.debug(f'Debug message {i}')
            plog.error(f'Error message {i}')
            try:
                raise ValueError('I am very bad')
            except Exception as e:
                plog.error(f'Error message exc {i}', e)
        plog.info(f'================= STOP PLOG1 =======================')

        # Examine generated contents.
        plog.stop()
        lines = []
        with open(self.log_fn) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 42)

        # def test_overwrite(self):
        plog.init('PLOG2', self.log_fn, append=False)
        plog.enable(True)

        plog.info(f'================= START PLOG1 =======================')
        plog.info(f'Info message only')
        plog.warn(f'Warning message only')
        plog.debug(f'Debug message only')
        plog.info(f'================= STOP PLOG1 =======================')

        # Examine generated contents.
        plog.stop()
        lines = []
        with open(self.log_fn) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 5)
