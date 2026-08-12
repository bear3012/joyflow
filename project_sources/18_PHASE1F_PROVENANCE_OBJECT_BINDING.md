# Phase 1F Provenance Object Binding

canonical_rule_id: RULE_MAPPING_SOURCE_SET_SINGLE_OWNER
source_section_id: 18::MAPPING_SOURCE_SET_SINGLE_OWNER

The top-level legacy source set is the single authority for source-set identity. Brain mapping rows do not independently author a source-set ID; generated migration rows derive the exact ID from the validated top-level source set. A stale or duplicated row-level source-set identity is blocking.

canonical_rule_id: RULE_SEMANTIC_EVIDENCE_EXACT_OBJECT_BINDING
source_section_id: 18::SEMANTIC_EVIDENCE_EXACT_OBJECT_BINDING

A confirmed Brain semantic mapping binds its evidence as a structured package-relative path, exact file SHA-256, unique evidence section ID and exact section SHA-256. Missing, duplicated, stale or mismatched evidence objects block before disposition or migration-state effects.

canonical_rule_id: RULE_SEMANTIC_EVIDENCE_MECHANICAL_SEMANTIC_BOUNDARY
source_section_id: 18::SEMANTIC_EVIDENCE_MECHANICAL_SEMANTIC_BOUNDARY

Mechanical validation proves which exact evidence bytes and section the Web Brain referenced; it does not decide whether those bytes semantically justify the Brain conclusion. Semantic sufficiency remains a Web Brain responsibility and is re-reviewed before any baseline, release or merge effect.

canonical_rule_id: RULE_DEFERRED_STATUS_BASIS_TRUTHFULNESS
source_section_id: 18::DEFERRED_STATUS_BASIS_TRUTHFULNESS

A deferred migration uses the neutral status `DEFERRED_BY_EXACT_CURRENT_DECISION`; the exact technical-scope or current-product basis remains in the bound disposition object rather than being falsely implied by the status name.
