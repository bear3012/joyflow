#!/usr/bin/env python3
"""Joyflow reconcile runner.

This is the only machine writer of closure_ready. It checks evidence and declared
semantic review status, but it does not approve product meaning or human acceptance.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from joyflow_common import changed_files, is_within_allowed, operational_output_paths, read_json, write_json
from validate_semantic_closure import validate_all as validate_semantic_closure


def add(blocking: List[str], condition: bool, reason: str) -> None:
    if condition:
        blocking.append(reason)


def main() -> int:
    blocking: List[str] = []
    warnings: List[str] = []

    raw: Dict[str, Any] = read_json("observer/raw_check_results.json", default={})
    bridge: Dict[str, Any] = read_json("runtime/execution_bridge_package.json", default={})
    red_team: Dict[str, Any] = read_json("observer/contract_red_team_receipt.json", default={})
    brain_review: Dict[str, Any] = read_json("observer/brain_semantic_review.json", default={})
    pr: Dict[str, Any] = read_json("observer/pr_receipt.json", default={})
    acceptance: Dict[str, Any] = read_json("observer/acceptance_receipt.json", default={})
    acceptance_plan: Dict[str, Any] = read_json("runtime/user_acceptance_plan.json", default={})
    pending: Dict[str, Any] = read_json("shadow/pending_formal_truth.json", default={})

    semantic_ok, semantic_findings = validate_semantic_closure(include_review=True)
    add(blocking, not semantic_ok, "semantic closure validation failed: " + "; ".join(semantic_findings))
    add(blocking, raw.get("exit_code") != 0, "checks did not pass")
    add(blocking, red_team.get("verdict") == "BLOCK" or bool(red_team.get("execution_blocked")), "contract red-team blocks execution")
    add(blocking, bridge.get("target_lane") == "HARD_STOP_LANE" and bool(bridge.get("execution_allowed")), "HARD_STOP is executable")

    add(blocking, brain_review.get("review_verdict") != "PASS", "Brain semantic review is not PASS")
    add(blocking, brain_review.get("semantic_drift_status") != "PASS", "semantic drift review is not PASS")
    add(blocking, brain_review.get("scope_drift_status") != "PASS", "scope drift review is not PASS")
    add(blocking, brain_review.get("overdesign_status") != "PASS", "overdesign review is not PASS")
    add(blocking, brain_review.get("original_problem_actually_solved") is not True, "original user problem is not proven solved")
    add(
        blocking,
        brain_review.get("technically_correct_but_practically_wrong_risk") != "NONE_FOUND",
        "technically-correct-but-practically-wrong risk is present or unknown",
    )

    planned_steps = acceptance_plan.get("steps", []) if isinstance(acceptance_plan, dict) else []
    planned_ids = [step.get("acceptance_id") for step in planned_steps if isinstance(step, dict) and step.get("acceptance_id")]
    completed_ids = acceptance.get("completed_acceptance_ids", []) if isinstance(acceptance, dict) else []
    add(blocking, not isinstance(acceptance, dict), "acceptance receipt invalid")
    add(blocking, acceptance.get("user_acceptance_status") != "PASS", "user acceptance is not PASS")
    add(blocking, sorted(set(completed_ids)) != sorted(set(planned_ids)), "user acceptance does not cover the predefined acceptance plan")
    add(blocking, acceptance.get("technically_correct_but_practically_wrong") is True, "user reports practically wrong result")

    changed_ok, changed, changed_err = changed_files()
    if not changed_ok:
        blocking.append("cannot determine changed files: " + changed_err)
        source_changes = []
    else:
        operational_paths = operational_output_paths(bridge)
        allowed_paths = bridge.get("allowed_paths", []) if isinstance(bridge.get("allowed_paths", []), list) else []
        combined_allowed = allowed_paths + operational_paths
        violations = [p for p in changed if not is_within_allowed(p, combined_allowed)]
        add(blocking, bool(violations), "changed files outside allowed_paths: " + ", ".join(violations))
        source_changes = [p for p in changed if not is_within_allowed(p, operational_paths)]

    if source_changes:
        add(blocking, pr.get("pr_required") is True and not pr.get("pr_present"), "missing required PR evidence")

    human_review = "observer/human_review_packet.md"
    try:
        review_text = Path(__file__).resolve().parents[1].joinpath(human_review).read_text(encoding="utf-8")
        add(blocking, not review_text.strip(), "missing human review packet content")
    except Exception:
        blocking.append("missing human review packet")

    pending_items = pending.get("pending_items", []) if isinstance(pending, dict) else []
    if pending_items:
        warnings.append("formal pending items recorded: " + str(len(pending_items)))

    result = {
        "closure_ready": len(blocking) == 0,
        "blocking_items": blocking,
        "warnings": warnings,
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
