# Phase 2 Architecture Convergence and Closure

canonical_rule_id: RULE_ARCHITECTURE_CONVERGENCE_SIX_STAGE_MAINLINE
source_section_id: 28::SIX_STAGE_MAINLINE

Joyflow's user-facing development mainline is Product Closure, conditional Technical Discovery, Technical Closure, Execution, exact-object Brain Review, and User Accept/Merge. Existing fibers, schemas and mechanical gates support these stages but do not create additional user-facing authorities or mandatory conversational phases. Technical Discovery is conditional: when Brain-accessible current repository evidence is sufficient for closure, it is skipped; when material repository/local/runtime facts remain unknown, the Web Brain frames a bounded discovery question for Local Codex.

canonical_rule_id: RULE_PRODUCT_SEMANTICS_BEFORE_UNKNOWN_IMPLEMENTATION
source_section_id: 28::PRODUCT_BEFORE_IMPLEMENTATION

Before Technical Discovery, User and Web Brain close product meaning, desired result, must-have/must-not-have behavior, non-goals, active invariants and already-decided important tradeoffs. Unknown implementation details remain open until repository-grounded discovery establishes the relevant facts. The Web Brain must not manufacture repository facts or freeze an implementation merely because the local repository has not yet been inspected.

canonical_rule_id: RULE_PR2X_READ_ONLY_DISCOVERY_ACTIVATION_BOUNDARY
source_section_id: 28::READ_ONLY_DISCOVERY_AUTHORIZATION

The current active Joyflow Development Project Instruction, explicitly confirmed by the user, authorizes the Web Brain to authorize strictly bounded pure read-only Local Codex Technical Discovery without a separate user approval. The read-only authorization permits repository/code/configuration inspection, call-chain and architecture discovery, root-cause investigation, technical route comparison and consequence analysis. It does not permit file/data mutation, material side-effect execution, Commit, Push, branch mutation, PR creation/update, migration, user acceptance or merge. Any later mutation/material execution requires explicit user approval of the current mutation execution envelope.

canonical_rule_id: RULE_TECHNICAL_DISCOVERY_TYPED_TRUTH_BOUNDARY
source_section_id: 28::DISCOVERY_TYPED_TRUTH

A Technical Discovery Return distinguishes direct repository facts, technical inference, candidate routes, technical consequences, recommendation and unresolved unknowns. Codex recommendation or inference is not promoted to direct repository fact. Web Brain owns the final technical closure and checks material claims against the exact current evidence available to it.

canonical_rule_id: RULE_BRAIN_OUTCOME_CODEX_IMPLEMENTATION_BOUNDARY
source_section_id: 28::BRAIN_CODEX_TECHNICAL_BOUNDARY

Web Brain owns product-semantic closure, material technical consequences, critical invariants, technical outcome boundaries and validation obligations. Local Codex owns repository-grounded implementation judgment inside the approved execution envelope: it may adapt implementation details, debug, locally refactor, select equivalent implementation techniques and add necessary regression validation without renewed user approval. Codex must stop when safe completion requires a material product-semantic change, an unresolved user-owned tradeoff, an active invariant change, material mutation-scope expansion, or inability to complete required validation.

canonical_rule_id: RULE_MUTATION_EXECUTION_ENVELOPE_APPROVAL_BINDING
source_section_id: 28::MUTATION_EXECUTION_ENVELOPE

User mutation approval binds a stable mutation execution envelope rather than one transient execution attempt. The envelope carries the product goal/result, must-preserve and must-not-happen obligations, active product semantics and invariants, user-confirmed consequence boundaries, mutation scope/repository boundary, minimum validation obligations and stop/reclosure conditions. Attempt-local Projection/Capsule identities may change without renewed user approval only when the authorization envelope remains semantically identical. A material envelope change invalidates the prior mutation approval.

canonical_rule_id: RULE_SAME_ENVELOPE_REWORK_NO_REAPPROVAL
source_section_id: 28::SAME_ENVELOPE_REWORK

Brain Review failure or User Acceptance failure does not automatically create a new approval cycle. If the defect is failure to satisfy the already-approved execution envelope, the task stays in the same approval round/cycle: Web Brain may produce a bounded rework handoff, the transition event records the review/acceptance failure, and Local Codex may perform another implementation attempt under the same mutation approval. Only a material execution-envelope change opens a new reclosure/approval cycle. No unattended rework loop is introduced; each Brain-to-Codex handoff remains an explicit human semi-automatic handoff.

canonical_rule_id: RULE_CURRENT_FACING_SEMANTIC_MIGRATION_CLOSURE
source_section_id: 28::CURRENT_FACING_SEMANTIC_MIGRATION

A material semantic convergence is not closed merely because one canonical Project Source and one Runtime implementation agree. For the converged semantic contract, every current-facing consumer actually used by the current Joyflow path must either express the converged semantics or be explicitly historical/non-authoritative. When applicable this includes the Bootloader, canonical Project Sources, Machine Model, Runtime, Schema/Compiler/Validator, generator fixtures, generated user-approval material, generated Codex handoff/Prompt material, current Golden/examples and targeted tests. This is a bounded closure obligation for the semantic change being migrated, not a requirement to build a general semantic-monitoring service or to scan unrelated historical material.

canonical_rule_id: RULE_PRODUCT_TOLERANCE_USER_AUTHORITY
source_section_id: 28::PRODUCT_TOLERANCE_AUTHORITY

Material operating assumptions distinguish descriptive conditions from product tolerances. A descriptive condition may be user-confirmed, repository-observed or a Brain technical inference with exact provenance. A product tolerance—such as acceptable downtime, acceptable data-loss consequence, acceptable manual recovery or an important recurring cost tradeoff—is user-owned and must be USER_CONFIRMED. Brain and Codex may explain technical consequences but may not invent the user's acceptability boundary.

canonical_rule_id: RULE_CONTEXTUAL_RISK_ASSURANCE_DISPOSITION
source_section_id: 28::CONTEXTUAL_RISK_ASSURANCE

Risk markers are primarily analysis triggers, not automatic answers. Contextual markers such as storage/shared-state/route/cross-module concerns are assessed from the real failure mechanism, technical consequence, recoverability, material operating conditions, active invariants and user-confirmed tolerances. That disposition may increase or decrease assurance depth relative to a generic default. Hard-floor risks involving protocol/core authority, payment custody, irreversible data or other explicitly hard-floor classes retain their mechanical minimum and cannot be downgraded merely because the product is small.

canonical_rule_id: RULE_ACTIVE_GLOBAL_INVARIANT_NOT_RESIDUAL_WAIVER
source_section_id: 28::GLOBAL_INVARIANT_BOUNDARY

An active GLOBAL_INVARIANT cannot be waived by recording `RESIDUAL_ACCEPTED_BY_USER`. If the user truly changes an invariant product requirement, that is an explicit product-semantic change that must modify/supersede the invariant and re-close the affected task. Risk acceptance may close a bounded residual only when it does not contradict an active invariant.

canonical_rule_id: RULE_FAILURE_MECHANISM_TARGETED_VALIDATION
source_section_id: 28::FAILURE_MECHANISM_VALIDATION

Joyflow does not pursue exhaustive enumeration of theoretical concurrency/failure interleavings. For material invariants and high-consequence behavior, Brain uses current architecture/repository evidence to identify failure mechanisms that can break the required result and derives representative, boundary and high-risk validation from those mechanisms. Validation depth may be strengthened during execution without renewed approval; minimum validation obligations already inside the mutation execution envelope may not be silently weakened.

canonical_rule_id: RULE_TARGET_CLAIM_EVIDENCE_SUPPORTED_CLAIM_SEPARATION
source_section_id: 28::SUPPORTED_CLAIM_BOUNDARY

A target operating/performance/reliability claim is not automatically an evidence-supported claim. Brain Review may conclude only to the level established by the current exact validation/evidence and must preserve known unsupported regions as limits. Existing semantic `CONSTRAINT`/`VALIDATE`, Evidence and known-limits structures carry this boundary; no new operating-envelope truth source is created.

canonical_rule_id: RULE_EVIDENCE_TRANSPORT_EXACT_CANONICAL_BUNDLE_BYTES
source_section_id: 28::EVIDENCE_EXACT_BYTES

When GitHub transport is needed for a large/complex current-round Evidence Bundle, the transported exact object bytes are the canonical bytes of that exact Evidence Bundle. A receipt cannot separately name one Evidence Bundle while hashing unrelated transport bytes. The temporary ref must remain inside the dedicated positive `refs/heads/joyflow-evidence/` namespace and transport remains transport-only, never product/governance PR truth.

canonical_rule_id: RULE_EVIDENCE_CLEANUP_GENERIC_TASK_TERMINAL
source_section_id: 28::EVIDENCE_TASK_TERMINAL

Ephemeral Evidence cleanup is eligible from exact task-terminal evidence, not only from a merged-PR pointer. Supported terminal outcomes may include merged, completed-without-PR, rejected, abandoned, cancelled and superseded. Cleanup deletes only the exact preauthorized temporary ref while it still points to the receipt commit. Cleanup authorization does not imply background execution: Web Brain produces the bounded continuation and the user-mediated/local Codex handoff performs it; no watcher, daemon or scheduler is required.

canonical_rule_id: RULE_ROLE_EXECUTABILITY_WEB_BRAIN_LOCAL_CODEX
source_section_id: 28::ROLE_EXECUTABILITY

Every mandatory Joyflow step must be executable by the real role that owns it. Web Brain is web-only and must not require direct local-filesystem/runtime access. Local Codex is the local repository executor and must not require Web Brain private chat context; Brain-to-Codex execution materials are complete and self-contained. Logical authorization does not imply automatic invocation. Handoffs remain user-mediated or use another explicitly available transport. GitHub/repository evidence is preferred when Brain-accessible, but no specific connector is mandatory; exact user-provided material with object identity is the fallback. If a required role is unavailable, Joyflow pauses rather than promoting another role into its authority.

canonical_rule_id: RULE_DEVELOPMENT_PROFILE_DEPTH_CONVERGENCE
source_section_id: 28::DEVELOPMENT_DEPTH

`DEVELOPMENT_LIGHT`, `DEVELOPMENT_STANDARD` and `DEVELOPMENT_STRICT` are compatibility route aliases for one DEVELOPMENT workflow whose material distinction is assurance/validation depth. This convergence candidate preserves the aliases to avoid unnecessary migration risk; user-facing reasoning treats them as depth rather than separate development architectures. Physical alias removal and Runtime module restructuring are deferred to a later engineering-optimization review after semantic closure.

canonical_rule_id: RULE_EXACT_GITHUB_REVIEW_SINGLE_SEMANTIC_REVIEW
source_section_id: 28::EXACT_GITHUB_REVIEW

For repository mutation, Web Brain Review consumes the exact current PR head, actual diff, current CI/validation, Codex Return and required Evidence; a second conceptual PR Review is not a separate semantic authority. If Brain cannot directly access the GitHub object, exact user-provided material plus commit/path/digest identity is an allowed transport fallback. Transport fallback never lowers the exact-object review standard.
