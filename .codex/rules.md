# Codex Rules for Joyflow

Codex executes only an `ACTIVE_TASK` released by the current Bridge and one complete task packet.

Before mutation, read:

```text
runtime/product_meaning_closure.json
runtime/translation_contract.json
runtime/codex_execution_interpretation.json
runtime/execution_bridge_package.json
runtime/context_palace.md
runtime/codex_task_packet.md
```

Halt when lifecycle mode is not `ACTIVE_TASK`, target lane is `HARD_STOP_LANE`, execution is not allowed, the packet says `HALT`, or the interpretation is a fixture/example rather than authentic reviewed Codex evidence.

Codex may modify only bridge `allowed_paths` and `executor_writable_outputs`.

Codex must not write Brain-only or human-only evidence, including:

```text
observer/brain_semantic_review.json
observer/acceptance_receipt.json
observer/pr_receipt.json
observer/human_review_packet.md
```

Run:

```bash
bash tests/run_checks.sh
```

Return structured execution evidence. Never claim `closure_ready` manually and never treat green candidate CI as execution authority.
