from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_MODES = {"Portable", "Rendered", "Synthetic", "Local live", "Provider live", "Unproved"}
ALLOWED_METHODS = {"Machine-verified", "Assessor-observed", "Peer-observed", "Customer-simulated", "Document-reviewed"}
PLACEHOLDERS = {"", "REPLACE_ME", "TBD", "CHOOSE", "UNSET"}
SAFE_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.invalid$")
DOC_IPV4_PREFIXES = ("192.0.2.", "198.51.100.", "203.0.113.")
FAULT_ID = re.compile(r"^[A-Z]+-[A-Z0-9]+-[0-9]{3}$")
FORBIDDEN_CONTROL_KEYS = {
    "customer_credentials", "external_system", "live_data", "production_access",
    "secret_value", "injection_mechanism", "expected_answer", "diagnostic_shortcut",
}
OBSERVATION_CATEGORIES = {
    "customer-specific configuration", "integration friction", "documentation or usability defect",
    "reusable capability gap", "product defect", "operational or commercial constraint",
    "unvalidated observation",
}


class ValidationError(ValueError):
    pass


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path}: {exc}") from exc


def read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except OSError as exc:
        raise ValidationError(f"{path}: {exc}") from exc


def is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() not in PLACEHOLDERS
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def require(obj: dict[str, Any], fields: Iterable[str], label: str) -> list[str]:
    return [f"{label}: missing or placeholder field {field}" for field in fields if not is_present(obj.get(field))]


def walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_strings(item)


def unsafe_reference_errors(value: Any, label: str) -> list[str]:
    errors: list[str] = []
    email_pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    ip_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    for text in walk_strings(value):
        for address in email_pattern.findall(text):
            if not SAFE_EMAIL.match(address):
                errors.append(f"{label}: non-reserved email reference {address}")
        for address in ip_pattern.findall(text):
            if not address.startswith(DOC_IPV4_PREFIXES):
                errors.append(f"{label}: non-documentation IPv4 reference {address}")
    return errors


def validate_research_plan(obj: dict[str, Any]) -> list[str]:
    fields = [
        "plan_id", "purpose", "research_objectives", "research_questions", "assumptions",
        "participant_groups", "methods", "inclusion_adjustments", "consent_and_recording_boundary",
        "data_handling", "non_goals", "decision_owner", "schedule", "limitations",
    ]
    errors = require(obj, fields, "research plan")
    for field, minimum in (("research_objectives", 2), ("research_questions", 4), ("assumptions", 3), ("participant_groups", 4)):
        if isinstance(obj.get(field), list) and len(obj[field]) < minimum:
            errors.append(f"research plan: {field} requires at least {minimum} entries")
    methods = {str(x).lower() for x in obj.get("methods", [])}
    if not any("interview" in x for x in methods):
        errors.append("research plan: include an interview method")
    if not any("observation" in x or "walk-through" in x for x in methods):
        errors.append("research plan: include observation or a workflow walk-through")
    return errors + unsafe_reference_errors(obj, "research plan")


def validate_stakeholders(rows: list[dict[str, str]]) -> list[str]:
    required = ["stakeholder_id", "role", "affected_or_accountable", "influence", "impact", "decision_right", "evidence_source", "escalation_trigger"]
    errors: list[str] = []
    if len(rows) < 6:
        errors.append("stakeholder matrix: at least six rows required")
    ids: list[str] = []
    for index, row in enumerate(rows, 1):
        errors.extend(require(row, required, f"stakeholder row {index}"))
        ids.append(row.get("stakeholder_id", ""))
        if "everything" in row.get("decision_right", "").lower():
            errors.append(f"stakeholder row {index}: decision right is overbroad")
    if len(ids) != len(set(ids)):
        errors.append("stakeholder matrix: stakeholder_id values must be unique")
    kinds = " ".join(row.get("affected_or_accountable", "").lower() for row in rows)
    if "affected" not in kinds or "accountable" not in kinds:
        errors.append("stakeholder matrix: include both affected and accountable perspectives")
    return errors + unsafe_reference_errors(rows, "stakeholder matrix")


def validate_workflow(rows: list[dict[str, str]]) -> list[str]:
    required = ["stage_id", "actor", "trigger", "action", "handoff_to", "evidence_source", "delay_minutes", "failure_demand", "accessibility_barrier", "uncertainty"]
    errors: list[str] = []
    if len(rows) < 5:
        errors.append("workflow: at least five stages required")
    ids: list[str] = []
    for index, row in enumerate(rows, 1):
        errors.extend(require(row, required, f"workflow row {index}"))
        ids.append(row.get("stage_id", ""))
        try:
            if float(row.get("delay_minutes", "-1")) < 0:
                errors.append(f"workflow row {index}: delay_minutes must be zero or greater")
        except ValueError:
            errors.append(f"workflow row {index}: delay_minutes must be numeric")
    if len(ids) != len(set(ids)):
        errors.append("workflow: stage_id values must be unique")
    return errors


def validate_problem_frame(obj: dict[str, Any]) -> list[str]:
    fields = [
        "frame_id", "customer_request", "observed_symptoms", "user_needs", "root_problem_hypothesis",
        "assumptions", "constraints", "non_goals", "outcome_hypothesis", "affected_groups",
        "evidence_strength", "decision_owner", "review_trigger", "product_implications",
    ]
    errors = require(obj, fields, "problem frame")
    if obj.get("customer_request") == obj.get("root_problem_hypothesis"):
        errors.append("problem frame: request and root problem hypothesis must be distinguished")
    for field in ("observed_symptoms", "user_needs", "assumptions", "constraints", "non_goals", "affected_groups"):
        if isinstance(obj.get(field), list) and len(obj[field]) < 2:
            errors.append(f"problem frame: {field} requires at least two entries")
    return errors


def validate_accessibility(rows: list[dict[str, str]]) -> list[str]:
    required = ["need_id", "user_group", "barrier", "context", "evidence_source", "adjustment", "acceptance_implication", "owner", "status"]
    errors: list[str] = []
    if len(rows) < 3:
        errors.append("accessibility record: at least three distinct needs required")
    for index, row in enumerate(rows, 1):
        errors.extend(require(row, required, f"accessibility row {index}"))
        if row.get("evidence_source", "").strip().lower() in {"common sense", "assumed"}:
            errors.append(f"accessibility row {index}: evidence source must be explicit")
    return errors


def validate_ai_decision(obj: dict[str, Any]) -> list[str]:
    fields = [
        "decision_id", "proposed_use", "necessary_or_alternative", "affected_people", "intended_benefit",
        "risks", "data_boundary", "human_decision_authority", "contestability", "authorisation_owner",
        "suitability_decision", "evidence_mode", "limitations", "review_trigger",
    ]
    errors = require(obj, fields, "AI suitability decision")
    allowed = {"not_suitable", "explore_with_controls", "suitable_for_bounded_experiment", "unproved"}
    if obj.get("suitability_decision") not in allowed:
        errors.append("AI suitability decision: invalid suitability_decision")
    if obj.get("evidence_mode") not in ALLOWED_MODES:
        errors.append("AI suitability decision: invalid evidence_mode")
    if "ai" in str(obj.get("proposed_use", "")).lower() and not is_present(obj.get("human_decision_authority")):
        errors.append("AI suitability decision: human_decision_authority is required")
    return errors + unsafe_reference_errors(obj, "AI suitability decision")


def validate_requirements(rows: list[dict[str, str]]) -> list[str]:
    required = ["requirement_id", "source_need_id", "statement", "type", "priority", "acceptance_criterion", "verification_method", "decision_owner", "status", "assumption_or_constraint", "version"]
    vague = ("user-friendly", "fast", "easy", "robust", "seamless", "as appropriate", "etc.")
    errors: list[str] = []
    if len(rows) < 8:
        errors.append("requirements traceability: at least eight rows required")
    ids: list[str] = []
    for index, row in enumerate(rows, 1):
        errors.extend(require(row, required, f"requirement row {index}"))
        ids.append(row.get("requirement_id", ""))
        statement = row.get("statement", "").lower()
        for term in vague:
            if term in statement:
                errors.append(f"requirement row {index}: vague term '{term}'")
        if row.get("acceptance_criterion", "").strip() == row.get("statement", "").strip():
            errors.append(f"requirement row {index}: acceptance criterion must add observable proof")
    if len(ids) != len(set(ids)):
        errors.append("requirements traceability: requirement_id values must be unique")
    return errors


def validate_value(rows: list[dict[str, str]]) -> list[str]:
    required = ["measure_id", "outcome_link", "measure_type", "definition", "numerator", "denominator", "data_source", "baseline_value", "target_value", "owner", "cadence", "limitations"]
    allowed = {"baseline", "leading", "lagging", "guardrail", "cost"}
    errors: list[str] = []
    types: set[str] = set()
    for index, row in enumerate(rows, 1):
        errors.extend(require(row, required, f"value row {index}"))
        kind = row.get("measure_type", "").lower()
        types.add(kind)
        if kind not in allowed:
            errors.append(f"value row {index}: invalid measure_type")
        if row.get("denominator", "").lower() in {"all", "cases", "users"}:
            errors.append(f"value row {index}: denominator is not operationally defined")
    missing = allowed - types
    if missing:
        errors.append("value scorecard: missing measure types " + ", ".join(sorted(missing)))
    return errors


def validate_observations(rows: list[dict[str, str]]) -> list[str]:
    required = ["observation_id", "category", "observation", "evidence_link", "affected_users", "confidence", "counter_evidence", "generalisation_limit", "product_boundary", "owner", "next_validation", "status"]
    errors: list[str] = []
    if len(rows) < 4:
        errors.append("field observations: at least four rows required")
    for index, row in enumerate(rows, 1):
        errors.extend(require(row, required, f"observation row {index}"))
        if row.get("category") not in OBSERVATION_CATEGORIES:
            errors.append(f"observation row {index}: invalid category")
        if row.get("generalisation_limit", "").lower() in {"none", "universal"}:
            errors.append(f"observation row {index}: state a bounded generalisation limit")
    return errors


def validate_change_impact(rows: list[dict[str, str]]) -> list[str]:
    required = ["change_id", "affected_artefact", "affected_ids", "update_required", "rationale", "status"]
    errors: list[str] = []
    if rows and len(rows) < 4:
        errors.append("change impact: record at least four affected artefacts")
    for index, row in enumerate(rows, 1):
        errors.extend(require(row, required, f"change impact row {index}"))
        if row.get("update_required", "").lower() not in {"yes", "no"}:
            errors.append(f"change impact row {index}: update_required must be yes or no")
    return errors


def validate_manifest(obj: dict[str, Any]) -> list[str]:
    errors = require(obj, ["engagement_id", "manifest_version", "claims"], "evidence manifest")
    claims = obj.get("claims", [])
    if not isinstance(claims, list) or not claims:
        return errors + ["evidence manifest: at least one claim required"]
    for index, claim in enumerate(claims, 1):
        fields = ["claim_id", "statement", "execution_mode", "validation_method", "observer_or_verifier", "artefacts", "captured_at", "environment", "redaction", "limitations", "retention"]
        errors.extend(require(claim, fields, f"claim {index}"))
        if claim.get("execution_mode") not in ALLOWED_MODES:
            errors.append(f"claim {index}: invalid execution_mode")
        if claim.get("validation_method") not in ALLOWED_METHODS:
            errors.append(f"claim {index}: invalid validation_method")
    return errors


WORKSPACE_FILES = {
    "research-plan.json": validate_research_plan,
    "stakeholder-decision-matrix.csv": validate_stakeholders,
    "present-state-workflow.csv": validate_workflow,
    "problem-frame.json": validate_problem_frame,
    "accessibility-needs.csv": validate_accessibility,
    "ai-suitability-decision.json": validate_ai_decision,
    "requirements-traceability.csv": validate_requirements,
    "value-scorecard.csv": validate_value,
    "field-observations.csv": validate_observations,
    "evidence-manifest.json": validate_manifest,
}


def validate_workspace(workspace: Path) -> list[str]:
    errors: list[str] = []
    for filename, validator in WORKSPACE_FILES.items():
        path = workspace / filename
        if not path.exists():
            errors.append(f"workspace: missing {filename}")
            continue
        try:
            value = read_csv(path) if path.suffix == ".csv" else read_json(path)
            errors.extend(validator(value))
        except ValidationError as exc:
            errors.append(str(exc))
    change_path = workspace / "change-impact.csv"
    if change_path.exists():
        try:
            rows = read_csv(change_path)
            if any(is_present(v) for row in rows for v in row.values()):
                errors.extend(validate_change_impact(rows))
        except ValidationError as exc:
            errors.append(str(exc))
    return errors


def validate_scenario(obj: dict[str, Any]) -> list[str]:
    fields = ["scenario_id", "organisation", "fictional_domain", "customer_request", "stated_outcome", "known_facts", "visible_tensions", "authorised_scope", "excluded_scope", "data_status"]
    errors = require(obj, fields, "scenario")
    if not str(obj.get("fictional_domain", "")).endswith(".invalid"):
        errors.append("scenario: fictional_domain must end in .invalid")
    if obj.get("data_status") != "synthetic_only":
        errors.append("scenario: data_status must be synthetic_only")
    return errors + unsafe_reference_errors(obj, "scenario")


def baseline_errors(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    required = ["README.md", "pyproject.toml", "uv.lock", "scenario/meridian-public-services.json", "personas/index.json", "templates/research-plan.json", "tools/module1.py"]
    for item in required:
        if not (root / item).exists():
            errors.append(f"baseline: missing {item}")
    try:
        errors.extend(validate_scenario(read_json(root / "scenario" / "meridian-public-services.json")))
        index = read_json(root / "personas" / "index.json")
        entries = index.get("personas", [])
        if len(entries) != 7:
            errors.append("baseline: expected seven personas")
        ids = [entry.get("persona_id") for entry in entries]
        if len(ids) != len(set(ids)):
            errors.append("baseline: persona ids must be unique")
        for entry in entries:
            path = root / "personas" / str(entry.get("file"))
            if not path.exists():
                errors.append(f"baseline: missing persona file {path.name}")
            else:
                errors.extend(unsafe_reference_errors(read_json(path), f"persona {path.name}"))
    except ValidationError as exc:
        errors.append(str(exc))
    return errors


def resolve_inside(path: Path, parent: Path) -> Path:
    resolved = path.resolve()
    allowed = parent.resolve()
    if resolved == allowed or allowed not in resolved.parents:
        raise ValidationError(f"refusing path outside {allowed}: {resolved}")
    return resolved


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def command_baseline(_: argparse.Namespace) -> int:
    errors = baseline_errors()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Module 1 learner baseline is complete and synthetic-only.")
    return 0


def command_personas(_: argparse.Namespace) -> int:
    index = read_json(ROOT / "personas" / "index.json")
    for item in index["personas"]:
        print(f"{item['persona_id']} | {item['role']} | {item['name']}")
    return 0


def command_prepare(args: argparse.Namespace) -> int:
    workspace = resolve_inside(Path(args.workspace), ROOT / "work")
    if workspace.exists() and any(workspace.iterdir()):
        raise ValidationError(f"workspace is not empty: {workspace}")
    workspace.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "scenario" / "meridian-public-services.json", workspace / "scenario.json")
    shutil.copytree(ROOT / "personas", workspace / "personas")
    for path in (ROOT / "templates").iterdir():
        if path.is_file():
            shutil.copy2(path, workspace / path.name)
    print(workspace)
    return 0


def command_validate(args: argparse.Namespace) -> int:
    workspace = resolve_inside(Path(args.workspace), ROOT / "work")
    errors = validate_workspace(workspace)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Workspace validation passed. Human, specialist and assessor review remain required.")
    return 0


def command_trace(args: argparse.Namespace) -> int:
    workspace = resolve_inside(Path(args.workspace), ROOT / "work")
    rows = read_csv(workspace / "requirements-traceability.csv")
    by_need: dict[str, int] = {}
    for row in rows:
        by_need[row.get("source_need_id", "")] = by_need.get(row.get("source_need_id", ""), 0) + 1
    print(json.dumps({"requirements": len(rows), "requirements_by_source_need": by_need}, indent=2))
    return 0


def control_errors(control: dict[str, Any]) -> list[str]:
    fields = ["catalogue_version", "fault_id", "assessment_impact", "authorised_by", "issued_utc", "changed_constraint", "learner_visible_text"]
    errors = require(control, fields, "control")
    forbidden = sorted(set(control) & FORBIDDEN_CONTROL_KEYS)
    if forbidden:
        errors.append("control: forbidden keys " + ", ".join(forbidden))
    if is_present(control.get("fault_id")) and not FAULT_ID.match(str(control["fault_id"])):
        errors.append("control: invalid fault_id")
    if control.get("assessment_impact") not in {"A1", "A2", "A3", "A4"}:
        errors.append("control: assessment_impact must be A1, A2, A3 or A4")
    return errors + unsafe_reference_errors(control, "control")


def command_control(args: argparse.Namespace) -> int:
    workspace = resolve_inside(Path(args.workspace), ROOT / "work")
    control_path = Path(args.control).resolve()
    if ROOT.resolve() in control_path.parents:
        raise ValidationError("assessor control must be supplied from outside the learner repository")
    control = read_json(control_path)
    errors = control_errors(control)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    learner_view = {key: control[key] for key in ("catalogue_version", "fault_id", "assessment_impact", "issued_utc", "changed_constraint", "learner_visible_text")}
    write_path = workspace / "changed-constraint.json"
    write_path.write_text(json.dumps(learner_view, indent=2) + "\n", encoding="utf-8")
    print(write_path)
    return 0


def command_seal(args: argparse.Namespace) -> int:
    workspace = resolve_inside(Path(args.workspace), ROOT / "work")
    evidence = resolve_inside(Path(args.evidence), ROOT / "evidence")
    if evidence.exists():
        raise ValidationError(f"evidence path already exists: {evidence}")
    errors = validate_workspace(workspace)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    evidence.mkdir(parents=True)
    artefacts = []
    for path in sorted(workspace.rglob("*")):
        if not path.is_file() or "personas" in path.parts:
            continue
        relative = path.relative_to(workspace)
        destination = evidence / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        artefacts.append({"path": relative.as_posix(), "sha256": file_digest(destination)})
    seal = {
        "format": "FDE1-SHA256-1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_workspace": workspace.relative_to(ROOT).as_posix(),
        "artefacts": artefacts,
    }
    (evidence / "SHA256SUMS.json").write_text(json.dumps(seal, indent=2) + "\n", encoding="utf-8")
    print(evidence)
    return 0


def verify_evidence(evidence: Path) -> list[str]:
    errors: list[str] = []
    seal_path = evidence / "SHA256SUMS.json"
    seal = read_json(seal_path)
    for item in seal.get("artefacts", []):
        path = evidence / item["path"]
        if not path.exists():
            errors.append(f"missing artefact: {item['path']}")
        elif file_digest(path) != item["sha256"]:
            errors.append(f"digest mismatch: {item['path']}")
    return errors


def command_verify(args: argparse.Namespace) -> int:
    evidence = resolve_inside(Path(args.evidence), ROOT / "evidence")
    errors = verify_evidence(evidence)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Evidence seal verified.")
    return 0


def command_reset(args: argparse.Namespace) -> int:
    workspace = resolve_inside(Path(args.workspace), ROOT / "work")
    if workspace.exists():
        shutil.rmtree(workspace)
    print(f"reset {workspace}")
    return 0


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="FDE Module 1 synthetic discovery lab")
    sub = value.add_subparsers(dest="command", required=True)
    sub.add_parser("baseline").set_defaults(func=command_baseline)
    sub.add_parser("list-personas").set_defaults(func=command_personas)
    prepare = sub.add_parser("prepare"); prepare.add_argument("--workspace", required=True); prepare.set_defaults(func=command_prepare)
    validate = sub.add_parser("validate"); validate.add_argument("--workspace", required=True); validate.set_defaults(func=command_validate)
    trace = sub.add_parser("trace-report"); trace.add_argument("--workspace", required=True); trace.set_defaults(func=command_trace)
    control = sub.add_parser("apply-control"); control.add_argument("--workspace", required=True); control.add_argument("--control", required=True); control.set_defaults(func=command_control)
    seal = sub.add_parser("seal"); seal.add_argument("--workspace", required=True); seal.add_argument("--evidence", required=True); seal.set_defaults(func=command_seal)
    verify = sub.add_parser("verify"); verify.add_argument("--evidence", required=True); verify.set_defaults(func=command_verify)
    reset = sub.add_parser("reset"); reset.add_argument("--workspace", required=True); reset.set_defaults(func=command_reset)
    return value


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
        return int(args.func(args))
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
