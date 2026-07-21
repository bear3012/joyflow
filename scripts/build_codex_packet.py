#!/usr/bin/env python3
"""Render one complete Codex execution prompt and its full input manifest."""
from __future__ import annotations

from typing import Any, Dict, List

from joyflow_common import canonical_json_hash, file_hash, read_json, read_text, write_json, write_text
from validate_semantic_closure import effective_interpretation

BRIDGE_PATH = "runtime/execution_bridge_package.json"
CONTEXT_PATH = "runtime/context_palace.md"
MEANING_PATH = "runtime/product_meaning_closure.json"
CONTRACT_PATH = "runtime/translation_contract.json"
DELTA_PATH = "runtime/meaning_delta.json"
GOLDEN_PATH = "runtime/golden_cases.json"
ACCEPTANCE_PATH = "runtime/user_acceptance_plan.json"
INTERPRETATION_PATH = "runtime/codex_execution_interpretation.json"
RED_TEAM_PATH = "observer/contract_red_team_receipt.json"
PACKET_PATH = "runtime/codex_task_packet.md"
MANIFEST_PATH = "runtime/codex_launch_manifest.json"

MANIFEST_INPUT_PATHS = [
    MEANING_PATH,
    CONTRACT_PATH,
    DELTA_PATH,
    GOLDEN_PATH,
    ACCEPTANCE_PATH,
    INTERPRETATION_PATH,
    RED_TEAM_PATH,
    BRIDGE_PATH,
    CONTEXT_PATH,
]


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
    lines: List[str] = []
    for case in cases if isinstance(cases, list) else []:
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
    lines: List[str] = []
    for step in steps if isinstance(steps, list) else []:
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
    input_hashes = {path: file_hash(path) for path in MANIFEST_INPUT_PATHS}
    input_bundle_hash = canonical_json_hash(input_hashes)
    identity = bridge.get("task_identity", {}) if isinstance(bridge.get("task_identity"), dict) else {}
    execution_allowed = bool(bridge.get("execution_allowed"))
    target_lane = bridge.get("target_lane", "")
    semantic = contract.get("human_semantic_layer", {}) if isinstance(contract.get("human_semantic_layer"), dict) else {}
    mechanical = contract.get("mechanical_execution_layer", {}) if isinstance(contract.get("mechanical_execution_layer"), dict) else {}
    walkthrough = meaning.get("product_walkthrough", {}) if isinstance(meaning.get("product_walkthrough"), dict) else {}

    header = f"""# Joyflow Codex Task Packet

BRIDGE_HASH: {bridge_hash}
INPUT_BUNDLE_HASH: {input_bundle_hash}

This is the one complete transfer block. Do not ask the human to assemble additional instruction fragments.
"""

    if not execution_allowed:
        packet = header + f"""
## Status

HALT

Lifecycle mode: `{bridge.get('lifecycle_mode', '')}`
Target lane: `{target_lane}`
Reason: {bridge.get('blocked_reason') or 'execution_allowed=false'}

Do not modify repository files, commit, push, open a PR, or write Brain/human approval artifacts.
Return halt evidence only. A reference candidate is intentionally non-executable until a real ACTIVE_TASK contract and authentic reviewed Codex interpretation replace the fixture.

Original problem:
{meaning.get('original_user_problem', '') or 'UNAVAILABLE'}
"""
    else:
        packet = header + f"""
## Identity

You are the bounded local Codex executor, not Joyflow Brain or product owner.
Task ID: `{identity.get('task_id', '')}`
Task title: {identity.get('task_title', '')}
Target lane: `{target_lane}`

## Authority and product meaning

Original user problem:
{meaning.get('original_user_problem', '')}

Entry: {walkthrough.get('entry', '')}
Success: {walkthrough.get('success_result', '')}
Failure: {walkthrough.get('failure_result', '')}

User flow:
{bullets(semantic.get('user_flow', []))}

Business rules:
{bullets(semantic.get('business_rules', []))}

Non-goals:
{bullets(semantic.get('non_goals', []))}

Correct examples:
{bullets(semantic.get('correct_examples', []))}

Incorrect examples:
{bullets(semantic.get('incorrect_examples', []))}

## Mechanical boundary

Must preserve:
{bullets(mechanical.get('must_preserve', []))}

Allowed solution surfaces:
{bullets(mechanical.get('allowed_solution_surfaces', []))}

Forbidden consequences:
{bullets(mechanical.get('forbidden_consequences', []))}

Allowed technical freedom:
{bullets(mechanical.get('allowed_technical_freedom', []))}

Stop conditions:
{bullets(mechanical.get('stop_conditions', []))}

## Reviewed execution interpretation

Source: `{interpretation_source}`
Status: `{interpretation.get('interpretation_status', '')}`
Objective understood: {interpretation.get('objective_understood', '')}
User-visible result: {interpretation.get('user_visible_result', '')}
Intended solution surface:
{bullets(interpretation.get('intended_solution_surface', []))}
Excluded changes:
{bullets(interpretation.get('excluded_changes', []))}
Unresolved items:
{bullets(interpretation.get('unresolved_items', []))}

If your current understanding differs, stop before mutation and return the difference to Brain.

## Golden Cases

{golden_case_lines(golden)}

## User acceptance fixed before implementation

{acceptance_lines(acceptance)}

## Deviation routing

- `AUTO_ACCEPTABLE_TECHNICAL_VARIATION`: equivalent implementation only, with no product, flow, data, risk, maintenance, tradeoff, or acceptance change.
- `BRAIN_REVIEW_REQUIRED`: stop for expanded surface, shared state, interfaces, maintenance impact, unexpected consequences, or insufficient boundary.
- `USER_DECISION_REQUIRED`: stop for product rule, user flow, data meaning, feature, important experience, material risk, or tradeoff change.

## Allowed writes

Source paths:
{bullets(bridge.get('allowed_paths', []))}

Executor outputs:
{bullets(bridge.get('executor_writable_outputs', []))}

Never write these Brain-only outputs:
{bullets(bridge.get('brain_only_outputs', []))}

Never write these human-only outputs:
{bullets(bridge.get('human_only_outputs', []))}

## Required check

```bash
{bridge.get('acceptance_command', 'bash tests/run_checks.sh')}
```

## Evidence return

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
"""

    manifest = {
        "artifact_type": "CODEX_LAUNCH_MANIFEST",
        "artifact_version": "2",
        "task_id": identity.get("task_id", ""),
        "lifecycle_mode": bridge.get("lifecycle_mode"),
        "bridge_source": BRIDGE_PATH,
        "bridge_hash": bridge_hash,
        "input_hashes": input_hashes,
        "input_bundle_hash": input_bundle_hash,
        "effective_interpretation_source": interpretation_source,
        "context_palace_source": CONTEXT_PATH,
        "packet_source": PACKET_PATH,
        "packet_generated_by": "scripts/build_codex_packet.py",
        "single_complete_prompt": True,
        "execution_allowed": execution_allowed,
    }
    write_text(PACKET_PATH, packet)
    write_json(MANIFEST_PATH, manifest)
    print("JOYFLOW_CODEX_PACKET_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
