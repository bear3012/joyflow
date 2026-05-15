# Node Cards

## H0_RAW_HUMAN_INTENT

Human states raw desire. No execution is allowed.

## H1_ASSOCIATIVE_DISCUSSION

Brain expands possible meanings, hidden assumptions, risks, counterexamples, and likely failure modes.

## H2_INTENT_CALIBRATION

Human marks which interpretations are correct, incorrect, deferred, or risky.

## H3_DETERMINISTIC_INTENT

Brain freezes deterministic intent, non-goals, forbidden outcomes, success criteria, and human observation points.

## H4_TRANSLATION_CONTRACT

Brain writes `runtime/translation_contract.json`.

## R0_CONTRACT_RED_TEAM_REVIEW

Mechanical or Brain-assisted pre-execution review checks whether the translation contract is ambiguous, unsafe, under-specified, or likely to produce false passing evidence.

Allowed writes:

```text
runtime/contract_red_team_review.md
observer/contract_red_team_receipt.json
```

Forbidden:

1. writing subject objects;
2. executing code;
3. approving closure;
4. creating alternate execution carriers.

## N1_ROUTE_TASK

`scripts/route_task.py` assigns FAST_LANE, REVIEW_QUEUE_LANE, or HARD_STOP_LANE.

## N2_PREFLIGHT_RECORD

System records preflight state. Phase 1 may use explicitly labeled placeholder fingerprints.

## N3_BUILD_BRIDGE

`scripts/build_bridge.py` builds `runtime/execution_bridge_package.json`, the only formal execution carrier.

## N4_BUILD_CONTEXT_PALACE

`scripts/build_context_palace.py` builds task-specific navigation context from the bridge.

## N5_BUILD_CODEX_PACKET

`scripts/build_codex_packet.py` renders `runtime/codex_task_packet.md` and `runtime/codex_launch_manifest.json`.

## N6_HUMAN_HANDOVER_TO_CODEX_APP

Human explicitly transfers the packet to Codex App.

## N7_CODEX_APP_EXECUTION

Codex executes only the bounded task and only within allowed paths.

## N8_RUN_CHECKS

Codex or human runs `bash tests/run_checks.sh`.

## N9_RETURN_EVIDENCE_TO_BRAIN

Human returns evidence to Brain.

## N10_HUMAN_REVIEW_PACKET

Brain or script translates evidence into human-native review.

## N11_RECONCILE

`scripts/reconcile.py` decides machine closure readiness only.

## N12_HUMAN_CLOSE_OR_REJECT

Human approves close, rejects, or escalates.
