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

CONTRACT_PATH = "runtime/translation_contract.json"
MEANING_PATH = "runtime/product_meaning_closure.json"
INTERPRETATION_PATH = "runtime/codex_execution_interpretation.json"
RECEIPT_PATH = "observer/contract_red_team_receipt.json"
ROUTING_PATH = "runtime/routing_result.json"


def main() -> int:
    contract: Dict[str, Any] = read_json(CONTRACT_PATH, default={})
    meaning: Dict[str, Any] = read_json(MEANING_PATH, default={})
    interpretation: Dict[str, Any] = read_json(INTERPRETATION_PATH, default={})
    red_team: Dict[str, Any] = read_json(RECEIPT_PATH, default={})

    seed = contract.get("task_id") or contract.get("deterministic_intent") or contract.get("human_intent") or lower_join(contract)
    task_id = str(contract.get("task_id") or meaning.get("task_id") or stable_task_id(str(seed)))
    text = lower_join(contract)

    basis: List[str] = []
    hard_hits = keyword_hits(text, HARD_STOP_KEYWORDS)
    review_hits = keyword_hits(text, REVIEW_KEYWORDS)
    if not contract.get("uncertainties") and "uncertain" in review_hits:
        review_hits.remove("uncertain")
    low_hits = keyword_hits(text, LOW_RISK_HINTS)

    confirmation = meaning.get("user_confirmation") if isinstance(meaning.get("user_confirmation"), dict) else {}
    meaning_confirmed = confirmation.get("status") == "CONFIRMED"
    material_ambiguity = meaning.get("material_ambiguity_status") != "NO_MATERIAL_AMBIGUITY"
    interpretation_status = interpretation.get("interpretation_status")
    lean_embedded = bool(contract.get("lean_interpretation_embedded"))
    interpretation_allows_execution = interpretation_status == "ALIGNED" or lean_embedded

    if not meaning_confirmed:
        target_lane = "HARD_STOP_LANE"
        risk_level = "HIGH"
        execution_allowed = False
        blocked_reason = "product meaning is not user-confirmed"
        basis.append("product_meaning_unconfirmed")
    elif material_ambiguity:
        target_lane = "HARD_STOP_LANE"
        risk_level = "HIGH"
        execution_allowed = False
        blocked_reason = "material product ambiguity remains"
        basis.append("material_ambiguity_remains")
    elif not interpretation_allows_execution:
        target_lane = "HARD_STOP_LANE"
        risk_level = "HIGH"
        execution_allowed = False
        blocked_reason = "Codex interpretation is not aligned"
        basis.append("codex_interpretation_not_aligned")
    elif red_team.get("verdict") == "BLOCK" or red_team.get("execution_blocked") is True:
        target_lane = "HARD_STOP_LANE"
        risk_level = "HIGH"
        execution_allowed = False
        blocked_reason = "contract red-team blocked execution"
        basis.append("contract_red_team_block")
    elif hard_hits:
        target_lane = "HARD_STOP_LANE"
        risk_level = "HIGH"
        execution_allowed = False
        blocked_reason = "hard-stop keywords: " + ", ".join(hard_hits)
        basis.append("hard_stop_keywords")
    elif contract.get("uncertainties") or red_team.get("verdict") == "WARN" or review_hits:
        target_lane = "REVIEW_QUEUE_LANE"
        risk_level = "MEDIUM"
        execution_allowed = True
        blocked_reason = ""
        basis.append("uncertain_or_review_required")
    elif low_hits:
        target_lane = "FAST_LANE"
        risk_level = "LOW"
        execution_allowed = True
        blocked_reason = ""
        basis.append("low_risk_documentation_or_text_change")
    else:
        target_lane = "REVIEW_QUEUE_LANE"
        risk_level = "MEDIUM"
        execution_allowed = True
        blocked_reason = ""
        basis.append("default_review_queue")

    if red_team.get("recommended_lane") and red_team.get("recommended_lane") != target_lane:
        basis.append(f"red_team_recommended={red_team.get('recommended_lane')}")

    routing = {
        "task_id": task_id,
        "target_lane": target_lane,
        "risk_level": risk_level,
        "execution_allowed": execution_allowed,
        "blocked_reason": blocked_reason,
        "routing_basis": basis,
        "semantic_closure_gate": {
            "meaning_confirmed": meaning_confirmed,
            "no_material_ambiguity": not material_ambiguity,
            "interpretation_status": interpretation_status,
            "lean_interpretation_embedded": lean_embedded,
        },
    }
    write_json(ROUTING_PATH, routing)
    graph_sync_required = any(x in text for x in ["spec/", "flow_graph", "node_cards", "edge_cards", "rule_cards", "graph", "topology"])
    ensure_task_state_update(task_id, target_lane, graph_sync_required=graph_sync_required)
    print("JOYFLOW_ROUTE_" + target_lane)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
