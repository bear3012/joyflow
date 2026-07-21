# Joyflow v4.3.6 Repair Candidate — Human Review Packet

## Current state

```text
repository candidate: REPAIR_IN_PROGRESS
lifecycle mode: REFERENCE_CANDIDATE
execution: BLOCKED_BY_DESIGN
Brain semantic review: BLOCK
user acceptance: NOT_RUN
merge: NOT_RECOMMENDED
standalone v4.3.6 ZIP: NOT_FROZEN
```

## Why acceptance is not starting yet

The previous unfamiliar cold review found stale committed runtime artifacts, false risk routing, fixture interpretation used as evidence, incomplete PR diff checking, evidence ownership confusion, incomplete binding, and a HARD_STOP closure gap.

This repair candidate must first pass:

1. repaired mechanical CI;
2. deterministic runtime freshness verification;
3. current-source Brain semantic review;
4. a new unfamiliar full cold review.

Only then may the predefined human acceptance plan begin.

## Later human acceptance targets

- reference package is clearly non-executable;
- a real local Codex interpretation is required for a medium-risk task;
- hidden paths and committed PR diff are enforced;
- Codex cannot write Brain or human approval evidence;
- Prompt and package inputs match exactly;
- reference or halted work cannot close.
