import subprocess
import string
import re
import enum
import json
import xml
import xml.dom.minidom
try:
    from . import LuaFormat # normal import
except:
    import LuaFormat # unittest import


#-----------------------------------------------------------------------------------
def format_json(s):
    ''' Clean and format the string. Returns the new string. '''

    class ScanState(enum.IntFlag):
        DEFAULT = enum.auto()   # Idle
        STRING = enum.auto()    # Process a quoted string
        LCOMMENT = enum.auto()  # Processing a single line comment
        BCOMMENT = enum.auto()  # Processing a block/multiline comment
        DONE = enum.auto()      # Finito

    # tabWidth = 4
    comment_count = 0
    sreg = []
    state = ScanState.DEFAULT
    current_comment = []
    current_char = -1
    next_char = -1
    escaped = False

    # Index is in cleaned version, value is in original.
    pos_map = []

    # Iterate the string.
    try:
        slen = len(s)
        i = 0
        while i < slen:
            current_char = s[i]
            next_char = s[i + 1] if i < slen - 1 else -1

            # Remove whitespace and transform comments into legal json.
            if state == ScanState.STRING:
                sreg.append(current_char)
                pos_map.append(i)
                # Handle escaped chars.
                if current_char == '\\':
                    escaped = True
                elif current_char == '\"':
                    if not escaped:
                        state = ScanState.DEFAULT
                    escaped = False
                else:
                    escaped = False

            elif state == ScanState.LCOMMENT:
                # Handle line comments.
                if current_char == '\n':
                    # End of comment.
                    scom = ''.join(current_comment)
                    stag = f'\"//{comment_count}\":\"{scom}\",'
                    comment_count += 1
                    sreg.append(stag)
                    pos_map.append(i)
                    state = ScanState.DEFAULT
                    current_comment.clear()
                elif current_char == '\r':
                    # ignore
                    pass
                else:
                    # Maybe escape.
                    if current_char == '\"' or current_char == '\\':
                        current_comment.append('\\')
                    current_comment.append(current_char)

            elif state == ScanState.BCOMMENT:
                # Handle block comments.
                if current_char == '*' and next_char == '/':
                    # End of comment.
                    scom = ''.join(current_comment)
                    stag = f'\"//{comment_count}\":\"{scom}\",'
                    comment_count += 1
                    sreg.append(stag)
                    pos_map.append(i)
                    state = ScanState.DEFAULT
                    current_comment.clear()
                    i += 1  # Skip next char.
                elif current_char == '\n' or current_char == '\r':
                    # ignore
                    pass
                else:
                    # Maybe escape.
                    if current_char == '\"' or current_char == '\\':
                        current_comment.append('\\')
                    current_comment.append(current_char)

            elif state == ScanState.DEFAULT:
                # Check for start of a line comment.
                if current_char == '/' and next_char == '/':
                    state = ScanState.LCOMMENT
                    current_comment.clear()
                    i += 1  # Skip next char.
                # Check for start of a block comment.
                elif current_char == '/' and next_char == '*':
                    state = ScanState.BCOMMENT
                    current_comment.clear()
                    i += 1  # Skip next char.
                elif current_char == '\"':
                    sreg.append(current_char)
                    pos_map.append(i)
                    state = ScanState.STRING
                # Skip ws.
                elif current_char not in string.whitespace:
                    sreg.append(current_char)
                    pos_map.append(i)

            else:  # state == ScanState.DONE:
                pass
            i += 1  # next

        # Prep for formatting.
        ret = ''.join(sreg)

        # Remove any trailing commas.
        ret = re.sub(',}', '}', ret)
        ret = re.sub(',]', ']', ret)

        # Run it through the formatter.
        ret = json.loads(ret)
        ret = json.dumps(ret, indent=4)

    except json.JSONDecodeError as je:
        # Get some context from the original string.
        context = []
        original_pos = pos_map[je.pos]
        start_pos = max(0, original_pos - 40)
        end_pos = min(len(s) - 1, original_pos + 40)
        context.append(f'Json Error: {je.msg} pos: {original_pos}')
        context.append(s[start_pos:original_pos])
        context.append('---------here----------')
        context.append(s[original_pos:end_pos])
        ret = '\n'.join(context)

    return ret


#-----------------------------------------------------------------------------------
def format_xml(s, sindent):
    ''' Clean and format the string. Returns the new string. '''

    def clean(node):
        for n in node.childNodes:
            if n.nodeType == xml.dom.minidom.Node.TEXT_NODE:
                if n.nodeValue:
                    n.nodeValue = n.nodeValue.strip()
            elif n.nodeType == xml.dom.minidom.Node.ELEMENT_NODE:
                clean(n)
    
    try:
        top = xml.dom.minidom.parseString(s)
        clean(top)  
        top.normalize()
        ret = top.toprettyxml(indent=sindent)
    except Exception as e:
        ret = f"Error: {e}"

    return ret


#-----------------------------------------------------------------------------------
def format_cx(s, syntax, indent):
    ''' Clean and format C/C++/C# string. Returns the new string. '''

    # Build the command. Uses --style=allman --indent=spaces=4 --indent-col1-comments --errors-to-stdout
    sindent = f"-s{indent}"
    p = ['astyle', '-A1', sindent, '-Y', '-X']
    if syntax == 'C#': # else default of C
        p.append('--mode=cs')

    try:
        cp = subprocess.run(p, input=s, text=True, universal_newlines=True, capture_output=True, shell=True, check=True)
        sout = cp.stdout
    except Exception:
        sout = "Format Cx failed. Is astyle installed and in your path?"

    return sout


#-----------------------------------------------------------------------------------
def format_lua(s, indent):
    ''' Clean and format lua string. Returns the new string. '''

    lines = s.splitlines()
    sout = LuaFormat.lua_format(lines, indent)

    return sout
