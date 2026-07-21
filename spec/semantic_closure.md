# Semantic Closure and Anti-Drift Contract

Protocol feature version: `4.3.6-repair-candidate`

## Operating model

Joyflow remains a single-human, Web Brain, local Codex, GitHub, human-semiautomatic workflow. It does not add autonomous execution, automatic product judgment, background dispatch, merge, or deployment.

## Lifecycle modes

`REFERENCE_CANDIDATE` is the safe package state used for cold review and installation preparation. It is always non-executable and must produce a HARD_STOP Bridge and HALT packet.

`ACTIVE_TASK` is allowed only after a real task has confirmed product meaning, no material ambiguity, an authentic Codex interpretation return, Brain alignment, a non-blocking red-team result, and a current Bridge.

A fixture, example, template, old Prompt, old CI result, or green candidate check cannot authorize execution.

## Three-layer closure

1. Human and Brain close product meaning through a concrete walkthrough, positive examples, failure examples, non-goals, tradeoffs, and contract-time acceptance.
2. Brain compiles a human semantic layer and a mechanical execution layer. Natural language carries meaning; structured fields bind scope and evidence.
3. Codex returns a short read-only interpretation before non-LEAN execution. Brain reviews it. Codex then executes inside the current Bridge, Brain reviews the actual result, and the user tests the predefined real experience.

## Authentic interpretation

An ACTIVE_TASK non-LEAN interpretation must contain:

```text
artifact_origin: CODEX_EXECUTION_RETURN
interpretation_status: ALIGNED
unresolved_items: []
brain_alignment_status: ALIGNED_CONFIRMED
brain_alignment_ref: non-empty durable reference
```

`not_codex_execution_evidence=true` always disqualifies execution.

LEAN may embed the same meaning only when all eight eligibility facts are true, the embedded origin is `CONTRACT_EMBEDDED_LEAN`, task and Golden Case IDs match, and no unresolved item remains.

## Write ownership

The Bridge separates:

- `allowed_paths`: source paths the executor may modify;
- `executor_writable_outputs`: machine/executor evidence outputs;
- `brain_only_outputs`: Brain review and handoff artifacts;
- `human_only_outputs`: user acceptance evidence;
- `machine_late_outputs`: Reconcile output after other gates.

Codex must never write Brain-only or human-only evidence.

## Evidence binding

The Bridge binds exact SHA-256 hashes for authority inputs and the source bundle. The launch Manifest binds the Bridge, product meaning, contract, Meaning Delta, Golden Cases, acceptance plan, interpretation, red-team receipt, and context. The packet contains both Bridge and input-bundle hashes.

Machine checks use the committed base-to-head diff, not merely the clean working tree. Hidden paths retain their leading dot. Absolute paths and parent traversal are invalid.

## Completion

Closure is impossible when lifecycle mode is not ACTIVE_TASK, target lane is HARD_STOP, execution was not released, or the packet is HALT.

For an active task, machine evidence, Brain review, PR evidence, and human acceptance must all bind to the same current HEAD, Bridge hash, input bundle, source bundle, task ID, Golden Cases, and acceptance plan. Human remains final closer.
