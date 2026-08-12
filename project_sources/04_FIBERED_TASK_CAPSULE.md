# Fibered Task Capsule

canonical_rule_id: JF_DL_TASK_CAPSULE_TEMPORARY_RULE
source_section_id: 04::TASK_CAPSULE_TEMPORARY

A Fibered Task Capsule carries only current-task activity state. It may reference repository evidence but must not copy or replace repository canonical state. Its digests bind the current object and detect ordinary mismatch; they do not claim an immutable history or hostile-tamper resistance.

canonical_rule_id: JF_DL_STAGE_FIBER_CYCLE_SEPARATION_RULE
source_section_id: 04::STAGE_FIBER_CYCLE_SEPARATION

`stage` states where work currently is; `active_fibers` state which local dimensions are expanded; `cycle` identifies the current material reclosure / mutation-authorization boundary. A same-envelope implementation retry is a new execution attempt inside the same cycle, represented by the new current Capsule/Projection/Return revision and transition event rather than by a second lifecycle object. These are independent mechanical dimensions.

canonical_rule_id: JF_DL_EVENT_CONSTRAINED_LIFECYCLE_RULE
source_section_id: 04::EVENT_CONSTRAINED_LIFECYCLE

A new Capsule starts only at the selected route's registered initial stage. When Brain creates a later revision inside the current task, the new object binds the exact prior packet supplied for that transition, previous stage, route, cycle reason, anchor delta and fiber delta. A sealed packet remains self-contained for later compilation. Joyflow does not maintain an autonomous or immutable event database.

canonical_rule_id: JF_DL_OPTIONAL_FIBER_RULE
source_section_id: 04::OPTIONAL_FIBERS

The fixed core is task anchor and progress. Semantic, repository-evidence, decision-boundary, validation, authority and execution-review fibers activate only when the selected route or stage requires them.

canonical_rule_id: JF_DL_NARROW_SPIRAL_RULE
source_section_id: 04::NARROW_SPIRAL

A cycle increments only when the task must materially re-close its execution authorization envelope—for example new evidence reverses a material decision, testing discovers a new root cause that changes the approved boundary, or material scope changes. Brain Review failure, User Acceptance failure, or another implementation retry does not increment the cycle when the already-approved envelope remains semantically identical; those are new execution attempts inside the current cycle. Ordinary stage progress also does not increment it.

canonical_rule_id: JF_DL_FROZEN_LINEAGE_RULE
source_section_id: 04::FROZEN_LINEAGE

Within the current task, changing or removing a frozen fiber requires an explicit new revision and update or invalidation of dependent fibers. This is ordinary packet continuity against drift and mismatch. It is not a cryptographic chain and does not defend against a malicious user rewriting local files.

canonical_rule_id: JF_DL_DERIVED_GATE_SNAPSHOT_RULE
source_section_id: 04::DERIVED_GATE_SNAPSHOT

Mechanical Gate results are derived from the sealed Capsule and cannot be supplied as caller-controlled conclusions. Mutation/material execution approval and merge approval are not mechanically inferred; they remain user-owned decisions recorded by the Web Brain after the explicit decision occurs. Bounded pure read-only Codex discovery is the explicit exception: the Web Brain may authorize the exact read-only object directly, and that authorization creates no user approval state.

canonical_rule_id: JF_DL_LIGHTWEIGHT_REFERENCE_GRAPH_RULE
source_section_id: 04::LIGHTWEIGHT_REFERENCE_GRAPH

The Capsule may use bounded dependency, effect, preservation, conflict, validation, evidence and supersession links. It is not a persistent knowledge graph.

canonical_rule_id: JF_DL_POST_MERGE_RELEASE_RULE
source_section_id: 04::POST_MERGE_RELEASE

After the Web Brain verifies current repository materials showing the approved PR was merged, the full Capsule stops evolving. Only a minimal result pointer may remain when useful; project truth is read from the repository.

canonical_rule_id: JF_DL_SINGLE_ACTIVE_TASK_PER_PROJECT_ROUND_RULE
source_section_id: 04::SINGLE_ACTIVE_TASK_PER_PROJECT_ROUND

For each project and cycle, Joyflow has one current task and one current execution attempt at a time. A newer same-cycle attempt supersedes the prior attempt-local Projection, Codex Return and Evidence Bundle while the stable mutation authorization envelope remains unchanged. The Web Brain owns this sequencing rule. Joyflow does not add a global scheduler, task lease service or parallel-task control plane. Mechanical artifacts bind `project_id`, `task_id`, cycle/round identity and the current attempt-local Projection so an earlier cycle or superseded attempt cannot silently substitute for the current one.

canonical_rule_id: JF_DL_STAGE_GATE_BLOCKING_RULE
source_section_id: 04::STAGE_GATE_BLOCKING

Derived Gates are actual stage-entry blockers, not informational labels. `BRAIN_REVIEW` requires a valid current-round Codex Return and Evidence Bundle. For repository PR tasks, Brain Review PASS is first sealed in the `BRAIN_REVIEW` stage, Brain Review PASS plus current PR CI PASS produces the exact Merge Candidate Freeze, and only then may the Capsule enter `USER_ACCEPTANCE` bound to that freeze. `MERGE_DECISION` requires the same exact freeze binding plus completed applicable User Acceptance and PR review PASS. Artifact tasks keep their applicable acceptance path without a repository freeze. Repository tasks do not become closed merely by setting the temporary Capsule stage to `CLOSED`; durable completion follows the observed repository merge result.

canonical_rule_id: RULE_TEMPORARY_TASK_OBJECT_LIFECYCLE
source_section_id: 04::TEMPORARY_TASK_OBJECT_LIFECYCLE

Each executable handoff carries one digest-bound temporary task-object lifecycle connecting the route-authorized input object, discovery object, approved mutation/material execution boundary when applicable, expected result contract, execution result, final validation target and Brain review source. These objects remain distinct and every later transition must mechanically bind the immediately preceding object. The lifecycle is current-task state only; it is not a persistent task database or repository truth source.

canonical_rule_id: RULE_STRUCTURAL_COGNITION_CONDITIONAL_LIFECYCLE_FIBER
source_section_id: 04::STRUCTURAL_COGNITION_CONDITIONAL_LIFECYCLE_FIBER

Structural cognition is a conditional dimension inside the existing temporary task lifecycle, not a parallel architecture system. A structurally clear task carries `NOT_REQUIRED` and stays on the ordinary fast path. A structurally escalated task preserves one exact lineage from the Brain structural decision frame, through the Codex structural discovery result and recommended route, the Brain architecture disposition and closed structural boundary, the Codex structural execution result, and the Brain actual-structure review/refold disposition. Each later object binds the exact immediately preceding structural object or digest; an open, stale or mismatched structural state cannot be skipped by later path, execution or review stages.
