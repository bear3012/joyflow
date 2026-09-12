# Codex Runtime Interface Boundary

The complete Prompt contains a self-contained machine Projection, the bounded Codex technical-authority contract, and exact source/build identity. A once-installed Codex Runtime may parse and verify it without asking the user to fill schemas or run per-task validation scripts.

Implemented:

1. verify the Prompt envelope, approval binding and exact build identity;
2. enforce allowed paths, stop conditions and validation obligations;
3. perform technical preflight internally in the same approved execution turn;
4. continue only for `ROUTE_CONFIRMED` or an explicitly recorded `EQUIVALENT_IMPLEMENTATION_ADJUSTMENT`;
5. stop with direct Evidence for `BRAIN_ROUTE_CONFLICT`, `APPROVAL_SCOPE_INSUFFICIENT`, or `REPOSITORY_STATE_MISMATCH`;
6. produce either a `CODEX_EXECUTION_RETURN` for mutating/artifact execution or a `PATH_DISCOVERY_RETURN` for bounded local read-only discovery, each bound to the exact Capsule and Projection;
7. permit an honest `BLOCKED` Return without invented PR or artifact evidence while preserving blocker, unresolved, mutation and cleanup facts;
8. for local discovery, return stable typed path/dependency/validation/finding IDs and deterministic before/after worktree captures while declaring `mutation_performed=false`;
9. for completed mutating execution, return exact commands, exit codes, raw-output references, touched files and candidate PR/head identity;
10. force `brain_review_status=PENDING_BRAIN_REVIEW`;
11. force `user_acceptance_status=PENDING_USER_ACCEPTANCE`;
12. force `merge_status=NOT_AUTHORIZED`.

Not implemented or permitted:

- changing product requirements, important tradeoffs or Joyflow authority topology;
- expanding `allowed_paths` or treating a technical objection as execution authority;
- creating user approval;
- marking Brain review or user acceptance PASS;
- setting `MERGE_READY` or `MERGE_ALLOWED`;
- merging a PR;
- automatic repository Promotion;
- user identity authentication, immutable event history or trusted observer services.

## Operational current-source replay

Static example files are structural fixtures only. For material repository work, run `runtime/joyflow_dual_layer.py verify-execution-projection ... --repository <repo>` before mutation and `verify-codex-return ... --repository <repo>` after execution. For local discovery, `verify-path-discovery-return` requires `--repository`. Artifact work supplies the exact approved input with `--artifact` and each produced output with `--artifact-output`. Brain Review sealing supplies the same current sources. These commands reproduce deterministic facts; they do not approve or merge.


## Exact operational replay boundary

- `PR_DIFF` observations require exact `base_ref` and `head_ref` and are recomputed from `git diff --name-only base...head`.
- Validation approval is the exact argv array at `SOURCE_ROOT`; command text is display-only and derived.
- Operational Return and Review commands always replay approved tests. There is no operational `--no-replay-tests` bypass.
- Ignored/runtime worktree coverage is supplied only through exact `--include-ignored-path` entries; the helper never scans every ignored path.
