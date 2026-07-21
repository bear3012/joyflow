#!/usr/bin/env python3
"""Render non-authoritative task navigation context from the execution bridge."""
from __future__ import annotations

from typing import Any, List

from joyflow_common import read_json, write_text

BRIDGE_PATH = "runtime/execution_bridge_package.json"
MEANING_PATH = "runtime/product_meaning_closure.json"
INTERPRETATION_PATH = "runtime/codex_execution_interpretation.json"
CONTEXT_PATH = "runtime/context_palace.md"


def bullets(values: Any) -> str:
    if isinstance(values, list) and values:
        return "\n".join(f"- {value}" for value in values)
    if isinstance(values, str) and values.strip():
        return f"- {values}"
    return "- NONE"


def main() -> int:
    bridge = read_json(BRIDGE_PATH, default={})
    meaning = read_json(MEANING_PATH, default={})
    interpretation = read_json(INTERPRETATION_PATH, default={})
    identity = bridge.get("task_identity", {}) if isinstance(bridge.get("task_identity"), dict) else {}
    walkthrough = meaning.get("product_walkthrough", {}) if isinstance(meaning.get("product_walkthrough"), dict) else {}

    text = f"""# Context Palace

## 1. Project identity

Joyflow Phase 1 Operational Skeleton with semantic-closure candidate rules.

## 2. Current room

Task ID: `{identity.get('task_id', '')}`

Task title: {identity.get('task_title', '')}

Target lane: `{bridge.get('target_lane', '')}`

Execution allowed: `{str(bridge.get('execution_allowed', False)).lower()}`

Blocked reason: {bridge.get('blocked_reason', '') or 'NONE'}

## 3. Original problem

{meaning.get('original_user_problem', '')}

## 4. User-visible result

{bridge.get('product_result', '')}

## 5. Product walkthrough

Entry: {walkthrough.get('entry', '')}

User actions:
{bullets(walkthrough.get('user_action_sequence', []))}

System responses:
{bullets(walkthrough.get('system_response_sequence', []))}

Success: {walkthrough.get('success_result', '')}

Failure: {walkthrough.get('failure_result', '')}

## 6. Fixed invariants

- Product meaning must be confirmed before execution.
- Material ambiguity cannot be delegated to Codex.
- Bridge is the only formal mutation carrier.
- Context palace is navigation only.
- Codex must not reinterpret raw human intent.
- Codex must not modify outside allowed paths.
- Human closure is required after machine checks, Brain semantic review, and user acceptance.

Must preserve:
{bullets(bridge.get('must_preserve', []))}

## 7. Confirmed interpretation

Status: `{interpretation.get('interpretation_status', '')}`

Objective: {interpretation.get('objective_understood', '')}

Intended solution surface:
{bullets(interpretation.get('intended_solution_surface', []))}

Excluded changes:
{bullets(interpretation.get('excluded_changes', []))}

## 8. Allowed objects

{bullets(bridge.get('allowed_paths', []))}

## 9. Forbidden doors

{bullets(bridge.get('forbidden', []))}

## 10. Golden Cases

{bullets(bridge.get('golden_case_refs', []))}

## 11. Deviation default

`{bridge.get('deviation_default', '')}`

Equivalent technical variation may proceed only inside the approved product result and mechanical boundary. Product changes return to the human.

## 12. Local map

{bullets(bridge.get('local_graph_subtree', []))}

## 13. Required inputs

{bullets(bridge.get('required_inputs', []))}

## 14. Acceptance exit

Acceptance command:

```bash
{bridge.get('acceptance_command', 'bash tests/run_checks.sh')}
```

Acceptance boundary:

{bullets(bridge.get('acceptance_boundary', []))}

Predefined human observation target:

{bullets(bridge.get('human_observation_points', []))}

## 15. Red-team status

Contract red-team receipt: `{bridge.get('contract_red_team_ref', 'observer/contract_red_team_receipt.json')}`

## 16. Authority note

If this file conflicts with product meaning, contract, interpretation, or `runtime/execution_bridge_package.json`, it cannot override them. Stop and return the conflict to Brain.
"""
    write_text(CONTEXT_PATH, text)
    print("JOYFLOW_CONTEXT_PALACE_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
