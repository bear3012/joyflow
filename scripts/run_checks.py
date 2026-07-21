#!/usr/bin/env python3
"""Joyflow Phase 1 mechanical check runner.

This script records evidence in observer/raw_check_results.json. It is intentionally conservative:
when it cannot prove safety, it fails closed. Mechanical validation never decides product meaning.
"""
from __future__ import annotations

from typing import Any, Dict, List

from joyflow_common import (
    ROOT,
    canonical_json_hash,
    changed_files,
    current_branch,
    is_within_allowed,
    operational_output_paths,
    read_json,
    task_state_shape_ok,
    write_json,
)
from validate_semantic_closure import (
    lean_interpretation_allowed,
    validate_all as validate_semantic_closure,
)

RESULTS: List[Dict[str, Any]] = []


def add(name: str, passed: bool, detail: Any = "") -> None:
    RESULTS.append({"name": name, "passed": bool(passed), "detail": detail})


def exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def load_bridge() -> Dict[str, Any]:
    try:
        bridge = read_json("runtime/execution_bridge_package.json", default={})
        add("bridge_json_loads", isinstance(bridge, dict), "runtime/execution_bridge_package.json")
        return bridge if isinstance(bridge, dict) else {}
    except Exception as exc:
        add("bridge_json_loads", False, str(exc))
        return {}


def main() -> int:
    required_files = [
        "subject/task_state.json",
        "runtime/product_meaning_closure.json",
        "runtime/translation_contract.json",
        "runtime/meaning_delta.json",
        "runtime/golden_cases.json",
        "runtime/user_acceptance_plan.json",
        "runtime/codex_execution_interpretation.json",
        "runtime/routing_result.json",
        "runtime/execution_bridge_package.json",
        "runtime/context_palace.md",
        "runtime/codex_task_packet.md",
        "runtime/codex_launch_manifest.json",
        "runtime/contract_red_team_review.md",
        "observer/contract_red_team_receipt.json",
        "observer/brain_semantic_review.json",
        "observer/acceptance_receipt.json",
        "observer/pr_receipt.json",
        "observer/human_review_packet.md",
        "observer/reconcile_result.json",
        "spec/semantic_closure.md",
    ]
    for rel in required_files:
        add(f"exists:{rel}", exists(rel), rel)

    try:
        state = read_json("subject/task_state.json", default={})
        add(
            "task_state_shape_exact",
            isinstance(state, dict) and task_state_shape_ok(state),
            list(state.keys()) if isinstance(state, dict) else type(state).__name__,
        )
    except Exception as exc:
        add("task_state_shape_exact", False, str(exc))

    for rel in ["bridge.json", "codex_packet.json", "runtime/bridge.json", "runtime/codex_packet.json"]:
        add(f"forbidden_carrier_absent:{rel}", not exists(rel), rel)

    semantic_ok, semantic_findings = validate_semantic_closure(include_review=True)
    add(
        "semantic_closure_artifacts_valid",
        semantic_ok,
        {"finding_count": len(semantic_findings), "findings": semantic_findings},
    )

    bridge = load_bridge()
    manifest = read_json("runtime/codex_launch_manifest.json", default={})
    packet_path = ROOT / "runtime/codex_task_packet.md"
    packet_text = packet_path.read_text(encoding="utf-8") if packet_path.exists() else ""

    if bridge and isinstance(manifest, dict):
        expected_hash = canonical_json_hash(bridge)
        add(
            "manifest_bridge_hash_matches",
            manifest.get("bridge_hash") == expected_hash,
            {"expected": expected_hash, "actual": manifest.get("bridge_hash")},
        )
        add("packet_contains_bridge_hash", f"BRIDGE_HASH: {expected_hash}" in packet_text, expected_hash)
    else:
        add("manifest_bridge_hash_matches", False, "missing bridge or manifest")
        add("packet_contains_bridge_hash", False, "missing bridge or packet")

    semantic_refs = bridge.get("semantic_closure_refs") if isinstance(bridge, dict) else None
    expected_semantic_refs = {
        "product_meaning": "runtime/product_meaning_closure.json",
        "meaning_delta": "runtime/meaning_delta.json",
        "golden_cases": "runtime/golden_cases.json",
        "user_acceptance_plan": "runtime/user_acceptance_plan.json",
        "codex_interpretation": "runtime/codex_execution_interpretation.json",
        "brain_semantic_review": "observer/brain_semantic_review.json",
    }
    add(
        "bridge_binds_semantic_closure_refs",
        isinstance(semantic_refs, dict)
        and all(semantic_refs.get(key) == value for key, value in expected_semantic_refs.items()),
        semantic_refs,
    )

    red_team = read_json("observer/contract_red_team_receipt.json", default={})
    verdict = red_team.get("verdict") if isinstance(red_team, dict) else None
    add("contract_red_team_ran", verdict in {"PASS", "WARN", "BLOCK"}, verdict)
    add(
        "contract_red_team_not_blocking",
        verdict in {"PASS", "WARN"} and not bool(red_team.get("execution_blocked")),
        red_team if isinstance(red_team, dict) else "invalid",
    )

    target_lane = bridge.get("target_lane")
    execution_allowed = bool(bridge.get("execution_allowed"))
    add(
        "hard_stop_not_executable",
        not (target_lane == "HARD_STOP_LANE" and execution_allowed),
        {"target_lane": target_lane, "execution_allowed": execution_allowed},
    )
    if target_lane == "HARD_STOP_LANE":
        add("hard_stop_packet_halts", "HALT" in packet_text and "Do not modify files" in packet_text, "packet must halt")

    interpretation = read_json("runtime/codex_execution_interpretation.json", default={})
    contract = read_json("runtime/translation_contract.json", default={})
    interpretation_status = interpretation.get("interpretation_status") if isinstance(interpretation, dict) else None
    lean_allowed = lean_interpretation_allowed(contract if isinstance(contract, dict) else {})
    add(
        "codex_interpretation_allows_execution",
        interpretation_status == "ALIGNED" or lean_allowed,
        {
            "interpretation_status": interpretation_status,
            "lean_interpretation_embedded": contract.get("lean_interpretation_embedded") if isinstance(contract, dict) else None,
            "lean_eligibility_mechanically_proven": lean_allowed,
        },
    )
    gate = bridge.get("interpretation_gate") if isinstance(bridge.get("interpretation_gate"), dict) else {}
    add(
        "bridge_lean_gate_matches_validator",
        gate.get("lean_eligibility_mechanically_proven") is lean_allowed,
        {"bridge": gate.get("lean_eligibility_mechanically_proven"), "validator": lean_allowed},
    )

    branch_ok, branch = current_branch()
    add("git_branch_detected", branch_ok, branch)

    changed_ok, changed, changed_err = changed_files()
    add("git_changed_files_detected", changed_ok, changed if changed_ok else changed_err)

    allowed_paths = bridge.get("allowed_paths", []) if isinstance(bridge.get("allowed_paths", []), list) else []
    operational_paths = operational_output_paths(bridge)
    combined_allowed = list(allowed_paths) + operational_paths

    if changed_ok:
        filtered_changed = [p for p in changed if "__pycache__/" not in p and not p.endswith(".pyc")]
        violations = [p for p in filtered_changed if not is_within_allowed(p, combined_allowed)]
        add(
            "changed_files_within_allowed_paths",
            not violations,
            {
                "changed_files": filtered_changed,
                "violations": violations,
                "allowed_paths": allowed_paths,
                "operational_paths": operational_paths,
            },
        )
        source_changes = [p for p in filtered_changed if not is_within_allowed(p, operational_paths)]
        code_or_repo_changing = bool(source_changes)
    else:
        add("changed_files_within_allowed_paths", False, changed_err)
        source_changes = []
        code_or_repo_changing = True

    if code_or_repo_changing:
        add("non_main_for_repo_changing_task", branch_ok and branch not in {"main", "master"}, branch)
    else:
        add("non_main_for_repo_changing_task", True, "no source changes detected")

    for rel in bridge.get("required_output_files", []) if isinstance(bridge.get("required_output_files", []), list) else []:
        add(f"required_output_exists:{rel}", exists(rel), rel)

    pr = read_json("observer/pr_receipt.json", default={})
    add(
        "pr_receipt_shape",
        isinstance(pr, dict) and {"branch_name", "pr_url", "pr_required", "pr_present"}.issubset(pr.keys()),
        pr,
    )

    exit_code = 0 if all(item["passed"] for item in RESULTS) else 1
    out = {
        "command": "bash tests/run_checks.sh",
        "exit_code": exit_code,
        "checks": RESULTS,
    }
    write_json("observer/raw_check_results.json", out)
    print("JOYFLOW_CHECKS_PASS" if exit_code == 0 else "JOYFLOW_CHECKS_FAIL")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
