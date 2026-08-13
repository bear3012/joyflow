# Phase 1 Combined Review Chain

canonical_rule_id: PHASE1_STAGE_PARENT_PACKAGE_EXACT_RULE
source_section_id: 11::PHASE1_STAGE_PARENT_PACKAGE_EXACT

Every later Phase 1 stage is applied to the exact most recent passed frozen package. The stage lineage record binds the parent package name, byte count and SHA-256. Older PR1C–PR1F candidates define target increments only and cannot substitute the passed parent implementation.

canonical_rule_id: PR_CURRENT_REPOSITORY_OBJECT_RULE
source_section_id: 11::PR_CURRENT_REPOSITORY_OBJECT

The PR mechanical gate reads the exact current repository, requires the approved Base to be an ancestor of the current Head, computes the Base-to-Head Diff from that repository, and compares the complete changed-path set with the exact Codex Return. Temporary current-review inputs are resolved from a separate PR-body locator and materialized outside the source tree; the locator's source Head must equal the checkout Head and its temporary ref must still resolve to the exact transport commit.

canonical_rule_id: PR_SEALED_SOURCE_CHAIN_RULE
source_section_id: 11::PR_SEALED_SOURCE_CHAIN

A ready PR record binds the exact approved Projection, Final Path Decision, Codex Return, Evidence Bundle, Brain Review Capsule and current repository Head. Digest-valid but unrelated or stale source objects are blocking mismatches.

canonical_rule_id: PR_EXISTING_FROZEN_REPLAY_BINDING_RULE
source_section_id: 11::PR_EXISTING_FROZEN_REPLAY_BINDING

For existing frozen PR replay, the PR record requires empty approved mutation paths and replay evidence rather than current-round PR mutation evidence. The record must exactly match the current repository, PR number, approved Base, existing Head, Base ancestry and complete review coverage, and must reject any source-state drift observed across the replay. The ordinary current-round PR path continues to require non-empty approved mutation paths, exact touched-path coverage and reported mutation.

canonical_rule_id: PR_BODY_ROLE_OWNERSHIP_RULE
source_section_id: 11::PR_BODY_ROLE_OWNERSHIP

The Web Brain owns the Brain block and review verdict. Codex owns the execution block and cannot write Brain review, user acceptance or merge authorization. The Tool only performs read-only mechanical checks and emits a source-bound CI result.

canonical_rule_id: PR_CI_OBSERVATION_ONLY_RULE
source_section_id: 11::PR_CI_OBSERVATION_ONLY

The PR CI entry is a short-lived observer. It may create isolated validation copies but must not change the authoritative source repository, approve execution, accept results, authorize merge or promote a stage.
