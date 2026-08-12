# Repository Files Policy

canonical_rule_id: JF_DL_NO_SECOND_TRUTH_SOURCE_RULE
source_section_id: 09::NO_SECOND_TRUTH_SOURCE

Do not commit temporary task capsules, Brain reasoning, intermediate Prompts, screenshots or transient repair cycles merely to preserve AI context. Repository files exist for project code, tests, schema, configuration and necessary durable constraints.

canonical_rule_id: JF_DL_REPOSITORY_VISIBLE_FACT_RULE
source_section_id: 09::REPOSITORY_VISIBLE_FACT

A project-specific fact that must survive task closure belongs in an appropriate repository-visible artifact through an approved PR, not in generic Joyflow Project Sources.

canonical_rule_id: JF_DL_AI_COMPATIBLE_STRUCTURE_RULE
source_section_id: 09::AI_COMPATIBLE_STRUCTURE

Repository structure should expose clear ownership, entry points, interfaces, tests and bounded feature slices so a replaceable AI executor can inspect and modify it without reconstructing hidden architecture.

canonical_rule_id: JF_DL_CODE_IDENTIFIER_NAMING_RULE
source_section_id: 09::CODE_IDENTIFIER_NAMING

Code identifiers and repository-visible names should be stable, descriptive and technology-appropriate. Joyflow protocol artifact naming must not leak into product code unless the repository explicitly adopts it.

canonical_rule_id: JF_DL_FEATURE_SLICE_LAYOUT_RULE
source_section_id: 09::FEATURE_SLICE_LAYOUT

Where the repository architecture supports feature slices, keep feature-owned code, tests and interfaces locally discoverable while preserving shared-core boundaries.

canonical_rule_id: JF_DL_PROTECTED_CORE_PLACEMENT_RULE
source_section_id: 09::PROTECTED_CORE_PLACEMENT

Protected shared core, routing, permission, storage and cross-module state must have explicit repository-visible ownership and strict validation boundaries.

canonical_rule_id: JF_DL_REPO_ARTIFACT_PLACEMENT_RULE
source_section_id: 09::REPO_ARTIFACT_PLACEMENT

Durable project artifacts belong only where the repository architecture and file policy assign them. Temporary task transfer artifacts do not gain repository placement merely because they are useful to AI.

canonical_rule_id: JF_DL_REPO_GOVERNANCE_FILE_RULE
source_section_id: 09::REPO_GOVERNANCE_FILE

Repository governance files must stay minimal, project-specific and mechanically useful. Generic Joyflow protocol explanations remain in Joyflow Project Sources, not application repositories.

canonical_rule_id: RULE_SHORT_LIVED_EXECUTION_EVIDENCE_RUNNER
source_section_id: 09::SHORT_LIVED_EXECUTION_EVIDENCE_RUNNER

`tools/capture_execution_evidence.py` is a repository-owned, current-task helper that executes one bounded command and emits a canonical raw capture. It is used locally and may be replayed by CI where appropriate. It does not run persistently, observe GitHub autonomously, modify PR text, approve work, or become a competing project truth source.

canonical_rule_id: RULE_TYPED_EXECUTION_EVIDENCE_RUNNER_MODES
source_section_id: 09::TYPED_EXECUTION_EVIDENCE_RUNNER_MODES

The short-lived execution Evidence runner uses typed modes that derive object identity from the observed target: repository HEAD from Git, Artifact SHA-256 from file bytes, repository-file content from the repository root, repository Diff from exact refs, and test output from an approved command on that object. Callers do not supply the repository/artifact identity that the capture claims to have observed. The runner produces facts only; Codex records separate technical derivations.

canonical_rule_id: RULE_SPARSE_STRUCTURAL_PROJECTION_REPO_FILE_BOUNDARY
source_section_id: 09::SPARSE_STRUCTURAL_PROJECTION_REPO_FILE_BOUNDARY

A long-term structural projection is repository-visible only when rediscovery cost/continuity justify it and it remains sparse, derived and non-authoritative. It must not mirror the repository, become a task/history database or require updates for ordinary local implementation detail; material structural refolds use the normal reviewed PR/merge path.

canonical_rule_id: RULE_TRANSPORT_ONLY_EVIDENCE_SURFACE
source_section_id: 09::TRANSPORT_ONLY_EVIDENCE_SURFACE

Large/complex current-round Evidence may be written only to an explicitly approved `TRANSPORT_ONLY_EVIDENCE_SURFACE` outside product main/development history. The surface is a temporary transport location, not a Repository First project truth source, governance source, product Artifact destination or PR promotion target. GitHub Evidence write is remote mutation and therefore must already be included in an exact user-approved mutation/material execution object. Known push side effects must be absent or explicitly included in that approved object; otherwise the transport surface is invalid and Joyflow falls back.

canonical_rule_id: RULE_EPHEMERAL_EVIDENCE_RETENTION_CLEANUP
source_section_id: 09::EPHEMERAL_EVIDENCE_RETENTION_CLEANUP

Transported mechanical Evidence is `EPHEMERAL_BY_DEFAULT`. The approved execution object freezes the exact temporary ref, retention policy and cleanup condition before upload. Default retention lasts until the current review object reaches its frozen terminal condition. For a merged repository PR, the existing exact `TASK_COMPLETION_POINTER` is the terminal basis: the Brain may then build a cleanup continuation that binds the original user-approved mutating Projection, the exact transport receipt, the exact temporary ref/transport commit and that completion pointer. Codex may delete only that exact ref without a second user approval, and only while the ref still resolves to the transport commit named by the receipt; a moved/repurposed ref blocks cleanup. Cleanup is a bounded follow-up mutation, not a background watcher/service, and branch/ref deletion does not claim cryptographic or platform-level erasure. Materially non-reproducible Evidence may be retained only with an explicit reason in the approved object. Secrets, credentials or material unsuitable for GitHub must never rely on later cleanup and instead use a different approved transport.



canonical_rule_id: RULE_EPHEMERAL_EVIDENCE_TERMINAL_CLEANUP_CONTINUATION
source_section_id: 09::EPHEMERAL_EVIDENCE_TERMINAL_CLEANUP_CONTINUATION

A preauthorized ephemeral cleanup is a continuation of the original user-approved Evidence transport mutation, not a new product execution authority. It must bind the original mutating Projection and user approval, the exact current-round transport receipt, the exact temporary repository/ref, and current terminal evidence. For merged repository work the terminal evidence is the exact validated `TASK_COMPLETION_POINTER`. Before deletion, the current remote ref must still resolve to the receipt's exact transport commit. Any changed ref, absent terminal evidence, changed task/round identity or retained-Evidence policy blocks cleanup. The continuation may delete only the exact temporary transport ref and may not modify product branches, evidence contents, PR state, acceptance, merge state or any other repository object.
