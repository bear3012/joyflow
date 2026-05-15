# Context Palace

## 1. Project identity

Joyflow Phase 1 Operational Skeleton.

## 2. Current room

Task ID: `JF-dc0ea150aba0`

Task title: Create or verify a short Phase 1 usage note for Joyflow baseline validation.

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

- docs/phase1_usage.md

## 5. Forbidden doors

- Do not modify implementation logic
- Do not modify data definitions
- Do not modify operational routing rules

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

- Verify docs/phase1_usage.md exists
- Verify docs/phase1_usage.md mentions Phase 1
- Verify docs/phase1_usage.md mentions baseline validation

## 9. Human observation target

- Confirm the usage note is limited to Phase 1 baseline validation

## 10. Red-team status

Contract red-team receipt: `observer/contract_red_team_receipt.json`

## 11. Authority note

If this file conflicts with `runtime/execution_bridge_package.json`, the bridge wins.
