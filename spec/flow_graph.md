# Flow Graph

```text
H0_RAW_HUMAN_INTENT
→ H1_ASSOCIATIVE_DISCUSSION
→ H2_INTENT_CALIBRATION
→ H3_PRODUCT_WALKTHROUGH
→ H4_PRODUCT_MEANING_CLOSURE
→ H5_DUAL_LAYER_TRANSLATION_CONTRACT
→ H6_GOLDEN_CASE_AND_USER_ACCEPTANCE_PLAN
→ R0_CONTRACT_RED_TEAM_REVIEW
→ N1_ROUTE_TASK
→ N2_PREFLIGHT_RECORD
→ N3_BUILD_BRIDGE
→ N4_BUILD_CONTEXT_PALACE
→ N5A_BUILD_CODEX_INTERPRETATION_REQUEST
→ N5B_CODEX_EXECUTION_INTERPRETATION
→ N5C_BRAIN_INTERPRETATION_REVIEW
→ N5_BUILD_CODEX_PACKET
→ N6_HUMAN_HANDOVER_TO_CODEX_APP
→ N7_CODEX_APP_EXECUTION
→ N8_RUN_CHECKS
→ N9_RETURN_EVIDENCE_TO_BRAIN
→ N9A_BRAIN_SEMANTIC_REVIEW
→ N10_USER_ACCEPTANCE
→ N11_RECONCILE
→ N12_HUMAN_CLOSE_OR_REJECT
```

## LEAN shortcut

A low-risk, known-path, no-product-meaning-change task may embed the N5A–N5C interpretation fields in the one complete N5 execution packet. This shortcut does not remove product meaning closure, hard boundaries, or evidence.

## Runtime rules

`R0_CONTRACT_RED_TEAM_REVIEW` is a pre-execution review gate. It writes only:

```text
runtime/contract_red_team_review.md
observer/contract_red_team_receipt.json
```

The interpretation request authorizes no mutation. The executable bridge remains the only formal mutation carrier.

Brain semantic review and human user acceptance are separate gates:

- Brain checks semantic drift, scope drift, overdesign, and whether the original problem was actually solved.
- The human checks the predefined real product behavior and experience.

Neither gate replaces machine checks, and machine checks replace neither gate.
