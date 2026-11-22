from _support import *
from tools.module1 import validate_stakeholders, validate_workflow

class StakeholderWorkflowTests(unittest.TestCase):
    def test_11_stakeholders_pass(self): self.assertEqual([], validate_stakeholders(stakeholder_rows()))
    def test_12_six_stakeholders_required(self): self.assertTrue(any("six" in x for x in validate_stakeholders(stakeholder_rows()[:3])))
    def test_13_overbroad_authority_rejected(self):
        rows=stakeholder_rows(); rows[0]["decision_right"]="approves everything"; self.assertTrue(any("overbroad" in x for x in validate_stakeholders(rows)))
    def test_14_workflow_passes(self): self.assertEqual([], validate_workflow(workflow_rows()))
    def test_15_numeric_delay_required(self):
        rows=workflow_rows(); rows[0]["delay_minutes"]="soon"; self.assertTrue(any("numeric" in x for x in validate_workflow(rows)))
