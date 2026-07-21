#!/usr/bin/env python3
"""Validate Joyflow semantic-closure artifacts without making semantic decisions.

The validator checks shape, cross-artifact references, declared lifecycle states,
and mechanically provable LEAN eligibility. Brain and the human still own
semantic correctness and product acceptance.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

from joyflow_common import read_json

MEANING_PATH = "runtime/product_meaning_closure.json"
CONTRACT_PATH = "runtime/translation_contract.json"
DELTA_PATH = "runtime/meaning_delta.json"
GOLDEN_PATH = "runtime/golden_cases.json"
ACCEPTANCE_PATH = "runtime/user_acceptance_plan.json"
INTERPRETATION_PATH = "runtime/codex_execution_interpretation.json"
BRAIN_REVIEW_PATH = "observer/brain_semantic_review.json"
ACCEPTANCE_RECEIPT_PATH = "observer/acceptance_receipt.json"

ALLOWED_INTERPRETATION_STATUS = {
    "ALIGNED",
    "TECHNICAL_DISCOVERY_REQUIRED",
    "MATERIAL_UNCERTAINTY",
    "CONTRACT_CONFLICT",
}
ALLOWED_DEVIATION_CLASSES = {
    "AUTO_ACCEPTABLE_TECHNICAL_VARIATION",
    "BRAIN_REVIEW_REQUIRED",
    "USER_DECISION_REQUIRED",
}
LEAN_REQUIRED_TRUE_FIELDS = (
    "low_risk",
    "known_paths",
    "technical_only_or_precisely_bounded",
    "no_product_meaning_change",
    "no_user_flow_change",
    "no_data_meaning_change",
    "no_shared_state_change",
    "exact_expected_result",
)
INTERPRETATION_LIST_FIELDS = (
    "user_flow_understood",
    "must_preserve",
    "intended_solution_surface",
    "excluded_changes",
    "golden_cases_understood",
)


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any, allow_empty: bool = False) -> bool:
    return isinstance(value, list) and (allow_empty or bool(value)) and all(
        _nonempty_string(item) for item in value
    )


def _add(findings: List[str], condition: bool, message: str) -> None:
    if not condition:
        findings.append(message)


def _load(path: str, findings: List[str]) -> Dict[str, Any]:
    try:
        value = read_json(path, default={})
    except Exception as exc:
        findings.append(f"{path}: cannot parse JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        findings.append(f"{path}: root must be an object")
        return {}
    return value


def embedded_interpretation_complete(contract: Dict[str, Any]) -> bool:
    value = contract.get("embedded_codex_interpretation")
    if not isinstance(value, dict):
        return False
    if value.get("artifact_type") != "CODEX_EXECUTION_INTERPRETATION":
        return False
    if value.get("task_id") != contract.get("task_id") or not _nonempty_string(value.get("task_id")):
        return False
    if not _nonempty_string(value.get("objective_understood")):
        return False
    if not _nonempty_string(value.get("user_visible_result")):
        return False
    if not all(_string_list(value.get(field)) for field in INTERPRETATION_LIST_FIELDS):
        return False
    if value.get("unresolved_items") != []:
        return False
    if value.get("interpretation_status") != "ALIGNED":
        return False
    if value.get("deviation_route") not in ALLOWED_DEVIATION_CLASSES:
        return False
    expected_cases = contract.get("golden_case_refs")
    return isinstance(expected_cases, list) and set(value.get("golden_cases_understood", [])) == set(expected_cases)


def lean_interpretation_allowed(contract: Dict[str, Any]) -> bool:
    """Return true only for an embedded, fully proven, self-contained LEAN task."""
    if contract.get("lean_interpretation_embedded") is not True:
        return False
    eligibility = contract.get("lean_eligibility")
    if not isinstance(eligibility, dict):
        return False
    if not all(eligibility.get(field) is True for field in LEAN_REQUIRED_TRUE_FIELDS):
        return False
    if not _nonempty_string(eligibility.get("basis")):
        return False
    return embedded_interpretation_complete(contract)


def effective_interpretation(contract: Dict[str, Any], external: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    if lean_interpretation_allowed(contract):
        embedded = contract.get("embedded_codex_interpretation")
        return embedded if isinstance(embedded, dict) else {}, "CONTRACT_EMBEDDED_LEAN"
    return external, "SEPARATE_CODEX_INTERPRETATION"


def validate_product_meaning(value: Dict[str, Any], findings: List[str]) -> None:
    _add(findings, value.get("artifact_type") == "PRODUCT_MEANING_CLOSURE", f"{MEANING_PATH}: artifact_type mismatch")
    for field in ["artifact_version", "task_id", "original_user_problem", "problem", "desired_result"]:
        _add(findings, _nonempty_string(value.get(field)), f"{MEANING_PATH}: {field} must be non-empty")
    for field in [
        "user_flow",
        "business_rules",
        "must_have",
        "must_not_have",
        "non_goals",
        "important_tradeoffs",
        "acceptance_examples",
        "failure_examples",
    ]:
        _add(findings, _string_list(value.get(field)), f"{MEANING_PATH}: {field} must be a non-empty string list")
    _add(findings, _string_list(value.get("remaining_unknowns"), allow_empty=True), f"{MEANING_PATH}: remaining_unknowns must be a string list")
    _add(
        findings,
        value.get("material_ambiguity_status") in {"NO_MATERIAL_AMBIGUITY", "MATERIAL_AMBIGUITY_REMAINS"},
        f"{MEANING_PATH}: invalid material_ambiguity_status",
    )
    if value.get("material_ambiguity_status") == "NO_MATERIAL_AMBIGUITY":
        _add(findings, value.get("remaining_unknowns") == [], f"{MEANING_PATH}: confirmed no-material-ambiguity cannot retain unknowns")

    walkthrough = value.get("product_walkthrough")
    _add(findings, isinstance(walkthrough, dict), f"{MEANING_PATH}: product_walkthrough must be an object")
    if isinstance(walkthrough, dict):
        for field in ["entry", "success_result", "failure_result"]:
            _add(findings, _nonempty_string(walkthrough.get(field)), f"{MEANING_PATH}: product_walkthrough.{field} must be non-empty")
        for field in ["user_action_sequence", "system_response_sequence", "preserved_behavior", "explicitly_absent_behavior"]:
            _add(findings, _string_list(walkthrough.get(field)), f"{MEANING_PATH}: product_walkthrough.{field} must be a non-empty string list")

    confirmation = value.get("user_confirmation")
    _add(findings, isinstance(confirmation, dict), f"{MEANING_PATH}: user_confirmation must be an object")
    if isinstance(confirmation, dict):
        _add(findings, confirmation.get("status") in {"DRAFT", "CONFIRMED"}, f"{MEANING_PATH}: invalid user_confirmation.status")
        if confirmation.get("status") == "CONFIRMED":
            _add(findings, _nonempty_string(confirmation.get("reference")), f"{MEANING_PATH}: confirmed meaning requires a reference")


def validate_contract(value: Dict[str, Any], findings: List[str]) -> None:
    for field in ["task_id", "deterministic_intent", "product_meaning_ref"]:
        _add(findings, _nonempty_string(value.get(field)), f"{CONTRACT_PATH}: {field} must be non-empty")

    semantic = value.get("human_semantic_layer")
    _add(findings, isinstance(semantic, dict), f"{CONTRACT_PATH}: human_semantic_layer must be an object")
    if isinstance(semantic, dict):
        for field in ["objective", "expected_user_result"]:
            _add(findings, _nonempty_string(semantic.get(field)), f"{CONTRACT_PATH}: human_semantic_layer.{field} must be non-empty")
        for field in ["user_flow", "business_rules", "accepted_tradeoffs", "non_goals", "correct_examples", "incorrect_examples"]:
            _add(findings, _string_list(semantic.get(field)), f"{CONTRACT_PATH}: human_semantic_layer.{field} must be a non-empty string list")

    mechanical = value.get("mechanical_execution_layer")
    _add(findings, isinstance(mechanical, dict), f"{CONTRACT_PATH}: mechanical_execution_layer must be an object")
    if isinstance(mechanical, dict):
        for field in [
            "must_preserve",
            "allowed_solution_surfaces",
            "forbidden_consequences",
            "required_outcomes",
            "allowed_technical_freedom",
            "stop_conditions",
            "evidence_requirements",
        ]:
            _add(findings, _string_list(mechanical.get(field)), f"{CONTRACT_PATH}: mechanical_execution_layer.{field} must be a non-empty string list")

    _add(findings, _string_list(value.get("golden_case_refs")), f"{CONTRACT_PATH}: golden_case_refs must be a non-empty string list")
    _add(findings, _nonempty_string(value.get("meaning_delta_ref")), f"{CONTRACT_PATH}: meaning_delta_ref must be non-empty")
    _add(findings, _nonempty_string(value.get("user_acceptance_plan_ref")), f"{CONTRACT_PATH}: user_acceptance_plan_ref must be non-empty")
    _add(findings, value.get("deviation_default") in ALLOWED_DEVIATION_CLASSES, f"{CONTRACT_PATH}: invalid deviation_default")

    embedded = value.get("lean_interpretation_embedded")
    _add(findings, isinstance(embedded, bool), f"{CONTRACT_PATH}: lean_interpretation_embedded must be boolean")
    eligibility = value.get("lean_eligibility")
    _add(findings, isinstance(eligibility, dict), f"{CONTRACT_PATH}: lean_eligibility must be an object")
    if isinstance(eligibility, dict):
        for field in LEAN_REQUIRED_TRUE_FIELDS:
            _add(findings, isinstance(eligibility.get(field), bool), f"{CONTRACT_PATH}: lean_eligibility.{field} must be boolean")
        _add(findings, _nonempty_string(eligibility.get("basis")), f"{CONTRACT_PATH}: lean_eligibility.basis must be non-empty")
    if embedded is True:
        _add(
            findings,
            lean_interpretation_allowed(value),
            f"{CONTRACT_PATH}: embedded LEAN requires all eligibility facts and a complete ALIGNED embedded_codex_interpretation matching task and Golden Cases",
        )


def validate_delta(value: Dict[str, Any], findings: List[str]) -> None:
    _add(findings, value.get("artifact_type") == "MEANING_DELTA", f"{DELTA_PATH}: artifact_type mismatch")
    _add(findings, _nonempty_string(value.get("parent_meaning_ref")), f"{DELTA_PATH}: parent_meaning_ref must be non-empty")
    for field in ["added", "removed", "changed"]:
        _add(findings, isinstance(value.get(field), (dict, list)), f"{DELTA_PATH}: {field} must be an object or list")
    _add(findings, _string_list(value.get("unchanged")), f"{DELTA_PATH}: unchanged must be a non-empty string list")
    _add(findings, _string_list(value.get("unresolved"), allow_empty=True), f"{DELTA_PATH}: unresolved must be a string list")
    _add(findings, isinstance(value.get("user_confirmation_required"), bool), f"{DELTA_PATH}: user_confirmation_required must be boolean")


def validate_golden(value: Dict[str, Any], findings: List[str]) -> List[str]:
    _add(findings, value.get("artifact_type") == "GOLDEN_CASE_SET", f"{GOLDEN_PATH}: artifact_type mismatch")
    cases = value.get("cases")
    _add(findings, isinstance(cases, list) and bool(cases), f"{GOLDEN_PATH}: cases must be a non-empty list")
    ids: List[str] = []
    if not isinstance(cases, list):
        return ids
    for index, case in enumerate(cases):
        prefix = f"{GOLDEN_PATH}: cases[{index}]"
        _add(findings, isinstance(case, dict), f"{prefix} must be an object")
        if not isinstance(case, dict):
            continue
        case_id = case.get("case_id")
        _add(findings, _nonempty_string(case_id), f"{prefix}.case_id must be non-empty")
        if _nonempty_string(case_id):
            ids.append(case_id)
        for field in [
            "original_problem_ref",
            "action",
            "expected_user_visible_result",
            "expected_state_change",
            "preserved_state",
            "forbidden_result",
            "machine_check_mapping",
            "human_acceptance_mapping",
        ]:
            _add(findings, field in case and case.get(field) not in (None, "", [], {}), f"{prefix}.{field} must be populated")
        _add(findings, isinstance(case.get("initial_state"), dict) and bool(case.get("initial_state")), f"{prefix}.initial_state must be a non-empty object")
    _add(findings, len(ids) == len(set(ids)), f"{GOLDEN_PATH}: case_id values must be unique")
    return ids


def validate_acceptance(value: Dict[str, Any], findings: List[str], golden_ids: Sequence[str]) -> List[str]:
    _add(findings, value.get("artifact_type") == "USER_ACCEPTANCE_PLAN", f"{ACCEPTANCE_PATH}: artifact_type mismatch")
    steps = value.get("steps")
    _add(findings, isinstance(steps, list) and bool(steps), f"{ACCEPTANCE_PATH}: steps must be a non-empty list")
    ids: List[str] = []
    if not isinstance(steps, list):
        return ids
    for index, step in enumerate(steps):
        prefix = f"{ACCEPTANCE_PATH}: steps[{index}]"
        _add(findings, isinstance(step, dict), f"{prefix} must be an object")
        if not isinstance(step, dict):
            continue
        acceptance_id = step.get("acceptance_id")
        _add(findings, _nonempty_string(acceptance_id), f"{prefix}.acceptance_id must be non-empty")
        if _nonempty_string(acceptance_id):
            ids.append(acceptance_id)
        for field in ["step", "expected", "validates", "failure_meaning"]:
            _add(findings, _nonempty_string(step.get(field)), f"{prefix}.{field} must be non-empty")
        refs = step.get("golden_case_refs", [])
        _add(findings, _string_list(refs, allow_empty=True), f"{prefix}.golden_case_refs must be a string list")
        if isinstance(refs, list):
            missing = sorted(set(refs) - set(golden_ids))
            _add(findings, not missing, f"{prefix}.golden_case_refs contain unknown ids: {missing}")
    _add(findings, len(ids) == len(set(ids)), f"{ACCEPTANCE_PATH}: acceptance_id values must be unique")
    return ids


def validate_interpretation(value: Dict[str, Any], findings: List[str], golden_ids: Sequence[str]) -> None:
    _add(findings, value.get("artifact_type") == "CODEX_EXECUTION_INTERPRETATION", f"{INTERPRETATION_PATH}: artifact_type mismatch")
    for field in ["task_id", "objective_understood", "user_visible_result"]:
        _add(findings, _nonempty_string(value.get(field)), f"{INTERPRETATION_PATH}: {field} must be non-empty")
    for field in INTERPRETATION_LIST_FIELDS:
        _add(findings, _string_list(value.get(field)), f"{INTERPRETATION_PATH}: {field} must be a non-empty string list")
    refs = value.get("golden_cases_understood")
    if isinstance(refs, list):
        missing = sorted(set(refs) - set(golden_ids))
        _add(findings, not missing, f"{INTERPRETATION_PATH}: unknown Golden Case ids: {missing}")
    _add(findings, _string_list(value.get("unresolved_items"), allow_empty=True), f"{INTERPRETATION_PATH}: unresolved_items must be a string list")
    status = value.get("interpretation_status")
    _add(findings, status in ALLOWED_INTERPRETATION_STATUS, f"{INTERPRETATION_PATH}: invalid interpretation_status")
    if status == "ALIGNED":
        _add(findings, value.get("unresolved_items") == [], f"{INTERPRETATION_PATH}: ALIGNED cannot retain unresolved items")
    _add(findings, value.get("deviation_route") in ALLOWED_DEVIATION_CLASSES, f"{INTERPRETATION_PATH}: invalid deviation_route")


def validate_brain_review(value: Dict[str, Any], findings: List[str]) -> None:
    _add(findings, value.get("artifact_type") == "BRAIN_SEMANTIC_REVIEW", f"{BRAIN_REVIEW_PATH}: artifact_type mismatch")
    for field in [
        "original_user_problem_ref",
        "confirmed_product_meaning_ref",
        "released_contract_ref",
        "codex_interpretation_ref",
        "actual_diff_and_evidence_ref",
        "test_results_ref",
        "golden_case_results_ref",
        "user_acceptance_plan_ref",
    ]:
        _add(findings, _nonempty_string(value.get(field)), f"{BRAIN_REVIEW_PATH}: {field} must be non-empty")
    for field in ["semantic_drift_status", "scope_drift_status", "overdesign_status"]:
        _add(findings, value.get(field) in {"PASS", "BLOCK", "NEEDS_USER_DECISION"}, f"{BRAIN_REVIEW_PATH}: invalid {field}")
    _add(findings, isinstance(value.get("original_problem_actually_solved"), bool), f"{BRAIN_REVIEW_PATH}: original_problem_actually_solved must be boolean")
    _add(findings, value.get("technically_correct_but_practically_wrong_risk") in {"NONE_FOUND", "PRESENT", "UNKNOWN"}, f"{BRAIN_REVIEW_PATH}: invalid technically_correct_but_practically_wrong_risk")
    _add(findings, value.get("review_verdict") in {"PASS", "BLOCK", "NEEDS_USER_DECISION"}, f"{BRAIN_REVIEW_PATH}: invalid review_verdict")


def validate_cross_refs(
    meaning: Dict[str, Any],
    contract: Dict[str, Any],
    interpretation: Dict[str, Any],
    findings: List[str],
    golden_ids: Sequence[str],
) -> None:
    task_ids = [meaning.get("task_id"), contract.get("task_id"), interpretation.get("task_id")]
    _add(findings, all(_nonempty_string(item) for item in task_ids) and len(set(task_ids)) == 1, "semantic closure task_id values must match")
    refs = contract.get("golden_case_refs", [])
    if isinstance(refs, list):
        missing = sorted(set(refs) - set(golden_ids))
        _add(findings, not missing, f"{CONTRACT_PATH}: unknown golden_case_refs: {missing}")
    _add(findings, contract.get("product_meaning_ref") == MEANING_PATH, f"{CONTRACT_PATH}: product_meaning_ref must be {MEANING_PATH}")
    _add(findings, contract.get("meaning_delta_ref") == DELTA_PATH, f"{CONTRACT_PATH}: meaning_delta_ref must be {DELTA_PATH}")
    _add(findings, contract.get("user_acceptance_plan_ref") == ACCEPTANCE_PATH, f"{CONTRACT_PATH}: user_acceptance_plan_ref must be {ACCEPTANCE_PATH}")


def validate_execution_gate(
    meaning: Dict[str, Any],
    contract: Dict[str, Any],
    interpretation: Dict[str, Any],
    findings: List[str],
) -> None:
    confirmation = meaning.get("user_confirmation")
    confirmed = isinstance(confirmation, dict) and confirmation.get("status") == "CONFIRMED"
    no_ambiguity = meaning.get("material_ambiguity_status") == "NO_MATERIAL_AMBIGUITY"
    aligned = interpretation.get("interpretation_status") == "ALIGNED"
    lean_allowed = lean_interpretation_allowed(contract)
    _add(findings, confirmed, "execution gate: product meaning is not user-confirmed")
    _add(findings, no_ambiguity, "execution gate: material ambiguity remains")
    _add(findings, aligned or lean_allowed, "execution gate: Codex interpretation is not aligned and mechanically valid self-contained LEAN embedding does not apply")


def validate_all(include_review: bool = True) -> Tuple[bool, List[str]]:
    findings: List[str] = []
    meaning = _load(MEANING_PATH, findings)
    contract = _load(CONTRACT_PATH, findings)
    delta = _load(DELTA_PATH, findings)
    golden = _load(GOLDEN_PATH, findings)
    acceptance = _load(ACCEPTANCE_PATH, findings)
    external_interpretation = _load(INTERPRETATION_PATH, findings)

    validate_product_meaning(meaning, findings)
    validate_contract(contract, findings)
    validate_delta(delta, findings)
    golden_ids = validate_golden(golden, findings)
    validate_acceptance(acceptance, findings, golden_ids)
    interpretation, _ = effective_interpretation(contract, external_interpretation)
    validate_interpretation(interpretation, findings, golden_ids)
    validate_cross_refs(meaning, contract, interpretation, findings, golden_ids)
    validate_execution_gate(meaning, contract, external_interpretation, findings)

    if include_review:
        brain_review = _load(BRAIN_REVIEW_PATH, findings)
        validate_brain_review(brain_review, findings)

    return not findings, findings


def main() -> int:
    passed, findings = validate_all(include_review=True)
    print("JOYFLOW_SEMANTIC_CLOSURE_PASS" if passed else "JOYFLOW_SEMANTIC_CLOSURE_BLOCK")
    for finding in findings:
        print("- " + finding)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
