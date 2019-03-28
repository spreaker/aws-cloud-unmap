import os
import unittest
from flake8.api import legacy as flake8

CURR_DIR = os.path.dirname(os.path.realpath(__file__))


class TestPep8(unittest.TestCase):
    def testPep8Compliance(self):
        style = flake8.get_style_guide(quiet=False, config_file="setup.cfg")
        pythonFiles = []

        # Get source files
        for root, dirs, files in os.walk(CURR_DIR + "/../cloudunmap"):
            pythonFiles += [os.path.join(root, f) for f in files if f.endswith('.py')]

        # Get test files
        for root, dirs, files in os.walk(CURR_DIR + "/../tests"):
            pythonFiles += [os.path.join(root, f) for f in files if f.endswith('.py')]

        # Run linter
        report = style.check_files(pythonFiles)

        for violation in ["E", "F", "W"]:
            self.assertEqual(report.get_statistics(violation), [], msg=f"Flake8 found violations of level {violation}")
