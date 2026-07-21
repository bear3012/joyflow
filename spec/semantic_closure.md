# Semantic Closure and Anti-Drift Contract

Protocol feature version: `4.3.6-candidate`

This source defines the product-semantic closure used by Joyflow's single-human, Web Brain, local Codex, GitHub, human-semiautomatic operating model. It does not introduce autonomous execution, background dispatch, or a new semantic agent.

## 1. Governing objective

Joyflow does not require natural language to become perfectly unambiguous. Before implementation, Brain must remove every ambiguity that could materially change:

- the user-visible result;
- the user flow;
- business rules or data meaning;
- approved scope or explicit non-goals;
- important risk or tradeoff;
- acceptance or failure judgment.

Residual wording differences that cannot change those outcomes do not block execution.

## 2. Three-layer responsibility model

### Layer 1 — Human and Brain close product meaning

The human owns product intent, product rules, user-facing tradeoffs, and final lived experience. Brain owns clarification, reverse restatement, scenario walkthrough, and identification of material ambiguity.

Brain must produce `runtime/product_meaning_closure.json`. It is authoritative only when:

- `material_ambiguity_status` is `NO_MATERIAL_AMBIGUITY`;
- `user_confirmation.status` is `CONFIRMED`;
- the walkthrough, correct examples, incorrect examples, and acceptance plan agree;
- no unresolved item can change product outcome, scope, risk, flow, data meaning, or acceptance.

The user confirms the concrete product walkthrough and acceptance meaning, not raw implementation details.

### Layer 2 — Brain compiles a dual-layer execution contract

`runtime/translation_contract.json` contains:

- a human semantic layer that preserves meaning;
- a mechanical execution layer that fixes boundaries;
- stable Golden Case references;
- the user acceptance plan;
- a meaning delta relative to the confirmed parent meaning.

Natural language carries product meaning. Mechanical fields constrain execution and make drift reviewable.

Codex may choose exact files after authorized discovery, local code organization, equivalent algorithms, and local tests inside the approved boundary. Codex may not change product rules, user flow, data meaning, features, accepted tradeoffs, or important experience.

### Layer 3 — Codex returns interpretation and evidence; Brain and human perform different reviews

Before implementation, Codex returns `runtime/codex_execution_interpretation.json`.

Brain compares the interpretation to the confirmed product meaning and contract. Implementation is allowed only when:

- `interpretation_status` is `ALIGNED`; or
- the task is LEAN-eligible and the interpretation is embedded in the single Codex packet with the same required fields.

After implementation:

- Brain checks original problem, confirmed meaning, contract, Codex interpretation, diff, tests, Golden Cases, scope drift, overdesign, and technically-correct-but-practically-wrong risk;
- the user performs the predefined product acceptance steps and judges actual experience.

Machine checks cannot replace human product acceptance. Human acceptance cannot replace required machine checks.

## 3. Product meaning closure shape

```json
{
  "artifact_type": "PRODUCT_MEANING_CLOSURE",
  "artifact_version": "1",
  "task_id": "stable task id",
  "original_user_problem": "verbatim or faithful source-bound problem",
  "problem": "current problem statement",
  "desired_result": "user-visible result",
  "user_flow": ["ordered behavior step"],
  "business_rules": ["confirmed rule"],
  "must_have": ["required result"],
  "must_not_have": ["forbidden product result"],
  "non_goals": ["explicitly excluded scope"],
  "important_tradeoffs": ["accepted tradeoff"],
  "acceptance_examples": ["correct product example"],
  "failure_examples": ["running but wrong example"],
  "remaining_unknowns": [],
  "material_ambiguity_status": "NO_MATERIAL_AMBIGUITY",
  "product_walkthrough": {
    "entry": "where the user starts",
    "user_action_sequence": ["action"],
    "system_response_sequence": ["response"],
    "success_result": "observable success",
    "failure_result": "observable failure",
    "preserved_behavior": ["unchanged behavior"],
    "explicitly_absent_behavior": ["behavior that must not be added"]
  },
  "user_confirmation": {
    "status": "CONFIRMED",
    "reference": "durable reference to the user's decision"
  }
}
```

A draft closure has no execution authority. If a material unknown remains, Brain must return to the human rather than translate it into implementation freedom.

## 4. Dual-layer translation contract

The contract must include:

```json
{
  "human_semantic_layer": {
    "objective": "product objective",
    "expected_user_result": "observable result",
    "user_flow": ["ordered behavior"],
    "business_rules": ["rule"],
    "accepted_tradeoffs": ["tradeoff"],
    "non_goals": ["excluded scope"],
    "correct_examples": ["Golden Case or concrete example"],
    "incorrect_examples": ["forbidden outcome or overdesign example"]
  },
  "mechanical_execution_layer": {
    "must_preserve": ["invariant"],
    "allowed_solution_surfaces": ["approved surface"],
    "forbidden_consequences": ["prohibited consequence"],
    "required_outcomes": ["mechanically reviewable result"],
    "allowed_technical_freedom": ["equivalent implementation freedom"],
    "stop_conditions": ["condition requiring halt"],
    "evidence_requirements": ["required evidence"]
  }
}
```

Behavior scenarios must replace unsupported adjectives such as simple, flexible, stable, easy, or efficient. If an adjective matters, the contract must state the observable behavior that gives it meaning.

## 5. Golden Cases

`runtime/golden_cases.json` contains stable product-level examples. Each case includes:

- `case_id`;
- `original_problem_ref`;
- `initial_state`;
- `action`;
- `expected_user_visible_result`;
- `expected_state_change`;
- `preserved_state`;
- `forbidden_result`;
- `machine_check_mapping`;
- `human_acceptance_mapping`.

The same `case_id` must be reused by Brain clarification, translation contract, Codex interpretation, tests, Brain review, human acceptance, and future regression work. A later stage must not silently restate the case into a different meaning.

## 6. Meaning delta

A successor must record only meaning changes in `runtime/meaning_delta.json`:

```json
{
  "artifact_type": "MEANING_DELTA",
  "parent_meaning_ref": "exact parent identity",
  "added": {},
  "removed": {},
  "changed": {},
  "unchanged": [],
  "unresolved": [],
  "user_confirmation_required": false
}
```

Unchanged product meaning must not be rewritten as a new meaning. A restatement that cannot be shown equivalent is a change and follows the user-decision route when material.

## 7. Codex execution interpretation

The interpretation artifact includes:

```json
{
  "artifact_type": "CODEX_EXECUTION_INTERPRETATION",
  "objective_understood": "objective",
  "user_visible_result": "expected result",
  "user_flow_understood": ["step"],
  "must_preserve": ["invariant"],
  "intended_solution_surface": ["surface"],
  "excluded_changes": ["excluded change"],
  "golden_cases_understood": ["case id"],
  "unresolved_items": [],
  "interpretation_status": "ALIGNED"
}
```

Allowed statuses:

- `ALIGNED`: implementation may continue;
- `TECHNICAL_DISCOVERY_REQUIRED`: read-only discovery only, then return to Brain;
- `MATERIAL_UNCERTAINTY`: no implementation, return to Brain;
- `CONTRACT_CONFLICT`: no implementation, return to Brain.

Codex reports observable uncertainty. Codex does not decide whether a product-scope change is acceptable.

## 8. LEAN route

A separate interpretation round is not mandatory when all are true:

- the task is technical-only or a precisely bounded low-risk correction;
- product behavior, user flow, data meaning, shared state, and tradeoffs do not change;
- paths and expected result are known;
- the single Codex packet embeds the interpretation fields;
- no material ambiguity exists.

Product behavior changes, user-flow changes, data-meaning changes, shared-state changes, nontrivial refactors, medium/high risk, ambiguous requirements, or multi-module changes require a distinct interpretation artifact and Brain check.

LEAN removes ceremony, not semantic boundaries.

## 9. Deviation classification

### AUTO_ACCEPTABLE_TECHNICAL_VARIATION

Codex may proceed and report:

- equivalent implementation;
- local function or file organization inside approved surfaces;
- necessary local tests;
- equivalent algorithm;
- local cleanup required by the approved change.

This class is valid only when product result, user flow, data meaning, risk, maintenance responsibility, and acceptance remain unchanged.

### BRAIN_REVIEW_REQUIRED

Stop mutation and return evidence when:

- solution surface expands;
- shared state is touched;
- interface relationships change;
- maintenance cost materially increases;
- an unexpected technical consequence appears;
- the approved boundary is insufficient.

Brain decides whether the result is equivalent technical work, requires a contract successor, or must return to the user.

### USER_DECISION_REQUIRED

No Brain or Codex substitution is allowed when:

- a product rule changes;
- user flow changes;
- data meaning changes;
- a feature is added or removed;
- important experience changes;
- a new material risk appears;
- an accepted tradeoff changes.

## 10. User acceptance plan

`runtime/user_acceptance_plan.json` is created at contract time. Each step includes:

- `acceptance_id`;
- `step`;
- `expected`;
- `validates`;
- `failure_meaning`;
- optional Golden Case references.

Codex reads the plan, Brain reviews against it, and the human executes the same plan. Post-hoc replacement of the plan requires an explicit meaning delta when it changes acceptance meaning.

## 11. Brain semantic review

`observer/brain_semantic_review.json` compares:

- `original_user_problem`;
- confirmed product meaning;
- released contract;
- Codex interpretation;
- actual diff and evidence;
- test and Golden Case results;
- predefined user acceptance plan.

It must state:

- `semantic_drift_status`;
- `scope_drift_status`;
- `overdesign_status`;
- `original_problem_actually_solved`;
- `technically_correct_but_practically_wrong_risk`;
- `review_verdict`.

A passing mechanical contract does not excuse failure to solve the original problem.

## 12. Durable product facts policy

Repository-visible durable facts may include:

- stable business rules;
- durable product boundaries;
- reusable Golden Cases;
- stable module relationships;
- repeated acceptance paths;
- confirmed non-goals.

Do not persist:

- Brain chain-of-thought;
- Codex hidden reasoning;
- chat transcripts;
- temporary contract drafts;
- speculative options;
- rejected internal reasoning;
- every task packet by default.

Save stable product facts, not AI thought process. A task-specific fact is stored only when future rediscovery cost materially exceeds maintenance cost.

## 13. Completion rule

A repository-changing product task is not closure-ready unless:

1. product meaning closure is confirmed;
2. no material ambiguity remains;
3. contract layers and Golden Cases are coherent;
4. Codex interpretation is aligned or validly embedded in LEAN;
5. machine evidence passes;
6. Brain semantic review passes without unresolved user-level drift;
7. required user acceptance has an explicit result;
8. the human remains the final closer.
