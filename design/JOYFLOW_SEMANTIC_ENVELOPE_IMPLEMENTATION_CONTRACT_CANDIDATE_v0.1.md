# JOYFLOW SEMANTIC ENVELOPE IMPLEMENTATION CONTRACT CANDIDATE v0.1

Revision: cold-read repair 1
Status: ENGINEERING_IMPLEMENTATION_CONTRACT_CANDIDATE / NO_MUTATION_AUTHORIZATION / NO_MERGE

## 1. Frozen design binding

This contract encodes, and may not redesign, the engineering design in:

- repository: `bear3012/joyflow`
- design branch prestate: `design/semantic-envelope-runtime-v1@4571f443e0fc6713f6eb0c7faf17da0603e970f3`
- design file: `design/JOYFLOW_SEMANTIC_ENVELOPE_RUNTIME_REFACTOR_CANDIDATE_v0.1.md`
- design revision: `targeted cold-read repair 4`

The implementation base remains `agent/r6-stable-baseline-integration@ab0d77831f154194a773525c8762aea67569e011` unless later current-source evidence proves that this exact base is no longer the authorized implementation object. Any base drift is a STOP/reclosure event, not an implicit rebase authorization.

This contract creates no Product semantics, Authority, User Acceptance, Stable Baseline, merge authorization, runtime activation or mutation authorization.

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

### Phase A — bounded read-only dependency discovery

Before mutation, Codex MUST inspect the exact current repository object and derive the minimum dependency-closed implementation surface needed to satisfy the frozen design.

Phase A is read-only Technical Discovery. It does not itself require user mutation approval when executed under the existing Joyflow Web-Brain-bounded read-only authorization semantics. This contract does not automatically invoke Phase A; an actual discovery run must still bind the exact current source object and remain read-only.

The discovery result MUST identify the exact affected source/generated/test/package paths and explain each path's dependency on the frozen requirement. It MUST distinguish authoritative source, generated artifact, runtime validator, test/fixture/example, and integrity/currentness metadata.

The discovered file set is evidence for later scope closure; discovery does not authorize mutation of that set.

Discovery MUST NOT redesign semantics, invent a second truth source, broaden Product scope, mutate the repository, or treat historical package metadata as current proof.

### Phase B — mutation after exact user authorization

Phase B is forbidden until explicit user implementation authorization is given for the exact implementation object and exact mutation scope derived from Phase A.

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

This list is a dependency checklist, not a predetermined changed-file list.

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

## 8. Prohibited actions

Without exact user mutation authorization, this contract forbids:

- modifying runtime/schema/generator/tests/package files;
- changing the implementation base by mutation;
- merging any PR;
- pushing to `main`;
- accepting or promoting a Stable Baseline;
- weakening P0 mechanical gates;
- adding a planner service, universal workflow engine, persistent controller, second Brain, Agent layer or Class-AI component;
- silently resolving any disposition-changing UNKNOWN.

Phase A read-only observation is not prohibited when separately invoked under the existing bounded Technical Discovery authorization semantics.

## 9. Completion meaning

Contract-freeze completion means only that this implementation contract faithfully encodes the frozen design and is ready for Phase A bounded read-only discovery and later separate mutation authorization.

Discovery completion means only that the exact current dependency-closed mutation surface has been established as Evidence; it is not mutation authorization.

Implementation completion, Brain Review PASS, User Acceptance, merge readiness and Stable Baseline are separate later states and cannot be inferred from this document.
