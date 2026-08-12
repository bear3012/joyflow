#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, re, sys, jsonschema
from typing import NamedTuple
TOOLS_DIR=pathlib.Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path: sys.path.insert(0,str(TOOLS_DIR))
from canonical_text import canonical_text_matches, read_canonical_text, write_canonical_text
ROOT=TOOLS_DIR.parent
INVENTORY=ROOT/'machine/legacy_rule_inventory_v1_7_6.json'
SOURCE_SET=ROOT/'machine/legacy_source_set_v1_7_6.json'
BRAIN_MAPPING=ROOT/'machine/brain_legacy_semantic_mapping_v1_7_6.json'
BRAIN_MAPPING_SEAL=ROOT/'machine/brain_legacy_semantic_mapping_seal.json'
DISPOSITION_DECISIONS=ROOT/'machine/legacy_disposition_decisions_v1_7_6.json'
DISPOSITION_SEAL=ROOT/'machine/legacy_disposition_decisions_seal.json'
CAPABILITY_CLAIM_REGISTRY=ROOT/'machine/capability_claim_registry.json'
TARGET_MAP={'JF_AI_COMPATIBLE_STRUCTURE_JUDGMENT_RULE': ['JF_DL_AI_COMPATIBLE_STRUCTURE_RULE'],
 'JF_APPROVAL_EXACT_BINDING_RULE': ['JF_DL_DETERMINISTIC_APPROVAL_VIEW_RULE', 'JF_DL_INV_APPROVAL_OWNERSHIP_BINDING'],
 'JF_BOOTLOADER_BOUNDARY_RULE': ['JF_DL_SOURCE_TRUTH_BOUNDARY_RULE'],
 'JF_BRAIN_FIRST_RULE': ['JF_DL_BRAIN_FIRST_RULE'],
 'JF_BRAIN_TECHNICAL_REVIEW_RULE': ['JF_DL_MECHANICAL_WALKTHROUGH_RULE', 'JF_DL_EXECUTION_REVIEW_RULE'],
 'JF_CODE_IDENTIFIER_NAMING_RULE': ['JF_DL_CODE_IDENTIFIER_NAMING_RULE'],
 'JF_DETAIL_SOURCE_ESCALATION_RULE': ['JF_DL_MINIMUM_SOURCE_LOADING_RULE'],
 'JF_DISCOVERY_EVIDENCE_RULE': ['JF_DL_REPOSITORY_EVIDENCE_REFERENCE_RULE',
                                'JF_DL_GITHUB_FIRST_PATH_DISCOVERY_RULE',
                                'JF_DL_CODEX_SUPPLEMENTAL_LOCAL_DISCOVERY_RULE',
                                'JF_DL_BRAIN_FINAL_PATH_BOUNDARY_RULE'],
 'JF_DISCRETE_BASE_GRAPH_RULE': ['JF_DL_STAGE_FIBER_CYCLE_SEPARATION_RULE'],
 'JF_DOMAIN_LANE_ACTIVATION_RULE': ['JF_DL_DOMAIN_LANE_CLASSIFICATION_RULE', 'JF_DL_RISK_ROUTE_SELECTION_RULE'],
 'JF_DOMAIN_LANE_REGISTRY_RULE': ['JF_DL_DOMAIN_LANE_CLASSIFICATION_RULE'],
 'JF_DOMAIN_LANE_TECHNOLOGY_RULE': ['JF_DL_DOMAIN_LANE_CLASSIFICATION_RULE'],
 'JF_DURABLE_PR_EVIDENCE_RULE': ['JF_DL_EXECUTION_REVIEW_RULE', 'JF_DL_PR_CANDIDATE_ONLY_RULE'],
 'JF_EVIDENCE_CLAIM_LEVEL_RULE': ['JF_DL_EVIDENCE_REGISTRY_RULE'],
 'JF_EXACT_EVIDENCE_KIND_RULE': ['JF_DL_VALIDATION_CLOSURE_RULE', 'JF_DL_EVIDENCE_REGISTRY_RULE'],
 'JF_FAILED_CHECK_RETURN_RULE': ['JF_DL_REPAIR_CIRCUIT_BREAKER_RULE'],
 'JF_FEATURE_SLICE_LAYOUT_RULE': ['JF_DL_FEATURE_SLICE_LAYOUT_RULE'],
 'JF_FIBERED_SINGLE_STATE_RULE': ['JF_DL_TASK_CAPSULE_TEMPORARY_RULE', 'JF_DL_DUAL_LAYER_CLOSURE_RULE'],
 'JF_FIBER_REGISTRY_RULE': ['JF_DL_OPTIONAL_FIBER_RULE'],
 'JF_FINAL_MERGE_GATE_RULE': ['JF_DL_MERGE_PROMOTION_RULE'],
 'JF_GENERATED_ASSET_BOUNDARY_RULE': ['JF_DL_GENERATED_ASSET_BOUNDARY_RULE'],
 'JF_GLOBAL_SECTION_PROJECTION_RULE': ['JF_DL_HIGH_FIDELITY_COMPILER_RULE'],
 'JF_GLOBAL_SECTION_RULE': ['JF_DL_DUAL_LAYER_CLOSURE_RULE'],
 'JF_GOAL_ACCEPTANCE_COVERAGE_RULE': ['JF_DL_VALIDATION_CLOSURE_RULE', 'JF_DL_INV_VALIDATION_OBLIGATIONS'],
 'JF_HIGH_FIDELITY_TRANSPORT_RULE': ['JF_DL_SEMANTIC_EFFECT_TRANSPORT_RULE', 'JF_DL_INV_SEMANTIC_EFFECT_TRANSPORT'],
 'JF_INV_ROUTE_PROFILE_MATCH': ['JF_DL_INV_ROUTE_PROFILE_MATCH'],
 'JF_JOYKEEP_REDESIGN_DEFERRED_RULE': ['JF_DL_DEFERRED_SCOPE_RULE'],
 'JF_MACHINE_HUMAN_VALIDATION_SPLIT_RULE': ['JF_DL_VALIDATION_CLOSURE_RULE'],
 'JF_MINIMUM_SOURCE_LOADING_RULE': ['JF_DL_MINIMUM_SOURCE_LOADING_RULE'],
 'JF_NEAREST_RETURN_FIBER_RULE': ['JF_DL_NARROW_SPIRAL_RULE', 'JF_DL_STAGE_FIBER_CYCLE_SEPARATION_RULE'],
 'JF_NO_EVIDENCE_NO_COMPLETION_RULE': ['JF_DL_VALIDATION_CLOSURE_RULE', 'JF_DL_INV_VALIDATION_OBLIGATIONS'],
 'JF_ONE_COMPLETE_CODEX_PROMPT_RULE': ['JF_DL_HIGH_FIDELITY_COMPILER_RULE', 'JF_DL_PROMPT_ROUND_TRIP_RULE'],
 'JF_ONE_ROUTE_PROFILE_RULE': ['JF_DL_RISK_ROUTE_SELECTION_RULE', 'JF_DL_INV_ROUTE_PROFILE_MATCH'],
 'JF_PLATFORM_MANAGED_PAYMENT_RULE': ['JF_DL_DOMAIN_LANE_CLASSIFICATION_RULE', 'JF_DL_RISK_ROUTE_SELECTION_RULE'],
 'JF_PROMPT_DATA_ISOLATION_RULE': ['JF_DL_PROMPT_ROUND_TRIP_RULE'],
 'JF_PROTECTED_CORE_EXTENSION_RULE': ['JF_DL_RISK_ROUTE_SELECTION_RULE', 'JF_DL_PROTECTED_CORE_PLACEMENT_RULE'],
 'JF_PROTECTED_CORE_PLACEMENT_RULE': ['JF_DL_PROTECTED_CORE_PLACEMENT_RULE'],
 'JF_PROTOCOL_REPAIR_WORKFLOW_RULE': ['JF_DL_PROTOCOL_REPAIR_WORKFLOW_RULE'],
 'JF_PR_DESCRIPTION_CONTRACT_SURFACE_RULE': ['JF_DL_EXECUTION_REVIEW_RULE', 'JF_DL_PR_CANDIDATE_ONLY_RULE'],
 'JF_PR_FIRST_EXECUTION_RULE': ['JF_DL_PR_CANDIDATE_ONLY_RULE'],
 'JF_READ_ONLY_DISCOVERY_RULE': ['JF_DL_READ_ONLY_DISCOVERY_RULE', 'JF_DL_PATH_DISCOVERY_RETURN_RULE'],
 'JF_REPAIR_CIRCUIT_BREAKER_RULE': ['JF_DL_REPAIR_CIRCUIT_BREAKER_RULE'],
 'JF_REPOSITORY_CONTEXT_DEFERRED_RULE': ['JF_DL_DEFERRED_SCOPE_RULE'],
 'JF_REPOSITORY_FACT_BOUNDARY_RULE': ['JF_DL_REPOSITORY_CANONICAL_TRUTH_RULE', 'JF_DL_REPOSITORY_EVIDENCE_REFERENCE_RULE'],
 'JF_REPO_ARTIFACT_PLACEMENT_RULE': ['JF_DL_REPO_ARTIFACT_PLACEMENT_RULE'],
 'JF_REPO_GOVERNANCE_FILE_RULE': ['JF_DL_REPO_GOVERNANCE_FILE_RULE'],
 'JF_REPO_POLICY_PR_EVIDENCE_RULE': ['JF_DL_PR_CANDIDATE_ONLY_RULE', 'JF_DL_EXECUTION_REVIEW_RULE'],
 'JF_ROLE_BOUNDARY_RULE': ['JF_DL_BRAIN_FIRST_RULE', 'JF_DL_PROJECTION_PROMOTION_SEPARATION_RULE'],
 'JF_ROUTE_BOUND_VALIDATION_RULE': ['JF_DL_RISK_ROUTE_SELECTION_RULE', 'JF_DL_VALIDATION_CLOSURE_RULE'],
 'JF_ROUTE_PROFILE_REGISTRY_RULE': ['JF_DL_INV_ROUTE_PROFILE_MATCH'],
 'JF_SINGLE_STATE_VIEW_RULE': ['JF_DL_TASK_CAPSULE_TEMPORARY_RULE', 'JF_DL_DETERMINISTIC_APPROVAL_VIEW_RULE'],
 'JF_SOURCE_COMPATIBLE_REPAIR_RULE': ['JF_DL_REPAIR_EXTENSION_RULE', 'JF_DL_INV_REPAIR_COMPATIBILITY'],
 'JF_SOURCE_GOVERNANCE_RULE': ['JF_DL_SOURCE_TRUTH_BOUNDARY_RULE'],
 'JF_TOKEN_SECONDARY_RULE': ['JF_DL_HIGH_FIDELITY_COMPILER_RULE'],
 'JF_TRANSPARENT_CODEX_RUNTIME_BOUNDARY_RULE': ['JF_DL_CODEX_RUNTIME_TRANSPARENT_RULE'],
 'JF_TRANSPORT_MAP_RULE': ['JF_DL_SEMANTIC_EFFECT_TRANSPORT_RULE', 'JF_DL_INV_SEMANTIC_EFFECT_TRANSPORT'],
 'JF_USER_READABLE_CONSEQUENCE_RULE': ['JF_DL_DETERMINISTIC_APPROVAL_VIEW_RULE'],
 'JF_USER_VALIDATION_MERGE_RULE': ['JF_DL_EXECUTION_REVIEW_RULE', 'JF_DL_MERGE_PROMOTION_RULE']}
REGISTRY=[{'verification_id': 'E_TARGET_PRESENT',
  'kind': 'UNIT_TEST',
  'claim_strength': 'STRUCTURAL_PRESENCE',
  'covered_target_rule_ids': [],
  'concrete_refs': ['tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_every_target_rule_exists'],
  'coverage_statement': 'Every migration target resolves to an active current Project Source rule ID.',
  'limitations': ['Target presence does not prove behavioral equivalence.'],
  'allowed_capability_ids': []},
 {'verification_id': 'E_SOURCE_INDEX',
  'kind': 'COMMAND',
  'claim_strength': 'SOURCE_CONSISTENCY',
  'covered_target_rule_ids': [],
  'concrete_refs': ['python runtime/joyflow_source_validator.py .'],
  'coverage_statement': 'Current Project Sources and generated rule index are mechanically consistent.',
  'limitations': ['Source consistency does not prove runtime behavior.'],
  'allowed_capability_ids': []},
 {'verification_id': 'E_EXPLICIT_DEFERRAL',
  'kind': 'POLICY',
  'claim_strength': 'EXPLICIT_DEFERRAL',
  'covered_target_rule_ids': ['JF_DL_DEFERRED_SCOPE_RULE'],
  'concrete_refs': ['project_sources/10_DEFERRED_AREAS.md'],
  'coverage_statement': 'The capability is explicitly outside the current active scope.',
  'limitations': ['Deferred behavior is not implemented or verified.'],
  'allowed_capability_ids': []},
 {'verification_id': 'E_RETIREMENT_RATIONALE',
  'kind': 'POLICY',
  'claim_strength': 'RETIREMENT_RATIONALE',
  'covered_target_rule_ids': [],
  'concrete_refs': ['project_sources/14_PHASE1F_MIGRATION_CLAIM_TRUTHFULNESS.md'],
  'coverage_statement': 'Retired forms retain a reason and current replacement target.',
  'limitations': ['Retirement rationale is not runtime equivalence evidence.'],
  'allowed_capability_ids': []},
 {'verification_id': 'E_MIGRATION_TRUTHFULNESS_ADVERSARIAL',
  'kind': 'UNIT_TEST',
  'claim_strength': 'BEHAVIOR_ADVERSARIAL',
  'covered_target_rule_ids': ['RULE_LEGACY_SOURCE_IDENTITY_SET',
                              'RULE_BRAIN_OWNED_LEGACY_SEMANTIC_MAPPING',
                              'RULE_LEGACY_DISPOSITION_DECISION_SEPARATION',
                              'RULE_LEGACY_MIGRATION_EVIDENCE_STRENGTH',
                              'RULE_LEGACY_MIGRATION_PER_TARGET_COVERAGE',
                              'RULE_LEGACY_MIGRATION_STATUS_SEMANTICS',
                              'RULE_CAPABILITY_STATUS_NAVIGATION_ONLY',
                              'RULE_CAPABILITY_EVIDENCE_CONTRACT_BINDING',
                              'RULE_CURRENT_CANDIDATE_DOCUMENT_IDENTITY',
                              'RULE_LEGACY_MIGRATION_SCHEMA_CLOSURE',
                              'RULE_LEGACY_PHASE_EFFECT_SEPARATION',
                              'RULE_DERIVED_TARGET_BEHAVIOR_STATUS',
                              'RULE_PRODUCT_DIRECTION_BOUND_DISPOSITION_AUTHORITY',
                              'RULE_SPARSE_USER_DECISION_GATE',
                              'RULE_DISPOSITION_PRODUCT_DIRECTION_EFFECT',
                              'RULE_PR1F_MECHANISM_EFFECT_SCOPE',
                              'RULE_HISTORICAL_REVIEW_CONTEXT_MARKING',
                              'RULE_DISPOSITION_TRANSITION_CONTRACT_SINGLE_SOURCE',
                              'RULE_TECHNICAL_RETIREMENT_SEMANTIC_EVIDENCE_GATE',
                              'RULE_DISPOSITION_TRANSITION_POSITIVE_COVERAGE'],
  'concrete_refs': ['tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_every_target_rule_exists',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_all_concrete_verification_refs_resolve',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_former_conflated_capability_input_removed',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_current_candidate_has_no_legacy_equivalence_claim',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_all_dispositions_are_not_evaluated',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_all_current_product_direction_effects_are_unresolved',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_behavior_status_requires_exact_text_and_confirmed_brain_mapping',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_brain_interpretation_mutation_without_digest_blocks',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_wrong_inventory_section_blocks',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_wrong_legacy_source_hash_blocks',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_semantic_mapping_cannot_contain_disposition',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_unsealed_disposition_mutation_blocks',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_defer_requires_exact_current_basis',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_retire_by_product_requires_user_owner_and_ref',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_brain_technical_defer_does_not_require_user_row_approval',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_brain_cannot_close_unknown_material_effect',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_brain_cannot_change_confirmed_product_direction',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_current_product_decision_requires_exact_user_ref',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_technical_duplication_retirement_requires_confirmed_semantic_gate',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_legacy_semantic_retirement_requires_confirmed_semantic_gate',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_transition_contract_all_legal_combinations_align_schema_validator_and_deriver',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_transition_contract_schema_rejects_unsupported_combination',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_technical_duplication_retirement_derives_confirmed_semantic_supersession',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_structural_or_source_evidence_cannot_support_behavior_status',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_multi_target_missing_one_behavior_ref_is_derived_partial',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_behavior_verified_targets_and_unverified_targets_are_disjoint',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_verified_behavior_does_not_close_legacy_equivalence',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_phase_effect_keeps_disposition_open',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_phase_effect_does_not_block_truthful_mechanism',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_phase_effect_does_not_decide_phase1_completion',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_retirement_policy_cannot_be_target_behavior_evidence',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_legacy_source_schema_rejects_unknown_field',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_brain_mapping_schema_rejects_wrong_owner_type',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_disposition_schema_rejects_unknown_field',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_migration_schema_rejects_old_ambiguous_field',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_nonexistent_test_symbol_blocks',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_capability_status_is_navigation_only',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_capability_status_exact_registry_subjects',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_arbitrary_capability_name_blocks_even_in_view',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_unrelated_concrete_ref_breaks_capability_contract',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_package_cannot_self_claim_independent_cold_review',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_capability_view_cannot_be_promoted_to_gate',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_generated_outputs_are_deterministic',
                    'tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_all_176_rows_have_one_truthful_status'],
  'coverage_statement': 'Adversarial cases block semantic/disposition collapse, evidence-axis contradictions, capability-view promotion, evidence-contract substitution, schema drift and '
                        'self-promotion.',
  'limitations': ['This verifies the PR1F classification mechanism, not legacy semantic equivalence for any row.'],
  'allowed_capability_ids': ['PR1F_MIGRATION_CLAIM_TRUTHFULNESS']},
 {'verification_id': 'E_ROUTE_AND_LANE_BEHAVIOR',
  'kind': 'UNIT_TEST',
  'claim_strength': 'BEHAVIOR_FAILURE',
  'covered_target_rule_ids': ['JF_DL_BRAIN_FIRST_RULE', 'JF_DL_DOMAIN_LANE_CLASSIFICATION_RULE', 'JF_DL_RISK_ROUTE_SELECTION_RULE', 'JF_DL_INV_ROUTE_PROFILE_MATCH'],
  'concrete_refs': ['tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_all_routes_have_legal_initial_capsule',
                    'tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_mutating_route_requires_brain_confirmed_final_boundary'],
  'coverage_statement': 'Route profiles form legal Capsules and mutating routes block without a Brain-confirmed boundary.',
  'limitations': ['Brain semantic classification remains judgment, not mechanical proof.'],
  'allowed_capability_ids': []},
 {'verification_id': 'E_DISCOVERY_BOUNDARY_BEHAVIOR',
  'kind': 'UNIT_TEST',
  'claim_strength': 'BEHAVIOR_ADVERSARIAL',
  'covered_target_rule_ids': ['JF_DL_GITHUB_FIRST_PATH_DISCOVERY_RULE',
                              'JF_DL_CODEX_SUPPLEMENTAL_LOCAL_DISCOVERY_RULE',
                              'JF_DL_BRAIN_FINAL_PATH_BOUNDARY_RULE',
                              'JF_DL_READ_ONLY_DISCOVERY_RULE',
                              'JF_DL_PATH_DISCOVERY_RETURN_RULE',
                              'JF_DL_REPOSITORY_EVIDENCE_REFERENCE_RULE'],
  'concrete_refs': ['tests/test_phase1_path_discovery_closure.py::PathClosure::test_non_repository_evidence_cannot_confirm_github_path',
                    'tests/test_phase1_path_discovery_closure.py::PathClosure::test_completed_local_discovery_requires_exact_binding',
                    'tests/test_phase1_source_replay_grounding.py::SourceReplayGrounding::test_fabricated_local_path_blocks_by_source_replay'],
  'coverage_statement': 'Discovery requires typed current sources, exact binding and Brain-owned final paths; fabricated facts block.',
  'limitations': ['Real task repository availability remains current evidence.'],
  'allowed_capability_ids': ['PR1A_TO_PR1E_SELECTED_RULE_COVERAGE']},
 {'verification_id': 'E_APPROVAL_BINDING_BEHAVIOR',
  'kind': 'UNIT_TEST',
  'claim_strength': 'BEHAVIOR_FAILURE',
  'covered_target_rule_ids': ['JF_DL_DETERMINISTIC_APPROVAL_VIEW_RULE', 'JF_DL_INV_APPROVAL_OWNERSHIP_BINDING'],
  'concrete_refs': ['tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_approval_binding_change_blocks',
                    'tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_codex_cannot_own_approval'],
  'coverage_statement': 'Approval view changes invalidate binding and Codex cannot own approval.',
  'limitations': ['Does not authenticate the human identity.'],
  'allowed_capability_ids': []},
 {'verification_id': 'E_PROMPT_COMPILER_BEHAVIOR',
  'kind': 'UNIT_TEST',
  'claim_strength': 'BEHAVIOR_FAILURE',
  'covered_target_rule_ids': ['JF_DL_HIGH_FIDELITY_COMPILER_RULE', 'JF_DL_PROMPT_ROUND_TRIP_RULE'],
  'concrete_refs': ['tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_brain_recorded_exact_approval_compiles',
                    'tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_project_source_change_invalidates_prompt'],
  'coverage_statement': 'Exact approved state compiles and a source change invalidates the prior Prompt.',
  'limitations': ['Does not prove an optimal technical route.'],
  'allowed_capability_ids': []},
 {'verification_id': 'E_SEMANTIC_VALIDATION_BEHAVIOR',
  'kind': 'UNIT_TEST',
  'claim_strength': 'BEHAVIOR_FAILURE',
  'covered_target_rule_ids': ['JF_DL_SEMANTIC_EFFECT_TRANSPORT_RULE',
                              'JF_DL_INV_SEMANTIC_EFFECT_TRANSPORT',
                              'JF_DL_INV_VALIDATION_OBLIGATIONS',
                              'JF_DL_VALIDATION_CLOSURE_RULE',
                              'JF_DL_MECHANICAL_WALKTHROUGH_RULE'],
  'concrete_refs': ['tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_completed_cannot_contain_failed_check',
                    'tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_completed_cannot_contain_unresolved_items',
                    'tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_generated_assets_match_model'],
  'coverage_statement': 'Represented semantic effects produce machine obligations and completion blocks on failed or unresolved checks.',
  'limitations': ['Unrepresented semantics remain Brain responsibility.'],
  'allowed_capability_ids': []},
 {'verification_id': 'E_EVIDENCE_BINDING_BEHAVIOR',
  'kind': 'UNIT_TEST',
  'claim_strength': 'BEHAVIOR_ADVERSARIAL',
  'covered_target_rule_ids': ['JF_DL_EVIDENCE_REGISTRY_RULE', 'JF_DL_REPOSITORY_EVIDENCE_REFERENCE_RULE'],
  'concrete_refs': ['tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_machine_evidence_binds_obligation_and_check',
                    'tests/test_phase1_codex_technical_authority.py::CodexTechnicalAuthority::test_codex_self_authored_direct_evidence_is_rejected',
                    'tests/test_phase1_evidence_content_binding.py::EvidenceContentBinding::test_dependency_cannot_use_path_evidence'],
  'coverage_statement': 'Evidence binds exact obligations, subjects and compatible claim content; self-authored or wrong-kind evidence blocks.',
  'limitations': ['No immutable evidence service is created.'],
  'allowed_capability_ids': []},
 {'verification_id': 'E_REPAIR_BEHAVIOR',
  'kind': 'UNIT_TEST',
  'claim_strength': 'BEHAVIOR_FAILURE',
  'covered_target_rule_ids': ['JF_DL_INV_REPAIR_COMPATIBILITY', 'JF_DL_REPAIR_EXTENSION_RULE', 'JF_DL_REPAIR_CIRCUIT_BREAKER_RULE', 'JF_DL_PROTOCOL_REPAIR_WORKFLOW_RULE'],
  'concrete_refs': ['tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_parent_checked_only_when_new_revision_sealed',
                    'tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_blocked_requires_unresolved_item',
                    'tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_project_source_change_invalidates_prompt'],
  'coverage_statement': 'Repair lineage and changed sources invalidate stale derived objects; blocked execution retains blockers.',
  'limitations': ['Does not establish a persistent repair-history database.'],
  'allowed_capability_ids': []},
 {'verification_id': 'E_MERGE_AUTHORITY_BEHAVIOR',
  'kind': 'UNIT_TEST',
  'claim_strength': 'BEHAVIOR_ADVERSARIAL',
  'covered_target_rule_ids': ['JF_DL_EXECUTION_REVIEW_RULE', 'JF_DL_MERGE_PROMOTION_RULE', 'JF_DL_PROJECTION_PROMOTION_SEPARATION_RULE', 'JF_DL_PR_CANDIDATE_ONLY_RULE'],
  'concrete_refs': ['tests/test_phase1_ai_native_change_projection.py::AINativeChangeProjectionTests::test_navigation_projection_cannot_become_fact_authority',
                    'tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_automatic_promotion_is_blocked',
                    'tests/test_phase1_review_acceptance_freeze.py::ReviewAcceptanceFreezeTests::test_post_freeze_acceptance_binds_exact_freeze'],
  'coverage_statement': 'Projection cannot become fact authority; automatic Promotion and acceptance substitution block.',
  'limitations': ['Final merge remains an external user decision and repository fact.'],
  'allowed_capability_ids': ['PR1A_TO_PR1E_SELECTED_RULE_COVERAGE']},
 {'verification_id': 'E_CURRENT_PR_BEHAVIOR',
  'kind': 'UNIT_TEST',
  'claim_strength': 'BEHAVIOR_ADVERSARIAL',
  'covered_target_rule_ids': ['JF_DL_PR_CANDIDATE_ONLY_RULE', 'JF_DL_EXECUTION_REVIEW_RULE'],
  'concrete_refs': ['tests/test_phase1_pr_body_ci_current_source.py::PRBodyCurrentSourceTests::test_non_ancestor_base_blocks',
                    'tests/test_phase1_pr_body_ci_current_source.py::PRBodyCurrentSourceTests::test_diff_mismatch_blocks_even_when_record_resealed'],
  'coverage_statement': 'Current PR Base ancestry and exact Diff mismatches block even when records are resealed.',
  'limitations': ['CI remains mechanical, not product-semantic authority.'],
  'allowed_capability_ids': ['PR1A_TO_PR1E_SELECTED_RULE_COVERAGE']},
 {'verification_id': 'E_SOURCE_TRUTH_BEHAVIOR',
  'kind': 'UNIT_TEST',
  'claim_strength': 'BEHAVIOR_ADVERSARIAL',
  'covered_target_rule_ids': ['JF_DL_REPOSITORY_CANONICAL_TRUTH_RULE', 'JF_DL_SOURCE_TRUTH_BOUNDARY_RULE'],
  'concrete_refs': ['tests/test_phase1_source_replay_grounding.py::SourceReplayGrounding::test_fabricated_repository_head_capture_blocks',
                    'tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_project_source_change_invalidates_prompt'],
  'coverage_statement': 'Fabricated repository facts block and active source changes invalidate derived prompts.',
  'limitations': ['Does not prove external repository availability.'],
  'allowed_capability_ids': ['PR1A_TO_PR1E_SELECTED_RULE_COVERAGE']},
 {'verification_id': 'E_TASK_LIFECYCLE_BEHAVIOR',
  'kind': 'UNIT_TEST',
  'claim_strength': 'BEHAVIOR_FAILURE',
  'covered_target_rule_ids': ['JF_DL_DUAL_LAYER_CLOSURE_RULE', 'JF_DL_TASK_CAPSULE_TEMPORARY_RULE', 'JF_DL_STAGE_FIBER_CYCLE_SEPARATION_RULE', 'JF_DL_NARROW_SPIRAL_RULE', 'JF_DL_OPTIONAL_FIBER_RULE'],
  'concrete_refs': ['tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_initial_capsule_cannot_start_late',
                    'tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_repository_task_cannot_close_inside_capsule',
                    'tests/test_phase1_task_object_lifecycle.py::TaskObjectLifecycleTests::test_projection_carries_typed_route_lifecycle'],
  'coverage_statement': 'Task Capsule stage and result lifecycle are typed and invalid transitions block.',
  'limitations': ['No persistent task scheduler or independent memory is introduced.'],
  'allowed_capability_ids': []},
 {'verification_id': 'E_GENERATED_ASSET_BEHAVIOR',
  'kind': 'UNIT_TEST',
  'claim_strength': 'BEHAVIOR_FAILURE',
  'covered_target_rule_ids': ['JF_DL_GENERATED_ASSET_BOUNDARY_RULE'],
  'concrete_refs': ['tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_generated_assets_match_model'],
  'coverage_statement': 'Generated mechanical assets must match the current machine model.',
  'limitations': ['Generation consistency does not prove all semantics.'],
  'allowed_capability_ids': []},
 {'verification_id': 'E_CODEX_TECHNICAL_BEHAVIOR',
  'kind': 'UNIT_TEST',
  'claim_strength': 'BEHAVIOR_ADVERSARIAL',
  'covered_target_rule_ids': ['JF_DL_AI_COMPATIBLE_STRUCTURE_RULE', 'JF_DL_CODEX_RUNTIME_TRANSPARENT_RULE'],
  'concrete_refs': ['tests/test_phase1_codex_technical_authority.py::CodexTechnicalAuthority::test_codex_cannot_select_user_owned_candidate_tradeoff',
                    'tests/test_phase1_codex_technical_authority.py::CodexTechnicalAuthority::test_material_codex_alternative_must_stop',
                    'tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_runtime_cli_has_no_automatic_promotion_command'],
  'coverage_statement': 'Codex technical alternatives remain bounded and runtime exposes no automatic Promotion command.',
  'limitations': ['Does not make Codex a product or approval authority.'],
  'allowed_capability_ids': []},
 {'verification_id': 'E_ARTIFACT_REPOSITORY_SPLIT_BEHAVIOR',
  'kind': 'UNIT_TEST',
  'claim_strength': 'BEHAVIOR_FAILURE',
  'covered_target_rule_ids': ['JF_DL_REPO_ARTIFACT_PLACEMENT_RULE'],
  'concrete_refs': ['tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_repository_review_rejects_artifact_target',
                    'tests/test_phase1_discovery_artifact_lifecycle_completion.py::DiscoveryArtifactLifecycleCompletionTests::test_artifact_complete_output_set_rejects_missing_or_extra_output'],
  'coverage_statement': 'Repository and Artifact routes use distinct review objects and incomplete Artifact outputs block.',
  'limitations': ['Repository file-layout aesthetics are not proven.'],
  'allowed_capability_ids': []},
 {'verification_id': 'E_LEGACY_SOURCE_IDENTITY',
  'kind': 'POLICY',
  'claim_strength': 'LEGACY_SOURCE_IDENTITY',
  'covered_target_rule_ids': [],
  'concrete_refs': ['machine/legacy_source_set_v1_7_6.json'],
  'coverage_statement': 'Legacy source filenames bind to an exact historical source-set digest and per-file SHA-256.',
  'limitations': ['Source bytes are not bundled.'],
  'allowed_capability_ids': []},
 {'verification_id': 'E_BRAIN_SEMANTIC_MAPPING_BINDING',
  'kind': 'POLICY',
  'claim_strength': 'BRAIN_SEMANTIC_MAPPING',
  'covered_target_rule_ids': [],
  'concrete_refs': ['machine/brain_legacy_semantic_mapping_v1_7_6.json', 'machine/brain_legacy_semantic_mapping_seal.json'],
  'coverage_statement': 'A WEB_BRAIN mapping object is sealed separately from generation.',
  'limitations': ['Mappings remain unconfirmed while exact section text is unavailable.'],
  'allowed_capability_ids': []},
 {'verification_id': 'E_DISPOSITION_DECISION_BINDING',
  'kind': 'POLICY',
  'claim_strength': 'DISPOSITION_DECISION',
  'covered_target_rule_ids': [],
  'concrete_refs': ['machine/legacy_disposition_decisions_v1_7_6.json', 'machine/legacy_disposition_decisions_seal.json'],
  'coverage_statement': 'Each migration row consumes a separately sealed Web-Brain disposition decision; the generator cannot author it.',
  'limitations': ['Current candidate decisions are all NOT_EVALUATED and do not close legacy semantics.'],
  'allowed_capability_ids': []}]
_pr1f_registry=next(row for row in REGISTRY if row["verification_id"]=="E_MIGRATION_TRUTHFULNESS_ADVERSARIAL")
_pr1f_registry["covered_target_rule_ids"].extend([
    "RULE_CURRENT_MIGRATION_INSTANCE_TRANSITION_CAPABILITY_SEPARATION",
    "RULE_EXACT_LEGACY_SOURCE_REPLAY_FIXTURE_BOUNDARY",
    "RULE_DISPOSITION_EVIDENCE_OUTCOME_CONTRACT_COMPLETE",
    "RULE_PUBLIC_TRANSITION_PATH_POSITIVE_COVERAGE",
    "RULE_MAPPING_SOURCE_SET_SINGLE_OWNER",
    "RULE_SEMANTIC_EVIDENCE_EXACT_OBJECT_BINDING",
    "RULE_SEMANTIC_EVIDENCE_MECHANICAL_SEMANTIC_BOUNDARY",
    "RULE_DEFERRED_STATUS_BASIS_TRUTHFULNESS",
    "RULE_CONFIRMED_TRANSITION_VALIDATED_BOUNDARY",
    "RULE_CONFIRMED_TRANSITION_SEAL_CONSUMPTION",
    "RULE_PACKAGE_RELATIVE_EXACT_SOURCE_BINDING",
    "RULE_ORDERED_SECTION_BOUNDARY",
    "RULE_DERIVED_MAPPING_STATUS",
    "RULE_CAPABILITY_CLAIM_TYPE_SEPARATION",
    "RULE_INHERITED_STAGE_PRESENCE_SCOPE",
    "RULE_VERIFIED_RULE_COVERAGE_EXACT",
    "RULE_VERIFIED_CROSS_STAGE_CHAIN_SCOPE",
    "RULE_CAPABILITY_COVERAGE_RELATION_BINDING",
])
_pr1f_registry["concrete_refs"].extend([
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_current_instance_and_transition_fixture_lifecycles_are_separate",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_exact_transition_fixture_uses_public_generation_path",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_exact_transition_fixture_tampered_source_bytes_block",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_exact_transition_fixture_wrong_section_digest_blocks",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_confirmed_mapping_without_source_root_blocks",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_carry_forward_public_path_uses_contract_for_complete_and_incomplete_behavior",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_mapping_rows_cannot_independently_own_source_set_identity",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_migration_row_derives_source_set_identity_from_top_level",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_semantic_evidence_wrong_section_id_blocks",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_semantic_evidence_file_digest_mismatch_blocks",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_semantic_evidence_section_digest_mismatch_blocks",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_product_defer_uses_neutral_exact_decision_status",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_confirmed_transition_public_path_consumes_both_seals",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_unsealed_mapping_mutation_blocks_formal_boundary",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_unsealed_disposition_mutation_blocks_formal_boundary",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_package_relative_source_root_escape_blocks",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_reversed_exact_section_markers_block",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_reversed_evidence_section_markers_block",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_mapping_status_must_be_derived_from_rows",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_inherited_stage_presence_is_not_behavioral_verification",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_verified_rule_coverage_matches_exact_evidence_union",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_cross_stage_chain_matches_exact_stage_and_rule_scope",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_five_stage_zero_rule_behavior_claim_blocks",
    "tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_cross_stage_chain_does_not_imply_full_stage_coverage",
])
_pr1f_registry["coverage_statement"]="Adversarial and positive public-path cases bind current-instance truthfulness separately from reusable confirmed-semantic transition capability, prove every evidence-conditioned outcome from the shared contract, and bind source-set and semantic-evidence provenance to exact objects, and prove one formal sealed confirmed-transition boundary without moving semantic judgment out of Web Brain; combined capability claims also separate inherited stage presence, exact rule coverage and one verified cross-stage chain."
_pr1f_registry["limitations"]=["Fixture evidence proves the transition mechanism only and does not establish legacy semantic equivalence for any of the 176 current rows."]

# Phase 1 combined-coverage claim evidence. Presence, exact rule coverage and
# one verified public chain remain separate facts.
_PHASE1A_TO_PR1E_STAGES=[
    "PR1A_PATH_DISCOVERY",
    "PR1B_SEALED_OBJECT_EXECUTION_AND_REVIEW",
    "PR1C_CURRENT_OBJECT_PR_BODY_CI",
    "PR1D_REVIEW_ACCEPTANCE_FREEZE",
    "PR1E_AI_NATIVE_CHANGE_PROJECTION",
]
_PR1B_TO_PR1E_PUBLIC_CHAIN_STAGES=[
    "PR1B_SEALED_OBJECT_EXECUTION_AND_REVIEW",
    "PR1C_CURRENT_OBJECT_PR_BODY_CI",
    "PR1D_REVIEW_ACCEPTANCE_FREEZE",
    "PR1E_AI_NATIVE_CHANGE_PROJECTION",
]
_PR1B_TO_PR1E_PUBLIC_CHAIN_RULES=[
    "PR_CURRENT_REPOSITORY_OBJECT_RULE",
    "PR_SEALED_SOURCE_CHAIN_RULE",
    "JF_PHASE1E_CURRENT_SOURCE_PROJECTION",
    "JF_PHASE1E_PR_CI_EXACT_CONSUMPTION",
    "JF_PHASE1E_FREEZE_EXACT_PROJECTION",
    "JF_PHASE1E_USER_MERGE_AUTHORIZATION",
    "JF_PHASE1E_COMPLETION_EXACT_CHAIN",
]
REGISTRY.extend([
    {
      "verification_id":"E_PHASE1A_TO_PR1E_STAGE_PRESENCE",
      "kind":"POLICY",
      "claim_strength":"STRUCTURAL_PRESENCE",
      "covered_stage_ids":_PHASE1A_TO_PR1E_STAGES,
      "covered_target_rule_ids":[],
      "concrete_refs":["PHASE1_STAGE_LINEAGE.json","PACKAGE_MANIFEST.json"],
      "coverage_statement":"The exact current package identity and lineage record contain the inherited PR1A through PR1E stage materials.",
      "limitations":["Stage presence does not prove every rule or path in a stage has been behaviorally verified."],
      "allowed_capability_ids":["PR1A_TO_PR1E_INHERITED_STAGE_PRESENCE"],
    },
    {
      "verification_id":"E_PR1B_TO_PR1E_PUBLIC_CHAIN",
      "kind":"UNIT_TEST",
      "claim_strength":"BEHAVIOR_ADVERSARIAL",
      "covered_stage_ids":_PR1B_TO_PR1E_PUBLIC_CHAIN_STAGES,
      "covered_target_rule_ids":_PR1B_TO_PR1E_PUBLIC_CHAIN_RULES,
      "concrete_refs":[
        "tests/test_phase1_ai_native_change_projection.py::AINativeChangeProjectionTests::test_public_completion_entry_requires_freeze_acceptance_authorization",
        "tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_merge_allowed_is_derived_from_freeze_acceptance_and_user_authorization",
        "tests/test_phase1_single_active_task_round.py::SingleActiveTaskRoundTests::test_completion_pointer_requires_freeze_acceptance_and_user_authorization_not_gate_snapshots",
      ],
      "coverage_statement":"One exact PR1B through PR1E repository path binds execution evidence, current PR review, exact merge freeze, applicable user acceptance, final user merge authorization and completion pointer; incomplete or mismatched chain inputs block.",
      "limitations":["This proves the declared public chain only and does not prove every rule or branch in each participating stage."],
      "allowed_capability_ids":["PR1A_TO_PR1E_PUBLIC_CHAIN"],
    },
])
PACKAGE_NAME='JOYFLOW_PHASE1_COMBINED_CAPABILITY_COVERAGE_REPAIR_CANDIDATE'
REPAIR_SOURCE={'name': 'JOYFLOW_PHASE1F_CONFIRMED_TRANSITION_BOUNDARY_REPAIR_CANDIDATE.zip', 'bytes': 989316, 'sha256': 'f3f8fe65cfc99715a0e56fbf4cdd2a8157ad9f81e75f14b9c8a021b1ca0f2c29'}
BEHAVIOR_STRENGTHS={"BEHAVIOR_POSITIVE","BEHAVIOR_FAILURE","BEHAVIOR_ADVERSARIAL"}
ALLOWED_STRENGTHS={"STRUCTURAL_PRESENCE","SOURCE_CONSISTENCY","LEGACY_SOURCE_IDENTITY","BRAIN_SEMANTIC_MAPPING","DISPOSITION_DECISION","BEHAVIOR_POSITIVE","BEHAVIOR_FAILURE","BEHAVIOR_ADVERSARIAL","EXPLICIT_DEFERRAL","RETIREMENT_RATIONALE"}
ALLOWED_STATUSES={"MAPPED_ONLY","SEMANTICALLY_PRESERVED_AND_BEHAVIORALLY_VERIFIED","DEFERRED_BY_EXACT_CURRENT_DECISION","RETIRED_BY_CURRENT_USER_DECISION","RETIRED_BY_CONFIRMED_SEMANTIC_SUPERSESSION"}
ALLOWED_DECISIONS={"NOT_EVALUATED","CARRY_FORWARD","DEFER","RETIRE"}

class ValidatedTransitionInputs(NamedTuple):
    inventory: list
    source_set: dict
    mapping: dict
    brain_mapping_seal: dict
    decisions: dict
    disposition_seal: dict
    claims: dict
# Single mechanical source for every legal disposition transition. Schema, semantic
# validation and migration-state derivation consume this exact contract.
def _same_outcome(status, equivalence=False):
    return {(semantic,behavior):{"migration_status":status,"behavioral_equivalence_claimed":equivalence}
            for semantic in ("UNCONFIRMED","CONFIRMED") for behavior in ("INCOMPLETE","COMPLETE")}

# One mechanical source for legal authority transitions and every evidence-conditioned
# migration outcome. Schema, validators, derivation and positive tests consume this table.
DISPOSITION_TRANSITION_CONTRACT={
    ("NOT_EVALUATED","EXACT_LEGACY_SEMANTICS_UNAVAILABLE"):{"owner":"WEB_BRAIN","effects":{"UNRESOLVED_MATERIAL_EFFECT"},"product_values":{"UNKNOWN"},"tradeoff_values":{"UNKNOWN"},"user_ref":"FORBIDDEN","semantic_gate":"MUST_BE_UNCONFIRMED","outcomes":{("UNCONFIRMED",b):{"migration_status":"MAPPED_ONLY","behavioral_equivalence_claimed":False} for b in ("INCOMPLETE","COMPLETE")}},
    ("DEFER","CURRENT_PHASE_SCOPE"):{"owner":"WEB_BRAIN","effects":{"NONE","PRESERVES_CONFIRMED_DIRECTION"},"product_values":{"NO"},"tradeoff_values":{"NO"},"user_ref":"FORBIDDEN","semantic_gate":"ANY","outcomes":_same_outcome("DEFERRED_BY_EXACT_CURRENT_DECISION")},
    ("DEFER","CURRENT_PRODUCT_DECISION"):{"owner":"USER","effects":{"PRESERVES_CONFIRMED_DIRECTION","CHANGES_CONFIRMED_DIRECTION"},"product_values":None,"tradeoff_values":None,"user_ref":"REQUIRED","semantic_gate":"ANY","outcomes":_same_outcome("DEFERRED_BY_EXACT_CURRENT_DECISION")},
    ("RETIRE","CURRENT_PRODUCT_DECISION"):{"owner":"USER","effects":{"PRESERVES_CONFIRMED_DIRECTION","CHANGES_CONFIRMED_DIRECTION"},"product_values":None,"tradeoff_values":None,"user_ref":"REQUIRED","semantic_gate":"ANY","outcomes":_same_outcome("RETIRED_BY_CURRENT_USER_DECISION")},
    ("RETIRE","LEGACY_SEMANTIC_ANALYSIS"):{"owner":"WEB_BRAIN","effects":{"NONE","PRESERVES_CONFIRMED_DIRECTION"},"product_values":{"NO"},"tradeoff_values":{"NO"},"user_ref":"FORBIDDEN","semantic_gate":"MUST_BE_CONFIRMED","outcomes":{("CONFIRMED",b):{"migration_status":"RETIRED_BY_CONFIRMED_SEMANTIC_SUPERSESSION","behavioral_equivalence_claimed":False} for b in ("INCOMPLETE","COMPLETE")}},
    ("RETIRE","TECHNICAL_DUPLICATION_ANALYSIS"):{"owner":"WEB_BRAIN","effects":{"NONE","PRESERVES_CONFIRMED_DIRECTION"},"product_values":{"NO"},"tradeoff_values":{"NO"},"user_ref":"FORBIDDEN","semantic_gate":"MUST_BE_CONFIRMED","outcomes":{("CONFIRMED",b):{"migration_status":"RETIRED_BY_CONFIRMED_SEMANTIC_SUPERSESSION","behavioral_equivalence_claimed":False} for b in ("INCOMPLETE","COMPLETE")}},
    ("CARRY_FORWARD","LEGACY_SEMANTIC_ANALYSIS"):{"owner":"WEB_BRAIN","effects":{"NONE","PRESERVES_CONFIRMED_DIRECTION"},"product_values":{"NO"},"tradeoff_values":{"NO"},"user_ref":"FORBIDDEN","semantic_gate":"OPEN_UNTIL_CONFIRMED","outcomes":{("UNCONFIRMED","INCOMPLETE"):{"migration_status":"MAPPED_ONLY","behavioral_equivalence_claimed":False},("UNCONFIRMED","COMPLETE"):{"migration_status":"MAPPED_ONLY","behavioral_equivalence_claimed":False},("CONFIRMED","INCOMPLETE"):{"migration_status":"MAPPED_ONLY","behavioral_equivalence_claimed":False},("CONFIRMED","COMPLETE"):{"migration_status":"SEMANTICALLY_PRESERVED_AND_BEHAVIORALLY_VERIFIED","behavioral_equivalence_claimed":True}}},
    ("CARRY_FORWARD","CURRENT_PRODUCT_DECISION"):{"owner":"USER","effects":{"PRESERVES_CONFIRMED_DIRECTION","CHANGES_CONFIRMED_DIRECTION"},"product_values":None,"tradeoff_values":None,"user_ref":"REQUIRED","semantic_gate":"OPEN_UNTIL_CONFIRMED","outcomes":{("UNCONFIRMED","INCOMPLETE"):{"migration_status":"MAPPED_ONLY","behavioral_equivalence_claimed":False},("UNCONFIRMED","COMPLETE"):{"migration_status":"MAPPED_ONLY","behavioral_equivalence_claimed":False},("CONFIRMED","INCOMPLETE"):{"migration_status":"MAPPED_ONLY","behavioral_equivalence_claimed":False},("CONFIRMED","COMPLETE"):{"migration_status":"SEMANTICALLY_PRESERVED_AND_BEHAVIORALLY_VERIFIED","behavioral_equivalence_claimed":True}}},
}
CAPABILITY_IDS={"PR1A_TO_PR1E_INHERITED_STAGE_PRESENCE","PR1A_TO_PR1E_SELECTED_RULE_COVERAGE","PR1A_TO_PR1E_PUBLIC_CHAIN","PR1F_MIGRATION_CLAIM_TRUTHFULNESS"}
TARGET_TO_BEHAVIOR={}
for _row in REGISTRY:
    if _row["claim_strength"] in BEHAVIOR_STRENGTHS:
        for _target in _row["covered_target_rule_ids"]:
            TARGET_TO_BEHAVIOR.setdefault(_target,[]).append(_row["verification_id"])

def _digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()
def _load_json(path): return json.loads(read_canonical_text(path))
def _verify_embedded_digest(obj,field):
    expected=obj.get(field); body=dict(obj); body.pop(field,None)
    if expected!=_digest(body): raise ValueError(f"{field} mismatch")
    return expected

def _unit_ref_exists(ref:str)->bool:
    import ast
    parts=ref.split("::")
    if len(parts)!=3:return False
    path=ROOT/parts[0]
    if not path.is_file():return False
    try: tree=ast.parse(read_canonical_text(path))
    except SyntaxError:return False
    for node in tree.body:
        if isinstance(node,ast.ClassDef) and node.name==parts[1]:
            return any(isinstance(fn,(ast.FunctionDef,ast.AsyncFunctionDef)) and fn.name==parts[2] for fn in node.body)
    return False
def _command_ref_exists(ref:str)->bool:
    import shlex
    try: argv=shlex.split(ref)
    except ValueError:return False
    return len(argv)>=2 and argv[0] in {"python","python3"} and (ROOT/argv[1]).is_file()
def _policy_ref_exists(ref:str)->bool: return (ROOT/ref).is_file()

def verification_contract_digest(row):
    return _digest({"verification_id":row["verification_id"],"claim_strength":row["claim_strength"],"covered_stage_ids":row.get("covered_stage_ids",[]),"covered_target_rule_ids":row["covered_target_rule_ids"],"concrete_refs":row["concrete_refs"],"allowed_capability_ids":row["allowed_capability_ids"]})

def validate_verification_registry(registry):
    if not isinstance(registry,list) or not registry: raise ValueError("verification registry must be a non-empty list")
    ids=[r.get("verification_id") for r in registry]
    if None in ids or len(ids)!=len(set(ids)): raise ValueError("verification IDs missing or duplicated")
    for row in registry:
        if row.get("claim_strength") not in ALLOWED_STRENGTHS: raise ValueError("invalid verification claim strength")
        if row.get("kind") not in {"UNIT_TEST","COMMAND","POLICY"}: raise ValueError("invalid verification kind")
        refs=row.get("concrete_refs")
        if not isinstance(refs,list) or not refs: raise ValueError("verification requires concrete refs")
        for ref in refs:
            ok=_unit_ref_exists(ref) if row["kind"]=="UNIT_TEST" else _command_ref_exists(ref) if row["kind"]=="COMMAND" else _policy_ref_exists(ref)
            if not ok: raise ValueError(f"unresolved concrete verification ref: {ref}")
        if not isinstance(row.get("covered_target_rule_ids"),list): raise ValueError("covered target list missing")
        if not isinstance(row.get("covered_stage_ids",[]),list): raise ValueError("covered stage list invalid")
        allowed=row.get("allowed_capability_ids")
        if not isinstance(allowed,list) or not set(allowed)<=CAPABILITY_IDS: raise ValueError("allowed capability subjects invalid")
        if not row.get("coverage_statement") or not isinstance(row.get("limitations"),list): raise ValueError("verification scope missing")
    return True

def current_rule_ids():
    ids=set()
    for p in (ROOT/"project_sources").glob("*.md"):
        ids.update(re.findall(r"^canonical_rule_id:\s*([A-Z0-9_]+)",read_canonical_text(p),re.M))
    return ids

def _extract_ordered_section(text,section_id,start_prefix,end_prefix,label):
    start_marker=f"{start_prefix}{section_id} -->"
    end_marker=f"{end_prefix}{section_id} -->"
    if text.count(start_marker)!=1 or text.count(end_marker)!=1:
        raise ValueError(f"{label} section markers missing or duplicated")
    start=text.find(start_marker); end=text.find(end_marker)
    content_start=start+len(start_marker)
    if start<0 or end<0 or content_start>=end:
        raise ValueError(f"{label} section markers reversed or section empty")
    section=text[content_start:end].strip("\n")+"\n"
    if not section.strip():
        raise ValueError(f"{label} section is empty")
    return section

def _extract_exact_section(text,section_id):
    return _extract_ordered_section(text,section_id,"<!-- JOYFLOW_SECTION:","<!-- /JOYFLOW_SECTION:","exact legacy")

def _extract_evidence_section(text,section_id):
    return _extract_ordered_section(text,section_id,"<!-- JOYFLOW_EVIDENCE_SECTION:","<!-- /JOYFLOW_EVIDENCE_SECTION:","Brain semantic evidence")

def _resolve_declared_source_root(source_set):
    declared=source_set.get("package_relative_source_root")
    if source_set.get("source_bytes_bundled") is True:
        if not isinstance(declared,str) or not declared.strip():
            raise ValueError("bundled exact source requires package-relative source root")
        package_root=ROOT.resolve(); candidate=(ROOT/declared).resolve()
        if candidate==package_root or package_root not in candidate.parents:
            raise ValueError("package-relative exact source root escapes package")
        if not candidate.is_dir():
            raise ValueError("package-relative exact source root does not resolve")
        return candidate
    if declared is not None:
        raise ValueError("unbundled source set cannot declare package-relative source root")
    return None

def _derived_mapping_status(mappings):
    statuses={row.get("brain_mapping_status") for row in mappings}
    if statuses=={"NOT_CONFIRMED_EXACT_SOURCE_TEXT_UNAVAILABLE"}: return "NOT_CONFIRMED_EXACT_SOURCE_TEXT_UNAVAILABLE"
    if statuses=={"CONFIRMED"}: return "CONFIRMED"
    if "BLOCKED" in statuses: return "BLOCKED"
    return "PARTIALLY_CONFIRMED"

def _resolve_package_relative_path(value):
    if not isinstance(value,str) or not value.strip():
        raise ValueError("Brain semantic evidence path missing")
    candidate=(ROOT/value).resolve(); package_root=ROOT.resolve()
    if candidate==package_root or package_root not in candidate.parents:
        raise ValueError("Brain semantic evidence path escapes package")
    return candidate

def _validate_semantic_evidence_ref(ref):
    if not isinstance(ref,dict):
        raise ValueError("confirmed mapping requires structured Brain semantic evidence ref")
    if set(ref)!={"path","section_id","file_sha256","section_sha256"}:
        raise ValueError("Brain semantic evidence ref fields mismatch")
    path=_resolve_package_relative_path(ref.get("path"))
    if not path.is_file():
        raise ValueError("Brain semantic evidence file does not resolve")
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ref.get("file_sha256"):
        raise ValueError("Brain semantic evidence file digest mismatch")
    section_id=ref.get("section_id")
    if not isinstance(section_id,str) or not section_id.strip():
        raise ValueError("Brain semantic evidence section ID missing")
    section=_extract_evidence_section(raw.decode("utf-8"),section_id)
    if hashlib.sha256(section.encode()).hexdigest()!=ref.get("section_sha256"):
        raise ValueError("Brain semantic evidence section digest mismatch")
    return True

def validate_brain_mapping(inventory,source_set,mapping,expected_count=176):
    if not isinstance(inventory,list) or len(inventory)!=expected_count: raise ValueError("legacy inventory row count mismatch")
    inv={r["old_rule_id"]:r for r in inventory}; sources={r["path"]:r for r in source_set.get("sources",[])}; maps=mapping.get("mappings")
    if mapping.get("source_set_id")!=source_set.get("source_set_id") or mapping.get("source_set_digest")!=source_set.get("source_set_digest"):
        raise ValueError("Brain mapping top-level source-set binding mismatch")
    if len(inv)!=expected_count or not isinstance(maps,list) or len(maps)!=expected_count or {r.get("old_rule_id") for r in maps}!=set(inv): raise ValueError("Brain mapping ID set mismatch")
    forbidden={"legacy_migration_status","disposition","decision","user_decision_ref"}
    current=current_rule_ids(); source_root=_resolve_declared_source_root(source_set)
    if mapping.get("mapping_status")!=_derived_mapping_status(maps): raise ValueError("Brain mapping top-level status is not derived from row states")
    for row in maps:
        old=inv[row["old_rule_id"]]; src=sources.get(row.get("old_source")); text=row.get("brain_capability_interpretation")
        if forbidden & set(row): raise ValueError("semantic mapping contains disposition authority")
        if "legacy_source_set_id" in row: raise ValueError("mapping row cannot independently own source-set identity")
        if row.get("owner")!="WEB_BRAIN" or row.get("mapping_id")!="BLSM::"+row["old_rule_id"]: raise ValueError("Brain mapping owner or ID mismatch")
        if row.get("old_source")!=old["old_source"] or row.get("old_section")!=old["old_section"]: raise ValueError("Brain mapping source/section mismatch")
        if not src or row.get("legacy_source_sha256")!=src.get("sha256"): raise ValueError("Brain mapping source SHA mismatch")
        if not isinstance(text,str) or hashlib.sha256(text.encode()).hexdigest()!=row.get("brain_capability_interpretation_digest"): raise ValueError("Brain interpretation digest mismatch")
        state=row.get("source_binding_status")
        if state=="DIGEST_AND_SECTION_ID_BOUND_TEXT_NOT_BUNDLED":
            if source_set.get("source_bytes_bundled") is not False or row.get("exact_source_text_in_package") is not False: raise ValueError("unavailable source binding state inconsistent")
            if row.get("exact_source_section_sha256") is not None or row.get("semantic_evidence_ref") is not None: raise ValueError("unavailable mapping cannot claim exact semantic evidence")
            if row.get("brain_mapping_status")!="NOT_CONFIRMED_EXACT_SOURCE_TEXT_UNAVAILABLE" or row.get("semantic_relation")!="MAPPING_CANDIDATE_NOT_SEMANTICALLY_CONFIRMED": raise ValueError("unavailable semantics cannot be confirmed")
        elif state=="EXACT_SOURCE_TEXT_VERIFIED":
            if source_set.get("source_bytes_bundled") is not True or row.get("exact_source_text_in_package") is not True: raise ValueError("confirmed mapping requires bundled exact source bytes")
            if source_root is None: raise ValueError("confirmed mapping requires a package-relative exact source root")
            path=source_root/row["old_source"]
            if not path.is_file(): raise ValueError("confirmed legacy source file missing")
            raw=path.read_bytes()
            if len(raw)!=src.get("bytes") or hashlib.sha256(raw).hexdigest()!=src.get("sha256"): raise ValueError("confirmed legacy source bytes or SHA mismatch")
            section=_extract_exact_section(raw.decode("utf-8"),row["old_section"])
            if hashlib.sha256(section.encode()).hexdigest()!=row.get("exact_source_section_sha256"): raise ValueError("confirmed legacy section digest mismatch")
            evidence=row.get("semantic_evidence_ref")
            _validate_semantic_evidence_ref(evidence)
            if row.get("brain_mapping_status")!="CONFIRMED" or row.get("semantic_relation")!="FULLY_PRESERVED": raise ValueError("confirmed exact source requires confirmed fully-preserved mapping")
            if not set(row.get("target_rule_ids",[]))<=current: raise ValueError("confirmed mapping target rule does not exist")
        else:
            raise ValueError("unsupported source binding state")
    return True

def _mapping_semantic_gate(mapping_row,current_rules=None):
    return (mapping_row.get("source_binding_status")=="EXACT_SOURCE_TEXT_VERIFIED"
            and mapping_row.get("exact_source_text_in_package") is True
            and mapping_row.get("brain_mapping_status")=="CONFIRMED"
            and mapping_row.get("semantic_relation")=="FULLY_PRESERVED"
            and isinstance(mapping_row.get("target_rule_ids"),list)
            and bool(mapping_row.get("target_rule_ids"))
            and (current_rules is None or set(mapping_row.get("target_rule_ids"))<=set(current_rules)))

def _transition_contract(decision):
    key=(decision.get("decision"),decision.get("basis"))
    row=DISPOSITION_TRANSITION_CONTRACT.get(key)
    if row is None:
        raise ValueError(f"unsupported disposition transition: {key[0]} + {key[1]}")
    return row

def validate_transition_contract_definition():
    expected_decisions=ALLOWED_DECISIONS
    if {key[0] for key in DISPOSITION_TRANSITION_CONTRACT} != expected_decisions:
        raise ValueError("transition contract decision coverage mismatch")
    for key,row in DISPOSITION_TRANSITION_CONTRACT.items():
        if row.get("owner") not in {"WEB_BRAIN","USER"} or not row.get("effects"):
            raise ValueError(f"transition contract authority incomplete: {key}")
        if row.get("user_ref") not in {"REQUIRED","FORBIDDEN"}:
            raise ValueError(f"transition contract user-ref rule invalid: {key}")
        if row.get("semantic_gate") not in {"ANY","MUST_BE_CONFIRMED","MUST_BE_UNCONFIRMED","OPEN_UNTIL_CONFIRMED"}:
            raise ValueError(f"transition contract semantic gate invalid: {key}")
        outcomes=row.get("outcomes")
        if not isinstance(outcomes,dict) or not outcomes: raise ValueError(f"transition contract outcomes missing: {key}")
        allowed_semantics={"CONFIRMED"} if row["semantic_gate"]=="MUST_BE_CONFIRMED" else {"UNCONFIRMED"} if row["semantic_gate"]=="MUST_BE_UNCONFIRMED" else {"CONFIRMED","UNCONFIRMED"}
        expected={(semantic,behavior) for semantic in allowed_semantics for behavior in {"COMPLETE","INCOMPLETE"}}
        if set(outcomes)!=expected: raise ValueError(f"transition contract evidence outcome coverage mismatch: {key}")
        for outcome in outcomes.values():
            if outcome.get("migration_status") not in ALLOWED_STATUSES or not isinstance(outcome.get("behavioral_equivalence_claimed"),bool):
                raise ValueError(f"transition contract outcome invalid: {key}")
    return True

def validate_disposition_decisions(mapping,decisions,expected_count=176):
    validate_transition_contract_definition()
    rows=decisions.get("decisions")
    maps={r["old_rule_id"]:r for r in mapping["mappings"]}
    if decisions.get("artifact_type")!="LEGACY_DISPOSITION_DECISION_SET" or decisions.get("decision_set_version")!=2 or decisions.get("owner")!="WEB_BRAIN" or decisions.get("generator_may_modify") is not False: raise ValueError("disposition decision identity invalid")
    if decisions.get("source_mapping_set_id")!=mapping["mapping_set_id"] or decisions.get("source_mapping_set_digest")!=mapping["mapping_set_digest"]: raise ValueError("disposition source mapping mismatch")
    if not isinstance(rows,list) or len(rows)!=expected_count or {r.get("old_rule_id") for r in rows}!=set(maps): raise ValueError("disposition decision set mismatch")
    for row in rows:
        if row.get("decision_id")!="LDD::"+row["old_rule_id"] or row.get("owner") not in {"WEB_BRAIN","USER"} or row.get("decision") not in ALLOWED_DECISIONS: raise ValueError("disposition decision identity invalid")
        contract=_transition_contract(row)
        owner=row.get("owner"); user_ref=row.get("user_decision_ref"); effect=row.get("product_direction_effect")
        product=row.get("affects_product_requirement"); tradeoff=row.get("affects_important_tradeoff")
        if owner!=contract["owner"]: raise ValueError("disposition owner does not match transition contract")
        if effect not in contract["effects"]: raise ValueError("product direction effect does not match transition contract")
        if contract["product_values"] is not None and product not in contract["product_values"]: raise ValueError("product requirement effect does not match transition contract")
        if contract["tradeoff_values"] is not None and tradeoff not in contract["tradeoff_values"]: raise ValueError("important tradeoff effect does not match transition contract")
        if contract["user_ref"]=="REQUIRED" and (not isinstance(user_ref,str) or not user_ref.strip()): raise ValueError("current product decision requires exact user reference")
        if contract["user_ref"]=="FORBIDDEN" and user_ref is not None: raise ValueError("technical disposition cannot contain user row approval")
        if row["decision"]!="NOT_EVALUATED" and not row.get("decision_ref"): raise ValueError("closed disposition requires exact decision ref")
        if contract["semantic_gate"]=="MUST_BE_CONFIRMED" and not _mapping_semantic_gate(maps[row["old_rule_id"]],current_rule_ids()):
            if row.get("basis")=="TECHNICAL_DUPLICATION_ANALYSIS": raise ValueError("technical duplication retirement requires confirmed exact legacy semantics and current replacement targets")
            raise ValueError("semantic supersession retirement requires confirmed exact legacy semantics")
        if contract["semantic_gate"]=="MUST_BE_UNCONFIRMED" and _mapping_semantic_gate(maps[row["old_rule_id"]],current_rule_ids()):
            raise ValueError("not-evaluated disposition cannot consume confirmed legacy semantics")
    return True

def validate_capability_claim_registry(doc,registry):
    if doc.get("artifact_type")!="CAPABILITY_CLAIM_REGISTRY" or doc.get("registry_version")!=3 or doc.get("registry_id")!="JOYFLOW_PHASE1_CAPABILITY_CLAIM_REGISTRY_V3" or doc.get("owner")!="WEB_BRAIN" or doc.get("generator_may_modify") is not False:
        raise ValueError("claim registry identity mismatch")
    expected_ids=[
        "PR1A_TO_PR1E_INHERITED_STAGE_PRESENCE",
        "PR1A_TO_PR1E_SELECTED_RULE_COVERAGE",
        "PR1A_TO_PR1E_PUBLIC_CHAIN",
        "PR1F_MIGRATION_CLAIM_TRUTHFULNESS",
    ]
    ids=[x.get("capability_id") for x in doc.get("claims",[])]
    if ids!=expected_ids: raise ValueError("claim subject set mismatch")
    by={r["verification_id"]:r for r in registry}
    current=current_rule_ids()
    for claim in doc["claims"]:
        ctype=claim.get("claim_type")
        refs=claim.get("exact_verification_refs"); contracts=claim.get("verification_contract_digests")
        if not isinstance(refs,list) or not refs or not isinstance(contracts,dict) or set(refs)!=set(contracts):
            raise ValueError("capability verification contract set mismatch")
        bound=[]
        for ref in refs:
            if ref not in by or claim["capability_id"] not in by[ref].get("allowed_capability_ids",[]):
                raise ValueError("verification not allowed for capability")
            if contracts[ref]!=verification_contract_digest(by[ref]):
                raise ValueError("capability verification contract digest mismatch")
            bound.append(by[ref])
        evidence_stages=sorted({s for row in bound for s in row.get("covered_stage_ids",[])})
        evidence_rules=sorted({r for row in bound for r in row.get("covered_target_rule_ids",[])})
        if any(r not in current for r in evidence_rules): raise ValueError("capability evidence references unknown rule")
        if ctype=="INHERITED_STAGE_PRESENCE":
            if claim.get("exact_status")!="PRESENT_AND_IDENTITY_BOUND": raise ValueError("stage presence cannot use behavioral verification status")
            if sorted(claim.get("covered_stage_ids",[]))!=evidence_stages or claim.get("covered_rule_ids") not in (None,[]):
                raise ValueError("inherited stage presence scope mismatch")
            if claim.get("participating_stage_ids") is not None: raise ValueError("stage presence cannot claim participating chain stages")
            if any(row.get("covered_target_rule_ids") for row in bound): raise ValueError("stage presence evidence cannot imply rule coverage")
        elif ctype=="VERIFIED_RULE_COVERAGE":
            rules=sorted(claim.get("covered_rule_ids",[]))
            if not rules or rules!=evidence_rules: raise ValueError("verified rule coverage must equal exact evidence rule union")
            if claim.get("covered_stage_ids") is not None or claim.get("participating_stage_ids") is not None:
                raise ValueError("verified rule coverage cannot independently claim stage scope")
            if claim.get("exact_status") not in {"POSITIVE_CASE_VERIFIED","FAILURE_CASE_VERIFIED","ADVERSARIAL_CASE_VERIFIED"}:
                raise ValueError("verified rule coverage status invalid")
        elif ctype=="VERIFIED_CROSS_STAGE_CHAIN":
            stages=sorted(claim.get("participating_stage_ids",[])); rules=sorted(claim.get("covered_rule_ids",[]))
            if len(stages)<2 or stages!=evidence_stages: raise ValueError("cross-stage participating stage scope mismatch")
            if not rules or rules!=evidence_rules: raise ValueError("cross-stage rule scope mismatch")
            if claim.get("covered_stage_ids") is not None: raise ValueError("cross-stage claim cannot imply full stage coverage")
            if claim.get("exact_status")!="END_TO_END_CHAIN_VERIFIED": raise ValueError("cross-stage chain status invalid")
        else:
            raise ValueError("unknown capability claim type")
    return True

def validate_transition_inputs(inventory,source_set,mapping,decisions,expected_count=176,expected_sources=17):
    jsonschema.validate(source_set,source_set_schema(expected_sources)); jsonschema.validate(mapping,brain_mapping_schema(expected_count)); jsonschema.validate(decisions,disposition_schema(expected_count))
    for obj,field in [(source_set,"source_set_digest"),(mapping,"mapping_set_digest"),(decisions,"decision_set_digest")]: _verify_embedded_digest(obj,field)
    if mapping.get("source_set_id")!=source_set.get("source_set_id") or mapping.get("source_set_digest")!=source_set.get("source_set_digest"): raise ValueError("mapping source-set binding mismatch")
    if decisions.get("source_mapping_set_id")!=mapping.get("mapping_set_id") or decisions.get("source_mapping_set_digest")!=mapping.get("mapping_set_digest"): raise ValueError("disposition source mapping mismatch")
    validate_brain_mapping(inventory,source_set,mapping,expected_count=expected_count)
    validate_disposition_decisions(mapping,decisions,expected_count=expected_count)
    return True

def validate_confirmed_transition_inputs(bound,expected_count=176,expected_sources=17):
    if not isinstance(bound,(tuple,list)) or len(bound)!=7: raise ValueError("confirmed transition requires complete seven-object input boundary")
    inventory,source_set,mapping,bseal,decisions,dseal,claims=bound
    jsonschema.validate(source_set,source_set_schema(expected_sources)); jsonschema.validate(mapping,brain_mapping_schema(expected_count)); jsonschema.validate(decisions,disposition_schema(expected_count)); jsonschema.validate(claims,claim_registry_schema())
    for obj,field in [(source_set,"source_set_digest"),(mapping,"mapping_set_digest"),(bseal,"seal_digest"),(decisions,"decision_set_digest"),(dseal,"seal_digest"),(claims,"registry_digest")]: _verify_embedded_digest(obj,field)
    if bseal.get("artifact_type")!="BRAIN_LEGACY_SEMANTIC_MAPPING_SEAL" or bseal.get("owner")!="WEB_BRAIN": raise ValueError("Brain mapping seal identity mismatch")
    if dseal.get("artifact_type")!="LEGACY_DISPOSITION_DECISION_SEAL" or dseal.get("owner")!="WEB_BRAIN": raise ValueError("disposition seal identity mismatch")
    if bseal.get("repair_source_package")!=REPAIR_SOURCE or dseal.get("repair_source_package")!=REPAIR_SOURCE: raise ValueError("repair source binding mismatch")
    if bseal.get("mapping_set_id")!=mapping.get("mapping_set_id") or bseal.get("mapping_set_digest")!=mapping.get("mapping_set_digest") or bseal.get("legacy_source_set_id")!=source_set.get("source_set_id") or bseal.get("legacy_source_set_digest")!=source_set.get("source_set_digest") or bseal.get("capability_claim_registry_id")!=claims.get("registry_id") or bseal.get("capability_claim_registry_digest")!=claims.get("registry_digest"): raise ValueError("Brain input seal mismatch")
    if dseal.get("decision_set_id")!=decisions.get("decision_set_id") or dseal.get("decision_set_digest")!=decisions.get("decision_set_digest") or dseal.get("mapping_set_id")!=mapping.get("mapping_set_id") or dseal.get("mapping_set_digest")!=mapping.get("mapping_set_digest"): raise ValueError("disposition decision seal mismatch")
    validate_transition_inputs(inventory,source_set,mapping,decisions,expected_count=expected_count,expected_sources=expected_sources)
    validate_capability_claim_registry(claims,REGISTRY)
    return ValidatedTransitionInputs(inventory,source_set,mapping,bseal,decisions,dseal,claims)

def _raw_bound_inputs():
    return (_load_json(INVENTORY),_load_json(SOURCE_SET),_load_json(BRAIN_MAPPING),_load_json(BRAIN_MAPPING_SEAL),_load_json(DISPOSITION_DECISIONS),_load_json(DISPOSITION_SEAL),_load_json(CAPABILITY_CLAIM_REGISTRY))

def load_bound_inputs():
    return validate_confirmed_transition_inputs(_raw_bound_inputs())

def render_confirmed_transition_rows(bound,registry=None,current=None,target_to_behavior=None,expected_count=176,expected_sources=17,validate_result_schema=True):
    validated=validate_confirmed_transition_inputs(bound,expected_count=expected_count,expected_sources=expected_sources)
    return render_migration_rows(validated,registry=registry,current=current,target_to_behavior=target_to_behavior,expected_count=expected_count,expected_sources=expected_sources,validate_result_schema=validate_result_schema)

def _behavior_state(targets,tv,by_id):
    verified=set()
    for target,refs in tv.items():
        for ref in refs:
            row=by_id[ref]
            if row["claim_strength"] in BEHAVIOR_STRENGTHS:
                if target not in row.get("covered_target_rule_ids",[]): raise ValueError("behavior ref subject mismatch")
                verified.add(target)
    unverified=set(targets)-verified
    status="VERIFIED_FOR_ALL_TARGETS" if not unverified else "PARTIALLY_VERIFIED" if verified else "NOT_VERIFIED"
    return status,sorted(verified),sorted(unverified)

def _evidence_state(semantic_gate,all_behavior):
    return ("CONFIRMED" if semantic_gate else "UNCONFIRMED","COMPLETE" if all_behavior else "INCOMPLETE")

def _derive_disposition_status(decision,semantic_gate,all_behavior):
    contract=_transition_contract(decision)
    evidence=_evidence_state(semantic_gate,all_behavior)
    outcome=contract["outcomes"].get(evidence)
    if outcome is None:
        if decision.get("basis")=="TECHNICAL_DUPLICATION_ANALYSIS": raise ValueError("technical duplication retirement requires confirmed exact legacy semantics and current replacement targets")
        if decision.get("basis")=="LEGACY_SEMANTIC_ANALYSIS" and decision.get("decision")=="RETIRE": raise ValueError("semantic supersession retirement requires confirmed exact legacy semantics")
        raise ValueError(f"transition evidence state is not legal for disposition: {evidence[0]} + {evidence[1]}")
    return outcome["migration_status"],outcome["behavioral_equivalence_claimed"]

def _phase_effect(decision,semantic_closed):
    d=decision["decision"]
    common={"blocks_pr1f_truthful_classification":False,"phase1_completion_effect":"NOT_DETERMINED_BY_THIS_ARTIFACT"}
    if d=="NOT_EVALUATED":
        return {**common,"disposition_closed":False,"legacy_semantics_closed":False,"closure_reason":"PR1F_MECHANISM_TRUTHFULLY_CLASSIFIES_UNRESOLVED_LEGACY_SEMANTICS","unresolved_owner":"WEB_BRAIN"}
    if d=="DEFER":
        return {**common,"disposition_closed":True,"legacy_semantics_closed":False,"closure_reason":"EXACT_CURRENT_SCOPE_OR_PRODUCT_DECISION_DEFERS_THIS_RULE","unresolved_owner":"WEB_BRAIN"}
    if d=="RETIRE":
        return {**common,"disposition_closed":True,"legacy_semantics_closed":bool(semantic_closed),"closure_reason":"EXACT_CURRENT_RETIREMENT_DECISION_RECORDED","unresolved_owner":None if semantic_closed or decision["basis"]=="CURRENT_PRODUCT_DECISION" else "WEB_BRAIN"}
    if d=="CARRY_FORWARD":
        return {**common,"disposition_closed":bool(semantic_closed),"legacy_semantics_closed":bool(semantic_closed),"closure_reason":"CARRY_FORWARD_REQUIRES_CONFIRMED_SEMANTIC_PRESERVATION" if not semantic_closed else "SEMANTIC_PRESERVATION_CONFIRMED","unresolved_owner":"WEB_BRAIN" if not semantic_closed else None}
    raise ValueError("unknown disposition")

def validate_migration_rows(rows,registry,current,bound=None,expected_count=176):
    validate_transition_contract_definition(); validate_verification_registry(registry); inventory,source_set,mapping,bseal,decisions,dseal,claims=bound or load_bound_inputs()
    by_map={r["old_rule_id"]:r for r in mapping["mappings"]}; by_dec={r["old_rule_id"]:r for r in decisions["decisions"]}; by_id={r["verification_id"]:r for r in registry}
    if not isinstance(rows,list) or len(rows)!=expected_count: raise ValueError("migration row count mismatch")
    for row in rows:
        m=by_map.get(row.get("old_rule_id")); decision=by_dec.get(row.get("old_rule_id"))
        if not m or not decision: raise ValueError("missing sealed mapping or disposition decision")
        exact={"old_source":m["old_source"],"old_section":m["old_section"],"legacy_source_set_id":source_set["source_set_id"],"legacy_source_sha256":m["legacy_source_sha256"],"source_binding_status":m["source_binding_status"],"exact_source_text_in_package":m["exact_source_text_in_package"],"exact_source_section_sha256":m["exact_source_section_sha256"],"semantic_evidence_ref":m["semantic_evidence_ref"],"brain_mapping_id":m["mapping_id"],"brain_mapping_digest":m["brain_capability_interpretation_digest"],"brain_mapping_status":m["brain_mapping_status"],"semantic_relation":m["semantic_relation"],"brain_capability_interpretation":m["brain_capability_interpretation"],"target_rule_ids":sorted(set(m["target_rule_ids"])),"disposition_decision":decision}
        if any(row.get(k)!=v for k,v in exact.items()): raise ValueError("migration row rewrites sealed source, mapping or disposition")
        targets=row["target_rule_ids"]; refs=row.get("verification_refs"); tv=row.get("target_verification")
        if row.get("migration_status") not in ALLOWED_STATUSES or not targets or not set(targets)<=current: raise ValueError("invalid status or targets")
        required={"E_LEGACY_SOURCE_IDENTITY","E_BRAIN_SEMANTIC_MAPPING_BINDING","E_DISPOSITION_DECISION_BINDING","E_TARGET_PRESENT","E_SOURCE_INDEX"}
        if not isinstance(refs,list) or any(x not in by_id for x in refs) or not required<=set(refs): raise ValueError("missing bound evidence")
        if not isinstance(tv,dict) or set(tv)!=set(targets): raise ValueError("target verification mismatch")
        for rr in tv.values():
            if any(ref not in refs for ref in rr): raise ValueError("target ref outside row")
        behavior_status,verified,unverified=_behavior_state(targets,tv,by_id)
        semantic_gate=_mapping_semantic_gate(row)
        expected_status,equiv=_derive_disposition_status(decision,semantic_gate,not unverified)
        unresolved_eq=[] if semantic_gate and not unverified else sorted(targets)
        expected_ver={"legacy_source_replayed":row["source_binding_status"]=="EXACT_SOURCE_TEXT_VERIFIED","legacy_semantic_mapping_confirmed":row["brain_mapping_status"]=="CONFIRMED","current_target_behavior_status":behavior_status,"behavior_verified_target_rule_ids":verified,"behavior_unverified_target_rule_ids":unverified,"legacy_equivalence_unresolved_target_rule_ids":unresolved_eq}
        expected_phase=_phase_effect(decision,semantic_gate)
        if row.get("migration_status")!=expected_status or row.get("behavioral_equivalence_claimed") is not equiv: raise ValueError("migration status not derived from separate axes")
        if row.get("verification_state")!=expected_ver: raise ValueError("verification state not mechanically derived")
        if row.get("phase_effect")!=expected_phase: raise ValueError("phase effect not mechanically derived")
        if row["migration_status"]=="SEMANTICALLY_PRESERVED_AND_BEHAVIORALLY_VERIFIED" and (not semantic_gate or unverified): raise ValueError("equivalence composite gate incomplete")
    return True

def _project_capability_claim(row):
    out={
        "capability_id":row["capability_id"],
        "claim_type":row["claim_type"],
        "claim_subject":row["claim_subject"],
        "status":row["exact_status"],
        "verification_refs":row["exact_verification_refs"],
        "limits":row["limits"],
    }
    for field in ("covered_stage_ids","covered_rule_ids","participating_stage_ids"):
        if field in row: out[field]=row[field]
    return out

def capability_status_document(counts,claims):
    return {"artifact_type":"CANDIDATE_CAPABILITY_STATUS","status_version":5,"package_name":PACKAGE_NAME,"artifact_role":"GENERATED_NON_AUTHORITATIVE_NAVIGATION_VIEW","may_satisfy_stage_gate":False,"may_satisfy_phase_gate":False,"artifact_status":"PHASE1_REPAIR_CANDIDATE_NOT_BASELINE","formal_release":False,"formal_baseline":False,"merged":False,"independent_stranger_cold_review_for_this_frozen_zip":"NOT_PERFORMED","migration_counts":counts,"legacy_semantic_equivalence_confirmed_rows":0,"capability_claim_registry_id":claims["registry_id"],"capability_claim_registry_digest":claims["registry_digest"],"capabilities":[_project_capability_claim(r) for r in claims["claims"]],"claim_limits":{"self_assign_independent_cold_review":False,"self_assign_baseline":False,"self_assign_release":False,"self_assign_merge_or_promotion":False,"legacy_equivalence_without_exact_source_and_brain_confirmation":False,"use_as_stage_or_phase_gate":False}}

def validate_capability_status(doc,registry=None,claim_registry=None):
    if doc.get("package_name")!=PACKAGE_NAME or doc.get("artifact_role")!="GENERATED_NON_AUTHORITATIVE_NAVIGATION_VIEW" or doc.get("may_satisfy_stage_gate") is not False or doc.get("may_satisfy_phase_gate") is not False: raise ValueError("capability view authority overstated")
    if doc.get("formal_release") is not False or doc.get("formal_baseline") is not False or doc.get("merged") is not False or doc.get("independent_stranger_cold_review_for_this_frozen_zip")!="NOT_PERFORMED" or doc.get("legacy_semantic_equivalence_confirmed_rows")!=0: raise ValueError("capability boundary overstated")
    claims=claim_registry or load_bound_inputs()[6]
    expected=[_project_capability_claim(r) for r in claims["claims"]]
    if doc.get("capability_claim_registry_digest")!=claims["registry_digest"] or doc.get("capabilities")!=expected: raise ValueError("capability claim subject mismatch")
    if registry: validate_capability_claim_registry(claims,registry)
    return True

def _str(min_len=1,pattern=None,enum=None,const=None):
    out={"type":"string"}
    if min_len is not None: out["minLength"]=min_len
    if pattern is not None: out["pattern"]=pattern
    if enum is not None: out["enum"]=enum
    if const is not None: out["const"]=const
    return out
def _str_list(min_items=0): return {"type":"array","items":_str(),"minItems":min_items,"uniqueItems":True}
def _nullable_str(): return {"type":["string","null"]}
def _semantic_evidence_ref_schema():
    return {"oneOf":[{"type":"null"},{"type":"object","additionalProperties":False,"required":["path","section_id","file_sha256","section_sha256"],"properties":{"path":_str(),"section_id":_str(),"file_sha256":_str(pattern="^[0-9a-f]{64}$"),"section_sha256":_str(pattern="^[0-9a-f]{64}$")}}]}

def disposition_item_schema():
    props={"decision_id":_str(pattern="^LDD::[A-Z0-9_]+$"),"old_rule_id":_str(pattern="^[A-Z0-9_]+$"),"owner":_str(enum=["WEB_BRAIN","USER"]),"decision":_str(enum=sorted(ALLOWED_DECISIONS)),"basis":_str(enum=sorted({key[1] for key in DISPOSITION_TRANSITION_CONTRACT})),"decision_ref":_str(),"user_decision_ref":_nullable_str(),"affects_product_requirement":_str(enum=["UNKNOWN","NO","YES"]),"affects_important_tradeoff":_str(enum=["UNKNOWN","NO","YES"]),"product_direction_effect":_str(enum=["NONE","PRESERVES_CONFIRMED_DIRECTION","CHANGES_CONFIRMED_DIRECTION","UNRESOLVED_MATERIAL_EFFECT"]),"rationale":_str()}
    branches=[]
    for (decision,basis),contract in sorted(DISPOSITION_TRANSITION_CONTRACT.items()):
        branch={"properties":{"decision":{"const":decision},"basis":{"const":basis},"owner":{"const":contract["owner"]},"product_direction_effect":{"enum":sorted(contract["effects"])}},"required":["decision","basis","owner","product_direction_effect"]}
        branch["properties"]["user_decision_ref"]={"type":"string","minLength":1} if contract["user_ref"]=="REQUIRED" else {"type":"null"}
        if contract["product_values"] is not None: branch["properties"]["affects_product_requirement"]={"enum":sorted(contract["product_values"])}
        if contract["tradeoff_values"] is not None: branch["properties"]["affects_important_tradeoff"]={"enum":sorted(contract["tradeoff_values"])}
        branches.append(branch)
    return {"type":"object","additionalProperties":False,"required":["decision_id","old_rule_id","owner","decision","basis","decision_ref","user_decision_ref","affects_product_requirement","affects_important_tradeoff","product_direction_effect","rationale"],"properties":props,"allOf":[{"oneOf":branches}]}
def disposition_schema(expected_count=176):
    return {"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"joyflow://legacy-disposition-decisions-v2","type":"object","additionalProperties":False,"required":["artifact_type","decision_set_version","decision_set_id","owner","source_mapping_set_id","source_mapping_set_digest","generator_may_modify","decision_scope","decisions","decision_set_digest"],"properties":{"artifact_type":_str(const="LEGACY_DISPOSITION_DECISION_SET"),"decision_set_version":{"const":2},"decision_set_id":_str(),"owner":_str(const="WEB_BRAIN"),"source_mapping_set_id":_str(),"source_mapping_set_digest":_str(pattern="^[0-9a-f]{64}$"),"generator_may_modify":{"const":False},"decision_scope":_str(),"decisions":{"type":"array","minItems":expected_count,"maxItems":expected_count,"items":disposition_item_schema()},"decision_set_digest":_str(pattern="^[0-9a-f]{64}$")}}

def migration_schema(expected_count=176):
    verification={"type":"object","additionalProperties":False,"required":["legacy_source_replayed","legacy_semantic_mapping_confirmed","current_target_behavior_status","behavior_verified_target_rule_ids","behavior_unverified_target_rule_ids","legacy_equivalence_unresolved_target_rule_ids"],"properties":{"legacy_source_replayed":{"type":"boolean"},"legacy_semantic_mapping_confirmed":{"type":"boolean"},"current_target_behavior_status":_str(enum=["NOT_VERIFIED","PARTIALLY_VERIFIED","VERIFIED_FOR_ALL_TARGETS"]),"behavior_verified_target_rule_ids":_str_list(0),"behavior_unverified_target_rule_ids":_str_list(0),"legacy_equivalence_unresolved_target_rule_ids":_str_list(0)}}
    phase={"type":"object","additionalProperties":False,"required":["blocks_pr1f_truthful_classification","phase1_completion_effect","disposition_closed","legacy_semantics_closed","closure_reason","unresolved_owner"],"properties":{"blocks_pr1f_truthful_classification":{"type":"boolean"},"phase1_completion_effect":_str(const="NOT_DETERMINED_BY_THIS_ARTIFACT"),"disposition_closed":{"type":"boolean"},"legacy_semantics_closed":{"type":"boolean"},"closure_reason":_str(),"unresolved_owner":{"type":["string","null"],"enum":["WEB_BRAIN","USER",None]}}}
    req=["old_rule_id","old_source","old_section","legacy_source_set_id","legacy_source_sha256","source_binding_status","exact_source_text_in_package","exact_source_section_sha256","semantic_evidence_ref","brain_mapping_id","brain_mapping_digest","brain_mapping_status","semantic_relation","brain_capability_interpretation","disposition_decision","migration_status","target_rule_ids","target_verification","verification_refs","verification_state","phase_effect","behavioral_equivalence_claimed","preservation_mechanism"]
    props={"old_rule_id":_str(pattern="^[A-Z0-9_]+$"),"old_source":_str(pattern="^[^/]+[.](md|json)$"),"old_section":_str(),"legacy_source_set_id":_str(),"legacy_source_sha256":_str(pattern="^[0-9a-f]{64}$"),"source_binding_status":_str(enum=["DIGEST_AND_SECTION_ID_BOUND_TEXT_NOT_BUNDLED","EXACT_SOURCE_TEXT_VERIFIED"]),"exact_source_text_in_package":{"type":"boolean"},"exact_source_section_sha256":_nullable_str(),"semantic_evidence_ref":_semantic_evidence_ref_schema(),"brain_mapping_id":_str(pattern="^BLSM::[A-Z0-9_]+$"),"brain_mapping_digest":_str(pattern="^[0-9a-f]{64}$"),"brain_mapping_status":_str(enum=["NOT_CONFIRMED_EXACT_SOURCE_TEXT_UNAVAILABLE","CONFIRMED","PARTIALLY_CONFIRMED","BLOCKED"]),"semantic_relation":_str(enum=["MAPPING_CANDIDATE_NOT_SEMANTICALLY_CONFIRMED","FULLY_PRESERVED","PARTIALLY_PRESERVED","REPLACED_WITH_CHANGED_SEMANTICS"]),"brain_capability_interpretation":_str(),"disposition_decision":disposition_item_schema(),"migration_status":_str(enum=sorted(ALLOWED_STATUSES)),"target_rule_ids":_str_list(1),"target_verification":{"type":"object","minProperties":1,"additionalProperties":_str_list(0)},"verification_refs":_str_list(1),"verification_state":verification,"phase_effect":phase,"behavioral_equivalence_claimed":{"type":"boolean"},"preservation_mechanism":_str()}
    return {"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"joyflow://legacy-rule-migration-v4","type":"array","minItems":expected_count,"maxItems":expected_count,"items":{"type":"object","additionalProperties":False,"required":req,"properties":props}}
def registry_schema():
    item={"type":"object","additionalProperties":False,"required":["verification_id","kind","claim_strength","covered_target_rule_ids","concrete_refs","coverage_statement","limitations","allowed_capability_ids"],"properties":{"verification_id":_str(pattern="^[A-Z0-9_]+$"),"kind":_str(enum=["UNIT_TEST","COMMAND","POLICY"]),"claim_strength":_str(enum=sorted(ALLOWED_STRENGTHS)),"covered_stage_ids":_str_list(0),"covered_target_rule_ids":_str_list(0),"concrete_refs":_str_list(1),"coverage_statement":_str(),"limitations":_str_list(0),"allowed_capability_ids":_str_list(0)}}
    return {"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"joyflow://migration-verification-registry-v5","type":"array","minItems":1,"items":item}
def _claim_properties(status_field):
    return {
        "capability_id":_str(pattern="^[A-Z0-9_]+$"),
        "claim_type":_str(enum=["INHERITED_STAGE_PRESENCE","VERIFIED_RULE_COVERAGE","VERIFIED_CROSS_STAGE_CHAIN"]),
        "claim_subject":_str(),
        "covered_stage_ids":_str_list(1),
        "covered_rule_ids":_str_list(1),
        "participating_stage_ids":_str_list(2),
        status_field:_str(enum=["PRESENT_AND_IDENTITY_BOUND","POSITIVE_CASE_VERIFIED","FAILURE_CASE_VERIFIED","ADVERSARIAL_CASE_VERIFIED","END_TO_END_CHAIN_VERIFIED"]),
        "verification_refs":_str_list(1),
        "exact_verification_refs":_str_list(1),
        "verification_contract_digests":{"type":"object","minProperties":1,"additionalProperties":_str(pattern="^[0-9a-f]{64}$")},
        "limits":_str_list(0),
    }

def capability_schema():
    cap={"type":"object","additionalProperties":False,"required":["capability_id","claim_type","claim_subject","status","verification_refs","limits"],"properties":_claim_properties("status")}
    false_fields=["self_assign_independent_cold_review","self_assign_baseline","self_assign_release","self_assign_merge_or_promotion","legacy_equivalence_without_exact_source_and_brain_confirmation","use_as_stage_or_phase_gate"]
    return {"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"joyflow://candidate-capability-status-v5","type":"object","additionalProperties":False,"required":["artifact_type","status_version","package_name","artifact_role","may_satisfy_stage_gate","may_satisfy_phase_gate","artifact_status","formal_release","formal_baseline","merged","independent_stranger_cold_review_for_this_frozen_zip","migration_counts","legacy_semantic_equivalence_confirmed_rows","capability_claim_registry_id","capability_claim_registry_digest","capabilities","claim_limits"],"properties":{"artifact_type":_str(const="CANDIDATE_CAPABILITY_STATUS"),"status_version":{"const":5},"package_name":_str(const=PACKAGE_NAME),"artifact_role":_str(const="GENERATED_NON_AUTHORITATIVE_NAVIGATION_VIEW"),"may_satisfy_stage_gate":{"const":False},"may_satisfy_phase_gate":{"const":False},"artifact_status":_str(const="PHASE1_REPAIR_CANDIDATE_NOT_BASELINE"),"formal_release":{"const":False},"formal_baseline":{"const":False},"merged":{"const":False},"independent_stranger_cold_review_for_this_frozen_zip":_str(const="NOT_PERFORMED"),"migration_counts":{"type":"object","additionalProperties":{"type":"integer","minimum":0}},"legacy_semantic_equivalence_confirmed_rows":{"const":0},"capability_claim_registry_id":_str(),"capability_claim_registry_digest":_str(pattern="^[0-9a-f]{64}$"),"capabilities":{"type":"array","minItems":4,"maxItems":4,"items":cap},"claim_limits":{"type":"object","additionalProperties":False,"required":false_fields,"properties":{k:{"const":False} for k in false_fields}}}}

def source_set_schema(expected_sources=17):
    src={"type":"object","additionalProperties":False,"required":["path","bytes","sha256"],"properties":{"path":_str(pattern="^[^/]+[.](md|json)$"),"bytes":{"type":"integer","minimum":1},"sha256":_str(pattern="^[0-9a-f]{64}$")}}
    return {"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"joyflow://legacy-source-set-v1","type":"object","additionalProperties":False,"required":["artifact_type","source_set_version","source_set_id","role","authoritative_for_current_joyflow","source_bytes_bundled","package_relative_source_root","source_identity_origin","sources","source_set_digest"],"properties":{"artifact_type":_str(const="LEGACY_SOURCE_SET"),"source_set_version":{"const":1},"source_set_id":_str(),"role":_str(const="HISTORICAL_COMPARISON_INPUT_ONLY"),"authoritative_for_current_joyflow":{"const":False},"source_bytes_bundled":{"type":"boolean"},"package_relative_source_root":{"type":["string","null"]},"source_identity_origin":_str(),"sources":{"type":"array","minItems":expected_sources,"maxItems":expected_sources,"items":src},"source_set_digest":_str(pattern="^[0-9a-f]{64}$")}}
def brain_mapping_schema(expected_count=176):
    item={"type":"object","additionalProperties":False,"required":["mapping_id","owner","old_rule_id","old_source","old_section","legacy_source_sha256","source_binding_status","exact_source_text_in_package","exact_source_section_sha256","semantic_evidence_ref","brain_capability_interpretation","brain_capability_interpretation_digest","target_rule_ids","semantic_relation","brain_mapping_status","semantic_delta","residual_scope"],"properties":{"mapping_id":_str(pattern="^BLSM::[A-Z0-9_]+$"),"owner":_str(const="WEB_BRAIN"),"old_rule_id":_str(pattern="^[A-Z0-9_]+$"),"old_source":_str(pattern="^[^/]+[.](md|json)$"),"old_section":_str(),"legacy_source_sha256":_str(pattern="^[0-9a-f]{64}$"),"source_binding_status":_str(enum=["DIGEST_AND_SECTION_ID_BOUND_TEXT_NOT_BUNDLED","EXACT_SOURCE_TEXT_VERIFIED"]),"exact_source_text_in_package":{"type":"boolean"},"exact_source_section_sha256":_nullable_str(),"semantic_evidence_ref":_semantic_evidence_ref_schema(),"brain_capability_interpretation":_str(),"brain_capability_interpretation_digest":_str(pattern="^[0-9a-f]{64}$"),"target_rule_ids":_str_list(1),"semantic_relation":_str(enum=["MAPPING_CANDIDATE_NOT_SEMANTICALLY_CONFIRMED","FULLY_PRESERVED","PARTIALLY_PRESERVED","REPLACED_WITH_CHANGED_SEMANTICS"]),"brain_mapping_status":_str(enum=["NOT_CONFIRMED_EXACT_SOURCE_TEXT_UNAVAILABLE","CONFIRMED","PARTIALLY_CONFIRMED","BLOCKED"]),"semantic_delta":_str(),"residual_scope":_str()}}
    return {"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"joyflow://brain-legacy-semantic-mapping-v2","type":"object","additionalProperties":False,"required":["artifact_type","mapping_version","mapping_set_id","owner","source_set_id","source_set_digest","mapping_scope","generator_may_modify","mapping_status","mappings","mapping_set_digest"],"properties":{"artifact_type":_str(const="BRAIN_LEGACY_SEMANTIC_MAPPING"),"mapping_version":{"const":2},"mapping_set_id":_str(),"owner":_str(const="WEB_BRAIN"),"source_set_id":_str(),"source_set_digest":_str(pattern="^[0-9a-f]{64}$"),"mapping_scope":_str(),"generator_may_modify":{"const":False},"mapping_status":_str(enum=["NOT_CONFIRMED_EXACT_SOURCE_TEXT_UNAVAILABLE","CONFIRMED","PARTIALLY_CONFIRMED","BLOCKED"]),"mappings":{"type":"array","minItems":expected_count,"maxItems":expected_count,"items":item},"mapping_set_digest":_str(pattern="^[0-9a-f]{64}$")}}
def claim_registry_schema():
    item={"type":"object","additionalProperties":False,"required":["capability_id","claim_type","claim_subject","exact_status","exact_verification_refs","verification_contract_digests","limits"],"properties":_claim_properties("exact_status")}
    return {"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"joyflow://capability-claim-registry-v3","type":"object","additionalProperties":False,"required":["artifact_type","registry_version","registry_id","owner","generator_may_modify","claims","registry_digest"],"properties":{"artifact_type":_str(const="CAPABILITY_CLAIM_REGISTRY"),"registry_version":{"const":3},"registry_id":_str(const="JOYFLOW_PHASE1_CAPABILITY_CLAIM_REGISTRY_V3"),"owner":_str(const="WEB_BRAIN"),"generator_may_modify":{"const":False},"claims":{"type":"array","minItems":4,"maxItems":4,"items":item},"registry_digest":_str(pattern="^[0-9a-f]{64}$")}}

def render_migration_rows(bound,registry=None,current=None,target_to_behavior=None,expected_count=176,expected_sources=17,validate_result_schema=True):
    if not isinstance(bound,ValidatedTransitionInputs): raise ValueError("migration renderer requires validated transition inputs")
    inventory,source_set,mapping,bseal,decisions,dseal,claims=bound
    registry=registry or REGISTRY; current=current or current_rule_ids(); target_to_behavior=target_to_behavior if target_to_behavior is not None else TARGET_TO_BEHAVIOR
    by_dec={r["old_rule_id"]:r for r in decisions["decisions"]}; by_id={r["verification_id"]:r for r in registry}; rows=[]
    for m in mapping["mappings"]:
        targets=sorted(set(m["target_rule_ids"])); tv={t:sorted(target_to_behavior.get(t,[])) for t in targets}
        behavior_status,verified,unverified=_behavior_state(targets,tv,by_id)
        decision=by_dec[m["old_rule_id"]]; semantic_gate=_mapping_semantic_gate(m,current)
        status,equiv=_derive_disposition_status(decision,semantic_gate,not unverified)
        refs=sorted({"E_LEGACY_SOURCE_IDENTITY","E_BRAIN_SEMANTIC_MAPPING_BINDING","E_DISPOSITION_DECISION_BINDING","E_TARGET_PRESENT","E_SOURCE_INDEX",*(x for rs in tv.values() for x in rs)})
        verification={"legacy_source_replayed":m["source_binding_status"]=="EXACT_SOURCE_TEXT_VERIFIED","legacy_semantic_mapping_confirmed":m["brain_mapping_status"]=="CONFIRMED","current_target_behavior_status":behavior_status,"behavior_verified_target_rule_ids":verified,"behavior_unverified_target_rule_ids":unverified,"legacy_equivalence_unresolved_target_rule_ids":[] if semantic_gate and not unverified else targets}
        phase=_phase_effect(decision,semantic_gate)
        rows.append({"old_rule_id":m["old_rule_id"],"old_source":m["old_source"],"old_section":m["old_section"],"legacy_source_set_id":source_set["source_set_id"],"legacy_source_sha256":m["legacy_source_sha256"],"source_binding_status":m["source_binding_status"],"exact_source_text_in_package":m["exact_source_text_in_package"],"exact_source_section_sha256":m["exact_source_section_sha256"],"semantic_evidence_ref":m["semantic_evidence_ref"],"brain_mapping_id":m["mapping_id"],"brain_mapping_digest":m["brain_capability_interpretation_digest"],"brain_mapping_status":m["brain_mapping_status"],"semantic_relation":m["semantic_relation"],"brain_capability_interpretation":m["brain_capability_interpretation"],"disposition_decision":decision,"migration_status":status,"target_rule_ids":targets,"target_verification":tv,"verification_refs":refs,"verification_state":verification,"phase_effect":phase,"behavioral_equivalence_claimed":equiv,"preservation_mechanism":"Semantic mapping, product-direction-bound disposition, current-target evidence and PR1F mechanism effect are separate sealed or mechanically derived axes."})
    if validate_result_schema: jsonschema.validate(rows,migration_schema(expected_count))
    validate_migration_rows(rows,registry,current,bound,expected_count=expected_count)
    return rows

def render_outputs():
    bound=load_bound_inputs(); claims=bound[6]; registry=REGISTRY
    rows=render_migration_rows(bound,registry=registry,current=current_rule_ids(),expected_count=176)
    counts={k:sum(r["migration_status"]==k for r in rows) for k in sorted(ALLOWED_STATUSES)}; cap=capability_status_document(counts,claims); jsonschema.validate(cap,capability_schema()); validate_capability_status(cap,registry,claims)
    behavior_counts={k:sum(r["verification_state"]["current_target_behavior_status"]==k for r in rows) for k in ["VERIFIED_FOR_ALL_TARGETS","PARTIALLY_VERIFIED","NOT_VERIFIED"]}
    lines=["# OLD RULE SEMANTIC MIGRATION","","artifact_role: HISTORICAL_REFERENCE_ONLY_MAPPING","active_architecture_authority: NO","",f"rows: {len(rows)}",*(f"{k.lower()}: {v}" for k,v in counts.items()),"",*(f"current_target_behavior_{k.lower()}: {v}" for k,v in behavior_counts.items()),"","legacy_semantic_equivalence_unresolved_rows: 176","disposition_not_evaluated_rows: 176","","> Current target behavior evidence does not prove legacy semantic equivalence. No row is deferred or retired. Web Brain technical closure does not require per-row user approval, but changed confirmed direction requires a current user decision.",""]
    return {"OLD_RULE_MIGRATION.json":json.dumps(rows,ensure_ascii=False,indent=2)+"\n","OLD_RULE_MIGRATION.md":"\n".join(lines),"machine/verification_registry.json":json.dumps(registry,ensure_ascii=False,indent=2)+"\n","CAPABILITY_STATUS.json":json.dumps(cap,ensure_ascii=False,indent=2)+"\n","schemas/legacy_rule_migration.schema.json":json.dumps(migration_schema(),ensure_ascii=False,indent=2)+"\n","schemas/migration_verification_registry.schema.json":json.dumps(registry_schema(),ensure_ascii=False,indent=2)+"\n","schemas/candidate_capability_status.schema.json":json.dumps(capability_schema(),ensure_ascii=False,indent=2)+"\n","schemas/legacy_source_set.schema.json":json.dumps(source_set_schema(),ensure_ascii=False,indent=2)+"\n","schemas/brain_legacy_semantic_mapping.schema.json":json.dumps(brain_mapping_schema(),ensure_ascii=False,indent=2)+"\n","schemas/legacy_disposition_decisions.schema.json":json.dumps(disposition_schema(),ensure_ascii=False,indent=2)+"\n","schemas/capability_claim_registry.schema.json":json.dumps(claim_registry_schema(),ensure_ascii=False,indent=2)+"\n"}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--check",action="store_true"); args=ap.parse_args()
    try: rendered=render_outputs()
    except (ValueError,OSError,jsonschema.ValidationError) as exc: print(f"MIGRATION_CLAIM_BLOCK: {exc}",file=sys.stderr); return 2
    outputs={ROOT/path:text for path,text in rendered.items()}
    if args.check:
        bad=[str(p.relative_to(ROOT)) for p,t in outputs.items() if not canonical_text_matches(p,t)]
        if bad: print("MIGRATION_ASSET_DRIFT: "+", ".join(bad),file=sys.stderr); return 2
    else:
        for p,t in outputs.items(): p.parent.mkdir(parents=True,exist_ok=True); write_canonical_text(p,t)
        print("generated disposition-evidence-phase-effect migration assets rows=176")
    return 0
if __name__=="__main__": raise SystemExit(main())
