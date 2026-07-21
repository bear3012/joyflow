#!/usr/bin/env bash
set -euo pipefail
python scripts/build_codex_interpretation_request.py
python scripts/route_task.py
python scripts/build_bridge.py
python scripts/build_context_palace.py
python scripts/build_codex_packet.py
printf '%s\n' "JOYFLOW_RUNTIME_REFRESHED"
