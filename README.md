# PyBagOfTricks

Python odds and ends, mainly for debugging (esp. Sublime Text plugins).

# PbotPdb

- Component for debugging python remotely over a TCP connection.
- Initially built to debug Sublime Text plugins but is actually generally useful standalone.
- Built for ST4 on Windows. Linux and OSX should be ok but are minimally tested.
- Uses generic telnet client - linux terminal, windows telnet/putty, etc.
- Option for colorizing of output. Totally unnecessary but cute. (note - doesn't work with windows telnet).

![Plugin Pdb](cli1.png)

## Usage

1. Copy `pbot_pdb.py` to the directory of the code you are debugging.
1. Edit the file being debugged [ex](https://github.com/cepthomas/PyBagOfTricks/blob/main/tests/ppdb_target.py).
    - Add `from pbot_pdb import breakpoint`
    - Add this at the place you want to break: `breakpoint(<port>)`
    - Other options are: `breakpoint(59120, log_fn=<your-log>, use_color=T/F)`
1. Run your client of choice.
1. Run the code being debugged. Client should break at the breakpoint line.
1. Now you can use any of the standard pdb commands.

## Notes

Because of the nature of remote debugging, issuing a `q(uit)` command instead of `c(ont)` causes
  an unhandled [BdbQuit exception](https://stackoverflow.com/a/34936583).
  Similarly, unhandled `ConnectionError` can occur. They are harmless but if it annoys you,
  add (or edit) this code somewhere in your code being debugged:

```python
import bdb
def excepthook(type, value, tb):
    if issubclass(type, bdb.BdbQuit) or issubclass(type, ConnectionError):
        return  # ignore
    sys.__excepthook__(type, value, tb)

# Connect the last chance hook.
sys.excepthook = excepthook
```

# Plog
Dumb simple logger for python. One per client module, threadsafe.

`l = plog.Plog('PPDB', <your-log>, keep_open=False)`

Usage - see [test](https://github.com/cepthomas/PyBagOfTricks/blob/main/tests/ppdb_target.py).


# Tracer
Tool for tracing through code, especially function entry/exit.
The best (only) documentation is to read [the test](https://github.com/cepthomas/PyBagOfTricks/blob/main/tests/test_tracer.py).
