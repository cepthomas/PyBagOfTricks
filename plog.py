import sys
import os
import datetime
import traceback
import threading

# Dumb simple logger for python.

# TODO future: Add trace level (maybe tracer.py). Min level property. Remove warn?


# Options for making bin readable. TODO user config?
xlat_tbl = { '\0':'NUL', '\n':'LF', '\r':'CR', '\t':'TAB', '\033':'ESC' }
left_delim = '<' # '|'
right_delim = '>' #'|'


class Plog:
    #---------------------------- Lifecycle ----------------------------------------

    #-------------------------------------------------------------------------------
    def __init__(self, name, fn, append=True, max=1000):
        ''' Start the logger
            - logger name
            - log file name
            - append or overwrite file
            - max file lines
            '''
        self.name = name[0:4].upper()
        self.log_fn = fn
        self.mode = 'a' if append else 'w'
        self.max = max

        # The log file object.
        self.f = None

        # Thread lock for writing.
        self.lock = threading.Lock()

        # Capture gate.
        self.enabled = False

        # Simple file size mgmt.
        self.line_cnt = 0

        # Open file now and keep it open.
        with self.lock:
            try:
                self.f = open(self.log_fn, self.mode)
            except Exception as e:
                self.stop()
                self.error(f'Failed to open log file: {self.log_fn}', e)

    #---------------------------- Public Functions ---------------------------------

    #-------------------------------------------------------------------------------
    def stop(self):
        '''Stop logging. Close file.'''
        self.enabled = False

        with self.lock:
            try:
                if self.f:
                    self.f.flush()
                    self.f.close()
                    self.f = None
            finally:
                self.f = None

    #-------------------------------------------------------------------------------
    def enable(self, enb):
        '''Set the capture flag.'''
        self.enabled = enb

    #-------------------------------------------------------------------------------
    def error(self, message, e=None, readable=False):
        '''Client logger function.'''
        if self.enabled:
            tb = None if not e else e.__traceback__
            self._write_log('ERR', message, tb=tb, readable=readable)

    #-------------------------------------------------------------------------------
    def warn(self, message):
        '''Client logger function.'''
        if self.enabled:
            self._write_log('WRN', message)

    #-------------------------------------------------------------------------------
    def info(self, message):
        '''Client logger function.'''
        if self.enabled:
            self._write_log('INF', message)

    #-------------------------------------------------------------------------------
    def debug(self, message, readable=False):
        '''Client logger function.'''
        if self.enabled:
            self._write_log('DBG', message, readable=readable)

    #-------------------------------------------------------------------------------
    def dump(self):
        '''Diagnostic.'''
        return f'plog name:{self.name} mode:{self.mode} fn:{self.log_fn} max:{self.max} line_cnt:{self.line_cnt}'


    #---------------------------- Private Functions --------------------------------

    #-------------------------------------------------------------------------------
    def _write_log(self, slevel, message, tb=None, readable=False):
        '''Format a standard message with caller info and log it.'''
        if self.f is None:
            self.enabled = False
            raise RuntimeError('Logger has not been initialized.')

        if readable:
            message = self._make_readable(message)

        # Get caller info.
        frame = sys._getframe(2)
        fn = os.path.basename(frame.f_code.co_filename)
        line = frame.f_lineno
        # f'func = {frame.f_code.co_name}'
        # f'mod_name = {frame.f_globals["__name__"]}'
        # f'class_name = {frame.f_locals["self"].__class__.__name__}'

        dt = datetime.datetime.now()
        sdate = f'{dt.year:04d}-{dt.month:02d}-{dt.day:02d}'
        stime = f'{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}.{dt.microsecond//1000:03d}.{dt.microsecond%1000:03d}'
        out_line = f'{sdate} {stime} {slevel} {self.name} {fn}({line}) {message}'

        with self.lock:
            # Write the main record.
            self.line_cnt += 1
            # _f.write(f'{out_line} {_line_cnt}\n')
            self.f.write(out_line)
            self.f.write('\n')

            # traceback?
            if tb is not None:
                for tbline in traceback.format_tb(tb):
                    for s in tbline.splitlines():
                        self.line_cnt += 1
                        # _f.write(f'{s} {_line_cnt}\n')
                        self.f.write(s + '\n')

            # Check limit.
            if self.line_cnt >= self.max:
                self.f.flush()
                self.f.close()
                old_fn = self.log_fn.replace('.log', '_old.log')
                try: os.remove(old_fn)
                except: pass
                os.rename(self.log_fn, old_fn)
                self.f = open(self.log_fn, self.mode)
                self.line_cnt = 0

    #-------------------------------------------------------------------------------
    def _make_readable(self, s):
        ''' Make non-printables visible.'''
        buff = []

        for ch in s:
            if ch >= ' ' and ch <= '~': # ascii printable
                buff.append(ch)
            elif ch in xlat_tbl:
                sout = xlat_tbl[ch]
                buff.append(left_delim)
                buff.append(sout)
                buff.append(right_delim)

            else: # Everything else is binary.
                buff.append(left_delim)
                if ch < ' ':
                    buff.append(f'0x{ord(ch):02X}')
                else:
                    buff.append(f'U+{ord(ch):04X}')
                buff.append(right_delim)

        return ''.join(buff) 
