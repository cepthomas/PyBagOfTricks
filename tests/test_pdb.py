import sys
import os
import unittest
# import subprocess
# import platform
import traceback
import datetime
# import importlib
import bdb

# try:
#     from . import sbot_common as sc  # normal import
# except:
#     import sbot_common as sc  # unittest import


# Benign reload in case of edited.
# importlib.reload(sc)


#-----------------------------------------------------------------------------------
# Clean dump file.
_dump_fn = os.path.join(os.path.dirname(__file__), 'out', '_dump.log')
try:
    os.remove(_dump_fn)
except:
    pass    

# Write to dump file.
def _dump(txt):
    with open(_dump_fn, 'a') as f:
        f.write(txt + '\n')
        f.flush()





#-----------------------------------------------------------------------------------

class TestPdb(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    #-----------------------------------------------------------------------------------
    # ------- class SbotRunPdbCommand():
    def doit1(self): 

        # TEST_OUT_PATH = os.path.join(os.path.dirname(__file__), 'out')
        # import sys, os
        # TODO1 sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Common'))
        # import Common

        # Set a breakpoint here then step through and examine the code.
        from . import sbot_pdb; sbot_pdb.breakpoint()

        ret = self.function_1(911, 'abcd')
        print('ret:', ret)

        # Unhandled exception actually goes to sys.__excepthook__.
        # function_boom()

        ret = self.function_2([33, 'thanks', 3.56], {'aaa': 111, 'bbb': 222, 'ccc': 333})
        print('ret:', ret)

    #----------------------------------------------------------
    def function_1(self, a1: int, a2: str):
        '''A simple function.'''
        ret = f'answer is:{a1 * len(a2)}'
        return ret

    #----------------------------------------------------------
    def function_2(self, a_list, a_dict):
        '''A simple function.'''
        return len(a_list) + len(a_dict)

    #----------------------------------------------------------
    def function_boom(self):
        '''A function that causes an unhandled exception.'''
        return 1 / 0


    #-----------------------------------------------------------------------------------
    # ------- class SbotDebugCommand():
    def doit2(self):
        pass

        # Blow stuff up. Force unhandled exception.
        # sc.debug('Forcing unhandled exception!')
        # sc.open_path('not-a-real-file')
        # i = 222 / 0


        # _dump('====== Dump a stack - most recent last')
        # for f in traceback.extract_stack():
        #     _dump(_frame_formatter(f))


        # _dump('====== Dump a traceback - most recent last')
        # try:
        #     x = 1 / 0
        # except Exception as e:
        #     for f in traceback.extract_tb(e.__traceback__):
        #         _dump(_frame_formatter(f))


        # '''
        # is_folded(region: Region) → bool
        # folded_regions() → list[sublime.Region]
        # fold(x: Region | list[sublime.Region]) → bool
        # unfold(x: Region | list[sublime.Region]) → list[sublime.Region]
        # '''
        # regions = self.view.folded_regions()
        # text = ["folded_regions"]
        # for r in regions:
        #     s = f'region:{r}'
        #     text.append(s)
        # new_view = sc.create_new_view(self.view.window(), '\n'.join(text))


#-----------------------------------------------------------------------------------
def _frame_formatter(frame, stkpos=-1):
    if stkpos >= 0:
        # extra info please
        s = f'stkpos:{stkpos} file:{frame.filename} func:{frame.name} lineno:{frame.lineno} line:{frame.line}'
    else:
        s = f'file:{frame.filename} func:{frame.name} lineno:{frame.lineno} line:{frame.line}'
    # Other frame.f_code attributes:
    # co_filename, co_firstlineno, co_argcount, co_name, co_varnames, co_consts, co_names
    # co_cellvars, co_freevars, co_kwonlyargcount, co_posonlyargcount, co_nlocals, co_stacksize
    return s


#-----------------------------------------------------------------------------------
def _dump_stack(stkpos=1):
    # Default is caller frame -> 1.

    buff = []

    # tb => traceback object.
    # limit => Print up to limit stack trace entries (starting from the invocation point) if limit is positive.
    #   Otherwise, print the last abs(limit) entries. If limit is omitted or None, all entries are printed.
    # f => optional argument can be used to specify an alternate stack frame to start. Otherwise uses current.
    # FrameSummary attributes of interest: 'filename', 'line', 'lineno', 'locals', 'name'.

    # [FrameSummary] traceback.extract_tb(tb, limit=None)  Useful for alternate formatting of stack traces.
    # [FrameSummary] traceback.extract_stack(f=None, limit=None)  Extract the raw traceback from the current stack frame.
    # [string] traceback.format_list([FrameSummary])  Kind of ugly printable format with dangling newlines.
    # [string] traceback.format_tb(tb, limit=None)  A shorthand for format_list(extract_tb(tb, limit)).
    # [string] traceback.format_stack(f=None, limit=None)  A shorthand for format_list(extract_stack(f, limit)).

    # Get most recent frame => traceback.extract_tb(tb)[:-1], traceback.extract_stack()[:-1]

    # try:
    #     while True:
    #         frame = sys._getframe(stkpos)  ??? this doesn't work any more
    #         buff.append(f'{_frame_formatter(frame, stkpos)}')
    #         stkpos += 1
    # except:
    #     # End of stack.
    #     pass


    for frame in traceback.extract_stack():
        buff.append(f'{_frame_formatter(frame)}')

    return buff


#-----------------------------------------------------------------------------------
def excepthook(type, value, tb):
    '''
    Process unhandled exceptions. This catches for all current plugins and is mainly
    used for debugging the sbot pantheon. Logs the full stack and pops up a message box
    with summary.
    '''

    # Sometimes gets these on shutdown:

    # FileNotFoundError '...Log\plugin_host-3.8-on_exit.log'
    # if issubclass(type, FileNotFoundError) and 'plugin_host-3.8-on_exit.log' in str(value):
    #     return

    # This happens with hard shutdown of SbotPdb: BrokenPipeError, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError.
    if issubclass(type, bdb.BdbQuit) or issubclass(type, ConnectionError):
        return

    # LSP is sometimes impolite when closing.
    # 2024-10-03 13:03:31.177 ERR sbot_dev.py:384 Unhandled exception TypeError: 'NoneType' object is not iterable
    # if type is TypeError and 'object is not iterable' in str(value):
    #     return

    # # Crude shutdown detection.
    # if len(sublime.windows()) > 0:
    #     msg = f'Unhandled exception {type.__name__}: {value}\nSee the log or ST console'
    #     sc.error(msg, tb)


    # Otherwise let nature take its course.
    sys.__excepthook__(type, value, tb)


#-----------------------------------------------------------------------------------
#----------------------- Finish initialization -------------------------------------
#-----------------------------------------------------------------------------------

# Connect the last chance hook.
sys.excepthook = excepthook





#-----------------------------------------------------------------------------------
#----------------------- ST flavor TODO1 test or example? --------------------------
#-----------------------------------------------------------------------------------


#-----------------------------------------------------------------------------------
class SbotPdbExampleCommand():
    '''Run the plugin from a menu item.'''

    def run(self, edit):
        del edit
        # Benign reload in case of being edited.
#        importlib.reload(sbot_pdb)
        # Run the code under debug.
        ret = do_a_suite(number=911, alpha='abcd')
        print('ret:', ret)


#----------------------------------------------------------
class MyClass(object):
    '''A simple object.'''

    def __init__(self, name, tags, arg):
        self._name = name
        self._tags = tags
        self._arg = arg

    def do_something(self, arg):
        res = f'{self._arg}-user-{arg}'
        return res

    def class_boom(self):
        # Cause unhandled exception.
        return 1 / 0


#----------------------------------------------------------
def function_1(a1: int, a2: float):
    '''A simple function.'''
    cl1 = MyClass('number 1', [45, 78, 23], a1)
    cl2 = MyClass('number 2', [100, 101, 102], a2)
    ret = f'answer is cl1:{cl1.do_something(a1)}...cl2:{cl2.do_something(a2)}'

    # Play with exception handling.
    # ret = f'{cl1.class_boom()}'

    return ret


#----------------------------------------------------------
def function_2(a_list, a_dict):
    '''A simple function.'''
    return len(a_list) + len(a_dict)


#----------------------------------------------------------
def function_boom():
    '''A function that causes an unhandled exception.'''
    return 1 / 0


#----------------------------------------------------------
def do_a_suite(alpha, number):
    '''Main code.'''

    # Set a breakpoint here then step through and examine the code.
    sbot_pdb.breakpoint()

    ret = function_1(number, len(alpha))

    # Unhandled exception actually goes to sys.__excepthook__.
    function_boom()

    ret = function_2([33, 'thanks', 3.56], {'aaa': 111, 'bbb': 222, 'ccc': 333})

    return ret
