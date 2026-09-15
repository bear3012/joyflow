# JOYFLOW SEMANTIC ENVELOPE IMPLEMENTATION CONTRACT CANDIDATE v0.1

Revision: cold-read repair 2
Status: ENGINEERING_IMPLEMENTATION_CONTRACT_CANDIDATE / NO_RUNTIME_MUTATION_AUTHORIZATION / NO_MERGE

## 1. Frozen design binding

This contract encodes, and may not redesign, the engineering design in:

- repository: `bear3012/joyflow`
- design branch prestate: `design/semantic-envelope-runtime-v1@c31c6ca5f9241e13bc02f20c093fbd85a33573e8`
- design file: `design/JOYFLOW_SEMANTIC_ENVELOPE_RUNTIME_REFACTOR_CANDIDATE_v0.1.md`
- design revision: `targeted cold-read repair 5`

The implementation base remains `agent/r6-stable-baseline-integration@ab0d77831f154194a773525c8762aea67569e011` unless later current-source evidence proves that this exact base is no longer the authorized implementation object. Any base drift is a STOP/reclosure event, not an implicit rebase authorization.

This contract creates no Product semantics, Authority, User Acceptance, Stable Baseline, merge authorization, runtime activation or runtime implementation authorization.

## 2. Objective

Implement the already-frozen Joyflow change from mandatory pre-enumerated Brain implementation routes to an executable semantic-envelope model in which ordinary fast-path execution may carry zero Brain route hints and Codex may construct a technical route inside the approved semantic boundary.

Target flow:

`Frozen Design -> executable semantic envelope -> Codex current-object preflight + bounded technical route construction -> mechanical Gate/Effect -> Evidence/verification`.

`类AI` is not introduced into Joyflow. Web Brain/Codex remain the cognition layer.

## 3. Frozen semantic requirements

Implementation MUST preserve all current Joyflow Authority/Authorization, repository truth, currentness, lifecycle, approved-path, Effect/failure/recovery, validation, Evidence, Brain Review, User Acceptance and merge boundaries.

The implementation MUST satisfy all of the following:

- ordinary `BRAIN_BOUNDED_FAST_PATH` accepts canonical `candidate_routes=[]` when material semantic/authority/tradeoff closure is sufficient;
- Web Brain is not required to pre-prove technical route feasibility; feasibility may remain a bounded Codex preflight question;
- zero-hint execution uses `candidate_evaluations=[]`;
- selected-route provenance can express `CODEX_CONSTRUCTED` distinctly from `BRAIN_CANDIDATE` and `CODEX_ALTERNATIVE`;
- `CODEX_ALTERNATIVE` remains meaningful only relative to actually supplied hints and must not be fabricated for zero-hint execution;
- `ROUTE_ASSUMPTION_VALIDITY` binds a task-local technical route space that remains valid with zero hints and is later supported by typed selected-route derivation plus current-object Evidence;
- concrete route construction may not expand approved paths, change material Product semantics, decide unresolved User/Web-Brain-owned tradeoffs, bypass material UNKNOWN, or change Effect/failure/recovery/compatibility/migration boundaries without targeted reclosure;
- Brain-accepted structural routes remain binding and may not be bypassed by zero-hint mode;
- optional route hints remain outside the material user-approval envelope while the exact current Projection/Prompt still binds them;
- P0 thread/session binding, writer release, completion/terminal Evidence, duplicate-dispatch protection and other Effect-sensitive mechanical continuation semantics remain preserved wherever the frozen P0 design requires mechanical certainty.

## 4. Execution shape

### Phase A — GitHub-first bounded read-only dependency closure

Before runtime implementation mutation, the Web Brain MUST first inspect the exact current Web-visible GitHub/repository objects needed to derive the minimum dependency-closed implementation surface for the frozen design. It MUST follow current Joyflow Authority, Source Navigation, generated-asset and currentness rules rather than treating this contract as a second source of project truth.

If exact current GitHub/source evidence is sufficient, Phase A closes directly without requiring a Local Codex discovery run. If a material repository/local/runtime fact remains unavailable or insufficient, the Web Brain may authorize one exact bounded pure read-only Codex discovery for only that residual frontier under the existing Joyflow read-only authorization semantics. Missing material facts remain UNKNOWN until obtained; they are not guessed.

Phase A is read-only Technical Discovery. It creates no user mutation approval state and no mutation authorization. Any Local Codex discovery used by Phase A must bind the exact current source object, remain read-only, and return only the bounded facts/evidence needed to close the residual question.

The discovery result MUST identify the dependency-closed implementation surface at the level required for later mutation authorization and explain each affected class's dependency on the frozen requirement. It MUST distinguish at least:

- authoritative Project Source / machine-model / generator / runtime source that may require hand mutation;
- generated schema/registry/example/fixture outputs that must be deterministically rebuilt rather than independently hand-edited;
- targeted tests/regression surfaces;
- package/integrity/currentness metadata that must be rebuilt or verified against the actual successor.

Phase A MUST NOT require implementation of a hypothetical successor merely to predict its future generated bytes. Exact successor generated-byte drift, generated file-set changes, manifest/SHA256 values and final validation results do not exist as current implementation Evidence before Phase B mutation. They are established after authorized implementation by deterministic generation, freeze and validation against the actual successor.

The discovered dependency surface is Evidence for later scope closure; discovery does not authorize mutation of that surface.

Discovery MUST NOT redesign semantics, invent a second truth source, broaden Product scope, mutate the repository, or treat historical package metadata as current proof.

### Phase B — mutation after exact user authorization

Phase B is forbidden until explicit user implementation authorization is given for the exact implementation object and a dependency-closed mutation scope established by Phase A.

The authorized scope MUST distinguish hand-edited authoritative/implementation sources from deterministic generated/currentness outputs. Generated artifacts are regenerated from their current authoritative sources and verified by the existing generation/currentness mechanisms; they are not manually edited merely because their bytes later change.

The user may authorize the full dependency-closed set or a smaller dependency-closed implementation slice. A partial slice cannot claim full implementation completion until all frozen requirements and dependencies are closed.

After authorization, Codex may implement only the frozen design and the authorized dependency-closed set. Equivalent low-level implementation choices are allowed only inside the frozen semantic envelope.

## 5. Mandatory discovery classes

Phase A MUST at least test whether the frozen change mechanically affects each of these existing classes; it may not assume a class is unaffected without current-source evidence:

- Project Source route semantics and zero-hint eligibility;
- machine-model execution-authority semantics;
- Fibered Task Capsule / decision-boundary technical route-space validation;
- Projection schema and generator;
- task-bound preflight subject generation/validation;
- Codex Return schema and generator;
- selected/alternative route provenance and typed derivations;
- runtime execution-return validation and status applicability;
- approved-path/scope/tradeoff fail-closed checks;
- structural-route binding;
- prompt/execution-view representation;
- fixtures/examples/tests and deterministic generated assets;
- P0 mechanical continuation regression surface;
- package manifest, SHA256 sums and validation report/currentness metadata.

This list is a dependency checklist, not a predetermined changed-file list and not a requirement that every class be hand-edited.

## 6. Required validation

An implementation candidate is not complete unless current-source evidence proves at least:

1. ordinary zero-hint Projection validates with `candidate_routes=[]`;
2. its preflight obligation binding remains non-empty and task-current without Brain route IDs;
3. successful zero-hint execution returns `candidate_evaluations=[]` and one typed `CODEX_CONSTRUCTED` route;
4. zero-hint no-feasible-route case stops without mutation and without requiring a pre-enumerated Brain candidate;
5. no fake alternative-to-candidate record is required;
6. hint-present behavior remains compatible and every supplied hint is evaluated exactly once;
7. non-material hint change may alter current Projection binding but does not fabricate a new material user-approval requirement when the authorization envelope is unchanged;
8. unresolved User/Web-Brain-owned material tradeoff or structural question blocks zero-hint construction;
9. new required path, material semantic distinction, compatibility/migration obligation, or Effect/failure/recovery change causes reclosure rather than silent execution;
10. object mismatch, path insufficiency, semantic/non-goal conflict, test contradiction, disposition-changing UNKNOWN and other existing hard blockers remain fail-closed;
11. Brain-accepted structural route rejects empty-route bypass and silent material substitution;
12. current P0 mechanical continuation behavior/tests remain preserved;
13. deterministic generation is coherent and generated assets match authoritative source;
14. package manifest, SHA256 sums and validation report are truthful for the actual successor source object;
15. no automatic approval, acceptance, merge, promotion, second Brain, Class-AI runtime or persistent controller is introduced.

## 7. STOP / reclosure conditions

STOP and return to Web Brain if current-source discovery or implementation reveals any of the following:

- the frozen design cannot be represented without semantic conflation;
- a required change would alter Product semantics, Authority/Authorization, user-owned decisions or merge policy;
- zero-hint execution would require Codex to decide an unresolved User/Web-Brain-owned material tradeoff;
- structural binding or P0 mechanical guarantees would need weakening;
- the approved path boundary is insufficient for the minimum correct implementation;
- a new material architecture choice appears;
- implementation depends on stale/unverifiable source or package identity;
- the proposed mutation set cannot be made dependency-closed under the authorized scope.

Missing technical feasibility inside a closed boundary is not itself a design defect: Codex may prove no legal route exists and return the applicable fail-closed/reclosure disposition without mutation.

A failed attempt to obtain optional local discovery evidence does not authorize guessing. If the missing fact is material, preserve UNKNOWN and STOP; if current GitHub/source evidence already closes the material dependency question, no Local Codex discovery is required merely for process symmetry.

## 8. Prohibited actions

Without exact user runtime implementation authorization, this contract forbids:

- modifying Project Source, machine-model, runtime, schema/generator, tests, examples or package/currentness files for the implementation itself;
- changing the implementation base by mutation;
- merging any PR;
- pushing to `main`;
- accepting or promoting a Stable Baseline;
- weakening P0 mechanical gates;
- adding a planner service, universal workflow engine, persistent controller, second Brain, Agent layer or Class-AI component;
- silently resolving any disposition-changing UNKNOWN.

Phase A Web-Brain/GitHub read-only observation is not prohibited. Bounded Local Codex read-only discovery is also not prohibited when the Web Brain separately determines that a material local/runtime fact remains missing and authorizes that exact read-only object under existing Joyflow rules.

## 9. Completion meaning

Contract-freeze completion means only that this implementation contract faithfully encodes the frozen design and is ready for GitHub-first Phase A dependency closure and later separate runtime implementation authorization.

Phase A completion means only that the exact current dependency-closed mutation surface has been established as Evidence at the level needed for authorization, including which surfaces are authoritative hand-edited inputs versus deterministic generated/currentness outputs. It does not require precomputing future successor bytes and is not runtime mutation authorization.

Implementation completion, Brain Review PASS, User Acceptance, merge readiness and Stable Baseline are separate later states and cannot be inferred from this document.
