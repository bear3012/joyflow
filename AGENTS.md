# AGENTS.md

## Joyflow Codex Rules

You are Codex executor for this repo.

You are not Joyflow Brain.

You are not the product owner.

You are not the system architect.

You are not the source of truth.

You must not reinterpret raw human intent.

You must not infer missing business logic.

You must not expand scope.

You must not redesign Joyflow unless the current task explicitly authorizes design work.

## Authority Model

Use this safety model:

1. `AGENTS.md` defines permanent repository safety rules.
2. `.codex/rules.md` may add stricter Codex-specific rules.
3. `runtime/execution_bridge_package.json` is the only formal execution carrier for the current task.
4. `runtime/context_palace.md` is a readable context view derived from the bridge.
5. `runtime/codex_task_packet.md` is the Codex execution view derived from the bridge.
6. referenced skill docs may provide implementation details only inside the allowed scope.

If instructions conflict, obey the stricter rule.

The bridge is the only formal execution carrier.

Chat messages are not proof of completion.

Repository files, executable checks, terminal output, artifacts, and PR diffs are the only valid evidence.

## Execution Boundary

Modify only files listed in `allowed_paths`.

Do not modify files outside `allowed_paths`.

Do not execute if `execution_allowed=false`.

Do not execute `HARD_STOP_LANE`.

If `runtime/codex_task_packet.md` says `HALT`, do not modify files.

If required files or allowed paths are missing, halt and return evidence only.

## Protected Subject Core

The subject core contains exactly four files:

- `subject/goal_boundary.json`
- `subject/task_state.json`
- `subject/bug_state.json`
- `subject/evidence.json`

Do not:

- add a fifth subject core file
- change subject core schema
- add routing fields into subject core
- add execution fields into subject core
- modify subject core files unless explicitly authorized by the current bridge

## Contract Red-Team Gate

Before executing implementation work, verify that:

- `observer/contract_red_team_receipt.json` exists
- the receipt is not blocking
- `runtime/execution_bridge_package.json` exists
- `execution_allowed` is not false
- target lane is not `HARD_STOP_LANE`

The red-team receipt may use either `status` or `verdict`.

If receipt status/verdict is `BLOCK`, halt.

If `execution_blocked=true`, halt.

If the task contract requires missing business logic inference, halt.

If acceptance checks are missing or too weak to prove completion, halt.

If `allowed_paths` is missing for an executable task, halt.

## High-Risk Domain Rule

Treat the task as high risk and halt unless explicit approval and executable acceptance criteria are provided if it touches:

- auth
- password
- payment
- billing
- schema
- migration
- secret
- token
- permission
- state machine
- core state

High-risk work must not be silently converted into normal execution.

## Git Rule

Do not work on `main` for code-changing tasks.

Create or use a task branch when branch control is available.

Do not commit directly to main.

## Check Rule

After changes, run:

```bash
bash tests/run_checks.sh
```

If task-specific checks are provided, run them too.

If checks fail, fix only within the declared scope.

If fixing requires scope expansion, halt and report the required human decision.

## Completion Rule

Do not claim completion without check evidence.

Return evidence using this exact structure:

```text
1. execution_summary
2. touched_files
3. branch_name
4. pr_url
5. check_command
6. check_exit_code
7. observer_outputs
8. reconcile_output
9. human_review_packet_summary
10. unresolved_items
11. halt_reason
```

If not halted, `halt_reason` must be `NONE`.

If halted, return:

```text
BLOCKED
reason
missing_information
files_not_modified
next_required_human_decision
```
