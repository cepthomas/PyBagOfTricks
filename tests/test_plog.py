import sys
import os
import datetime
import importlib
import unittest


# Add code-under-test path to sys.
npath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if npath not in sys.path:
    sys.path.insert(0, npath)

# OK to import now.
import plog
# Benign reload in case it's edited.
# importlib.reload(plog)


#-----------------------------------------------------------------------------------
class TestPlog(unittest.TestCase): # TODO1

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_success(self):
        pass
        # trace_fn = os.path.join(os.path.join(os.path.dirname(__file__), 'tracer.log'))
        # tr.start(trace_fn, clean_file=True, stop_on_exception=True, sep=('(', ')'))

        # T(f'Start {do_a_suite.__name__}:{do_a_suite.__doc__} {datetime.datetime.now()}')
        # do_a_suite(number=911, alpha='abcd')  # named args
        # tr.stop()  # Always clean up resources!!

        # # Examine generated contents.
        # lines = []
        # with open(trace_fn) as f:
        #     lines = f.readlines()

        # self.assertEqual(len(lines), 25)
