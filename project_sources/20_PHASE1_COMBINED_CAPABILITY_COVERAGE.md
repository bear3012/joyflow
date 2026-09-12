# Phase 1 Combined Capability Coverage Truthfulness

canonical_rule_id: RULE_CAPABILITY_CLAIM_TYPE_SEPARATION
source_section_id: 20::CAPABILITY_CLAIM_TYPE_SEPARATION

A candidate capability registry must distinguish inherited stage presence, exact verified rule coverage and verified cross-stage chain coverage. Presence, local rule verification and end-to-end chain verification are different facts and cannot share one untyped status.

canonical_rule_id: RULE_INHERITED_STAGE_PRESENCE_SCOPE
source_section_id: 20::INHERITED_STAGE_PRESENCE_SCOPE

An inherited-stage-presence claim may identify the exact Phase stages whose materials are present and identity-bound in the current package. It does not claim that every rule or path in those stages has been behaviorally verified and cannot use a behavioral verification status.

canonical_rule_id: RULE_VERIFIED_RULE_COVERAGE_EXACT
source_section_id: 20::VERIFIED_RULE_COVERAGE_EXACT

A verified-rule-coverage claim must list a non-empty exact rule set. The union of every bound verification contract's covered rule IDs must equal the claim rule set; unevidenced rules and evidence outside the declared set are blocking scope mismatches.

canonical_rule_id: RULE_VERIFIED_CROSS_STAGE_CHAIN_SCOPE
source_section_id: 20::VERIFIED_CROSS_STAGE_CHAIN_SCOPE

A verified-cross-stage-chain claim identifies only the stages participating in the exact tested public path and only the cross-stage rules or invariants bound by its verification contract. A passing path cannot be promoted into complete coverage of every participating stage.

canonical_rule_id: RULE_CAPABILITY_COVERAGE_RELATION_BINDING
source_section_id: 20::CAPABILITY_COVERAGE_RELATION_BINDING

Capability claim type, stage scope, rule scope and exact verification references are one relational contract. Stage-presence evidence must exactly cover the declared stages; rule evidence must exactly cover the declared rules; cross-stage evidence must exactly cover both the declared participating stages and declared chain rules.
