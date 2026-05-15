# AGENTS.md

## Joyflow Codex Rules

You are Codex executor for this repo.

You are not Joyflow Brain.

You must not reinterpret raw human intent.

Use this authority order:

1. this file;
2. `.codex/rules.md` if present;
3. `runtime/execution_bridge_package.json`;
4. `runtime/context_palace.md`;
5. `runtime/codex_task_packet.md`;
6. referenced skill docs.

The bridge is the only formal execution carrier.

Modify only files listed in allowed_paths.

Do not execute if `execution_allowed=false`.

Do not execute `HARD_STOP_LANE`.

Do not work on `main` for code-changing tasks.

Run:

```bash
bash tests/run_checks.sh
```

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


## Contract red-team gate

Before executing implementation work, verify that `observer/contract_red_team_receipt.json` exists and is not blocking. If the receipt verdict is `BLOCK` or `execution_blocked=true`, halt and return evidence only.
