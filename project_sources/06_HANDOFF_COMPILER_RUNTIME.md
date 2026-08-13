# Handoff Compiler and Runtime Boundary

canonical_rule_id: JF_DL_HIGH_FIDELITY_COMPILER_RULE
source_section_id: 06::HIGH_FIDELITY_COMPILER

The compiler first preserves all material meaning and exact typed effects, then reduces transfer friction and Token cost. Compression may not omit, rewrite or weaken active semantics, boundaries, validation or stop conditions.

canonical_rule_id: JF_DL_DETERMINISTIC_APPROVAL_VIEW_RULE
source_section_id: 06::DETERMINISTIC_APPROVAL_VIEW

The Runtime deterministically renders the exact authorization view for the current Projection. Mutation/material execution renders a user approval view; bounded pure read-only discovery renders a Web Brain read-only authorization view. Both bind the exact task semantics, evidence, boundary, validation, return contract and stop conditions, but only the former creates a user execution approval state.

canonical_rule_id: JF_DL_USER_DECISION_EVENT_RULE
source_section_id: 06::USER_DECISION_EVENT

The Runtime validates route-appropriate authorization but does not create authority. Mutation/material execution requires `APPROVED_FINAL`, owner `WEB_BRAIN`, scope `EXECUTION_ONLY`, basis `CURRENT_EXPLICIT_USER_DECISION`, a current user decision reference and exact digest binding. Bounded pure read-only discovery instead requires `AUTHORIZED_READ_ONLY_DISCOVERY`, owner `WEB_BRAIN`, scope `READ_ONLY_DISCOVERY_ONLY`, basis `WEB_BRAIN_BOUNDED_READ_ONLY_DISCOVERY_AUTHORIZATION`, a Brain authorization reference and exact digest binding; it creates no user approval state. Codex may verify either binding but may not create, modify, elevate or reuse it across route types.

canonical_rule_id: RULE_BOUNDED_READ_ONLY_DISCOVERY_BRAIN_AUTHORIZATION
source_section_id: 06::BOUNDED_READ_ONLY_DISCOVERY_BRAIN_AUTHORIZATION

When the Web Brain determines that current Repository/local/runtime facts are insufficient for technical closure, the confirmed replacement architecture permits it to authorize one exact bounded pure read-only Codex Discovery without a separate user approval Gate; until the replacement Project Instruction is explicitly confirmed, the currently active Project Instruction remains controlling. The authorization binds the current task, repository anchor, discovery question/scope, no-mutation boundary, return contract and stop conditions. It cannot authorize file mutation, material artifact production, Commit/PR creation or update, migration, product/protocol decisions, final mutation paths, Brain review, user acceptance or merge. Any later mutation/material execution requires a newly closed exact execution object and explicit user approval.

canonical_rule_id: JF_DL_BUILD_IDENTITY_BINDING_RULE
source_section_id: 06::BUILD_IDENTITY_BINDING

Projection and Prompt bind the Project Instructions and Project Source set, generated rule index, mechanical model, schemas, compiler and generator. A different receiving ruleset or build rejects the handoff.

canonical_rule_id: JF_DL_PROMPT_ROUND_TRIP_RULE
source_section_id: 06::PROMPT_ROUND_TRIP

The complete self-contained Prompt parses back into the exact Projection and execution semantic view. Dynamic task values remain escaped typed data, not instructions.

canonical_rule_id: JF_DL_CODEX_RUNTIME_TRANSPARENT_RULE
source_section_id: 06::CODEX_RUNTIME_TRANSPARENT

Codex-side validation is a once-installed bounded runtime concern. It verifies the Prompt and executes only route-authorized boundaries. A mutating/artifact task produces `CODEX_EXECUTION_RETURN`; a local discovery task produces `PATH_DISCOVERY_RETURN`, forbids mutation, and does not decide final allowed paths. The return must keep Brain review pending, user acceptance pending and merge unauthorized. Runtime does not automatically approve, review, accept, merge or promote.

canonical_rule_id: JF_DL_DISCOVERY_CAPTURE_HELPER_PROMPT_RULE
source_section_id: 06::DISCOVERY_CAPTURE_HELPER_PROMPT

A complete read-only Discovery Prompt instructs Codex to invoke the repository-owned deterministic worktree-capture helper before and after discovery, use distinct capture IDs and Evidence IDs, and return stable IDs for every path, dependency, validation entry and local finding. Codex still performs one bounded task and does not gain final path authority.

canonical_rule_id: RULE_CODEX_TECHNICAL_PREFLIGHT
source_section_id: 06::CODEX_TECHNICAL_PREFLIGHT

Every mutating or artifact handoff carries the bounded Codex technical-authority contract. Codex performs the preflight internally in the same execution turn. `ROUTE_CONFIRMED` and `EQUIVALENT_IMPLEMENTATION_ADJUSTMENT` may continue; `BRAIN_ROUTE_CONFLICT`, `APPROVAL_SCOPE_INSUFFICIENT`, and `REPOSITORY_STATE_MISMATCH` must return `BLOCKED` with direct evidence and no invented completion artifact. This does not create a second semantic Brain.

canonical_rule_id: RULE_HONEST_BLOCKED_RETURN
source_section_id: 06::HONEST_BLOCKED_RETURN

A `BLOCKED` Codex Return may truthfully omit PR or artifact evidence. It must provide an explicit technical objection, blocker evidence, unresolved items, and mutation/cleanup state. A blocked Return can never be promoted by Brain review to `PASS`.

canonical_rule_id: RULE_CODEX_PREFLIGHT_TYPED_EVIDENCE
source_section_id: 06::CODEX_PREFLIGHT_TYPED_EVIDENCE

Every Codex technical preflight separates the approved expected repository or artifact reference from the actually observed reference. A successful preflight requires typed repository-reference and assumption-check Evidence bound to the current Projection. A technical objection requires a status-specific typed finding whose normalized claim matches the declared conflict, route correction and any requested paths. Generic Diff, narration or unrelated Evidence cannot substitute for the technical finding.

canonical_rule_id: RULE_CODEX_SCOPE_GAP_OUTSIDE_APPROVED_BOUNDARY
source_section_id: 06::CODEX_SCOPE_GAP_OUTSIDE_APPROVED_BOUNDARY

`APPROVAL_SCOPE_INSUFFICIENT` may request only valid repository-relative paths that are not already covered by the approved `allowed_paths`. Each requested path remains a proposal to the Web Brain and does not expand Codex authority.

canonical_rule_id: RULE_CODEX_PR_MUTATION_COHERENCE
source_section_id: 06::CODEX_PR_MUTATION_COHERENCE

Any Return carrying PR Evidence must report that mutation occurred, bind the exact non-empty touched-path set to typed Diff Evidence, and keep every touched path inside the approved boundary. A completed PR has no residual cleanup state. A blocked PR must report its current touched paths as pending residual changes rather than claiming no mutation.

canonical_rule_id: RULE_BRAIN_NON_EXHAUSTIVE_TECHNICAL_ROUTE_SPACE
source_section_id: 06::BRAIN_NON_EXHAUSTIVE_TECHNICAL_ROUTE_SPACE

On the ordinary structurally-clear fast path, the Web Brain fixes user intent, protected semantics, non-goals, approved paths, acceptance conditions and the critical technical questions that cannot be skipped, and may provide one to three non-exhaustive candidate routes. This Brain-bounded route space does not govern a task that has entered structural escalation. For a structurally escalated task, final mutation paths are not frozen first; Codex produces the repository-grounded architecture candidates and recommendation, and the Brain later accepts/reworks that exact proposal before mutation approval.

canonical_rule_id: RULE_CODEX_BOUNDED_ALTERNATIVE_ROUTE
source_section_id: 06::CODEX_BOUNDED_ALTERNATIVE_ROUTE

On the ordinary fast path, Codex evaluates every Brain candidate against the current execution object and may select a feasible candidate or propose a better equivalent route. An alternative may execute without another round only when product behavior, protocol/schema semantics, approved paths, migration, compatibility, user-visible result and important tradeoffs remain unchanged. A structurally escalated task instead uses the exact Codex structural route accepted by Brain review; Codex may not self-substitute a different material architecture route during mutation and must stop for re-closure if the approved structural route becomes invalid.

canonical_rule_id: RULE_EXECUTION_OBJECT_IDENTITY
source_section_id: 06::EXECUTION_OBJECT_IDENTITY

Technical preflight binds one exact execution object. Repository work binds repository ID and approved base ref. Existing Artifact work binds source artifact ID and SHA-256. New Artifact work binds explicit source-material references. The Return separately records the observed object and uses a typed tool capture; object mismatch cannot be hidden by a generic `artifact:current` or expected-ref placeholder.

canonical_rule_id: RULE_CANDIDATE_REQUIRED_PATH_APPROVAL_COVERAGE
source_section_id: 06::CANDIDATE_REQUIRED_PATH_APPROVAL_COVERAGE

A Brain candidate route may be marked feasible PASS or selected only when every required expected repository path is covered by the user-approved `allowed_paths`. A candidate outside the approved boundary may be evaluated as partial or failed, but cannot become the executable route. Candidate routes guide technical choice and never expand approval.

canonical_rule_id: RULE_OBJECT_MISMATCH_STOPS_ROUTE_EVALUATION
source_section_id: 06::OBJECT_MISMATCH_STOPS_ROUTE_EVALUATION

When the typed execution-object observation differs from the approved repository or Artifact object, Codex stops before evaluating or selecting a route. Object identity is FAIL, remaining preflight obligations are `NOT_APPLICABLE`, candidates are `NOT_EVALUATED`, no route is selected, and the Return is `BLOCKED` for Brain re-closure.

canonical_rule_id: RULE_APPROVED_PREFLIGHT_TEST_COMMAND
source_section_id: 06::APPROVED_PREFLIGHT_TEST_COMMAND

A `TEST_RESULT` used for acceptance feasibility, test contradiction or route evaluation must come from a typed test-command capture whose command is one of the approved validation checks. Route, path, product-semantic, non-goal and migration conclusions also require a structural current-object fact; arbitrary command output cannot prove them.

canonical_rule_id: RULE_PREMUTATION_PROJECTION_SOURCE_REPLAY
source_section_id: 06::PREMUTATION_PROJECTION_SOURCE_REPLAY

Before repository mutation, the operational runtime validates the approved Projection against the supplied current repository. The repository identity, approved baseline, typed GitHub path observations and any exact local Path Discovery Return are replayed. If the current HEAD differs from the approved baseline, or an approved path has no current repository anchor, Codex stops before mutation. This check verifies the approved object without removing Codex bounded implementation judgment.

canonical_rule_id: RULE_OPERATIONAL_VALIDATION_REQUIRES_CURRENT_SOURCE
source_section_id: 06::OPERATIONAL_VALIDATION_REQUIRES_CURRENT_SOURCE

Operational `verify-execution-projection`, `verify-path-discovery-return`, `verify-codex-return` and execution-review sealing require the current repository or exact Artifact source. Structural-only fixture helpers are restricted to package examples and tests and cannot authorize mutation, Brain PASS or merge state. A digest-shaped record without its replay source cannot produce a material operational effect.

canonical_rule_id: RULE_DEDICATED_OPERATIONAL_REVIEW_ENTRIES
source_section_id: 06::DEDICATED_OPERATIONAL_REVIEW_ENTRIES

Formal Repository and Artifact review sealing use distinct operational entry points with route-specific required arguments. Repository review requires the exact repository source and PR result; Artifact review requires the exact source Artifact and complete output Artifact set. Shared lower-level validation may be reused, but optional generic parameters may not silently omit a route's required result object.

canonical_rule_id: RULE_SHORT_LIVED_RESULT_HEAD_WORKTREE
source_section_id: 06::SHORT_LIVED_RESULT_HEAD_WORKTREE

Repository result validation creates a temporary Git-administration-isolated shared-object clone at the exact result Head, runs only the approved argv inside that disposable repository, verifies the checked-out Commit and deletes the clone after the current validation. The authoritative source repository is never registered as a linked worktree owner and remains unchanged even when the command attempts to write refs or Git objects. This is a bounded Codex/Validator operation, not a persistent observer, competing repository fact source or second execution authority.

canonical_rule_id: RULE_STRUCTURAL_ROUTE_PLANNING_MODES
source_section_id: 06::STRUCTURAL_ROUTE_PLANNING_MODES

The Handoff has two mutually exclusive planning modes. `BRAIN_BOUNDED_FAST_PATH` is the ordinary path and carries no structural-route binding. `CODEX_STRUCTURAL_ROUTE_BRAIN_ACCEPTED` is used only after a structurally escalated Codex discovery is closed and the Web Brain has accepted one exact Codex route. The structural mode binds the exact structural discovery Return digest, structural question ID, accepted Codex route ID and Brain disposition digest. The final Brain technical route may refine implementation detail but must preserve that accepted route identity; a different material route requires targeted re-closure rather than silent substitution.

canonical_rule_id: RULE_STRUCTURAL_CLOSURE_PRECEDES_FINAL_MUTATION_PATH
source_section_id: 06::STRUCTURAL_CLOSURE_PRECEDES_FINAL_MUTATION_PATH

A task whose Brain structural frame requires discovery cannot receive a confirmed Final Path Decision until its exact structural discovery result is closed, contains no material unresolved structural question, has one recommended Codex route, and that exact route has an ACCEPT Brain architecture disposition. Final Path consumes this closed structural object directly; clearing ordinary path-level unresolved questions cannot bypass an open nested structural question. `NOT_REQUIRED` is valid only when no Brain structural frame exists for the current task.

canonical_rule_id: RULE_OPTIONAL_EVIDENCE_TRANSPORT_PLAN
source_section_id: 06::OPTIONAL_EVIDENCE_TRANSPORT_PLAN

Every executable Handoff carries an exact Evidence transport plan. The default is inline/manual transport with no remote mutation. For mutation/material execution that already has explicit user approval, the same approved Projection may conditionally authorize `GITHUB_EXACT_OBJECT_IF_NEEDED` for a frozen transport-only GitHub surface when Evidence is too large/complex for chat or Brain requires the raw package. The transport plan is part of the same approval binding; it must not create a second approval Gate when the frozen trigger later occurs.

canonical_rule_id: RULE_OPTIONAL_CURRENT_PR_REVIEW_INPUT_TRANSPORT_PLAN
source_section_id: 06::OPTIONAL_CURRENT_PR_REVIEW_INPUT_TRANSPORT_PLAN

A repository PR execution Projection may separately and optionally authorize `CURRENT_PR_REVIEW_INPUT_TRANSPORT` after the final product source Head exists. This plan is distinct from `CURRENT_ROUND_EVIDENCE_BUNDLE_TRANSPORT_ONLY`, is included in the execution authorization envelope when present, and may use inline/manual fallback or one exact user-approved temporary GitHub surface. It never makes GitHub transport mandatory for general Joyflow tasks and never weakens the current source-Head bindings.

canonical_rule_id: RULE_READ_ONLY_DISCOVERY_EVIDENCE_TRANSPORT_MUTATION_BOUNDARY
source_section_id: 06::READ_ONLY_DISCOVERY_EVIDENCE_TRANSPORT_MUTATION_BOUNDARY

Web-Brain authorization for bounded pure read-only Codex Discovery cannot authorize GitHub Evidence commit/push or remote cleanup. If read-only discovery produces Evidence that cannot be returned inline and no user-approved remote Evidence write object already exists, the task must use a non-mutating fallback or obtain a separate exact mutation/material execution approval before GitHub write. The no-separate-approval read-only exception never propagates into remote mutation.

