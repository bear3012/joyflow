# Phase 2C — Scenario-Bounded Goal and Cumulative Review

canonical_rule_id: RULE_PHASE2C_SCENARIO_BOUNDED_GOAL_REVIEW
source_section_id: 23::SCENARIO_BOUNDED_GOAL_REVIEW

Brain Review judges whether the frozen product goal is supported in the material operating assumptions carried by the current Task Capsule. Validation supports a bounded current conclusion and must not claim exhaustive absence of unknown defects.

canonical_rule_id: RULE_PHASE2C_MACHINE_HUMAN_VALIDATION_BOUNDARY
source_section_id: 23::MACHINE_HUMAN_VALIDATION_BOUNDARY

Machine validation covers deterministic behavior, data/state integrity, relevant regression and material high-loss failure paths when mechanically testable. User acceptance remains a separate human-owned gate for user-visible flow, product meaning and subjective experience when applicable. Neither status promotes the other.

canonical_rule_id: RULE_PHASE2C_RELEVANT_PRIOR_BEHAVIOR_REVIEW
source_section_id: 23::RELEVANT_PRIOR_BEHAVIOR_REVIEW

Cumulative review expands only the prior behaviors explicitly relevant to the current change unit. A Brain PASS requires every relevant prior behavior to close according to its approved expected disposition; unrelated historical capabilities are not automatically reloaded or revalidated.

canonical_rule_id: RULE_PHASE2C_EXPECTED_OBSERVED_IMPACT
source_section_id: 23::EXPECTED_OBSERVED_IMPACT

Brain Review compares the expected current-source path impact with the actual current result. Unexpected material impact requires re-closure and cannot be hidden behind passing tests. This comparison does not authorize wider paths.

canonical_rule_id: RULE_PHASE2C_TRUTHFUL_RESIDUALS
source_section_id: 23::TRUTHFUL_RESIDUALS

Current residuals state the remaining issue, material risk and reopen trigger. Residuals are bounded current-task facts, not a permanent debt database, and cannot be silently converted into completed scope.

canonical_rule_id: RULE_PHASE2C_USER_RISK_ACCEPTANCE_AUTHORITY_BINDING
source_section_id: 23::USER_RISK_ACCEPTANCE_AUTHORITY_BINDING

The Web Brain may record `RESIDUAL_ACCEPTED_BY_USER`, but the authority belongs to the user. That status requires current USER_DECISION evidence bound to the exact risk identifier. Brain recommendation or Brain-review evidence cannot substitute for user agreement. `BLOCKED` high-loss risk cannot coexist with Brain Review PASS.

canonical_rule_id: RULE_PHASE2C_PRIOR_BEHAVIOR_DISPOSITION_CLOSURE
source_section_id: 23::PRIOR_BEHAVIOR_DISPOSITION_CLOSURE

Cumulative review consumes the current change unit's expected disposition for every relevant prior behavior. `PRESERVE_REQUIRED` must end PRESERVED; `CHANGE_AUTHORIZED` may end CHANGED_WITH_RECLOSURE; `SUPERSEDE_AUTHORIZED` may end SUPERSEDED_WITH_RECLOSURE. An unapproved change remains blocking. This protects prior capability without freezing legitimate user-authorized product evolution.

canonical_rule_id: RULE_PHASE2C_IMPACT_COMPARE_EXACT_TARGET
source_section_id: 23::IMPACT_COMPARE_EXACT_TARGET

Expected impact is mechanically derived from the approved current-source context; observed repository impact is mechanically derived from the exact reviewed PR head's changed paths. The Brain may interpret the consequence, but may not self-author an observed-path set that differs from the exact review target.

canonical_rule_id: RULE_PHASE2C_EXIT_CONDITION_CONSUMPTION
source_section_id: 23::EXIT_CONDITION_CONSUMPTION

Brain Review consumes every exit condition from the current task anchor exactly once. Brain PASS requires all current change-unit exit conditions to be SATISFIED with evidence; a pending or blocked exit condition prevents PASS.


canonical_rule_id: RULE_PHASE2C_WHOLE_SYSTEM_STRUCTURAL_REVIEW
source_section_id: 23::WHOLE_SYSTEM_STRUCTURAL_REVIEW

When the current change used structural discovery or materially changes the reviewed structural skeleton, Brain Review compares the approved project-level technical closure with the actual reviewed Diff/source evidence. The Brain reviews from the whole-project product/architecture perspective but may use the goal-conditioned structural projection rather than rereading the entire repository. Any material structural consequence not covered by the approved closure requires re-closure; a path-matching Diff and passing tests do not by themselves prove structural continuity.

canonical_rule_id: RULE_PHASE2C_EXACT_STRUCTURAL_CONSEQUENCE_DISPOSITION
source_section_id: 23::EXACT_STRUCTURAL_CONSEQUENCE_DISPOSITION

If the approved mutating Handoff carries a structural-route binding, Brain Review must bind the exact approved structural closure and consume the exact set of material structural consequences returned by Codex. Each consequence receives one explicit `PRESERVED`, `AUTHORIZED_CHANGE` or `RECLOSURE_REQUIRED` disposition with review basis grounded in the current result target. Brain PASS cannot omit a Codex-reported material consequence or coexist with any `RECLOSURE_REQUIRED` disposition. The same review records `NO_REFOLD_REQUIRED` or `REFOLD_REQUIRED` for the sparse long-term structural projection; path matching and passing tests do not substitute for this structural review.
