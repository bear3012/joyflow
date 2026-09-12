#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.metadata, json, pathlib, subprocess, sys, yaml
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from canonical_text import read_canonical_text
META={'PACKAGE_MANIFEST.json','VALIDATION_REPORT.json','SHA256SUMS.txt'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p): return str(p.relative_to(ROOT)).replace('\\','/')
def files(): return sorted(p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
def check_manifest():
    m=json.loads(read_canonical_text(ROOT/'PACKAGE_MANIFEST.json'))
    l=json.loads(read_canonical_text(ROOT/'PHASE2_STAGE_LINEAGE.json'))
    if m.get('package_name')!=l.get('package_name') or m.get('artifact_status')!='PHASE2_REPAIR_CANDIDATE_NOT_BASELINE': raise RuntimeError('phase2 manifest identity mismatch')
    if m.get('repair_source_package')!=l.get('parent_package'): raise RuntimeError('phase2 parent identity mismatch')
    rows=m.get('payload_files',[]); actual={rel(p) for p in files()}; expected={r['path'] for r in rows}|META
    if actual!=expected: raise RuntimeError(f'phase2 manifest file set mismatch missing={sorted(expected-actual)} unexpected={sorted(actual-expected)}')
    if m.get('payload_file_count')!=len(rows): raise RuntimeError('phase2 manifest count mismatch')
    for r in rows:
        p=ROOT/r['path']
        if p.stat().st_size!=r['bytes'] or sha(p)!=r['sha256']: raise RuntimeError('manifest digest mismatch '+r['path'])
    sums={}
    for line in read_canonical_text(ROOT/'SHA256SUMS.txt').splitlines():
        if line.strip():
            h,n=line.split('  ',1); sums[n]=h
    target={rel(p) for p in files() if p.name!='SHA256SUMS.txt'}
    if set(sums)!=target: raise RuntimeError('sha file set mismatch')
    for n,h in sums.items():
        if sha(ROOT/n)!=h: raise RuntimeError('sha mismatch '+n)
    return m,l
def run(cmd):
    p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=90)
    if p.returncode: raise RuntimeError('command failed: '+' '.join(cmd)+'\n'+p.stdout+p.stderr)
    return (p.stdout+p.stderr).strip()
def check_canonical_package_text():
    suffixes={'.md','.json','.yaml','.yml','.py','.txt'}; bad=[]; count=0
    for path in files():
        if path.suffix.lower() not in suffixes: continue
        count+=1; data=path.read_bytes()
        if data.startswith(b'\xef\xbb\xbf') or b'\r' in data:
            bad.append(rel(path)); continue
        try: data.decode('utf-8')
        except UnicodeDecodeError: bad.append(rel(path))
    if bad: raise RuntimeError('non-canonical Joyflow package text: '+', '.join(bad))
    return count
def check_validation_dependencies():
    expected=['PyYAML==6.0.3','jsonschema==4.26.0']
    actual=[line.strip() for line in read_canonical_text(ROOT/'requirements-validation.txt').splitlines() if line.strip() and not line.lstrip().startswith('#')]
    if actual!=expected: raise RuntimeError(f'validation dependency contract mismatch: {actual}')
    installed={'PyYAML':importlib.metadata.version('PyYAML'),'jsonschema':importlib.metadata.version('jsonschema')}
    if installed!={'PyYAML':'6.0.3','jsonschema':'4.26.0'}: raise RuntimeError(f'validation dependency environment mismatch: {installed}')
    return installed
def main():
    m,l=check_manifest(); canonical_text_files=check_canonical_package_text(); dependency_versions=check_validation_dependencies()
    model=yaml.safe_load(read_canonical_text(ROOT/'machine/joyflow_dual_layer_model.yaml')); ext=model.get('phase2_extension') or {}
    if ext.get('stage_id')!=l.get('stage_id'): raise RuntimeError('model extension stage mismatch')
    stage=l['stage_id']
    if ext.get('architecture_change') is not (stage in {'PR2V_READ_ONLY_DISCOVERY_BRAIN_AUTHORIZATION_ALIGNMENT','PR2X_ARCHITECTURE_CONVERGENCE_CLOSURE_REPAIR'}) or ext.get('skill_system') is not False or ext.get('persistent_new_truth_source') is not False: raise RuntimeError('phase2 architecture boundary drift')
    if any('skill' in p.name.lower() for p in files() if p.parent.name in {'skills','skill'}): raise RuntimeError('skill layer unexpectedly present')
    run([sys.executable,'tools/generate_mechanical_assets.py','--check'])
    src='\n'.join(read_canonical_text(p) for p in (ROOT/'project_sources').glob('*.md'))
    required={'PR2A_PR_GOAL_SCENARIO_GROUNDING':['RULE_PHASE2A_PARENT_GOAL_CONTINUITY','RULE_PHASE2A_MATERIAL_OPERATING_ASSUMPTIONS_ONLY'],
              'PR2B_CURRENT_SOURCE_CONTEXT_GROUNDING':['RULE_PHASE2B_CURRENT_SOURCE_CONTEXT','RULE_PHASE2B_NO_CHANGE_IS_VALID'],
              'PR2C_SCENARIO_CUMULATIVE_REVIEW':['RULE_PHASE2C_SCENARIO_BOUNDED_GOAL_REVIEW','RULE_PHASE2C_RELEVANT_PRIOR_BEHAVIOR_REVIEW'],
              'PR2D_COMPACT_HANDOFF_DELTA_RESUME':['RULE_PHASE2D_COMPACT_COMPLETE_HANDOFF','RULE_PHASE2D_DERIVED_RESUME_VIEW'],
              'PR2R_SEMANTIC_TRUTH_TRANSPORT_REPAIR':['RULE_PHASE2_SEMANTIC_TRUTH_TRANSPORT','RULE_PHASE2_RECORDED_BY_DOES_NOT_CREATE_AUTHORITY','RULE_PHASE2_EVIDENCE_COMPATIBILITY','RULE_PHASE2_LAYERED_PACKAGE_IDENTITY'],
              'PR2R1_CLAIM_SUPPORT_RELEVANCE_REPAIR':['RULE_PHASE2_CLAIM_SUPPORT_RELEVANCE','RULE_PHASE2_SINGLE_USER_RELEVANCE_BOUNDARY'],
              'PR2R2_CUMULATIVE_DISPOSITION_PROSE_REPAIR':['RULE_PHASE2C_RELEVANT_PRIOR_BEHAVIOR_REVIEW'],
              'PR2R3_TEST_RUNNER_EFFICIENCY_REPAIR':['RULE_TEST_RUNNER_ADAPTIVE_ISOLATION'],
              'PR2S5_CUMULATIVE_SELF_HOSTING_REPRODUCIBILITY_REPAIR':['RULE_PHASE2_SELF_HOSTED_PACKAGE_IDENTITY_AUTHORITY','RULE_PHASE2_CANONICAL_GENERATED_TEXT_BYTES','RULE_PHASE2_RAW_EXECUTION_EVIDENCE_BYTE_TRUTH','RULE_PHASE2_VALIDATION_DEPENDENCY_CONTRACT','RULE_PHASE2_CI_EXISTING_PUBLIC_ENTRY_CONTRACT','RULE_PHASE2_PLATFORM_CAPABILITY_NA_BOUNDARY','RULE_PHASE2_GIT_FIXTURE_UNKNOWN_NOT_REPAIRED'],
              'PR2T_STRUCTURAL_COGNITION_CONTINUITY_REPAIR':['RULE_PHASE2_STRUCTURAL_DISCOVERY_TRIGGER_BOUNDARY','RULE_PHASE2_CODEX_ARCHITECTURE_PROPOSAL_BRAIN_CLOSURE','RULE_PHASE2_GOAL_CONDITIONED_STRUCTURAL_UNFOLDING','RULE_PHASE2_SEMANTIC_STRUCTURAL_FIBER_MAPPING','RULE_PHASE2_STRUCTURAL_QUESTION_CLOSURE','RULE_PHASE2_LOSSLESS_MATERIAL_STRUCTURAL_FOLD','RULE_PHASE2_LONG_TERM_STRUCTURAL_PROJECTION','RULE_PHASE2_STRUCTURAL_PROJECTION_FRESHNESS','RULE_PHASE2_MATERIAL_STRUCTURAL_CHANGE_REFOLD','RULE_PHASE2_STRUCTURAL_RECLOSURE_AND_REGROUNDING','RULE_PHASE2_STRUCTURAL_PROJECTION_AUTHORITY_BOUNDARY'],
              'PR2U_STRUCTURAL_COGNITION_LIFECYCLE_RECLOSURE_REPAIR':['RULE_STRUCTURAL_QUESTION_BRAIN_AUTHORITY','RULE_BRAIN_WHOLE_PROJECT_STRUCTURAL_REVIEW','RULE_STRUCTURAL_COGNITION_CONDITIONAL_LIFECYCLE_FIBER','RULE_STRUCTURAL_EVIDENCE_SEMANTIC_COMPATIBILITY','RULE_STRUCTURAL_ROUTE_PLANNING_MODES','RULE_STRUCTURAL_CLOSURE_PRECEDES_FINAL_MUTATION_PATH','RULE_STRUCTURAL_DISCOVERY_QUESTION_CLOSURE_AND_TARGETED_REWORK','RULE_PHASE2C_EXACT_STRUCTURAL_CONSEQUENCE_DISPOSITION','RULE_STRUCTURAL_COGNITION_EXACT_LINEAGE_TRANSPORT','RULE_PHASE2_STRUCTURAL_LIFECYCLE_STATE_MACHINE','RULE_PHASE2_LONG_TERM_STRUCTURAL_REFOLD_REVIEW_CHAIN'],
              'PR2V_READ_ONLY_DISCOVERY_BRAIN_AUTHORIZATION_ALIGNMENT':['RULE_BOUNDED_READ_ONLY_DISCOVERY_BRAIN_AUTHORIZATION','RULE_STRUCTURAL_QUESTION_BRAIN_AUTHORITY','RULE_STRUCTURAL_CLOSURE_PRECEDES_FINAL_MUTATION_PATH','RULE_PHASE2_STRUCTURAL_LIFECYCLE_STATE_MACHINE'],
              'PR2W_EPHEMERAL_GITHUB_EVIDENCE_TRANSPORT_REPAIR':['RULE_EVIDENCE_OBJECT_TRANSPORT_SEPARATION','RULE_GITHUB_EXACT_OBJECT_EVIDENCE_TRANSPORT_RECEIPT','RULE_OPTIONAL_EVIDENCE_TRANSPORT_PLAN','RULE_READ_ONLY_DISCOVERY_EVIDENCE_TRANSPORT_MUTATION_BOUNDARY','RULE_GITHUB_EVIDENCE_TRANSPORT_NOT_PRODUCT_PR','RULE_TRANSPORT_ONLY_EVIDENCE_SURFACE','RULE_EPHEMERAL_EVIDENCE_RETENTION_CLEANUP','RULE_EPHEMERAL_EVIDENCE_TERMINAL_CLEANUP_CONTINUATION','RULE_EVIDENCE_TRANSPORT_EXACT_LINEAGE','RULE_EVIDENCE_TRANSPORT_CLEANUP_EXACT_LINEAGE'],
              'PR2X_ARCHITECTURE_CONVERGENCE_CLOSURE_REPAIR':['RULE_ARCHITECTURE_CONVERGENCE_SIX_STAGE_MAINLINE','RULE_BOUNDED_READ_ONLY_DISCOVERY_BRAIN_AUTHORIZATION','RULE_MUTATION_EXECUTION_ENVELOPE_APPROVAL_BINDING','RULE_SAME_ENVELOPE_REWORK_NO_REAPPROVAL','RULE_PRODUCT_TOLERANCE_USER_AUTHORITY','RULE_CONTEXTUAL_RISK_ASSURANCE_DISPOSITION','RULE_ACTIVE_GLOBAL_INVARIANT_NOT_RESIDUAL_WAIVER','RULE_FAILURE_MECHANISM_TARGETED_VALIDATION','RULE_EVIDENCE_TRANSPORT_EXACT_CANONICAL_BUNDLE_BYTES','RULE_EVIDENCE_CLEANUP_GENERIC_TASK_TERMINAL','RULE_ROLE_EXECUTABILITY_WEB_BRAIN_LOCAL_CODEX']}[stage]
    for rid in required:
        if rid not in src: raise RuntimeError('missing stage rule '+rid)
    if stage in {'PR2T_STRUCTURAL_COGNITION_CONTINUITY_REPAIR','PR2U_STRUCTURAL_COGNITION_LIFECYCLE_RECLOSURE_REPAIR','PR2V_READ_ONLY_DISCOVERY_BRAIN_AUTHORIZATION_ALIGNMENT','PR2W_EPHEMERAL_GITHUB_EVIDENCE_TRANSPORT_REPAIR','PR2X_ARCHITECTURE_CONVERGENCE_CLOSURE_REPAIR'}:
        arch=model.get('architecture',{})
        discovery=model.get('path_discovery_policy',{})
        binding=model.get('path_discovery_binding_policy',{})
        structural=model.get('structural_cognition_policy',{})
        if arch.get('path_discovery_topology') not in {'GITHUB_DEFAULT_WITH_CODEX_GOAL_CONDITIONED_STRUCTURAL_DISCOVERY_BEFORE_FINAL_BOUNDARY','BRAIN_ACCESSIBLE_REPOSITORY_EVIDENCE_WITH_CODEX_GOAL_CONDITIONED_STRUCTURAL_DISCOVERY_BEFORE_FINAL_BOUNDARY'}:
            raise RuntimeError('phase2t structural discovery topology mismatch')
        if discovery.get('structural_discovery_reader')!='CODEX_LOCAL_READ_ONLY' or discovery.get('structural_discovery_may_precede_final_mutation_path_freeze') is not True:
            raise RuntimeError('phase2t structural discovery ordering mismatch')
        required_structural={
            'trigger':'MATERIAL_ARCHITECTURE_UNCERTAINTY',
            'discovery_owner':'CODEX',
            'architecture_proposal_owner':'CODEX',
            'project_level_review_owner':'WEB_BRAIN',
            'final_technical_closure_owner':'WEB_BRAIN',
            'discovery_scope':'GOAL_CONDITIONED_SEMANTIC_RELATION_UNFOLDING',
            'final_mutation_paths_frozen_after_structural_closure':True,
        }
        if any(structural.get(k)!=v for k,v in required_structural.items()):
            raise RuntimeError('phase2t Brain/Codex structural authority split mismatch')
        persistent=structural.get('persistent_projection',{})
        if persistent.get('artifact_role')!='DERIVED_NON_AUTHORITATIVE_STRUCTURAL_NAVIGATION' or persistent.get('sparse_only') is not True or persistent.get('based_on_exact_commit') is not True or persistent.get('stale_or_conflict_never_overrides_repository') is not True:
            raise RuntimeError('phase2t long-term structural projection authority/freshness mismatch')
        required_binding={
            'structural_relations_require_typed_semantic_mapping':True,
            'structural_question_closure_required_before_route_recommendation':True,
            'structural_fold_preserves_counterevidence_unresolved_and_omissions':True,
            'persistent_structural_projection_is_sparse_derived_and_commit_anchored':True,
            'persistent_structural_projection_never_overrides_current_repository':True,
        }
        if any(binding.get(k) is not v for k,v in required_binding.items()):
            raise RuntimeError('phase2t structural cognition binding policy incomplete')
        projection_schema=json.loads(read_canonical_text(ROOT/'schemas/long_term_structural_projection.schema.json'))
        if projection_schema.get('$id')!='joyflow://long-term-structural-projection-v2':
            raise RuntimeError('phase2t long-term structural projection schema identity mismatch')
        if stage in {'PR2U_STRUCTURAL_COGNITION_LIFECYCLE_RECLOSURE_REPAIR','PR2V_READ_ONLY_DISCOVERY_BRAIN_AUTHORIZATION_ALIGNMENT','PR2W_EPHEMERAL_GITHUB_EVIDENCE_TRANSPORT_REPAIR','PR2X_ARCHITECTURE_CONVERGENCE_CLOSURE_REPAIR'}:
            required_u={
                'lifecycle_object':'STRUCTURAL_COGNITION_LIFECYCLE',
                'brain_question_frame_owner':'WEB_BRAIN',
                'codex_may_not_rewrite_brain_question':True,
                'closure_requires_compatible_evidence':True,
                'final_path_requires_closed_structural_closure_when_triggered':True,
                'codex_route_requires_brain_disposition_before_mutation':True,
                'post_implementation_structural_review_required_when_closed':True,
                'long_term_projection_self_review_status_forbidden':True,
                'read_only_structural_discovery_user_approval_policy':('WEB_BRAIN_BOUNDED_READ_ONLY_AUTHORIZATION_NO_SEPARATE_USER_APPROVAL' if stage in {'PR2V_READ_ONLY_DISCOVERY_BRAIN_AUTHORIZATION_ALIGNMENT','PR2W_EPHEMERAL_GITHUB_EVIDENCE_TRANSPORT_REPAIR','PR2X_ARCHITECTURE_CONVERGENCE_CLOSURE_REPAIR'} else 'CURRENT_INSTRUCTION_REQUIRES_APPROVAL_PENDING_REPLACEMENT_CONFIRMATION'),
            }
            if any(structural.get(k)!=v for k,v in required_u.items()):
                raise RuntimeError('phase2u structural lifecycle policy incomplete')
            if json.loads(read_canonical_text(ROOT/'schemas/final_path_decision.schema.json')).get('$id')!='joyflow://final-path-decision-v4': raise RuntimeError('phase2u final-path schema identity mismatch')
            if json.loads(read_canonical_text(ROOT/'schemas/path_discovery_return.schema.json')).get('$id')!='joyflow://path-discovery-return-v7': raise RuntimeError('phase2u path-discovery schema identity mismatch')
            if stage in {'PR2U_STRUCTURAL_COGNITION_LIFECYCLE_RECLOSURE_REPAIR','PR2V_READ_ONLY_DISCOVERY_BRAIN_AUTHORIZATION_ALIGNMENT'}:
                if json.loads(read_canonical_text(ROOT/'schemas/codex_handoff_projection.schema.json')).get('$id')!='joyflow://codex-handoff-projection-v9': raise RuntimeError('phase2u/v handoff schema identity mismatch')
                if json.loads(read_canonical_text(ROOT/'schemas/codex_execution_return.schema.json')).get('$id')!='joyflow://codex-execution-return-v9': raise RuntimeError('phase2u/v codex-return schema identity mismatch')
            run([sys.executable,'-m','unittest','tests.test_phase2_structural_lifecycle_reclosure'])
            if stage in {'PR2V_READ_ONLY_DISCOVERY_BRAIN_AUTHORIZATION_ALIGNMENT','PR2W_EPHEMERAL_GITHUB_EVIDENCE_TRANSPORT_REPAIR','PR2X_ARCHITECTURE_CONVERGENCE_CLOSURE_REPAIR'}:
                req=model.get('approval_requirements',{})
                if req.get('mutating_requires_user_approval') is not True or req.get('read_only_discovery_requires_separate_user_approval') is not False or req.get('read_only_discovery_authorization_owner')!='WEB_BRAIN': raise RuntimeError('phase2v read-only authorization policy mismatch')
                run([sys.executable,'-m','unittest','tests.test_phase2_read_only_discovery_authorization'])
            if stage=='PR2X_ARCHITECTURE_CONVERGENCE_CLOSURE_REPAIR':
                role=model.get('role_executability_policy',{}); approval=model.get('mutation_execution_envelope_policy',{}); inv=model.get('global_invariant_policy',{}); pol=model.get('evidence_transport_policy',{})
                if role.get('web_brain_surface')!='WEB_ONLY' or role.get('executor_surface')!='LOCAL_CODEX' or role.get('handoff_topology')!='USER_MEDIATED_SEMIAUTOMATIC' or role.get('logical_authorization_is_not_automatic_invocation') is not True or role.get('connector_specific_dependency_forbidden') is not True or role.get('background_controller_required') is not False:
                    raise RuntimeError('PR2X role executability policy mismatch')
                if approval.get('stable_across_same_semantic_rework') is not True or approval.get('material_change_invalidates_prior_authorization') is not True or approval.get('same_envelope_brain_review_failure_requires_new_user_approval') is not False or approval.get('same_envelope_user_acceptance_failure_requires_new_user_approval') is not False:
                    raise RuntimeError('PR2X mutation execution envelope policy mismatch')
                if inv.get('residual_risk_acceptance_cannot_waive_active_global_invariant') is not True:
                    raise RuntimeError('PR2X global invariant policy mismatch')
                if pol.get('transported_object_bytes_are_exact_canonical_evidence_bundle') is not True or pol.get('temporary_ref_namespace')!='refs/heads/joyflow-evidence/' or pol.get('temporary_ref_positive_namespace_only') is not True or pol.get('cleanup_continuation_terminal_basis')!='TASK_TERMINAL_EVIDENCE':
                    raise RuntimeError('PR2X Evidence transport convergence mismatch')
                if json.loads(read_canonical_text(ROOT/'schemas/evidence_transport_receipt.schema.json')).get('$id')!='joyflow://evidence-transport-receipt-v2': raise RuntimeError('PR2X receipt schema identity mismatch')
                if json.loads(read_canonical_text(ROOT/'schemas/evidence_transport_cleanup_continuation.schema.json')).get('$id')!='joyflow://evidence-transport-cleanup-continuation-v2': raise RuntimeError('PR2X cleanup continuation schema identity mismatch')
                if json.loads(read_canonical_text(ROOT/'schemas/codex_handoff_projection.schema.json')).get('$id')!='joyflow://codex-handoff-projection-v11': raise RuntimeError('PR2X handoff schema identity mismatch')
                if json.loads(read_canonical_text(ROOT/'schemas/codex_execution_return.schema.json')).get('$id')!='joyflow://codex-execution-return-v11': raise RuntimeError('PR2X return schema identity mismatch')
                pib=l.get('project_instruction_change_status',{})
                active=pib.get('active_instruction',{}) if isinstance(pib,dict) else {}
                if pib.get('change')!='USER_CONFIRMED_ACTIVE_COMPACT_V2_DEVELOPMENT_INSTRUCTION': raise RuntimeError('PR2X active Development Instruction binding missing')
                if active.get('confirmed_source_sha256')!='126b6e73df483e8d6bc81d6c18d41f8068844b46d529425ddac0b3fe54f6dff8': raise RuntimeError('PR2X active Development Instruction digest mismatch')
                if active.get('physical_surface')!='WEB_BRAIN_PROJECT_INSTRUCTION_EXTERNAL_TO_RUNTIME_PACKAGE' or pib.get('development_instruction_duplicated_into_runtime_package') is not False: raise RuntimeError('PR2X Development Instruction physical boundary mismatch')
                if (ROOT/'JOYFLOW_PROJECT_INSTRUCTION_REPLACEMENT_CANDIDATE_ARCHITECTURE_CONVERGENCE.md').exists(): raise RuntimeError('stale embedded Project Instruction replacement candidate present')
                run([sys.executable,'-m','unittest','tests.test_architecture_convergence_closure'])
                # Evidence transport suite is run method-by-method elsewhere when full-module runtime exceeds the bounded validator window.
            if stage=='PR2W_EPHEMERAL_GITHUB_EVIDENCE_TRANSPORT_REPAIR':
                pol=model.get('evidence_transport_policy',{}); merge=model.get('merge_boundary',{})
                if pol.get('role')!='OPTIONAL_TRANSPORT_ADAPTER_FOR_CURRENT_ROUND_EVIDENCE_BUNDLE' or pol.get('github_transport_requires_user_approved_remote_mutation') is not True or pol.get('ephemeral_by_default') is not True or pol.get('background_cleanup_service_forbidden') is not True or pol.get('cleanup_continuation_requires_original_user_approved_mutating_projection') is not True or pol.get('cleanup_continuation_merged_pr_terminal_basis')!='TASK_COMPLETION_POINTER' or pol.get('cleanup_ref_must_still_match_receipt_commit') is not True or merge.get('transport_only_evidence_remote_mutation_requires_product_pr') is not False or merge.get('transport_only_evidence_remote_mutation_requires_user_execution_approval') is not True or merge.get('product_or_governance_repository_change_requires_pr') is not True:
                    raise RuntimeError('phase2w Evidence transport authority/lifecycle policy mismatch')
                if json.loads(read_canonical_text(ROOT/'schemas/evidence_transport_receipt.schema.json')).get('$id')!='joyflow://evidence-transport-receipt-v1': raise RuntimeError('phase2w receipt schema identity mismatch')
                if json.loads(read_canonical_text(ROOT/'schemas/evidence_transport_cleanup_continuation.schema.json')).get('$id')!='joyflow://evidence-transport-cleanup-continuation-v1': raise RuntimeError('phase2w cleanup continuation schema identity mismatch')
                if json.loads(read_canonical_text(ROOT/'schemas/codex_handoff_projection.schema.json')).get('$id')!='joyflow://codex-handoff-projection-v10': raise RuntimeError('phase2w handoff schema identity mismatch')
                if json.loads(read_canonical_text(ROOT/'schemas/codex_execution_return.schema.json')).get('$id')!='joyflow://codex-execution-return-v10': raise RuntimeError('phase2w return schema identity mismatch')
                run([sys.executable,'-m','unittest','tests.test_phase2_ephemeral_github_evidence_transport'])
        run([sys.executable,'-m','unittest','tests.test_phase2_structural_cognition_continuity'])
    if 'FOLDED_REPOSITORY_STATE_DATABASE' in src or 'PERSISTENT_SKILL_REGISTRY' in src: raise RuntimeError('over-design marker present')
    print(json.dumps({'verdict':'PASS_PHASE2_CANDIDATE','stage_id':stage,'package_name':m['package_name'],'payload_files':m['payload_file_count'],'canonical_text_files':canonical_text_files,'validation_dependencies':dependency_versions,'git_fixture_flake':'UNRESOLVED_DISCOVERY_REQUIRED'},ensure_ascii=False)); return 0
if __name__=='__main__': raise SystemExit(main())
