from _support import *
from tools.module1 import ValidationError, control_errors, resolve_inside, validate_manifest, validate_observations, verify_evidence

class EvidenceControlTests(unittest.TestCase):
    def test_26_observations_pass(self): self.assertEqual([], validate_observations(observation_rows()))
    def test_27_manifest_passes(self): self.assertEqual([], validate_manifest(manifest()))
    def test_28_invalid_method_rejected(self):
        value=manifest(); value["claims"][0]["validation_method"]="Self-certified"; self.assertTrue(any("validation_method" in x for x in validate_manifest(value)))
    def test_29_control_forbidden_key_rejected(self):
        value={"catalogue_version":"1","fault_id":"HUM-COMMS-101","assessment_impact":"A2","authorised_by":"assessor","issued_utc":"2026-08-19T00:00:00Z","changed_constraint":"test","learner_visible_text":"test","expected_answer":"secret"}; self.assertTrue(any("forbidden" in x for x in control_errors(value)))
    def test_30_reset_path_must_stay_inside_work(self):
        with self.assertRaises(ValidationError): resolve_inside(ROOT/"README.md",ROOT/"work")
