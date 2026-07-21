#!/usr/bin/env python3
"""Build the only formal Joyflow mutation carrier."""
from __future__ import annotations

from typing import Any, Dict, List

from joyflow_common import bundle_hash, infer_allowed_paths, read_json, source_bundle_hash, stable_task_id, write_json
from validate_semantic_closure import effective_interpretation, execution_release_allowed, lean_interpretation_allowed

CONTRACT_PATH = "runtime/translation_contract.json"
MEANING_PATH = "runtime/product_meaning_closure.json"
DELTA_PATH = "runtime/meaning_delta.json"
GOLDEN_PATH = "runtime/golden_cases.json"
ACCEPTANCE_PLAN_PATH = "runtime/user_acceptance_plan.json"
INTERPRETATION_PATH = "runtime/codex_execution_interpretation.json"
ROUTING_PATH = "runtime/routing_result.json"
RECEIPT_PATH = "observer/contract_red_team_receipt.json"
BRIDGE_PATH = "runtime/execution_bridge_package.json"

AUTHORITY_INPUTS = [
    MEANING_PATH,
    CONTRACT_PATH,
    DELTA_PATH,
    GOLDEN_PATH,
    ACCEPTANCE_PLAN_PATH,
    INTERPRETATION_PATH,
    RECEIPT_PATH,
]

EXECUTOR_WRITABLE_OUTPUTS = [
    "observer/raw_check_results.json",
]

BRAIN_ONLY_OUTPUTS = [
    "observer/brain_semantic_review.json",
    "observer/pr_receipt.json",
    "observer/human_review_packet.md",
]

HUMAN_ONLY_OUTPUTS = [
    "observer/acceptance_receipt.json",
]

MACHINE_LATE_OUTPUTS = [
    "observer/reconcile_result.json",
]


def as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def main() -> int:
    contract: Dict[str, Any] = read_json(CONTRACT_PATH, default={})
    meaning: Dict[str, Any] = read_json(MEANING_PATH, default={})
    external_interpretation: Dict[str, Any] = read_json(INTERPRETATION_PATH, default={})
    routing: Dict[str, Any] = read_json(ROUTING_PATH, default={})
    red_team: Dict[str, Any] = read_json(RECEIPT_PATH, default={})

    task_id = (
        contract.get("task_id")
        or meaning.get("task_id")
        or routing.get("task_id")
        or stable_task_id(str(contract.get("deterministic_intent") or contract))
    )
    lifecycle_mode = contract.get("lifecycle_mode")
    target_lane = routing.get("target_lane") or "HARD_STOP_LANE"
    execution_allowed = bool(routing.get("execution_allowed"))
    blocked_reason = str(routing.get("blocked_reason") or "")

    confirmation = meaning.get("user_confirmation") if isinstance(meaning.get("user_confirmation"), dict) else {}
    meaning_confirmed = confirmation.get("status") == "CONFIRMED"
    no_material_ambiguity = meaning.get("material_ambiguity_status") == "NO_MATERIAL_AMBIGUITY"
    lean_allowed = lean_interpretation_allowed(contract)
    interpretation, interpretation_source = effective_interpretation(contract, external_interpretation)
    active_release_allowed = execution_release_allowed(contract, external_interpretation)

    if lifecycle_mode != "ACTIVE_TASK":
        execution_allowed = False
        target_lane = "HARD_STOP_LANE"
        blocked_reason = blocked_reason or "reference candidate is not executable"
    if not meaning_confirmed:
        execution_allowed = False
        blocked_reason = blocked_reason or "product meaning is not user-confirmed"
    if not no_material_ambiguity:
        execution_allowed = False
        blocked_reason = blocked_reason or "material product ambiguity remains"
    if lifecycle_mode == "ACTIVE_TASK" and not active_release_allowed:
        execution_allowed = False
        blocked_reason = blocked_reason or "active task lacks authentic aligned Codex interpretation"
    if red_team.get("verdict") == "BLOCK" or red_team.get("execution_blocked") is True:
        execution_allowed = False
        target_lane = "HARD_STOP_LANE"
        blocked_reason = blocked_reason or "contract red-team blocked execution"
    if target_lane == "HARD_STOP_LANE":
        execution_allowed = False
        blocked_reason = blocked_reason or "HARD_STOP_LANE forbids execution"

    allowed_paths = infer_allowed_paths(contract, target_lane)
    semantic_layer = contract.get("human_semantic_layer") if isinstance(contract.get("human_semantic_layer"), dict) else {}
    mechanical_layer = contract.get("mechanical_execution_layer") if isinstance(contract.get("mechanical_execution_layer"), dict) else {}
    interpretation_ref = (
        f"{CONTRACT_PATH}#/embedded_codex_interpretation"
        if lean_allowed
        else INTERPRETATION_PATH
    )

    authority_bundle, authority_hashes = bundle_hash(AUTHORITY_INPUTS)
    source_bundle, source_hashes = source_bundle_hash()

    bridge = {
        "artifact_type": "JOYFLOW_EXECUTION_BRIDGE_PACKAGE",
        "artifact_version": "2",
        "task_identity": {
            "task_id": task_id,
            "task_title": str(
                semantic_layer.get("objective")
                or contract.get("deterministic_intent")
                or "Joyflow task"
            )[:160],
        },
        "lifecycle_mode": lifecycle_mode,
        "execution_mode": "PATCH_MODE" if lifecycle_mode == "ACTIVE_TASK" else "REFERENCE_ONLY",
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
        "acceptance_boundary": as_list(contract.get("acceptance_checks")),
        "acceptance_command": "bash tests/run_checks.sh",
        "allowed_paths": allowed_paths,
        "executor_writable_outputs": EXECUTOR_WRITABLE_OUTPUTS,
        "required_output_files": EXECUTOR_WRITABLE_OUTPUTS,
        "brain_only_outputs": BRAIN_ONLY_OUTPUTS,
        "human_only_outputs": HUMAN_ONLY_OUTPUTS,
        "machine_late_outputs": MACHINE_LATE_OUTPUTS,
        "protected_authority_artifacts": AUTHORITY_INPUTS,
        "truth_fingerprint": {
            "mode": "SHA256_AUTHORITY_AND_SOURCE_BUNDLES",
            "authority_bundle_sha256": authority_bundle,
            "source_bundle_sha256": source_bundle,
        },
        "authority_input_hashes": authority_hashes,
        "source_input_hashes": source_hashes,
        "semantic_closure_refs": {
            "product_meaning": MEANING_PATH,
            "meaning_delta": DELTA_PATH,
            "golden_cases": GOLDEN_PATH,
            "user_acceptance_plan": ACCEPTANCE_PLAN_PATH,
            "codex_interpretation": interpretation_ref,
            "brain_semantic_review": "observer/brain_semantic_review.json",
        },
        "interpretation_gate": {
            "effective_source": interpretation_source,
            "effective_interpretation_status": interpretation.get("interpretation_status"),
            "active_execution_release_allowed": active_release_allowed,
            "lean_interpretation_embedded": contract.get("lean_interpretation_embedded") is True,
            "lean_eligibility_mechanically_proven": lean_allowed,
            "lean_eligibility": contract.get("lean_eligibility", {}),
        },
        "golden_case_refs": as_list(contract.get("golden_case_refs")),
        "deviation_default": contract.get("deviation_default", "BRAIN_REVIEW_REQUIRED"),
        "required_inputs": AUTHORITY_INPUTS + [
            ROUTING_PATH,
            "AGENTS.md",
            ".codex/rules.md",
            "spec/semantic_closure.md",
        ],
        "local_graph_subtree": [
            "H4_PRODUCT_MEANING_CLOSURE",
            "H5_DUAL_LAYER_TRANSLATION_CONTRACT",
            "R0_CONTRACT_RED_TEAM_REVIEW",
            "N1_ROUTE_TASK",
            "N3_BUILD_BRIDGE",
            "N4_BUILD_CONTEXT_PALACE",
            "N5A_CODEX_EXECUTION_INTERPRETATION",
            "N5_BUILD_CODEX_PACKET",
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
        "formalization_state": "PHASE1_SEMANTIC_CLOSURE_REPAIR_CANDIDATE",
        "pending_formal_truth_ref": "shadow/pending_formal_truth.json",
        "contract_red_team_ref": RECEIPT_PATH,
        "human_observation_points": as_list(contract.get("human_observation_points")),
    }

    write_json(BRIDGE_PATH, bridge)
    print("JOYFLOW_BRIDGE_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
