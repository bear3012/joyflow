# GENERATED DUAL-LAYER MECHANICAL REGISTRY

> Generated from `machine/joyflow_dual_layer_model.yaml`. Do not edit manually.

## Architecture

```yaml
architecture:
  persistent_layer: REPOSITORY_CANONICAL_STATE
  temporary_layer: FIBERED_TASK_CAPSULE
  downward_gate: PROJECTION_GATE
  upward_gates:
  - BRAIN_PR_REVIEW_GATE
  - USER_MERGE_DECISION_GATE
  canonical_promotion_event: OBSERVED_MERGE_RESULT_IN_REPOSITORY
  automation_boundary: HUMAN_SEMIAUTOMATIC_NO_AUTOMATIC_PROMOTION
  task_concurrency: ONE_ACTIVE_TASK_PER_PROJECT_ROUND
  round_semantics: TASK_PROGRESS_CYCLE_IS_MATERIAL_RECLOSURE_OR_AUTHORIZATION_BOUNDARY
  path_discovery_topology: BRAIN_ACCESSIBLE_REPOSITORY_EVIDENCE_WITH_CODEX_GOAL_CONDITIONED_STRUCTURAL_DISCOVERY_BEFORE_FINAL_BOUNDARY
  codex_execution_authority: BOUNDED_ROUTE_SELECTION_WITH_TASK_BOUND_PREFLIGHT_AND_TYPED_FACT_DERIVATION
  temporary_task_object_lifecycle: AUTHORIZED_INPUT_TO_DISCOVERY_TO_BOUNDARY_TO_RESULT_TO_VALIDATION_TO_REVIEW
  operational_route_entries: DEDICATED_REPOSITORY_AND_ARTIFACT_REVIEW
  sealed_object_consumption: BOUNDARY_SAFE_READ_COMPLETE_WORKSPACE_OBSERVATION_IMMUTABLE_REVIEW_SOURCE
  structural_cognition: REPOSITORY_ANCHORED_SPARSE_DERIVED_SKELETON_PLUS_TASK_LOCAL_GOAL_CONDITIONED_UNFOLDING
  structural_projection_authority: DERIVED_NAVIGATION_BELOW_REPOSITORY
```

## Route profiles

```yaml
route_profiles:
  DISCUSSION:
    executable: false
    initial_stage: INTENT_DISCUSSION
    allowed_change_scopes:
    - NONE
    flow_depth: LIGHT
    validation_depth: NONE
    required_fibers:
    - semantic
    optional_fibers: []
    allowed_stages:
    - INTENT_DISCUSSION
    - DECISION_CLOSURE
    - CLOSED
    - BLOCKED
    requires_repository_binding: false
    requires_pr: false
    required_repository_fact_slots: []
    execution_mode: NONE
  REVIEW:
    executable: false
    initial_stage: INTENT_DISCUSSION
    allowed_change_scopes:
    - READ_ONLY
    flow_depth: STANDARD
    validation_depth: BASIC
    required_fibers:
    - semantic
    - validation
    optional_fibers:
    - repository_evidence
    allowed_stages:
    - INTENT_DISCUSSION
    - REPOSITORY_DISCOVERY
    - DECISION_CLOSURE
    - BRAIN_REVIEW
    - CLOSED
    - BLOCKED
    requires_repository_binding: false
    requires_pr: false
    required_repository_fact_slots: []
    execution_mode: NONE
  READ_ONLY_DISCOVERY:
    executable: true
    initial_stage: REPOSITORY_DISCOVERY
    allowed_change_scopes:
    - READ_ONLY
    flow_depth: LIGHT
    validation_depth: BASIC
    required_fibers:
    - semantic
    - repository_evidence
    - decision_boundary
    - validation
    - authority
    optional_fibers: []
    allowed_stages:
    - REPOSITORY_DISCOVERY
    - CODEX_EXECUTION
    - DECISION_CLOSURE
    - BLOCKED
    requires_repository_binding: true
    requires_pr: false
    required_repository_fact_slots:
    - discovery_target
    - search_scope
    execution_mode: READ_ONLY
  ARTIFACT_REPAIR:
    executable: true
    initial_stage: DECISION_CLOSURE
    allowed_change_scopes:
    - ARTIFACT_CHANGE
    flow_depth: STANDARD
    validation_depth: STANDARD
    required_fibers:
    - semantic
    - decision_boundary
    - validation
    - authority
    optional_fibers:
    - repository_evidence
    - execution_review
    allowed_stages:
    - DECISION_CLOSURE
    - USER_APPROVAL
    - CODEX_EXECUTION
    - BRAIN_REVIEW
    - USER_ACCEPTANCE
    - CLOSED
    - BLOCKED
    requires_repository_binding: false
    requires_pr: false
    required_repository_fact_slots: []
    execution_mode: MUTATING
  DEVELOPMENT_LIGHT:
    executable: true
    initial_stage: INTENT_DISCUSSION
    allowed_change_scopes:
    - REPOSITORY_CHANGE
    flow_depth: LIGHT
    validation_depth: BASIC
    required_fibers:
    - semantic
    - repository_evidence
    - decision_boundary
    - validation
    - authority
    optional_fibers:
    - execution_review
    allowed_stages:
    - INTENT_DISCUSSION
    - REPOSITORY_DISCOVERY
    - DECISION_CLOSURE
    - USER_APPROVAL
    - CODEX_EXECUTION
    - BRAIN_REVIEW
    - USER_ACCEPTANCE
    - MERGE_DECISION
    - BLOCKED
    requires_repository_binding: true
    requires_pr: true
    required_repository_fact_slots:
    - implementation_entry
    - affected_behavior
    - validation_entry
    execution_mode: MUTATING
  DEVELOPMENT_STANDARD:
    executable: true
    initial_stage: INTENT_DISCUSSION
    allowed_change_scopes:
    - REPOSITORY_CHANGE
    flow_depth: STANDARD
    validation_depth: STANDARD
    required_fibers:
    - semantic
    - repository_evidence
    - decision_boundary
    - validation
    - authority
    optional_fibers:
    - execution_review
    allowed_stages:
    - INTENT_DISCUSSION
    - REPOSITORY_DISCOVERY
    - DECISION_CLOSURE
    - USER_APPROVAL
    - CODEX_EXECUTION
    - BRAIN_REVIEW
    - USER_ACCEPTANCE
    - MERGE_DECISION
    - BLOCKED
    requires_repository_binding: true
    requires_pr: true
    required_repository_fact_slots:
    - implementation_entry
    - affected_behavior
    - validation_entry
    execution_mode: MUTATING
  DEVELOPMENT_STRICT:
    executable: true
    initial_stage: INTENT_DISCUSSION
    allowed_change_scopes:
    - REPOSITORY_CHANGE
    flow_depth: STRICT
    validation_depth: STRICT
    required_fibers:
    - semantic
    - repository_evidence
    - decision_boundary
    - validation
    - authority
    optional_fibers:
    - execution_review
    allowed_stages:
    - INTENT_DISCUSSION
    - REPOSITORY_DISCOVERY
    - DECISION_CLOSURE
    - USER_APPROVAL
    - CODEX_EXECUTION
    - BRAIN_REVIEW
    - USER_ACCEPTANCE
    - MERGE_DECISION
    - BLOCKED
    requires_repository_binding: true
    requires_pr: true
    required_repository_fact_slots:
    - implementation_entry
    - affected_behavior
    - validation_entry
    execution_mode: MUTATING
  REPAIR_STANDARD:
    executable: true
    initial_stage: REPOSITORY_DISCOVERY
    allowed_change_scopes:
    - REPOSITORY_CHANGE
    flow_depth: STANDARD
    validation_depth: STANDARD
    required_fibers:
    - semantic
    - repository_evidence
    - decision_boundary
    - validation
    - authority
    optional_fibers:
    - execution_review
    allowed_stages:
    - REPOSITORY_DISCOVERY
    - DECISION_CLOSURE
    - USER_APPROVAL
    - CODEX_EXECUTION
    - BRAIN_REVIEW
    - USER_ACCEPTANCE
    - MERGE_DECISION
    - BLOCKED
    requires_repository_binding: true
    requires_pr: true
    required_repository_fact_slots:
    - failure_observation
    - root_cause_location
    - existing_behavior
    - implementation_entry
    - validation_entry
    execution_mode: MUTATING
  PROTOCOL_CHANGE:
    executable: true
    initial_stage: DECISION_CLOSURE
    allowed_change_scopes:
    - ARTIFACT_CHANGE
    - REPOSITORY_CHANGE
    flow_depth: PROTOCOL
    validation_depth: STRICT
    required_fibers:
    - semantic
    - decision_boundary
    - validation
    - authority
    optional_fibers:
    - repository_evidence
    - execution_review
    allowed_stages:
    - DECISION_CLOSURE
    - USER_APPROVAL
    - CODEX_EXECUTION
    - BRAIN_REVIEW
    - USER_ACCEPTANCE
    - MERGE_DECISION
    - CLOSED
    - BLOCKED
    requires_repository_binding: conditional
    requires_pr: conditional
    required_repository_fact_slots_when_repository_change:
    - protocol_authority
    - implementation_entry
    - validation_entry
    execution_mode: MUTATING
```

## Evidence authority

```yaml
evidence_kinds_by_authority:
  USER_DECISION:
  - PRODUCT_DECISION
  - EXECUTION_APPROVAL
  - USER_ACCEPTANCE
  - MERGE_APPROVAL
  REPOSITORY_EVIDENCE:
  - FILE
  - COMMIT
  - SCHEMA
  - CONFIG
  - TEST_DEFINITION
  - PR
  - GITHUB_TREE_SNAPSHOT
  - GITHUB_FILE
  - GITHUB_COMMIT_PATHS
  - GITHUB_PR_PATHS
  - GITHUB_PR_DIFF_PATHS
  EXECUTION_EVIDENCE:
  - TEST_RESULT
  - PR_CHECK
  - DIFF
  - GIT_STATE
  - RUNTIME_OUTPUT
  - CODEX_RETURN
  - EVIDENCE_BUNDLE
  - ARTIFACT_RESULT
  - GIT_STATE_FINGERPRINT
  - PATH_OBSERVATION
  - SOURCE_SNAPSHOT_OBSERVATION
  - REPOSITORY_REF_OBSERVATION
  - ROUTE_ASSUMPTION_CHECK
  - ROUTE_CONFLICT_FINDING
  - SCOPE_GAP_OBSERVATION
  - REPOSITORY_REF_MISMATCH
  - EXECUTION_OBJECT_OBSERVATION
  - PREFLIGHT_OBLIGATION_RESULT
  - ROUTE_CANDIDATE_EVALUATION
  - SELECTED_TECHNICAL_ROUTE
  - CODEX_ALTERNATIVE_ROUTE
  - EXECUTION_OBJECT_MISMATCH
  - REPOSITORY_HEAD_OBSERVATION
  - REPOSITORY_COMMIT_OBSERVATION
  - REPOSITORY_STATE_OBSERVATION
  - ARTIFACT_SHA256_OBSERVATION
  - SOURCE_MATERIAL_SET_OBSERVATION
  - REPOSITORY_FILE_SNAPSHOT
  - REPOSITORY_DIFF
  - PREFLIGHT_OBLIGATION_DERIVATION
  - ROUTE_CANDIDATE_DERIVATION
  - SELECTED_ROUTE_DERIVATION
  - CODEX_ALTERNATIVE_DERIVATION
  - TECHNICAL_OBJECTION_DERIVATION
  - PATH_CANDIDATE_DERIVATION
  - DEPENDENCY_DERIVATION
  - VALIDATION_ENTRY_DERIVATION
  - LOCAL_FINDING_DERIVATION
  - STRUCTURAL_RELATION_DERIVATION
  - ARCHITECTURE_ROUTE_DERIVATION
  BRAIN_DERIVATION:
  - COLD_REVIEW
  - TECHNICAL_INFERENCE
  - ROUTE_ANALYSIS
  - RED_TEAM
  - PR_REVIEW
```

## Repository fact slots

```yaml
repository_fact_slot_policy:
  implementation_entry:
    allow_not_applicable: false
  affected_behavior:
    allow_not_applicable: false
  validation_entry:
    allow_not_applicable: true
  discovery_target:
    allow_not_applicable: false
  search_scope:
    allow_not_applicable: false
  failure_observation:
    allow_not_applicable: false
  root_cause_location:
    allow_not_applicable: false
  existing_behavior:
    allow_not_applicable: false
  protocol_authority:
    allow_not_applicable: false
```

## Risk and domain routing

```yaml
risk_minimum_route:
  IRREVERSIBLE_DATA: DEVELOPMENT_STRICT
  PAYMENT_CUSTODY: DEVELOPMENT_STRICT
  PROTECTED_CORE: PROTOCOL_CHANGE
  PROTOCOL_SOURCE: PROTOCOL_CHANGE
  SCHEMA_COMPILER: PROTOCOL_CHANGE
```

## Human semi-automatic merge boundary

```yaml
merge_boundary:
  repository_change_requires_pr: true
  codex_merge_forbidden: true
  brain_review_and_ci_before_merge_candidate_freeze: true
  user_acceptance_after_exact_freeze_when_applicable: true
  separate_user_merge_decision_required: true
  automatic_promotion_forbidden: true
  merge_result_requires_current_direct_repository_evidence: true
  post_merge_retention: TASK_COMPLETION_POINTER_ONLY
  transport_only_evidence_remote_mutation_requires_product_pr: false
  transport_only_evidence_remote_mutation_requires_user_execution_approval: true
  transport_only_evidence_ref_may_be_merged_to_product_history: false
  product_or_governance_repository_change_requires_pr: true
```

## Single active task round

```yaml
single_active_round:
  one_active_task_per_project_round: true
  one_active_projection_per_round: true
  one_codex_return_per_round: true
  cross_round_substitution_forbidden: true
  global_scheduler_required: false
  owner: WEB_BRAIN
```

## Hybrid path discovery

```yaml
path_discovery_policy:
  first_reader: WEB_BRAIN_ACCESSIBLE_REPOSITORY_EVIDENCE
  supplemental_reader: CODEX_LOCAL_READ_ONLY
  structural_discovery_reader: CODEX_LOCAL_READ_ONLY
  final_boundary_owner: WEB_BRAIN
  brain_accessible_repository_evidence_first_for_ordinary_path_discovery: true
  structural_discovery_may_precede_final_mutation_path_freeze: true
  local_discovery_only_when_needed: true
  local_discovery_reasons:
  - GITHUB_INSUFFICIENT
  - GITHUB_UNAVAILABLE
  - UNPUSHED_LOCAL_STATE
  - RUNTIME_ONLY_FACT
  - LOCAL_ENVIRONMENT_DIFFERENCE
  - MATERIAL_ARCHITECTURE_UNCERTAINTY
  repository_mutation_forbidden_during_local_discovery: true
  local_discovery_return_type: PATH_DISCOVERY_RETURN
```

## Codex bounded technical authority

```yaml
codex_technical_authority:
  role: BOUNDED_EXECUTION_TECHNICAL_AUTHORITY
  may_decide_without_reapproval:
  - CONCRETE_IMPLEMENTATION_WITHIN_APPROVED_PATHS
  - INTERNAL_FUNCTION_OR_MODULE_ORGANIZATION
  - EQUIVALENT_ALGORITHM_OR_DATA_STRUCTURE
  - TEST_ORGANIZATION_AND_COMMANDS
  - LOCAL_FIX_WITHOUT_EXTERNAL_SEMANTIC_CHANGE
  must_stop_when:
  - BRAIN_ROUTE_CONFLICTS_WITH_DIRECT_REPOSITORY_EVIDENCE
  - APPROVED_PATHS_INSUFFICIENT
  - PRODUCT_SEMANTICS_OR_NON_GOALS_WOULD_CHANGE
  - APPROVED_REPOSITORY_REF_MISMATCH
  - MATERIAL_USER_TRADEOFF_REQUIRED
  - REQUIRED_RESULT_CANNOT_BE_MET_WITHIN_APPROVED_ENVELOPE
  - REQUIRED_VALIDATION_CANNOT_BE_COMPLETED
  cannot:
  - CHANGE_PRODUCT_SEMANTICS
  - CHANGE_JOYFLOW_AUTHORITY_TOPOLOGY
  - EXPAND_ALLOWED_PATHS
  - FILL_BRAIN_REVIEW
  - FILL_USER_APPROVAL_OR_ACCEPTANCE
  - AUTHORIZE_MERGE
```

## Stage gate requirements

```yaml
stage_gate_requirements:
  USER_ACCEPTANCE:
  - codex_return_gate:PASS
  - brain_review_gate:PASS
  - repository_merge_candidate_freeze_binding:PRESENT_WHEN_PR
  MERGE_DECISION:
  - codex_return_gate:PASS
  - brain_review_gate:PASS
  - user_acceptance_gate:PASS
  - pr_review_gate:PASS
  - repository_merge_candidate_freeze_binding:PRESENT_WHEN_PR
  CLOSED_EXECUTABLE_ARTIFACT:
  - codex_return_gate:PASS
  - brain_review_gate:PASS
  - user_acceptance_gate:PASS
  - artifact_review_gate:PASS
  CLOSED_NON_EXECUTABLE:
  - semantic_gate:PASS
  - repository_evidence_gate:PASS
  - validation_gate:PASS
```

## Phase 1 stage lineage policy

```yaml
phase1_stage_policy:
  current_stage: PR1F_MIGRATION_CLAIM_TRUTHFULNESS
  completed_stages:
  - PR1A_PATH_DISCOVERY
  - PR1B_SEALED_OBJECT_EXECUTION_AND_REVIEW
  - PR1C_CURRENT_OBJECT_PR_BODY_CI
  - PR1D_REVIEW_ACCEPTANCE_FREEZE
  - PR1E_AI_NATIVE_CHANGE_PROJECTION
  parent_package:
    name: JOYFLOW_PHASE1E_AI_NATIVE_CHANGE_PROJECTION_REPAIR_CANDIDATE.zip
    bytes: 883786
    sha256: 9cb27a5e3d963cd79f976730697b195dc41d23f3dd74cafd17d7765ae5ddd1bc
  later_stage_inputs_are_targets_not_implementation_bases: true
  repair_source_package:
    name: JOYFLOW_PHASE1F_CONFIRMED_TRANSITION_BOUNDARY_REPAIR_CANDIDATE.zip
    bytes: 989316
    sha256: f3f8fe65cfc99715a0e56fbf4cdd2a8157ad9f81e75f14b9c8a021b1ca0f2c29
```

## GitHub CI mechanical gate

```yaml
github_ci_mechanical_gate:
  owner: TOOL
  read_only: true
  requires_exact_current_repository: true
  requires_base_ancestor_of_head: true
  requires_exact_projection_return_bundle_review_capsule: true
  requires_complete_current_diff_equality: true
  does_not_approve_accept_or_merge: true
```

## Legacy migration truthfulness

```yaml
legacy_migration_truth_policy:
  mapping_source_set_identity_single_owner: true
  semantic_evidence_exact_object_binding_required: true
  semantic_evidence_semantic_sufficiency_owner: WEB_BRAIN
  deferred_status_neutral_exact_decision: true
  allowed_statuses:
  - MAPPED_ONLY
  - SEMANTICALLY_PRESERVED_AND_BEHAVIORALLY_VERIFIED
  - DEFERRED_BY_EXACT_CURRENT_DECISION
  - RETIRED_BY_CURRENT_USER_DECISION
  - RETIRED_BY_CONFIRMED_SEMANTIC_SUPERSESSION
  separate_axes:
  - SEMANTIC_MAPPING
  - PRODUCT_DIRECTION_BOUND_DISPOSITION
  - CURRENT_TARGET_EVIDENCE
  - PR1F_MECHANISM_EFFECT
  disposition_decision_set_required: true
  generator_may_not_author_disposition: true
  current_candidate_all_dispositions: NOT_EVALUATED
  current_candidate_mapped_only_rows: 176
  current_candidate_legacy_equivalence_confirmed_rows: 0
  current_target_behavior_status_mechanically_derived: true
  legacy_equivalence_unresolved_targets_separate_from_behavior_unverified_targets: true
  phase_effect_separate_from_semantic_closure: true
  exact_legacy_source_identity_set_required: true
  exact_legacy_section_text_required_for_equivalence: true
  brain_owned_semantic_mapping_required: true
  generator_may_not_derive_or_modify_brain_mapping: true
  repair_source_package:
    name: JOYFLOW_PHASE1F_CONFIRMED_TRANSITION_BOUNDARY_REPAIR_CANDIDATE.zip
    bytes: 989316
    sha256: f3f8fe65cfc99715a0e56fbf4cdd2a8157ad9f81e75f14b9c8a021b1ca0f2c29
  strict_schema_before_semantic_validation: true
  disposition_authority_bound_to_product_direction: true
  web_brain_may_close_preserving_technical_dispositions: true
  per_row_user_approval_required: false
  changed_confirmed_direction_requires_user_decision: true
  grouped_user_decision_reference_allowed: true
  unresolved_material_effect_remains_open: true
  pr1f_mechanism_effect_does_not_determine_phase1_completion: true
  historical_review_context_must_be_non_authoritative: true
  disposition_transition_contract_single_source: true
  schema_validator_and_deriver_share_transition_contract: true
  technical_retirement_requires_confirmed_semantic_gate: true
  legal_transition_positive_coverage_required: true
  current_instance_separate_from_transition_fixture: true
  transition_fixture_test_only_non_authoritative: true
  confirmed_mapping_requires_exact_source_bytes_and_section_digest: true
  transition_contract_evidence_outcome_complete: true
  public_transition_path_positive_coverage_required: true
  fixture_cannot_modify_current_rows: true
  confirmed_transition_validated_boundary_required: true
  confirmed_transition_consumes_mapping_and_disposition_seals: true
  bundled_exact_source_root_package_relative: true
  exact_section_markers_ordered_nonempty: true
  top_level_mapping_status_derived: true
  validated_transition_inputs_are_temporary_process_state: true
```

## Candidate capability claims

```yaml
candidate_capability_claim_policy:
  artifact_role: GENERATED_NON_AUTHORITATIVE_NAVIGATION_VIEW
  may_satisfy_stage_gate: false
  may_satisfy_phase_gate: false
  package_may_self_claim_independent_cold_review: false
  package_may_self_claim_baseline_or_release: false
  exact_capability_claim_registry_required: true
  verification_contract_digest_required: true
  typed_stage_and_rule_coverage_required: true
  capability_claim_type_separation_required: true
  inherited_stage_presence_not_behavior_verification: true
  verified_rule_coverage_exact_relation_required: true
  verified_cross_stage_chain_exact_relation_required: true
  cross_stage_chain_does_not_imply_full_stage_coverage: true
```

## Mechanical invariants

canonical_rule_id: JF_P2_INV_COMPACT_HANDOFF_DELTA_RESUME
source_section_id: 03::INVARIANT::JF_P2_INV_COMPACT_HANDOFF_DELTA_RESUME

Generated mechanical invariant implemented by `validate_compact_handoff_delta_resume`.

canonical_rule_id: JF_P2_INV_SCENARIO_CUMULATIVE_REVIEW
source_section_id: 03::INVARIANT::JF_P2_INV_SCENARIO_CUMULATIVE_REVIEW

Generated mechanical invariant implemented by `validate_scenario_cumulative_review`.

canonical_rule_id: JF_P2_INV_CURRENT_SOURCE_TASK_GROUNDING
source_section_id: 03::INVARIANT::JF_P2_INV_CURRENT_SOURCE_TASK_GROUNDING

Generated mechanical invariant implemented by `validate_current_source_task_grounding`.

canonical_rule_id: JF_P2_INV_PR_GOAL_SCENARIO_GROUNDING
source_section_id: 03::INVARIANT::JF_P2_INV_PR_GOAL_SCENARIO_GROUNDING

Generated mechanical invariant implemented by `validate_pr_goal_scenario_grounding`.

canonical_rule_id: JF_DL_INV_ROUTE_PROFILE_MATCH
source_section_id: 03::INVARIANT::JF_DL_INV_ROUTE_PROFILE_MATCH

Generated mechanical invariant implemented by `validate_route_profile`.

canonical_rule_id: JF_DL_INV_STAGE_EVENT_LINEAGE
source_section_id: 03::INVARIANT::JF_DL_INV_STAGE_EVENT_LINEAGE

Generated mechanical invariant implemented by `validate_progress`.

canonical_rule_id: JF_DL_INV_ACTIVE_FIBERS
source_section_id: 03::INVARIANT::JF_DL_INV_ACTIVE_FIBERS

Generated mechanical invariant implemented by `validate_active_fibers`.

canonical_rule_id: JF_DL_INV_PACKET_CONTINUITY
source_section_id: 03::INVARIANT::JF_DL_INV_PACKET_CONTINUITY

Generated mechanical invariant implemented by `validate_lineage`.

canonical_rule_id: JF_DL_INV_DIGEST_CHAIN
source_section_id: 03::INVARIANT::JF_DL_INV_DIGEST_CHAIN

Generated mechanical invariant implemented by `validate_digest_chain`.

canonical_rule_id: JF_DL_INV_MATERIAL_CLASSIFICATION
source_section_id: 03::INVARIANT::JF_DL_INV_MATERIAL_CLASSIFICATION

Generated mechanical invariant implemented by `validate_materiality`.

canonical_rule_id: JF_DL_INV_EVIDENCE_AUTHORITY
source_section_id: 03::INVARIANT::JF_DL_INV_EVIDENCE_AUTHORITY

Generated mechanical invariant implemented by `validate_evidence_authority`.

canonical_rule_id: JF_DL_INV_EXCLUSION_LOGIC
source_section_id: 03::INVARIANT::JF_DL_INV_EXCLUSION_LOGIC

Generated mechanical invariant implemented by `validate_exclusions`.

canonical_rule_id: JF_DL_INV_RISK_ROUTE_LANE
source_section_id: 03::INVARIANT::JF_DL_INV_RISK_ROUTE_LANE

Generated mechanical invariant implemented by `validate_risk_route`.

canonical_rule_id: JF_DL_INV_SEMANTIC_EFFECT_TRANSPORT
source_section_id: 03::INVARIANT::JF_DL_INV_SEMANTIC_EFFECT_TRANSPORT

Generated mechanical invariant implemented by `validate_effect_transport`.

canonical_rule_id: JF_DL_INV_REPOSITORY_READINESS
source_section_id: 03::INVARIANT::JF_DL_INV_REPOSITORY_READINESS

Generated mechanical invariant implemented by `validate_repository_readiness`.

canonical_rule_id: JF_DL_INV_MECHANICAL_WALKTHROUGH
source_section_id: 03::INVARIANT::JF_DL_INV_MECHANICAL_WALKTHROUGH

Generated mechanical invariant implemented by `validate_mechanical_walkthrough`.

canonical_rule_id: JF_DL_INV_VALIDATION_OBLIGATIONS
source_section_id: 03::INVARIANT::JF_DL_INV_VALIDATION_OBLIGATIONS

Generated mechanical invariant implemented by `validate_validation_closure`.

canonical_rule_id: JF_DL_INV_REPAIR_COMPATIBILITY
source_section_id: 03::INVARIANT::JF_DL_INV_REPAIR_COMPATIBILITY

Generated mechanical invariant implemented by `validate_repair_extension`.

canonical_rule_id: JF_DL_INV_DERIVED_GATES
source_section_id: 03::INVARIANT::JF_DL_INV_DERIVED_GATES

Generated mechanical invariant implemented by `validate_derived_gates`.

canonical_rule_id: JF_DL_INV_APPROVAL_OWNERSHIP_BINDING
source_section_id: 03::INVARIANT::JF_DL_INV_APPROVAL_OWNERSHIP_BINDING

Generated mechanical invariant implemented by `validate_approval`.

canonical_rule_id: JF_DL_INV_BUILD_IDENTITY_BINDING
source_section_id: 03::INVARIANT::JF_DL_INV_BUILD_IDENTITY_BINDING

Generated mechanical invariant implemented by `validate_build_identity`.

canonical_rule_id: JF_DL_INV_PROMPT_TRUE_ROUND_TRIP
source_section_id: 03::INVARIANT::JF_DL_INV_PROMPT_TRUE_ROUND_TRIP

Generated mechanical invariant implemented by `validate_prompt_round_trip`.

canonical_rule_id: JF_DL_INV_ROLE_OWNERSHIP
source_section_id: 03::INVARIANT::JF_DL_INV_ROLE_OWNERSHIP

Generated mechanical invariant implemented by `validate_role_ownership`.

canonical_rule_id: JF_DL_INV_SINGLE_ACTIVE_TASK_ROUND
source_section_id: 03::INVARIANT::JF_DL_INV_SINGLE_ACTIVE_TASK_ROUND

Generated mechanical invariant implemented by `validate_single_active_round_binding`.

canonical_rule_id: JF_DL_INV_STAGE_GATE_BLOCKING
source_section_id: 03::INVARIANT::JF_DL_INV_STAGE_GATE_BLOCKING

Generated mechanical invariant implemented by `validate_stage_gate_requirements`.

canonical_rule_id: JF_DL_INV_CURRENT_ROUND_OBJECT_BINDING
source_section_id: 03::INVARIANT::JF_DL_INV_CURRENT_ROUND_OBJECT_BINDING

Generated mechanical invariant implemented by `validate_review_input_binding`.

canonical_rule_id: JF_DL_INV_CODEX_EVIDENCE_BUNDLE_BINDING
source_section_id: 03::INVARIANT::JF_DL_INV_CODEX_EVIDENCE_BUNDLE_BINDING

Generated mechanical invariant implemented by `validate_codex_execution_return`.

canonical_rule_id: JF_DL_INV_CODEX_RETURN_STATE_COHERENCE
source_section_id: 03::INVARIANT::JF_DL_INV_CODEX_RETURN_STATE_COHERENCE

Generated mechanical invariant implemented by `validate_codex_execution_return`.

canonical_rule_id: JF_DL_INV_ARTIFACT_REPOSITORY_REVIEW_SPLIT
source_section_id: 03::INVARIANT::JF_DL_INV_ARTIFACT_REPOSITORY_REVIEW_SPLIT

Generated mechanical invariant implemented by `validate_execution_review`.

canonical_rule_id: JF_DL_INV_MERGE_GATE_CONTINUITY
source_section_id: 03::INVARIANT::JF_DL_INV_MERGE_GATE_CONTINUITY

Generated mechanical invariant implemented by `validate_merge_gate_record`.

canonical_rule_id: JF_DL_INV_GITHUB_FIRST_PATH_DISCOVERY
source_section_id: 03::INVARIANT::JF_DL_INV_GITHUB_FIRST_PATH_DISCOVERY

Generated mechanical invariant implemented by `validate_path_discovery_state`.

canonical_rule_id: JF_DL_INV_LOCAL_READ_ONLY_DISCOVERY
source_section_id: 03::INVARIANT::JF_DL_INV_LOCAL_READ_ONLY_DISCOVERY

Generated mechanical invariant implemented by `validate_path_discovery_state`.

canonical_rule_id: JF_DL_INV_BRAIN_FINAL_PATH_BOUNDARY
source_section_id: 03::INVARIANT::JF_DL_INV_BRAIN_FINAL_PATH_BOUNDARY

Generated mechanical invariant implemented by `validate_path_discovery_state`.

canonical_rule_id: JF_P2_INV_GOAL_CONDITIONED_STRUCTURAL_DISCOVERY
source_section_id: 03::INVARIANT::JF_P2_INV_GOAL_CONDITIONED_STRUCTURAL_DISCOVERY

Generated mechanical invariant implemented by `validate_path_discovery_return`.

canonical_rule_id: JF_P2_INV_SEMANTIC_STRUCTURAL_FIBER_MAPPING
source_section_id: 03::INVARIANT::JF_P2_INV_SEMANTIC_STRUCTURAL_FIBER_MAPPING

Generated mechanical invariant implemented by `validate_path_discovery_return`.

canonical_rule_id: JF_P2_INV_STRUCTURAL_QUESTION_CLOSURE
source_section_id: 03::INVARIANT::JF_P2_INV_STRUCTURAL_QUESTION_CLOSURE

Generated mechanical invariant implemented by `validate_path_discovery_return`.

canonical_rule_id: JF_P2_INV_LONG_TERM_STRUCTURAL_PROJECTION
source_section_id: 03::INVARIANT::JF_P2_INV_LONG_TERM_STRUCTURAL_PROJECTION

Generated mechanical invariant implemented by `validate_long_term_structural_projection`.

canonical_rule_id: JF_DL_INV_PATH_DISCOVERY_RETURN
source_section_id: 03::INVARIANT::JF_DL_INV_PATH_DISCOVERY_RETURN

Generated mechanical invariant implemented by `validate_path_discovery_return`.

canonical_rule_id: JF_DL_INV_GITHUB_PATH_EVIDENCE_OBJECT_BINDING
source_section_id: 03::INVARIANT::JF_DL_INV_GITHUB_PATH_EVIDENCE_OBJECT_BINDING

Generated mechanical invariant implemented by `validate_github_path_evidence`.

canonical_rule_id: JF_DL_INV_FINAL_PATH_DECISION_SOURCE_BINDING
source_section_id: 03::INVARIANT::JF_DL_INV_FINAL_PATH_DECISION_SOURCE_BINDING

Generated mechanical invariant implemented by `validate_final_path_decision`.

canonical_rule_id: JF_DL_INV_FINAL_PATH_GITHUB_COVERAGE
source_section_id: 03::INVARIANT::JF_DL_INV_FINAL_PATH_GITHUB_COVERAGE

Generated mechanical invariant implemented by `validate_final_path_decision`.

canonical_rule_id: JF_DL_INV_WORKTREE_FINGERPRINT_NO_MUTATION
source_section_id: 03::INVARIANT::JF_DL_INV_WORKTREE_FINGERPRINT_NO_MUTATION

Generated mechanical invariant implemented by `validate_path_discovery_return`.

canonical_rule_id: JF_DL_INV_LITERAL_PREFIX_PATH_BOUNDARY
source_section_id: 03::INVARIANT::JF_DL_INV_LITERAL_PREFIX_PATH_BOUNDARY

Generated mechanical invariant implemented by `_valid_repo_path`.

canonical_rule_id: JF_DL_INV_GITHUB_PATH_SCOPE_CONTENT_BINDING
source_section_id: 03::INVARIANT::JF_DL_INV_GITHUB_PATH_SCOPE_CONTENT_BINDING

Generated mechanical invariant implemented by `validate_github_path_evidence`.

canonical_rule_id: JF_DL_INV_LOCAL_DISCOVERY_TYPED_EVIDENCE
source_section_id: 03::INVARIANT::JF_DL_INV_LOCAL_DISCOVERY_TYPED_EVIDENCE

Generated mechanical invariant implemented by `validate_path_discovery_return`.

canonical_rule_id: JF_DL_INV_LOCAL_RETURN_ITEM_SOURCE_BINDING
source_section_id: 03::INVARIANT::JF_DL_INV_LOCAL_RETURN_ITEM_SOURCE_BINDING

Generated mechanical invariant implemented by `validate_final_path_decision`.

canonical_rule_id: JF_DL_INV_LOCAL_DISCOVERY_QUESTIONS_CLOSED
source_section_id: 03::INVARIANT::JF_DL_INV_LOCAL_DISCOVERY_QUESTIONS_CLOSED

Generated mechanical invariant implemented by `validate_local_discovery_seal_input`.

canonical_rule_id: JF_DL_INV_DISTINCT_WORKTREE_CAPTURES
source_section_id: 03::INVARIANT::JF_DL_INV_DISTINCT_WORKTREE_CAPTURES

Generated mechanical invariant implemented by `validate_path_discovery_return`.

canonical_rule_id: INV_CODEX_BOUNDED_TECHNICAL_JUDGMENT
source_section_id: 03::INVARIANT::INV_CODEX_BOUNDED_TECHNICAL_JUDGMENT

Generated mechanical invariant implemented by `validate_codex_execution_return`.

canonical_rule_id: INV_CODEX_TECHNICAL_OBJECTION_STOPS_EXECUTION
source_section_id: 03::INVARIANT::INV_CODEX_TECHNICAL_OBJECTION_STOPS_EXECUTION

Generated mechanical invariant implemented by `validate_codex_execution_return`.

canonical_rule_id: INV_BLOCKED_RETURN_MAY_OMIT_PR_OR_ARTIFACT
source_section_id: 03::INVARIANT::INV_BLOCKED_RETURN_MAY_OMIT_PR_OR_ARTIFACT

Generated mechanical invariant implemented by `validate_codex_execution_return`.

canonical_rule_id: INV_BLOCKED_RETURN_CANNOT_BECOME_BRAIN_PASS
source_section_id: 03::INVARIANT::INV_BLOCKED_RETURN_CANNOT_BECOME_BRAIN_PASS

Generated mechanical invariant implemented by `validate_execution_review`.

canonical_rule_id: INV_CODEX_EXPECTED_OBSERVED_REF_SEPARATION
source_section_id: 03::INVARIANT::INV_CODEX_EXPECTED_OBSERVED_REF_SEPARATION

Generated mechanical invariant implemented by `validate_codex_execution_return`.

canonical_rule_id: INV_CODEX_PREFLIGHT_TYPED_EVIDENCE_BINDING
source_section_id: 03::INVARIANT::INV_CODEX_PREFLIGHT_TYPED_EVIDENCE_BINDING

Generated mechanical invariant implemented by `validate_codex_execution_return`.

canonical_rule_id: INV_CODEX_SCOPE_GAP_OUTSIDE_APPROVED_PATHS
source_section_id: 03::INVARIANT::INV_CODEX_SCOPE_GAP_OUTSIDE_APPROVED_PATHS

Generated mechanical invariant implemented by `validate_codex_execution_return`.

canonical_rule_id: INV_CODEX_PR_MUTATION_DIFF_COHERENCE
source_section_id: 03::INVARIANT::INV_CODEX_PR_MUTATION_DIFF_COHERENCE

Generated mechanical invariant implemented by `validate_codex_execution_return`.

canonical_rule_id: INV_BLOCKED_RETURN_EXACT_REVIEW_TARGET
source_section_id: 03::INVARIANT::INV_BLOCKED_RETURN_EXACT_REVIEW_TARGET

Generated mechanical invariant implemented by `validate_review_input_binding`.

canonical_rule_id: INV_BRAIN_NON_EXHAUSTIVE_TECHNICAL_ROUTE_SPACE
source_section_id: 03::INVARIANT::INV_BRAIN_NON_EXHAUSTIVE_TECHNICAL_ROUTE_SPACE

Generated mechanical invariant implemented by `validate_technical_route_space`.

canonical_rule_id: INV_CODEX_EXACT_PREFLIGHT_OBLIGATION_COVERAGE
source_section_id: 03::INVARIANT::INV_CODEX_EXACT_PREFLIGHT_OBLIGATION_COVERAGE

Generated mechanical invariant implemented by `validate_codex_execution_return`.

canonical_rule_id: INV_CODEX_ALL_CANDIDATES_EVALUATED
source_section_id: 03::INVARIANT::INV_CODEX_ALL_CANDIDATES_EVALUATED

Generated mechanical invariant implemented by `validate_codex_execution_return`.

canonical_rule_id: INV_CODEX_EQUIVALENT_ALTERNATIVE_BOUNDARY
source_section_id: 03::INVARIANT::INV_CODEX_EQUIVALENT_ALTERNATIVE_BOUNDARY

Generated mechanical invariant implemented by `validate_codex_execution_return`.

canonical_rule_id: INV_EXECUTION_RAW_CAPTURE_BINDING
source_section_id: 03::INVARIANT::INV_EXECUTION_RAW_CAPTURE_BINDING

Generated mechanical invariant implemented by `validate_codex_execution_evidence_bundle`.

canonical_rule_id: INV_EXECUTION_OBJECT_IDENTITY
source_section_id: 03::INVARIANT::INV_EXECUTION_OBJECT_IDENTITY

Generated mechanical invariant implemented by `validate_task_object_anchor`.

canonical_rule_id: INV_INITIAL_REVIEW_EXACT_SOURCE_TRIO
source_section_id: 03::INVARIANT::INV_INITIAL_REVIEW_EXACT_SOURCE_TRIO

Generated mechanical invariant implemented by `validate_review_seal_input`.

canonical_rule_id: INV_TASK_BOUND_PREFLIGHT_SUBJECT
source_section_id: 03::INVARIANT::INV_TASK_BOUND_PREFLIGHT_SUBJECT

Generated mechanical invariant implemented by `validate_technical_route_space`.

canonical_rule_id: INV_CANDIDATE_REQUIRED_PATH_WITHIN_APPROVAL
source_section_id: 03::INVARIANT::INV_CANDIDATE_REQUIRED_PATH_WITHIN_APPROVAL

Generated mechanical invariant implemented by `validate_codex_execution_return`.

canonical_rule_id: INV_TYPED_FACT_CODEX_DERIVATION_SEPARATION
source_section_id: 03::INVARIANT::INV_TYPED_FACT_CODEX_DERIVATION_SEPARATION

Generated mechanical invariant implemented by `validate_codex_execution_evidence_bundle`.

canonical_rule_id: INV_APPROVED_TEST_COMMAND_BINDING
source_section_id: 03::INVARIANT::INV_APPROVED_TEST_COMMAND_BINDING

Generated mechanical invariant implemented by `validate_codex_execution_return`.

canonical_rule_id: INV_MISMATCH_STOPS_ROUTE_EVALUATION
source_section_id: 03::INVARIANT::INV_MISMATCH_STOPS_ROUTE_EVALUATION

Generated mechanical invariant implemented by `validate_codex_execution_return`.

canonical_rule_id: INV_REVIEW_SOURCE_DERIVED_SNAPSHOT_CONTINUITY
source_section_id: 03::INVARIANT::INV_REVIEW_SOURCE_DERIVED_SNAPSHOT_CONTINUITY

Generated mechanical invariant implemented by `validate_review_seal_input`.

canonical_rule_id: INV_GITHUB_PATH_REPOSITORY_SOURCE_REPLAY
source_section_id: 03::INVARIANT::INV_GITHUB_PATH_REPOSITORY_SOURCE_REPLAY

Generated mechanical invariant implemented by `verify_github_path_evidence_against_repository`.

canonical_rule_id: INV_PATH_DISCOVERY_REPOSITORY_SOURCE_REPLAY
source_section_id: 03::INVARIANT::INV_PATH_DISCOVERY_REPOSITORY_SOURCE_REPLAY

Generated mechanical invariant implemented by `verify_path_discovery_return_against_repository`.

canonical_rule_id: INV_EXECUTION_PROJECTION_PREMUTATION_REPLAY
source_section_id: 03::INVARIANT::INV_EXECUTION_PROJECTION_PREMUTATION_REPLAY

Generated mechanical invariant implemented by `validate_execution_projection_sources`.

canonical_rule_id: INV_EXECUTION_EVIDENCE_CURRENT_SOURCE_REPLAY
source_section_id: 03::INVARIANT::INV_EXECUTION_EVIDENCE_CURRENT_SOURCE_REPLAY

Generated mechanical invariant implemented by `verify_execution_evidence_bundle_against_source`.

canonical_rule_id: INV_TEST_COMMAND_CURRENT_SOURCE_REPLAY
source_section_id: 03::INVARIANT::INV_TEST_COMMAND_CURRENT_SOURCE_REPLAY

Generated mechanical invariant implemented by `verify_execution_evidence_bundle_against_source`.

canonical_rule_id: INV_REVIEW_CURRENT_SOURCE_REPLAY
source_section_id: 03::INVARIANT::INV_REVIEW_CURRENT_SOURCE_REPLAY

Generated mechanical invariant implemented by `validate_review_input_binding`.

canonical_rule_id: INV_PR_DIFF_EXACT_BASE_HEAD_REPLAY
source_section_id: 03::INVARIANT::INV_PR_DIFF_EXACT_BASE_HEAD_REPLAY

Generated mechanical invariant implemented by `verify_github_path_evidence_against_repository`.

canonical_rule_id: INV_LOCAL_DISCOVERY_DIRECT_FACT_DERIVATION_SPLIT
source_section_id: 03::INVARIANT::INV_LOCAL_DISCOVERY_DIRECT_FACT_DERIVATION_SPLIT

Generated mechanical invariant implemented by `validate_path_discovery_return`.

canonical_rule_id: INV_BOUNDED_DECLARED_IGNORED_PATH_COVERAGE
source_section_id: 03::INVARIANT::INV_BOUNDED_DECLARED_IGNORED_PATH_COVERAGE

Generated mechanical invariant implemented by `validate_path_discovery_return`.

canonical_rule_id: INV_APPROVED_VALIDATION_ARGV_CWD_BINDING
source_section_id: 03::INVARIANT::INV_APPROVED_VALIDATION_ARGV_CWD_BINDING

Generated mechanical invariant implemented by `validate_validation_closure`.

canonical_rule_id: INV_OPERATIONAL_TEST_REPLAY_MANDATORY
source_section_id: 03::INVARIANT::INV_OPERATIONAL_TEST_REPLAY_MANDATORY

Generated mechanical invariant implemented by `verify_execution_evidence_bundle_against_source`.

canonical_rule_id: INV_TASK_OBJECT_LIFECYCLE_DIGEST_BOUND
source_section_id: 03::INVARIANT::INV_TASK_OBJECT_LIFECYCLE_DIGEST_BOUND

Generated mechanical invariant implemented by `validate_task_object_lifecycle`.

canonical_rule_id: INV_APPROVED_BASE_ANCESTOR_OF_RESULT_HEAD
source_section_id: 03::INVARIANT::INV_APPROVED_BASE_ANCESTOR_OF_RESULT_HEAD

Generated mechanical invariant implemented by `verify_execution_evidence_bundle_against_source`.

canonical_rule_id: INV_FINAL_VALIDATION_TARGET_EQUALS_EXECUTION_RESULT
source_section_id: 03::INVARIANT::INV_FINAL_VALIDATION_TARGET_EQUALS_EXECUTION_RESULT

Generated mechanical invariant implemented by `validate_execution_lifecycle_result_structure`.

canonical_rule_id: INV_RESULT_HEAD_DETACHED_WORKTREE_VALIDATION
source_section_id: 03::INVARIANT::INV_RESULT_HEAD_DETACHED_WORKTREE_VALIDATION

Generated mechanical invariant implemented by `verify_execution_evidence_bundle_against_source`.

canonical_rule_id: INV_ARTIFACT_OUTPUT_SET_REVIEW_CONTINUITY
source_section_id: 03::INVARIANT::INV_ARTIFACT_OUTPUT_SET_REVIEW_CONTINUITY

Generated mechanical invariant implemented by `validate_review_input_binding`.

canonical_rule_id: INV_TYPED_IGNORED_COVERAGE
source_section_id: 03::INVARIANT::INV_TYPED_IGNORED_COVERAGE

Generated mechanical invariant implemented by `_normalize_ignored_coverage`.

canonical_rule_id: INV_DEDICATED_REPOSITORY_REVIEW_ENTRY
source_section_id: 03::INVARIANT::INV_DEDICATED_REPOSITORY_REVIEW_ENTRY

Generated mechanical invariant implemented by `prepare_repository_review_capsule`.

canonical_rule_id: INV_DEDICATED_ARTIFACT_REVIEW_ENTRY
source_section_id: 03::INVARIANT::INV_DEDICATED_ARTIFACT_REVIEW_ENTRY

Generated mechanical invariant implemented by `prepare_artifact_review_capsule`.

canonical_rule_id: INV_DISCOVERY_SOURCE_OBJECT_TRANSITION
source_section_id: 03::INVARIANT::INV_DISCOVERY_SOURCE_OBJECT_TRANSITION

Generated mechanical invariant implemented by `verify_projection_path_sources_against_repository`.

canonical_rule_id: INV_IGNORED_EXACT_SYMLINK_NO_FOLLOW
source_section_id: 03::INVARIANT::INV_IGNORED_EXACT_SYMLINK_NO_FOLLOW

Generated mechanical invariant implemented by `_manifest_row_for_path`.

canonical_rule_id: INV_IGNORED_EXCLUSION_SUBTREE_PRUNING
source_section_id: 03::INVARIANT::INV_IGNORED_EXCLUSION_SUBTREE_PRUNING

Generated mechanical invariant implemented by `_recursive_directory_manifest`.

canonical_rule_id: INV_DECLARED_IGNORED_DIRECT_FACT_SET
source_section_id: 03::INVARIANT::INV_DECLARED_IGNORED_DIRECT_FACT_SET

Generated mechanical invariant implemented by `verify_path_discovery_return_against_repository`.

canonical_rule_id: INV_ARTIFACT_COMPLETE_OUTPUT_SET
source_section_id: 03::INVARIANT::INV_ARTIFACT_COMPLETE_OUTPUT_SET

Generated mechanical invariant implemented by `validate_execution_lifecycle_result_structure`.

canonical_rule_id: INV_ARTIFACT_OUTPUT_TARGETED_VALIDATION
source_section_id: 03::INVARIANT::INV_ARTIFACT_OUTPUT_TARGETED_VALIDATION

Generated mechanical invariant implemented by `verify_execution_evidence_bundle_against_source`.

canonical_rule_id: INV_NEW_ARTIFACT_SOURCE_MATERIAL_SET
source_section_id: 03::INVARIANT::INV_NEW_ARTIFACT_SOURCE_MATERIAL_SET

Generated mechanical invariant implemented by `prepare_artifact_review_capsule`.

canonical_rule_id: INV_BOUNDARY_SAFE_OBJECT_RESOLUTION
source_section_id: 03::INVARIANT::INV_BOUNDARY_SAFE_OBJECT_RESOLUTION

Generated mechanical invariant implemented by `_boundary_safe_repository_object`.

canonical_rule_id: INV_OBSERVATION_ONLY_FINAL_VALIDATION
source_section_id: 03::INVARIANT::INV_OBSERVATION_ONLY_FINAL_VALIDATION

Generated mechanical invariant implemented by `verify_execution_evidence_bundle_against_source`.

canonical_rule_id: INV_VALIDATION_WORKSPACE_COMPLETE_OBJECT_SET
source_section_id: 03::INVARIANT::INV_VALIDATION_WORKSPACE_COMPLETE_OBJECT_SET

Generated mechanical invariant implemented by `_validation_workspace_tree_snapshot`.

canonical_rule_id: INV_REPOSITORY_VALIDATION_GIT_ADMIN_ISOLATION
source_section_id: 03::INVARIANT::INV_REPOSITORY_VALIDATION_GIT_ADMIN_ISOLATION

Generated mechanical invariant implemented by `_detached_validation_worktree`.

canonical_rule_id: INV_ARTIFACT_DEDICATED_OUTPUT_ROOT_COMPLETE_SET
source_section_id: 03::INVARIANT::INV_ARTIFACT_DEDICATED_OUTPUT_ROOT_COMPLETE_SET

Generated mechanical invariant implemented by `_validate_artifact_output_root`.

canonical_rule_id: INV_IMMUTABLE_REVIEW_SOURCE_EVIDENCE
source_section_id: 03::INVARIANT::INV_IMMUTABLE_REVIEW_SOURCE_EVIDENCE

Generated mechanical invariant implemented by `validate_review_input_binding`.

canonical_rule_id: INV_SEALED_OBJECT_TRANSITION
source_section_id: 03::INVARIANT::INV_SEALED_OBJECT_TRANSITION

Generated mechanical invariant implemented by `validate_review_seal_input`.

canonical_rule_id: INV_PHASE1_STAGE_PARENT_PACKAGE_EXACT
source_section_id: 03::INVARIANT::INV_PHASE1_STAGE_PARENT_PACKAGE_EXACT

Generated mechanical invariant implemented by `tools/validate_package.py::verify_stage_lineage`.

canonical_rule_id: INV_PR_CURRENT_BASE_ANCESTOR
source_section_id: 03::INVARIANT::INV_PR_CURRENT_BASE_ANCESTOR

Generated mechanical invariant implemented by `runtime/joyflow_phase1_review.py::validate_pr_record`.

canonical_rule_id: INV_PR_EXACT_SEALED_SOURCE_CHAIN
source_section_id: 03::INVARIANT::INV_PR_EXACT_SEALED_SOURCE_CHAIN

Generated mechanical invariant implemented by `runtime/joyflow_phase1_review.py::validate_pr_record`.

canonical_rule_id: INV_PR_CI_SOURCE_OBSERVATION_ONLY
source_section_id: 03::INVARIANT::INV_PR_CI_SOURCE_OBSERVATION_ONLY

Generated mechanical invariant implemented by `runtime/joyflow_phase1_review.py::build_pr_ci_result`.

canonical_rule_id: INV_MERGE_FREEZE_EXACT_REVIEW_CHAIN
source_section_id: 03::INVARIANT::INV_MERGE_FREEZE_EXACT_REVIEW_CHAIN

Generated mechanical invariant implemented by `runtime/joyflow_phase1_merge.py::validate_merge_candidate_freeze`.

canonical_rule_id: INV_POST_FREEZE_USER_ACCEPTANCE_EXACT_SOURCE
source_section_id: 03::INVARIANT::INV_POST_FREEZE_USER_ACCEPTANCE_EXACT_SOURCE

Generated mechanical invariant implemented by `runtime/joyflow_phase1_merge.py::validate_post_freeze_user_acceptance`.

canonical_rule_id: INV_MERGED_CHANGE_PROJECTION_EXACT_CURRENT_SOURCE
source_section_id: 03::INVARIANT::INV_MERGED_CHANGE_PROJECTION_EXACT_CURRENT_SOURCE

Generated mechanical invariant implemented by `runtime/joyflow_phase1_projection.py::validate_merged_change_projection`.

canonical_rule_id: INV_MERGED_CHANGE_PROJECTION_NAVIGATION_ONLY
source_section_id: 03::INVARIANT::INV_MERGED_CHANGE_PROJECTION_NAVIGATION_ONLY

Generated mechanical invariant implemented by `runtime/joyflow_phase1_projection.py::validate_merged_change_projection`.

canonical_rule_id: INV_PR_CI_EXACT_CURRENT_REVIEW_CHAIN_ONLY
source_section_id: 03::INVARIANT::INV_PR_CI_EXACT_CURRENT_REVIEW_CHAIN_ONLY

Generated mechanical invariant implemented by `runtime/joyflow_phase1_review.py::validate_pr_record`.

canonical_rule_id: INV_MERGE_FREEZE_BEFORE_USER_DECISIONS
source_section_id: 03::INVARIANT::INV_MERGE_FREEZE_BEFORE_USER_DECISIONS

Generated mechanical invariant implemented by `validate_repository_acceptance_freeze_binding`.

canonical_rule_id: INV_USER_MERGE_AUTHORIZATION_EXACT_FREEZE_AND_ACCEPTANCE
source_section_id: 03::INVARIANT::INV_USER_MERGE_AUTHORIZATION_EXACT_FREEZE_AND_ACCEPTANCE

Generated mechanical invariant implemented by `runtime/joyflow_dual_layer.py::validate_user_merge_authorization`.

canonical_rule_id: INV_COMPLETION_POINTER_EXACT_FREEZE_AUTHORIZATION_CHAIN
source_section_id: 03::INVARIANT::INV_COMPLETION_POINTER_EXACT_FREEZE_AUTHORIZATION_CHAIN

Generated mechanical invariant implemented by `runtime/joyflow_dual_layer.py::validate_completion_pointer`.

canonical_rule_id: INV_UNIFIED_EXAMPLE_GENERATION_CURRENT_MODEL
source_section_id: 03::INVARIANT::INV_UNIFIED_EXAMPLE_GENERATION_CURRENT_MODEL

Generated mechanical invariant implemented by `tools/generate_all_examples.py::main`.

canonical_rule_id: INV_MIGRATION_EVIDENCE_STRENGTH_BOUNDARY
source_section_id: 03::INVARIANT::INV_MIGRATION_EVIDENCE_STRENGTH_BOUNDARY

Generated mechanical invariant implemented by `tools/generate_old_rule_migration.py::validate_migration_rows`.

canonical_rule_id: INV_MIGRATION_PER_TARGET_BEHAVIOR_COVERAGE
source_section_id: 03::INVARIANT::INV_MIGRATION_PER_TARGET_BEHAVIOR_COVERAGE

Generated mechanical invariant implemented by `tools/generate_old_rule_migration.py::validate_migration_rows`.

canonical_rule_id: INV_CANDIDATE_CAPABILITY_CLAIM_BOUNDARY
source_section_id: 03::INVARIANT::INV_CANDIDATE_CAPABILITY_CLAIM_BOUNDARY

Generated mechanical invariant implemented by `tools/generate_old_rule_migration.py::validate_capability_status`.

canonical_rule_id: INV_CURRENT_CANDIDATE_DOCUMENT_IDENTITY
source_section_id: 03::INVARIANT::INV_CURRENT_CANDIDATE_DOCUMENT_IDENTITY

Generated mechanical invariant implemented by `tools/validate_package.py::verify_current_candidate_documents`.

canonical_rule_id: INV_LEGACY_SOURCE_IDENTITY_SET_BOUND
source_section_id: 03::INVARIANT::INV_LEGACY_SOURCE_IDENTITY_SET_BOUND

Generated mechanical invariant implemented by `tools/generate_old_rule_migration.py::validate_brain_mapping`.

canonical_rule_id: INV_BRAIN_OWNED_LEGACY_SEMANTIC_MAPPING
source_section_id: 03::INVARIANT::INV_BRAIN_OWNED_LEGACY_SEMANTIC_MAPPING

Generated mechanical invariant implemented by `tools/generate_old_rule_migration.py::load_bound_inputs`.

canonical_rule_id: INV_LEGACY_EQUIVALENCE_COMPOSITE_GATE
source_section_id: 03::INVARIANT::INV_LEGACY_EQUIVALENCE_COMPOSITE_GATE

Generated mechanical invariant implemented by `tools/generate_old_rule_migration.py::validate_migration_rows`.

canonical_rule_id: INV_CAPABILITY_CLAIM_SUBJECT_REGISTRY
source_section_id: 03::INVARIANT::INV_CAPABILITY_CLAIM_SUBJECT_REGISTRY

Generated mechanical invariant implemented by `tools/generate_old_rule_migration.py::validate_capability_status`.

canonical_rule_id: INV_LEGACY_MIGRATION_SCHEMA_CLOSURE
source_section_id: 03::INVARIANT::INV_LEGACY_MIGRATION_SCHEMA_CLOSURE

Generated mechanical invariant implemented by `tools/validate_migration_claims.py::main`.

canonical_rule_id: INV_LEGACY_DISPOSITION_SEPARATE_FROM_MAPPING
source_section_id: 03::INVARIANT::INV_LEGACY_DISPOSITION_SEPARATE_FROM_MAPPING

Generated mechanical invariant implemented by `tools/generate_old_rule_migration.py::validate_brain_mapping`.

canonical_rule_id: INV_SEALED_PER_RULE_DISPOSITION_DECISIONS
source_section_id: 03::INVARIANT::INV_SEALED_PER_RULE_DISPOSITION_DECISIONS

Generated mechanical invariant implemented by `tools/generate_old_rule_migration.py::validate_disposition_decisions`.

canonical_rule_id: INV_DERIVED_CURRENT_TARGET_BEHAVIOR_STATUS
source_section_id: 03::INVARIANT::INV_DERIVED_CURRENT_TARGET_BEHAVIOR_STATUS

Generated mechanical invariant implemented by `tools/generate_old_rule_migration.py::validate_migration_rows`.

canonical_rule_id: INV_LEGACY_EQUIVALENCE_AXIS_SEPARATE
source_section_id: 03::INVARIANT::INV_LEGACY_EQUIVALENCE_AXIS_SEPARATE

Generated mechanical invariant implemented by `tools/generate_old_rule_migration.py::validate_migration_rows`.

canonical_rule_id: INV_PHASE_EFFECT_SEPARATE_FROM_SEMANTIC_STATE
source_section_id: 03::INVARIANT::INV_PHASE_EFFECT_SEPARATE_FROM_SEMANTIC_STATE

Generated mechanical invariant implemented by `tools/generate_old_rule_migration.py::validate_migration_rows`.

canonical_rule_id: INV_CAPABILITY_STATUS_NAVIGATION_ONLY
source_section_id: 03::INVARIANT::INV_CAPABILITY_STATUS_NAVIGATION_ONLY

Generated mechanical invariant implemented by `tools/generate_old_rule_migration.py::validate_capability_status`.

canonical_rule_id: INV_CAPABILITY_VERIFICATION_CONTRACT_DIGEST
source_section_id: 03::INVARIANT::INV_CAPABILITY_VERIFICATION_CONTRACT_DIGEST

Generated mechanical invariant implemented by `tools/generate_old_rule_migration.py::validate_capability_claim_registry`.
