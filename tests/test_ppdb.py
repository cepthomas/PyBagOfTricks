import sys
import os
import importlib


# This is an example of using ppdb in a python code file. TODO1

doc = '''
######################################################
# This is not a python unittest.
# use:
#   - run one of:
#     - UDP client on localhost:59140
#     - TCP client on localhost:59120
#   - py test_ppdb.py
######################################################
'''

# Add code-under-test path to sys.
npath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if npath not in sys.path:
    sys.path.insert(0, npath)
import pbot_pdb



#-----------------------------------------------------------------------------------
class MyClass(object):
    '''A simple debug target.'''

    def __init__(self, name, tags, arg):
        self._name = name
        self._tags = tags
        self._arg = arg

    def do_something(self, arg):
        res = f'{self._arg}-user-{arg}'
        return res

    def do_boom(self):
        # Cause unhandled exception.
        return 1 / 0


#----------------------------------------------------------
class TestPbotPdb():

    def setUp(self):
        pass

    def tearDown(self):
        pass

    #----------------------------------------------------------
    def go(self):

        # Set a breakpoint here then step through and examine the code.
        pbot_pdb.breakpoint()

        ret = self.klass_function_1(911, 'abcd')
        # print('ret:', ret)

        # Unhandled exception actually goes to sys.__excepthook__. Capture these in the code under test.
        # self.klass_function_boom()

        ret = self.klass_function_2([33, 'thanks', 3.56], {'aaa': 111, 'bbb': 222, 'ccc': 333})
        # print('ret:', ret)

        # Run the code under debug.
        ret = do_it(number=911, alpha='abcd')
        # print('ret:', ret)

    #----------------------------------------------------------
    def klass_function_1(self, a1: int, a2: str):
        '''A simple function.'''
        ret = f'answer is:{a1 * len(a2)}'
        return ret

    #----------------------------------------------------------
    def klass_function_2(self, a_list, a_dict):
        '''A simple function.'''
        return len(a_list) + len(a_dict)

    #----------------------------------------------------------
    def klass_function_boom(self):
        '''A function that causes an unhandled exception.'''
        return 1 / 0


#----------------------------------------------------------
def function_1(a1: int, a2: float):
    '''A simple function.'''
    cl1 = MyClass('number 1', [45, 78, 23], a1)
    cl2 = MyClass('number 2', [100, 101, 102], a2)
    ret = f'answer is cl1:{cl1.do_something(a1)}...cl2:{cl2.do_something(a2)}'

    # Play with exception handling.
    # ret = f'{cl1.do_boom()}'

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
def do_it(alpha, number):
    '''Main code.'''

    # Benign reload in case of being edited.
    # importlib.reload(pbot_pdb)

    # Set a breakpoint here then step through and examine the code.
    pbot_pdb.breakpoint()

    ret = function_1(number, len(alpha))

    # Unhandled exception actually goes to sys.__excepthook__.
    function_boom()

    ret = function_2([33, 'thanks', 3.56], {'aaa': 111, 'bbb': 222, 'ccc': 333})

    return ret


#----------------------------------------------------------
if __name__ == "__main__":
    t = TestPbotPdb()
    t.go()
else:
    print(doc)
