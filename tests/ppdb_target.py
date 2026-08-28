import sys
import os
import bdb
import helpers as h
h.add_parent_to_path()
import pbot_pdb




#---------------- Breakpoint test code ----------------------------
# Target test code below.
def function2(arg):
    x = 111
    y = 22
    return arg + x + y

def function1(arg):
    # Set a breakpoint in here then step through and examine the code.
    print('function1 set breakpoint')

    ppdb_log_fn = h.init_log(h.my_dir(), 'out', 'pbot_pdb.log', clean=True)
    pbot_pdb.breakpoint(59120, log_fn=ppdb_log_fn, use_color=True) # turn off color for unit test
    
    print('function1 done breakpoint')

    return function2(len(arg))

def go():
    print('go() enter')

    # Benign reload in case of edited.
    # importlib.reload(pbot_pdb)

    # Run some test code.
    function1('ABCD')
    print('go() exit')

#------------------------------------------------------------------
def excepthook(type, value, tb):
    '''Process unhandled exceptions.'''

    print(f'excepthook!! type:[{type}] value:[{value}]')
    # l.error(f'traceback:\n', tb)

    # This happens with hard shutdown of SbotPdb.
    # BdbQuit
    # ConnectionError: BrokenPipeError, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError.
    if issubclass(type, bdb.BdbQuit) or issubclass(type, ConnectionError):
        pass
    else:       
        # Otherwise use original hook.
        sys.__excepthook__(type, value, tb)


#------------------------------------------------------------------
if __name__ == '__main__':
    # Connect the last chance hook.
    sys.excepthook = excepthook

    print('target says go!')
    go()
