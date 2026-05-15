#!/usr/bin/env python3
"""Render runtime/codex_task_packet.md and runtime/codex_launch_manifest.json."""
from __future__ import annotations

from joyflow_common import canonical_json_hash, read_json, read_text, write_json, write_text

BRIDGE_PATH = "runtime/execution_bridge_package.json"
CONTEXT_PATH = "runtime/context_palace.md"
PACKET_PATH = "runtime/codex_task_packet.md"
MANIFEST_PATH = "runtime/codex_launch_manifest.json"


def bullets(values):
    if isinstance(values, list) and values:
        return "\n".join(f"- {v}" for v in values)
    if isinstance(values, str) and values.strip():
        return f"- {values}"
    return "- NONE"


def main() -> int:
    bridge = read_json(BRIDGE_PATH, default={})
    context = read_text(CONTEXT_PATH)
    bridge_hash = canonical_json_hash(bridge)
    identity = bridge.get("task_identity", {}) if isinstance(bridge.get("task_identity"), dict) else {}
    execution_allowed = bool(bridge.get("execution_allowed"))
    target_lane = bridge.get("target_lane", "")

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

## 4. Source bridge

`{BRIDGE_PATH}`

## 5. Context palace

`{CONTEXT_PATH}`
"""
    else:
        packet = f"""# Joyflow Codex Task Packet

BRIDGE_HASH: {bridge_hash}

## 1. Identity

You are Codex executor, not Joyflow Brain.

Task ID: `{identity.get('task_id', '')}`

Task title: {identity.get('task_title', '')}

Target lane: `{target_lane}`

## 2. Authority order

1. `AGENTS.md`
2. `.codex/rules.md`
3. `runtime/execution_bridge_package.json`
4. `runtime/context_palace.md`
5. this packet
6. referenced skill docs

The bridge is the only formal execution carrier.

## 3. Task boundary

Execute only the task described by the bridge.

Do not reinterpret raw human intent.

Do not expand scope.

## 4. Allowed paths

{bullets(bridge.get('allowed_paths', []))}

## 5. Forbidden actions

{bullets(bridge.get('forbidden', []))}

## 6. Non-negotiables

{bullets(bridge.get('non_negotiables', []))}

## 7. Required inputs

{bullets(bridge.get('required_inputs', []))}

## 8. Required outputs

{bullets(bridge.get('required_output_files', []))}

## 9. Acceptance command

Run before reporting completion:

```bash
{bridge.get('acceptance_command', 'bash tests/run_checks.sh')}
```

## 10. Acceptance boundary

{bullets(bridge.get('acceptance_boundary', []))}

## 11. Context palace excerpt

{context}

## 12. Evidence return format

Return exactly:

```text
execution_summary:
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
        "context_palace_source": CONTEXT_PATH,
        "packet_source": PACKET_PATH,
        "packet_generated_by": "scripts/build_codex_packet.py",
    }
    write_text(PACKET_PATH, packet)
    write_json(MANIFEST_PATH, manifest)
    print("JOYFLOW_CODEX_PACKET_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
