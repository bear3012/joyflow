# JOYFLOW SEMANTIC ENVELOPE RUNTIME REFACTOR CANDIDATE v0.1

Status: ENGINEERING_DESIGN_CANDIDATE / NO_MERGE / NO_RUNTIME_ACTIVATION
Source base: `agent/r6-stable-baseline-integration@ab0d77831f154194a773525c8762aea67569e011`
Product-semantics intent: preserve current Joyflow authority, authorization, lifecycle, effect, validation, repository and review semantics while reducing unnecessary predefinition of implementation behavior paths.

## 1. Problem

Joyflow already states that Web Brain route candidates are non-exhaustive and that Codex may make equivalent implementation adjustments inside approved semantics and paths. However the current handoff schema still requires a non-empty `technical_route_space.candidate_routes` array. That representation can pressure the Web Brain to preconstruct at least one implementation path even when the Frozen Design is already sufficiently closed by semantic boundaries and Codex could legally construct the technical route from current repository facts at execution time.

The refactor target is therefore not a new planner, Rule engine, Manager, DSL, Agent, or second Brain. It is a representation/ownership correction:

`Frozen Design -> executable semantic envelope -> Codex current-object preflight + dynamic route construction -> mechanical gates/effect -> evidence/verification`.

Not:

`Frozen Design -> mandatory predicted implementation route -> Codex follows/repairs that path`.

## 2. Cognition owner

Joyflow itself uses real AI cognition:

- Web Brain owns product/project-level reasoning, design closure, semantic boundary, Authority/Authorization framing, acceptance conditions and reclosure.
- Codex owns bounded repository-grounded technical judgment and implementation construction inside the approved envelope.
- Tool/Runtime owns deterministic observation, validation, binding, effect gating and evidence capture.
- User retains the existing user-owned decisions, including explicit mutation approval, acceptance where applicable and final merge authorization.

`类AI` is NOT introduced into Joyflow runtime by this refactor. It is a separate downstream-software research concept.

## 3. Executable semantic envelope

The minimum sufficient executable handoff is defined by existing Joyflow primitives, not a new universal object. Its material distinctions are:

1. exact execution object / prestate;
2. Goal and desired effect;
3. material semantics and non-goals that MUST be preserved;
4. exact authorization / allowed path / publication boundary;
5. current source facts and required technical questions;
6. hard risk, Effect, compatibility, migration and recovery boundaries;
7. validation/evidence obligations and completion meaning;
8. STOP / reclosure conditions;
9. implementation freedom inside the equivalence class that preserves all above distinctions.

Current Joyflow fields already cover these through `task_anchor`, `material_semantics`, `repository_evidence`, `decision_boundary`, `validation`, `execution_object`, `task_object_lifecycle`, `delivery`, `stop_conditions`, approval binding and runtime policy. No second contract truth source is required.

## 4. Route representation change

### 4.1 Ordinary structurally-clear fast path

Web Brain MUST close the executable semantic envelope before mutation approval. It MAY provide zero or more non-exhaustive route hints when a hint materially reduces transfer cost or records an important known mechanism.

A route hint is not a required behavior path and does not narrow Codex implementation freedom unless that distinction is independently present in the approved semantic envelope.

When no route hint is supplied, Codex constructs the technical route from the exact current execution object while satisfying every applicable preflight obligation, approved path boundary, semantic/non-goal constraint, validation duty and STOP condition.

### 4.2 Equivalent implementation

Codex may continue without reclosure only when the dynamically constructed route preserves the same product behavior, protocol/schema semantics, approved paths, compatibility/migration commitments, Effect/failure/recovery semantics, validation obligations, user-visible result and user/Brain-owned important tradeoffs.

Different implementation steps, helper choice, operation order or internal algorithm that do not change those material distinctions remain implementation-equivalent and SHOULD NOT require the Web Brain to pre-enumerate them.

### 4.3 Reclosure boundary

Codex MUST stop and return to Web Brain reclosure when execution discovers that a legal solution requires any material change to product semantics, allowed paths, Authority/Authorization, publication mode, important user/Brain-owned tradeoff, Effect/failure/recovery boundary, compatibility/migration obligation, validation/acceptance meaning, or exact execution object.

`UNKNOWN` that can change legal disposition MUST NOT be resolved by route invention.

### 4.4 Structural escalation

The existing structurally-escalated flow remains different. When repository-grounded architecture discovery produces a material architecture route and Web Brain explicitly accepts that route, its structural identity remains binding because it is no longer merely an implementation hint: it is part of closed design. A different material architecture still requires targeted reclosure.

## 5. Mechanical versus cognitive responsibilities

Keep mechanical:

- exact object/currentness binding;
- approved path and repository-publication boundary;
- user/Brain authorization binding;
- thread/session identity where applicable;
- duplicate-effect protection;
- deterministic captures/digests;
- test argv/source binding;
- validation and Return/Evidence coherence;
- commit/PR/merge gates and lifecycle facts;
- fail-closed handling when required material facts are absent.

Leave to Web Brain/Codex cognition inside those boundaries:

- which legal implementation mechanism to use;
- which current repository fact to inspect first when several are sufficient;
- ordering of equivalent implementation operations;
- local technical diagnosis and repair route inside the approved scope;
- choice among equivalent algorithms/helpers;
- whether more bounded technical observation is useful before choosing the next legal step.

The split is by semantic consequence, not by whether code uses `if`, a state machine, a search routine or an AI model.

## 6. P0 treatment

The P0 mechanical-continuation semantics are NOT rewritten into a cognitive runtime by this candidate. Thread binding, writer release, completion/terminal evidence, duplicate dispatch prevention and other effect-sensitive lifecycle distinctions remain mechanical where the current Frozen Design requires mechanical certainty.

P0 is instead used as a regression boundary: the refactor must not weaken its current semantics. Future Joyflow implementation work should avoid adding new pre-enumerated behavior paths when the same requirement can be expressed as a closed semantic boundary plus bounded Brain/Codex implementation freedom.

## 7. Minimal implementation delta

Subject to cold review and separate implementation closure, the smallest expected code/schema delta is:

1. ordinary fast-path `candidate_routes` becomes optional/possibly empty rather than mandatory non-empty;
2. generated schema and generator remain mutually consistent;
3. validators accept a route-hint-free Projection only when all semantic-envelope obligations remain present;
4. Codex preflight/Return still records the actual selected/constructed route and evidence;
5. structural-route accepted mode keeps its existing exact route binding;
6. no Authority, approval, path, Effect, review, acceptance or merge gate is weakened.

No new `SemanticEnvelopeManager`, planner service, agent loop, universal workflow engine, persistent controller or Class-AI component is justified.

## 8. Validation requirements before implementation adoption

A valid implementation candidate must demonstrate at minimum:

- an ordinary mutating fixture with zero route hints validates and produces one current-object-grounded legal Codex route;
- the same fixture still blocks on object mismatch, path insufficiency, product-semantic conflict and validation contradiction;
- a route hint, when supplied, does not become falsely exhaustive;
- a structural accepted-route fixture still rejects silent material route substitution;
- current P0 mechanical continuation tests preserve behavior;
- schema/generator/examples/package metadata are coherent for the new candidate;
- no automatic approval, merge, promotion or second authority is introduced.

## 9. Current disposition

Derived design conclusion: current Joyflow already contains most required primitives. The confirmed residual is representation pressure from mandatory pre-enumerated route candidates on the ordinary fast path. The preferred refactor is COMPOSE + NARROW_EXTENSION, not a new architecture stack.

This document is an engineering design candidate only. It does not change the current P0 candidate, current PR state, Stable Baseline status, user approval state, Brain Review, User Acceptance, merge authorization, `main`, or PDLP Product semantics.
