# Joyflow Phase 2 Architecture Convergence & Closure Repair Candidate

This package is **CANDIDATE_NOT_BASELINE**. It repairs the exact cold-reviewed Phase2W package (`sha256 7a21e27a9445646c08e05ce7c9de4a6c1d3b2cc30799701126ae5b6bf7c1d053`) and intentionally prioritizes semantic/workflow closure before later engineering cleanup.

## Current convergence target

Joyflow remains one real **Web Brain** + one **Local Codex** execution layer + **User** product/authorization control + **GitHub/repository** long-term fact. It does not introduce a background Joyflow controller, scheduler, autonomous rework loop, second Brain/Executor, automatic approval, automatic acceptance, automatic promotion or automatic merge.

The user-facing mainline is:

`PRODUCT CLOSURE → conditional TECHNICAL DISCOVERY → TECHNICAL CLOSURE → USER-APPROVED MUTATION EXECUTION → EXACT-OBJECT BRAIN REVIEW → USER ACCEPT/MERGE`.

Technical Discovery is conditional. When current Brain-accessible repository evidence is sufficient, it is skipped. When material repository/local/runtime facts are missing, Local Codex performs bounded read-only discovery and distinguishes direct repository facts from technical inference/recommendation.

## Architecture-change activation boundary

The current active Joyflow Development Project Instruction has been explicitly confirmed by the user. It authorizes Web Brain to authorize strictly bounded pure read-only Local Codex Technical Discovery without a separate user approval; any mutation/material execution still requires explicit user approval. The Development Instruction lives in the Web Brain Project Instruction surface and is not duplicated into this Runtime/Project Sources package. This candidate records only its external authority binding in `PHASE2_STAGE_LINEAGE.json`.

## Repairs in this candidate

- mutation approval binds a stable execution envelope rather than an attempt-local Projection/Capsule;
- same-envelope implementation rework does not require renewed mutation approval, while material envelope change does;
- product tolerances are User-owned; Brain/Codex may explain consequences but cannot invent acceptability;
- contextual risk markers drive consequence/recoverability/reality analysis rather than mechanically mapping every storage/shared-state change to STRICT; hard floors remain;
- active `GLOBAL_INVARIANT` cannot be waived by residual-risk acceptance;
- Evidence GitHub transport carries the exact canonical Evidence Bundle bytes, uses only `refs/heads/joyflow-evidence/`, and cleanup binds generic task-terminal evidence;
- logical Brain authorization is explicitly separated from physical invocation; Brain↔Local Codex handoff remains user-mediated or uses another explicitly available transport;
- GitHub/repository evidence is preferred when Brain-accessible, but no specific connector is mandatory and exact manual-material fallback is allowed;
- user-facing approval view is compact while machine binding remains exact.

## Deliberately deferred engineering optimization

Runtime module splitting, physical removal of `DEVELOPMENT_LIGHT/STANDARD/STRICT` compatibility aliases, and broad rule-registry compression are **not** part of this repair. They will be evaluated only after the corrected workflow is cold-reviewed.

## Remaining evidence limits

Windows Git-fixture root cause, Windows fresh-extract replay, actual Ubuntu GitHub Actions runner replay and cross-platform authoritative replay remain unresolved/not obtained. Final stable closure also requires a real human-semi-automatic Web Brain ↔ user-mediated handoff ↔ Local Codex replay with no background Joyflow control plane.
