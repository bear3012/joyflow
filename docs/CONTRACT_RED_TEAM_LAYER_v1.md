# CONTRACT_RED_TEAM_LAYER_v1

## 0. Purpose

This layer adds a minimal pre-execution contract red-team gate to Joyflow Phase 1.

It does not replace Brain, routing, bridge, Codex packet, checks, reconcile, or human approval.

It exists to catch contract ambiguity before Codex receives an execution packet.

## 1. Boundary

The contract red-team layer may inspect:

```text
runtime/human_intent_card.md
runtime/translation_contract.json
runtime/routing_result.json
runtime/execution_bridge_package.json
runtime/context_palace.md
runtime/codex_task_packet.md
```

The contract red-team layer writes only:

```text
runtime/contract_red_team_review.md
observer/contract_red_team_receipt.json
```

It must not write subject objects.

It must not create an alternate execution carrier.

It must not approve closure.

It must not execute code.

## 2. Position in the loop

The minimal Phase 1 position is:

```text
H4_TRANSLATION_CONTRACT
→ R0_CONTRACT_RED_TEAM_REVIEW
→ N1_ROUTE_TASK
```

If the receipt blocks the contract, route/build scripts must keep execution blocked until the human revises intent or explicitly escalates.

## 3. Required review questions

The review must check:

1. Is deterministic intent present?
2. Is translated engineering scope present?
3. Are non-goals present?
4. Are must-not-infer constraints present?
5. Are forbidden outcomes present?
6. Are acceptance checks present?
7. Are human observation points present?
8. Are unresolved uncertainties explicit?
9. Does the contract touch hard-stop domains?
10. Could Codex execute this without guessing?
11. Could checks falsely pass without proving the intended behavior?
12. Does the contract need human escalation before execution?

## 4. Output contract

`observer/contract_red_team_receipt.json` must include:

```json
{
  "verdict": "PASS|WARN|BLOCK",
  "execution_blocked": false,
  "recommended_lane": "FAST_LANE|REVIEW_QUEUE_LANE|HARD_STOP_LANE",
  "blocking_issues": [],
  "warnings": [],
  "questions_for_human": [],
  "reviewed_inputs": [],
  "generated_review": "runtime/contract_red_team_review.md"
}
```

## 5. Verdict rules

`PASS` means the contract is sufficiently bounded for routing.

`WARN` means the contract may proceed only through review queue or stricter handling.

`BLOCK` means execution must not proceed.

BLOCK is required when:

1. deterministic intent is empty;
2. engineering scope is empty;
3. acceptance checks are empty;
4. hard-stop keywords appear in scope or intent;
5. the contract requires Codex to infer missing implementation details;
6. the task appears to modify Joyflow governance boundaries without explicit human escalation.

## 6. Human-readable review

`runtime/contract_red_team_review.md` must explain:

1. what the contract says in plain language;
2. what could go wrong;
3. what is ambiguous;
4. what Codex might misread;
5. what must be verified;
6. whether the task should proceed, queue, or halt.
