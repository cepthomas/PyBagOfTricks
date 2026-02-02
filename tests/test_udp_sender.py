# import sys
import os
import importlib
import utils
import random
import time


# Add source path to sys.path.
my_dir = os.path.dirname(__file__)
utils.ensure_import(my_dir, '..')
# OK to import now.
import udp_tools
# Benign reload in case it's edited.
importlib.reload(udp_tools)


lines = []
with open('ross.txt') as f:
    lines = f.readlines()
lenl = len(lines)


# outer loop
for i in range(5):
    # inner loop
    for j in range(10):
        r =  random.randrange(0, lenl)
        udp_tools.send(lines[r].rstrip())
        time.sleep(0.05)
    time.sleep(0.5)
