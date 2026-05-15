#!/usr/bin/env python3
"""Render runtime/context_palace.md from the current execution bridge."""
from __future__ import annotations

from typing import Any, List

from joyflow_common import read_json, write_text

BRIDGE_PATH = "runtime/execution_bridge_package.json"
CONTEXT_PATH = "runtime/context_palace.md"


def bullets(values: Any) -> str:
    if isinstance(values, list) and values:
        return "\n".join(f"- {v}" for v in values)
    if isinstance(values, str) and values.strip():
        return f"- {values}"
    return "- NONE"


def main() -> int:
    bridge = read_json(BRIDGE_PATH, default={})
    identity = bridge.get("task_identity", {}) if isinstance(bridge.get("task_identity"), dict) else {}

    text = f"""# Context Palace

## 1. Project identity

Joyflow Phase 1 Operational Skeleton.

## 2. Current room

Task ID: `{identity.get('task_id', '')}`

Task title: {identity.get('task_title', '')}

Target lane: `{bridge.get('target_lane', '')}`

Execution allowed: `{str(bridge.get('execution_allowed', False)).lower()}`

Blocked reason: {bridge.get('blocked_reason', '') or 'NONE'}

## 3. Fixed invariants

- Bridge is the only formal execution carrier.
- Context palace is navigation only.
- Codex must not reinterpret raw human intent.
- Codex must not modify outside allowed paths.
- Codex must not execute HARD_STOP tasks.
- Human closure is still required after checks and reconcile.

## 4. Allowed objects

{bullets(bridge.get('allowed_paths', []))}

## 5. Forbidden doors

{bullets(bridge.get('forbidden', []))}

## 6. Local map

{bullets(bridge.get('local_graph_subtree', []))}

## 7. Required inputs

{bullets(bridge.get('required_inputs', []))}

## 8. Acceptance exit

Acceptance command:

```bash
{bridge.get('acceptance_command', 'bash tests/run_checks.sh')}
```

Acceptance boundary:

{bullets(bridge.get('acceptance_boundary', []))}

## 9. Human observation target

{bullets(bridge.get('human_observation_points', []))}

## 10. Red-team status

Contract red-team receipt: `{bridge.get('contract_red_team_ref', 'observer/contract_red_team_receipt.json')}`

## 11. Authority note

If this file conflicts with `runtime/execution_bridge_package.json`, the bridge wins.
"""
    write_text(CONTEXT_PATH, text)
    print("JOYFLOW_CONTEXT_PALACE_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
