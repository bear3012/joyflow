# Phase 2A — PR / Change-Unit Goal and Scenario Grounding


canonical_rule_id: RULE_PHASE2A_EXISTING_TASK_CAPSULE_EXTENSION
source_section_id: 21::EXISTING_TASK_CAPSULE_EXTENSION

A repository PR remains one bounded current task round. Phase 2A does not create a parallel PR-plan object: parent product goal, material operating assumptions, relevant prior behaviors and exit conditions are carried inside the existing task anchor.

canonical_rule_id: RULE_PHASE2A_PARENT_GOAL_CONTINUITY
source_section_id: 21::PARENT_GOAL_CONTINUITY

Repository-changing PR work must state the parent product goal that explains why the current PR exists. The parent goal guides continuity but does not authorize later PRs and does not replace the current user-approved execution object.

canonical_rule_id: RULE_PHASE2A_MATERIAL_OPERATING_ASSUMPTIONS_ONLY
source_section_id: 21::MATERIAL_OPERATING_ASSUMPTIONS_ONLY

Operating assumptions are recorded only when user scale, data scale, environment, failure tolerance or another scenario fact can materially change technical route, validation depth or acceptance. Every assumption states its basis and a reopen trigger. No standalone scenario profile or second product-requirements document is created.

canonical_rule_id: RULE_PHASE2A_RELEVANT_PRIOR_BEHAVIOR_BOUNDING
source_section_id: 21::RELEVANT_PRIOR_BEHAVIOR_BOUNDING

Only prior behaviors plausibly affected by the current change unit are referenced. They must bind source references and explain relevance. Phase 2A does not build a permanent capability registry or require every PR to reload all historical capabilities.

canonical_rule_id: RULE_PHASE2A_EXIT_CONDITION_CLOSURE
source_section_id: 21::EXIT_CONDITION_CLOSURE

Each current change unit states explicit exit conditions. An exit condition can be satisfied by a bounded change, a truthful no-change conclusion on an applicable route, or a blocker; it cannot imply user acceptance, merge authorization or automatic promotion.

canonical_rule_id: RULE_PHASE2A_CLAIM_AUTHORSHIP_AUTHORITY_SEPARATION
source_section_id: 21::CLAIM_AUTHORSHIP_AUTHORITY_SEPARATION

The Web Brain may structure and record planning claims, including claims that reflect a user decision, but `recorded_by` semantics never create authority. A user-confirmed operating assumption must bind USER_DECISION evidence; a repository-observed assumption must bind repository evidence; a Brain inference must remain explicitly INFERRED and bind Brain-derivation evidence. The exact planning context is visible in the user execution-approval view.

canonical_rule_id: RULE_PHASE2A_PRIOR_BEHAVIOR_DISPOSITION
source_section_id: 21::PRIOR_BEHAVIOR_DISPOSITION

A relevant prior behavior is not automatically immutable. Each current change unit declares whether the behavior is `PRESERVE_REQUIRED`, `CHANGE_AUTHORIZED`, or `SUPERSEDE_AUTHORIZED`. Authorized change or supersession requires current user-decision evidence; preservation must not carry fabricated change authorization.

canonical_rule_id: RULE_PHASE2A_STRUCTURAL_FRAME_INHERITS_GOAL
source_section_id: 21::STRUCTURAL_FRAME_INHERITS_GOAL

A Structural Decision Frame is a conditional technical-question view of the already-grounded current product goal. It must bind the same goal/non-goals/protected semantics and cannot introduce a parallel requirement object or turn a Codex architecture preference into user-confirmed product intent.
