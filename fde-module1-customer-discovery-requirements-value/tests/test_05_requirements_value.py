from _support import *
from tools.module1 import validate_requirements, validate_value

class RequirementsValueTests(unittest.TestCase):
    def test_21_requirements_pass(self): self.assertEqual([], validate_requirements(requirement_rows()))
    def test_22_eight_requirements_required(self): self.assertTrue(any("eight" in x for x in validate_requirements(requirement_rows()[:3])))
    def test_23_vague_requirement_rejected(self):
        rows=requirement_rows(); rows[0]["statement"]="The service shall be user-friendly."; self.assertTrue(any("vague" in x for x in validate_requirements(rows)))
    def test_24_value_scorecard_passes(self): self.assertEqual([], validate_value(value_rows()))
    def test_25_undefined_denominator_rejected(self):
        rows=value_rows(); rows[0]["denominator"]="all"; self.assertTrue(any("denominator" in x for x in validate_value(rows)))
