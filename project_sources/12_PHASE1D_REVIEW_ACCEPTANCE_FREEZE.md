# Phase 1D Review, Acceptance and Freeze

canonical_rule_id: JF_PHASE1D_EXACT_PARENT
source_section_id: 12::EXACT_PARENT

PR1D extends only the exact passed PR1C package recorded in `PHASE1_STAGE_LINEAGE.json`. Earlier PR1D–PR1F uploads are target material and cannot substitute for that parent.

canonical_rule_id: JF_PHASE1D_EXACT_REVIEW_CHAIN
source_section_id: 12::EXACT_REVIEW_CHAIN

A merge-candidate freeze consumes the exact current repository, PR body, PR record, PR CI result, Projection, Codex Return, Evidence Bundle and Brain Review Capsule. A digest-only replacement is insufficient when the current source object is available.

canonical_rule_id: JF_PHASE1D_ACCEPTANCE_SOURCE
source_section_id: 12::ACCEPTANCE_SOURCE

Applicable User Acceptance occurs only after an exact Merge Candidate Freeze exists. `user_acceptance_status: PASS` must come from the exact current user-acceptance Capsule and its user decision evidence reference, and that Capsule must bind the exact freeze digest. `NOT_APPLICABLE` must carry the exact reason and the same freeze binding. The Web Brain cannot create a bare acceptance PASS.

canonical_rule_id: JF_PHASE1D_MERGE_READY_SOURCE
source_section_id: 12::MERGE_READY_SOURCE

`MERGE_READY` is a derived Gate result after the exact freeze and applicable acceptance are satisfied; it is not a predecessor object consumed by the freeze. The freeze itself is created from Brain Review PASS plus current PR CI PASS. Codex and tools cannot fill or elevate user acceptance or final merge authorization.

canonical_rule_id: JF_PHASE1D_FAIL_CLOSED
source_section_id: 12::FAIL_CLOSED

PR1D stops with an exact Merge Candidate Freeze awaiting user decisions. It does not require a Merged Change Projection before merge and does not issue user final merge authorization, automatic merge, automatic acceptance or automatic Promotion.
