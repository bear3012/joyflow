# Edge Cards

## E0: H0_RAW_HUMAN_INTENT → H1_ASSOCIATIVE_DISCUSSION

Raw intent must be explored before being frozen.

## E1: H1_ASSOCIATIVE_DISCUSSION → H2_INTENT_CALIBRATION

Brain presents risks and interpretations; human calibrates.

## E2: H2_INTENT_CALIBRATION → H3_DETERMINISTIC_INTENT

Only calibrated intent may be frozen.

## E3: H3_DETERMINISTIC_INTENT → H4_TRANSLATION_CONTRACT

Deterministic intent becomes `runtime/translation_contract.json`.

## E4: H4_TRANSLATION_CONTRACT → R0_CONTRACT_RED_TEAM_REVIEW

The contract must be attacked for ambiguity, missing acceptance, false-pass risk, and hard-stop risk.

## E5: R0_CONTRACT_RED_TEAM_REVIEW → N1_ROUTE_TASK

Routing must respect the red-team receipt. BLOCK forces HARD_STOP_LANE.

## E6: N1_ROUTE_TASK → N3_BUILD_BRIDGE

Routing result becomes bridge input.

## E7: N3_BUILD_BRIDGE → N4_BUILD_CONTEXT_PALACE

Context palace is derived from bridge only.

## E8: N4_BUILD_CONTEXT_PALACE → N5_BUILD_CODEX_PACKET

Codex packet is derived from bridge and context palace.

## E9: N5_BUILD_CODEX_PACKET → N6_HUMAN_HANDOVER_TO_CODEX_APP

Human handoff is mandatory.

## E10: N6_HUMAN_HANDOVER_TO_CODEX_APP → N7_CODEX_APP_EXECUTION

Codex may execute only if packet and bridge allow execution.

## E11: N7_CODEX_APP_EXECUTION → N8_RUN_CHECKS

Checks must run before evidence return.

## E12: N8_RUN_CHECKS → N9_RETURN_EVIDENCE_TO_BRAIN

Raw check evidence is returned to Brain.

## E13: N9_RETURN_EVIDENCE_TO_BRAIN → N10_HUMAN_REVIEW_PACKET

Evidence is translated into human-native review.

## E14: N10_HUMAN_REVIEW_PACKET → N11_RECONCILE

Reconcile reads checks, receipts, PR evidence, and human review packet.

## E15: N11_RECONCILE → N12_HUMAN_CLOSE_OR_REJECT

Human remains the final closer even when machine closure readiness is true.
