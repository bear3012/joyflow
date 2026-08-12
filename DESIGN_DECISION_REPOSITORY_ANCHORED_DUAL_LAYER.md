# Design Decision: Repository-Anchored Single-Active-Task Round Closure

## Accurate repair target

```yaml
HISTORICAL_REVIEW_CONTEXT:
  target_type: PACKAGE
  target_name_or_ref: JOYFLOW_PHASE1_SINGLE_ACTIVE_TASK_ROUND_REPAIR_CANDIDATE.zip
  target_digest_or_commit_if_available: ff0ed53e697049eadbee02091e57bc47835ed5db763aee99b8e7fadf2fcc144e
  historical_reference_only: YES
  authoritative_for_current_review: NO
  comparison_material_cannot_substitute_current_target: YES
```

## Persistent and temporary layers

Merged repository content is durable project fact. Open branches and PRs are candidates. Task Capsules, approval views, Prompts, Codex Returns, Evidence Bundles and review records are temporary unless a separately justified repository artifact is merged.

## One task per project round

For each project, one execution round has one current task, one current approved Projection, one Codex Return and one Evidence Bundle. The Web Brain owns this sequence. Mechanical fields bind the current object chain but do not create a global task scheduler or prove hostile-tamper resistance.

`task_progress.cycle` is the execution round number. A new round is created only after substantive rework such as Brain-review failure, user-acceptance failure, new root cause, material scope change or required re-execution.

## Authority boundary

- **User:** product direction, execution approval, applicable acceptance and final merge approval.
- **Web Brain:** semantic/technical closure, current-round sequencing, exact Prompt, Return/evidence review, PR or Artifact review, `MERGE_READY`, and recording user decisions only after they occur.
- **Codex:** bounded execution technical authority for current local repository/runtime facts. It preflights the approved route, chooses equivalent implementation details inside approved semantics and paths, and stops with direct evidence when the route or approved scope is technically invalid. It may evolve local implementation architecture inside the approved mutation envelope, but cannot change product semantics, material architecture boundaries, approved mutation paths/scope, active invariants, user-confirmed important consequences, Brain review, user acceptance, `MERGE_ALLOWED` or merge-result state.
- **Mechanical Runtime:** schema, digest, path, current-round object binding, validation-result coherence, Prompt round-trip and role-field checks. It cannot create authority.

## Review and stage Gates

```text
CODEX_EXECUTION
→ valid current-round Return + Evidence Bundle
→ BRAIN_REVIEW
→ Brain review PASS
→ USER_ACCEPTANCE
→ applicable acceptance PASS / justified NOT_APPLICABLE
```

Repository tasks then enter `MERGE_DECISION`; Artifact tasks may close without PR after Artifact review PASS. Repository tasks do not close merely by setting the temporary Capsule to `CLOSED`.

## Merge continuity

```text
Brain Review PASS + current PR CI PASS
→ exact Merge Candidate Freeze for the reviewed PR head
→ applicable User Acceptance bound to that freeze
→ separate explicit USER final merge authorization bound to freeze + acceptance
→ actual merge
→ Brain rechecks current repository evidence
→ minimal Task Completion Pointer
→ optional post-merge Merged Change Projection when navigation/context continuity is materially useful
```

No automatic Promotion Adapter is part of Joyflow.


## Hybrid Path Discovery narrow repair

Path discovery is current-repository-evidence-first. The Web Brain uses accurate repository/PR/commit/diff/file evidence that is actually accessible to it and closes the path boundary directly when sufficient. If material unpushed, runtime, local-environment or structural facts remain missing, Local Codex supplies bounded pure read-only Technical Discovery. Under the current active Development Project Instruction this discovery needs no separate user approval; any later mutation remains bound to explicit user approval. Logical Brain authorization is not automatic Local Codex invocation, and no specific connector, agent, service, scheduler, repository cache or autonomous loop is required.

## Codex bounded technical judgment

The Brain decides the product meaning, overall technical route, final path boundary and validation target. Codex does not blindly execute those assumptions: before mutation it checks the current approved repository/artifact reference and the route assumptions. Equivalent local implementation choices may continue in the same turn. Any conflict with direct repository evidence, insufficient approved paths, or reference mismatch returns `BLOCKED` with evidence and no invented completion object. This is one execution layer with technical responsibility, not a second semantic Brain.


## Non-exhaustive technical route space

The Web Brain does not hard-code a closed implementation menu. It defines the approved product semantics, non-goals, path boundary, acceptance conditions, material assumptions and critical questions, and may offer one to three non-exhaustive candidate routes. Codex evaluates all candidates against the current execution object and may choose a route whose important tradeoff is delegated within the approved boundary or propose a demonstrably equivalent alternative. Any path expansion, product/protocol change, compatibility or migration commitment, or important-tradeoff change stops for Brain re-closure and, when the approved object changes, renewed user approval.

This preserves one semantic Brain while preventing Codex from becoming blind execution.

## Current-source replay without a new authority layer

Repository and Artifact facts remain facts of the current source, not facts of an AI-authored record. The existing short-lived Validator rereads deterministic values and reruns approved commands when the task reaches a material boundary. This does not make the Validator a semantic authority: Brain still judges meaning and sufficiency, Codex still chooses bounded implementation, and the user retains every key approval. No persistent observer, signature infrastructure or competing truth source is introduced.

## PR1A + PR1B Discovery and Artifact lifecycle completion

This candidate completes the two shared-lifecycle branches left open by the exact stranger cold review of the prior lifecycle-refactor package. Local or combined discovery now crosses into execution through a formal source object that retains the original read-only Projection, exact Return and selected item IDs. Declared ignored facts use lexical symlink inspection, true subtree pruning and a bounded direct-fact set. Artifact execution now preserves an exact canonical complete output set through Return, final validation and Brain Review, and `NEW_ARTIFACT` uses an approved source-material set rather than an invented source file. The already-closed Repository Base-to-Head route is preserved and regression-tested.
