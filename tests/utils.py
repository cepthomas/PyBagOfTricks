import sys
import os
import traceback

# Various test helpers.

# Init trace log.
_tlog_fn = 'tlog.log'
def reset_tlog(fn):
    global _tlog_fn
    _tlog_fn = fn
    # print('!!!', _tlog_fn)
    try:
        os.remove(_tlog_fn)
    except:
        pass    


# Write to trace log.
def write_tlog(txt):
    global _tlog_fn
    # print('xxx', _tlog_fn)
    with open(_tlog_fn, 'a') as f:
        f.write(txt + '\n')
        f.flush()


# Add path to sys.
def ensure_import(*path_parts):
    npath = os.path.abspath(os.path.join(*path_parts))
    if npath not in sys.path:
        # append rather than insert so can override builtin.
        sys.path.append(npath)


#-----------------------------from sbot_dev------------------------------------------------------
def format_frame(frame, stkpos=-1):
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
def dump_stack(stkpos=1):
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

    for frame in traceback.extract_stack():
        buff.append(f'{format_frame(frame)}')

    return buff
