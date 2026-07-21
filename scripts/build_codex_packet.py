#!/usr/bin/env python3
"""Render one complete Codex execution prompt and launch manifest."""
from __future__ import annotations

from typing import Any, Dict, List

from joyflow_common import canonical_json_hash, read_json, read_text, write_json, write_text
from validate_semantic_closure import effective_interpretation

BRIDGE_PATH = "runtime/execution_bridge_package.json"
CONTEXT_PATH = "runtime/context_palace.md"
MEANING_PATH = "runtime/product_meaning_closure.json"
CONTRACT_PATH = "runtime/translation_contract.json"
GOLDEN_PATH = "runtime/golden_cases.json"
ACCEPTANCE_PATH = "runtime/user_acceptance_plan.json"
INTERPRETATION_PATH = "runtime/codex_execution_interpretation.json"
PACKET_PATH = "runtime/codex_task_packet.md"
MANIFEST_PATH = "runtime/codex_launch_manifest.json"


def bullets(values: Any) -> str:
    if isinstance(values, list) and values:
        rendered: List[str] = []
        for value in values:
            if isinstance(value, dict):
                rendered.append("- " + "; ".join(f"{key}={item}" for key, item in value.items()))
            else:
                rendered.append(f"- {value}")
        return "\n".join(rendered)
    if isinstance(values, str) and values.strip():
        return f"- {values}"
    return "- NONE"


def golden_case_lines(value: Dict[str, Any]) -> str:
    cases = value.get("cases", []) if isinstance(value, dict) else []
    if not isinstance(cases, list) or not cases:
        return "- NONE"
    lines: List[str] = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        lines.append(
            "- {case_id}: initial={initial}; action={action}; expected={expected}; preserve={preserve}; forbidden={forbidden}".format(
                case_id=case.get("case_id", ""),
                initial=case.get("initial_state", {}),
                action=case.get("action", ""),
                expected=case.get("expected_user_visible_result", ""),
                preserve=case.get("preserved_state", ""),
                forbidden=case.get("forbidden_result", ""),
            )
        )
    return "\n".join(lines) or "- NONE"


def acceptance_lines(value: Dict[str, Any]) -> str:
    steps = value.get("steps", []) if isinstance(value, dict) else []
    if not isinstance(steps, list) or not steps:
        return "- NONE"
    lines: List[str] = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        lines.append(
            "- {acceptance_id}: step={step}; expected={expected}; validates={validates}; failure={failure}".format(
                acceptance_id=step.get("acceptance_id", ""),
                step=step.get("step", ""),
                expected=step.get("expected", ""),
                validates=step.get("validates", ""),
                failure=step.get("failure_meaning", ""),
            )
        )
    return "\n".join(lines) or "- NONE"


def main() -> int:
    bridge = read_json(BRIDGE_PATH, default={})
    context = read_text(CONTEXT_PATH)
    meaning = read_json(MEANING_PATH, default={})
    contract = read_json(CONTRACT_PATH, default={})
    golden = read_json(GOLDEN_PATH, default={})
    acceptance = read_json(ACCEPTANCE_PATH, default={})
    external_interpretation = read_json(INTERPRETATION_PATH, default={})
    interpretation, interpretation_source = effective_interpretation(contract, external_interpretation)

    bridge_hash = canonical_json_hash(bridge)
    identity = bridge.get("task_identity", {}) if isinstance(bridge.get("task_identity"), dict) else {}
    execution_allowed = bool(bridge.get("execution_allowed"))
    target_lane = bridge.get("target_lane", "")
    semantic = contract.get("human_semantic_layer", {}) if isinstance(contract.get("human_semantic_layer"), dict) else {}
    mechanical = contract.get("mechanical_execution_layer", {}) if isinstance(contract.get("mechanical_execution_layer"), dict) else {}
    walkthrough = meaning.get("product_walkthrough", {}) if isinstance(meaning.get("product_walkthrough"), dict) else {}

    if not execution_allowed:
        packet = f"""# Joyflow Codex Task Packet

BRIDGE_HASH: {bridge_hash}

## 1. Status

HALT

## 2. Halt reason

{bridge.get('blocked_reason') or 'execution_allowed=false'}

## 3. Instruction to Codex

Do not modify files.
Do not run implementation steps.
Return halt evidence only.
If the reason is interpretation uncertainty or invalid LEAN eligibility, use the separate interpretation request and return a `CODEX_EXECUTION_INTERPRETATION` artifact to Brain.

## 4. Original problem

{meaning.get('original_user_problem', '') or 'UNAVAILABLE'}

## 5. Product meaning source

`{MEANING_PATH}`

## 6. Source bridge

`{BRIDGE_PATH}`

## 7. Context palace

`{CONTEXT_PATH}`
"""
    else:
        packet = f"""# Joyflow Codex Task Packet

BRIDGE_HASH: {bridge_hash}

This is the one complete execution prompt. Do not require the human to assemble extra instruction fragments.

## 1. Identity

You are Codex executor, not Joyflow Brain or product owner.

Task ID: `{identity.get('task_id', '')}`

Task title: {identity.get('task_title', '')}

Target lane: `{target_lane}`

## 2. Authority order

1. `AGENTS.md`
2. `.codex/rules.md`
3. `runtime/product_meaning_closure.json`
4. `runtime/translation_contract.json`
5. effective interpretation source shown in section 7
6. `runtime/execution_bridge_package.json`
7. `runtime/context_palace.md`
8. this packet
9. referenced skill docs

The bridge is the only formal mutation carrier. Product meaning and contract constrain the bridge; they do not create unbounded mutation authority.

## 3. Original user problem

{meaning.get('original_user_problem', '')}

## 4. Confirmed product walkthrough

Entry: {walkthrough.get('entry', '')}

User actions:
{bullets(walkthrough.get('user_action_sequence', []))}

System responses:
{bullets(walkthrough.get('system_response_sequence', []))}

Success: {walkthrough.get('success_result', '')}

Failure: {walkthrough.get('failure_result', '')}

Preserve:
{bullets(walkthrough.get('preserved_behavior', []))}

Explicitly absent:
{bullets(walkthrough.get('explicitly_absent_behavior', []))}

## 5. Human semantic layer

Objective: {semantic.get('objective', '')}

Expected user result: {semantic.get('expected_user_result', '')}

User flow:
{bullets(semantic.get('user_flow', []))}

Business rules:
{bullets(semantic.get('business_rules', []))}

Accepted tradeoffs:
{bullets(semantic.get('accepted_tradeoffs', []))}

Non-goals:
{bullets(semantic.get('non_goals', []))}

Correct examples:
{bullets(semantic.get('correct_examples', []))}

Incorrect examples:
{bullets(semantic.get('incorrect_examples', []))}

## 6. Mechanical execution layer

Must preserve:
{bullets(mechanical.get('must_preserve', []))}

Allowed solution surfaces:
{bullets(mechanical.get('allowed_solution_surfaces', []))}

Forbidden consequences:
{bullets(mechanical.get('forbidden_consequences', []))}

Required outcomes:
{bullets(mechanical.get('required_outcomes', []))}

Allowed technical freedom:
{bullets(mechanical.get('allowed_technical_freedom', []))}

Stop conditions:
{bullets(mechanical.get('stop_conditions', []))}

Evidence requirements:
{bullets(mechanical.get('evidence_requirements', []))}

## 7. Effective execution interpretation

Source: `{interpretation_source}`

Status: `{interpretation.get('interpretation_status', '')}`

Objective understood: {interpretation.get('objective_understood', '')}

User-visible result: {interpretation.get('user_visible_result', '')}

User flow understood:
{bullets(interpretation.get('user_flow_understood', []))}

Must preserve:
{bullets(interpretation.get('must_preserve', []))}

Intended solution surface:
{bullets(interpretation.get('intended_solution_surface', []))}

Excluded changes:
{bullets(interpretation.get('excluded_changes', []))}

Golden Cases understood:
{bullets(interpretation.get('golden_cases_understood', []))}

Unresolved items:
{bullets(interpretation.get('unresolved_items', []))}

If your actual implementation understanding differs from this interpretation, stop before modifying files and return the difference to Brain. For a LEAN task, execution itself confirms the embedded interpretation; disagreement cancels LEAN immediately.

## 8. Golden Cases

{golden_case_lines(golden)}

Use the same case IDs in tests and evidence. Do not silently rewrite their meaning.

## 9. User acceptance plan fixed at contract time

{acceptance_lines(acceptance)}

Implementation and evidence must support these same acceptance steps. Do not invent a weaker post-hoc acceptance standard.

## 10. Deviation routing

You may proceed and report an `AUTO_ACCEPTABLE_TECHNICAL_VARIATION` only for an equivalent implementation inside the approved boundary with no product, flow, data-meaning, risk, maintenance, or acceptance change.

Stop and return `BRAIN_REVIEW_REQUIRED` if the solution surface expands, shared state or interfaces change, maintenance cost materially increases, an unexpected technical consequence appears, or the approved boundary is insufficient.

Stop and return `USER_DECISION_REQUIRED` if a product rule, user flow, data meaning, feature set, important experience, material risk, or accepted tradeoff would change.

## 11. Allowed paths

{bullets(bridge.get('allowed_paths', []))}

## 12. Forbidden actions

{bullets(bridge.get('forbidden', []))}

## 13. Non-negotiables

{bullets(bridge.get('non_negotiables', []))}

## 14. Required inputs

{bullets(bridge.get('required_inputs', []))}

## 15. Required outputs

{bullets(bridge.get('required_output_files', []))}

## 16. Acceptance command

Run before reporting completion:

```bash
{bridge.get('acceptance_command', 'bash tests/run_checks.sh')}
```

## 17. Acceptance boundary

{bullets(bridge.get('acceptance_boundary', []))}

## 18. Context palace excerpt

{context}

## 19. Evidence return format

Return exactly:

```text
execution_summary:
original_problem_result:
confirmed_interpretation_ref:
golden_case_results:
deviation_classification:
deviation_details:
touched_files:
branch_name:
pr_url:
check_command:
check_exit_code:
observer_outputs:
reconcile_output:
human_review_packet_summary:
unresolved_items:
halt_reason:
```

If not halted, `halt_reason` must be `NONE`.
"""

    manifest = {
        "bridge_source": BRIDGE_PATH,
        "bridge_hash": bridge_hash,
        "product_meaning_source": MEANING_PATH,
        "translation_contract_source": CONTRACT_PATH,
        "golden_cases_source": GOLDEN_PATH,
        "user_acceptance_plan_source": ACCEPTANCE_PATH,
        "codex_interpretation_source": INTERPRETATION_PATH,
        "effective_interpretation_source": interpretation_source,
        "context_palace_source": CONTEXT_PATH,
        "packet_source": PACKET_PATH,
        "packet_generated_by": "scripts/build_codex_packet.py",
        "single_complete_prompt": True,
    }
    write_text(PACKET_PATH, packet)
    write_json(MANIFEST_PATH, manifest)
    print("JOYFLOW_CODEX_PACKET_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
