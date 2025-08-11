import sys
import os
import unittest
# import subprocess
# import platform
import traceback
import datetime
import importlib
import bdb


#-----------------------------------------------------------------------------------
my_dir = os.path.dirname(__file__)

# Add source path to sys.
src_dir = os.path.abspath(os.path.join(my_dir, '..'))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir) # or? sys.path.append(path)

# Reset dump file.
dump_fn = os.path.join(my_dir, 'out', 'dump.log')
try:
    os.remove(dump_fn)
except:
    pass    

# Write to dump file.
def dump(txt):
    with open(dump_fn, 'a') as f:
        f.write(txt + '\n')
        f.flush()


#-----------------------------------------------------------------------------------

class TestPbotPdb(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    #-----------------------------------------------------------------------------------
    # ------- was SbotRunPdbCommand():
    def doit_happy(self): 

        # Set a breakpoint here then step through and examine the code.
        # from . import pbot_pdb; pbot_pdb.breakpoint()
        import pbot_pdb; pbot_pdb.breakpoint()

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
    # ------- TODO1 was SbotDebugCommand():
    def doit_boom(self):
        pass

        # Blow stuff up. Force unhandled exception.
        # sc.debug('Forcing unhandled exception!')
        # sc.open_path('not-a-real-file')
        # i = 222 / 0


        # dump('====== Dump a stack - most recent last')
        # for f in traceback.extract_stack():
        #     dump(_frame_formatter(f))


        # dump('====== Dump a traceback - most recent last')
        # try:
        #     x = 1 / 0
        # except Exception as e:
        #     for f in traceback.extract_tb(e.__traceback__):
        #         dump(_frame_formatter(f))


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
#----------------------- ST flavor TODO1 test or example? --------------------------
#-----------------------------------------------------------------------------------



#-----------------------------------------------------------------------------------

class TestPdb_fromST(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    #-----------------------------------------------------------------------------------
    # ------- was SbotRunPdbCommand():
    def doit_woo(self):

        # Set a breakpoint here then step through and examine the code.
        # from . import sbot_pdb;

        # Benign reload in case of being edited.
        # importlib.reload(sbot_pdb)

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

    # Benign reload in case of being edited.
    importlib.reload(pbot_pdb)

    # Set a breakpoint here then step through and examine the code.
    pbot_pdb.breakpoint()

    ret = function_1(number, len(alpha))

    # Unhandled exception actually goes to sys.__excepthook__.
    function_boom()

    ret = function_2([33, 'thanks', 3.56], {'aaa': 111, 'bbb': 222, 'ccc': 333})

    return ret
