from _support import *
from tools.module1 import baseline_errors, read_json, validate_scenario

class BundleTests(unittest.TestCase):
    def test_01_baseline_passes(self): self.assertEqual([], baseline_errors(ROOT))
    def test_02_scenario_is_synthetic(self): self.assertEqual("synthetic_only", read_json(ROOT/"scenario"/"meridian-public-services.json")["data_status"])
    def test_03_scenario_uses_reserved_domain(self): self.assertTrue(read_json(ROOT/"scenario"/"meridian-public-services.json")["fictional_domain"].endswith(".invalid"))
    def test_04_seven_unique_personas(self):
        ids=[x["persona_id"] for x in read_json(ROOT/"personas"/"index.json")["personas"]]; self.assertEqual(7,len(ids)); self.assertEqual(len(ids),len(set(ids)))
    def test_05_scenario_schema_passes(self): self.assertEqual([], validate_scenario(read_json(ROOT/"scenario"/"meridian-public-services.json")))
