# JOYFLOW PHASE 1 COMBINED CAPABILITY COVERAGE REPAIR CANDIDATE BOOTLOADER

status: PHASE1_REPAIR_CANDIDATE_NOT_BASELINE

For a Joyflow task:

1. Keep the authority topology fixed: one Web Brain, one local Codex execution layer and user-controlled execution, acceptance and merge decisions.
2. Each project has one current task per material reclosure / authorization cycle. A same-envelope implementation rework stays in that cycle as a new execution attempt with current Projection, Codex Return and Evidence Bundle revisions; only a material change to product semantics, scope, active invariant, important tradeoff or authorization boundary opens a new approval cycle. The Web Brain owns this sequencing rule; do not add a global scheduler or multi-task control plane.
3. Treat repository merged artifacts as durable project facts and Task Capsules, Prompts, Returns and review records as temporary activity state.
4. Use digests and exact object binding to prevent ordinary packet, round and evidence mismatch; do not claim identity authentication, immutable history or hostile-tamper resistance.
5. Ordinary path discovery is Brain-accessible-current-repository-evidence-first: the Web Brain uses exact repository, PR, commit, diff and file evidence that it can actually access. When that evidence is insufficient/unavailable, local/runtime facts are materially required, or a material architecture question cannot be safely closed before local repository analysis, Brain may issue a bounded local read-only Codex discovery Prompt. Under the current active Development Project Instruction, this pure read-only discovery needs no separate user approval. Any later mutation/material execution still requires explicit user approval of the newly closed mutation execution envelope. Logical authorization remains an explicit human-semi-automatic handoff, not automatic Local Codex invocation.
6. Final repository-relative `allowed_paths` are always decided by the Web Brain and bound to user approval. Codex discovery may report paths but may not authorize them or mutate files.
7. The Web Brain may record `APPROVED_FINAL` only after the user explicitly approves the exact current approval view and Projection. Runtime validates the binding but does not create the decision.
8. Codex receives one complete Prompt containing its bounded technical-authority contract and performs technical preflight internally in the same execution turn.
9. Codex may choose equivalent implementation details only inside approved product semantics and paths. A Brain-route conflict, insufficient approved paths or repository-reference mismatch must stop with a source-bound technical objection.
10. A completed Codex Return must cover every required machine check, contain only PASS with exit code zero and have no unresolved item. A truthful `BLOCKED` Return may omit PR or artifact evidence but must include blocker Evidence, unresolved items and mutation/cleanup state. Codex leaves Brain review, user acceptance and merge authorization pending.
11. Brain review may not promote an exact source Return whose execution status is `BLOCKED` to `PASS`.
12. Derived Gates are actual blockers: Brain review requires the current Return/Bundle. For repository merge, Brain Review PASS + current PR CI PASS first produce the exact Merge Candidate Freeze; applicable User Acceptance then binds that exact freeze, and the separate final user merge authorization binds both. Derived gate results do not replace those user decisions.
13. Repository execution is reviewed against a PR head. Non-repository Artifact execution is reviewed against artifact identity, digest and validation evidence and must not fabricate PR fields.
14. Execution approval never authorizes merge. The exact Merge Candidate Freeze binds the reviewed PR head; applicable User Acceptance binds that freeze; final USER merge authorization binds the same freeze and acceptance disposition. `MERGE_READY` / `MERGE_ALLOWED` are optional derived Gate results, not required predecessor lifecycle objects.
15. Joyflow performs no automatic approval, acceptance, merge or promotion. Repository completion is recorded only after Brain reviews current merge evidence.
16. Typed GitHub path evidence binds the exact GitHub object type, canonical observed-path scope and raw-object digest. A file object proves only its exact file.
17. Every local discovery path, dependency, validation entry and finding has a stable ID and compatible typed Evidence. A generic Git-state snapshot cannot prove those facts.
18. A local or combined final path names the exact confirmed Return path IDs that support it. Unresolved local questions block final mutating closure.
19. Codex captures distinct BEFORE and AFTER worktree states with the repository-owned deterministic capture helper; equal state fingerprints support the read-only claim.
20. Technical preflight records the approved expected repository reference separately from the actually observed reference and binds both to typed current-object Evidence.
21. `ROUTE_CONFIRMED` requires typed repository-reference and assumption-check Evidence. Every blocker uses a status-specific typed finding whose normalized claim matches the declared conflict.
22. `APPROVAL_SCOPE_INSUFFICIENT` may propose only paths outside the current approved boundary; it never expands Codex authority.
23. Any PR Evidence binds an exact non-empty changed-path set and coherent mutation, residual and cleanup state.
24. A no-PR `BLOCKED` Return is reviewed only as the exact `BLOCKED_EXECUTION_RETURN`; Brain may not invent or retain a PR target, machine result or PASS verdict.

Hard stop when:

- GitHub evidence is skipped without a stated reason, Codex discovery is requested by default, or typed GitHub evidence is not bound to its exact observed scope and raw object;
- local discovery mutates files, creates a commit or PR, decides final allowed paths, reuses one capture as both BEFORE and AFTER, or returns untyped/mismatched local Evidence;
- a prior round, packet, Return or Evidence Bundle is substituted for the current one;
- a BLOCK or NEEDS Gate is bypassed by advancing the task stage;
- Codex continues after a technical preflight conflict, expands approved paths, changes product semantics, or claims an equivalent adjustment without recording the implementation decision;
- a `COMPLETED` Codex Return contains a failed/not-run check, nonzero PASS exit code or unresolved item;
- a `BLOCKED` Return lacks direct blocker Evidence, unresolved items, coherent mutation/cleanup state, or invents completion evidence;
- Brain review marks a `BLOCKED` source Return as `PASS`;
- Brain records user-owned approval without a current explicit user decision;
- Codex fills Brain review, user acceptance, merge approval or repository-result state;
- an Artifact task fabricates PR evidence or a repository task lacks PR-head evidence;
- a final USER merge authorization is absent, is bound to another Merge Candidate Freeze / acceptance disposition, or is reused after the PR head changes;
- a Task Capsule is treated as a second persistent project truth source;
- expected and observed repository refs are conflated, route confirmation lacks typed assumption Evidence, or a blocker cites a generic unrelated Evidence row;
- a scope-gap finding requests a path already covered by approved `allowed_paths`;
- PR Evidence exists while mutation is denied, the changed-path set is empty or does not match the typed Diff claim, or blocked residual/cleanup state contradicts the current Diff;
- a blocked Return without completion Evidence is reviewed as a PR or Artifact, a blocked review invents machine results, or Brain promotes it to PASS;
- any interface claims automatic promotion, trusted identity proof or immutable event history.

25. For ordinary bounded implementation the Web Brain may provide exact critical preflight questions and one to three non-exhaustive candidate routes. For material architecture uncertainty, Brain instead frames the product/technical question and preserved boundaries; Codex read-only discovery is the primary producer of repository-grounded architecture candidates/recommendation, while Brain performs project-level review and final technical closure. Neither route candidates nor Codex recommendations authorize mutation paths.
26. In mutating execution Codex must answer every applicable Brain preflight obligation, evaluate every approved candidate route when candidates were supplied, and may select a candidate or a demonstrably equivalent alternative only when product semantics, approved paths, compatibility, migration and important tradeoffs remain unchanged. In Brain-authorized bounded pure read-only structural discovery Codex may generate architecture candidates but cannot self-approve them, create user approval state, mutate, or freeze final mutation paths.
27. Every technical observation, obligation result, route evaluation, selected route, blocker and machine result binds a preserved tool capture containing the actual command, exit code, stdout, stderr, observed object and SHA-256.
28. Existing Artifact repair binds the exact source artifact ID and SHA-256. A new or changed Brain review source can be sealed only with the exact Projection, Codex Return and Evidence Bundle together.

Additional hard stops:

- Codex substitutes unrelated self-selected checks for the Brain preflight obligations, omits a candidate evaluation, or declares a blocking status without the corresponding failed dimension;
- Codex labels an alternative equivalent while expanding paths, changing product/protocol behavior, introducing migration or compatibility commitments, or changing an important tradeoff;
- an execution Evidence row lacks a preserved tool capture, does not match the capture subject, or its raw bytes digest does not match;
- an Artifact route uses a generic `artifact:current` identity rather than the exact approved source artifact or explicit new-artifact source materials;
- Brain creates or changes an execution review source without supplying the exact Projection, Return and Evidence Bundle.

29. Every Brain preflight obligation uses the canonical question for its dimension and binds exact current task subjects, routes, semantics, non-goals, validation duties or approved path decisions; a generic non-empty question is insufficient.
30. A candidate route may be evaluated `PASS` or selected only when all required expected paths are inside the user-approved path boundary.
31. Repository and Artifact identity, file, Diff and test observations are direct typed tool facts. Product-semantic, non-goal, route-feasibility, selection and objection conclusions are explicit Codex derivations that cite those facts; they are not direct observations.
32. Test-command facts used by preflight or route evaluation must match a command in the approved validation plan. Route, product, non-goal and path conclusions require a structural current-object fact.
33. An execution-object mismatch stops before route evaluation: remaining obligations are `NOT_APPLICABLE`, candidates are `NOT_EVALUATED`, no route is selected and execution returns for Brain re-closure.
34. All source-derived Brain Review content is covered by one source snapshot digest. Any later change to Review target, source machine results, unresolved items or source status requires the exact Projection, Return and Evidence Bundle to be supplied and compared again.

Additional hard stops:

- a Brain preflight question or subject binding does not match its current task dimension;
- a passing or selected candidate requires any path outside approved `allowed_paths`;
- a semantic or route conclusion is presented as a direct tool observation instead of a Codex derivation from typed current-object facts;
- a test capture used in preflight does not match the approved validation command set;
- route evaluation continues after the observed repository or Artifact differs from the approved execution object;
- later Brain Review edits replace source-derived machine Evidence or unresolved state without re-supplying and comparing the exact source trio.

## Current-source replay repair boundary

For material execution, do not trust a capture merely because its structure, tool label and digest are self-consistent. The operational runtime must reread the supplied repository or exact Artifact, replay deterministic path/object/Diff facts and rerun approved test commands. Brain and Codex may derive technical conclusions from replayed facts but may not promote unreplayed records into direct facts. Structural fixture sealing is test/example-only.

## Current narrow repair additions

- A `PR_DIFF` observation is valid only for the actual changed paths of its exact `base...head` pair.
- TOOL direct facts cover path existence and bounded bytes; dependency, relevance, validation-entry and route meaning remain Codex derivations.
- Read-only fingerprinting includes only exact task-declared ignored/runtime paths and never claims full filesystem coverage.
- Approved validation is bound to exact argv plus `SOURCE_ROOT`; display text is derived.
- Operational Codex Return and Brain Review validation cannot disable approved test replay.

34. Local or combined execution must bind the exact original read-only Discovery Projection, exact Return and exact selected item IDs through a formal Discovery Source Object.
35. Ignored exact symlinks are inspected without following their targets; recursive exclusions prune subtrees before read; only explicitly declared ignored entries enter the local direct-fact set.
36. Artifact completion uses one canonical complete output set. Actual output files, Return, final validation and Brain Review must have exact set equality.
37. Every required Artifact output needs exact digest Evidence and applicable output-targeted validation; source input validation cannot substitute.
38. `NEW_ARTIFACT` binds an approved exact source-material set and produces a complete output set; it never fabricates an existing source Artifact.


## Inherited PR1A + PR1B validation-workspace closure repair

The prior frozen candidate correctly protected declared lifecycle files but did not close the actual validation workspace object set. A Repository validation command could add an untracked or ignored object inside the detached Base or result-Head worktree, and an Artifact validation command could add an undeclared file beside the approved input or outputs, while operational verification still accepted the old result identity. A second public-entry counterexample showed that a linked Git worktree could also change shared refs or object administration while HEAD, Diff and checked-out files remained equal.

This repair keeps the existing short-lived Validator and extends the same observation-only comparison to the complete lexical object set beneath every actual validation working directory. Repository replay uses disposable Git-administration-isolated shared-object clones rather than linked worktrees; the complete clone tree, including local `.git` administration, is sealed before and after each command, while the authoritative repository remains unchanged. Repository routes record tracked, untracked and ignored files, directories, symlink objects and other entries without following symlinks. Artifact routes additionally require one explicit real dedicated output root: every declared output is one direct regular-file child, source inputs and source materials remain outside it, and the root's complete object set must equal the sealed output set before replay and remain unchanged afterward. Any pre-existing undeclared object, addition, deletion, replacement or content change blocks validation and returns the task to execution for a new result identity. At the historical PR1A + PR1B freeze, the runner used sequential module execution and the recorded scope was 153 tests. This is historical scope only; current test count and exit-code granularity come from the current frozen package validation evidence.

The exact repair source is `JOYFLOW_PHASE1B_PR1A_PR1B_SEALED_OBJECT_CONSUMPTION_REPAIR_CANDIDATE.zip` with 750119 bytes and SHA-256 `9fb81fcef640411a65d8a6de46a6852752f017c9401467fd2f9a797e4d5b2189`. The source package remains unchanged.

The repair adds no persistent observer, background service, repository cache, identity system, second authority, automatic approval, acceptance, merge or Promotion. It remains a repair candidate, not a baseline or release, and independent stranger cold review of this new frozen object has not been performed.

At the historical PR1A + PR1B freeze, the mechanical scope was 153 tests, 229 unique Project Source rules, 95 mechanical invariants and 176 legacy migration rows. Later accumulated stages are defined below and by the current exact package Model.

## Inherited PR1E AI-native change-projection repair

39. The merged change projection is a navigation and context-recovery view only. It binds the exact current PR identity, complete current Diff path set, Projection, Codex Return, Evidence Bundle, Codex block and Brain Review Capsule, but it never substitutes for current repository bytes, Diff, tests or source Evidence.
40. The public PR CI replays the exact current PR/review execution chain and current repository Diff without consuming a Merged Change Projection. A navigation-only Merged Change Projection is never a mandatory pre-merge Gate and cannot substitute for current source replay.
41. Brain Review PASS plus current PR CI PASS first produce the exact Merge Candidate Freeze. Applicable User Acceptance then binds that exact freeze; only after that may `MERGE_READY` be derived. This derived state is not merge authorization and does not require a Merged Change Projection.
42. Final merge authorization is a separate explicit USER-owned decision bound to the exact Merge Candidate Freeze and applicable post-freeze User Acceptance. `MERGE_READY` / `MERGE_ALLOWED` may only be derived diagnostic results; neither Brain, Codex nor Tool creates or substitutes the USER decision.
43. A completion pointer records only an already observed repository merge and binds the exact Merge Candidate Freeze, applicable User Acceptance and final USER merge authorization. It does not require standalone `MERGE_READY` / `MERGE_ALLOWED` objects. A Merged Change Projection, when useful for long-term navigation/context recovery, is conditional post-merge derived state and is never a pre-merge Gate.
44. All model-derived Schemas, registries, base examples and PR1E examples are regenerated by the same current-model generation entry before package validation. A mixed model version or stale generated byte blocks the candidate.

Additional hard stops:

- a merged change projection is used as repository fact authority or omits any current changed path;
- the PR body, PR CI or freeze silently substitutes another approved execution Projection, Return, Evidence Bundle, Brain Review or Head, or makes a Merged Change Projection a pre-merge prerequisite;
- a USER merge authorization is absent, Brain-owned, or bound to another freeze;
- a completion pointer is accepted without the exact freeze + applicable acceptance + final USER merge authorization binding, or a post-merge navigation projection is made a pre-merge prerequisite;
- generated assets or examples belong to another Model version;
- any interface performs automatic approval, acceptance, merge or Promotion.

The exact parent for this stage is `JOYFLOW_PHASE1D_REVIEW_ACCEPTANCE_FREEZE_REPAIR_CANDIDATE.zip`, 871831 bytes, SHA-256 `e527513547d7275f73ed3ef4a9928cef240c2b4f6af3f81b65242942596e45c9`. This candidate remains non-baseline and non-release.


## Current PR1F legacy semantic-mapping binding repair

45. Every legacy migration binds an exact historical source filename, byte count, SHA-256 and section identity. A digest-and-section binding without the exact section text is not replayed semantic evidence.
46. Legacy-to-current semantic relations are supplied by a separately sealed `WEB_BRAIN` mapping object. Generators and Validators may consume and verify this object but may not author or modify its interpretation.
47. `BEHAVIORALLY_VERIFIED` requires the composite Gate: exact legacy section text verified, Web Brain mapping status `CONFIRMED`, semantic relation `FULLY_PRESERVED`, and behavior-level evidence for every current target bound to the same claim subject.
48. Current-target tests prove only current targets. With exact legacy text unavailable, active rows remain `MAPPED_ONLY`; deferred and retired rows never claim equivalence.
49. Capability IDs, subjects, statuses and verification refs exactly match the capability claim registry. Evidence strength alone cannot support another claim subject.
50. Strict Schemas for source identity, Brain mapping, migration rows, verification registry, capability registry and capability status run before semantic validation. Unknown fields, wrong types and invalid statuses block.
51. This package cannot assign itself independent cold-review confirmation, baseline, release, merge authorization or Promotion.

Additional hard stops:

- a derived legacy summary is treated as exact old-source text;
- a current-target behavior test is used to prove unavailable legacy meaning;
- a generator authors or silently rewrites Web Brain semantic mapping;
- any active row claims equivalence while exact legacy section text is unavailable;
- strong evidence is reused for an unregistered capability subject;
- migration input or output bypasses strict Schema validation;
- an unresolved test, command or policy reference is used as evidence;
- any interface performs automatic approval, acceptance, merge or Promotion.

## Legacy semantic mapping binding repair

```yaml
repair_source_package:
  name: JOYFLOW_PHASE1F_MIGRATION_CLAIM_TRUTHFULNESS_REPAIR_CANDIDATE.zip
  bytes: 910391
  sha256: c450fd8cfab8440f282e55b36774721908d29902d9be6ba0e3b0ef2172ff9f2b
legacy_source_bytes_bundled: NO
brain_semantic_mapping_owner: WEB_BRAIN
mechanical_generator_may_author_mapping: NO
current_legacy_behavioral_equivalence_claims: 0
```


## Current PR1F instance / transition evidence-outcome repair

52. The frozen 176-row migration instance and reusable confirmed-semantic transition capability are separate lifecycle objects. Fixture evidence cannot become current historical evidence.
53. Current exact-source-unavailable rows remain `NOT_EVALUATED / MAPPED_ONLY`; this repair does not change any current disposition fact.
54. Confirmed-semantic transition coverage uses one isolated test-only exact source fixture and the same public source-binding, Brain-mapping, disposition and migration-generation path.
55. Exact fixture confirmation requires actual file bytes, byte count, SHA-256, uniquely marked section extraction, section SHA-256, a resolvable Brain semantic-evidence reference and existing current target rules.
56. `DISPOSITION_TRANSITION_CONTRACT` defines every legal authority transition and every allowed `(semantic evidence, behavior evidence)` outcome, including exact migration status and equivalence-claim value.
57. Migration derivation consumes the declared contract outcome directly. Carry-forward may not retain independent hard-coded result semantics.
58. Positive tests cover public-path confirmed technical retirement and carry-forward complete/incomplete behavior outcomes. Tampered bytes, wrong section digest and missing source root must block.
59. User decision remains sparse and boundary-focused. Brain may close technical decisions that preserve confirmed direction; changed product direction still requires a current user decision.

Additional hard stops:

- a test-only fixture is treated as evidence for any of the 176 current legacy rows;
- confirmed mapping is accepted without actual source bytes, file SHA, exact section digest or Brain semantic-evidence reference;
- a positive transition test bypasses the public mapping/disposition/generation path;
- derivation or tests maintain carry-forward result rules outside the shared evidence-outcome contract;
- the repair changes any current `NOT_EVALUATED` row without a new exact Brain or user decision object;
- any interface performs automatic approval, acceptance, merge or Promotion.

```yaml
repair_source_package:
  name: JOYFLOW_PHASE1F_INSTANCE_TRANSITION_EVIDENCE_OUTCOME_REPAIR_CANDIDATE.zip
  bytes: 975823
  sha256: e752a70c1e86992665bd9f229e9a690ea54ef45be59a00a8ffdf55b6bdb57895
architecture_fit: PASS_NORMAL_REPAIR
minimality_gate: PASS_MINIMAL_NORMAL_REPAIR
```

## Current provenance object binding repair

The top-level legacy source set is the only source-set identity authority. Mapping rows cannot independently author that identity. Confirmed semantic evidence is bound by exact package-relative file and unique section digests, while semantic sufficiency remains with Web Brain. Deferred migration status is neutral and the exact basis remains in the disposition object.


## Current PR1F confirmed-transition boundary repair

60. The public confirmed-semantic transition path verifies the exact source set, Brain mapping seal, disposition seal and capability registry together before returning a short-lived validated input object. Raw mapping or disposition objects cannot enter migration derivation.
61. Bundled exact source bytes use one package-relative source root included in the source-set digest. The root must resolve inside the current frozen package; unbundled current legacy sources declare no source root.
62. Exact legacy and Brain semantic-evidence sections require one start marker followed by one end marker with non-empty content. Missing, duplicated, reversed or empty boundaries block.
63. The top-level Brain mapping status is mechanically derived from row states and cannot be independently overstated.
64. Internal renderers may consume only `ValidatedTransitionInputs`; validation remains a short-lived mechanical boundary and does not create a new durable authority or control plane.

Additional hard stops:

- a raw or independently re-digested mapping or disposition object bypasses its Brain-owned Seal;
- exact source bytes are claimed as package-bundled while the declared source root is absent, outside the package or mismatched;
- a reversed or empty section is accepted as exact source or semantic evidence;
- top-level mapping status conflicts with row-level mapping states;
- a short-lived validated input object is promoted into a persistent truth source or autonomous control layer.

```yaml
repair_source_package:
  name: JOYFLOW_PHASE1F_CONFIRMED_TRANSITION_BOUNDARY_REPAIR_CANDIDATE.zip
  bytes: 989316
  sha256: f3f8fe65cfc99715a0e56fbf4cdd2a8157ad9f81e75f14b9c8a021b1ca0f2c29
architecture_fit: PASS_NORMAL_REPAIR
minimality_gate: PASS_MINIMAL_NORMAL_REPAIR
```


## Structural cognition continuity addendum

64. A material architecture question uses goal-conditioned Codex read-only discovery before final mutation-path freeze. Codex derives typed semantic relations from direct current-repository path/source observations, covers each requested closure dimension exactly once, and may recommend a route only when no requested dimension remains unresolved.
65. Structural relation transport is semantic, not ID-only: relation type, subject, source, semantic claim, materiality and direct evidence basis must remain bound together.
66. The task structural projection must preserve all material relations, counterevidence, unresolved structural questions and material omissions. Brain may request targeted re-unfolding to exact repository observations.
67. A repository may retain a sparse `LONG_TERM_STRUCTURAL_PROJECTION` for cross-task architecture continuity. It is derived/non-authoritative, anchored to exact commit/source bytes, updated only for material structural changes and always subordinate to current repository facts.
68. If current HEAD changes a referenced structural-projection source, that projection is stale for current use; if its based-on commit is not an ancestor, it is conflicted. Stale/conflicted projections may navigate discovery but cannot prove current structure or authorize paths.
69. Codex owns repository-grounded architecture discovery, root-cause diagnosis, candidate generation and technical recommendation. Web Brain owns whole-project architecture review and final technical closure. User retains product/protocol/important-tradeoff decisions, execution approval and final merge authorization.
70. A shared structural root cause blocks the current Feature only when the Feature depends on it, would duplicate/worsen it, or cannot honestly be absorbed without repair. Unrelated legacy architecture debt remains non-blocking. After a Structural Repair merge, the original goal must be re-grounded against the new repository state; stale route/path/approval objects cannot be reused.


## Architecture Convergence Candidate Addendum

- Logical authorization does not imply automatic Local Codex invocation. Web Brain → Local Codex handoff remains user-mediated or uses another explicitly available transport; no background Joyflow controller or mandatory connector is assumed.
- User mutation approval binds the stable product/scope/invariant/consequence/minimum-validation/stop-condition execution envelope, not one transient implementation attempt. Same-envelope implementation rework does not require renewed mutation approval; a material envelope change does.
- Product tolerance is user-owned. Brain/Codex may identify technical consequences but may not invent acceptable downtime, data loss, recovery burden or other material tradeoffs.
- Active GLOBAL_INVARIANT requirements cannot be waived through residual-risk acceptance; changing an invariant requires explicit product reclosure.
- Large/complex GitHub Evidence transport carries the exact canonical Evidence Bundle bytes under the dedicated `refs/heads/joyflow-evidence/` namespace, with task-terminal bounded cleanup and no background cleanup service.
