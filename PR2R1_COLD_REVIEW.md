# PR2R1 Stranger Cold Review — Claim Support Relevance

REVIEW_TARGET: `JOYFLOW_PHASE2R1_CLAIM_SUPPORT_RELEVANCE_REPAIR_CANDIDATE`

The stage is reviewable only if the exact frozen candidate rejects unrelated-but-authority-compatible support for operating assumptions, prior-behavior change authorization, impact dimensions, high-loss risk control, prior-behavior preservation, and exit-condition closure.

The repair must reuse the existing task-local Evidence Registry subject binding. It must not add multi-user identity, authentication, signatures, a persistent claim graph, or a second semantic authority.

Expected blocking examples:
- a user decision about Joyflow topology cannot confirm a different 10,000-concurrency assumption;
- a user decision about another subject cannot authorize `CHANGE_AUTHORIZED` for an unrelated `behavior_id`;
- a generic repository tree snapshot cannot satisfy every impact dimension;
- a generic passing test cannot control an unrelated risk or preserve an unrelated prior behavior;
- unrelated evidence cannot satisfy a PR exit condition.
