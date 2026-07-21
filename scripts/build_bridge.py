#!/usr/bin/env python3
"""Build runtime/execution_bridge_package.json from semantic closure, routing, and contract."""
from __future__ import annotations

from typing import Any, Dict, List

from joyflow_common import infer_allowed_paths, read_json, stable_task_id, write_json

CONTRACT_PATH = "runtime/translation_contract.json"
MEANING_PATH = "runtime/product_meaning_closure.json"
DELTA_PATH = "runtime/meaning_delta.json"
GOLDEN_PATH = "runtime/golden_cases.json"
ACCEPTANCE_PLAN_PATH = "runtime/user_acceptance_plan.json"
INTERPRETATION_PATH = "runtime/codex_execution_interpretation.json"
BRAIN_REVIEW_PATH = "observer/brain_semantic_review.json"
ROUTING_PATH = "runtime/routing_result.json"
RECEIPT_PATH = "observer/contract_red_team_receipt.json"
BRIDGE_PATH = "runtime/execution_bridge_package.json"

REQUIRED_OUTPUT_FILES = [
    "observer/contract_red_team_receipt.json",
    "runtime/contract_red_team_review.md",
    "observer/raw_check_results.json",
    "observer/brain_semantic_review.json",
    "observer/acceptance_receipt.json",
    "observer/pr_receipt.json",
    "observer/human_review_packet.md",
    "observer/reconcile_result.json",
]


def as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def main() -> int:
    contract: Dict[str, Any] = read_json(CONTRACT_PATH, default={})
    meaning: Dict[str, Any] = read_json(MEANING_PATH, default={})
    interpretation: Dict[str, Any] = read_json(INTERPRETATION_PATH, default={})
    routing: Dict[str, Any] = read_json(ROUTING_PATH, default={})
    red_team: Dict[str, Any] = read_json(RECEIPT_PATH, default={})

    task_id = (
        contract.get("task_id")
        or meaning.get("task_id")
        or routing.get("task_id")
        or stable_task_id(str(contract.get("deterministic_intent") or contract.get("human_intent") or contract))
    )
    target_lane = routing.get("target_lane") or "REVIEW_QUEUE_LANE"
    execution_allowed = bool(routing.get("execution_allowed"))
    blocked_reason = str(routing.get("blocked_reason") or "")

    confirmation = meaning.get("user_confirmation") if isinstance(meaning.get("user_confirmation"), dict) else {}
    meaning_confirmed = confirmation.get("status") == "CONFIRMED"
    no_material_ambiguity = meaning.get("material_ambiguity_status") == "NO_MATERIAL_AMBIGUITY"
    interpretation_aligned = interpretation.get("interpretation_status") == "ALIGNED"
    lean_embedded = bool(contract.get("lean_interpretation_embedded"))

    if not meaning_confirmed:
        execution_allowed = False
        blocked_reason = blocked_reason or "product meaning is not user-confirmed"
    if not no_material_ambiguity:
        execution_allowed = False
        blocked_reason = blocked_reason or "material product ambiguity remains"
    if not (interpretation_aligned or lean_embedded):
        execution_allowed = False
        blocked_reason = blocked_reason or "Codex execution interpretation is not aligned"

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
    semantic_layer = contract.get("human_semantic_layer") if isinstance(contract.get("human_semantic_layer"), dict) else {}
    mechanical_layer = contract.get("mechanical_execution_layer") if isinstance(contract.get("mechanical_execution_layer"), dict) else {}

    bridge = {
        "task_identity": {
            "task_id": task_id,
            "task_title": str(
                semantic_layer.get("objective")
                or contract.get("deterministic_intent")
                or contract.get("human_intent")
                or "Joyflow task"
            )[:160],
        },
        "execution_mode": "PATCH_MODE",
        "target_lane": target_lane,
        "risk_level": routing.get("risk_level", "MEDIUM"),
        "execution_allowed": execution_allowed,
        "blocked_reason": blocked_reason,
        "product_result": semantic_layer.get("expected_user_result", ""),
        "must_preserve": as_list(mechanical_layer.get("must_preserve")),
        "allowed_solution_surfaces": as_list(mechanical_layer.get("allowed_solution_surfaces")),
        "allowed_technical_freedom": as_list(mechanical_layer.get("allowed_technical_freedom")),
        "non_negotiables": as_list(contract.get("must_not_infer")) + as_list(mechanical_layer.get("stop_conditions")),
        "forbidden": as_list(contract.get("forbidden_outcomes")) + as_list(mechanical_layer.get("forbidden_consequences")),
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
            "observer/brain_semantic_review.json",
            "observer/acceptance_receipt.json",
            "observer/pr_receipt.json",
            "observer/human_review_packet.md",
            "observer/reconcile_result.json",
        ],
        "semantic_closure_refs": {
            "product_meaning": MEANING_PATH,
            "meaning_delta": DELTA_PATH,
            "golden_cases": GOLDEN_PATH,
            "user_acceptance_plan": ACCEPTANCE_PLAN_PATH,
            "codex_interpretation": INTERPRETATION_PATH,
            "brain_semantic_review": BRAIN_REVIEW_PATH,
        },
        "golden_case_refs": as_list(contract.get("golden_case_refs")),
        "deviation_default": contract.get("deviation_default", "BRAIN_REVIEW_REQUIRED"),
        "allowed_paths": allowed_paths,
        "required_inputs": [
            MEANING_PATH,
            CONTRACT_PATH,
            DELTA_PATH,
            GOLDEN_PATH,
            ACCEPTANCE_PLAN_PATH,
            INTERPRETATION_PATH,
            ROUTING_PATH,
            RECEIPT_PATH,
            "AGENTS.md",
            "spec/semantic_closure.md",
        ],
        "local_graph_subtree": [
            "H4_PRODUCT_MEANING_CLOSURE",
            "H5_DUAL_LAYER_TRANSLATION_CONTRACT",
            "R0_CONTRACT_RED_TEAM_REVIEW",
            "N1_ROUTE_TASK",
            "N3_BUILD_BRIDGE",
            "N4_BUILD_CONTEXT_PALACE",
            "N5_BUILD_CODEX_PACKET",
            "N5A_CODEX_EXECUTION_INTERPRETATION",
            "N6_HUMAN_HANDOVER_TO_CODEX_APP",
            "N8_RUN_CHECKS",
            "N9A_BRAIN_SEMANTIC_REVIEW",
            "N10_USER_ACCEPTANCE",
            "N11_RECONCILE",
        ],
        "graph_refs": [
            "spec/flow_graph.md",
            "spec/node_cards.md",
            "spec/edge_cards.md",
            "spec/rule_cards.md",
            "spec/semantic_closure.md",
        ],
        "expected_affected_zones": allowed_paths,
        "formalization_state": "PHASE1_SEMANTIC_CLOSURE_CANDIDATE",
        "pending_formal_truth_ref": "shadow/pending_formal_truth.json",
        "contract_red_team_ref": RECEIPT_PATH,
        "human_observation_points": human_points,
    }

    write_json(BRIDGE_PATH, bridge)
    print("JOYFLOW_BRIDGE_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
