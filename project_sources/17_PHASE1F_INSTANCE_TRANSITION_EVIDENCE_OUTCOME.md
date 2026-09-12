# Phase 1F Current-Instance / Transition-Capability Separation

canonical_rule_id: RULE_CURRENT_MIGRATION_INSTANCE_TRANSITION_CAPABILITY_SEPARATION
source_section_id: 17::CURRENT_INSTANCE_TRANSITION_CAPABILITY_SEPARATION

The frozen 176-row migration instance and the reusable disposition-transition capability are different lifecycle objects. The current instance may remain exact-source-unavailable and `NOT_EVALUATED / MAPPED_ONLY`; mechanism tests for confirmed semantics use isolated test-only fixtures and may not promote fixture evidence into any current legacy row.

canonical_rule_id: RULE_EXACT_LEGACY_SOURCE_REPLAY_FIXTURE_BOUNDARY
source_section_id: 17::EXACT_LEGACY_SOURCE_REPLAY_FIXTURE_BOUNDARY

A confirmed-semantic transition test must consume real fixture bytes through the same public mapping and migration-generation path: verify full-file byte count and SHA-256, extract one uniquely marked section, verify its section digest, resolve the Brain semantic-evidence reference, validate current target-rule identity, then consume the disposition. Field mutation without exact bytes is not positive evidence.

canonical_rule_id: RULE_DISPOSITION_EVIDENCE_OUTCOME_CONTRACT_COMPLETE
source_section_id: 17::DISPOSITION_EVIDENCE_OUTCOME_CONTRACT_COMPLETE

The shared disposition transition contract includes both authority dimensions and evidence dimensions. For each legal decision/basis combination it defines every allowed `(semantic evidence state, target behavior evidence state)` pair and the exact resulting migration status plus equivalence-claim value. Derivation and tests read those outcomes and may not maintain separate carry-forward result logic.

canonical_rule_id: RULE_PUBLIC_TRANSITION_PATH_POSITIVE_COVERAGE
source_section_id: 17::PUBLIC_TRANSITION_PATH_POSITIVE_COVERAGE

Positive capability coverage must execute the public transition path from exact source fixture through source identity, Brain mapping, disposition validation and generated migration row. It must include confirmed technical retirement, confirmed carry-forward with complete behavior evidence, confirmed carry-forward with incomplete behavior evidence, and failure cases for source-byte, section-digest or source-root mismatch.
