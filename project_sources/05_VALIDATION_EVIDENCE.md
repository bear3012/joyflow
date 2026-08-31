# Validation and Evidence

canonical_rule_id: JF_DL_RISK_ROUTE_SELECTION_RULE
source_section_id: 05::RISK_ROUTE_SELECTION

Every active semantic item and technical decision explicitly classifies risk markers and domain lanes. Minimum route follows risk nature across repository and protocol artifacts; changing `change_scope` cannot bypass Protected Core, protocol-source or compiler risk.

canonical_rule_id: JF_DL_CLASSIFICATION_REVIEW_RULE
source_section_id: 05::CLASSIFICATION_REVIEW

Before route selection closes, Brain reviews active meanings and typed effects for risk and domain classification and records its basis. Mechanical validation checks the declared result; it does not pretend to infer unstated semantics.

canonical_rule_id: JF_DL_SEMANTIC_EFFECT_TRANSPORT_RULE
source_section_id: 05::SEMANTIC_EFFECT_TRANSPORT

High-fidelity transport uses typed semantic effects. Boundary obligations, validation cases and validation obligations are exact digest-bound projections, not independently rewritten summaries.

canonical_rule_id: JF_DL_REPOSITORY_EXECUTION_READINESS_RULE
source_section_id: 05::REPOSITORY_EXECUTION_READINESS

Repository mutation requires at least one confirmed repository-relative allowed path, a non-default working branch, exact baseline binding, route-specific fact slots and no blocking repository question. The Web Brain first inspects GitHub. Only materially missing local/runtime facts route to bounded Codex read-only discovery; final allowed paths remain a Brain decision. Fact slots store bounded claims and references only; they do not form Repository Cache.

canonical_rule_id: RULE_EXISTING_PR_REPLAY_STATE_PRESERVATION
source_section_id: 05::EXISTING_PR_REPLAY_STATE_PRESERVATION

Existing frozen PR replay is observation-only and carries typed before/after repository-state observations. Head, index Diff, worktree Diff, tracked source set, untracked manifest and task-declared ignored-path coverage must remain identical, while the replay evidence must exactly cover the bound repository, PR, Base, Head and complete Base-to-Head changed-path set. Replay evidence and current-round PR mutation evidence are mutually exclusive.

canonical_rule_id: JF_DL_EVIDENCE_AUTHORITY_COMPATIBILITY_RULE
source_section_id: 05::EVIDENCE_AUTHORITY_COMPATIBILITY

Evidence authority is limited to `USER_DECISION`, `REPOSITORY_EVIDENCE`, `EXECUTION_EVIDENCE` and `BRAIN_DERIVATION`. Each record names its producer role and exact subject. User decisions may be recorded only as user-owned decisions; execution evidence must come from Codex/tool return; Brain review is Brain-owned. This enforces ordinary responsibility boundaries, not identity authentication.

canonical_rule_id: JF_DL_EXCLUSION_LOGIC_RULE
source_section_id: 05::EXCLUSION_LOGIC

Excluded material needs a structured independence proof backed by registered evidence. Material connected to active work through dependency, effect, validation, failure, conflict or preservation relations cannot be excluded.

canonical_rule_id: JF_DL_VALIDATION_CLOSURE_RULE
source_section_id: 05::VALIDATION_CLOSURE

Every active material meaning requiring validation produces one stable validation obligation. Codex returns exact required machine commands, independent exit codes and raw stdout/stderr references tied to the matching obligation. Codex cannot mark human validation, Brain review or user acceptance complete. Brain and user complete those later gates from current raw materials.

canonical_rule_id: JF_DL_MECHANICAL_WALKTHROUGH_RULE
source_section_id: 05::MECHANICAL_WALKTHROUGH

Before executable projection, every active semantic item receives a literal walkthrough linking meaning digest, typed effects, boundary obligations, validation cases, user-visible preview and unresolved execution details. Unspecified material details block projection.

canonical_rule_id: JF_DL_ADVERSARIAL_REVIEW_RULE
source_section_id: 05::ADVERSARIAL_REVIEW

Strict and protocol routes require evidence-backed adversarial coverage. Scope expansion, semantic omission, failure path and evidence gap cannot all be marked not applicable.

canonical_rule_id: JF_DL_EVIDENCE_REGISTRY_RULE
source_section_id: 05::EVIDENCE_REGISTRY

Every provenance, transition, exclusion, repair, risk-control, validation result and review reference resolves to a bounded Evidence Registry record containing authority, kind, producer, subject, claim and applicable raw-output reference. A summary or self-declared PASS cannot substitute for the current raw evidence required by the task.

canonical_rule_id: JF_DL_CURRENT_ROUND_EVIDENCE_BUNDLE_RULE
source_section_id: 05::CURRENT_ROUND_EVIDENCE_BUNDLE

Codex returns a digest-bound `CODEX_EXECUTION_EVIDENCE_BUNDLE` for the current `project_id`, `task_id`, round, Capsule and Projection. The Codex Return binds that bundle digest. Brain review records the exact Projection, Return and bundle digests used for the current round. This is ordinary object consistency against stale or mismatched files; it is not an immutable evidence database.

canonical_rule_id: JF_DL_CODEX_RETURN_COHERENCE_RULE
source_section_id: 05::CODEX_RETURN_COHERENCE

A `COMPLETED` Codex Return covers every required machine validation path, has only PASS results with exit code zero and has no unresolved item. A `BLOCKED` return names at least one blocker. Every machine evidence record binds the exact `obligation_id + check_id`, command and raw output reference. Codex still leaves Brain review, user acceptance and merge authorization pending.

canonical_rule_id: JF_DL_EVIDENCE_CONTENT_COMPATIBILITY_RULE
source_section_id: 05::EVIDENCE_CONTENT_COMPATIBILITY

Evidence validity requires compatible authority, kind, subject, current object and exact claim content. Existence of an Evidence ID or a digest does not allow a repository-state snapshot to prove a path, a path observation to prove a dependency, or a historical Return to prove an unrelated final boundary.


canonical_rule_id: RULE_CODEX_TECHNICAL_OBJECTION_EVIDENCE
source_section_id: 05::CODEX_TECHNICAL_OBJECTION_EVIDENCE

A Codex technical objection binds the exact approved repository or artifact reference, explicit conflicting assumptions, direct execution Evidence, minimum correct route, any required additional repository paths, unresolved items, and mutation/cleanup state. Evidence IDs alone do not prove the objection; they must remain current execution evidence with raw-output references.

canonical_rule_id: RULE_EXECUTION_RAW_CAPTURE_BINDING
source_section_id: 05::EXECUTION_RAW_CAPTURE_BINDING

Every execution Evidence row used for technical preflight, route selection, blockers, validation, PR Diff or Artifact result binds one preserved tool capture. The capture contains the exact command, independent exit code, stdout, stderr, observed execution object, subject and SHA-256. Codex may interpret the capture but may not replace it with a self-authored raw-output reference. This is a short-lived current-task evidence mechanism, not a trusted observer or immutable evidence service.

canonical_rule_id: RULE_TECHNICAL_PREFLIGHT_EXACT_OBLIGATION_COVERAGE
source_section_id: 05::TECHNICAL_PREFLIGHT_EXACT_OBLIGATION_COVERAGE

The Web Brain defines the critical preflight questions as typed obligations. Codex must return exactly one result for every obligation and may not substitute unrelated checks. `ROUTE_CONFIRMED` requires every blocking obligation to PASS. Each blocking status requires a FAIL in its corresponding dimension: object identity, route-assumption validity or path sufficiency.

canonical_rule_id: RULE_TYPED_DIRECT_FACT_AND_CODEX_DERIVATION_SEPARATION
source_section_id: 05::TYPED_DIRECT_FACT_AND_CODEX_DERIVATION_SEPARATION

Repository head, Artifact SHA-256, repository file, repository Diff and test-command results are typed direct tool facts. Product-semantic preservation, non-goal preservation, route feasibility, route selection, equivalent alternatives and technical objections are Codex technical derivations that cite compatible direct facts. A semantic or route conclusion cannot be presented as a direct observation, and every test-command fact used by preflight must match the approved validation command set.

canonical_rule_id: RULE_DIRECT_FACT_SOURCE_REPLAY
source_section_id: 05::DIRECT_FACT_SOURCE_REPLAY

A typed direct fact is accepted for material execution only when the current short-lived Validator re-observes the exact repository or Artifact source and reproduces the claimed deterministic fact. Capture JSON, producer labels and self-consistent digests alone prove only record integrity. Repository HEAD, file bytes, Diff paths and Artifact SHA-256 are reread from the supplied current source. Codex remains responsible for explicit technical derivations from those facts; it cannot manufacture the facts themselves.

canonical_rule_id: RULE_TEST_RESULT_COMMAND_REPLAY
source_section_id: 05::TEST_RESULT_COMMAND_REPLAY

A test PASS used by execution, technical preflight or Brain review is current only when the Validator or repository CI reruns the exact approved argv in the bound source context and independently reproduces the required process outcome, including the exact expected exit status. The original execution stdout and stderr remain exact raw Evidence whose bytes, previews and digests must retain their full integrity. Replay stdout and stderr are attempt-local diagnostics and are not generically required to be byte-identical to the original capture; materially significant output content must instead be represented by an explicit validation or Evidence contract. A Codex-authored capture that merely claims exit code zero is not sufficient. Replay is a current-task mechanical check and does not create a persistent observer or autonomous approval gate.

canonical_rule_id: RULE_APPROVED_VALIDATION_ARGV_CWD_BINDING
source_section_id: 05::APPROVED_VALIDATION_ARGV_CWD_BINDING

The authoritative approved validation object is the exact argument vector plus the declared source-root working-directory scope. Any displayed command string is deterministically derived from that argv and has no independent authority. Machine results and test captures must match the approved argv and cwd; a matching display string cannot authorize different executed arguments.

canonical_rule_id: RULE_OPERATIONAL_TEST_REPLAY_MANDATORY
source_section_id: 05::OPERATIONAL_TEST_REPLAY_MANDATORY

Operational validation for a Codex Return or Brain Review always reruns the approved validation argv against the supplied current repository or Artifact source. A no-replay option may exist only inside non-authoritative structural fixtures and cannot be exposed by the operational CLI or used to support execution, review, acceptance or merge claims.

canonical_rule_id: RULE_FINAL_VALIDATION_EXACT_RESULT_OBJECT
source_section_id: 05::FINAL_VALIDATION_EXACT_RESULT_OBJECT

Final machine validation is performed against the exact execution result object. Repository validation runs the approved argv in a short-lived Git-administration-isolated validation repository at the result Head; Artifact validation binds the exact output Artifact set. A passing command on the approved input Base or another checkout cannot support the result object.

canonical_rule_id: RULE_EXECUTION_LIFECYCLE_RESULT_BINDING
source_section_id: 05::EXECUTION_LIFECYCLE_RESULT_BINDING

A completed Codex Return carries a digest-bound execution lifecycle result whose approved-lifecycle digest matches the Projection, whose execution result matches the PR Head or Artifact output set, and whose final validation target is that same result. A blocked Return carries no validated result object. Brain Review freezes both lifecycle digests with the source-derived snapshot.


canonical_rule_id: RULE_BOUNDARY_SAFE_OBJECT_RESOLUTION
source_section_id: 05::BOUNDARY_SAFE_OBJECT_RESOLUTION

Every repository-relative object consumed by Path Discovery, ignored coverage, repository snapshotting or validation is resolved component by component with `lstat`. A parent path component may not be a symbolic link. The final component must match the declared type; an explicitly declared final symlink is read as a link object and its target is not followed. A lexical repository-relative spelling alone does not prove that the consumed object remains inside the approved repository boundary.

canonical_rule_id: RULE_OBSERVATION_ONLY_FINAL_VALIDATION
source_section_id: 05::OBSERVATION_ONLY_FINAL_VALIDATION

Execution may create or modify a result before it is sealed. Final validation may only observe the approved input object and sealed execution result. Before replay and after every approved validation command, the short-lived Validator snapshots both the exact lifecycle objects and the complete lexical object set beneath each actual validation working directory. Repository snapshots include tracked, untracked and ignored entries in the isolated Base and result-Head validation repositories, including each disposable local `.git` administration tree. Artifact snapshots include the input and source-material workspaces plus one explicit dedicated output root whose complete direct-child regular-file set must exactly equal the declared result set before replay and remain unchanged afterward. Source inputs and source materials stay outside that output root. Symlinks are recorded by link-object metadata and are never followed. Any added, removed, replaced or changed workspace object invalidates the validation; the task returns to execution, creates a new result identity and reruns downstream validation.

canonical_rule_id: RULE_REPOSITORY_VALIDATION_GIT_ADMIN_ISOLATION
source_section_id: 05::REPOSITORY_VALIDATION_GIT_ADMIN_ISOLATION

Repository final validation must not use a linked worktree that shares writable refs, object administration, logs, config or worktree registration with the authoritative source repository. The short-lived Validator creates a disposable shared-object clone at the exact lifecycle Commit; source objects are read through the clone's alternates file, while every write remains inside the disposable clone. The complete clone tree, including its local `.git` administration, is compared before and after every approved argv. Any ref, index, log, config, local Git-object or checked-out-tree change blocks the old result, and deleting the clone leaves the source repository unchanged.

canonical_rule_id: RULE_IMMUTABLE_REVIEW_SOURCE_SNAPSHOT
source_section_id: 05::IMMUTABLE_REVIEW_SOURCE_SNAPSHOT

Brain Review consumes an immutable source snapshot generated from the exact Projection, Codex Return and Evidence Bundle. Every source Evidence fact and Codex derivation is normalized into the Capsule Evidence Registry and frozen by its canonical row digest. Brain-owned verdicts, findings and explanations remain an overlay; they may cite but may not rewrite, omit or substitute source rows. A source-row change creates a new Review source and requires the exact source trio again.

canonical_rule_id: RULE_SEALED_OBJECT_TRANSITION
source_section_id: 05::SEALED_OBJECT_TRANSITION

Across Discovery, execution, final validation and Brain Review, each stage consumes the exact prior sealed object. It may not expand the object's read boundary, mutate the consumed object during observation or rewrite source content. If an object changes, it receives a new identity and all dependent validation and review steps are repeated. This is a short-lived task consistency rule, not a persistent observer, immutable database or new authority layer.

canonical_rule_id: RULE_TEST_RUNNER_ADAPTIVE_ISOLATION
source_section_id: 05::TEST_RUNNER_ADAPTIVE_ISOLATION

The local mechanical test runner may reduce process-start overhead without reducing validation coverage. Small bounded test modules may run once as a complete module; large modules keep the proven isolated batch path so a slow module-first attempt does not add a full timeout before diagnostics. A module failure remains blocking even if isolated batches later pass, because the module-level failure may expose ordering or shared-state behavior. Module timeout may recover only when every discovered test passes through the bounded fallback. Test discovery count, raw stdout/stderr, exit-code failure semantics and all existing validation gates remain unchanged. No parallel runner, cached prior PASS, background service or automatic promotion is introduced.

A Web Brain tool execution window is not an authoritative substitute for local full-package validation. When the complete suite exceeds the Web tool window, the existing bounded local Codex execution layer runs the exact full validation command and returns preserved stdout, stderr and exit code for Brain review. A partial Web replay remains `NOT_OBTAINED_TO_COMPLETION`; it may never be promoted to PASS.

canonical_rule_id: RULE_STRUCTURAL_EVIDENCE_SEMANTIC_COMPATIBILITY
source_section_id: 05::STRUCTURAL_EVIDENCE_SEMANTIC_COMPATIBILITY

A structural closure status is evidentiary, not a label. `CHECKED` requires current compatible direct evidence and a typed semantic relation that actually addresses the requested dimension. `NOT_APPLICABLE` requires a current evidence-backed applicability basis; an empty N/A is invalid. `UNRESOLVED` preserves the missing fact/reason and cannot support a final executable architecture route. Evidence strength must match claim meaning: a path-existence observation may prove a path exists but cannot by itself prove authority ownership, rule ownership, lifecycle transition, shared-core responsibility or runtime behavior. Higher-semantic structural relations require current source/runtime/persistence observations capable of supporting that relation type.

canonical_rule_id: RULE_EVIDENCE_OBJECT_TRANSPORT_SEPARATION
source_section_id: 05::EVIDENCE_OBJECT_TRANSPORT_SEPARATION

The current-round `CODEX_EXECUTION_EVIDENCE_BUNDLE` remains the evidence object. Direct Tool Evidence owns physical identity only: repository plus exact Commit SHA, Artifact plus SHA-256, or canonical source-material-set digest. Logical execution roles such as existing PR Head or repository base belong to the Brain-owned execution contract and are verified from the appropriate native source; a Tool observation never acquires or imitates that authority. A GitHub ZIP or other transport envelope only carries that bundle and its raw materials; it does not become a second Evidence Bundle, product Artifact, repository fact authority, review verdict or PASS/FAIL authority. Transport integrity and evidence semantic sufficiency are separate dimensions.

canonical_rule_id: RULE_GITHUB_EXACT_OBJECT_EVIDENCE_TRANSPORT_RECEIPT
source_section_id: 05::GITHUB_EXACT_OBJECT_EVIDENCE_TRANSPORT_RECEIPT

When the approved task uses GitHub exact-object Evidence transport, Codex returns a compact `EVIDENCE_TRANSPORT_RECEIPT` binding repository, exact commit SHA, exact path, object byte length, object SHA-256 and the exact current-round Evidence Bundle digest. Brain must fetch the exact commit/path and independently re-check bytes/hash before consuming the bundle. A receipt never contains PASS, Brain review, acceptance, merge or project-truth status.

canonical_rule_id: RULE_CURRENT_PR_REVIEW_INPUT_TRANSPORT_LOCATOR
source_section_id: 05::CURRENT_PR_REVIEW_INPUT_TRANSPORT_LOCATOR

Repository PR CI may consume the exact current Projection, Codex Return, Evidence Bundle and Brain Review Capsule through a separate mechanical PR-body locator. The locator binds repository, PR, Base, immutable source Head, temporary ref, distinct exact transport commit, and each object's exact path, bytes, SHA-256 and semantic digest. The transport commit contains exactly the four lifecycle inputs and never contains its own locator or a field that requires the commit to name itself. This locator is Tool-owned mechanical routing data and carries no Brain verdict, User decision, acceptance or merge authority.

canonical_rule_id: RULE_ONE_CURRENT_BUNDLE_PER_TRANSPORT_OBJECT
source_section_id: 05::ONE_CURRENT_BUNDLE_PER_TRANSPORT_OBJECT

One GitHub transport object corresponds by default to one exact current `project_id + task_id + round_id + evidence_bundle_digest`. Multiple tasks or rounds must not be mixed into one evidence transport envelope merely to reduce file count. Transport identity cannot substitute for Evidence Bundle completeness or task identity checks.
