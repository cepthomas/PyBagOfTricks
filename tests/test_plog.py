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

    def tearDown(self):
        pass

    #----------------------------------------------------------------
    def test_basic_keep_open(self):
        log_fn = h.init_log(h.my_dir(), 'out', 'test_basic_keep_open.log', clean=True)
        log_fn_old = h.init_log(h.my_dir(), 'out', 'test_basic_keep_open_old.log', clean=True)

        # Make a dummy full log file.
        with open(log_fn, 'w') as f:
            for i in range(110):
                f.write(f'{i:03d}-----------------------------------------------\n')

        # The new log file.
        l = plog.Plog('Log333', log_fn, max=5000, keep_open=True)
        l.enable(True)
        l.info(f'================= START {l.name} =======================')

        for i in range(20):
            l.info(f'Info message {i}')
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
        self.assertEqual(len(lines), 122)

        with open(log_fn_old) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 110)

    #----------------------------------------------------------------
    def test_close_after(self):
        log_fn = h.init_log(h.my_dir(), 'out', 'test_close_after.log', clean=True)

        l = plog.Plog('Log888', log_fn, max=5000, keep_open=False)
        l.enable(True)
        l.info(f'================= START {l.name} =======================')

        for i in range(21):
            l.info(f'Info message {i}')
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
        self.assertEqual(len(lines), 128)

    #----------------------------------------------------------------
    def test_overwrite(self):
        log_fn = h.init_log(h.my_dir(), 'out', 'test_overwrite.log', clean=True)
        l = plog.Plog('Log444', log_fn, append=False)
        l.enable(True)
        l.info(f'================= START {l.name} =======================')

        time.sleep(0.123)
        l.info(f'Info message only')
        time.sleep(0.123)
        l.debug(f'Debug message only')
        time.sleep(0.123)

        l.info(f'================= STOP {l.name} =======================')

        # Examine generated contents.
        l.stop()
        lines = []
        with open(log_fn) as f:  # pyright: ignore
            lines = f.readlines()
        self.assertEqual(len(lines), 4)

    #----------------------------------------------------------------
    def test_readable(self):
        log_fn = h.init_log(h.my_dir(), 'out', 'test_readable.log', clean=True)
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
        # l.debug('With UC readable=False [😀]', readable=True)

        l.info(f'================= STOP {l.name} =======================')

        # Examine generated contents.
        l.stop()
        lines = []
        with open(log_fn, encoding='utf-8') as f:  # pyright: ignore
            lines = f.readlines()
            self.assertEqual(len(lines), 12)
            self.assertTrue('With TAB readable=True [<TAB>]' in lines[4])
            self.assertTrue('With UC readable=True [<0xE2><0x99><0xA5>]' in lines[7])
            # When piping terminal output or executing Python in certain environments, Python may default
            # to an encoding that cannot handle special characters (like emojis or non-English alphabets),
            # leading to errors. Force the standard output to use UTF-8. My default is cp1252 (win ansi).
            print('stdout current:', sys.stdout.encoding)
            sys.stdout.reconfigure(encoding='utf-8')  # pyright: ignore
            self.assertTrue(R'With UC readable=False [😀]' in lines[10])

#------------------------------------------------------------------------------
if __name__ == '__main__':
    print('Error! Use python -m unittest <test_yourcode.py>')
    sys.exit(1)
