import unittest
import os
import py_compile

class ExamplesCompileTest(unittest.TestCase):
    def test_local_reversal_indicator_compiles(self):
        example_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'local_reversal_indicator.py')
        )
        if not os.path.exists(example_path):
            self.skipTest(f"{example_path} not found")
        py_compile.compile(example_path, doraise=True)
