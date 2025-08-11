import sys
import os
import unittest
# from unittest.mock import MagicMock
import code_format


#-----------------------------------------------------------------------------------
my_dir = os.path.dirname(__file__)

# Add source path to sys.
src_dir = os.path.abspath(os.path.join(my_dir, '..'))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir) # or? sys.path.append(path)


#-----------------------------------------------------------------------------------
class TestFormat(unittest.TestCase): 

    def setUp(self):
        pass

    def tearDown(self):
        pass


    #------------------------------------------------------------
    def test_format_json(self):

        fn = os.path.join(my_dir, 'messy.json')
        with open(f'{fn}', 'r') as fp:
            # The happy path.
            s = fp.read()
            # cmd = sbot_format.SbotFormatJsonCommand(v)
            # res = cmd._do_one(s)
            res = code_format.format_json(s)
            self.assertEqual(res[:50], '{\n    "MarkPitch": {\n        "Original": 0,\n      ')

            # Make it a bad file.
            s = s.replace('\"Original\"', '')
            res = code_format.format_json(s)
            self.assertEqual(res[:50], "Json Error: Expecting property name enclosed in do")


    #------------------------------------------------------------
    def test_format_xml(self):

        fn = os.path.join(my_dir, 'messy.xml')
        with open(f'{fn}', 'r') as fp:
            # The happy path.
            s = fp.read()
            # cmd = sbot_format.SbotFormatXmlCommand(v)
            # res = cmd._do_one(s, '    ')
            res = code_format.format_xml(s, 4)

            if 'Error:' in res:
                self.fail(res)
            else:
                self.assertEqual(res[100:150], 'nType="Anti-IgG (PEG)" TestSpec="08 ABSCR4 IgG" Du')

            # Make it a bad file.
            s = s.replace('ColumnType=', '')
            # res = cmd._do_one(s, '    ')
            res = code_format.format_xml(s, 4)
            self.assertEqual(res, "Error: not well-formed (invalid token): line 6, column 4")


# TODO1 test CX
