import sys
import os
import pdb


##### Execute builtin pdb.



#---------------- Breakpoint test code ----------------------------
# Target test code below.
def function2(arg):
    x = 111
    y = 22
    return arg + x + y

def function1(arg):
    # Set a breakpoint here then step through and examine the code.
    print('set bp')
    breakpoint()
    print('done bp')
    return function2(len(arg))

def go():
    print('go() enter')

    # Benign reload in case of edited.
    # importlib.reload(pbot_pdb)

    # Run some test code.
    function1('ABCD')
    print('go() exit')

#------------------------------------------------------------------------------
if __name__ == '__main__':
    go()
