import sys
import os

# TODO1 eliminate this file?

current_line_color = 93 # yellow
exception_line_color = 92 # green
stack_location_color = 96 # cyan
prompt_color = 94 # blue
error_color = 91 # red

# Make non-printables visible.
xlat_tbl = { '\0':'NUL', '\n':'LF', '\r':'CR', '\t':'TAB', '\033':'ESC' }
left_delim = '<'
right_delim = '>'

def make_readable(s):
    buff = []

    # for k, v in xlat_tbl.items():
    #     s = s.replace(k, v)
    # return s

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
