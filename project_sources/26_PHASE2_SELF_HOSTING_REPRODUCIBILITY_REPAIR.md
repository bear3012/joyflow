# Phase 2 Repair — Joyflow Self-Hosting Reproducibility Boundaries

canonical_rule_id: RULE_PHASE2_SELF_HOSTED_PACKAGE_IDENTITY_AUTHORITY
source_section_id: 26::SELF_HOSTED_PACKAGE_IDENTITY_AUTHORITY

The exact current `PACKAGE_MANIFEST.json` owns the current package identity. `PHASE2_STAGE_LINEAGE.json` supplies stage and parent lineage facts and must agree with the Manifest, while the Runtime model extension must agree with that current stage. README, scope/status documents and review records are human-readable projections: they may be mechanically checked for contradiction with the structured current facts, but free prose or one exact natural-language sentence cannot become a second machine identity authority.

canonical_rule_id: RULE_PHASE2_CANONICAL_GENERATED_TEXT_BYTES
source_section_id: 26::CANONICAL_GENERATED_TEXT_BYTES

Joyflow-owned deterministic text assets use UTF-8 without BOM and LF newlines. Canonicalization happens when Joyflow writes its own deterministic text; integrity digests continue to bind the exact stored bytes. Hashing must not normalize CRLF, encoding or other byte differences after the fact, and this rule does not authorize rewriting arbitrary target-product or user-supplied repository files.

canonical_rule_id: RULE_PHASE2_RAW_EXECUTION_EVIDENCE_BYTE_TRUTH
source_section_id: 26::RAW_EXECUTION_EVIDENCE_BYTE_TRUTH

Execution capture truth binds the actual stdout and stderr byte streams independently. Human-readable UTF-8 projections may use replacement decoding for display, but the capture also carries SHA-256 of the original stdout bytes and original stderr bytes; replay checks those byte digests against the exact command result. Canonical package text rules never normalize external raw execution output before evidence comparison.

canonical_rule_id: RULE_PHASE2_VALIDATION_DEPENDENCY_CONTRACT
source_section_id: 26::VALIDATION_DEPENDENCY_CONTRACT

The Joyflow candidate carries one minimal validation dependency declaration for its third-party Python validation libraries. The current GitHub mechanical gate installs that declaration before invoking the existing repository-owned public check entry. This is a reproducible validation-environment contract, not a package manager platform, background service, Skill system or new truth source.

canonical_rule_id: RULE_PHASE2_CI_EXISTING_PUBLIC_ENTRY_CONTRACT
source_section_id: 26::CI_EXISTING_PUBLIC_ENTRY_CONTRACT

GitHub Actions remains a read-only mechanical Gate. It calls the existing `tools/joyflow_repo_check.py` public entry for the current PR, while that entry supplies the fixed `.joyflow/current/` pre-merge source objects required by the Runtime. A Merged Change Projection is not among those mandatory PR-CI inputs because it is conditional and post-merge. Workflow YAML must not independently duplicate the Runtime's complete internal current-object CLI contract. CI PASS creates no Brain verdict, user acceptance, merge authorization or Promotion authority.

canonical_rule_id: RULE_PHASE2_PLATFORM_CAPABILITY_NA_BOUNDARY
source_section_id: 26::PLATFORM_CAPABILITY_NA_BOUNDARY

A platform-specific integration capability may be classified `NOT_APPLICABLE_PLATFORM_CAPABILITY` only from a direct capability probe performed before the integration path. An expected unsupported symlink capability is reported explicitly and the test method still completes without using unittest Skip; an unexpected failure after a successful probe remains a real test failure. The package runner treats any ordinary skipped unittest as blocking, preventing N/A from becoming a generic skip-after-failure path.

canonical_rule_id: RULE_PHASE2_GIT_FIXTURE_UNKNOWN_NOT_REPAIRED
source_section_id: 26::GIT_FIXTURE_UNKNOWN_NOT_REPAIRED

The previously observed Windows `not a git repository` fixture failure remains a real unresolved observation until exact failure-boundary evidence identifies its cause. This candidate does not add retry, does not label the failure a Windows bug, and does not modify process cleanup or Git fixture behavior on an unconfirmed hypothesis. Formal closure of that observation requires a separate bounded discovery and, only if a package defect is confirmed, a later exact repair.
