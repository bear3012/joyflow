# JOYFLOW SEMANTIC ENVELOPE RUNTIME REFACTOR CANDIDATE v0.1

Revision: targeted cold-read repair 4
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
7. `ROUTE_ASSUMPTION_VALIDITY` currently binds a `BRAIN_ROUTE_SPACE` whose refs are Brain route IDs, so a zero-hint case cannot satisfy its non-empty subject binding.

This is one dependency-closed `COMPOSE + NARROW_EXTENSION`, not a new architecture.

## 3. Ownership

- Web Brain owns Goal, Frozen Design, semantic boundary, non-goals, Authority/Authorization framing, acceptance meaning and reclosure.
- Codex owns repository-grounded technical judgment and implementation construction inside the approved envelope.
- Tool/Runtime owns deterministic observation, currentness, binding, validation, Effect gating and Evidence capture.
- User retains existing mutation approval, applicable acceptance and final merge authorization.

`technical_route_space.owner=WEB_BRAIN` remains valid: it means Web Brain owns the bounded technical decision space, not that Web Brain must produce the concrete implementation route.

Route construction never creates Product semantics or Authority.

## 4. Executable semantic envelope and approval boundary

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

Current Joyflow's execution authorization envelope does not make `technical_route_space` or candidate routes part of the material user-approval digest. Preserve that property. A route hint change may change the exact Projection/Prompt and therefore must be current-round bound, but by itself must not create a new user approval requirement when the material authorization envelope is unchanged. If a proposed route introduces a material path, semantic, Effect, compatibility/migration or important tradeoff distinction, that distinction must first enter the approved semantic envelope and reclosure rules; it cannot hide inside a route hint.

## 5. Route modes and canonical representation

### A. Ordinary fast path with zero Brain hints

Zero-hint construction is legal only when:

- `planning_mode=BRAIN_BOUNDED_FAST_PATH`;
- no structural decision frame / accepted structural route is active;
- the executable semantic envelope is sufficiently closed for user/material decisions;
- no material USER- or WEB_BRAIN-owned technical tradeoff remains unresolved;
- the approved path, publication, Effect and validation boundaries are exact enough that Codex can test route feasibility without gaining authority to expand them.

Web Brain does NOT have to prove in advance that a feasible implementation route exists inside those boundaries. Technical feasibility may remain a bounded preflight question. Codex must prove that a legal route exists from the current execution object before mutation; if not, it returns the existing conflict/scope/reclosure disposition. This avoids reintroducing mandatory Brain route planning while still failing closed.

If Codex discovers a new important tradeoff owned by User/Web Brain, a material architecture question, or a legal route requiring a new path/boundary, it MUST stop for targeted reclosure rather than choose for the owner.

Use the minimum-compatible representation:

- `candidate_routes` remains required and canonical zero-hint value is `[]`;
- ordinary fast path accepts 0-3 unique route hints;
- `candidate_evaluations` remains required and is `[]` when there are zero candidates;
- Codex still answers every applicable preflight obligation from current-object Evidence;
- Codex constructs one technical route inside the approved envelope;
- selected-route `source` adds the distinct value `CODEX_CONSTRUCTED`;
- `alternative_route` MUST be null for `CODEX_CONSTRUCTED`; no `why_better_than_candidates` claim is fabricated;
- material UNKNOWN, scope gap, object mismatch or semantic conflict stops for reclosure.

### B. Ordinary fast path with Brain hints

Brain hints remain optional, non-exhaustive and non-authoritative. Every supplied hint is evaluated exactly once.

- selecting a supplied hint uses existing `BRAIN_CANDIDATE` provenance;
- a true equivalent alternative to supplied hint(s) uses existing `CODEX_ALTERNATIVE` provenance and its alternative-route comparison object;
- `EQUIVALENT_IMPLEMENTATION_ADJUSTMENT` applies only to this real alternative case.

### C. Brain-accepted structural route

A structural route accepted after repository-grounded architecture discovery is part of Frozen Design, not a hint. Preserve the existing structural representation: structural mode must retain a non-empty candidate set containing the exact accepted `source_route_id`, and the source structural binding remains binding for route identity. Ordinary zero-hint construction is not legal in this mode and cannot bypass it.

### D. Status mapping

For minimum semantic change:

- `ROUTE_CONFIRMED` covers either a valid supplied `BRAIN_CANDIDATE` or a valid zero-hint `CODEX_CONSTRUCTED` route;
- `EQUIVALENT_IMPLEMENTATION_ADJUSTMENT` is reserved for `CODEX_ALTERNATIVE` relative to actual supplied hint(s);
- existing conflict/scope/object-mismatch statuses retain their stop meanings.

## 6. Preflight subject binding and Return semantics

### A. Pre-execution subject

`ROUTE_ASSUMPTION_VALIDITY` cannot remain bound only to Brain route IDs because zero hints would produce an empty subject. Replace its universal subject meaning with a task-local technical route space that exists before execution.

The subject must:

- have at least one stable task-local reference independent of candidate count;
- digest the current planning mode, optional candidate routes, technical decisions, route-change boundaries and structural route binding where applicable;
- add concrete route refs when hints or an accepted structural route exist;
- remain an execution-obligation binding, not a new persistent truth object.

The exact identifier is engineering naming; the semantic subject is `TECHNICAL_ROUTE_SPACE`, not "a non-empty set of Brain routes".

### B. Concrete route proof after construction

The pre-execution obligation binds the allowed route-construction space. After Codex constructs/selects the concrete route, `ROUTE_ASSUMPTION_VALIDITY` must be supported by the selected-route typed derivation plus current-object Evidence sufficient for the route's material assumptions.

`PATH_SUFFICIENCY` remains independently blocking. A Codex-constructed route may not rely on an unapproved path simply because no Brain candidate listed expected paths. Any newly required path must produce the existing scope-gap/reclosure disposition before mutation. Post-result exact touched-path enforcement remains an additional mechanical backstop, not a substitute for preflight.

A constructed route also may not resolve a material User/Web Brain-owned tradeoff. Discovery of such a tradeoff changes disposition and requires reclosure.

### C. Candidate evaluations

`candidate_evaluations` has exact set equality with supplied candidates:

- zero candidates -> `[]`;
- N candidates -> exactly N rows;
- object mismatch remains fail-closed; supplied candidates remain `NOT_EVALUATED` as required, while zero candidates remain `[]`.

### D. Selected/alternative route

A non-mismatch execution still requires one selected/constructed route.

- `BRAIN_CANDIDATE`: selected from supplied candidates;
- `CODEX_CONSTRUCTED`: zero-hint construction inside the envelope;
- `CODEX_ALTERNATIVE`: equivalent alternative to actual supplied candidate(s).

Structural mode is distinguished by `planning_mode` plus exact source structural route binding; it does not require another provenance enum.

Reuse the existing selected-route record and typed `SELECTED_ROUTE_DERIVATION`. Do not create a parallel route truth source.

## 7. Machine model and Project Source alignment

Machine-model execution authority must mean bounded route construction with optional hint selection, not mandatory selection from a pre-existing set. Its successor meaning must cover both construction from a closed envelope and selection/equivalent adjustment when hints are present.

Prefer narrow repair of existing Project Source route rules, including the current non-exhaustive route-space, bounded alternative-route, path-coverage, object-mismatch and task-bound preflight rules. Ordinary hints become optional; accepted structural routes remain binding.

The full Projection/Prompt continues to bind the exact current technical route space, including any hints, even though optional hints are not material user-approval semantics. This preserves current-round exactness without making implementation suggestions into Authority.

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

- Project Source route semantics, zero-hint eligibility and separation of material closure from technical route feasibility;
- machine-model execution-authority semantics;
- `technical_route_space` validation: ordinary 0-3 candidates, structural mode preserving its accepted route;
- Projection schema/generator canonical zero-hint `candidate_routes=[]`;
- task-bound `ROUTE_ASSUMPTION_VALIDITY` subject generation/validation that remains valid with zero hints;
- Return schema/generator canonical zero-hint `candidate_evaluations=[]`;
- selected-route `CODEX_CONSTRUCTED` provenance;
- alternative-route and preflight-status applicability;
- runtime validation for hint-present, hint-absent and structural modes;
- typed Evidence/derivation validation linking the concrete constructed route back to the preflight obligation;
- preflight scope/tradeoff checks proving zero-hint construction cannot expand approved paths or decide User/Brain-owned material tradeoffs;
- approval/lifecycle tests proving route hints do not silently become material authorization semantics;
- fixtures/examples/tests and deterministic generated assets;
- package manifest, SHA256 sums and validation report bound to the actual successor.

Exact changed files must be derived from the current source dependency graph during separately authorized implementation. This design does not pre-authorize a mutation file list.

## 11. Required validation before adoption

The implementation candidate must prove:

1. ordinary zero-hint Projection uses `candidate_routes=[]`, validates its task-local preflight subject binding, and completes with `candidate_evaluations=[]` plus one typed `CODEX_CONSTRUCTED` route;
2. zero-hint preflight can truthfully return no feasible route / scope insufficiency without mutation and without requiring Brain to have pre-enumerated a candidate;
3. no fake alternative-to-candidate record is required;
4. hint-present behavior remains compatible and every supplied hint is evaluated exactly once;
5. changing only a non-material route hint changes current Projection binding as applicable but does not falsely require or fabricate a new material user-approval decision when the authorization envelope is unchanged;
6. zero-hint is rejected while a material User/Web Brain-owned tradeoff or structural question remains unresolved;
7. any material distinction or new required path discovered through a route triggers reclosure instead of hiding in the hint/route;
8. zero-hint path still blocks on object mismatch, path insufficiency, semantic/non-goal conflict, test contradiction, migration/compatibility change, disposition-changing UNKNOWN and out-of-envelope Effect/failure/recovery change;
9. Brain-accepted structural route still rejects empty-route bypass and silent material substitution;
10. P0 mechanical continuation semantics/tests remain preserved;
11. generator/schema/examples/validators/package metadata are mutually current and coherent;
12. no automatic approval, acceptance, merge, promotion or second authority is introduced.

## 12. Stop boundary and disposition

Implementation remains blocked if zero-hint route construction cannot be represented without semantic conflation, if the pre-execution route-space subject cannot bind a later concrete route without weakening Evidence, if zero candidate evaluations weakens a Gate, if unresolved owner-level tradeoffs can leak into Codex construction, if structural binding is weakened, if P0 regression cannot be preserved, or if truthful successor currentness cannot be established.

Current design conclusion: Joyflow already contains the required semantic, Authority, Evidence and Gate primitives. The residual is the coupled assumption that ordinary execution always begins from at least one Brain candidate route. Repair remains `COMPOSE + NARROW_EXTENSION`.

This repaired design file changes no runtime behavior, P0 state, Stable Baseline state, user approval, Brain Review, User Acceptance, merge authorization, `main`, or PDLP Product semantics. Separate implementation authorization is still required after stranger cold-read closure.