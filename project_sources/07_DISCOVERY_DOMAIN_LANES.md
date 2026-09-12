# Repository Evidence, Hybrid Path Discovery and Domain Lanes

canonical_rule_id: JF_DL_REPOSITORY_EVIDENCE_REFERENCE_RULE
source_section_id: 07::REPOSITORY_EVIDENCE_REFERENCE

The repository-evidence fiber stores bounded observations, evidence references, the path-discovery state and unresolved questions. It must not copy the repository or become long-term project memory.

canonical_rule_id: JF_DL_GITHUB_FIRST_PATH_DISCOVERY_RULE
source_section_id: 07::GITHUB_FIRST_PATH_DISCOVERY

The Web Brain first reads the current GitHub repository, PR, commit, diff and relevant files to identify behavior entry points, candidate paths, dependencies and validation entries. Existing GitHub evidence must not be redundantly delegated to Codex by default.

canonical_rule_id: JF_DL_CODEX_SUPPLEMENTAL_LOCAL_DISCOVERY_RULE
source_section_id: 07::CODEX_SUPPLEMENTAL_LOCAL_DISCOVERY

Codex performs bounded local read-only discovery only when GitHub evidence is insufficient or unavailable, or when unpushed state, runtime resolution or local environment facts are materially required. Under the current active Development Project Instruction, the Web Brain may authorize that exact pure read-only discovery without a separate user approval; the discovery prompt forbids mutation, material artifact production, commits, PR creation/update and migration.

canonical_rule_id: JF_DL_BRAIN_FINAL_PATH_BOUNDARY_RULE
source_section_id: 07::BRAIN_FINAL_PATH_BOUNDARY

Codex may report confirmed and candidate local paths but may not authorize them. The Web Brain integrates GitHub and local evidence, decides the final repository-relative allowed paths and presents that bounded object for user approval before mutating execution.

canonical_rule_id: JF_DL_PATH_DISCOVERY_RETURN_RULE
source_section_id: 07::PATH_DISCOVERY_RETURN

A Path Discovery Return binds the current project, task, round and Projection; reports repository identity, local state, discovered paths, dependency edges, validation entries, local-only findings and unresolved questions; and mechanically declares that no mutation was performed.

canonical_rule_id: JF_DL_DOMAIN_LANE_CLASSIFICATION_RULE
source_section_id: 07::DOMAIN_LANE_CLASSIFICATION

Domain lanes are programming-technology lanes. Active material and technical decisions explicitly declare relevant lanes; risk markers may require specific lanes and validation extensions.

canonical_rule_id: JF_DL_READ_ONLY_DISCOVERY_RULE
source_section_id: 07::READ_ONLY_DISCOVERY

Read-only discovery is an executable but non-mutating Codex task directly authorized by the Web Brain for the exact bounded question/scope. It creates no user approval state. It may establish local paths, entry points and evidence but may not mutate project files, create material artifacts, create/update commits or PRs, run migrations, or decide final allowed paths.


canonical_rule_id: JF_DL_GITHUB_PATH_EVIDENCE_OBJECT_BINDING_RULE
source_section_id: 07::GITHUB_PATH_EVIDENCE_OBJECT_BINDING

A GITHUB_CONFIRMED path must be supported by typed repository evidence bound to the current repository and observed commit or PR head. Brain inference remains GITHUB_DERIVED and may not masquerade as direct GitHub observation.

canonical_rule_id: JF_DL_FINAL_PATH_DECISION_SOURCE_BINDING_RULE
source_section_id: 07::FINAL_PATH_DECISION_SOURCE_BINDING

The Web Brain owns the final path decision, may narrow or combine discovered paths, and records the evidence or bounded derivation basis for every final path. A local or combined path binds the exact current Path Discovery Return digest.

canonical_rule_id: JF_DL_WORKTREE_FINGERPRINT_READ_ONLY_RULE
source_section_id: 07::WORKTREE_FINGERPRINT_READ_ONLY

Read-only discovery records canonical before and after fingerprints of HEAD, staged changes, tracked worktree changes and untracked file content. A changed fingerprint blocks a no-mutation result without adding a trusted observer or persistent monitoring service.

canonical_rule_id: JF_DL_LITERAL_PREFIX_PATH_PATTERN_RULE
source_section_id: 07::LITERAL_PREFIX_PATH_PATTERN

Recursive allowed paths use only a literal repository-relative prefix followed by `/**`. Global and intermediate wildcard patterns are forbidden.


canonical_rule_id: JF_DL_LOCAL_DISCOVERY_SEAL_INPUT_RULE
source_section_id: 07::LOCAL_DISCOVERY_SEAL_INPUT

The first mutating capsule revision that marks local discovery completed is sealed only while the exact read-only Projection and PATH_DISCOVERY_RETURN are supplied and validated together. A digest-shaped value alone is insufficient.


canonical_rule_id: JF_DL_FINAL_PATH_GITHUB_COVERAGE_RULE
source_section_id: 07::FINAL_PATH_GITHUB_COVERAGE

A `GITHUB_CONFIRMED` final path must stay inside at least one path actually covered by the current typed `GITHUB_PATH_EVIDENCE`; a file observation cannot authorize a broader directory. A `GITHUB_DERIVED` or `COMBINED` path names the exact observed source paths from which the Brain derives the final boundary. Generic repository evidence, test-plan evidence and user decisions may support reasoning but may not occupy the typed GitHub path-source field.

canonical_rule_id: JF_DL_GITHUB_PATH_SCOPE_CONTENT_BINDING_RULE
source_section_id: 07::GITHUB_PATH_SCOPE_CONTENT_BINDING

Typed GitHub path evidence binds one exact current GitHub object, a compatible object type, the raw-object SHA-256 and a canonical observed-path scope. `FILE` evidence represents one exact file only. Tree, Commit, PR and PR-Diff evidence use an explicit path set. Changing the observed paths without changing the exact backing object claim and raw-object digest is rejected.

canonical_rule_id: JF_DL_LOCAL_DISCOVERY_TYPED_ITEM_EVIDENCE_RULE
source_section_id: 07::LOCAL_DISCOVERY_TYPED_ITEM_EVIDENCE

Every Codex local discovery item has a stable item ID and compatible Evidence kind and subject. Path observations, path candidates, dependency edges, validation entries, local findings and worktree captures cannot substitute for one another merely because an Evidence ID exists.

canonical_rule_id: JF_DL_LOCAL_RETURN_ITEM_SOURCE_BINDING_RULE
source_section_id: 07::LOCAL_RETURN_ITEM_SOURCE_BINDING

A `LOCAL_DISCOVERY` or `COMBINED` final path binds the exact current Path Discovery Return and names the confirmed local path item IDs that support that final path. Optional dependency, validation and local-finding IDs must exist in the same Return and concern the selected path. A Return digest alone is insufficient.

canonical_rule_id: JF_DL_UNRESOLVED_LOCAL_QUESTION_BLOCK_RULE
source_section_id: 07::UNRESOLVED_LOCAL_QUESTION_BLOCK

A Path Discovery Return may honestly report unresolved questions, but a mutating Final Path Decision cannot be sealed from that Return until those questions are cleared. The Brain may not silently ignore unresolved local path facts.

canonical_rule_id: JF_DL_DETERMINISTIC_WORKTREE_CAPTURE_RULE
source_section_id: 07::DETERMINISTIC_WORKTREE_CAPTURE

Read-only discovery uses the repository-owned `tools/capture_worktree_fingerprint.py` helper to capture staged diff bytes, tracked worktree diff bytes and a canonical untracked-file manifest. Before and after are distinct capture records. Equal state fingerprints support a no-mutation claim; the helper is a short-lived mechanical check, not a trusted observer or persistent service.

canonical_rule_id: RULE_GITHUB_PATH_REPOSITORY_SOURCE_REPLAY
source_section_id: 07::GITHUB_PATH_REPOSITORY_SOURCE_REPLAY

Typed GitHub path evidence is replayed against the supplied repository and exact observed Commit before it can support a mutating Projection. Every observed file or literal-prefix directory must match at least one path in that Commit. Brain remains the final path-boundary owner, but it cannot turn a self-authored path list into direct GitHub observation merely by recomputing claims and digests.

canonical_rule_id: RULE_LOCAL_DISCOVERY_REPOSITORY_SOURCE_REPLAY
source_section_id: 07::LOCAL_DISCOVERY_REPOSITORY_SOURCE_REPLAY

Operational Path Discovery validation rereads the current repository. Confirmed and candidate paths, dependency endpoints, validation entries and affected local-finding paths must exist in the supplied repository. The Validator independently recomputes HEAD, staged Diff, tracked worktree Diff and the canonical untracked manifest and compares them with both distinct capture records. Local direct Evidence rows are TOOL-produced; Codex may derive technical meaning but may not self-author a direct local observation.

canonical_rule_id: RULE_PR_DIFF_EXACT_BASE_HEAD_REPLAY
source_section_id: 07::PR_DIFF_EXACT_BASE_HEAD_REPLAY

A typed `PR_DIFF` path observation binds an exact base Commit and exact head Commit. Operational validation first requires the approved Base to be an ancestor of the result Head, then computes the exact two-point `git diff --name-only base head`. A divergent branch, merge-base substitution or path that merely exists in the Head tree is not evidence of change from the approved Base.

canonical_rule_id: RULE_LOCAL_DISCOVERY_DIRECT_FACT_DERIVATION_SPLIT
source_section_id: 07::LOCAL_DISCOVERY_DIRECT_FACT_DERIVATION_SPLIT

Local path existence and bounded worktree bytes are direct TOOL facts. Candidate relevance, dependency relation, validation-entry suitability and local technical findings are explicit CODEX derivations citing the exact direct path observations. The Validator checks source existence and citation continuity; it does not label Codex semantic interpretation as a tool observation.

canonical_rule_id: RULE_BOUNDED_DECLARED_IGNORED_PATH_COVERAGE
source_section_id: 07::BOUNDED_DECLARED_IGNORED_PATH_COVERAGE

Read-only worktree fingerprinting covers tracked state, non-ignored untracked content and only ignored/runtime objects declared material to the current task. Coverage is typed as exact files, exact symbolic links, or explicitly bounded recursive directory roots with exclusions. A directory cannot masquerade as one empty file digest. Joyflow does not claim the full local filesystem is unchanged and does not create an unbounded ignored-file monitor.

canonical_rule_id: RULE_REPOSITORY_BASE_RESULT_ANCESTRY
source_section_id: 07::REPOSITORY_BASE_RESULT_ANCESTRY

A Repository execution result is legal only when the exact user-approved Base Commit is an ancestor of the exact result Head. Diff, touched-path and final-validation claims bind this same Base-to-Head transition. Existing Commits on divergent branches cannot be relabelled as the approved execution result.

canonical_rule_id: RULE_TYPED_IGNORED_COVERAGE_OBJECTS
source_section_id: 07::TYPED_IGNORED_COVERAGE_OBJECTS

Declared ignored/runtime coverage distinguishes exact files, exact symbolic links and bounded recursive directories. Exact-file and exact-symlink entries reject an existing object of another type. Recursive directory coverage generates a canonical relative-path, type and content manifest only under the declared root and exclusions. No other ignored tree is scanned or claimed unchanged.

canonical_rule_id: JF_DL_DISCOVERY_SOURCE_OBJECT_TRANSITION_RULE
source_section_id: 07::DISCOVERY_SOURCE_OBJECT_TRANSITION

A mutating execution Projection that uses local or combined discovery must carry a formal Discovery Source Object binding the exact original read-only Discovery Projection digest, exact Path Discovery Return digest and exact selected Return item IDs. The Return remains owned by its original discovery Projection; it is never reassigned to the later execution Projection.

canonical_rule_id: JF_DL_IGNORED_SYMLINK_NO_FOLLOW_RULE
source_section_id: 07::IGNORED_SYMLINK_NO_FOLLOW

An exact ignored symlink is inspected with lexical `lstat` and `readlink`. Its target text is recorded without following or reading the target object unless that target is separately inside the approved observation boundary.

canonical_rule_id: JF_DL_IGNORED_EXCLUSION_PRUNING_RULE
source_section_id: 07::IGNORED_EXCLUSION_PRUNING

A bounded recursive ignored-directory exclusion prunes the directory before descent. The excluded directory and every descendant are absent from the Manifest and are not opened by the capture helper.

canonical_rule_id: JF_DL_DECLARED_IGNORED_DIRECT_FACT_RULE
source_section_id: 07::DECLARED_IGNORED_DIRECT_FACT

Only exact files, exact symlinks and bounded recursive entries declared in the current ignored-coverage contract join the local direct-fact set. Undeclared ignored content remains invisible and cannot support a Path Discovery item.


canonical_rule_id: RULE_CODEX_GOAL_CONDITIONED_STRUCTURAL_DISCOVERY
source_section_id: 07::GOAL_CONDITIONED_STRUCTURAL_DISCOVERY

For material architecture uncertainty, the existing read-only Path Discovery task may additionally return a goal-conditioned structural discovery projection before final mutation paths are selected. It binds the current architecture question to the approved task goal, derives typed semantic relations from direct current-repository observations, closes each requested structural dimension explicitly and may recommend a technical route only when no requested structural dimension remains unresolved. It remains read-only and cannot decide the final mutation boundary.

canonical_rule_id: RULE_STRUCTURAL_DISCOVERY_QUESTION_CLOSURE_AND_TARGETED_REWORK
source_section_id: 07::STRUCTURAL_DISCOVERY_QUESTION_CLOSURE_AND_TARGETED_REWORK

Goal-conditioned structural discovery expands from the Brain-owned question through only the repository relations needed to answer its required dimensions. Closure is question-specific: every requested dimension must be evidence-closed or remain explicitly unresolved, and hidden/runtime relations that matter but cannot be established remain unknown rather than being inferred absent. A Brain `REWORK` disposition must name the exact unresolved structural subject, why the current Codex route does not close it and the targeted reopen scope; Codex re-unfolds only that bounded gap instead of rescanning the project or reopening unrelated legacy architecture debt.
