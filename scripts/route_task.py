#!/usr/bin/env python3
"""Route a Joyflow task after semantic closure into an execution lane."""
from __future__ import annotations

from typing import Any, Dict, List

from joyflow_common import (
    HARD_STOP_KEYWORDS,
    LOW_RISK_HINTS,
    REVIEW_KEYWORDS,
    ensure_task_state_update,
    keyword_hits,
    lower_join,
    read_json,
    stable_task_id,
    write_json,
)
from validate_semantic_closure import execution_release_allowed, lean_interpretation_allowed

CONTRACT_PATH = "runtime/translation_contract.json"
MEANING_PATH = "runtime/product_meaning_closure.json"
INTERPRETATION_PATH = "runtime/codex_execution_interpretation.json"
RECEIPT_PATH = "observer/contract_red_team_receipt.json"
ROUTING_PATH = "runtime/routing_result.json"


def routing_risk_surface(contract: Dict[str, Any]) -> Dict[str, Any]:
    """Return only fields describing intended changes, not non-goals or examples.

    Negative statements such as "do not add authentication" must not themselves
    turn a task into an authentication change.
    """
    mechanical = contract.get("mechanical_execution_layer")
    if not isinstance(mechanical, dict):
        mechanical = {}
    return {
        "risk_surfaces": contract.get("risk_surfaces", []),
        "declared_risk_level": contract.get("risk_level", ""),
    }


def main() -> int:
    contract: Dict[str, Any] = read_json(CONTRACT_PATH, default={})
    meaning: Dict[str, Any] = read_json(MEANING_PATH, default={})
    interpretation: Dict[str, Any] = read_json(INTERPRETATION_PATH, default={})
    red_team: Dict[str, Any] = read_json(RECEIPT_PATH, default={})

    seed = contract.get("task_id") or contract.get("deterministic_intent") or lower_join(contract)
    task_id = str(contract.get("task_id") or meaning.get("task_id") or stable_task_id(str(seed)))
    full_text = lower_join(contract)
    risk_text = lower_join(routing_risk_surface(contract))

    basis: List[str] = []
    hard_hits = keyword_hits(risk_text, HARD_STOP_KEYWORDS)
    review_hits = keyword_hits(risk_text, REVIEW_KEYWORDS)
    low_hits = keyword_hits(risk_text, LOW_RISK_HINTS)

    confirmation = meaning.get("user_confirmation") if isinstance(meaning.get("user_confirmation"), dict) else {}
    meaning_confirmed = confirmation.get("status") == "CONFIRMED"
    no_material_ambiguity = meaning.get("material_ambiguity_status") == "NO_MATERIAL_AMBIGUITY"
    lean_allowed = lean_interpretation_allowed(contract)
    release_allowed = execution_release_allowed(contract, interpretation)
    lifecycle_mode = contract.get("lifecycle_mode")

    if lifecycle_mode == "REFERENCE_CANDIDATE":
        target_lane = "HARD_STOP_LANE"
        risk_level = "REFERENCE_ONLY"
        execution_allowed = False
        blocked_reason = "reference candidate is not an active execution task"
        basis.append("reference_candidate_non_executable")
    elif lifecycle_mode != "ACTIVE_TASK":
        target_lane = "HARD_STOP_LANE"
        risk_level = "HIGH"
        execution_allowed = False
        blocked_reason = "invalid lifecycle mode"
        basis.append("invalid_lifecycle_mode")
    elif not meaning_confirmed:
        target_lane = "HARD_STOP_LANE"
        risk_level = "HIGH"
        execution_allowed = False
        blocked_reason = "product meaning is not user-confirmed"
        basis.append("product_meaning_unconfirmed")
    elif not no_material_ambiguity:
        target_lane = "HARD_STOP_LANE"
        risk_level = "HIGH"
        execution_allowed = False
        blocked_reason = "material product ambiguity remains"
        basis.append("material_ambiguity_remains")
    elif not release_allowed:
        target_lane = "HARD_STOP_LANE"
        risk_level = "HIGH"
        execution_allowed = False
        blocked_reason = "active task lacks authentic aligned Codex interpretation"
        basis.append("codex_interpretation_not_authentic_or_aligned")
    elif red_team.get("verdict") == "BLOCK" or red_team.get("execution_blocked") is True:
        target_lane = "HARD_STOP_LANE"
        risk_level = "HIGH"
        execution_allowed = False
        blocked_reason = "contract red-team blocked execution"
        basis.append("contract_red_team_block")
    elif hard_hits or str(contract.get("risk_level", "")).lower() == "high":
        target_lane = "HARD_STOP_LANE"
        risk_level = "HIGH"
        execution_allowed = False
        blocked_reason = "high-risk execution surface requires explicit successor approval"
        if hard_hits:
            blocked_reason += ": " + ", ".join(hard_hits)
        basis.append("hard_stop_execution_surface")
    elif contract.get("uncertainties") or red_team.get("verdict") == "WARN" or review_hits:
        target_lane = "REVIEW_QUEUE_LANE"
        risk_level = "MEDIUM"
        execution_allowed = True
        blocked_reason = ""
        basis.append("review_required")
    elif low_hits and lean_allowed:
        target_lane = "FAST_LANE"
        risk_level = "LOW"
        execution_allowed = True
        blocked_reason = ""
        basis.append("mechanically_proven_lean")
    else:
        target_lane = "REVIEW_QUEUE_LANE"
        risk_level = "MEDIUM"
        execution_allowed = True
        blocked_reason = ""
        basis.append("default_review_queue")

    routing = {
        "artifact_type": "JOYFLOW_ROUTING_RESULT",
        "artifact_version": "2",
        "task_id": task_id,
        "lifecycle_mode": lifecycle_mode,
        "target_lane": target_lane,
        "risk_level": risk_level,
        "execution_allowed": execution_allowed,
        "blocked_reason": blocked_reason,
        "routing_basis": basis,
        "routing_keyword_hits": {
            "hard_stop": hard_hits,
            "review": review_hits,
            "low_risk": low_hits,
            "scope_only": True,
        },
        "semantic_closure_gate": {
            "meaning_confirmed": meaning_confirmed,
            "no_material_ambiguity": no_material_ambiguity,
            "external_interpretation_status": interpretation.get("interpretation_status"),
            "active_execution_release_allowed": release_allowed,
            "lean_interpretation_embedded": contract.get("lean_interpretation_embedded") is True,
            "lean_eligibility_mechanically_proven": lean_allowed,
        },
    }
    write_json(ROUTING_PATH, routing)
    graph_sync_required = any(x in full_text for x in ["spec/", "flow_graph", "node_cards", "edge_cards", "rule_cards", "graph", "topology"])
    ensure_task_state_update(task_id, target_lane, graph_sync_required=graph_sync_required)
    print("JOYFLOW_ROUTE_" + target_lane)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
