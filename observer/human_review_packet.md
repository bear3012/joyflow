# Joyflow v4.3.6 Repository Reference Candidate — Unfamiliar Cold Review

## Verdict

```text
unfamiliar_cold_review: PASS_WITH_DECLARED_LIMITATIONS
reviewed_source_head: ddfe6257b403b9e29e202b0bf71bddc59503af80
repository_candidate: MECHANICALLY_COHERENT_REFERENCE_CANDIDATE
execution: BLOCKED_BY_DESIGN
Brain semantic review: PASS
user acceptance: NOT_RUN
Reconcile: BLOCKED_AS_DESIGNED
PR: OPEN_DRAFT
merge: NOT_RECOMMENDED
standalone v4.3.6 ZIP: NOT_FROZEN
```

## What was independently re-checked

The review did not inherit the previous PASS. It re-read the current authority model, semantic artifacts, routing, path handling, committed PR diff logic, Bridge construction, one-Prompt generation, evidence ownership, hash binding, CI workflow, counterexample tests, Reconcile, and the generated GitHub evidence bundle.

## Confirmed repairs

- committed runtime artifacts match deterministic regeneration;
- normal words such as `product` and `authority` no longer trigger `prod` or `auth` risk matches;
- routing inspects intended change surfaces rather than negative examples;
- `.github/`, `.codex/`, and `.gitignore` retain their exact identity;
- committed base-to-head PR changes are checked even with a clean worktree;
- a protocol fixture cannot impersonate authentic Codex interpretation evidence;
- Codex cannot write Brain or human approval receipts;
- Bridge and Prompt bind current authority inputs and source bundle;
- reference, HARD_STOP, non-released, and HALT states cannot close;
- review and acceptance receipts bind one reviewed source HEAD, while later commits must be mechanically proven evidence-only.

## Mechanical evidence

```text
GitHub Actions run: 29840988291
workflow conclusion: success
workflow job: semantic-closure success
raw checks: 49 passed, 0 failed
evidence artifact: 8499324759
artifact SHA-256: cf56d5e50a43d34be56f91803eb6e503f642428de8844e761e759b6ef2aea73d
Bridge hash: ba364b1394b1327cf6e173e3dfa77c49da3cf8448e4f3de7065ca9f5c9b81b5a
input bundle hash: 1851b8c6580ab88129ad830cca587345563b9353603bc550f3295d9df3aa3cdf
source bundle SHA-256: 30221bf35a5865fdbcd1a88d3624a8e10cf7917b21e14741b877cba22e3c0444
```

The checked reference candidate correctly produced `HARD_STOP_LANE`, `execution_allowed=false`, and a `HALT` packet. Reconcile remained false with explicit blockers rather than pretending that candidate CI was execution evidence.

## Declared limitations

1. This review covers the GitHub repository reference candidate, not a frozen standalone v4.3.6 ZIP.
2. A real medium-risk ACTIVE_TASK has not yet exercised the full Web Brain → local Codex interpretation → one execution Prompt → PR evidence → Brain review → user acceptance lifecycle.
3. Single-owner role separation is logical duty separation, not cryptographic identity separation.
4. Mechanical checks prove structure and binding, not subjective product correctness or lived experience.

## Human acceptance gate

Human acceptance remains `NOT_RUN`. It may begin only after this evidence-only review commit itself passes CI and proves that the reviewed source HEAD remains unchanged while the suffix contains only approved observer evidence.

The later acceptance plan remains in `runtime/user_acceptance_plan.json`. The user should test actual product behavior, not internal functions, schemas, or file organization.
