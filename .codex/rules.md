# Codex Rules for Joyflow

Codex executes bounded tasks only.

Codex must read current task artifacts:

```text
runtime/execution_bridge_package.json
runtime/context_palace.md
runtime/codex_task_packet.md
```

Codex must not:

1. reinterpret human intent;
2. widen scope;
3. modify outside allowed_paths;
4. execute HARD_STOP;
5. work on main for code-changing tasks;
6. skip checks;
7. claim closure_ready manually.

Codex must:

1. obey bridge;
2. use context palace only as navigation;
3. run `bash tests/run_checks.sh`;
4. produce/update required observer outputs;
5. return structured evidence.


## Contract red-team gate

Before executing implementation work, verify that `observer/contract_red_team_receipt.json` exists and is not blocking. If the receipt verdict is `BLOCK` or `execution_blocked=true`, halt and return evidence only.
