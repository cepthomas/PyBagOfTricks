import sys
import os
import time
import traceback
import functools
import platform
import inspect



#-----------------------------------------------------------------------------------
#---------------------------- Private fields ---------------------------------------
#-----------------------------------------------------------------------------------

# The trace file.
_ftrace = None

# For elapsed time stamps.
_trace_start_time = 0

# Dynamic flag controls execution.
_trace_enabled = False

# If false continue to execute the steps after error.
_stop_on_exception = False

# Arg separators for records.
_sep = ('(', ')')  # or ('[', ']') ('|', '|')


#-----------------------------------------------------------------------------------
#---------------------------- Public trace functions -------------------------------
#-----------------------------------------------------------------------------------

#---------------------------------------------------------------------------
def start(trace_fn, clean_file=True, stop_on_exception=True, sep=('(', ')')):
    '''
    - clean_file: cleans the file (default is True)
    - stop_on_exception: If false continue to execute the steps after error.
    - sep: Arg separators for records. '[', ']', '|',...
    '''
    global _ftrace
    global _trace_start_time
    global _trace_enabled
    global _stop_on_exception

    stop()  # just in case

    if clean_file:
        try:
            os.remove(trace_fn)
        except:
            pass    

    # Open file now and keep it open. Open/close on every write is too expensive.
    # Note that each instance requires its own file.
    try:
        _ftrace = open(trace_fn, 'a')
        _trace_start_time = time.perf_counter_ns()
        _trace_enabled = True
    except Exception as e:
        _ftrace = None
        _trace_start_time = 0
        _trace_enabled = False
        raise RuntimeError(f'Failed to open trace file - disabling tracing. {e}')


#---------------------------------------------------------------------------
def stop():
    '''Stop tracing.'''
    global _ftrace
    global _trace_enabled

    if _ftrace is not None:
        _ftrace.flush()
        _ftrace.close()
        _ftrace = None
    _trace_enabled = False


#---------------------------------------------------------------------------
def enable(enable):
    '''Gate tracing without start/stop.'''
    global _trace_enabled
    _trace_enabled = enable


#---------------------------------------------------------------------------
def T(*args):
    '''General purpose trace function for user code.'''
    if _ftrace is not None and _trace_enabled:
        func_name, line = _get_caller_site(2)
        argl = []
        for m in args:
            argl.append(m)
        _trace(func_name, line, argl)


#---------------------------------------------------------------------------
def A(cond):
    '''General purpose assert function for user code.'''
    if _ftrace is not None and _trace_enabled and not cond:
        func_name, line = _get_caller_site(2)
        site = f'{func_name}:{line}'
        raise AssertionError(site)


#---------------------------------------------------------------------------
def trfunc(f):
    '''Decorator to support function entry/exit tracing.'''
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        global _trace_enabled
        res = None

        # Check for enabled.
        if _ftrace is not None and _trace_enabled:
            # Instrumented execution.
            msgs = []
            if len(args) > 0:
                for i in range(len(args)):
                    msgs.append(f'{args[i]}') # nice to have name but difficult
            if len(kwargs) > 0:
                for k,v in kwargs.items():
                    msgs.append(f'{k}:{v}')

            func_name = _get_func_name_from_func(f)

            # Record entry.
            _trace(func_name, 'enter', msgs)

            # Execute the wrapped function.
            ret = []
            try:
                res = f(*args, **kwargs)

                # No runtime errors.
                ret.append(f'{res}')
                # Record exit.
                _trace(func_name, 'exit', ret)

            except AssertionError as e:
                # User A() hit. Record a useful message.
                _trace(e, 'assert')
                if _stop_on_exception:
                    # Stop execution now.
                    _trace_enabled = False

            except Exception as e:
                # Other exception in T() code. Record a useful message.
                tb = e.__traceback__
                frame = traceback.extract_tb(tb)[-1]
                _trace(_get_func_name_from_frame(frame), frame.lineno, [f'exception: {e}'])
                if _stop_on_exception:
                    # Stop execution now.
                    _trace_enabled = False

        else:
            # Simple execution.
            res = f(*args, **kwargs)

        return res

    return wrapper


#-----------------------------------------------------------------------------------
#---------------------------- Private functions ------------------------------------
#-----------------------------------------------------------------------------------


#---------------------------------------------------------------------------
def _trace(func_name, line, args=None):
    '''Do one trace record.'''
    elapsed = time.perf_counter_ns() - _trace_start_time
    msec = elapsed // 1000000
    usec = elapsed // 1000

    parts = []
    parts.append(f'{msec:04}.{usec:03}')
    parts.append(f'{func_name}:{line}')

    if args is not None:
        for a in args:
            parts.append(f'{_sep[0]}{a}{_sep[1]}')
    s = ' '.join(parts) + '\n'

    # Write the record.
    _ftrace.write(s)


#---------------------------------------------------------------------------
def _get_caller_site(stkpos):
    '''Dig out caller source func name and line from call stack. Includes class name if member.'''
    frame = sys._getframe(stkpos)
    if 'self' in frame.f_locals:
        class_name = frame.f_locals['self'].__class__.__name__
        func_name = f'{class_name}.{frame.f_code.co_name}'
    else:
        func_name = frame.f_code.co_name  # could also be '<module>'
    return (func_name, frame.f_lineno)


#---------------------------------------------------------------------------
def _get_func_name_from_func(f):
    '''Dig out func name from function object.'''
    func_name = getattr(f, '__qualname__')
    return func_name


#---------------------------------------------------------------------------
def _get_func_name_from_frame(frame):
    '''Dig out func name and line from frame. Includes class name if member.'''
    if frame.locals is not None and 'self' in frame.locals:
        class_name = frame.locals['self'].__class__.__name__
        func_name = f'{class_name}.{frame.name}'
    else:
        func_name = frame.name  # could also be '<module>'
    return func_name
