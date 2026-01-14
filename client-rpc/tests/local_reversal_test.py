import unittest
import py_compile
import pathlib

class LocalReversalCompileTest(unittest.TestCase):
    def test_example_compiles(self):
        example = pathlib.Path(__file__).resolve().parents[2] / 'examples' / 'local_reversal_indicator.py'
        py_compile.compile(str(example), doraise=True)

if __name__ == '__main__':
    unittest.main()
