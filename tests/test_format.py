import sys
import os
import unittest
import utils


#-----------------------------------------------------------------------------------
my_dir = os.path.dirname(__file__)
# Add source path to sys.
utils.ensure_import(my_dir, '..')
# OK to import now.
import code_format
# # Benign reload in case of edited.
# importlib.reload(tr)


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
            res = code_format.format_xml(s, 4)
            if 'Error:' in res:
                self.fail(res)
            else:
                self.assertEqual(res[100:150], 'nType="Anti-IgG (PEG)" TestSpec="08 ABSCR4 IgG" Du')

            # Make it a bad file.
            s = s.replace('ColumnType=', '')
            res = code_format.format_xml(s, 4)
            self.assertEqual(res, "Error: not well-formed (invalid token): line 6, column 4")


    #------------------------------------------------------------
    def test_format_c(self):

        fn = os.path.join(my_dir, 'messy.c')
        with open(f'{fn}', 'r') as fp:
            # The happy path.
            s = fp.read()
            res = code_format.format_cx(s, 'C', 4)
            self.assertEqual(res[450:475], '[1] = (val >> 8) & 0xFF;\n')


    #------------------------------------------------------------
    def test_format_cs(self):

        fn = os.path.join(my_dir, 'messy.cs')
        with open(f'{fn}', 'r') as fp:
            # The happy path.
            s = fp.read()

            res = code_format.format_cx(s, 'C#', 4)
            self.assertEqual(res[700:738], '\n    public Dumper(TextWriter writer)\n')

