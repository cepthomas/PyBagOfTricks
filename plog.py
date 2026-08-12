import sys
import os
import socket
import time
import datetime
import traceback
import shutil
import threading
from ntpath import exists


# Dumb simple logger for python.

#-------------------------------------------------------------------------------
#---------------------------- Vars ---------------------------------------------
#-------------------------------------------------------------------------------

# Log file name. Arg req.
_log_fn = '???'

# Logger name. Arg req.
_name = '???'

# Mode - overwrite/append. Arg opt - default is append
_mode = '?'

# Make readable, stuff like \n etc.
_readable = False

# Max log file lines. Arg opt.
_max = 1000

# The log file object.
_f = None

# Thread lock for writing.
_lock = threading.Lock()

# For elapsed time stamps.
_start_time = time.perf_counter_ns()

# Capturing.
_enabled = False

# Simple file size mgmt.
_line_cnt = 0


#-------------------------------------------------------------------------------
#---------------------------- Lifecycle ----------------------------------------
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
def init(name, fn, append=True, readable=False, max=1000):
    ''' Start the file '''
    global _name, _log_fn, _mode, _max, _f, _enabled

    stop() # just in case

    _name = name
    _log_fn = fn
    _readable = readable
    _max = max
    _mode = 'a' if append else 'w'

    with _lock:
        try:
            # Open file now and keep it open.
            _f = open(_log_fn, _mode)
        except Exception as e:
            stop()
            error(f'Failed to open log file: {fn}', e)

#-------------------------------------------------------------------------------
def stop():
    '''Stop logging. Close file.'''
    global _f, _enabled
    _enabled = False

    with _lock:
        try:
            if _f:
                _f.flush()
                _f.close()
                _f = None
        finally:
            _f = None

#-------------------------------------------------------------------------------
#---------------------------- Public Functions ---------------------------------
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
def enable(enb):
    '''Set the capture flag.'''
    global _enabled
    _enabled = enb

#-------------------------------------------------------------------------------
def error(message, exc=None):
    '''Client logger function.'''
    if _enabled:
        tb = None if not exc else exc.__traceback__
        _write_log('ERR', message, tb)

        # Show the user some context info.
        info = [message]
        for s in traceback.format_tb(tb):
            if len(s) > 0:
                info.append(s[:-1])

#-------------------------------------------------------------------------------
def warn(message):
    '''Client logger function.'''
    if _enabled:
        _write_log('WRN', message)

#-------------------------------------------------------------------------------
def info(message):
    '''Client logger function.'''
    if _enabled:
        _write_log('INF', message)

#-------------------------------------------------------------------------------
def debug(message):
    '''Client logger function.'''
    if _enabled:
        _write_log('DBG', message)

#-------------------------------------------------------------------------------
def dump():
    '''Diagnostic.'''
    return f'plog name:{_name} mode:{_mode} readable:{_readable} fn:{_log_fn} max:{_max} line_cnt:{_line_cnt}'


#-------------------------------------------------------------------------------
#---------------------------- Private Functions --------------------------------
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
def _write_log(slevel, message, tb=None):
    '''Format a standard message with caller info and log it.'''
    global _enabled, _line_cnt, _f

    if _f is None:
        _enabled = False
        raise RuntimeError('Logger has not been initialized.')

    if _readable:
        message = _make_readable(message)

    # Get caller info.
    frame = sys._getframe(2)
    fn = os.path.basename(frame.f_code.co_filename)
    line = frame.f_lineno
    # f'func = {frame.f_code.co_name}'
    # f'mod_name = {frame.f_globals["__name__"]}'
    # f'class_name = {frame.f_locals["self"].__class__.__name__}'

    time_str = f'{str(datetime.datetime.now())}'[0:-3]
    out_line = f'{time_str} {slevel} {_name} {fn}({line}) {message}'

    with _lock:
        # Write the main record.
        _line_cnt += 1
        # _f.write(f'{out_line} {_line_cnt}\n')
        _f.write(out_line)
        _f.write('\n')

        # traceback?
        if tb is not None:
            for tbline in traceback.format_tb(tb):
                for s in tbline.splitlines():
                    _line_cnt += 1
                    # _f.write(f'{s} {_line_cnt}\n')
                    _f.write(s + '\n')

        # Check limit.
        if _line_cnt >= _max:
            _f.flush()
            _f.close()
            old_fn = _log_fn.replace('.log', '_old.log')
            if exists(old_fn): os.remove(old_fn)
            os.rename(_log_fn, old_fn)
            _f = open(_log_fn, _mode)
            _line_cnt = 0

#-------------------------------------------------------------------------------
def _make_readable(s):
    '''So we can see things like LF, CR, ESC in log. TODO user-supplied list.'''
    s = s.replace('\n', '_N').replace('\r', '_R').replace('\u001b', '_E')
    return s

#-------------------------------------------------------------------------------
def _get_msec():
    '''Get current msec.'''
    return time.perf_counter_ns() / 1000000
