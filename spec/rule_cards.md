# Rule Cards

## R1. Brain-first

Raw human intent cannot be executed directly.

## R2. Contract red-team gate

`runtime/translation_contract.json` must be reviewed before routing. The review writes:

```text
runtime/contract_red_team_review.md
observer/contract_red_team_receipt.json
```

If the receipt verdict is `BLOCK`, execution must remain blocked.

## R3. Lane freeze

Allowed lanes are:

```text
FAST_LANE
REVIEW_QUEUE_LANE
HARD_STOP_LANE
```

Unclear tasks default to REVIEW_QUEUE_LANE. High-risk tasks route to HARD_STOP_LANE.

## R4. Single execution carrier

The only formal execution carrier is:

```text
runtime/execution_bridge_package.json
```

## R5. Context palace boundary

`runtime/context_palace.md` is navigation only and cannot override the bridge.

## R6. Codex boundary

Codex may modify only files listed in bridge `allowed_paths`.

Codex must not execute if `execution_allowed=false` or `target_lane=HARD_STOP_LANE`.

## R7. Evidence-first

Completion requires mechanical evidence, not AI explanation.

## R8. Reconcile authority

`scripts/reconcile.py` is the only machine writer of `closure_ready`.

Human approval is still required after reconcile.

## R9. Subject freeze

`subject/task_state.json` must keep exactly five fields:

```text
task_id
task_status
target_lane
graph_sync_required
formal_pending
```
