from _support import *
from tools.module1 import validate_accessibility, validate_ai_decision, validate_problem_frame

class FrameAccessAITests(unittest.TestCase):
    def test_16_problem_frame_passes(self): self.assertEqual([], validate_problem_frame(problem_frame()))
    def test_17_request_is_not_root_problem(self):
        value=problem_frame(); value["root_problem_hypothesis"]=value["customer_request"]; self.assertTrue(any("distinguished" in x for x in validate_problem_frame(value)))
    def test_18_accessibility_record_passes(self): self.assertEqual([], validate_accessibility(accessibility_rows()))
    def test_19_assumed_accessibility_evidence_rejected(self):
        rows=accessibility_rows(); rows[0]["evidence_source"]="assumed"; self.assertTrue(any("evidence source" in x for x in validate_accessibility(rows)))
    def test_20_ai_decision_passes(self): self.assertEqual([], validate_ai_decision(ai_decision()))
