# JOYFLOW_CODEX_SKILLS_v1

## 0. Purpose

This document defines reusable Joyflow execution skills for Codex.

These are not autonomous permissions.

They are bounded procedures that Codex may use when the current task packet authorizes them.

## 1. Skill: `joyflow_read_bridge`

### Purpose

Read the formal execution carrier.

### Inputs

```text
runtime/execution_bridge_package.json
```

### Procedure

1. Confirm file exists.
2. Read `execution_allowed`.
3. Read `target_lane`.
4. Read `allowed_paths`.
5. Read `forbidden` and `non_negotiables`.
6. Read `acceptance_command`.
7. Read `required_output_files`.

### Halt conditions

Halt if:

1. bridge missing;
2. malformed bridge;
3. `execution_allowed=false`;
4. `target_lane=HARD_STOP_LANE`.

## 2. Skill: `joyflow_check_allowed_paths`

### Purpose

Confirm changed files are within allowed paths.

### Inputs

1. allowed paths from bridge;
2. changed file list from git.

### Procedure

1. List changed files.
2. Compare each changed file against allowed paths.
3. Report violations.
4. Do not silently keep unauthorized modifications.

### Output

```json
{
  "allowed_paths_check": "PASS|FAIL",
  "changed_files": [],
  "violations": []
}
```

## 3. Skill: `joyflow_run_checks`

### Purpose

Run public Joyflow check command.

### Command

```bash
bash tests/run_checks.sh
```

### Procedure

1. Run command.
2. Capture exit code.
3. Capture stdout/stderr.
4. Confirm `observer/raw_check_results.json` is written.
5. Report result.

### Output

```json
{
  "check_command": "bash tests/run_checks.sh",
  "check_exit_code": 0,
  "raw_check_results_exists": true
}
```

## 4. Skill: `joyflow_report_evidence`

### Purpose

Return evidence to Brain in a stable format.

### Output sections

```text
execution_summary:
touched_files:
branch_name:
pr_url:
check_command:
check_exit_code:
observer_outputs:
reconcile_output:
human_review_packet_summary:
unresolved_items:
halt_reason:
```

### Rule

Do not omit failed or missing evidence.

## 5. Skill: `joyflow_create_or_update_pr`

### Purpose

Create or update PR evidence for code-changing tasks.

### Procedure

1. Confirm current branch is not main.
2. Commit changes according to repo practice.
3. Push branch if required.
4. Create or update PR if tool access allows.
5. Return PR URL.

### If PR cannot be created

Report:

1. branch name;
2. reason PR could not be created;
3. exact human action needed.

Do not mark closure ready without PR evidence for code-changing tasks.

## 6. Skill: `joyflow_write_human_review_packet`

### Purpose

Generate human-native review packet after execution.

### Output path

```text
observer/human_review_packet.md
```

### Required sections

1. Original goal;
2. actual change;
3. human check steps;
4. verified scenarios;
5. unverified scenarios;
6. affected areas;
7. red flags;
8. risk explanation;
9. recommendation;
10. final human decision field.

### Rule

Do not write vague praise.

Write observable results and uncertainty.

## 7. Skill: `joyflow_reconcile`

### Purpose

Run or report closure readiness.

### Command

```bash
python scripts/reconcile.py
```

### Rule

Only `scripts/reconcile.py` may create machine `closure_ready` result.

Codex must not manually mark closure ready.

## 8. Skill use constraints

A skill cannot override bridge.

A skill cannot expand allowed paths.

A skill cannot change task intent.

A skill cannot bypass checks.

A skill cannot turn HARD_STOP into executable work.
