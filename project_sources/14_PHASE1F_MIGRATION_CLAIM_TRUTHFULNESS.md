# Phase 1F Migration Claim Truthfulness

canonical_rule_id: RULE_LEGACY_SOURCE_IDENTITY_SET
source_section_id: 14::LEGACY_SOURCE_IDENTITY_SET

Every legacy row binds an exact historical source filename, byte count and SHA-256. Missing exact section text cannot be treated as replayed evidence.

canonical_rule_id: RULE_BRAIN_OWNED_LEGACY_SEMANTIC_MAPPING
source_section_id: 14::BRAIN_OWNED_LEGACY_SEMANTIC_MAPPING

Legacy-to-current semantics belong to Web Brain. A separately sealed mapping object is consumed but never authored by generators.

canonical_rule_id: RULE_LEGACY_MIGRATION_EVIDENCE_STRENGTH
source_section_id: 14::LEGACY_MIGRATION_EVIDENCE_STRENGTH

Current-target tests prove only current targets and cannot prove unavailable legacy meaning.

canonical_rule_id: RULE_LEGACY_MIGRATION_PER_TARGET_COVERAGE
source_section_id: 14::LEGACY_MIGRATION_PER_TARGET_COVERAGE

BEHAVIORALLY_VERIFIED requires exact legacy text, FULLY_PRESERVED Brain mapping and every target behavior evidence.

canonical_rule_id: RULE_LEGACY_MIGRATION_STATUS_SEMANTICS
source_section_id: 14::LEGACY_MIGRATION_STATUS_SEMANTICS

MAPPED_ONLY identifies targets without semantic equivalence. Deferred and retired states never claim equivalence.

canonical_rule_id: RULE_CAPABILITY_CLAIM_SUBJECT_REGISTRY
source_section_id: 14::CAPABILITY_CLAIM_SUBJECT_REGISTRY

Capability IDs, subjects, statuses and verification refs must exactly match the registry.

canonical_rule_id: RULE_CANDIDATE_CAPABILITY_CLAIM_BOUNDARY
source_section_id: 14::CANDIDATE_CAPABILITY_CLAIM_BOUNDARY

The package cannot self-assign independent review, baseline, release, merge or Promotion.

canonical_rule_id: RULE_CURRENT_CANDIDATE_DOCUMENT_IDENTITY
source_section_id: 14::CURRENT_CANDIDATE_DOCUMENT_IDENTITY

All active candidate identity surfaces must match the exact current PACKAGE_MANIFEST package name, current bootloader, scope, README, repair matrix and repair record. Inherited review targets must be explicitly marked historical and non-authoritative for the current review.

canonical_rule_id: RULE_LEGACY_MIGRATION_SCHEMA_CLOSURE
source_section_id: 14::LEGACY_MIGRATION_SCHEMA_CLOSURE

Legacy source identity, Brain semantic mapping, migration rows, verification registry, capability claim registry and capability status must pass strict current Schemas before semantic migration validation. Unknown fields, wrong types and status values are blocking.
