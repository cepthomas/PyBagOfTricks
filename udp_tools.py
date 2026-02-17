import sys
import socket
import os
import random
import time



# Optional ansi color for categories.
CATS = { "INF":37, "DBG":93, "ERR":91 }

# Delimiter for message lines. LF=10  CR=13  NUL=0
MDEL = '\u000a'

# Debug.
SEQ_NUM = False
seq_num = 0

# Send a UDP message.
def send(msg, host, port, cat=None):
    if SEQ_NUM:
        global seq_num
        msg = f'[{seq_num}]{msg}'
        seq_num = seq_num + 1

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            msg = f'\u001b[{CATS[cat]}m{msg}\u001b[0m{MDEL}' if cat in CATS else f'{msg}{MDEL}'
            udp_socket.sendto(msg.encode('utf-8'), (host, port))

    except Exception as e:
        print(f"An error occurred: {e}")
        pass
