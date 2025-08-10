import sys
import os
import unittest
from unittest.mock import MagicMock

# Set up the sublime emulation environment.
import emu_sublime_api as emu

# Import the code under test.
import sbot_format
# import sbot_common as sc


#-----------------------------------------------------------------------------------
class TestFormat(unittest.TestCase):  # TEST more tests

    def setUp(self):
        
        self.my_dir = os.path.dirname(__file__)

        # mock_settings = {
        #     "tab_size": 4,
        # }
        # emu.set_settings(mock_settings)

    def tearDown(self):
        pass


    #------------------------------------------------------------
    def test_format_json(self):
        v = emu.View(601)

        fn = os.path.join(self.my_dir, 'messy.json')
        with open(f'{fn}', 'r') as fp:
            # The happy path.
            s = fp.read()
            cmd = sbot_format.SbotFormatJsonCommand(v)
            res = cmd._do_one(s)
            self.assertEqual(res[:50], '{\n    "MarkPitch": {\n        "Original": 0,\n      ')

            # Make it a bad file.
            s = s.replace('\"Original\"', '')
            res = cmd._do_one(s)
            self.assertEqual(res[:50], "Json Error: Expecting property name enclosed in do")


    #------------------------------------------------------------
    def test_format_xml(self):
        v = emu.View(602)

        fn = os.path.join(self.my_dir, 'messy.xml')
        with open(f'{fn}', 'r') as fp:
            # The happy path.
            s = fp.read()
            cmd = sbot_format.SbotFormatXmlCommand(v)
            res = cmd._do_one(s, '    ')

            if 'Error:' in res:
                self.fail(res)
            else:
                self.assertEqual(res[100:150], 'nType="Anti-IgG (PEG)" TestSpec="08 ABSCR4 IgG" Du')

            # Make it a bad file.
            s = s.replace('ColumnType=', '')
            res = cmd._do_one(s, '    ')
            self.assertEqual(res, "Error: not well-formed (invalid token): line 6, column 4")
