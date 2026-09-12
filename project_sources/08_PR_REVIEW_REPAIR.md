# PR, Review, Repair and Human Merge Boundary

canonical_rule_id: JF_DL_PR_CANDIDATE_ONLY_RULE
source_section_id: 08::PR_CANDIDATE_ONLY

Product/governance repository-changing execution is PR-first and must not mutate the default branch. A transport-only Evidence ref is a separately classified temporary remote-mutation surface: it still requires the exact user-approved execution authority, but it is not a candidate product/governance change and therefore does not enter product PR or merge promotion. A product/governance PR remains candidate state even when checks pass.

canonical_rule_id: JF_DL_EXECUTION_REVIEW_RULE
source_section_id: 08::EXECUTION_REVIEW

Codex returns the exact candidate PR/head identity, raw diff path list and required machine evidence while leaving Brain review, user acceptance and merge status pending. The Web Brain then checks the current PR, Diff, checks, logs and contract. Codex narration is a claim to verify, not final evidence by itself.

canonical_rule_id: JF_DL_SEPARATE_MERGE_AUTHORIZATION_RULE
source_section_id: 08::SEPARATE_MERGE_AUTHORIZATION

Execution approval does not authorize merge. After Brain Review PASS and current PR CI PASS, the Web Brain freezes the exact Merge Candidate. Applicable User Acceptance is then recorded against that exact freeze, and only a separate explicit user final merge authorization for the same frozen PR head permits merge. `MERGE_READY` and `MERGE_ALLOWED` are derived Gate results, not user-authoritative lifecycle objects; Codex and tools may never create or elevate the underlying user decisions.

canonical_rule_id: JF_DL_RUNTIME_GIT_PROMOTION_EVIDENCE_RULE
source_section_id: 08::RUNTIME_GIT_PROMOTION_EVIDENCE

Joyflow does not use an autonomous trusted GitHub observer or automatic promotion adapter. Codex returns current raw Git/PR materials; the Web Brain independently rechecks the exact current review target and repository evidence before any merge recommendation or post-merge record. Missing or stale materials block the claim.

canonical_rule_id: JF_DL_MERGE_PROMOTION_RULE
source_section_id: 08::MERGE_PROMOTION

Joyflow does not automatically promote state. The chain is: candidate PR evidence → Brain Review PASS + current PR CI PASS → exact Merge Candidate Freeze → applicable User Acceptance → separate User Final Merge Authorization → actual merge → Brain recheck of current repository evidence. `MERGE_READY` / `MERGE_ALLOWED` may be rendered only as derived Gate results. Only the observed merged repository result becomes durable fact. A Task Completion Pointer is a minimal reference record, not a competing truth source.

canonical_rule_id: JF_DL_REPAIR_EXTENSION_RULE
source_section_id: 08::REPAIR_EXTENSION

Repair is a decision-boundary extension containing failure evidence, root cause, source Projection digest, retained-boundary digest and source-compatibility verdict. It is not another complete task template.

canonical_rule_id: JF_DL_TASK_COMPLETION_POINTER_RULE
source_section_id: 08::TASK_COMPLETION_POINTER

After Brain rechecks current repository materials showing the approved PR head was merged, it may record a minimal pointer to task, PR head, merge commit and direct evidence reference. The pointer does not independently prove or replace repository state.

canonical_rule_id: JF_DL_PROTOCOL_REPAIR_WORKFLOW_RULE
source_section_id: 08::PROTOCOL_REPAIR_WORKFLOW

A Joyflow protocol repair proceeds through issue repair, reverse consistency sweep, independent stranger cold review and user decision. A producing package may not self-promote before independent review.

canonical_rule_id: JF_DL_REPAIR_CIRCUIT_BREAKER_RULE
source_section_id: 08::REPAIR_CIRCUIT_BREAKER

Repeated failed execution, source incompatibility, unbounded scope growth or evidence conflict returns to Brain. The cycle increments only when resolving the problem materially changes the execution authorization envelope and therefore requires reclosure; a same-envelope implementation retry remains a new attempt in the current cycle.

canonical_rule_id: JF_DL_ARTIFACT_REPOSITORY_REVIEW_SPLIT_RULE
source_section_id: 08::ARTIFACT_REPOSITORY_REVIEW_SPLIT

Repository-changing execution is reviewed against a specific PR head, Diff and touched-path evidence. Non-repository Artifact execution is reviewed against the complete exact output Artifact set, its deterministic output-set digest and per-output SHA-256 Evidence, and must not fabricate PR fields. Both paths remain Brain-reviewed and user acceptance is recorded only when applicable.

canonical_rule_id: JF_DL_MERGE_RECORD_CONTINUITY_RULE
source_section_id: 08::MERGE_RECORD_CONTINUITY

The exact Merge Candidate Freeze is the pre-merge object-binding authority for the current PR head and reviewed execution chain. Applicable User Acceptance binds that exact freeze; User Final Merge Authorization binds both the exact freeze and acceptance disposition. `MERGE_READY` and `MERGE_ALLOWED` are derivable status results only and are not required predecessor objects. A completion pointer binds the exact freeze, acceptance and final merge authorization plus the later observed repository result.


canonical_rule_id: RULE_BLOCKED_RETURN_REVIEW_BOUNDARY
source_section_id: 08::BLOCKED_RETURN_REVIEW_BOUNDARY

Brain review binds the exact Codex source execution status. A source Return whose status is `BLOCKED` may be accepted as blocked, returned for repair, or submitted for user decision, but it cannot receive Brain review `PASS`. Only a new exact `COMPLETED` Return can later be reviewed for PASS.

canonical_rule_id: RULE_BLOCKED_RETURN_EXACT_REVIEW_TARGET
source_section_id: 08::BLOCKED_RETURN_EXACT_REVIEW_TARGET

A `BLOCKED` Codex Return is reviewed as the exact blocked Return, not as a fabricated or retained PR head. Its review target binds the Return digest, technical-preflight status, finding ID, blocker Evidence, mutation state and unresolved items. Only machine checks actually run before the block may appear, and their results remain factual rather than being forced to PASS.

canonical_rule_id: RULE_INITIAL_REVIEW_EXACT_SOURCE_TRIO
source_section_id: 08::INITIAL_REVIEW_EXACT_SOURCE_TRIO

The first creation of an execution-review fiber, or any later change to its source Projection, Return, Evidence Bundle, execution status or review target, must be sealed with the exact Projection, Codex Return and Evidence Bundle together. Internal copied fields and matching digests cannot substitute for those current source objects. Later review-state edits may reuse the already frozen source only while all source identity fields remain unchanged.

canonical_rule_id: RULE_REVIEW_SOURCE_DERIVED_SNAPSHOT_CONTINUITY
source_section_id: 08::REVIEW_SOURCE_DERIVED_SNAPSHOT_CONTINUITY

Brain Review freezes a digest over all source-derived content: source Projection/Return/Bundle identities, source execution status, review target, copied machine results and unresolved followups. Brain verdict, explanation and later user-owned state may change independently. Any change to source-derived content requires the exact Projection, Codex Return and Evidence Bundle to be supplied and compared again; retaining top-level source digests while substituting machine Evidence is rejected.

canonical_rule_id: RULE_REVIEW_CURRENT_SOURCE_REPLAY
source_section_id: 08::REVIEW_CURRENT_SOURCE_REPLAY

The exact Projection, Codex Return and Evidence Bundle used to create or materially revise Brain Review are not only structurally compared: deterministic direct facts and approved test commands are replayed against the supplied current repository or exact Artifact files. A Review cannot inherit PASS from a self-consistent fabricated capture. Brain still decides semantic sufficiency and Verdict after the mechanical replay; replay itself has no review, acceptance or merge authority.

canonical_rule_id: RULE_REPOSITORY_RESULT_REVIEW_CONTINUITY
source_section_id: 08::REPOSITORY_RESULT_REVIEW_CONTINUITY

Repository Brain Review binds the approved Base, descendant result Head, exact Base-to-Head Diff and validation replay performed at that same result Head. A current checkout, another Commit or an input-Base test result cannot substitute for the reviewed Head.

canonical_rule_id: RULE_ARTIFACT_OUTPUT_SET_REVIEW_CONTINUITY
source_section_id: 08::ARTIFACT_OUTPUT_SET_REVIEW_CONTINUITY

Artifact Codex Return, operational Review sealing and later Review revisions preserve the same ordered canonical output set and output-set digest. Every output is supplied to the formal route and covered by a direct SHA-256 observation. Missing, additional or substituted outputs block Review rather than being lost through an optional generic interface.

canonical_rule_id: JF_DL_ARTIFACT_COMPLETE_OUTPUT_SET_RULE
source_section_id: 08::ARTIFACT_COMPLETE_OUTPUT_SET

Artifact execution returns a canonical complete output array with unique Artifact IDs, exact SHA-256, byte length, media type, role and validation Evidence. A validated result is supplied through one explicit real dedicated output root. Every declared output is one direct regular-file child of that root, source inputs and source materials remain outside it, and the root's complete lexical object set must equal the declared output set. The actual files supplied to operational validation, Codex Return, final validation object and Brain Review must represent exactly that same set; missing, extra, pre-existing undeclared, replaced, duplicate, nested, symlink or other non-regular objects block.

canonical_rule_id: JF_DL_ARTIFACT_OUTPUT_TARGET_VALIDATION_RULE
source_section_id: 08::ARTIFACT_OUTPUT_TARGET_VALIDATION

Artifact completion requires every required output to be covered by applicable final validation Evidence bound to that exact output. Input or source-material validation proves only the approved input and cannot substitute for output validation.

canonical_rule_id: JF_DL_NEW_ARTIFACT_SOURCE_MATERIAL_RULE
source_section_id: 08::NEW_ARTIFACT_SOURCE_MATERIAL

`NEW_ARTIFACT` execution uses an exact canonical source-material set instead of an invented source Artifact. The source-material IDs and digests are approved input, while the generated complete output set is the execution result, final validation target and Brain Review target.

canonical_rule_id: RULE_PR_REVIEW_STRUCTURAL_RESULT_REFERENCE
source_section_id: 08::PR_REVIEW_STRUCTURAL_RESULT_REFERENCE

When a PR was executed under an approved structural closure, PR review must feed the exact result Diff/source evidence into the Phase 2C structural consequence review. PR path correctness, check success and mergeability cannot substitute for the project-level structural disposition defined by Phase 2C.

canonical_rule_id: RULE_GITHUB_EVIDENCE_TRANSPORT_NOT_PRODUCT_PR
source_section_id: 08::GITHUB_EVIDENCE_TRANSPORT_NOT_PRODUCT_PR

A commit/ref used only to transport the current-round Evidence Bundle is not a candidate product/governance change, is not merged into the product PR, does not enter Merge Ready/Allowed promotion, and cannot become the reviewed product result. The product/governance change continues through its normal PR-first Brain review and user merge authorization. Brain reviews the transported Evidence only after exact-object identity and bundle identity are independently verified.

