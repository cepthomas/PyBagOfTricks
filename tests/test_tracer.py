import sys
import os
import datetime
import importlib
import unittest
import utils

# Add source path to sys.
my_dir = os.path.dirname(__file__)
utils.ensure_import(my_dir, '..')
# OK to import now.
import tracer as tr
# Benign reload in case of edited.
importlib.reload(tr)


# Some optional shorthand.
trfunc = tr.trfunc
A = tr.A
T = tr.T


#------------------------ Dummy test object ------------------------------------------
class ExampleClass(object):
    ''' Class function tracing.'''

    # Note: don't use @trfunc on constructor!
    def __init__(self, name, tags, arg):
        '''Construction.'''
        T('making one ExampleClass', name, tags, arg)
        self._name = name
        self._tags = tags
        self._arg = arg

    @trfunc
    def do_something(self, arg):
        '''Entry/exit is traced with args and return value.'''
        res = f'{self._arg}-user-{arg}'
        return res

    @trfunc
    def do_class_assert(self, arg):
        '''Entry/exit is traced with args and return value.'''
        A(1 == 2)

    @trfunc
    def do_class_exception(self, arg):
        '''Entry/exit is traced with args and return value.'''
        x = 1 / 0

    def __str__(self):
        '''Required for readable trace.'''
        s = f'ExampleClass:{self._name} tags:{self._tags} arg:{self._arg}'
        return s


#------------------------ Test functions ------------------------------------------
def no_trfunc_function(s):
    '''Entry/exit is not traced but explicit traces are ok.'''
    T(f'I still can do this => "{s}"')

@trfunc
def another_function(a_list, a_dict):
    '''Entry/exit is traced with args and return value.'''
    return len(a_list) + len(a_dict)

@trfunc
def one_function(a1: int, a2: float):
    '''Entry/exit is traced with args and return value.'''
    cl1 = ExampleClass('number 1', [45, 78, 23], a1)
    cl2 = ExampleClass('number 2', [100, 101, 102], a2)
    T(cl1)
    T(cl2)
    ret = f'answer is cl1:{cl1.do_something(a1)}...cl2:{cl2.do_something(a2)}'

    ret = f'{cl1.do_class_assert(a1)}'

    ret = f'{cl1.do_class_exception(a2)}'
    return ret

@trfunc
def exception_function():
    '''Cause exception and handling.'''
    i = 0
    return 1 / i

@trfunc
def assert_function():
    '''Assert processing.'''
    i = 10
    j = 10

    A(i == j)  # ok - no trace
    i += 1
    A(i == j)  # assert

@trfunc
def do_a_suite(alpha, number):
    '''Make a nice suite with entry/exit and return value.'''
    T('something sweet')

    ret = one_function(5, 9.126)

    exception_function()

    assert_function()

    no_trfunc_function('can you see me?')
    # ret = another_function([33, 'tyu', 3.56], {'aaa': 111, 'bbb': 222, 'ccc': 333})
    ret = another_function([33, 'tyu', 3.56], {'aaa': number, alpha: 222, 'ccc': 333})
    return ret


#-----------------------------------------------------------------------------------
class TestTracer(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_success(self):
        trace_fn = os.path.join(my_dir, 'out', 'tracer.log')
        tr.start(trace_fn, clean_file=True, stop_on_exception=True, sep=('(', ')'))

        T(f'Start {do_a_suite.__name__}:{do_a_suite.__doc__} {datetime.datetime.now()}')
        do_a_suite(number=911, alpha='abcd')  # named args
        tr.stop()  # Always clean up resources!!

        # Examine generated contents.
        lines = []
        with open(trace_fn) as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 25)
