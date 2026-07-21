# Rule Cards

## R1. Brain-first

Raw human intent cannot be executed directly. Brain must first close every ambiguity that could materially change product result, user flow, data meaning, scope, risk, tradeoff, or acceptance.

## R2. Product meaning closure

`runtime/product_meaning_closure.json` is authoritative only when:

- `material_ambiguity_status=NO_MATERIAL_AMBIGUITY`;
- `user_confirmation.status=CONFIRMED`;
- walkthrough, examples, Golden Cases, and acceptance meaning agree.

The user confirms concrete product behavior, not implementation details.

## R3. Reverse product walkthrough

Brain must restate:

```text
entry
→ user action
→ system response
→ success and failure
→ preserved behavior
→ explicitly absent behavior
```

An abstract “is this correct?” question is not sufficient when behavior is material.

## R4. Dual-layer contract

`runtime/translation_contract.json` must contain:

- `human_semantic_layer` for objective, result, flow, rules, tradeoffs, non-goals, and positive/negative examples;
- `mechanical_execution_layer` for invariants, solution surfaces, forbidden consequences, required outcomes, technical freedom, stop conditions, and evidence.

Natural language carries meaning. Mechanical fields bind the boundary.

## R5. Meaning delta

A successor records `added`, `removed`, `changed`, and `unchanged` in `runtime/meaning_delta.json`.

Unchanged meaning must not be rewritten into a new meaning. A non-equivalent restatement is a semantic change.

## R6. Golden Cases

`runtime/golden_cases.json` contains stable case IDs reused across clarification, contract, Codex interpretation, tests, Brain review, human acceptance, and later regression work.

Do not silently weaken or restate a Golden Case.

## R7. User acceptance at contract time

`runtime/user_acceptance_plan.json` is created before implementation. Codex, Brain, and the human use the same steps and expected outcomes.

## R8. Contract red-team gate

The contract and product closure must be reviewed before routing. The review writes:

```text
runtime/contract_red_team_review.md
observer/contract_red_team_receipt.json
```

If the receipt verdict is `BLOCK`, execution remains blocked.

## R9. Lane freeze

Allowed lanes are:

```text
FAST_LANE
REVIEW_QUEUE_LANE
HARD_STOP_LANE
```

Unclear tasks default to REVIEW_QUEUE_LANE. High-risk tasks route to HARD_STOP_LANE.

## R10. Codex interpretation handshake

Before non-LEAN implementation, Codex returns `runtime/codex_execution_interpretation.json` with one status:

```text
ALIGNED
TECHNICAL_DISCOVERY_REQUIRED
MATERIAL_UNCERTAINTY
CONTRACT_CONFLICT
```

Only `ALIGNED` may reach normal execution. A valid LEAN task may embed the same interpretation fields in its single execution prompt.

## R11. LEAN proportionality

LEAN avoids a separate handshake only for low-risk, known-path, no-product-meaning-change work. It does not remove semantic boundaries, Golden Cases when relevant, or evidence.

## R12. Single execution carrier and single complete prompt

The only formal mutation carrier is:

```text
runtime/execution_bridge_package.json
```

The user receives one complete Codex execution Prompt. Internal artifacts may be referenced but must not require the user to assemble instruction fragments.

## R13. Deviation triage

Differences route as:

- `AUTO_ACCEPTABLE_TECHNICAL_VARIATION` for equivalent implementation inside the approved boundary;
- `BRAIN_REVIEW_REQUIRED` for expanded solution surface, shared state, interface, maintenance, or unexpected technical consequence;
- `USER_DECISION_REQUIRED` for product rules, user flow, data meaning, features, experience, risk, or tradeoff changes.

## R14. Context palace boundary

`runtime/context_palace.md` is navigation only and cannot override product meaning, contract, interpretation, or bridge.

## R15. Codex boundary

Codex may modify only files listed in bridge `allowed_paths`.

Codex must not execute if product meaning is unconfirmed, material ambiguity remains, interpretation is not aligned, `execution_allowed=false`, or target lane is HARD_STOP_LANE.

## R16. Evidence-first

Completion requires mechanical evidence, Brain semantic review, predefined user acceptance, and final human closure. AI explanation alone is insufficient.

## R17. Original-problem recheck

`observer/brain_semantic_review.json` must compare the PR to the original user problem, not only the latest contract, and must report technically-correct-but-practically-wrong risk.

## R18. Reconcile authority

`scripts/reconcile.py` is the only machine writer of `closure_ready`.

Reconcile checks declared evidence and gates. It cannot approve product meaning or replace human acceptance.

## R19. Durable facts policy

Store stable business rules, durable boundaries, reusable Golden Cases, stable module relations, repeated acceptance paths, and confirmed non-goals when future reuse justifies it.

Do not store AI chain-of-thought, chat transcripts, speculative options, or every temporary task packet as product truth.

## R20. Subject freeze

`subject/task_state.json` must keep exactly five fields:

```text
task_id
task_status
target_lane
graph_sync_required
formal_pending
```
