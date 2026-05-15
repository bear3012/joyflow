#!/usr/bin/env python3
"""Route a Joyflow task into FAST_LANE, REVIEW_QUEUE_LANE, or HARD_STOP_LANE."""
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
RECEIPT_PATH = "observer/contract_red_team_receipt.json"
ROUTING_PATH = "runtime/routing_result.json"


def main() -> int:
    contract: Dict[str, Any] = read_json(CONTRACT_PATH, default={})
    red_team: Dict[str, Any] = read_json(RECEIPT_PATH, default={})

    seed = contract.get("deterministic_intent") or contract.get("human_intent") or lower_join(contract)
    task_id = stable_task_id(str(seed))
    text = lower_join(contract)

    basis: List[str] = []
    hard_hits = keyword_hits(text, HARD_STOP_KEYWORDS)
    review_hits = keyword_hits(text, REVIEW_KEYWORDS)
    if not contract.get("uncertainties") and "uncertain" in review_hits:
        review_hits.remove("uncertain")
    low_hits = keyword_hits(text, LOW_RISK_HINTS)

    if red_team.get("verdict") == "BLOCK" or red_team.get("execution_blocked") is True:
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
        basis.append("default_uncertain_review_queue")

    if red_team.get("recommended_lane") and red_team.get("recommended_lane") != target_lane:
        basis.append(f"red_team_recommended={red_team.get('recommended_lane')}")

    routing = {
        "task_id": task_id,
        "target_lane": target_lane,
        "risk_level": risk_level,
        "execution_allowed": execution_allowed,
        "blocked_reason": blocked_reason,
        "routing_basis": basis,
    }
    write_json(ROUTING_PATH, routing)
    graph_sync_required = any(x in text for x in ["spec/", "flow_graph", "node_cards", "edge_cards", "rule_cards", "graph", "topology"])
    ensure_task_state_update(task_id, target_lane, graph_sync_required=graph_sync_required)
    print("JOYFLOW_ROUTE_" + target_lane)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
