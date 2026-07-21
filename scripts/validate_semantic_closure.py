#!/usr/bin/env python3
"""Mechanical semantic-closure validator. Never decides product quality."""
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

ALLOWED_INTERPRETATION_STATUS = {"ALIGNED", "TECHNICAL_DISCOVERY_REQUIRED", "MATERIAL_UNCERTAINTY", "CONTRACT_CONFLICT"}
ALLOWED_DEVIATION_CLASSES = {"AUTO_ACCEPTABLE_TECHNICAL_VARIATION", "BRAIN_REVIEW_REQUIRED", "USER_DECISION_REQUIRED"}
LEAN_REQUIRED_TRUE_FIELDS = (
    "low_risk", "known_paths", "technical_only_or_precisely_bounded",
    "no_product_meaning_change", "no_user_flow_change", "no_data_meaning_change",
    "no_shared_state_change", "exact_expected_result",
)
INTERPRETATION_LIST_FIELDS = (
    "user_flow_understood", "must_preserve", "intended_solution_surface",
    "excluded_changes", "golden_cases_understood",
)


def _s(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _sl(value: Any, empty: bool = False) -> bool:
    return isinstance(value, list) and (empty or bool(value)) and all(_s(x) for x in value)


def _add(out: List[str], ok: bool, msg: str) -> None:
    if not ok:
        out.append(msg)


def _load(path: str, out: List[str]) -> Dict[str, Any]:
    try:
        value = read_json(path, default={})
    except Exception as exc:
        out.append(f"{path}: cannot parse JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        out.append(f"{path}: root must be object")
        return {}
    return value


def interpretation_is_authentic_execution_return(value: Dict[str, Any]) -> bool:
    return (
        value.get("artifact_origin") == "CODEX_EXECUTION_RETURN"
        and value.get("not_codex_execution_evidence") is not True
        and value.get("brain_alignment_status") == "ALIGNED_CONFIRMED"
        and _s(value.get("brain_alignment_ref"))
    )


def embedded_interpretation_complete(contract: Dict[str, Any]) -> bool:
    value = contract.get("embedded_codex_interpretation")
    return (
        isinstance(value, dict)
        and value.get("artifact_type") == "CODEX_EXECUTION_INTERPRETATION"
        and value.get("artifact_origin") == "CONTRACT_EMBEDDED_LEAN"
        and value.get("task_id") == contract.get("task_id")
        and _s(value.get("task_id"))
        and _s(value.get("objective_understood"))
        and _s(value.get("user_visible_result"))
        and all(_sl(value.get(field)) for field in INTERPRETATION_LIST_FIELDS)
        and value.get("unresolved_items") == []
        and value.get("interpretation_status") == "ALIGNED"
        and value.get("deviation_route") in ALLOWED_DEVIATION_CLASSES
        and set(value.get("golden_cases_understood", [])) == set(contract.get("golden_case_refs", []))
    )


def lean_interpretation_allowed(contract: Dict[str, Any]) -> bool:
    e = contract.get("lean_eligibility")
    return (
        contract.get("lean_interpretation_embedded") is True
        and isinstance(e, dict)
        and all(e.get(k) is True for k in LEAN_REQUIRED_TRUE_FIELDS)
        and _s(e.get("basis"))
        and embedded_interpretation_complete(contract)
    )


def effective_interpretation(contract: Dict[str, Any], external: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    if lean_interpretation_allowed(contract):
        return contract["embedded_codex_interpretation"], "CONTRACT_EMBEDDED_LEAN"
    return external, "SEPARATE_CODEX_INTERPRETATION"


def execution_release_allowed(contract: Dict[str, Any], external: Dict[str, Any]) -> bool:
    if contract.get("lifecycle_mode") != "ACTIVE_TASK":
        return False
    if lean_interpretation_allowed(contract):
        return True
    return (
        external.get("interpretation_status") == "ALIGNED"
        and external.get("unresolved_items") == []
        and interpretation_is_authentic_execution_return(external)
    )


def validate_product_meaning(v: Dict[str, Any], out: List[str]) -> None:
    _add(out, v.get("artifact_type") == "PRODUCT_MEANING_CLOSURE", "meaning artifact_type mismatch")
    for k in ("artifact_version", "task_id", "original_user_problem", "problem", "desired_result"):
        _add(out, _s(v.get(k)), f"meaning.{k} must be non-empty")
    for k in ("user_flow", "business_rules", "must_have", "must_not_have", "non_goals", "important_tradeoffs", "acceptance_examples", "failure_examples"):
        _add(out, _sl(v.get(k)), f"meaning.{k} must be non-empty string list")
    _add(out, _sl(v.get("remaining_unknowns"), True), "meaning.remaining_unknowns must be list")
    _add(out, v.get("material_ambiguity_status") in {"NO_MATERIAL_AMBIGUITY", "MATERIAL_AMBIGUITY_REMAINS"}, "invalid material ambiguity status")
    if v.get("material_ambiguity_status") == "NO_MATERIAL_AMBIGUITY":
        _add(out, v.get("remaining_unknowns") == [], "no-material-ambiguity cannot retain unknowns")
    w = v.get("product_walkthrough")
    _add(out, isinstance(w, dict), "product_walkthrough must be object")
    if isinstance(w, dict):
        for k in ("entry", "success_result", "failure_result"):
            _add(out, _s(w.get(k)), f"walkthrough.{k} must be non-empty")
        for k in ("user_action_sequence", "system_response_sequence", "preserved_behavior", "explicitly_absent_behavior"):
            _add(out, _sl(w.get(k)), f"walkthrough.{k} must be list")
    c = v.get("user_confirmation")
    _add(out, isinstance(c, dict), "user_confirmation must be object")
    if isinstance(c, dict):
        _add(out, c.get("status") in {"DRAFT", "CONFIRMED"}, "invalid user_confirmation.status")
        if c.get("status") == "CONFIRMED":
            _add(out, _s(c.get("reference")), "confirmed meaning needs reference")


def validate_contract(v: Dict[str, Any], out: List[str]) -> None:
    _add(out, v.get("artifact_type") == "DUAL_LAYER_TRANSLATION_CONTRACT", "contract artifact_type mismatch")
    for k in ("artifact_version", "task_id", "deterministic_intent", "product_meaning_ref"):
        _add(out, _s(v.get(k)), f"contract.{k} must be non-empty")
    _add(out, v.get("lifecycle_mode") in {"ACTIVE_TASK", "REFERENCE_CANDIDATE"}, "invalid lifecycle_mode")
    for section, fields in {
        "human_semantic_layer": ("objective", "expected_user_result", "user_flow", "business_rules", "accepted_tradeoffs", "non_goals", "correct_examples", "incorrect_examples"),
        "mechanical_execution_layer": ("must_preserve", "allowed_solution_surfaces", "forbidden_consequences", "required_outcomes", "allowed_technical_freedom", "stop_conditions", "evidence_requirements"),
    }.items():
        obj = v.get(section)
        _add(out, isinstance(obj, dict), f"{section} must be object")
        if isinstance(obj, dict):
            for k in fields:
                _add(out, _s(obj.get(k)) if k in {"objective", "expected_user_result"} else _sl(obj.get(k)), f"{section}.{k} invalid")
    _add(out, _sl(v.get("golden_case_refs")), "golden_case_refs invalid")
    _add(out, v.get("meaning_delta_ref") == DELTA_PATH, "meaning_delta_ref mismatch")
    _add(out, v.get("user_acceptance_plan_ref") == ACCEPTANCE_PATH, "acceptance ref mismatch")
    _add(out, v.get("deviation_default") in ALLOWED_DEVIATION_CLASSES, "invalid deviation_default")
    _add(out, isinstance(v.get("lean_interpretation_embedded"), bool), "lean flag must be bool")
    e = v.get("lean_eligibility")
    _add(out, isinstance(e, dict), "lean_eligibility must be object")
    if isinstance(e, dict):
        for k in LEAN_REQUIRED_TRUE_FIELDS:
            _add(out, isinstance(e.get(k), bool), f"lean_eligibility.{k} must be bool")
        _add(out, _s(e.get("basis")), "lean basis missing")
    if v.get("lean_interpretation_embedded") is True:
        _add(out, lean_interpretation_allowed(v), "embedded LEAN is incomplete")


def _validate_task_artifact(v: Dict[str, Any], out: List[str], typ: str, task_id: str, name: str) -> None:
    _add(out, v.get("artifact_type") == typ, f"{name} artifact_type mismatch")
    _add(out, v.get("task_id") == task_id and _s(task_id), f"{name} task_id mismatch")


def validate_all(include_review: bool = True) -> Tuple[bool, List[str]]:
    out: List[str] = []
    meaning = _load(MEANING_PATH, out)
    contract = _load(CONTRACT_PATH, out)
    delta = _load(DELTA_PATH, out)
    golden = _load(GOLDEN_PATH, out)
    acceptance = _load(ACCEPTANCE_PATH, out)
    external = _load(INTERPRETATION_PATH, out)
    validate_product_meaning(meaning, out)
    validate_contract(contract, out)
    task_id = str(contract.get("task_id") or "")
    _add(out, meaning.get("task_id") == task_id and bool(task_id), "semantic task_id mismatch")
    _validate_task_artifact(delta, out, "MEANING_DELTA", task_id, "delta")
    _add(out, _s(delta.get("parent_meaning_ref")) and _s(delta.get("parent_package_sha256")), "delta parent identity missing")
    for k in ("added", "removed", "changed"):
        _add(out, isinstance(delta.get(k), (dict, list)), f"delta.{k} invalid")
    _add(out, _sl(delta.get("unchanged")), "delta.unchanged invalid")
    _add(out, _sl(delta.get("unresolved"), True), "delta.unresolved invalid")
    _validate_task_artifact(golden, out, "GOLDEN_CASE_SET", task_id, "golden")
    cases = golden.get("cases") if isinstance(golden.get("cases"), list) else []
    ids: List[str] = []
    _add(out, bool(cases), "golden cases missing")
    for i, case in enumerate(cases):
        _add(out, isinstance(case, dict), f"case[{i}] must be object")
        if not isinstance(case, dict):
            continue
        cid = case.get("case_id")
        _add(out, _s(cid), f"case[{i}].case_id missing")
        if _s(cid): ids.append(cid)
        for k in ("original_problem_ref", "action", "expected_user_visible_result", "expected_state_change", "preserved_state", "forbidden_result", "machine_check_mapping", "human_acceptance_mapping"):
            _add(out, case.get(k) not in (None, "", [], {}), f"case[{i}].{k} missing")
        _add(out, isinstance(case.get("initial_state"), dict) and bool(case.get("initial_state")), f"case[{i}].initial_state invalid")
    _add(out, len(ids) == len(set(ids)), "duplicate Golden Case IDs")
    _validate_task_artifact(acceptance, out, "USER_ACCEPTANCE_PLAN", task_id, "acceptance")
    steps = acceptance.get("steps") if isinstance(acceptance.get("steps"), list) else []
    _add(out, bool(steps), "acceptance steps missing")
    seen: List[str] = []
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            out.append(f"acceptance[{i}] must be object"); continue
        aid = step.get("acceptance_id")
        _add(out, _s(aid), f"acceptance[{i}].id missing")
        if _s(aid): seen.append(aid)
        for k in ("step", "expected", "validates", "failure_meaning"):
            _add(out, _s(step.get(k)), f"acceptance[{i}].{k} missing")
        refs = step.get("golden_case_refs", [])
        _add(out, _sl(refs, True) and not (set(refs) - set(ids)), f"acceptance[{i}] refs invalid")
    _add(out, len(seen) == len(set(seen)), "duplicate acceptance IDs")
    effective, _ = effective_interpretation(contract, external)
    _validate_task_artifact(effective, out, "CODEX_EXECUTION_INTERPRETATION", task_id, "interpretation")
    for k in ("objective_understood", "user_visible_result"):
        _add(out, _s(effective.get(k)), f"interpretation.{k} missing")
    for k in INTERPRETATION_LIST_FIELDS:
        _add(out, _sl(effective.get(k)), f"interpretation.{k} invalid")
    _add(out, _sl(effective.get("unresolved_items"), True), "interpretation unresolved invalid")
    _add(out, effective.get("interpretation_status") in ALLOWED_INTERPRETATION_STATUS, "invalid interpretation status")
    _add(out, effective.get("deviation_route") in ALLOWED_DEVIATION_CLASSES, "invalid deviation route")
    if effective.get("not_codex_execution_evidence") is True:
        _add(out, effective.get("artifact_origin") == "PROTOCOL_REPAIR_REFERENCE_FIXTURE", "fixture origin mismatch")
    _add(out, set(contract.get("golden_case_refs", [])) == set(ids), "contract Golden Case refs mismatch")
    _add(out, contract.get("product_meaning_ref") == MEANING_PATH, "product meaning ref mismatch")
    c = meaning.get("user_confirmation", {})
    _add(out, isinstance(c, dict) and c.get("status") == "CONFIRMED", "meaning not confirmed")
    _add(out, meaning.get("material_ambiguity_status") == "NO_MATERIAL_AMBIGUITY", "material ambiguity remains")
    if contract.get("lifecycle_mode") == "ACTIVE_TASK":
        _add(out, execution_release_allowed(contract, external), "active task lacks authentic aligned interpretation")
    if include_review:
        review = _load(BRAIN_REVIEW_PATH, out)
        _validate_task_artifact(review, out, "BRAIN_SEMANTIC_REVIEW", task_id, "brain review")
        for k in ("original_user_problem_ref", "confirmed_product_meaning_ref", "released_contract_ref", "codex_interpretation_ref", "actual_diff_and_evidence_ref", "test_results_ref", "golden_case_results_ref", "user_acceptance_plan_ref"):
            _add(out, _s(review.get(k)), f"brain review.{k} missing")
        for k in ("semantic_drift_status", "scope_drift_status", "overdesign_status"):
            _add(out, review.get(k) in {"PASS", "BLOCK", "NEEDS_USER_DECISION"}, f"brain review.{k} invalid")
        _add(out, isinstance(review.get("original_problem_actually_solved"), bool), "brain review original problem result invalid")
        _add(out, review.get("technically_correct_but_practically_wrong_risk") in {"NONE_FOUND", "PRESENT", "UNKNOWN"}, "brain review risk invalid")
        _add(out, review.get("review_verdict") in {"PASS", "BLOCK", "NEEDS_USER_DECISION"}, "brain review verdict invalid")
    return not out, out


def main() -> int:
    ok, findings = validate_all(True)
    print("JOYFLOW_SEMANTIC_CLOSURE_PASS" if ok else "JOYFLOW_SEMANTIC_CLOSURE_BLOCK")
    for item in findings:
        print("- " + item)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
