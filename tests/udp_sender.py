import sys
import socket
import os
import importlib
import random
import time


# Add path to logger.
npath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if npath not in sys.path:
    sys.path.insert(0, npath)
import plog


# Where to log. Usually same as the server log. None indicates no logging.
LOG_FN = os.path.join(os.path.dirname(__file__), '..', 'log', 'udp_sender.log')

HOST = '127.0.0.1' # 'localhost'
PORT = 59140
# Delimiter for message lines. LF=10  CR=13  NUL=0
MDEL = ''
# MDEL = '\u0000'
TIMEOUT = 5

seq_num = 0

lines = [
    "===first-line-ross===",
    "We can always carry this a step further. There's really no end to this.",
    "Here's some embedded ansi color codes! [38;2;204;39;187mYou have freedom here.[0mThe only guide is your heart.",
    "Let's give him a friend too. Everybody needs a friend. Follow the lay of the land. It's most important. Only eight colors that you need. Now we can begin working on lots of happy little things. Even the worst thing we can do here is good.",
    "Nothing wrong with washing your brush. What the devil. Fluff that up.",
    "You have freedom here. The only guide is your heart. We can always carry this a step further. There's really no end to this. ",
    "I really recommend you use odorless thinner or your spouse is gonna run you right out into the yard and you'll be working by yourself.",
    "Let's give him a friend too. Everybody needs a friend. Follow the lay of the land. It's most important. Only eight colors that you need. ",
    "Now we can begin working on lots of happy little things. Even the worst thing we can do here is good.",
    "Let's do it again then, what the heck. Everything's not great in life, but we can still find beauty in it.",
    "Use what happens naturally, don't fight it. How do you make a round circle with a square knife? That's your challenge for the day. These little son of a guns hide in your brush and you just have to push them out.",
    "If it's not what you want - stop and change it. Don't just keep going and expect it will get better.",
    "Let all these things just sort of happen. As trees get older they lose their chlorophyll. So often we avoid running water, and running water is a lot of fun. And just raise cain. You don't have to be crazy to do this but it does help.",
    "This is a happy place, little squirrels live here and play. We'll do another happy little painting.",
    "Exercising the imagination, experimenting with talents, being creative; these things, to me, are truly the windows to your soul.",
    "Once you start, they sort of just make themselves.",
    "===last-line-ross===",
    ]

# Send function.
def send(msg):
    global seq_num
    seq_num = seq_num + 1
    msg = f'[{seq_num}]{msg}'

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            msg = f'{msg}{MDEL}'
            udp_socket.sendto(msg.encode('utf-8'), (HOST, PORT))

    except Exception as e:
        plog.error("An error occurred", e)


# Wait until we are told to go.
exit = False
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    if TIMEOUT > 0:
        sock.settimeout(TIMEOUT)  # Seconds.
    plog.debug(f'UDP on {HOST}:{PORT} [{TIMEOUT}]')

    while not exit:
        try:
            data, _ = sock.recvfrom(4096) # blocks
            msg = data.decode('utf-8')
            plog.debug(f'Received message: {msg}')

            if msg == 'GO':
                # outer loop
                for i in range(5):
                    # inner loop
                    for j in range(5):
                        r =  random.randrange(0, len(lines))
                        send(lines[r].rstrip())
                        time.sleep(0.05)
                    time.sleep(0.2)
                exit = True

        except (ConnectionError, socket.timeout) as e:
            plog.debug(f'ConnectionError timeout')
            # future use
            time.sleep(5)

        except Exception as e:
            plog.debug(f'CommIf.readline() exception: {str(e)}')
            raise # hard fail
