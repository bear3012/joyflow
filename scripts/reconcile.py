#!/usr/bin/env python3
"""Compute closure readiness from bound machine, Brain and human evidence."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from joyflow_common import (
    canonical_json_hash,
    changed_files,
    current_head,
    evidence_suffix_status,
    is_within_allowed,
    read_json,
    source_bundle_hash,
    write_json,
)
from validate_semantic_closure import validate_all as validate_semantic_closure


def add(blocking: List[str], condition: bool, reason: str) -> None:
    if condition:
        blocking.append(reason)


def execution_state_blockers(contract: Dict[str, Any], bridge: Dict[str, Any], packet_text: str) -> List[str]:
    blockers: List[str] = []
    if contract.get("lifecycle_mode") != "ACTIVE_TASK":
        blockers.append("reference candidate or invalid lifecycle mode cannot close")
    if bridge.get("target_lane") == "HARD_STOP_LANE":
        blockers.append("HARD_STOP task cannot close")
    if bridge.get("execution_allowed") is not True:
        blockers.append("execution was not released")
    if "\nHALT\n" in packet_text:
        blockers.append("execution packet is HALT")
    return blockers


def main() -> int:
    blocking: List[str] = []
    warnings: List[str] = []

    raw: Dict[str, Any] = read_json("observer/raw_check_results.json", default={})
    bridge: Dict[str, Any] = read_json("runtime/execution_bridge_package.json", default={})
    manifest: Dict[str, Any] = read_json("runtime/codex_launch_manifest.json", default={})
    contract: Dict[str, Any] = read_json("runtime/translation_contract.json", default={})
    red_team: Dict[str, Any] = read_json("observer/contract_red_team_receipt.json", default={})
    brain_review: Dict[str, Any] = read_json("observer/brain_semantic_review.json", default={})
    pr: Dict[str, Any] = read_json("observer/pr_receipt.json", default={})
    acceptance: Dict[str, Any] = read_json("observer/acceptance_receipt.json", default={})
    acceptance_plan: Dict[str, Any] = read_json("runtime/user_acceptance_plan.json", default={})
    pending: Dict[str, Any] = read_json("shadow/pending_formal_truth.json", default={})

    task_id = contract.get("task_id")
    semantic_ok, semantic_findings = validate_semantic_closure(include_review=True)
    add(blocking, not semantic_ok, "semantic closure validation failed: " + "; ".join(semantic_findings))

    packet_path = Path(__file__).resolve().parents[1] / "runtime/codex_task_packet.md"
    packet_text = packet_path.read_text(encoding="utf-8") if packet_path.exists() else ""

    blocking.extend(execution_state_blockers(contract, bridge, packet_text))
    add(blocking, red_team.get("verdict") == "BLOCK" or bool(red_team.get("execution_blocked")), "contract red-team blocks execution")

    bridge_hash = canonical_json_hash(bridge)
    input_bundle_hash = manifest.get("input_bundle_hash")
    source_bundle, _ = source_bundle_hash()
    head_ok, head_sha = current_head()

    add(blocking, raw.get("exit_code") != 0, "checks did not pass")
    add(blocking, raw.get("task_id") != task_id, "raw checks task_id mismatch")
    add(blocking, raw.get("bridge_hash") != bridge_hash, "raw checks are not bound to current bridge")
    add(blocking, raw.get("input_bundle_hash") != input_bundle_hash, "raw checks are not bound to current input bundle")
    add(blocking, raw.get("source_bundle_sha256") != source_bundle, "raw checks are not bound to current source bundle")
    raw_git = raw.get("git_binding", {}) if isinstance(raw.get("git_binding"), dict) else {}
    source_head = raw_git.get("head_sha") if isinstance(raw_git.get("head_sha"), str) else ""
    suffix_ok, suffix_files, suffix_violations, suffix_error = evidence_suffix_status(source_head, "HEAD")
    add(blocking, not head_ok or not source_head, "raw checks do not identify a reviewed source HEAD")
    add(blocking, not suffix_ok, "current HEAD is not an evidence-only suffix of reviewed source HEAD: " + (suffix_error or ", ".join(suffix_violations)))

    add(blocking, brain_review.get("task_id") != task_id, "Brain review task_id mismatch")
    add(blocking, brain_review.get("review_verdict") != "PASS", "Brain semantic review is not PASS")
    add(blocking, brain_review.get("semantic_drift_status") != "PASS", "semantic drift review is not PASS")
    add(blocking, brain_review.get("scope_drift_status") != "PASS", "scope drift review is not PASS")
    add(blocking, brain_review.get("overdesign_status") != "PASS", "overdesign review is not PASS")
    add(blocking, brain_review.get("original_problem_actually_solved") is not True, "original user problem is not proven solved")
    add(blocking, brain_review.get("technically_correct_but_practically_wrong_risk") != "NONE_FOUND", "practically-wrong risk is present or unknown")
    add(blocking, brain_review.get("reviewed_source_bundle_sha256") != source_bundle, "Brain review is not bound to current source bundle")
    add(blocking, brain_review.get("reviewed_bridge_hash") != bridge_hash, "Brain review is not bound to current bridge")
    add(blocking, brain_review.get("reviewed_input_bundle_hash") != input_bundle_hash, "Brain review is not bound to current input bundle")
    add(blocking, brain_review.get("reviewed_source_head_sha") != source_head, "Brain review is not bound to the reviewed source HEAD")

    planned_steps = acceptance_plan.get("steps", []) if isinstance(acceptance_plan, dict) else []
    planned_ids = [step.get("acceptance_id") for step in planned_steps if isinstance(step, dict) and step.get("acceptance_id")]
    completed_ids = acceptance.get("completed_acceptance_ids", []) if isinstance(acceptance, dict) else []
    add(blocking, acceptance.get("artifact_origin") != "HUMAN_ACCEPTANCE", "acceptance receipt is not human-origin evidence")
    add(blocking, acceptance.get("task_id") != task_id, "acceptance receipt task_id mismatch")
    add(blocking, acceptance.get("user_acceptance_status") != "PASS", "user acceptance is not PASS")
    add(blocking, sorted(set(completed_ids)) != sorted(set(planned_ids)), "user acceptance does not cover the predefined plan")
    add(blocking, acceptance.get("technically_correct_but_practically_wrong") is True, "user reports practically wrong result")
    add(blocking, acceptance.get("bound_bridge_hash") != bridge_hash, "user acceptance is not bound to current bridge")
    add(blocking, acceptance.get("bound_input_bundle_hash") != input_bundle_hash, "user acceptance is not bound to current input bundle")
    add(blocking, acceptance.get("bound_source_bundle_sha256") != source_bundle, "user acceptance is not bound to current source bundle")
    add(blocking, acceptance.get("bound_source_head_sha") != source_head, "user acceptance is not bound to the reviewed source HEAD")

    changed_ok, changed, changed_err = changed_files()
    if not changed_ok:
        blocking.append("cannot determine PR diff: " + changed_err)
    else:
        allowed_paths = bridge.get("allowed_paths", []) if isinstance(bridge.get("allowed_paths"), list) else []
        violations = [path for path in changed if not is_within_allowed(path, allowed_paths)]
        add(blocking, bool(violations), "PR diff outside allowed_paths: " + ", ".join(violations))

    add(blocking, pr.get("pr_required") is True and not pr.get("pr_present"), "missing required PR evidence")
    add(blocking, pr.get("task_id") != task_id, "PR receipt task_id mismatch")
    add(blocking, pr.get("branch_name") != raw_git.get("branch"), "PR receipt branch mismatch")
    add(blocking, pr.get("verified_source_head_sha") != source_head, "PR receipt is not bound to the reviewed source HEAD")

    human_review = Path(__file__).resolve().parents[1] / "observer/human_review_packet.md"
    add(blocking, not human_review.exists() or not human_review.read_text(encoding="utf-8").strip(), "missing human review packet")

    pending_items = pending.get("pending_items", []) if isinstance(pending, dict) else []
    if pending_items:
        warnings.append("formal pending items recorded: " + str(len(pending_items)))

    result = {
        "artifact_type": "JOYFLOW_RECONCILE_RESULT",
        "artifact_version": "2",
        "task_id": task_id,
        "closure_ready": len(blocking) == 0,
        "blocking_items": blocking,
        "warnings": warnings,
        "bindings": {
            "current_head_sha": head_sha,
            "reviewed_source_head_sha": source_head,
            "evidence_only_suffix_files": suffix_files,
            "head_sha": head_sha,
            "bridge_hash": bridge_hash,
            "input_bundle_hash": input_bundle_hash,
            "source_bundle_sha256": source_bundle,
        },
        "machine_checks_complete": raw.get("exit_code") == 0,
        "brain_semantic_review_passed": brain_review.get("review_verdict") == "PASS",
        "user_acceptance_passed": acceptance.get("user_acceptance_status") == "PASS",
        "human_approval_required": True,
    }
    write_json("observer/reconcile_result.json", result)
    print("JOYFLOW_RECONCILE_READY" if not blocking else "JOYFLOW_RECONCILE_BLOCKED")
    print(result)
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
