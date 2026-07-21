#!/usr/bin/env python3
"""Render non-authoritative navigation context from the current bridge."""
from __future__ import annotations

from typing import Any

from joyflow_common import read_json, write_text
from validate_semantic_closure import effective_interpretation


def bullets(values: Any) -> str:
    if isinstance(values, list) and values:
        return "\n".join(f"- {value}" for value in values)
    if isinstance(values, str) and values.strip():
        return f"- {values}"
    return "- NONE"


def main() -> int:
    bridge = read_json("runtime/execution_bridge_package.json", default={})
    meaning = read_json("runtime/product_meaning_closure.json", default={})
    contract = read_json("runtime/translation_contract.json", default={})
    external = read_json("runtime/codex_execution_interpretation.json", default={})
    interpretation, source = effective_interpretation(contract, external)
    identity = bridge.get("task_identity", {}) if isinstance(bridge.get("task_identity"), dict) else {}
    walkthrough = meaning.get("product_walkthrough", {}) if isinstance(meaning.get("product_walkthrough"), dict) else {}

    text = f"""# Context Palace

This file is navigation only. It cannot override product meaning, contract, reviewed interpretation, or Bridge.

## Current identity

Task ID: `{identity.get('task_id', '')}`
Lifecycle mode: `{bridge.get('lifecycle_mode', '')}`
Target lane: `{bridge.get('target_lane', '')}`
Execution allowed: `{str(bridge.get('execution_allowed', False)).lower()}`
Blocked reason: {bridge.get('blocked_reason', '') or 'NONE'}

## Original problem

{meaning.get('original_user_problem', '')}

## Product walkthrough

Entry: {walkthrough.get('entry', '')}
User actions:
{bullets(walkthrough.get('user_action_sequence', []))}
System responses:
{bullets(walkthrough.get('system_response_sequence', []))}
Success: {walkthrough.get('success_result', '')}
Failure: {walkthrough.get('failure_result', '')}

## Effective interpretation

Source: `{source}`
Status: `{interpretation.get('interpretation_status', '')}`
Origin: `{interpretation.get('artifact_origin', '')}`
Not execution evidence: `{str(interpretation.get('not_codex_execution_evidence', False)).lower()}`

## Allowed source paths

{bullets(bridge.get('allowed_paths', []))}

## Executor-writable outputs

{bullets(bridge.get('executor_writable_outputs', []))}

## Brain-only outputs

{bullets(bridge.get('brain_only_outputs', []))}

## Human-only outputs

{bullets(bridge.get('human_only_outputs', []))}

## Golden Cases

{bullets(bridge.get('golden_case_refs', []))}

## Required check

```bash
{bridge.get('acceptance_command', 'bash tests/run_checks.sh')}
```
"""
    write_text("runtime/context_palace.md", text)
    print("JOYFLOW_CONTEXT_PALACE_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
