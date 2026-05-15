#!/usr/bin/env python3
"""Joyflow Phase 1 reconcile runner.

This is the only machine writer of closure_ready. It does not approve closure;
human approval is still required after this result.
"""
from __future__ import annotations

from typing import Any, Dict, List

from joyflow_common import changed_files, is_within_allowed, operational_output_paths, read_json, write_json


def add(blocking: List[str], condition: bool, reason: str) -> None:
    if condition:
        blocking.append(reason)


def main() -> int:
    blocking: List[str] = []
    warnings: List[str] = []

    raw: Dict[str, Any] = read_json("observer/raw_check_results.json", default={})
    bridge: Dict[str, Any] = read_json("runtime/execution_bridge_package.json", default={})
    red_team: Dict[str, Any] = read_json("observer/contract_red_team_receipt.json", default={})
    pr: Dict[str, Any] = read_json("observer/pr_receipt.json", default={})
    acceptance: Dict[str, Any] = read_json("observer/acceptance_receipt.json", default={})
    pending: Dict[str, Any] = read_json("shadow/pending_formal_truth.json", default={})

    add(blocking, raw.get("exit_code") != 0, "checks did not pass")
    add(blocking, red_team.get("verdict") == "BLOCK" or bool(red_team.get("execution_blocked")), "contract red-team blocks execution")
    add(blocking, bridge.get("target_lane") == "HARD_STOP_LANE" and bool(bridge.get("execution_allowed")), "HARD_STOP is executable")
    add(blocking, not isinstance(acceptance, dict), "acceptance receipt invalid")

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
        from pathlib import Path
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
        "human_approval_required": True,
    }
    write_json("observer/reconcile_result.json", result)
    print("JOYFLOW_RECONCILE_READY" if not blocking else "JOYFLOW_RECONCILE_BLOCKED")
    print(result)
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
