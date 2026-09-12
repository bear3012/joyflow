# Protocol Repair Record — Phase 1 Combined Capability Coverage

repair_source_package:
  name: JOYFLOW_PHASE1F_CONFIRMED_TRANSITION_BOUNDARY_REPAIR_CANDIDATE.zip
  bytes: 989316
  sha256: f3f8fe65cfc99715a0e56fbf4cdd2a8157ad9f81e75f14b9c8a021b1ca0f2c29

root_cause:
  - one untyped capability claim conflated inherited stage presence, selected rule verification and a passing cross-stage path
  - stage IDs, rule IDs and verification references were independent collections rather than one exact relation
  - a five-stage claim with zero rules and one local verification reference could be resealed as `ADVERSARIAL_CASE_VERIFIED`

repair:
  - add `INHERITED_STAGE_PRESENCE`, `VERIFIED_RULE_COVERAGE` and `VERIFIED_CROSS_STAGE_CHAIN` claim types
  - give each claim type separate allowed fields and status semantics
  - require exact equality between a verified-rule claim and the union of its verification contracts' rule IDs
  - require exact equality between a cross-stage claim and the union of its verification contracts' stage and rule scopes
  - prevent a passing chain from implying complete coverage of participating stages
  - retain candidate capability status as navigation-only and unusable as a Stage or Phase Gate

unchanged:
  - PR1A–PR1E operational mechanisms
  - PR1F confirmed-transition boundary
  - current 176-row migration instance
  - user execution, acceptance and merge Gates
  - single Web Brain and single local Codex execution layer

architecture_fit: PASS_NORMAL_REPAIR
minimality_gate: PASS_MINIMAL_NORMAL_REPAIR

validation_before_freeze:
  tests_total: 244
  tests_passed: 244
  tests_failed: 0
  project_source_rules: 316
  unique_project_source_rules: 316
  current_legacy_rows: 176
  current_mapped_only_rows: 176

---

# Protocol Repair Record — Phase 2 Semantic Truth Transport

repair_source_package:
  name: JOYFLOW_PHASE2D_COMPACT_HANDOFF_DELTA_RESUME_CANDIDATE.zip
  bytes: 986429
  sha256: d3440b24af6e3acf5ea60548b0d5194452045641a0c302c2cf3ec6546178fd90

root_cause:
  - Phase 2 correctly extended existing Phase 1 objects instead of creating a second state system, but some new planning/review/resume semantics were only shape-valid.
  - record authorship and decision authority were not consistently separated for Phase 2 claims.
  - evidence references could exist without being compatible with the claim they were used to prove.
  - cumulative impact and Resume state were not fully derived from exact current review objects and blocking deltas.

repair:
  - require provenance + epistemic status for material operating assumptions and expose the exact planning context in the user approval view
  - require compatible evidence for relevant prior behavior and current-source impact coverage
  - separate PRESERVE_REQUIRED / CHANGE_AUTHORIZED / SUPERSEDE_AUTHORIZED and require USER_DECISION evidence for authorized behavior evolution
  - allow Web Brain to record user residual-risk acceptance only when exact risk-bound USER_DECISION evidence exists
  - derive observed impact from the exact current PR review target and consume every change-unit exit condition in Brain Review
  - require evidence-bound rework_delta for Codex/Brain/User blocking outcomes
  - validate Resume Projection schema/digest/project/task/round and exact approval binding before using it

unchanged:
  - single Web Brain
  - single local Codex execution layer
  - user product authority
  - explicit user execution approval
  - separate user acceptance and merge authorization
  - repository as long-term project truth
  - no Skill system
  - no second truth source
  - no automatic promotion

architecture_fit: PASS_NORMAL_REPAIR
minimality_gate: PASS_MINIMAL_NORMAL_REPAIR

---

# Protocol Repair Record — Phase 2R1 Claim Support Relevance

repair_source_package:
  name: JOYFLOW_PHASE2R_SEMANTIC_TRUTH_TRANSPORT_REPAIR_CANDIDATE.zip
  bytes: 996453
  sha256: 9e295cfb42dfb52e13fb48a137dc88bd72ae009243011ee7236358b7181dc61e

root_cause:
  - Phase2R already separated record authorship from authority and checked evidence authority/kind/current-object binding.
  - a remaining task-local gap allowed evidence with the correct authority/kind to be reused for a different material claim subject.
  - the problem is semantic relevance mismatch in a single-user workflow, not user identity or authentication.

repair:
  - add one task-local claim-support relevance rule using existing Evidence Registry subject_type/subject_id
  - bind operating assumptions to OPERATING_ASSUMPTION subjects
  - bind prior behavior source/review to PRIOR_BEHAVIOR and authorized disposition to PRIOR_BEHAVIOR_DISPOSITION
  - bind current-source impact support to the exact IMPACT_DIMENSION
  - bind controlled high-loss risk evidence to the exact RISK
  - bind closed PR exit conditions to the exact EXIT_CONDITION
  - add adversarial regression cases for same-user unrelated decisions, unrelated tests, generic tree snapshots and unrelated exit evidence

unchanged:
  - single Web Brain and single local Codex execution layer
  - user product authority and existing approval/acceptance/merge gates
  - no user identity/authentication/signatures
  - no persistent claim graph or second truth source
  - no Skill system or automatic promotion

architecture_fit: PASS_NORMAL_REPAIR
minimality_gate: PASS_MINIMAL_NORMAL_REPAIR

---

# Protocol Repair Record — Phase 2R2 Cumulative Disposition Prose

root_cause:
  - Phase2C implemented authorized change and supersession correctly in Runtime, but one earlier canonical prose sentence still said every relevant prior behavior must remain preserved.
  - the contradiction could lead Brain/Codex readers to two different interpretations even though the mechanical model already supported legitimate user-authorized evolution.

repair:
  - replace the preserve-all sentence with one rule: every relevant prior behavior closes according to its approved expected disposition
  - retain PRESERVE_REQUIRED / CHANGE_AUTHORIZED / SUPERSEDE_AUTHORIZED unchanged

architecture_fit: PASS_NORMAL_REPAIR
minimality_gate: PASS_MINIMAL_NORMAL_REPAIR

---

# Protocol Repair Record — Phase 2R3 Test Runner Efficiency

observed_failure_basis:
  - the monolithic full-package command can exceed the Web Brain tool execution window even when individual Gates are healthy
  - the old runner starts a new Python process for every eight test methods
  - direct measurement showed a 9-test module fall from about 34 seconds on the old two-batch path to about 22-23 seconds as one module
  - direct measurement also showed that large modules can exceed a module-first window, so unconditional module-first would add cost rather than remove it

repair:
  - use module-first only for bounded modules up to 12 discovered tests
  - keep the existing 8-test batch path for larger modules
  - retain batch fallback for small-module timeout, count mismatch or diagnostics
  - keep real module failure fail-closed even when isolated batches later pass
  - keep exact test discovery count and raw output/exit-code behavior

architecture_fit: PASS_NORMAL_REPAIR
minimality_gate: PASS_MINIMAL_NORMAL_REPAIR

## PR2S5 — Self-hosting reproducibility confirmed repairs

- source candidate: `JOYFLOW_PHASE2R3_TEST_RUNNER_EFFICIENCY_REPAIR_CANDIDATE.zip` / 1021391 bytes / `dea8bac44934f02d3a2524131d707acd82faf2b0699226681a2a5aaf1e965fe9`
- observed confirmed defects: prose phrase used as machine identity gate; CI omitted a required runtime object; Joyflow-owned generated bytes depended on host newline/encoding defaults; raw execution capture digest could lose distinctions after replacement decoding; validation dependencies were undeclared; ordinary unittest skip could hide platform capability N/A.
- repair: reuse existing Manifest/lineage/runtime authority topology; canonical UTF-8/LF/no-BOM helper for Joyflow-owned deterministic text; exact stdout/stderr byte digests; minimal validation dependency declaration; existing `joyflow_repo_check.py` current-PR entry; capability probe plus unexpected-skip block.
- explicitly not repaired: historical Windows Git fixture flake because its root cause remains unknown. No retry and no speculative process-cleanup change.
- architecture_fit: `PASS_NORMAL_REPAIR`
- minimality_gate: `PASS_MINIMAL_NORMAL_REPAIR`
- formal_phase2: `NOT_ESTABLISHED`
- stable_baseline: `NO`

# Protocol Repair Record — Phase 2T Structural Cognition Continuity

## Failure basis

- Current Joyflow can ground current source, allowed paths, technical preflight and Brain review, but material architecture planning may still begin inside a prematurely selected path boundary.
- Codex can propose equivalent routes, but the current default makes the Web Brain the primary producer of candidate technical routes before deep local repository analysis.
- Task-local-only structural understanding is insufficient for stable cross-PR whole-project architecture review; rebuilding the entire structure from scratch on every task increases rediscovery cost and semantic drift.
- A persistent architecture cache/database would over-correct this problem and create a competing truth risk.

## Repair

- keep ordinary path discovery GitHub-first, but allow `MATERIAL_ARCHITECTURE_UNCERTAINTY` to trigger a separately approved read-only Codex structural discovery before final mutation paths are frozen;
- add goal-bound structural discovery fields to `PATH_DISCOVERY_RETURN`;
- bind typed semantic structural relations to direct current-repository path/source snapshot observations;
- require exact question-specific closure coverage and prohibit final route recommendation while any requested dimension is unresolved;
- require task structural folding to preserve all material relation IDs, counterevidence, unresolved questions and material omissions;
- add `LONG_TERM_STRUCTURAL_PROJECTION` as a sparse, derived, non-authoritative, exact-commit/source-byte-anchored repository artifact;
- mechanically assess projection freshness as current, current-for-referenced-sources, stale-relevant-source-changed or conflicted-by-non-ancestor history;
- preserve Brain project-level architecture review/final technical closure and user product/tradeoff/execution/merge authority;
- require original goals to be re-grounded after a structural repair changes the repository object.

## Architecture fit

`ARCHITECTURE_FIT: PASS_NORMAL_REPAIR`

The repair changes information flow and task-local architecture planning responsibility but does not add another Brain/Agent, execution authority, autonomous control plane, automatic approval/acceptance/merge, or competing truth source. Codex produces repository-grounded architecture proposals; Web Brain retains final technical closure.

## Minimality

`MINIMALITY_GATE: PASS_MINIMAL_NORMAL_REPAIR`

The implementation reuses the existing Path Discovery Return, current-source replay, Evidence rows, Brain review, exact Repository anchor and human approval chain. The long-term projection is a sparse repository artifact rather than a Repository Cache or service.

---

# Protocol Repair Record — Phase 2U Structural Cognition Lifecycle Re-closure

repair_source_package:
  name: JOYFLOW_PHASE2T_STRUCTURAL_COGNITION_CONTINUITY_REPAIR_CANDIDATE.zip
  bytes: 1066958
  sha256: 54478064da48e249396616aa0d9d0e266ad56f2aa8231aad7bd88ef7ed283db7

root_cause:
  - `STRUCTURAL_COGNITION_LIFECYCLE_OBJECT_GAP`: structural cognition was implemented as a strong Discovery-side capability but was not one exact task-lifecycle object from Brain question through Final Path, execution review and long-term refold.
  - Brain-owned architecture questions were not mechanically bound, so Codex could narrow/downgrade dimensions.
  - structural closure status did not prove compatible evidence coverage.
  - nested structural unresolved state was not a direct Final Path blocker.
  - Codex architecture proposal, Brain final closure, implementation result and Brain actual structural review lacked exact lineage.
  - long-term projection could self-assert Brain review status.

repair:
  - bind one Brain Structural Decision Frame and require Codex to answer its exact question/dimensions
  - require evidence-compatible semantic relations for CHECKED/N/A closure
  - make closed structural state and exact Brain ACCEPT disposition a direct Final Path prerequisite
  - bind structural planning mode and Codex route lineage into the mutating Handoff
  - require Codex structural execution result and exact Brain consequence disposition/refold decision
  - remove self-asserted Brain review status from long-term structural projections
  - realign structural rules across existing Project Source authority domains instead of creating a parallel architecture system

unchanged:
  - single Web Brain
  - single local Codex execution layer
  - repository as long-term fact source
  - user product/protocol authority
  - HISTORICAL_AT_PR2U_TIME: explicit user approval Gate for Codex read-only structural discovery
  - user mutation execution approval
  - applicable user acceptance
  - final user merge authorization
  - inherited Windows Git fixture and cross-platform replay blockers

architecture_fit: PASS_NORMAL_REPAIR
minimality_gate: PASS_MINIMAL_NORMAL_REPAIR

project_instruction_change_note:
  HISTORICAL_AT_PR2U_TIME: the user requested removal of the separate approval Gate for bounded pure read-only Codex structural discovery. At that stage it required a complete replacement Development Project Instruction and was not activated by the normal repair package.

## PR2V — Historical read-only Discovery authorization alignment

HISTORICAL_REFERENCE_ONLY: PR2V implemented candidate semantics in which Web Brain authorizes an exact bounded pure read-only discovery object without a separate user approval state, while mutation/material execution still requires explicit user approval. Earlier PR2V prose overstated activation before the replacement Development Instruction was actually confirmed. That historical claim is not current authority. The current Compact V2 Development Project Instruction has since been explicitly confirmed by the user and now authorizes that bounded pure read-only Discovery.

## PR2W Ephemeral GitHub Evidence Transport

This candidate adds no new Evidence authority or database. It adds an optional exact-object transport adapter for the existing current-round Evidence Bundle, requires any GitHub Evidence write to be inside the exact user-approved mutation/material execution object, keeps product/governance changes on their normal PR/merge chain, and makes transport Evidence ephemeral by default with exact preauthorized terminal cleanup and no background service.

---

# PR2X Architecture Convergence & Closure Repair

repair_source_review_target:
  name: JOYFLOW_PHASE2W_EPHEMERAL_GITHUB_EVIDENCE_TRANSPORT_REPAIR_CANDIDATE.zip
  bytes: 1106194
  sha256: 7a21e27a9445646c08e05ce7c9de4a6c1d3b2cc30799701126ae5b6bf7c1d053

current_authority_correction:
  Historical PR2V/PR2W package prose is not authority for the current review. The user has explicitly confirmed and installed the Compact V2 Joyflow Development Project Instruction. Under that current authority, Web Brain may authorize strictly bounded pure read-only Technical Discovery without a separate user approval; mutation/material execution approval remains user-owned. The Development Instruction itself is external to this Runtime/Project Sources package.

repairs:
  - six-stage conceptual mainline without adding a new execution authority
  - conditional typed Technical Discovery
  - stable mutation execution envelope approval binding
  - same-envelope bounded rework without renewed mutation approval
  - user-owned product tolerance boundary
  - contextual risk / proportional assurance with retained hard floors
  - active GLOBAL_INVARIANT residual-waiver block
  - exact canonical Evidence Bundle transport bytes
  - dedicated positive Evidence namespace
  - generic task-terminal cleanup without a daemon
  - real Web Brain / Local Codex role-executability and exact manual fallback
  - active Compact V2 activation state consistency across lineage and Machine Model
  - cycle/attempt semantic migration so same-envelope implementation rework does not create a new approval cycle
  - merge-chain convergence: exact Freeze before applicable Acceptance and final USER merge authorization; `MERGE_READY` / `MERGE_ALLOWED` are derived Gate results; Merged Change Projection is conditional post-merge navigation only
  - R4 primary-Capsule closure: Brain Review PASS is sealed before Freeze creation; repository `USER_ACCEPTANCE` / `MERGE_DECISION` require the exact freeze digest binding; the primary derived `merge_gate` cannot emit `MERGE_READY` without that binding

explicit_non_goals:
  - runtime module split in this repair
  - physical deletion of DEVELOPMENT compatibility aliases
  - broad rule-registry compression
  - autonomous Brain-to-Codex invocation
  - background cleanup or rework loop

architecture_fit: CURRENT_DEVELOPMENT_INSTRUCTION_AUTHORITY_ALIGNED
minimality_gate: PASS_MINIMAL_NORMAL_REPAIR_FOR_ALL_NON_AUTHORITY_CHANGES
