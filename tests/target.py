import sys
import os
import helpers as h
h.add_parent_to_path()
import pbot_pdb
import plog


# Setup logging.
target_log_fn = h.init_log(h.my_dir(), 'out', 'target.log', clean=True)
ppdb_log_fn = h.init_log(h.my_dir(), 'out', 'pbot_pdb.log', clean=True)
l = plog.Plog('TRGT', target_log_fn)
l.enable(True)
l.info('----- target.py loaded -----')


#---------------- Breakpoint test code ----------------------------
# Target test code below.
def function2(arg):
    x = 111
    y = 22
    return arg + x + y

def function1(arg):
    # Set a breakpoint in here then step through and examine the code.
    l.info('function1 set breakpoint')
    pbot_pdb.breakpoint(59120, log_fn=ppdb_log_fn, use_color=False) # turn off color for unit test
    l.info('function1 done breakpoint')
    
    return function2(len(arg))

def go():
    l.info('go() enter')

    # Benign reload in case of edited.
    # importlib.reload(pbot_pdb)

    # Run some test code.
    function1('ABCD')
    l.info('go() exit')

#------------------------------------------------------------------------------
if __name__ == '__main__':
    print('>>> target prints hi')
    go()
    print('>>> target prints bye')
    l.stop()