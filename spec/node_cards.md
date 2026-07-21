# Node Cards

## H0_RAW_HUMAN_INTENT

Human states raw desire. No execution is allowed.

## H1_ASSOCIATIVE_DISCUSSION

Brain explores possible meanings, hidden assumptions, risks, counterexamples, failure modes, and meaningful tradeoffs.

## H2_INTENT_CALIBRATION

Human marks which interpretations are correct, incorrect, deferred, or unacceptable.

## H3_PRODUCT_WALKTHROUGH

Brain reverse-restates the actual product path:

```text
entry
→ user action
→ system response
→ success/failure
→ preserved behavior
→ explicitly absent behavior
```

The human confirms concrete use, not technical design.

## H4_PRODUCT_MEANING_CLOSURE

Brain writes `runtime/product_meaning_closure.json`.

Execution authority requires:

- no material ambiguity;
- confirmed user reference;
- explicit must-have, must-not-have, non-goals, tradeoffs, positive examples, and failure examples.

## H5_DUAL_LAYER_TRANSLATION_CONTRACT

Brain writes `runtime/translation_contract.json` with:

- a human semantic layer for product meaning;
- a mechanical execution layer for boundaries and evidence;
- references to Golden Cases, meaning delta, and user acceptance plan.

## H6_GOLDEN_CASE_AND_USER_ACCEPTANCE_PLAN

Brain writes:

```text
runtime/meaning_delta.json
runtime/golden_cases.json
runtime/user_acceptance_plan.json
```

Golden Case IDs are stable across all downstream stages. User acceptance is defined before implementation.

## R0_CONTRACT_RED_TEAM_REVIEW

Mechanical or Brain-assisted pre-execution review checks ambiguity, false-pass risk, overdesign risk, weak acceptance, and boundary gaps.

Allowed writes:

```text
runtime/contract_red_team_review.md
observer/contract_red_team_receipt.json
```

Forbidden:

1. writing subject objects;
2. executing code;
3. approving closure;
4. creating alternate execution carriers;
5. deciding product meaning for the human.

## N1_ROUTE_TASK

`scripts/route_task.py` assigns FAST_LANE, REVIEW_QUEUE_LANE, or HARD_STOP_LANE. Material ambiguity or non-aligned interpretation cannot produce executable routing.

## N2_PREFLIGHT_RECORD

System records preflight state. Phase 1 may use explicitly labeled placeholder fingerprints.

## N3_BUILD_BRIDGE

`scripts/build_bridge.py` builds `runtime/execution_bridge_package.json`, the only formal mutation carrier. It binds product meaning, contract, meaning delta, Golden Cases, user acceptance plan, Codex interpretation, and Brain review references.

## N4_BUILD_CONTEXT_PALACE

`scripts/build_context_palace.py` builds task-specific navigation context from the bridge. It is non-authoritative.

## N5A_BUILD_CODEX_INTERPRETATION_REQUEST

`scripts/build_codex_interpretation_request.py` renders one short read-only Prompt. It authorizes no file mutation, commit, push, or PR.

## N5B_CODEX_EXECUTION_INTERPRETATION

Codex returns `runtime/codex_execution_interpretation.json` with objective, user-visible result, flow, invariants, intended solution surface, exclusions, Golden Case IDs, unresolved items, and one interpretation status.

## N5C_BRAIN_INTERPRETATION_REVIEW

Brain decides whether Codex interpretation aligns with the confirmed product meaning and contract. Codex does not self-authorize product uncertainty.

## N5_BUILD_CODEX_PACKET

`scripts/build_codex_packet.py` renders `runtime/codex_task_packet.md` and `runtime/codex_launch_manifest.json` as one complete execution Prompt after alignment.

## N6_HUMAN_HANDOVER_TO_CODEX_APP

Human explicitly transfers either the read-only interpretation request or the complete execution Prompt to Codex App.

## N7_CODEX_APP_EXECUTION

Codex executes only the bounded task, only within allowed paths, and uses deviation triage:

- `AUTO_ACCEPTABLE_TECHNICAL_VARIATION`;
- `BRAIN_REVIEW_REQUIRED`;
- `USER_DECISION_REQUIRED`.

## N8_RUN_CHECKS

Codex or human runs `bash tests/run_checks.sh`. Machine checks validate mechanics, not product meaning.

## N9_RETURN_EVIDENCE_TO_BRAIN

Human returns diff, checks, Golden Case results, deviation record, and PR evidence to Brain.

## N9A_BRAIN_SEMANTIC_REVIEW

Brain writes `observer/brain_semantic_review.json` after comparing original problem, confirmed meaning, contract, Codex interpretation, diff, tests, Golden Cases, and acceptance plan.

Brain must evaluate semantic drift, scope drift, overdesign, original-problem resolution, and technically-correct-but-practically-wrong risk.

## N10_USER_ACCEPTANCE

The human performs `runtime/user_acceptance_plan.json` against the real product and records `observer/acceptance_receipt.json`.

The human does not need to audit internal file or function design.

## N11_RECONCILE

`scripts/reconcile.py` decides machine closure readiness only. It requires passing machine evidence, Brain semantic review, and predefined user acceptance coverage.

## N12_HUMAN_CLOSE_OR_REJECT

Human approves close, rejects, requests narrow repair, or returns to product meaning closure.
