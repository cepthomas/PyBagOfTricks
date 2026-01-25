# import sys
import os
import importlib
import utils
import random
import time


# Use a script similar to:
# cls
# start C:\Dev\Apps\NTerm\bin\net8.0-windows\win-x64\NTerm.exe udp 127.0.0.1 51111
# timeout 1
# py test_udp_sender.py


# Add source path to sys.path.
my_dir = os.path.dirname(__file__)
utils.ensure_import(my_dir, '..')
# OK to import now.
import udp_sender
# Benign reload in case it's edited.
importlib.reload(udp_sender)


lines = []
with open('ross.txt') as f:
    lines = f.readlines()
lenl = len(lines)


# CATS = { "INF":37, "DBG":93, "ERR":91 }

# outer loop
for i in range(5):
    # inner loop
    for j in range(10):
        r =  random.randrange(0, lenl)
        udp_sender.send(lines[r].rstrip())
        time.sleep(0.05)
    time.sleep(0.5)
