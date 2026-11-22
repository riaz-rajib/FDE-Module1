from _support import *
from tools.module1 import validate_research_plan

class ResearchTests(unittest.TestCase):
    def test_06_complete_plan_passes(self): self.assertEqual([], validate_research_plan(research_plan()))
    def test_07_four_questions_required(self):
        value=research_plan(); value["research_questions"]=["one"]; self.assertTrue(any("research_questions" in x for x in validate_research_plan(value)))
    def test_08_interview_method_required(self):
        value=research_plan(); value["methods"]=["Workflow observation"]; self.assertTrue(any("interview" in x for x in validate_research_plan(value)))
    def test_09_observation_method_required(self):
        value=research_plan(); value["methods"]=["Interview"]; self.assertTrue(any("observation" in x for x in validate_research_plan(value)))
    def test_10_live_email_rejected(self):
        value=research_plan(); value["purpose"]="Contact person@example.com"; self.assertTrue(any("non-reserved email" in x for x in validate_research_plan(value)))
