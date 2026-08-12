# Phase 2 Structural Cognition Continuity

canonical_rule_id: RULE_PHASE2_STRUCTURAL_DISCOVERY_TRIGGER_BOUNDARY
source_section_id: 27::STRUCTURAL_DISCOVERY_TRIGGER_BOUNDARY

Ordinary repository work stays on the existing fast path and carries no structural cognition burden. When the current task has material architecture uncertainty—such as uncertain authority/rule/lifecycle ownership, shared-core responsibility, material dependency direction, runtime relationship, or a change that may require a new long-lived abstraction—the Web Brain creates one exact Structural Decision Frame containing the current question, required dimensions, materiality basis, protected product semantics, non-goals and bounded discovery seed, but does not prescribe the repository architecture or freeze final mutation paths first. Under the current active Development Project Instruction, the Web Brain may authorize this exact bounded pure read-only structural discovery without a separate user approval and without creating user approval state. Codex must answer the exact Brain frame; the final mutation boundary remains unavailable until the structural lifecycle reaches Brain-reviewed CLOSED state.

canonical_rule_id: RULE_PHASE2_CODEX_ARCHITECTURE_PROPOSAL_BRAIN_CLOSURE
source_section_id: 27::CODEX_ARCHITECTURE_PROPOSAL_BRAIN_CLOSURE

Codex owns repository-grounded structural discovery, technical root-cause diagnosis, architecture candidate generation and technical recommendation for the current bounded question. The Web Brain owns project-level architecture review and final technical closure: it may accept, request targeted rediscovery/rework, or return a material product/protocol tradeoff to the user. Codex cannot self-approve a material architecture expansion, change product requirements/non-goals/important tradeoffs, widen final mutation paths, fill Brain review or authorize merge.

canonical_rule_id: RULE_PHASE2_GOAL_CONDITIONED_STRUCTURAL_UNFOLDING
source_section_id: 27::GOAL_CONDITIONED_STRUCTURAL_UNFOLDING

Structural discovery starts from the exact current repository anchor and the current architecture question, then unfolds only relations that are relevant to answering that question and material if wrong. It may expand through authority writers, rule ownership, lifecycle transitions, dependencies, shared core, runtime relations, consumer/producer relations and validation surfaces. It must stop when the question-specific closure obligations are satisfied; unrelated legacy debt is not expanded merely because discovery encounters it. A bounded omission is preserved explicitly rather than silently treated as nonexistent.

canonical_rule_id: RULE_PHASE2_SEMANTIC_STRUCTURAL_FIBER_MAPPING
source_section_id: 27::SEMANTIC_STRUCTURAL_FIBER_MAPPING

A structural relation is a typed semantic derivation, not an ID-only graph edge. Each material relation states its type, subject, source, semantic claim, materiality and exact direct repository observation basis. Direct repository path/source snapshots are tool-produced current-source facts. Codex relations and architecture routes are derived judgments over those facts. A relation ID or matching digest without the semantic mapping does not establish ownership, lifecycle, dependency or authority meaning.

canonical_rule_id: RULE_PHASE2_STRUCTURAL_QUESTION_CLOSURE
source_section_id: 27::STRUCTURAL_QUESTION_CLOSURE

Each goal-conditioned architecture question is copied from the exact Brain Structural Decision Frame and declares the closure dimensions needed for the current decision. The Path Discovery Return must cover every requested dimension exactly once as `CHECKED`, `NOT_APPLICABLE` or `UNRESOLVED`. `CHECKED` and `NOT_APPLICABLE` require the compatible evidence semantics defined by the Validation/Evidence domain; `UNRESOLVED` requires an explicit reason and keeps the structural lifecycle OPEN. Codex cannot recommend a final architecture route while a requested dimension is unresolved. Absence of observed evidence is not evidence of absence, and material hidden/runtime relationships that cannot be established remain unresolved rather than being silently downgraded.

canonical_rule_id: RULE_PHASE2_LOSSLESS_MATERIAL_STRUCTURAL_FOLD
source_section_id: 27::LOSSLESS_MATERIAL_STRUCTURAL_FOLD

The task structural projection is a minimum-sufficient fold for Brain review, not a free-form summary. It must preserve every material semantic relation plus counterevidence, unresolved structural questions and material omissions from the discovery result. Brain may request targeted re-unfolding to the supporting repository observations. Compression may reduce irrelevant detail but may not remove material contradiction, uncertainty, authority boundary or omission information.

canonical_rule_id: RULE_PHASE2_LONG_TERM_STRUCTURAL_PROJECTION
source_section_id: 27::LONG_TERM_STRUCTURAL_PROJECTION

A project may keep one sparse long-term structural projection in the repository when it materially reduces rediscovery cost for long-lived architecture review. It is a derived, non-authoritative navigation/cognitive skeleton anchored to one exact repository commit and source-file byte identities. It may record stable lifecycle anchors, authority boundaries, rule owners, shared-core anchors, major dependency boundaries, material structural exceptions and semantic fibers. It must not mirror all files/functions, become a Repository Cache, become an AI memory database, or compete with current repository facts.

canonical_rule_id: RULE_PHASE2_STRUCTURAL_PROJECTION_FRESHNESS
source_section_id: 27::STRUCTURAL_PROJECTION_FRESHNESS

A long-term structural projection is valid as a historical derived artifact when its based-on commit and source digests replay. When used for a current task, current repository source has precedence. If HEAD equals the based-on commit it is current at HEAD; if HEAD descends from that commit and none of the projection's referenced source paths changed, it may remain current for those referenced sources; if a referenced source changed it is STALE for current use; if the based-on commit is not an ancestor of current HEAD it is CONFLICTED. STALE/CONFLICTED projection claims may navigate discovery but cannot substitute current-source evidence or final technical closure.

canonical_rule_id: RULE_PHASE2_MATERIAL_STRUCTURAL_CHANGE_REFOLD
source_section_id: 27::MATERIAL_STRUCTURAL_CHANGE_REFOLD

The long-term structural projection is updated only when a merged change materially changes the structural skeleton—for example authority ownership, lifecycle boundary, major rule ownership, shared-core responsibility, major dependency boundary or a material structural exception. Ordinary feature implementation details, private helpers, UI changes and local bug fixes do not require projection churn. Any projection update is reviewed as derived repository content in the same human semi-automatic PR/merge chain; Codex discovery does not autonomously promote it.

canonical_rule_id: RULE_PHASE2_STRUCTURAL_RECLOSURE_AND_REGROUNDING
source_section_id: 27::STRUCTURAL_RECLOSURE_AND_REGROUNDING

When current discovery establishes a shared structural root cause that the current feature depends on, would duplicate/worsen, or cannot honestly absorb, the current feature stops for Brain re-closure. A bounded Structural Repair Change Unit may be one PR or a staged PR sequence under one frozen root-cause objective; unrelated architecture cleanup remains out of scope. After such a repair merges, the original product goal may remain, but its old repository grounding, architecture projection, route, final path decision and execution approval are stale. The original goal is re-grounded against the new repository state before any new mutation approval.

canonical_rule_id: RULE_PHASE2_STRUCTURAL_PROJECTION_AUTHORITY_BOUNDARY
source_section_id: 27::STRUCTURAL_PROJECTION_AUTHORITY_BOUNDARY

Current repository direct facts outrank every structural projection. A long-term structural projection is a derived non-authoritative repository artifact, not product authority, execution authority, user authorization, repository canonical truth or an independent architecture truth source. It never self-asserts Brain review or approval status; any update enters the repository only through the ordinary Brain review and user merge chain. A current task projection is temporary by default. Neither projection may authorize architecture change, approval, acceptance, merge or promotion.

canonical_rule_id: RULE_PHASE2_STRUCTURAL_LIFECYCLE_STATE_MACHINE
source_section_id: 27::STRUCTURAL_LIFECYCLE_STATE_MACHINE

The structural cognition lifecycle is conditional and has one exact task-local object chain. No Brain structural frame means `NOT_REQUIRED`. A Brain frame creates an OPEN structural lifecycle. Codex evidence-grounded discovery may produce a recommended route only after every required dimension closes; the Web Brain then records an exact `ACCEPT`, `REWORK` or `USER_DECISION_REQUIRED` disposition against that Codex route. Only an ACCEPT of the exact current route produces CLOSED structural closure and unlocks Final Path. The mutating Handoff binds that closure, Codex reports `PRESERVED` or `DEVIATION_DETECTED` against it, and Brain actual-Diff review consumes every returned material structural consequence before PASS. A deviation or review conflict returns the lifecycle to re-closure rather than being hidden by path/test success.

canonical_rule_id: RULE_PHASE2_LONG_TERM_STRUCTURAL_REFOLD_REVIEW_CHAIN
source_section_id: 27::LONG_TERM_STRUCTURAL_REFOLD_REVIEW_CHAIN

Long-term structural refold is an output of the ordinary reviewed repository-change lifecycle, not a self-authorizing state. Brain actual-structure review decides `NO_REFOLD_REQUIRED` or `REFOLD_REQUIRED` only when the current result materially changes the sparse structural skeleton. A refolded projection records its exact repository basis, reviewed scope, source structural-closure provenance, unresolved items and bounded omissions; its freshness means only currentness of its referenced basis, never proof that no new competing structure exists elsewhere. Current repository evidence always wins on conflict, and a later task re-unfolds relevant current source before relying on the skeleton for technical closure.
