# Phase 1F Product-Direction-Bound Disposition

canonical_rule_id: RULE_PRODUCT_DIRECTION_BOUND_DISPOSITION_AUTHORITY
source_section_id: 16::PRODUCT_DIRECTION_BOUND_DISPOSITION_AUTHORITY

Web Brain may close technical carry-forward, defer, retirement or supersession decisions when the result preserves the currently confirmed product direction, important tradeoffs, non-goals, authority topology and user Gates. A disposition that changes any of those boundaries requires a current explicit user decision.

canonical_rule_id: RULE_SPARSE_USER_DECISION_GATE
source_section_id: 16::SPARSE_USER_DECISION_GATE

User decision is sparse and boundary-focused, not a per-row approval workflow. One exact user decision may cover a clearly identified group of legacy rules. Execution approval, applicable acceptance and final merge authorization remain separate user Gates.

canonical_rule_id: RULE_DISPOSITION_PRODUCT_DIRECTION_EFFECT
source_section_id: 16::DISPOSITION_PRODUCT_DIRECTION_EFFECT

Every disposition declares one product-direction effect: `NONE`, `PRESERVES_CONFIRMED_DIRECTION`, `CHANGES_CONFIRMED_DIRECTION` or `UNRESOLVED_MATERIAL_EFFECT`. Web Brain may close only `NONE` and `PRESERVES_CONFIRMED_DIRECTION`; changed direction requires USER ownership and an exact decision reference; unresolved material effect remains open.

canonical_rule_id: RULE_PR1F_MECHANISM_EFFECT_SCOPE
source_section_id: 16::PR1F_MECHANISM_EFFECT_SCOPE

Migration rows state whether they block the PR1F truthful-classification mechanism and separately state that Phase 1 completion is not determined by this artifact. They cannot convert local mechanism validation into a global Phase completion claim.

canonical_rule_id: RULE_HISTORICAL_REVIEW_CONTEXT_MARKING
source_section_id: 16::HISTORICAL_REVIEW_CONTEXT_MARKING

An inherited review target may remain only as explicitly historical comparison context with no authority for the current review. Active candidate identity surfaces bind the exact current package manifest and bootloader.

canonical_rule_id: RULE_DISPOSITION_TRANSITION_CONTRACT_SINGLE_SOURCE
source_section_id: 16::DISPOSITION_TRANSITION_CONTRACT_SINGLE_SOURCE

Every legal disposition decision/basis combination, its owner boundary, product-direction constraint, semantic-evidence requirement and resulting migration state are defined once in the mechanical transition contract. Schema, semantic Validator and state derivation consume that same contract; none may maintain an independent legal-combination list.

canonical_rule_id: RULE_TECHNICAL_RETIREMENT_SEMANTIC_EVIDENCE_GATE
source_section_id: 16::TECHNICAL_RETIREMENT_SEMANTIC_EVIDENCE_GATE

Web Brain retirement based on legacy semantic analysis or technical duplication requires exact legacy text replay, confirmed Brain semantic mapping, a fully preserved semantic relation and existing current replacement rule targets. Missing evidence blocks at disposition validation before migration-state derivation.

canonical_rule_id: RULE_DISPOSITION_TRANSITION_POSITIVE_COVERAGE
source_section_id: 16::DISPOSITION_TRANSITION_POSITIVE_COVERAGE

Every transition declared legal by the shared contract must have a positive test proving Schema acceptance, semantic Validator acceptance and the declared derived migration state. Unsupported combinations and evidence-incomplete irreversible transitions must have failure tests.
