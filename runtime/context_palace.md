# Context Palace

## 1. Project identity

Joyflow Phase 1 Operational Skeleton.

## 2. Current room

Task ID: `JF-eb94ba89536f`

Task title: Apply Codex governance rules to AGENTS.md.

Target lane: `REVIEW_QUEUE_LANE`

Execution allowed: `true`

Blocked reason: NONE

## 3. Fixed invariants

- Bridge is the only formal execution carrier.
- Context palace is navigation only.
- Codex must not reinterpret raw human intent.
- Codex must not modify outside allowed paths.
- Codex must not execute HARD_STOP tasks.
- Human closure is still required after checks and reconcile.

## 4. Allowed objects

- AGENTS.md

## 5. Forbidden doors

- NONE

## 6. Local map

- H4_TRANSLATION_CONTRACT
- R0_CONTRACT_RED_TEAM_REVIEW
- N1_ROUTE_TASK
- N3_BUILD_BRIDGE
- N4_BUILD_CONTEXT_PALACE
- N5_BUILD_CODEX_PACKET
- N6_HUMAN_HANDOVER_TO_CODEX_APP
- N8_RUN_CHECKS
- N11_RECONCILE

## 7. Required inputs

- runtime/translation_contract.json
- runtime/routing_result.json
- observer/contract_red_team_receipt.json
- AGENTS.md

## 8. Acceptance exit

Acceptance command:

```bash
bash tests/run_checks.sh
```

Acceptance boundary:

- AGENTS.md exists
- AGENTS.md contains Joyflow Codex Rules
- AGENTS.md says Codex is not Joyflow Brain
- AGENTS.md says Codex must not infer missing business logic
- AGENTS.md says Codex must obey allowed_paths
- AGENTS.md says Codex must halt when execution_allowed=false
- AGENTS.md says Codex must not execute HARD_STOP_LANE
- AGENTS.md contains Protected Subject Core
- AGENTS.md requires bash tests/run_checks.sh
- AGENTS.md requires evidence return format

## 9. Human observation target

- NONE

## 10. Red-team status

Contract red-team receipt: `observer/contract_red_team_receipt.json`

## 11. Authority note

If this file conflicts with `runtime/execution_bridge_package.json`, the bridge wins.
