#!/usr/bin/env python3
"""Minimal pre-execution contract red-team review for Joyflow Phase 1.

This script is mechanical and conservative. It reviews the translation contract before routing/execution,
then writes a human-readable review and a machine-readable receipt. It never writes subject state.
"""
from __future__ import annotations

from typing import Any, Dict, List

from joyflow_common import (
    HARD_STOP_KEYWORDS,
    REVIEW_KEYWORDS,
    keyword_hits,
    lower_join,
    read_json,
    read_text,
    stable_task_id,
    write_json,
    write_text,
)

CONTRACT_PATH = "runtime/translation_contract.json"
REVIEW_PATH = "runtime/contract_red_team_review.md"
RECEIPT_PATH = "observer/contract_red_team_receipt.json"

REQUIRED_LIST_FIELDS = [
    "translated_engineering_scope",
    "non_goals",
    "must_not_infer",
    "forbidden_outcomes",
    "acceptance_checks",
    "human_observation_points",
]


def as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def main() -> int:
    contract: Dict[str, Any] = read_json(CONTRACT_PATH, default={})
    human_card = read_text("runtime/human_intent_card.md")
    task_seed = contract.get("deterministic_intent") or contract.get("human_intent") or human_card
    task_id = stable_task_id(str(task_seed))

    blocking: List[str] = []
    warnings: List[str] = []
    questions: List[str] = []

    if not str(contract.get("deterministic_intent", "")).strip():
        blocking.append("deterministic_intent is empty")

    for field in REQUIRED_LIST_FIELDS:
        if not as_list(contract.get(field)):
            # These three are required for execution safety; the others can warn.
            if field in {"translated_engineering_scope", "acceptance_checks", "must_not_infer"}:
                blocking.append(f"{field} is empty")
            else:
                warnings.append(f"{field} is empty")

    uncertainties = as_list(contract.get("uncertainties"))
    if uncertainties:
        warnings.append("uncertainties are present; task should not be treated as clean FAST_LANE")
        questions.extend(str(x) for x in uncertainties if str(x).strip())

    text = lower_join(contract) + " " + human_card.lower()
    hard_hits = keyword_hits(text, HARD_STOP_KEYWORDS)
    review_hits = keyword_hits(text, REVIEW_KEYWORDS)
    if not uncertainties and "uncertain" in review_hits:
        review_hits.remove("uncertain")

    if hard_hits:
        blocking.append("hard-stop domain detected: " + ", ".join(hard_hits))

    if review_hits:
        warnings.append("review-risk terms detected: " + ", ".join(review_hits))

    acceptance_checks = as_list(contract.get("acceptance_checks"))
    if acceptance_checks and not any("check" in str(x).lower() or "test" in str(x).lower() or "verify" in str(x).lower() or "run" in str(x).lower() for x in acceptance_checks):
        warnings.append("acceptance_checks may be descriptive rather than mechanically verifiable")

    if blocking:
        verdict = "BLOCK"
        execution_blocked = True
        recommended_lane = "HARD_STOP_LANE"
    elif warnings:
        verdict = "WARN"
        execution_blocked = False
        recommended_lane = "REVIEW_QUEUE_LANE"
    else:
        verdict = "PASS"
        execution_blocked = False
        recommended_lane = "FAST_LANE"

    review = f"""# Contract Red Team Review

## Task ID

{task_id}

## Verdict

{verdict}

## Plain-language contract summary

Human intent: {contract.get('human_intent', '')}

Deterministic intent: {contract.get('deterministic_intent', '')}

Engineering scope:
{chr(10).join('- ' + str(x) for x in as_list(contract.get('translated_engineering_scope'))) or '- NONE'}

## Ambiguity risks

{chr(10).join('- ' + x for x in warnings) or '- No ambiguity warnings detected by mechanical review.'}

## Execution risks

{chr(10).join('- ' + x for x in blocking) or '- No blocking execution risks detected by mechanical review.'}

## False-pass risks

- Acceptance checks must prove behavior, not merely file existence.
- Codex must not treat natural-language success claims as evidence.
- Final closure still requires checks, reconcile, and human approval.

## Questions for human

{chr(10).join('- ' + x for x in questions) or '- No explicit unresolved questions detected.'}

## Recommendation

Recommended lane: `{recommended_lane}`

Execution blocked by red-team layer: `{str(execution_blocked).lower()}`
"""

    receipt = {
        "task_id": task_id,
        "verdict": verdict,
        "execution_blocked": execution_blocked,
        "recommended_lane": recommended_lane,
        "blocking_issues": blocking,
        "warnings": warnings,
        "questions_for_human": questions,
        "reviewed_inputs": [CONTRACT_PATH, "runtime/human_intent_card.md"],
        "generated_review": REVIEW_PATH,
    }

    write_text(REVIEW_PATH, review)
    write_json(RECEIPT_PATH, receipt)
    print("JOYFLOW_CONTRACT_RED_TEAM_" + verdict)
    return 1 if verdict == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
