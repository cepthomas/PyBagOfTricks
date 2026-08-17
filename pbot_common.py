import sys
import os

# TODO eliminate this file?

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
    out_pos = 0

    # for k, v in xlat_tbl.items():
    #     s = s.replace(k, v)
    # return s

    for ch in s:
        if ch >= ' ' and ch <= '~': # ascii printable
            buff.append(ch)
            out_pos += 1

        elif ch in xlat_tbl:
            start_pos = out_pos
            sout = xlat_tbl[ch]
            buff.append(sout)
            out_pos += len(sout)

        else: # Everything else is binary.
            start_pos = out_pos
            if ch < ' ':
                sout = f'{left_delim}0x{ord(ch):02X}{right_delim}'
                buff.append(sout)
                out_pos += len(sout)
            else:
                sout = f'{left_delim}U+{ord(ch):04X}{right_delim}'
                buff.append(sout)
                out_pos += len(sout)

    return buff
