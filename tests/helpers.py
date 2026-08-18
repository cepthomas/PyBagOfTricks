import sys
import os


# Add file location to python path.
def add_parent_to_path():
    frame = sys._getframe(1)
    dir = os.path.dirname(frame.f_code.co_filename)
    sys.path.append(os.path.abspath(os.path.join(dir, '..')))

# Get caller's dir.
def my_dir():
    frame = sys._getframe(1)
    dir = os.path.dirname(frame.f_code.co_filename)
    return dir

# Init log. explain args.
def init_log(dir, *subdirs, clean=False):
    log_fn = os.path.abspath(os.path.join(dir, *subdirs))
    # log_fn = os.path.abspath(os.path.join(os.path.dirname(__file__), 'out', 'test_plog.log'))
    if clean:
        try: os.remove(log_fn)
        except: pass
    return log_fn
