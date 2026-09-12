# Phase 2B — Current-Source Task Grounding and Context Selection

canonical_rule_id: RULE_PHASE2B_CURRENT_SOURCE_CONTEXT
source_section_id: 22::CURRENT_SOURCE_CONTEXT

Historical merged-change projections and prior-behavior references are navigation seeds only. Repository-changing execution must bind the current repository and baseline, replay the current path decision, and carry one current-source context section inside the existing Codex Handoff Projection. No standalone repository-context database or context lifecycle is created.

canonical_rule_id: RULE_PHASE2B_NO_CHANGE_IS_VALID
source_section_id: 22::NO_CHANGE_IS_VALID

For bug-fix and reported-failure routes, current problem reality is an explicit result. `NO_CHANGE_REQUIRED` and `CANNOT_DETERMINE_BLOCKED` are valid outcomes and must not be converted into a mutating approval merely to produce a Diff. New-feature routes may use `NOT_APPLICABLE`.

canonical_rule_id: RULE_PHASE2B_NON_EXHAUSTIVE_HISTORY_SEED
source_section_id: 22::NON_EXHAUSTIVE_HISTORY_SEED

Historical anchors narrow the initial search but never claim complete repository coverage, never exclude unindexed code, and never authorize paths. Current source, dependency, validation and runtime observations may expand the bounded read-only search.

canonical_rule_id: RULE_PHASE2B_IMPACT_COVERAGE_BEFORE_MUTATION
source_section_id: 22::IMPACT_COVERAGE_BEFORE_MUTATION

Before repository mutation, the current task evaluates direct implementation, direct callers, interfaces or schema, data or state boundaries, shared core, relevant tests and the runtime chain. A dimension may be `NOT_APPLICABLE`, but unresolved material impact blocks the mutating handoff.

canonical_rule_id: RULE_PHASE2B_CONTEXT_EXCLUSION_REVERSIBLE
source_section_id: 22::CONTEXT_EXCLUSION_REVERSIBLE

Context exclusions require a current basis and a reopen trigger. Exclusion is a task-local compression decision, not a durable statement that the excluded code can never become relevant.

canonical_rule_id: RULE_PHASE2B_IMPACT_EVIDENCE_COMPATIBILITY
source_section_id: 22::IMPACT_EVIDENCE_COMPATIBILITY

Impact coverage is truth-bound, not shape-bound. `CHECKED` and `NOT_APPLICABLE` require current repository or execution evidence that is compatible with source-location, dependency, validation, or runtime discovery. User product decisions cannot by themselves prove that a source-impact dimension was inspected. A repository mutation must have `DIRECT_IMPLEMENTATION` checked, and unresolved impact blocks mutation.


canonical_rule_id: RULE_PHASE2B_STRUCTURAL_PROJECTION_NAVIGATION_SEED
source_section_id: 22::STRUCTURAL_PROJECTION_NAVIGATION_SEED

A reviewed long-term structural projection may seed navigation and help the Brain frame a current architecture question, but it is not current-source proof. Current repository replay and goal-conditioned Codex discovery confirm or contradict the relevant structural area. A stale/conflicted projection cannot satisfy current-source impact coverage or final path selection.

canonical_rule_id: RULE_PHASE2B_STRUCTURAL_UNCERTAINTY_FROM_CURRENT_SOURCE
source_section_id: 22::STRUCTURAL_UNCERTAINTY_FROM_CURRENT_SOURCE

Current-source grounding may expose material structural uncertainty when ownership, lifecycle, shared-core, dependency/runtime relation or long-lived abstraction cannot be safely determined from the current bounded evidence. That uncertainty is an escalation trigger for structural discovery, not proof that the architecture is defective; structurally clear cross-module work may remain on the ordinary path.
