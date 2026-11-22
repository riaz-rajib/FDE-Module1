from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.module1 import ROOT, file_digest


def research_plan():
    return {
        "plan_id":"RP-001", "purpose":"Understand the synthetic casework problem before selecting a solution.",
        "research_objectives":["Understand current work", "Test the backlog assumptions"],
        "research_questions":["Who is affected?", "Where does work wait?", "Which decisions need authority?", "What would success mean?"],
        "assumptions":["Queue count is unique", "Triage is the main delay", "Digital is the preferred channel"],
        "participant_groups":["Sponsor", "Operator", "Affected user", "Risk adviser", "Finance"],
        "methods":["Semi-structured interview", "Workflow observation walk-through"],
        "inclusion_adjustments":["Provide questions in advance", "Support audio-only participation"],
        "consent_and_recording_boundary":"Fictional personas only; no recording or personal information.",
        "data_handling":"Generated notes retained only for this synthetic assessment.",
        "non_goals":["Production design", "Policy conclusion"], "decision_owner":"Service owner",
        "schedule":"Six sessions across five synthetic working days", "limitations":["No real participant evidence"]
    }


def stakeholder_rows():
    return [
        {"stakeholder_id":f"STK-{i:02d}","role":role,"affected_or_accountable":kind,"influence":"high","impact":"high","decision_right":right,"evidence_source":"persona card","escalation_trigger":"conflicting authority"}
        for i,(role,kind,right) in enumerate([
            ("Sponsor","accountable","discovery purpose"),("Service owner","accountable","operational acceptance"),
            ("Caseworker","affected","validate workflow"),("Applicant advocate","affected","validate user need"),
            ("Risk adviser","accountable","security advice"),("Finance","accountable","cost assumptions")
        ],1)
    ]


def workflow_rows():
    return [
        {"stage_id":f"STG-{i:02d}","actor":actor,"trigger":"prior stage complete","action":action,"handoff_to":"next role","evidence_source":"persona walk-through","delay_minutes":"30","failure_demand":"repeat contact","accessibility_barrier":"unclear status","uncertainty":"timing unvalidated"}
        for i,(actor,action) in enumerate([("Applicant","submit"),("Intake","validate"),("Caseworker","triage"),("Specialist","review"),("Service owner","decide")],1)
    ]


def problem_frame():
    return {"frame_id":"PF-001","customer_request":"Build an AI queue","observed_symptoms":["aged queue","repeat contacts"],"user_needs":["understand status","provide information once"],"root_problem_hypothesis":"Incomplete intake and unclear hand-off ownership create avoidable delay.","assumptions":["counts are unique","sample is representative"],"constraints":["assisted channel remains","policy controls remain"],"non_goals":["production AI","policy redesign"],"outcome_hypothesis":"Clear intake and ownership will reduce avoidable wait and contacts.","affected_groups":["applicants","caseworkers"],"evidence_strength":"Synthetic interviews and generated fixtures only","decision_owner":"Service owner","review_trigger":"baseline definition changes","product_implications":["status capability may be reusable"]}


def accessibility_rows():
    return [
        {"need_id":f"ACC-{i:02d}","user_group":group,"barrier":barrier,"context":"synthetic service journey","evidence_source":"persona statement","adjustment":adjustment,"acceptance_implication":"observable task result","owner":"service owner","status":"open"}
        for i,(group,barrier,adjustment) in enumerate([("screen magnifier users","small fixed layout","reflow and zoom support"),("non-digital users","digital-only path","assisted channel"),("cognitive accessibility","unclear status language","plain-language status")],1)
    ]


def ai_decision():
    return {"decision_id":"AI-001","proposed_use":"AI-assisted triage recommendation","necessary_or_alternative":"Compare with rules and workflow repair","affected_people":["applicants","caseworkers"],"intended_benefit":"reduce avoidable triage effort","risks":["incorrect priority","hidden rationale"],"data_boundary":"generated records only","human_decision_authority":"authorised caseworker","contestability":"operator can reject and record a reason","authorisation_owner":"AI use-case owner, not assigned in this exercise","suitability_decision":"explore_with_controls","evidence_mode":"Synthetic","limitations":["no evaluation","no production authority"],"review_trigger":"data, purpose or authority changes"}


def requirement_rows():
    return [
        {"requirement_id":f"REQ-{i:03d}","source_need_id":f"NEED-{(i%3)+1:02d}","statement":f"The synthetic service shall expose observable outcome {i}.","type":"functional","priority":"must","acceptance_criterion":f"It is done when test {i} records the expected result.","verification_method":"demonstration","decision_owner":"service owner","status":"proposed","assumption_or_constraint":"generated records only","version":"1.0"}
        for i in range(1,9)
    ]


def value_rows():
    values=[]
    for i,kind in enumerate(["baseline","leading","lagging","guardrail","cost"],1):
        values.append({"measure_id":f"VAL-{i:02d}","outcome_link":"OUT-01","measure_type":kind,"definition":f"Defined {kind} measure","numerator":"eligible synthetic events with outcome","denominator":"all eligible synthetic events entering the stage in the period","data_source":"generated fixture","baseline_value":"18","target_value":"12","owner":"performance analyst","cadence":"weekly","limitations":"synthetic and unvalidated"})
    return values


def observation_rows():
    categories=["integration friction","documentation or usability defect","reusable capability gap","unvalidated observation"]
    return [{"observation_id":f"OBS-{i:02d}","category":kind,"observation":"Synthetic field observation","evidence_link":"notes/session.md","affected_users":"caseworkers","confidence":"medium","counter_evidence":"one persona disagreed","generalisation_limit":"single fictional engagement","product_boundary":"review for reusable capability","owner":"product manager","next_validation":"compare another synthetic scenario","status":"open"} for i,kind in enumerate(categories,1)]


def manifest():
    return {"engagement_id":"ENG-FDE1-001","manifest_version":"1.0","claims":[{"claim_id":"CLM-001","statement":"The workspace passed the local structural validator.","execution_mode":"Local live","validation_method":"Machine-verified","observer_or_verifier":"tools/module1.py","artefacts":["validation.txt"],"captured_at":"2026-08-19T00:00:00Z","environment":"local synthetic lab","redaction":"none; generated data only","limitations":["no customer or production proof"],"retention":"learner and assessor; delete after portfolio sanitisation"}]}
