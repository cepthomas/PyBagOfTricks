import sys
import os
import datetime
import shutil
import traceback
import threading
import pdb

# Dumb simple logger for python.


class Plog:
    # Options for making bin readable. These could be uxer configurable.
    xlat_tbl = { 0:'NUL', 10:'LF', 13:'CR', 9:'TAB', 27:'ESC' }
    left_delim = '<' # '|'
    right_delim = '>' #'|'
    
    #---------------------------- Lifecycle ----------------------------------------

    #-------------------------------------------------------------------------------
    def __init__(self, name, fn, append=True, keep_open=True, max=50000):
        ''' Start the logger
            - logger name
            - log file name
            - append or overwrite new file
            - keep log file open. Open: 5-10 usec per write, Close: 200-300 usec
            - max file size
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

        # Maybe roll over log now.
        if os.path.exists(self.log_fn) and os.path.getsize(self.log_fn) > max:
            bup = self.log_fn.replace('.log', '_old.log')
            shutil.copyfile(self.log_fn, bup)
            # Clear current log file.
            with open(self.log_fn, 'w'):
                pass

        if keep_open:
            # Open file now and keep it open.
            with self.lock:
                try:
                    self.f = open(self.log_fn, self.mode, encoding='utf-8')
                except Exception as e:
                    self.stop()
                    self.error(f'Failed to open log file: {self.log_fn}', e.__traceback__)


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
    def error(self, message, tb=None, readable=False):
        '''Client logger function.'''
        if self.enabled:
            tb = None if not tb else tb
            self._write_log('ERR', message, tb=tb, readable=readable)

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
        return f'plog name:{self.name} mode:{self.mode} fn:{self.log_fn} max:{self.max}'


    #---------------------------- Private Functions --------------------------------

    #-------------------------------------------------------------------------------
    def _write_log(self, slevel, message, tb=None, readable=False):
        '''Format a standard message with caller info and log it.'''
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
            flog = self.f or open(self.log_fn, 'a', encoding='utf-8')

            flog.write(out_line + '\n')
            # traceback?
            if tb is not None:
                for tbline in traceback.format_tb(tb):
                    for s in tbline.splitlines():
                        flog.write(s + '\n')

            if not self.f:
                flog.flush()
                flog.close()

    #-------------------------------------------------------------------------------
    def _make_readable(self, s):
        ''' Make non-printables visible.'''
        buff = []
        bytes = s.encode("utf-8")

        for b in bytes:
            if b >= ord(' ') and b <= ord('~'): # ascii printable
                buff.append(chr(b))
            elif b in self.xlat_tbl:
                sxlat = self.xlat_tbl[b]
                buff.append(self.left_delim)
                buff.append(sxlat)
                buff.append(self.right_delim)
            else: # Everything else is binary.
                buff.append(self.left_delim)
                buff.append(f'0x{b:02X}')
                buff.append(self.right_delim)

        return ''.join(buff) 
