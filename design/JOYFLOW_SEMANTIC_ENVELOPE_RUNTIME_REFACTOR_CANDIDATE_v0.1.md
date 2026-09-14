# JOYFLOW SEMANTIC ENVELOPE RUNTIME REFACTOR CANDIDATE v0.1

Revision: targeted cold-read repair 1
Status: ENGINEERING_DESIGN_CANDIDATE / NO_IMPLEMENTATION_AUTHORIZATION / NO_MERGE / NO_RUNTIME_ACTIVATION
Source base: `agent/r6-stable-baseline-integration@ab0d77831f154194a773525c8762aea67569e011`

## 1. Target

Preserve current Joyflow Product semantics, Authority/Authorization, lifecycle, Effect, validation, Evidence, review, acceptance and merge boundaries while removing the residual assumption that ordinary implementation must start from at least one Web Brain candidate route.

Target flow:

`Frozen Design -> executable semantic envelope -> Codex current-object preflight + bounded technical route construction -> mechanical Gate/Effect -> Evidence/verification`.

No new planner, Manager, DSL, Agent, Class-AI component, persistent controller or second Brain is introduced.

## 2. Confirmed dependency gap

The current representation assumes Brain routes at several coupled layers, so changing only `candidate_routes.minItems` is invalid. The repair must close together:

1. Projection requires non-empty `technical_route_space.candidate_routes`;
2. Codex Return requires non-empty `candidate_evaluations`;
3. selected-route provenance cannot express a Codex-constructed route with no Brain candidate;
4. `alternative_route` assumes candidates exist to compare against;
5. runtime validation assumes every execution has Brain candidates to evaluate;
6. machine-model execution authority is phrased as bounded route selection;
7. `ROUTE_ASSUMPTION_VALIDITY` presupposes Brain candidate-route assumptions.

This is one dependency-closed `COMPOSE + NARROW_EXTENSION`, not a new architecture.

## 3. Ownership

- Web Brain owns Goal, Frozen Design, semantic boundary, non-goals, Authority/Authorization framing, acceptance meaning and reclosure.
- Codex owns repository-grounded technical judgment and implementation construction inside the approved envelope.
- Tool/Runtime owns deterministic observation, currentness, binding, validation, Effect gating and Evidence capture.
- User retains existing mutation approval, applicable acceptance and final merge authorization.

Route construction never creates Product semantics or Authority.

## 4. Executable semantic envelope

The handoff must preserve, using existing Joyflow primitives:

1. exact execution object/prestate;
2. Goal and desired Effect;
3. material semantics and non-goals;
4. approved path/publication/authorization boundary;
5. current facts and required technical questions;
6. hard Effect, failure, recovery, compatibility and migration boundaries;
7. validation/Evidence/completion obligations;
8. STOP/reclosure conditions;
9. implementation freedom inside the equivalence class preserving all above.

No second `SemanticEnvelope` truth object is created. A route hint is only optional technical guidance and cannot become an independent semantic source.

## 5. Route modes

### A. Ordinary fast path with zero Brain hints

When the semantic envelope is sufficiently closed, Web Brain may provide zero route hints.

Required semantics:

- Projection has one canonical zero-hint representation;
- `candidate_evaluations` is empty because there are no candidates;
- Codex still answers every applicable preflight obligation from current-object Evidence;
- Codex constructs one technical route inside the approved envelope;
- selected-route provenance distinguishes a Codex-constructed route from selection of or alternative to a Brain hint;
- `alternative_route` is not fabricated and no `why_better_than_candidates` claim exists;
- material UNKNOWN, scope gap, object mismatch or semantic conflict stops for reclosure.

The exact enum spelling is engineering naming, but the semantic case `CODEX_CONSTRUCTED_WITHIN_ENVELOPE` must remain distinguishable.

### B. Ordinary fast path with Brain hints

Brain hints remain optional, non-exhaustive and non-authoritative. Every supplied hint is evaluated exactly once. Codex may select a valid hint or construct an equivalent alternative only inside the approved envelope.

### C. Brain-accepted structural route

A structural route accepted after repository-grounded architecture discovery is part of Frozen Design, not a hint. Its identity remains binding; materially different architecture requires targeted reclosure. Ordinary zero-hint construction cannot bypass it.

## 6. Preflight and Return semantics

`ROUTE_ASSUMPTION_VALIDITY` becomes route-origin aware:

- hints present -> verify hint assumptions;
- zero hints -> verify assumptions required by the Codex-constructed route;
- structural mode -> verify current technical assumptions of the accepted structural route.

The canonical question must not universally assume Brain candidates exist.

`candidate_evaluations` has exact set equality with supplied hints: zero hints -> empty array; N hints -> exactly N rows. Object-mismatch handling remains fail-closed.

A non-mismatch execution still requires one selected/constructed route. Selected-route provenance must distinguish at least:

- Brain hint selected;
- Codex constructed within envelope;
- Codex equivalent alternative to supplied hint;
- exact Brain-accepted structural route when structural mode applies.

Prefer reuse of the existing selected-route record and typed `SELECTED_ROUTE_DERIVATION`; do not create a parallel route truth source.

`alternative_route` applies only when there is something meaningful to be alternative to. A zero-hint route must not fabricate candidate comparison semantics.

Existing preflight status names may remain only if they truthfully cover the zero-hint case. `EQUIVALENT_IMPLEMENTATION_ADJUSTMENT` must not be used when no prior or supplied route exists.

## 7. Machine model and Project Source alignment

Machine-model execution authority must mean bounded route construction with optional hint selection, not mandatory selection from a pre-existing set. Its successor meaning must cover both construction from a closed envelope and selection/equivalent adjustment when hints are present.

Prefer narrow repair of existing Project Source route rules, including the current non-exhaustive route-space, bounded alternative-route, path-coverage, object-mismatch and task-bound preflight rules. Ordinary hints become optional; accepted structural routes remain binding.

## 8. Mechanical versus cognitive responsibilities

Keep mechanical where semantic consequence requires certainty: exact object/currentness, approved paths, Authorization binding, thread/session identity where applicable, duplicate-Effect protection, digests, test argv/source binding, validation/Return/Evidence coherence, lifecycle/commit/PR/merge Gates, and fail-closed handling of required missing facts.

Leave to Web Brain/Codex cognition inside those boundaries: implementation mechanism, order among equivalent operations, local diagnosis/repair route, equivalent helper/algorithm choice, and bounded additional observation.

The split is by semantic consequence, not by whether code uses `if`, a state machine, search or AI.

## 9. P0 boundary

P0 thread binding, writer release, terminal/completion Evidence, duplicate-dispatch prevention and other Effect-sensitive lifecycle distinctions remain mechanical wherever the frozen P0 design requires mechanical certainty.

P0 is a regression boundary, not a target for cognitive replacement. This design does not establish P0 completion, Brain Review PASS, User Acceptance, merge authorization or Stable Baseline.

Any implementation successor must create truthful current package metadata and validation Evidence for its actual source object; stale historical metadata may not be reused as current proof.

## 10. Dependency-closed implementation obligations

Before adoption, the smallest implementation slice must make all of these coherent together:

- Project Source route semantics;
- machine-model execution-authority semantics;
- Projection schema/generator zero-hint representation;
- Return schema/generator zero candidate evaluations when appropriate;
- selected-route provenance for Codex-constructed routes;
- alternative-route applicability;
- route-origin-aware preflight question/template;
- runtime validation for hint-present, hint-absent and structural modes;
- typed Evidence/derivation validation;
- fixtures/examples/tests and deterministic generated assets;
- package manifest, SHA256 sums and validation report bound to the actual successor.

Exact changed files must be derived from the current source dependency graph during separately authorized implementation. This design does not pre-authorize a mutation file list.

## 11. Required validation before adoption

The implementation candidate must prove:

1. zero-hint ordinary mutation validates with empty candidate evaluations and one typed Codex-constructed route;
2. no fake alternative-to-candidate record is required;
3. hint-present behavior remains compatible and every supplied hint is evaluated exactly once;
4. zero-hint path still blocks on object mismatch, path insufficiency, semantic/non-goal conflict, test contradiction, migration/compatibility change, disposition-changing UNKNOWN and out-of-envelope Effect/failure/recovery change;
5. Brain-accepted structural route still rejects silent material substitution;
6. P0 mechanical continuation semantics/tests remain preserved;
7. generator/schema/examples/validators/package metadata are mutually current and coherent;
8. no automatic approval, acceptance, merge, promotion or second authority is introduced.

## 12. Stop boundary and disposition

Implementation remains blocked if no-hint route construction cannot be represented without semantic conflation, if zero candidate evaluations weakens a Gate, if structural binding is weakened, if P0 regression cannot be preserved, or if truthful successor currentness cannot be established.

Current design conclusion: Joyflow already contains the required semantic, Authority, Evidence and Gate primitives. The residual is the coupled assumption that ordinary execution always begins from at least one Brain candidate route. Repair remains `COMPOSE + NARROW_EXTENSION`.

This repaired design file changes no runtime behavior, P0 state, Stable Baseline state, user approval, Brain Review, User Acceptance, merge authorization, `main`, or PDLP Product semantics. Separate implementation authorization is still required after stranger cold-read closure.