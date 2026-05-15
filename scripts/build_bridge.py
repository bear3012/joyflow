#!/usr/bin/env python3
"""Build runtime/execution_bridge_package.json from routing and translation contract."""
from __future__ import annotations

from typing import Any, Dict, List

from joyflow_common import infer_allowed_paths, read_json, stable_task_id, write_json

CONTRACT_PATH = "runtime/translation_contract.json"
ROUTING_PATH = "runtime/routing_result.json"
RECEIPT_PATH = "observer/contract_red_team_receipt.json"
BRIDGE_PATH = "runtime/execution_bridge_package.json"

REQUIRED_OUTPUT_FILES = [
    "observer/contract_red_team_receipt.json",
    "runtime/contract_red_team_review.md",
    "observer/raw_check_results.json",
    "observer/acceptance_receipt.json",
    "observer/pr_receipt.json",
    "observer/human_review_packet.md",
    "observer/reconcile_result.json",
]


def as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def main() -> int:
    contract: Dict[str, Any] = read_json(CONTRACT_PATH, default={})
    routing: Dict[str, Any] = read_json(ROUTING_PATH, default={})
    red_team: Dict[str, Any] = read_json(RECEIPT_PATH, default={})

    task_id = routing.get("task_id") or stable_task_id(str(contract.get("deterministic_intent") or contract.get("human_intent") or contract))
    target_lane = routing.get("target_lane") or "REVIEW_QUEUE_LANE"
    execution_allowed = bool(routing.get("execution_allowed"))
    blocked_reason = str(routing.get("blocked_reason") or "")

    if red_team.get("verdict") == "BLOCK" or red_team.get("execution_blocked") is True:
        execution_allowed = False
        target_lane = "HARD_STOP_LANE"
        blocked_reason = blocked_reason or "contract red-team blocked execution"

    if target_lane == "HARD_STOP_LANE":
        execution_allowed = False
        blocked_reason = blocked_reason or "HARD_STOP_LANE forbids execution"

    allowed_paths = infer_allowed_paths(contract, target_lane)
    acceptance_checks = as_list(contract.get("acceptance_checks"))
    human_points = as_list(contract.get("human_observation_points"))

    bridge = {
        "task_identity": {
            "task_id": task_id,
            "task_title": str(contract.get("deterministic_intent") or contract.get("human_intent") or "Joyflow task")[:160],
        },
        "execution_mode": "PATCH_MODE",
        "target_lane": target_lane,
        "risk_level": routing.get("risk_level", "MEDIUM"),
        "execution_allowed": execution_allowed,
        "blocked_reason": blocked_reason,
        "non_negotiables": as_list(contract.get("must_not_infer")),
        "forbidden": as_list(contract.get("forbidden_outcomes")),
        "acceptance_boundary": acceptance_checks,
        "acceptance_command": "bash tests/run_checks.sh",
        "required_output_files": REQUIRED_OUTPUT_FILES,
        "truth_fingerprint": {
            "mode": "PHASE1_PLACEHOLDER",
            "value": "PHASE1_PLACEHOLDER_UNVERIFIED",
        },
        "evidence_slots": [
            "observer/contract_red_team_receipt.json",
            "observer/raw_check_results.json",
            "observer/acceptance_receipt.json",
            "observer/pr_receipt.json",
            "observer/human_review_packet.md",
            "observer/reconcile_result.json",
        ],
        "allowed_paths": allowed_paths,
        "required_inputs": [
            "runtime/translation_contract.json",
            "runtime/routing_result.json",
            "observer/contract_red_team_receipt.json",
            "AGENTS.md",
        ],
        "local_graph_subtree": [
            "H4_TRANSLATION_CONTRACT",
            "R0_CONTRACT_RED_TEAM_REVIEW",
            "N1_ROUTE_TASK",
            "N3_BUILD_BRIDGE",
            "N4_BUILD_CONTEXT_PALACE",
            "N5_BUILD_CODEX_PACKET",
            "N6_HUMAN_HANDOVER_TO_CODEX_APP",
            "N8_RUN_CHECKS",
            "N11_RECONCILE",
        ],
        "graph_refs": [
            "spec/flow_graph.md",
            "spec/node_cards.md",
            "spec/edge_cards.md",
            "spec/rule_cards.md",
        ],
        "expected_affected_zones": allowed_paths,
        "formalization_state": "PHASE1_OPERATIONAL",
        "pending_formal_truth_ref": "shadow/pending_formal_truth.json",
        "contract_red_team_ref": "observer/contract_red_team_receipt.json",
        "human_observation_points": human_points,
    }

    write_json(BRIDGE_PATH, bridge)
    print("JOYFLOW_BRIDGE_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
