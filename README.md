
# PyBagOfTricks

Python odds and ends, mainly for debugging (esp. Sublime Text plugins).

![logo](felix600.jpg)


# PbotPdb 

- Server for debugging python remotely over a tcp connection.
- Initially developed for debugging Sublime Text plugins but is actually generally useful standalone.
- There's a fair amount hacked from [remote-db](https://github.com/ionelmc/python-remote-pdb).
- Built for ST4 on Windows. Linux and OSX should be ok but are minimally tested.

## Features

- Uses generic tcp client - linux terminal, windows putty, etc. Or optional companion [Fancy Client](#fancy-client).
- Option for colorizing of output. Totally unnecessary but cute.
- Optional timeout can be set to force socket closure which unfreezes the ST application rather
  than having to forcibly shut it down.

![Plugin Pdb](cli1.png)

## Usage

General workflow goes something like the following. A typical usage is demonstrated with
[this example](https://github.com/cepthomas/PyBagOfTricks/blob/main/tests/test_pdb.py).

1. Copy `pbot_pdb.py` to the directory of the code you are debugging.

1. Optionally edit the configuration block in this file. A `sublime-settings` file doesn't make sense for this plugin. Settings are hard-coded in the py files themselves. This seems ok since they are unlikely to change often.

1. Edit the file being debugged and add this at the place you want to break:

  `import pbot_pdb; pbot_pdb.breakpoint()`

1. Run your client of choice.

1. Run the code being debugged. Client should break at the breakpoint line.

1. Now you can use any of the standard pdb commands.


## Fancy Client

Optionally you can use the smarter `pbot_pdb_client.py` script which does all of the above plus:
- Automatically connects to the server. This means that you can edit/run your code
  without having to restart the client.
- Detects unresponsive server by requiring a response for each command sent.
- Provides some extra system status information, indicated by `!` (or marker of your choosing).
- Workflow is similar to the above except you can now reload/run the code as part of your dev/edit cycle.
- Optionally edit the configuration block in this file.
- Use ctrl-C to exit the client. The server will also stop/unblock.

![Fancy Client](cli2.png)

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
    sys.__excepthook__(type, value, traceback)

# Connect the last chance hook.
sys.excepthook = excepthook
```

# Remote Log
remlog.py is a simple tool to broadcast UDP log messages from a balck-box component.
Alos used for sublime plugin debugging using print() semantics.

# Tracer
Tool for tracing through code, especially function entry/exit.
The best (only) documentation is to read [the example](https://github.com/cepthomas/PyBagOfTricks/blob/main/tests/test_tracer.py).
