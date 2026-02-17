import os
import importlib
import utils
import random
import time


######################################################
# This is not a python unittest.
# use:
#   run a UDP client e.g. NTerm udp localhost 59140
#   then py test_udp_sender
######################################################


# Add source path to sys.path.
my_dir = os.path.dirname(__file__)
utils.ensure_import(my_dir, '..')
# OK to import now.
import udp_tools
# Benign reload in case it's edited.
importlib.reload(udp_tools)

# Configuration
HOST = 'localhost'
PORT = 59140

lines = []
with open('ross.txt') as f:
    lines = f.readlines()
lenl = len(lines)

num_to_send = 10

# outer loop
for i in range(5):
    print('Sent lines:', i * num_to_send)
    # inner loop
    for j in range(num_to_send):
        r =  random.randrange(0, lenl)
        udp_tools.send(f'>>>{i * 10 + j} {lines[r].rstrip()}', HOST, PORT)
        time.sleep(0.05)
    time.sleep(0.5)

print('fini!')