# Joyflow Class-AI Adoption Replay v0.2

Status: RESEARCH / E0 EXACT-CURRENT EXPRESSIBILITY REPLAY  
Date: 2026-09-15  
Predecessor: `research/JOYFLOW_CLASS_AI_ADOPTION_REPLAY_v0.1.md`  
Product semantics change: NO  
Frozen Design change performed: NO  
Implementation authorization: NO  
Merge authorization: NO

## 1. Why v0.2 exists

The first adoption replay correctly preserved Joyflow Authority/currentness/acceptance/merge boundaries, but it was too broad in saying that a bounded Class-AI helper could simply be composed into current Joyflow.

Exact-current replay against the frozen semantic-envelope design and implementation contract shows a stronger boundary:

- the frozen design explicitly states that no new Class-AI component is introduced;
- the current implementation contract explicitly preserves Web Brain/Codex as the cognition layer and requires validation that no Class-AI runtime or second Brain is introduced.

Therefore a distinct additional Class-AI model/service/runtime inside Joyflow is **not expressible inside the current frozen implementation object**.

## 2. E0 classification

### A. Research roles already expressible through current cognition

The following functions are already expressible by the existing Web Brain / Codex / deterministic compiler/tool boundary without adding a new Class-AI component:

- contract/projection candidate generation;
- affected-scope reconstruction;
- repair localization;
- migration/version analysis;
- typed-interface candidate generation;
- recurring-pattern analysis and deterministic hardening proposals.

Disposition: `ALREADY_EXPRESSIBLE` or `EXPRESSIBLE_BY_COMPOSITION_OR_NARROW_CONFIGURATION`, depending on the concrete task.

Calling these behaviors "Class-AI-like" does not create a new runtime component. They remain ordinary cognition/engineering work performed by the existing admitted roles.

### B. Distinct Class-AI runtime/model/component inside Joyflow

A new small model, local Class-AI service, persistent Class-AI process, new runtime decision component or additional cognition layer would contradict the current frozen design/contract boundary.

Disposition: `NOT_EXPRESSIBLE_INSIDE_CURRENT_FROZEN_DESIGN`.

This is not merely `SEMANTICS_EXPRESSIBLE_BUT_MECHANICAL_CARRIER_GAP`, because the current frozen object deliberately excludes such a component. A future adoption would require a separate Frozen Design successor and its own cold-read/confirmation/implementation-authorization lifecycle.

### C. Global Class-AI manager / second semantic Brain

Disposition: `REJECTED` under current evidence and current Joyflow architecture.

No current research establishes a need for a global manager, second semantic Brain, new approval plane or universal AI lifecycle.

## 3. Correct Joyflow interpretation

Current Joyflow can adopt the **principles** from the Class-AI research without adopting a new Class-AI component:

```text
User/Web Brain closes product meaning
        ↓
existing semantic envelope / contract compiler
        ↓
Codex performs bounded repository-grounded technical cognition
        ↓
mechanical currentness / path / Effect / Evidence gates
        ↓
Brain/User review, acceptance and merge boundaries
```

Within that flow, use the research principles:

- minimum-sufficient context;
- typed-interface-first composition;
- targeted affected-scope reopen;
- bounded route construction;
- deterministic hardening when product requirements and safety are satisfied;
- UNKNOWN/fail-closed where required facts are missing.

These are method/engineering principles, not a new Class-AI runtime.

## 4. Future distinct Class-AI adoption boundary

If later evidence shows that a distinct Class-AI component would materially improve Joyflow itself, the next object must be a **new engineering design successor**, not a silent implementation extension.

That future design must answer at minimum:

- exact role relative to Web Brain and Codex;
- whether it is a Brain resource, compiler helper, runtime selector or other bounded compute realization;
- exact scope and lifecycle;
- Authority/Authorization non-ownership;
- currentness/Evidence source boundaries;
- failure/UNKNOWN behavior;
- security and resource envelope;
- why existing Web Brain/Codex/compiler composition is insufficient;
- why no smaller deterministic or configuration-level mechanism closes the gap.

Only after that design closes may implementation authorization be considered.

## 5. Current disposition

```text
CLASS_AI_RESEARCH_PRINCIPLES_IN_JOYFLOW:
  ALREADY_EXPRESSIBLE / COMPOSE

CLASS_AI_LIKE_WORK_BY_WEB_BRAIN_OR_CODEX:
  ALREADY_EXPRESSIBLE

NEW_DISTINCT_CLASS_AI_RUNTIME_OR_MODEL:
  NOT_EXPRESSIBLE_INSIDE_CURRENT_FROZEN_DESIGN

REQUIRES_FROZEN_DESIGN_SUCCESSOR_IF_LATER_ADOPTED:
  YES

PRODUCT_SEMANTICS_CHANGE_ESTABLISHED:
  NO

CURRENT_FROZEN_DESIGN_MUTATION:
  NO

IMPLEMENTATION_AUTHORIZATION:
  NO

MERGE_AUTHORIZATION:
  NO
```

This v0.2 successor narrows v0.1. It does not erase the prior artifact; it corrects the exact-current expressibility disposition after reading the frozen design and contract.