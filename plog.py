import sys
import os
import socket
import time
import datetime
import traceback
import shutil
import threading
import enum

# Dumb simple logger for python.

#-------------------------------------------------------------------------------
#---------------------------- Vars ---------------------------------------------
#-------------------------------------------------------------------------------

# Log file name. Arg req.
_log_fn = None

# Logger name. Arg req.
_name = None

# Mode - overwrite/append. Arg opt.
_mode = 'w' # 'a'

# Max log file. Arg opt.
_file_size = 50000

# The log file object.
_f = None

# For elapsed time stamps.
_start_time = 0

# Dynamic flag controls execution.
_enabled = False

# Thread lock for writing.
_lock = threading.Lock()


#-------------------------------------------------------------------------------
#---------------------------- Lifecycle ----------------------------------------
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
def init(name, fn, append=True, max=50000):
    ''' Open the file '''
    global _name, _log_fn, _file_size, _f, _start_time, _enabled
    _start_time = time.perf_counter_ns()

    _name = name
    _log_fn = fn
    _file_size = max

    with _lock:
        try:
            # Initialize logging. Maybe roll over log now.
            if os.path.exists(_log_fn) and os.path.getsize(_log_fn) > _file_size:
                bup = _log_fn.replace('.log', '_old.log')
                shutil.copyfile(_log_fn, bup)
                # Clear current log file.
                with open(_log_fn, 'w'):
                    pass

            # Open file now and keep it open. Note that each instance requires its own file.
            _f = open(_log_fn, 'a' if append else 'w')

        except Exception as e:
            _f = None
            _start_time = 0
            _enabled = False
            error(f'Failed to open log file: {fn}', e)

#-------------------------------------------------------------------------------
def close():
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
def setEnable(enable):
    '''Set the capture flag.'''
    global _enabled
    _enabled = enable

#-------------------------------------------------------------------------------
def flush():
    '''Whoosh.'''
    if _f:
        _f.flush()

#-------------------------------------------------------------------------------
def error(message, exc=None):
    '''Client logger function.'''
    if not _enabled:
        return

    tb = exc.__traceback__
    _write_log('ERR', message, tb)

    # Show the user some context info.
    info = [message]
    for s in traceback.format_tb(tb):
        if len(s) > 0:
            info.append(s[:-1])

#-------------------------------------------------------------------------------
def warn(message):
    '''Client logger function.'''
    if not _enabled:
        return

    _write_log('WRN', message)

#-------------------------------------------------------------------------------
def info(message):
    '''Client logger function.'''
    if not _enabled:
        return

    _write_log('INF', message)

#-------------------------------------------------------------------------------
def debug(message):
    '''Client logger function.'''
    if not _enabled:
        return

    _write_log('DBG', message)


#-------------------------------------------------------------------------------
#---------------------------- Private Functions --------------------------------
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
def _write_log(slevel, message, tb=None):
    '''Format a standard message with caller info and log it.'''
    global _enabled

    if _f is None:
        _enabled = False
        raise RuntimeError('Logger has not been initialized.')

    # # Sometimes get stray empty lines.
    # if len(message) == 0:
    #     return
    # if len(message) == 1 and message[0] == '\n':
    #     return

    # Get caller info.
    frame = sys._getframe(2)
    fn = os.path.basename(frame.f_code.co_filename)
    line = frame.f_lineno
    # f'func = {frame.f_code.co_name}'
    # f'mod_name = {frame.f_globals["__name__"]}'
    # f'class_name = {frame.f_locals["self"].__class__.__name__}'

    time_str = f'{str(datetime.datetime.now())}'[0:-3]
    out_line = f'{time_str} : {slevel} {_name} {fn}({line}) {message}'

    stb = None
    if tb is not None:
        # The traceback formatter is a bit ugly - clean it up.
        tblines = []
        for s in traceback.format_tb(tb):
            if len(s) > 0:
                tblines.append(s[:-1])
        stb = '\n'.join(tblines)

    with _lock:
        # Write the record.
        _f.write(out_line + '\n')
        if stb:
            _f.write(stb + '\n')
        # _f.flush()

#-------------------------------------------------------------------------------
def _make_readable(s):
    '''So we can see things like LF, CR, ESC in log.'''
    s = s.replace('\n', '_N').replace('\r', '_R').replace('\u001b', '_E')
    return s

#-------------------------------------------------------------------------------
def _get_msec():
    '''Get current msec.'''
    return time.perf_counter_ns() / 1000000
