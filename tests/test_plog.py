import sys
import os
import datetime
import time
import unittest
import helpers as h
h.add_parent_to_path()
import plog

import pdb

#-----------------------------------------------------------------------------------
class TestPlog(unittest.TestCase):

    def setUp(self):
        pass
        # self.log_fn = h.init_log(h.my_dir(), 'out', 'test_plog.log', clean=True)
        # self.log_fn_old = h.init_log(h.my_dir(), 'out', 'test_plog_old.log', clean=True)

        # try: os.remove(self.log_fn)
        # except: pass
        # try: os.remove(self.log_fn_old)
        # except: pass

    def tearDown(self):
        pass

    #----------------------------------------------------------------
    def test_keep_open(self):
        log_fn = h.init_log(h.my_dir(), 'out', 'test_plog_basic.log', clean=True)
        log_fn_old = h.init_log(h.my_dir(), 'out', 'test_plog_basic_old.log', clean=True)

        # Make a dummy log file.
        with open(log_fn, 'w') as f:
            for i in range(110):
                f.write(f'{i:03d}-----------------------------------------------\n')

        # breakpoint()

        l = plog.Plog('Log333', log_fn, max=5000)
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
                l.error(f'Error message exc {i}', e.__traceback__)

        l.info(f'================= STOP {l.name} =======================')

        # Examine generated contents.
        l.stop()

        lines = []
        with open(log_fn) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 142)

        with open(log_fn_old) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 110)

    #----------------------------------------------------------------
    def test_close_after(self):
        log_fn = h.init_log(h.my_dir(), 'out', 'test_plog_basic.log', clean=True)
        log_fn_old = h.init_log(h.my_dir(), 'out', 'test_plog_basic_old.log', clean=True)

        # Make a dummy log file.
        with open(log_fn, 'w') as f:
            for i in range(111):
                f.write(f'{i:03d}-----------------------------------------------\n')

        # breakpoint()

        l = plog.Plog('Log888', log_fn, max=5000, keep_open=False)
        l.enable(True)
        l.info(f'================= START {l.name} =======================')

        for i in range(21):
            l.info(f'Info message {i}')
            l.warn(f'Warning message {i}')
            l.debug(f'Debug message {i}')
            l.error(f'Error message {i}')
            try:
                raise ValueError('I am very bad')
            except Exception as e:
                l.error(f'Error message exc {i}', e.__traceback__)

        l.info(f'================= STOP {l.name} =======================')

        # Examine generated contents.
        l.stop()

        lines = []
        with open(log_fn) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 149)

        with open(log_fn_old) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 111)

    #----------------------------------------------------------------
    def test_overwrite(self):
        log_fn = h.init_log(h.my_dir(), 'out', 'test_plog_overwrite.log', clean=True)
        l = plog.Plog('Log444', log_fn, append=False)
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
        with open(log_fn) as f:  # pyright: ignore
            lines = f.readlines()
        self.assertEqual(len(lines), 5)

    #----------------------------------------------------------------
    def test_readable(self):
        log_fn = h.init_log(h.my_dir(), 'out', 'test_plog_readable.log', clean=True)
        l = plog.Plog('Log555', log_fn)
        l.enable(True)
        l.info(f'================= START {l.name} =======================')

        l.debug('Plain line', readable=True)
        l.debug('Plain line', readable=False)
        l.debug('With NL readable=True [\n]', readable=True)
        l.debug('With TAB readable=True [\t]', readable=True)
        l.debug('With TAB readable=False [\t]', readable=False)
        l.debug('With ESC readable=True [\x1B]', readable=True)
        l.debug('With UC readable=True [♥]', readable=True)
        l.debug('With UC readable=False [♥]', readable=False)
        l.debug('With UC readable=True [🔥]', readable=True)
        l.debug('With UC readable=False [😀]', readable=False)

        l.info(f'================= STOP {l.name} =======================')

        # Examine generated contents.
        l.stop()
        lines = []
        with open(log_fn) as f:  # pyright: ignore
            lines = f.readlines()
        # LOG5 test_plog.py(85) ================= START LOG5 =======================
        # LOG5 test_plog.py(123) Plain line
        # LOG5 test_plog.py(124) Plain line
        # LOG5 test_plog.py(125) With NL readable=True [<LF>]
        # LOG5 test_plog.py(126) With TAB readable=True [<TAB>]
        # LOG5 test_plog.py(127) With TAB readable=False [    ]
        # LOG5 test_plog.py(128) With ESC readable=True [<ESC>]
        # LOG5 test_plog.py(129) With UC readable=True [<0xE2><0x99><0xA5>]
        # LOG5 test_plog.py(130) With UC readable=False [<0xE2><0x99><0xA5>]
        # LOG5 test_plog.py(131) With UC readable=True [<0xF0><0x9F><0x94><0xA5>]
        # LOG5 test_plog.py(132) With UC readable=False [<0xF0><0x9F><0x98><0x80>]
        # LOG5 test_plog.py(148) ================= STOP LOG5 =======================

        self.assertEqual(len(lines), 12)
        pass

#------------------------------------------------------------------------------
if __name__ == '__main__':
    print('Error! Use python -m unittest <test_yourcode.py>')
    sys.exit(1)
