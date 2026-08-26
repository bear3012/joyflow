#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, pathlib, re, sys
import yaml
from canonical_text import canonical_text_matches, read_canonical_text, write_canonical_text

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / 'machine' / 'joyflow_dual_layer_model.yaml'
HEX={'type':'string','pattern':'^[0-9a-f]{64}$'}
ROLE_ENUM=['USER','WEB_BRAIN','CODEX','TOOL']
RULE_RE=re.compile(r'^canonical_rule_id:\s*([A-Z0-9_]+)\s*$',re.M)
SECTION_RE=re.compile(r'^source_section_id:\s*([^\n]+)\s*$',re.M)

def dump_json(v): return json.dumps(v,ensure_ascii=False,indent=2)+'\n'

def event_schema(model):
    return {'type':'object','additionalProperties':False,'required':['event_id','event_type','from_stage','to_stage','changed_anchor_fields','added_fibers','changed_fibers','removed_fibers','evidence_refs','reason'],'properties':{
      'event_id':{'type':'string','minLength':1},'event_type':{'enum':model['transition_event_types']},'from_stage':{'type':['string','null']},'to_stage':{'enum':model['stages']},
      'changed_anchor_fields':{'type':'array','items':{'type':'string'},'uniqueItems':True},'added_fibers':{'type':'array','items':{'enum':list(model['fiber_types'])},'uniqueItems':True},
      'changed_fibers':{'type':'array','items':{'enum':list(model['fiber_types'])},'uniqueItems':True},'removed_fibers':{'type':'array','items':{'enum':list(model['fiber_types'])},'uniqueItems':True},
      'evidence_refs':{'type':'array','items':{'type':'string'},'minItems':1,'uniqueItems':True},'reason':{'type':'string','minLength':1}}}

def approval_record_schema(model):
    binding={'type':'object','additionalProperties':False,'required':model['approval_requirements']['binding_fields'],'properties':{k:HEX for k in model['approval_requirements']['binding_fields']}}
    return {'type':'object','additionalProperties':False,'required':['status','owner','scope','basis','decision_ref','binding'],'properties':{
      'status':{'enum':['NEEDS_USER_APPROVAL','APPROVED_FINAL','NEEDS_BRAIN_READ_ONLY_AUTHORIZATION','AUTHORIZED_READ_ONLY_DISCOVERY']},'owner':{'const':'WEB_BRAIN'},'scope':{'enum':model['approval_requirements']['approval_scopes']},
      'basis':{'enum':['NOT_YET_APPROVED','CURRENT_EXPLICIT_USER_DECISION','NOT_YET_AUTHORIZED','WEB_BRAIN_BOUNDED_READ_ONLY_DISCOVERY_AUTHORIZATION']},'decision_ref':{'type':['string','null']},'binding':{'oneOf':[binding,{'type':'null'}]}},
      'allOf':[
        {'if':{'properties':{'status':{'const':'APPROVED_FINAL'}}},'then':{'properties':{'scope':{'const':'EXECUTION_ONLY'},'basis':{'const':'CURRENT_EXPLICIT_USER_DECISION'},'decision_ref':{'type':'string','minLength':1}},'required':['binding']}},
        {'if':{'properties':{'status':{'const':'NEEDS_USER_APPROVAL'}}},'then':{'properties':{'scope':{'const':'EXECUTION_ONLY'},'basis':{'const':'NOT_YET_APPROVED'},'decision_ref':{'type':'null'},'binding':{'type':'null'}}}},
        {'if':{'properties':{'status':{'const':'AUTHORIZED_READ_ONLY_DISCOVERY'}}},'then':{'properties':{'scope':{'const':'READ_ONLY_DISCOVERY_ONLY'},'basis':{'const':'WEB_BRAIN_BOUNDED_READ_ONLY_DISCOVERY_AUTHORIZATION'},'decision_ref':{'type':'string','minLength':1}},'required':['binding']}},
        {'if':{'properties':{'status':{'const':'NEEDS_BRAIN_READ_ONLY_AUTHORIZATION'}}},'then':{'properties':{'scope':{'const':'READ_ONLY_DISCOVERY_ONLY'},'basis':{'const':'NOT_YET_AUTHORIZED'},'decision_ref':{'type':'null'},'binding':{'type':'null'}}}}
      ]}

def capsule_schema(model):
    fiber_names=list(model['fiber_types'])
    fiber={'type':'object','additionalProperties':False,'required':['fiber_type','status','revision','previous_digest','payload','fiber_digest'],'properties':{
      'fiber_type':{'enum':fiber_names},'status':{'enum':model['fiber_statuses']},'revision':{'type':'integer','minimum':1},'previous_digest':{'type':['string','null'],'pattern':'^[0-9a-f]{64}$'},'payload':{'type':'object'},'fiber_digest':HEX}}
    effect={'type':'object','additionalProperties':True,'required':['effect_id','effect_type','value','effect_digest'],'properties':{'effect_id':{'type':'string','minLength':1},'effect_type':{'enum':model['effect_types']},'value':{'type':'string','minLength':1},'effect_digest':HEX}}
    evidence={'type':'object','additionalProperties':False,'required':['evidence_id','authority','kind','ref','claim','claim_digest','produced_by','subject_type','subject_id','raw_output_ref'],'properties':{
      'evidence_id':{'type':'string','minLength':1},'authority':{'enum':model['evidence_authorities']},'kind':{'type':'string','minLength':1},'ref':{'type':'string','minLength':1},'claim':{'type':'string','minLength':1},'claim_digest':HEX,
      'produced_by':{'enum':ROLE_ENUM},'subject_type':{'type':'string','minLength':1},'subject_id':{'type':'string','minLength':1},'raw_output_ref':{'type':['string','null']},'raw_output_sha256':{'oneOf':[HEX,{'type':'null'}]}}}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'joyflow://fibered-task-capsule-v5','type':'object','additionalProperties':False,
      'required':['artifact_type','model_id','model_version','capsule_id','task_anchor','task_progress','route_profile','task_classification','active_fibers','evidence_registry','refs','derived_gates','unresolved_blockers','approval_record','stop_conditions','capsule_digest'],
      'properties':{
        'artifact_type':{'const':'FIBERED_TASK_CAPSULE'},'model_id':{'const':model['model_id']},'model_version':{'const':model['model_version']},'capsule_id':{'type':'string','minLength':1},
        'task_anchor':{'type':'object','additionalProperties':False,'required':['project_id','task_id','task_version','goal','desired_result','non_goals','planning_context','change_scope','repository_operation','repository_anchor','artifact_anchor','anchor_digest'],'properties':{
          'project_id':{'type':'string','minLength':1},'task_id':{'type':'string','minLength':1},'task_version':{'type':'integer','minimum':1},'goal':{'type':'string','minLength':1},'desired_result':{'type':'string','minLength':1},'non_goals':{'type':'array','items':{'type':'string'},'uniqueItems':True},
          'planning_context':{'type':'object','additionalProperties':False,'required':['parent_goal','material_operating_assumptions','relevant_prior_behaviors','exit_conditions'],'properties':{
            'parent_goal':{'type':['string','null']},
            'material_operating_assumptions':{'type':'array','items':{'type':'object','additionalProperties':False,'required':['condition_type','assumption','material_effect','source_basis','epistemic_status','source_refs','reopen_trigger'],'properties':{'condition_type':{'enum':['DESCRIPTIVE_CONDITION','PRODUCT_TOLERANCE']},'assumption':{'type':'string','minLength':1},'material_effect':{'type':'string','minLength':1},'source_basis':{'enum':['USER_CONFIRMED','REPOSITORY_OBSERVED','BRAIN_INFERENCE']},'epistemic_status':{'enum':['CONFIRMED','OBSERVED','INFERRED']},'source_refs':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True},'reopen_trigger':{'type':'string','minLength':1}}},'uniqueItems':True},
            'relevant_prior_behaviors':{'type':'array','items':{'type':'object','additionalProperties':False,'required':['behavior_id','statement','source_refs','why_relevant','expected_disposition','authorization_refs'],'properties':{'behavior_id':{'type':'string','minLength':1},'statement':{'type':'string','minLength':1},'source_refs':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True},'why_relevant':{'type':'string','minLength':1},'expected_disposition':{'enum':['PRESERVE_REQUIRED','CHANGE_AUTHORIZED','SUPERSEDE_AUTHORIZED']},'authorization_refs':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True}}},'uniqueItems':True},
            'exit_conditions':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True}}},
          'change_scope':{'enum':model['change_scopes']},'repository_operation':{'enum':model['repository_operations']},'repository_anchor':{'type':['object','null']},'artifact_anchor':{'type':['object','null']},'anchor_digest':HEX}},
        'task_progress':{'type':'object','additionalProperties':False,'required':['stage','cycle','previous_stage','cycle_trigger','parent_capsule_digest','transition_event'],'properties':{
          'stage':{'enum':model['stages']},'cycle':{'type':'integer','minimum':1},'previous_stage':{'type':['string','null']},'cycle_trigger':{'enum':['NONE']+model['cycle_triggers']},'parent_capsule_digest':{'type':['string','null'],'pattern':'^[0-9a-f]{64}$'},'transition_event':{'oneOf':[event_schema(model),{'type':'null'}]}}},
        'route_profile':{'enum':list(model['route_profiles'])},
        'task_classification':{'type':'object','additionalProperties':False,'required':['risk_markers','domain_lanes'],'properties':{'risk_markers':{'type':'array','items':{'enum':model['risk_markers']},'minItems':1,'uniqueItems':True},'domain_lanes':{'type':'array','items':{'enum':model['domain_lanes']},'minItems':1,'uniqueItems':True}}},
        'active_fibers':{'type':'object','additionalProperties':fiber,'propertyNames':{'enum':fiber_names}},
        'evidence_registry':{'type':'array','items':evidence},'refs':{'type':'object'},'derived_gates':{'type':'object'},'unresolved_blockers':{'type':'array','items':{'type':'string'}},
        'approval_record':approval_record_schema(model),'stop_conditions':{'type':'array','items':{'type':'string'},'minItems':1},'capsule_digest':HEX},
      '$defs':{'fiber':fiber,'effect':effect,'approval_record':approval_record_schema(model),'evidence':evidence}}

def projection_schema(model):
    req=['artifact_type','projection_version','build_identity','project_id','task_id','round_id','capsule_id','capsule_digest','task_anchor','task_progress','route_profile','execution_mode','flow_depth','validation_depth','task_classification','material_semantics','repository_evidence','current_source_context','decision_boundary','validation','traceability','derived_gates','codex_technical_authority','technical_route_space','execution_object','task_object_lifecycle','delivery','stop_conditions','projection_digest']
    route={'type':'object','additionalProperties':False,'required':['route_id','summary','expected_mechanisms','expected_paths','advantages','known_costs','known_risks','important_tradeoff_owner'],'properties':{
      'route_id':{'type':'string','minLength':1},'summary':{'type':'string','minLength':1},
      'expected_mechanisms':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True},
      'expected_paths':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
      'advantages':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True},
      'known_costs':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
      'known_risks':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
      'important_tradeoff_owner':{'enum':['CODEX_WITHIN_BOUNDARY','WEB_BRAIN','USER']}}}
    subject_binding={'type':'object','additionalProperties':False,'required':['subject_type','subject_refs','subject_digest'],'properties':{
      'subject_type':{'type':'string','minLength':1},'subject_refs':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True},'subject_digest':HEX}}
    obligation={'type':'object','additionalProperties':False,'required':['obligation_id','dimension','question','blocking','source_refs','subject_binding'],'properties':{
      'obligation_id':{'type':'string','minLength':1},'dimension':{'enum':model['technical_preflight_dimensions']},'question':{'type':'string','minLength':1},'blocking':{'type':'boolean'},'source_refs':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},'subject_binding':subject_binding}}
    route_space={'type':'object','additionalProperties':False,'required':['owner','candidate_set_exhaustive','codex_alternative_route_allowed','required_dimensions','obligations','candidate_routes','route_change_boundaries'],'properties':{
      'owner':{'const':'WEB_BRAIN'},'candidate_set_exhaustive':{'const':False},'codex_alternative_route_allowed':{'const':True},
      'required_dimensions':{'type':'array','items':{'enum':model['technical_preflight_dimensions']},'minItems':1,'uniqueItems':True},
      'obligations':{'type':'array','items':obligation,'minItems':1},'candidate_routes':{'type':'array','items':route,'minItems':1,'maxItems':3},
      'route_change_boundaries':{'type':'object','additionalProperties':False,'required':['may_execute_without_reclosure','must_return_for_reclosure'],'properties':{
        'may_execute_without_reclosure':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True},
        'must_return_for_reclosure':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True}}}}}
    execution_object={'type':'object','additionalProperties':False,'required':['object_type','source_mode','object_id','expected_ref_or_sha256','source_material_refs'],'properties':{
      'object_type':{'enum':['REPOSITORY','ARTIFACT']},'source_mode':{'enum':['REPOSITORY_REF','EXISTING_PR_HEAD','EXISTING_ARTIFACT','NEW_ARTIFACT']},
      'object_id':{'type':['string','null']},'expected_ref_or_sha256':{'type':['string','null']},
      'source_material_refs':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True}}}
    task_object_lifecycle={'type':'object','additionalProperties':False,'required':['lifecycle_version','route_type','approved_input_object','discovery_object','approved_execution_boundary','expected_result_contract','lifecycle_digest'],'properties':{
      'lifecycle_version':{'const':1},'route_type':{'enum':['REPOSITORY_CHANGE','EXISTING_PR_REPLAY','REPOSITORY_DISCOVERY','ARTIFACT_REPAIR','NEW_ARTIFACT']},
      'approved_input_object':{'type':'object'},'discovery_object':{'type':'object'},'approved_execution_boundary':{'type':'object'},'expected_result_contract':{'type':'object'},'lifecycle_digest':HEX}}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'joyflow://codex-handoff-projection-v8','type':'object','additionalProperties':False,'required':req,'properties':{
      'artifact_type':{'const':'CODEX_HANDOFF_PROJECTION'},'projection_version':{'const':8},'build_identity':{'type':'object'},'project_id':{'type':'string','minLength':1},'task_id':{'type':'string','minLength':1},'round_id':{'type':'integer','minimum':1},'capsule_id':{'type':'string'},'capsule_digest':HEX,'task_anchor':{'type':'object'},'task_progress':{'type':'object'},'route_profile':{'enum':list(model['route_profiles'])},'execution_mode':{'enum':model['execution_modes']},'flow_depth':{'type':'string'},'validation_depth':{'type':'string'},'task_classification':{'type':'object'},'material_semantics':{'type':'array'},'repository_evidence':{'type':'object'},
      'current_source_context':{'type':'object','additionalProperties':False,'required':['problem_reality','context_status','historical_retrieval_refs','selected_paths','current_product_mutation_paths','review_coverage_paths','impact_coverage','excluded_context','unresolved_questions','expansion_triggers','source_binding'],'properties':{
        'problem_reality':{'enum':['NOT_APPLICABLE','CHANGE_REQUIRED','PARTIAL_CHANGE_REQUIRED','NO_CHANGE_REQUIRED','CANNOT_DETERMINE_BLOCKED']},
        'context_status':{'enum':['NOT_APPLICABLE','DISCOVERY_ONLY','SUFFICIENT','INCOMPLETE_BLOCKED']},
        'historical_retrieval_refs':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
        'selected_paths':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
        'current_product_mutation_paths':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
        'review_coverage_paths':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
        'impact_coverage':{'type':'array','items':{'type':'object','additionalProperties':False,'required':['dimension','status','evidence_refs','applicability_basis'],'properties':{'dimension':{'enum':['DIRECT_IMPLEMENTATION','DIRECT_CALLERS','INTERFACES_SCHEMA','DATA_STATE_BOUNDARIES','SHARED_CORE','RELEVANT_TESTS','RUNTIME_CHAIN']},'status':{'enum':['CHECKED','NOT_APPLICABLE','UNRESOLVED']},'evidence_refs':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},'applicability_basis':{'type':'string','minLength':1}}},'uniqueItems':True},
        'excluded_context':{'type':'array','items':{'type':'object','additionalProperties':False,'required':['item','basis','reopen_when'],'properties':{'item':{'type':'string','minLength':1},'basis':{'type':'string','minLength':1},'reopen_when':{'type':'string','minLength':1}}},'uniqueItems':True},
        'unresolved_questions':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
        'expansion_triggers':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True},
        'source_binding':{'type':'object','additionalProperties':False,'required':['repository_id','baseline_commit','final_path_decision_digest'],'properties':{'repository_id':{'type':['string','null']},'baseline_commit':{'type':['string','null']},'final_path_decision_digest':{'type':['string','null']}}}}},
      'decision_boundary':{'type':'object'},'validation':{'type':'object'},'traceability':{'type':'array'},'derived_gates':{'type':'object'},
      'codex_technical_authority':{'type':'object','additionalProperties':False,'required':['role','may_decide_without_reapproval','must_stop_when','cannot'],'properties':{'role':{'const':'BOUNDED_EXECUTION_TECHNICAL_AUTHORITY'},'may_decide_without_reapproval':{'type':'array','items':{'type':'string'},'minItems':1,'uniqueItems':True},'must_stop_when':{'type':'array','items':{'type':'string'},'minItems':1,'uniqueItems':True},'cannot':{'type':'array','items':{'type':'string'},'minItems':1,'uniqueItems':True}}},
      'technical_route_space':route_space,'execution_object':execution_object,'task_object_lifecycle':task_object_lifecycle,'delivery':{'type':'object'},'stop_conditions':{'type':'array'},'projection_digest':HEX}}

def approval_schema(model):
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'joyflow://approval-binding-v3','type':'object','additionalProperties':False,'required':model['approval_requirements']['binding_fields'],'properties':{k:HEX for k in model['approval_requirements']['binding_fields']}}

def codex_return_schema():
    machine={'type':'object','additionalProperties':False,'required':['obligation_id','check_id','actual_command','actual_argv','actual_cwd_scope','exit_code','result','evidence_ref'],'properties':{'obligation_id':{'type':'string'},'check_id':{'type':'string'},'actual_command':{'type':'string'},'actual_argv':{'type':'array','minItems':1,'items':{'type':'string','minLength':1}},'actual_cwd_scope':{'const':'SOURCE_ROOT'},'exit_code':{'type':['integer','null']},'result':{'enum':['PASS','FAIL','NOT_RUN']},'evidence_ref':{'type':'string'}}}
    pr={'type':'object','additionalProperties':False,'required':['repository_id','base_branch','working_branch','pr_url','base_commit','head_sha','touched_files','diff_evidence_ref'],'properties':{'repository_id':{'type':'string','minLength':1},'base_branch':{'type':'string','minLength':1},'working_branch':{'type':'string','minLength':1},'pr_url':{'type':'string','minLength':1},'base_commit':{'type':'string','minLength':1},'head_sha':{'type':'string','minLength':1},'touched_files':{'type':'array','minItems':1,'items':{'type':'string','minLength':1},'uniqueItems':True},'diff_evidence_ref':{'type':'string','minLength':1}}}
    replay={'type':'object','additionalProperties':False,'required':['evidence_role','repository_id','pr_number','pr_url','base_branch','working_branch','base_commit','frozen_head_sha','review_coverage_paths','diff_evidence_ref','source_state_before_evidence_ref','source_state_after_evidence_ref'],'properties':{
      'evidence_role':{'const':'EXISTING_FROZEN_PR_REVIEW_TARGET'},'repository_id':{'type':'string','minLength':1},'pr_number':{'type':'integer','minimum':1},'pr_url':{'type':'string','minLength':1},
      'base_branch':{'type':'string','minLength':1},'working_branch':{'type':'string','minLength':1},'base_commit':{'type':'string','minLength':1},'frozen_head_sha':{'type':'string','minLength':1},
      'review_coverage_paths':{'type':'array','minItems':1,'items':{'type':'string','minLength':1},'uniqueItems':True},'diff_evidence_ref':{'type':'string','minLength':1},
      'source_state_before_evidence_ref':{'type':'string','minLength':1},'source_state_after_evidence_ref':{'type':'string','minLength':1}}}
    artifact_output={'type':'object','additionalProperties':False,'required':['artifact_id','artifact_digest','bytes','media_type','role','validation_evidence_refs'],'properties':{
      'artifact_id':{'type':'string','minLength':1},'artifact_digest':HEX,'bytes':{'type':'integer','minimum':0},
      'media_type':{'type':'string','minLength':1},'role':{'type':'string','minLength':1},
      'validation_evidence_refs':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True}}}
    artifact={'type':'object','additionalProperties':False,'required':['outputs','output_set_digest'],'properties':{
      'outputs':{'type':'array','items':artifact_output,'minItems':1},'output_set_digest':HEX}}
    obj={'type':'object','additionalProperties':False,'required':['object_type','source_mode','object_id','ref_or_sha256'],'properties':{'object_type':{'enum':['REPOSITORY','ARTIFACT']},'source_mode':{'enum':['REPOSITORY_REF','EXISTING_PR_HEAD','EXISTING_ARTIFACT','NEW_ARTIFACT']},'object_id':{'type':['string','null']},'ref_or_sha256':{'type':['string','null']}}}
    obligation_result={'type':'object','additionalProperties':False,'required':['obligation_id','dimension','subject_digest','result','finding_summary','evidence_refs'],'properties':{'obligation_id':{'type':'string','minLength':1},'dimension':{'type':'string','minLength':1},'subject_digest':HEX,'result':{'enum':['PASS','FAIL','NOT_APPLICABLE']},'finding_summary':{'type':'string','minLength':1},'evidence_refs':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True}}}
    candidate_eval={'type':'object','additionalProperties':False,'required':['route_id','feasibility','evidence_refs','rejection_reason'],'properties':{'route_id':{'type':'string','minLength':1},'feasibility':{'enum':['PASS','FAIL','PARTIAL','NOT_EVALUATED']},'evidence_refs':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True},'rejection_reason':{'type':['string','null']}}}
    selected={'type':'object','additionalProperties':False,'required':['source','route_id','implementation_summary','evidence_refs'],'properties':{'source':{'enum':['BRAIN_CANDIDATE','CODEX_ALTERNATIVE']},'route_id':{'type':'string','minLength':1},'implementation_summary':{'type':'string','minLength':1},'evidence_refs':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True}}}
    alternative={'oneOf':[{'type':'object','additionalProperties':False,'required':['route_id','summary','why_better_than_candidates','product_semantics_unchanged','approved_paths_sufficient','important_tradeoff_changed','protocol_or_compatibility_changed','migration_required','evidence_refs'],'properties':{'route_id':{'type':'string','minLength':1},'summary':{'type':'string','minLength':1},'why_better_than_candidates':{'type':'string','minLength':1},'product_semantics_unchanged':{'type':'boolean'},'approved_paths_sufficient':{'type':'boolean'},'important_tradeoff_changed':{'type':'boolean'},'protocol_or_compatibility_changed':{'type':'boolean'},'migration_required':{'type':'boolean'},'evidence_refs':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True}}},{'type':'null'}]}
    material={'type':'object','additionalProperties':False,'required':['product_behavior_changed','protocol_or_schema_semantics_changed','approved_paths_expanded','migration_required','compatibility_commitment_changed','user_visible_result_changed','important_tradeoff_changed'],'properties':{k:{'type':'boolean'} for k in ['product_behavior_changed','protocol_or_schema_semantics_changed','approved_paths_expanded','migration_required','compatibility_commitment_changed','user_visible_result_changed','important_tradeoff_changed']}}
    objection={'oneOf':[{'type':'object','additionalProperties':False,'required':['finding_id','failed_obligation_ids','finding_derivation_refs','technical_conflict','minimum_correct_route','additional_paths_required'],'properties':{'finding_id':{'type':'string','minLength':1},'failed_obligation_ids':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True},'finding_derivation_refs':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True},'technical_conflict':{'type':'string','minLength':1},'minimum_correct_route':{'type':'string','minLength':1},'additional_paths_required':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True}}},{'type':'null'}]}
    preflight={'type':'object','additionalProperties':False,'required':['status','expected_execution_object','observed_execution_object','object_observation_evidence_ref','obligation_results','candidate_evaluations','selected_route','alternative_route','material_change_assessment','execution_decision','implementation_decisions','objection'],'properties':{
      'status':{'enum':['ROUTE_CONFIRMED','EQUIVALENT_IMPLEMENTATION_ADJUSTMENT','BRAIN_ROUTE_CONFLICT','APPROVAL_SCOPE_INSUFFICIENT','REPOSITORY_STATE_MISMATCH']},
      'expected_execution_object':obj,'observed_execution_object':obj,'object_observation_evidence_ref':{'type':'string','minLength':1},
      'obligation_results':{'type':'array','items':obligation_result,'minItems':1},'candidate_evaluations':{'type':'array','items':candidate_eval,'minItems':1},
      'selected_route':{'oneOf':[selected,{'type':'null'}]},'alternative_route':alternative,'material_change_assessment':material,
      'execution_decision':{'enum':['EXECUTE','STOP_FOR_BRAIN_RECLOSURE']},'implementation_decisions':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},'objection':objection}}
    mutation={'type':'object','additionalProperties':False,'required':['mutation_performed','cleanup_status','residual_changed_paths'],'properties':{'mutation_performed':{'type':'boolean'},'cleanup_status':{'enum':['NOT_REQUIRED','PENDING','COMPLETED']},'residual_changed_paths':{'type':'array','items':{'type':'string'},'uniqueItems':True}}}
    lifecycle_result={'type':'object','additionalProperties':False,'required':['approved_lifecycle_digest','transition_status','execution_result_object','final_validation_object','transition_digest'],'properties':{
      'approved_lifecycle_digest':HEX,'transition_status':{'enum':['RESULT_VALIDATED','BLOCKED_BEFORE_VALIDATED_RESULT']},
      'execution_result_object':{'oneOf':[{'type':'object'},{'type':'null'}]},'final_validation_object':{'oneOf':[{'type':'object'},{'type':'null'}]},'transition_digest':HEX}}
    schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'joyflow://codex-execution-return-v8','type':'object','additionalProperties':False,'required':['artifact_type','project_id','task_id','round_id','capsule_digest','projection_digest','evidence_bundle_digest','technical_preflight','execution_status','execution_lifecycle_result','machine_results','pr_evidence','repository_replay_evidence','artifact_evidence','blocker_evidence_refs','mutation_summary','unresolved_items','brain_review_status','user_acceptance_status','merge_status','return_digest'],'properties':{
      'artifact_type':{'const':'CODEX_EXECUTION_RETURN'},'project_id':{'type':'string','minLength':1},'task_id':{'type':'string','minLength':1},'round_id':{'type':'integer','minimum':1},'capsule_digest':HEX,'projection_digest':HEX,'evidence_bundle_digest':HEX,
      'technical_preflight':preflight,'execution_status':{'enum':['COMPLETED','BLOCKED']},'execution_lifecycle_result':lifecycle_result,'machine_results':{'type':'array','items':machine},
      'pr_evidence':{'oneOf':[pr,{'type':'null'}]},'repository_replay_evidence':{'oneOf':[replay,{'type':'null'}]},'artifact_evidence':{'oneOf':[artifact,{'type':'null'}]},
      'blocker_evidence_refs':{'type':'array','items':{'type':'string'},'uniqueItems':True},'mutation_summary':mutation,'unresolved_items':{'type':'array','items':{'type':'string'},'uniqueItems':True},
      'brain_review_status':{'const':'PENDING_BRAIN_REVIEW'},'user_acceptance_status':{'const':'PENDING_USER_ACCEPTANCE'},'merge_status':{'const':'NOT_AUTHORIZED'},'return_digest':HEX}}
    schema['allOf']=[
      {
        'if':{'properties':{'pr_evidence':{'type':'object'}},'required':['pr_evidence']},
        'then':{'properties':{
          'repository_replay_evidence':{'type':'null'},
          'mutation_summary':{'properties':{'mutation_performed':{'const':True}}},
        }},
      },
      {
        'if':{'properties':{'repository_replay_evidence':{'type':'object'}},'required':['repository_replay_evidence']},
        'then':{'properties':{
          'pr_evidence':{'type':'null'},
          'mutation_summary':{'properties':{'mutation_performed':{'const':False},'residual_changed_paths':{'maxItems':0}}},
        }},
      },
    ]
    return schema

def evidence_bundle_schema(model):
    obj={'type':'object','additionalProperties':False,'required':['object_type','source_mode','object_id','ref_or_sha256'],'properties':{'object_type':{'enum':['REPOSITORY','ARTIFACT']},'source_mode':{'enum':['REPOSITORY_REF','EXISTING_PR_HEAD','EXISTING_ARTIFACT','NEW_ARTIFACT']},'object_id':{'type':['string','null']},'ref_or_sha256':{'type':['string','null']}}}
    capture={'type':'object','additionalProperties':False,'required':['capture_id','tool','capture_kind','command','exit_code','stdout','stderr','stdout_bytes_base64','stderr_bytes_base64','stdout_sha256','stderr_sha256','observed_object','observation','subject_type','subject_id','capture_sha256'],'properties':{
      'capture_id':{'type':'string','minLength':1},'tool':{'const':'joyflow-typed-execution-evidence-runner'},'capture_kind':{'enum':['REPOSITORY_HEAD','REPOSITORY_COMMIT','REPOSITORY_STATE','ARTIFACT_SHA256','SOURCE_MATERIAL_SET','REPOSITORY_FILE','REPOSITORY_DIFF','TEST_COMMAND']},'command':{'type':'string','minLength':1},'exit_code':{'type':'integer'},'stdout':{'type':'string'},'stderr':{'type':'string'},'stdout_bytes_base64':{'type':'string'},'stderr_bytes_base64':{'type':'string'},'stdout_sha256':HEX,'stderr_sha256':HEX,'observed_object':obj,'observation':{'type':'object'},'subject_type':{'type':'string','minLength':1},'subject_id':{'type':'string','minLength':1},'capture_sha256':HEX}}
    evidence={'type':'object','additionalProperties':False,'required':['evidence_id','authority','kind','ref','claim','claim_digest','produced_by','subject_type','subject_id','raw_output_ref','raw_output_sha256'],'properties':{
      'evidence_id':{'type':'string','minLength':1},'authority':{'const':'EXECUTION_EVIDENCE'},'kind':{'enum':['REPOSITORY_HEAD_OBSERVATION','REPOSITORY_COMMIT_OBSERVATION','REPOSITORY_STATE_OBSERVATION','ARTIFACT_SHA256_OBSERVATION','SOURCE_MATERIAL_SET_OBSERVATION','REPOSITORY_FILE_SNAPSHOT','REPOSITORY_DIFF','TEST_RESULT']},'ref':{'type':'string','minLength':1},'claim':{'type':'string','minLength':1},'claim_digest':HEX,'produced_by':{'const':'TOOL'},'subject_type':{'type':'string','minLength':1},'subject_id':{'type':'string','minLength':1},'raw_output_ref':{'type':'string','minLength':1},'raw_output_sha256':HEX}}
    derivation={'type':'object','additionalProperties':False,'required':['derivation_id','authority','kind','claim','claim_digest','produced_by','subject_type','subject_id','source_evidence_refs'],'properties':{
      'derivation_id':{'type':'string','minLength':1},'authority':{'const':'EXECUTION_EVIDENCE'},'kind':{'enum':['PREFLIGHT_OBLIGATION_DERIVATION','ROUTE_CANDIDATE_DERIVATION','SELECTED_ROUTE_DERIVATION','CODEX_ALTERNATIVE_DERIVATION','TECHNICAL_OBJECTION_DERIVATION']},'claim':{'type':'string','minLength':1},'claim_digest':HEX,'produced_by':{'const':'CODEX'},'subject_type':{'type':'string','minLength':1},'subject_id':{'type':'string','minLength':1},'source_evidence_refs':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True}}}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'joyflow://codex-execution-evidence-bundle-v3','type':'object','additionalProperties':False,'required':['artifact_type','project_id','task_id','round_id','capsule_digest','projection_digest','raw_captures','evidence_rows','derivation_rows','evidence_bundle_digest'],'properties':{
      'artifact_type':{'const':'CODEX_EXECUTION_EVIDENCE_BUNDLE'},'project_id':{'type':'string','minLength':1},'task_id':{'type':'string','minLength':1},'round_id':{'type':'integer','minimum':1},'capsule_digest':HEX,'projection_digest':HEX,
      'raw_captures':{'type':'array','items':capture,'minItems':1},'evidence_rows':{'type':'array','items':evidence,'minItems':1},'derivation_rows':{'type':'array','items':derivation,'minItems':1},'evidence_bundle_digest':HEX}}

def path_discovery_return_schema(model):
    path_row={'type':'object','additionalProperties':False,'required':['path_id','path','role','evidence_ref'],'properties':{'path_id':{'type':'string','minLength':1},'path':{'type':'string','minLength':1},'role':{'type':'string','minLength':1},'evidence_ref':{'type':'string','minLength':1}}}
    candidate={'type':'object','additionalProperties':False,'required':['path_id','path','why_relevant','confidence','evidence_ref'],'properties':{'path_id':{'type':'string','minLength':1},'path':{'type':'string','minLength':1},'why_relevant':{'type':'string','minLength':1},'confidence':{'enum':['HIGH','MEDIUM','LOW']},'evidence_ref':{'type':'string','minLength':1}}}
    edge={'type':'object','additionalProperties':False,'required':['edge_id','from','to','relation','evidence_ref'],'properties':{'edge_id':{'type':'string','minLength':1},'from':{'type':'string','minLength':1},'to':{'type':'string','minLength':1},'relation':{'type':'string','minLength':1},'evidence_ref':{'type':'string','minLength':1}}}
    validation={'type':'object','additionalProperties':False,'required':['validation_id','path','command','evidence_ref'],'properties':{'validation_id':{'type':'string','minLength':1},'path':{'type':'string','minLength':1},'command':{'type':'string','minLength':1},'evidence_ref':{'type':'string','minLength':1}}}
    finding={'type':'object','additionalProperties':False,'required':['finding_id','finding','affected_paths','evidence_ref'],'properties':{'finding_id':{'type':'string','minLength':1},'finding':{'type':'string','minLength':1},'affected_paths':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True},'evidence_ref':{'type':'string','minLength':1}}}
    evidence={'type':'object','additionalProperties':False,'required':['evidence_id','authority','kind','ref','claim','claim_digest','produced_by','subject_type','subject_id','observed_path','source_sha256','source_evidence_refs','raw_output_ref','raw_output_sha256'],'properties':{
      'evidence_id':{'type':'string','minLength':1},'authority':{'const':'EXECUTION_EVIDENCE'},
      'kind':{'enum':['GIT_STATE_FINGERPRINT','PATH_OBSERVATION','SOURCE_SNAPSHOT_OBSERVATION','PATH_CANDIDATE_DERIVATION','DEPENDENCY_DERIVATION','VALIDATION_ENTRY_DERIVATION','LOCAL_FINDING_DERIVATION','STRUCTURAL_RELATION_DERIVATION','ARCHITECTURE_ROUTE_DERIVATION']},
      'ref':{'type':'string','minLength':1},'claim':{'type':'string','minLength':1},'claim_digest':HEX,
      'produced_by':{'enum':['TOOL','CODEX']},'subject_type':{'enum':['PATH_DISCOVERY_CAPTURE','REPOSITORY_PATH','REPOSITORY_SOURCE_SNAPSHOT','REPOSITORY_PATH_CANDIDATE','DEPENDENCY_EDGE','VALIDATION_ENTRY','LOCAL_FINDING','STRUCTURAL_RELATION','ARCHITECTURE_ROUTE']},'subject_id':{'type':'string','minLength':1},
      'observed_path':{'oneOf':[{'type':'string','minLength':1},{'type':'null'}]},'source_sha256':{'oneOf':[HEX,{'type':'null'}]},
      'source_evidence_refs':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
      'raw_output_ref':{'oneOf':[{'type':'string','minLength':1},{'type':'null'}]},'raw_output_sha256':{'oneOf':[HEX,{'type':'null'}]}}}
    fingerprint={'type':'object','additionalProperties':False,'required':['capture_id','capture_phase','head_commit','index_diff_sha256','worktree_diff_sha256','untracked_manifest_sha256','declared_ignored_manifest_sha256','evidence_ref','state_fingerprint_sha256','capture_record_digest'],'properties':{'capture_id':{'type':'string','minLength':1},'capture_phase':{'enum':['BEFORE','AFTER']},'head_commit':{'type':'string','minLength':1},'index_diff_sha256':HEX,'worktree_diff_sha256':HEX,'untracked_manifest_sha256':HEX,'declared_ignored_manifest_sha256':HEX,'evidence_ref':{'type':'string','minLength':1},'state_fingerprint_sha256':HEX,'capture_record_digest':HEX}}
    recursive_dir={'type':'object','additionalProperties':False,'required':['root','exclusions'],'properties':{'root':{'type':'string','minLength':1},'exclusions':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True}}}
    ignored={'type':'object','additionalProperties':False,'required':['mode','exact_files','exact_symlinks','recursive_directories','coverage_status','full_local_filesystem_unchanged_claim'],'properties':{
      'mode':{'const':'DECLARED_EXECUTION_RELEVANT_ONLY'},
      'exact_files':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
      'exact_symlinks':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
      'recursive_directories':{'type':'array','items':recursive_dir,'uniqueItems':True},
      'coverage_status':{'enum':['COMPLETE_FOR_DECLARED_EXECUTION_RELEVANT_PATHS','READ_ONLY_COVERAGE_INCOMPLETE']},'full_local_filesystem_unchanged_claim':{'const':False}}}
    relation={'type':'object','additionalProperties':False,'required':['relation_id','relation_type','subject','source','semantic_claim','basis_evidence_refs','materiality','evidence_ref'],'properties':{
      'relation_id':{'type':'string','minLength':1},'relation_type':{'enum':['AUTHORITY_WRITER','RULE_OWNERSHIP','LIFECYCLE_TRANSITION','DEPENDENCY','SHARED_CORE','RUNTIME_RELATION','PROJECTION_CACHE_RELATION','CONSUMER_PRODUCER','OTHER_MATERIAL_RELATION']},
      'subject':{'type':'string','minLength':1},'source':{'type':'string','minLength':1},'semantic_claim':{'type':'string','minLength':1},
      'basis_evidence_refs':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True},'materiality':{'enum':['MATERIAL','SUPPORTING']},'evidence_ref':{'type':'string','minLength':1}}}
    closure={'type':'object','additionalProperties':False,'required':['dimension','status','evidence_refs','unresolved_reason'],'properties':{
      'dimension':{'enum':['AUTHORITY_BOUNDARY','RULE_OWNERSHIP','LIFECYCLE','DEPENDENCY','SHARED_CORE','RUNTIME_RELATION','VALIDATION_SURFACE']},'status':{'enum':['CHECKED','NOT_APPLICABLE','UNRESOLVED']},
      'evidence_refs':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},'unresolved_reason':{'oneOf':[{'type':'string','minLength':1},{'type':'null'}]}}}
    route={'type':'object','additionalProperties':False,'required':['route_id','summary','advantages','known_costs','known_risks','evidence_refs','evidence_ref'],'properties':{
      'route_id':{'type':'string','minLength':1},'summary':{'type':'string','minLength':1},'advantages':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True},
      'known_costs':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},'known_risks':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
      'evidence_refs':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True},'evidence_ref':{'type':'string','minLength':1}}}
    question={'type':'object','additionalProperties':False,'required':['question_id','statement','materiality_basis','goal_binding_digest','closure_dimensions'],'properties':{
      'question_id':{'type':'string','minLength':1},'statement':{'type':'string','minLength':1},'materiality_basis':{'type':'string','minLength':1},'goal_binding_digest':HEX,
      'closure_dimensions':{'type':'array','items':{'enum':['AUTHORITY_BOUNDARY','RULE_OWNERSHIP','LIFECYCLE','DEPENDENCY','SHARED_CORE','RUNTIME_RELATION','VALIDATION_SURFACE']},'minItems':1,'uniqueItems':True}}}
    task_projection={'type':'object','additionalProperties':False,'required':['status','material_relation_ids','counterevidence_refs','unresolved_questions','omitted_material_summary'],'properties':{
      'status':{'enum':['NOT_APPLICABLE','CLOSED','INCOMPLETE']},'material_relation_ids':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
      'counterevidence_refs':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},'unresolved_questions':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
      'omitted_material_summary':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True}}}
    structural={'type':'object','additionalProperties':False,'required':['mode','architecture_question','semantic_relations','closure_obligations','counterevidence_refs','unresolved_structural_questions','omitted_material_summary','candidate_routes','recommended_route_id','task_structural_projection'],'properties':{
      'mode':{'enum':['NOT_APPLICABLE','GOAL_CONDITIONED']},'architecture_question':{'oneOf':[question,{'type':'null'}]},'semantic_relations':{'type':'array','items':relation},'closure_obligations':{'type':'array','items':closure},
      'counterevidence_refs':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},'unresolved_structural_questions':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
      'omitted_material_summary':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},'candidate_routes':{'type':'array','items':route},'recommended_route_id':{'oneOf':[{'type':'string','minLength':1},{'type':'null'}]},'task_structural_projection':task_projection}}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'joyflow://path-discovery-return-v6','type':'object','additionalProperties':False,'required':['artifact_type','project_id','task_id','round_id','capsule_digest','projection_digest','repository','ignored_path_coverage','repository_state_before','repository_state_after','confirmed_paths','candidate_paths','dependency_edges','validation_entries','local_only_findings','structural_discovery','unresolved_questions','evidence_rows','mutation_performed','return_digest'],'properties':{
      'artifact_type':{'const':'PATH_DISCOVERY_RETURN'},'project_id':{'type':'string','minLength':1},'task_id':{'type':'string','minLength':1},'round_id':{'type':'integer','minimum':1},'capsule_digest':HEX,'projection_digest':HEX,
      'repository':{'type':'object','additionalProperties':False,'required':['repository_id','github_ref'],'properties':{'repository_id':{'type':'string','minLength':1},'github_ref':{'type':'string','pattern':r'^github:[^@\s]+@[^\s]+$'}}},
      'ignored_path_coverage':ignored,'repository_state_before':fingerprint,'repository_state_after':fingerprint,
      'confirmed_paths':{'type':'array','items':path_row},'candidate_paths':{'type':'array','items':candidate},'dependency_edges':{'type':'array','items':edge},'validation_entries':{'type':'array','items':validation},'local_only_findings':{'type':'array','items':finding},'structural_discovery':structural,'unresolved_questions':{'type':'array','items':{'type':'string'}},'evidence_rows':{'type':'array','items':evidence,'minItems':1},'mutation_performed':{'const':False},'return_digest':HEX}}

def long_term_structural_projection_schema():
    source_ref={'type':'object','additionalProperties':False,'required':['path','source_sha256'],'properties':{'path':{'type':'string','minLength':1},'source_sha256':HEX}}
    anchor={'type':'object','additionalProperties':False,'required':['anchor_id','anchor_type','statement','epistemic_status','source_refs'],'properties':{
      'anchor_id':{'type':'string','minLength':1},'anchor_type':{'enum':['LIFECYCLE','AUTHORITY_BOUNDARY','RULE_OWNER','SHARED_CORE','DEPENDENCY_BOUNDARY','STRUCTURAL_EXCEPTION']},
      'statement':{'type':'string','minLength':1},'epistemic_status':{'enum':['OBSERVED','INFERRED','UNRESOLVED']},'source_refs':{'type':'array','items':source_ref,'minItems':1,'uniqueItems':True}}}
    fiber={'type':'object','additionalProperties':False,'required':['fiber_id','fiber_type','from_anchor','to_anchor','statement','epistemic_status','source_refs'],'properties':{
      'fiber_id':{'type':'string','minLength':1},'fiber_type':{'enum':['OWNS','DEPENDS_ON','CONSUMES','PRODUCES','PART_OF_LIFECYCLE','DERIVES_FROM','CONSTRAINS','EXCEPTION_TO']},
      'from_anchor':{'type':'string','minLength':1},'to_anchor':{'type':'string','minLength':1},'statement':{'type':'string','minLength':1},'epistemic_status':{'enum':['OBSERVED','INFERRED','UNRESOLVED']},
      'source_refs':{'type':'array','items':source_ref,'minItems':1,'uniqueItems':True}}}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'joyflow://long-term-structural-projection-v1','type':'object','additionalProperties':False,
      'required':['artifact_type','projection_version','artifact_role','repository_id','based_on_commit','review_status','structural_anchors','semantic_fibers','counterevidence_refs','unresolved','material_omissions','projection_digest'],
      'properties':{'artifact_type':{'const':'LONG_TERM_STRUCTURAL_PROJECTION'},'projection_version':{'const':1},'artifact_role':{'const':'DERIVED_NON_AUTHORITATIVE_STRUCTURAL_NAVIGATION'},
        'repository_id':{'type':'string','minLength':1},'based_on_commit':{'type':'string','minLength':1},'review_status':{'const':'BRAIN_REVIEWED_DERIVED_PROJECTION'},
        'structural_anchors':{'type':'array','items':anchor},'semantic_fibers':{'type':'array','items':fiber},'counterevidence_refs':{'type':'array','items':source_ref,'uniqueItems':True},
        'unresolved':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},'material_omissions':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},'projection_digest':HEX}}

def github_path_evidence_schema():
    scope={'type':'object','additionalProperties':False,'required':['scope_type','object_path','observed_paths','observed_paths_digest','raw_object_sha256','scope_digest'],'properties':{
      'scope_type':{'enum':['EXACT_FILE','PATH_SET']},
      'object_path':{'oneOf':[{'type':'string','minLength':1},{'type':'null'}]},
      'observed_paths':{'type':'array','minItems':1,'uniqueItems':True,'items':{'type':'string','minLength':1}},
      'observed_paths_digest':HEX,'raw_object_sha256':HEX,'scope_digest':HEX}}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'joyflow://github-path-evidence-v3','type':'object','additionalProperties':False,'required':['artifact_type','evidence_id','repository_id','object_type','object_ref','observed_commit_or_head','base_ref','head_ref','scope','raw_evidence_ref','evidence_digest'],'properties':{
      'artifact_type':{'const':'GITHUB_PATH_EVIDENCE'},'evidence_id':{'type':'string','minLength':1},'repository_id':{'type':'string','minLength':1},'object_type':{'enum':['REPOSITORY_TREE','FILE','COMMIT','PR_DIFF']},'object_ref':{'type':'string','pattern':r'^github:[^@\s]+@[^\s]+$'},'observed_commit_or_head':{'type':'string','minLength':1},
      'base_ref':{'oneOf':[{'type':'string','minLength':1},{'type':'null'}]},'head_ref':{'oneOf':[{'type':'string','minLength':1},{'type':'null'}]},
      'scope':scope,'raw_evidence_ref':{'type':'string','minLength':1},'evidence_digest':HEX}}

def final_path_decision_schema():
    item={'type':'object','additionalProperties':False,
      'required':['path','basis_type','source_github_path_evidence_ids','derived_from_paths','supporting_evidence_refs','source_path_discovery_return_digest','source_return_path_ids','source_return_dependency_ids','source_return_validation_ids','source_return_finding_ids','derivation_summary'],
      'properties':{
        'path':{'type':'string','minLength':1},
        'basis_type':{'enum':['GITHUB_CONFIRMED','GITHUB_DERIVED','LOCAL_DISCOVERY','COMBINED','BRAIN_TASK_DERIVATION']},
        'source_github_path_evidence_ids':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
        'derived_from_paths':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
        'supporting_evidence_refs':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
        'source_path_discovery_return_digest':{'oneOf':[HEX,{'type':'null'}]},
        'source_return_path_ids':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
        'source_return_dependency_ids':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
        'source_return_validation_ids':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
        'source_return_finding_ids':{'type':'array','items':{'type':'string','minLength':1},'uniqueItems':True},
        'derivation_summary':{'type':'string','minLength':1}}}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'joyflow://final-path-decision-v3','type':'object','additionalProperties':False,
      'required':['artifact_type','owner','project_id','task_id','round_id','repository_id','baseline_commit','allowed_path_items','unresolved_path_questions','decision_digest'],
      'properties':{
        'artifact_type':{'const':'FINAL_PATH_DECISION'},'owner':{'const':'WEB_BRAIN'},'project_id':{'type':'string','minLength':1},
        'task_id':{'type':'string','minLength':1},'round_id':{'type':'integer','minimum':1},'repository_id':{'type':'string','minLength':1},
        'baseline_commit':{'type':'string','minLength':1},'allowed_path_items':{'type':'array','items':item},
        'unresolved_path_questions':{'type':'array','items':{'type':'string'}},'decision_digest':HEX}}

def merge_gate_schema():
    # Optional diagnostic snapshot only. Merge authorization comes from the exact
    # USER decision bound to the frozen candidate and acceptance Capsule; this
    # snapshot is never a predecessor object required by merge or completion.
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'joyflow://merge-gate-derived-snapshot-v3','type':'object','additionalProperties':False,'required':['artifact_type','artifact_role','status','owner','project_id','task_id','round_id','repository_id','pr_url','reviewed_head_sha','merge_candidate_freeze_digest','user_acceptance_status','user_acceptance_capsule_digest','user_merge_authorization_digest','derivation_basis','record_digest'],'properties':{
      'artifact_type':{'const':'MERGE_GATE_RECORD'},'artifact_role':{'const':'DERIVED_GATE_SNAPSHOT_ONLY'},'status':{'enum':['MERGE_READY','MERGE_ALLOWED']},'owner':{'const':'WEB_BRAIN'},'project_id':{'type':'string','minLength':1},'task_id':{'type':'string','minLength':1},'round_id':{'type':'integer','minimum':1},'repository_id':{'type':'string','minLength':1},'pr_url':{'type':'string','minLength':1},'reviewed_head_sha':{'type':'string','minLength':1},'merge_candidate_freeze_digest':HEX,'user_acceptance_status':{'enum':['PASS','NOT_APPLICABLE']},'user_acceptance_capsule_digest':HEX,'user_merge_authorization_digest':{'oneOf':[HEX,{'type':'null'}]},'derivation_basis':{'enum':['CURRENT_FREEZE_AND_ACCEPTANCE','CURRENT_FREEZE_ACCEPTANCE_AND_USER_AUTHORIZATION']},'record_digest':HEX},
      'allOf':[
        {'if':{'properties':{'status':{'const':'MERGE_READY'}}},'then':{'properties':{'user_merge_authorization_digest':{'type':'null'},'derivation_basis':{'const':'CURRENT_FREEZE_AND_ACCEPTANCE'}}}},
        {'if':{'properties':{'status':{'const':'MERGE_ALLOWED'}}},'then':{'properties':{'user_merge_authorization_digest':HEX,'derivation_basis':{'const':'CURRENT_FREEZE_ACCEPTANCE_AND_USER_AUTHORIZATION'}}}}
      ]}

def pointer_schema():
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'joyflow://task-completion-pointer-v4','type':'object','additionalProperties':False,'required':['artifact_type','status','owner','project_id','task_id','round_id','task_capsule_id','repository_id','pr_url','reviewed_head_sha','merge_candidate_freeze_digest','user_acceptance_capsule_digest','user_merge_authorization_digest','merge_commit','repository_evidence_ref','result','pointer_digest'],'properties':{
      'artifact_type':{'const':'TASK_COMPLETION_POINTER'},'status':{'const':'MERGE_OBSERVED'},'owner':{'const':'WEB_BRAIN'},'project_id':{'type':'string','minLength':1},'task_id':{'type':'string','minLength':1},'round_id':{'type':'integer','minimum':1},'task_capsule_id':{'type':'string','minLength':1},'repository_id':{'type':'string','minLength':1},'pr_url':{'type':'string','minLength':1},'reviewed_head_sha':{'type':'string','minLength':1},'merge_candidate_freeze_digest':HEX,'user_acceptance_capsule_digest':HEX,'user_merge_authorization_digest':HEX,'merge_commit':{'type':'string','minLength':7},'repository_evidence_ref':{'type':'string','minLength':1},'result':{'const':'MERGED_REPOSITORY_RESULT'},'pointer_digest':HEX}}

def evidence_transport_receipt_schema(include_meta=True):
    props={
      'artifact_type':{'const':'EVIDENCE_TRANSPORT_RECEIPT'},'transport_mode':{'const':'GITHUB_EXACT_OBJECT'},'transport_role':{'const':'CURRENT_ROUND_EVIDENCE_BUNDLE_TRANSPORT_ONLY'},
      'project_id':{'type':'string','minLength':1},'task_id':{'type':'string','minLength':1},'round_id':{'type':'integer','minimum':1},'evidence_bundle_digest':HEX,
      'repository_id':{'type':'string','minLength':1},'exact_commit_sha':{'type':'string','pattern':'^[0-9a-f]{40,64}$'},'exact_path':{'type':'string','minLength':1},
      'object_bytes':{'type':'integer','minimum':1},'object_sha256':HEX,'object_encoding':{'const':'CANONICAL_JSON_UTF8'},'temporary_ref':{'type':'string','pattern':'^refs/heads/joyflow-evidence/[A-Za-z0-9._/-]+$'},
      'retention_policy':{'enum':['EPHEMERAL_BY_DEFAULT','EXCEPTIONAL_RETAIN_MATERIAL_NON_REPRODUCIBLE']},'cleanup_trigger':{'enum':['TASK_TERMINAL','NOT_APPLICABLE_RETAINED']},'receipt_digest':HEX}
    body={'type':'object','additionalProperties':False,'required':list(props),'properties':props}
    return ({'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'joyflow://evidence-transport-receipt-v2',**body} if include_meta else body)


def current_pr_review_input_transport_schema():
    entry={'type':'object','additionalProperties':False,'required':['object_role','artifact_type','exact_path','bytes','sha256','semantic_digest_field_name','semantic_digest'],'properties':{
      'object_role':{'enum':['CODEX_HANDOFF_PROJECTION','CODEX_EXECUTION_RETURN','CODEX_EXECUTION_EVIDENCE_BUNDLE','BRAIN_REVIEW_CAPSULE']},
      'artifact_type':{'enum':['CODEX_HANDOFF_PROJECTION','CODEX_EXECUTION_RETURN','CODEX_EXECUTION_EVIDENCE_BUNDLE','FIBERED_TASK_CAPSULE']},
      'exact_path':{'type':'string','pattern':'^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9._/-]+$'},
      'bytes':{'type':'integer','minimum':1},'sha256':HEX,
      'semantic_digest_field_name':{'enum':['projection_digest','return_digest','evidence_bundle_digest','capsule_digest']},
      'semantic_digest':HEX}}
    props={
      'artifact_type':{'const':'CURRENT_PR_REVIEW_INPUT_TRANSPORT_LOCATOR'},'locator_version':{'const':1},'owner':{'const':'TOOL'},
      'repository_id':{'type':'string','minLength':1},'pr_number':{'type':'integer','minimum':1},
      'base_sha':{'type':'string','pattern':'^[0-9a-f]{40,64}$'},'source_head_sha':{'type':'string','pattern':'^[0-9a-f]{40,64}$'},
      'transport_kind':{'const':'CURRENT_PR_REVIEW_INPUT_TRANSPORT'},
      'temporary_ref':{'type':'string','pattern':'^refs/heads/joyflow-evidence/[A-Za-z0-9._/-]+$'},
      'exact_transport_commit':{'type':'string','pattern':'^[0-9a-f]{40,64}$'},
      'retention_policy':{'const':'EPHEMERAL_BY_DEFAULT'},'cleanup_action':{'const':'DELETE_EXACT_TEMPORARY_REF'},
      'object_entries':{'type':'array','items':entry,'minItems':4,'maxItems':4},'locator_digest':HEX}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'joyflow://current-pr-review-input-transport-v1','type':'object','additionalProperties':False,'required':list(props),'properties':props}


def current_pr_review_transport_cleanup_continuation_schema():
    props={
      'artifact_type':{'const':'CURRENT_PR_REVIEW_TRANSPORT_CLEANUP_CONTINUATION'},'owner':{'const':'WEB_BRAIN'},
      'authority_basis':{'const':'ORIGINAL_USER_APPROVED_EXECUTION_AND_CURRENT_TASK_TERMINAL_EVIDENCE'},
      'project_id':{'type':'string','minLength':1},'task_id':{'type':'string','minLength':1},'round_id':{'type':'integer','minimum':1},
      'source_projection_digest':HEX,'source_user_approval_decision_ref':{'type':'string','minLength':1},'source_locator_digest':HEX,
      'transport_repository_id':{'type':'string','minLength':1},'temporary_ref':{'type':'string','pattern':'^refs/heads/joyflow-evidence/[A-Za-z0-9._/-]+$'},
      'expected_ref_commit':{'type':'string','pattern':'^[0-9a-f]{40,64}$'},'terminal_basis':{'const':'TASK_TERMINAL_EVIDENCE'},
      'task_terminal_status':{'enum':['MERGED','COMPLETED_NO_PR','REJECTED','ABANDONED','CANCELLED','SUPERSEDED']},
      'terminal_evidence_ref':{'type':'string','minLength':1},'terminal_evidence_digest':HEX,
      'cleanup_action':{'const':'DELETE_EXACT_TEMPORARY_REF'},'background_service_used':{'const':False},
      'user_mediated_handoff_required':{'const':True},'continuation_digest':HEX}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'joyflow://current-pr-review-transport-cleanup-continuation-v1','type':'object','additionalProperties':False,'required':list(props),'properties':props}



def evidence_transport_cleanup_continuation_schema():
    props={
      'artifact_type':{'const':'EVIDENCE_TRANSPORT_CLEANUP_CONTINUATION'},'owner':{'const':'WEB_BRAIN'},
      'authority_basis':{'const':'ORIGINAL_USER_APPROVED_EXECUTION_AND_CURRENT_TASK_TERMINAL_EVIDENCE'},
      'project_id':{'type':'string','minLength':1},'task_id':{'type':'string','minLength':1},'round_id':{'type':'integer','minimum':1},
      'source_projection_digest':HEX,'source_user_approval_decision_ref':{'type':'string','minLength':1},'source_transport_receipt_digest':HEX,
      'transport_repository_id':{'type':'string','minLength':1},'temporary_ref':{'type':'string','pattern':'^refs/heads/joyflow-evidence/[A-Za-z0-9._/-]+$'},'expected_ref_commit':{'type':'string','pattern':'^[0-9a-f]{40,64}$'},
      'terminal_basis':{'const':'TASK_TERMINAL_EVIDENCE'},'task_terminal_status':{'enum':['MERGED','COMPLETED_NO_PR','REJECTED','ABANDONED','CANCELLED','SUPERSEDED']},
      'terminal_evidence_ref':{'type':'string','minLength':1},'terminal_evidence_digest':HEX,
      'cleanup_action':{'const':'DELETE_EXACT_TEMPORARY_REF'},'background_service_used':{'const':False},'user_mediated_handoff_required':{'const':True},'continuation_digest':HEX}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'joyflow://evidence-transport-cleanup-continuation-v2','type':'object','additionalProperties':False,'required':list(props),'properties':props}

def evidence_transport_plan_schema():
    surface={'type':'object','additionalProperties':False,'required':['repository_id','temporary_ref','path_prefix','side_effect_status','side_effect_basis'],'properties':{
      'repository_id':{'type':'string','minLength':1},'temporary_ref':{'type':'string','pattern':'^refs/heads/joyflow-evidence/[A-Za-z0-9._/-]+$'},'path_prefix':{'type':'string','minLength':1},
      'side_effect_status':{'enum':['NONE','EXPLICITLY_INCLUDED_IN_APPROVED_EXECUTION_OBJECT']},'side_effect_basis':{'type':'string','minLength':1}}}
    cleanup={'type':'object','additionalProperties':False,'required':['trigger','action','preauthorized','background_service_forbidden'],'properties':{
      'trigger':{'enum':['TASK_TERMINAL','NOT_APPLICABLE_RETAINED']},'action':{'enum':['DELETE_EXACT_TEMPORARY_REF','NO_DELETE_RETAINED']},'preauthorized':{'type':'boolean'},'background_service_forbidden':{'const':True}}}
    return {'type':'object','additionalProperties':False,'required':['mode','transport_role','github_surface','trigger_conditions','retention_policy','retention_reason','cleanup','fallback_mode','product_pr_promotion_forbidden','product_main_or_development_branch_forbidden'],'properties':{
      'mode':{'enum':['INLINE','GITHUB_EXACT_OBJECT_IF_NEEDED','MANUAL_FALLBACK']},'transport_role':{'const':'CURRENT_ROUND_EVIDENCE_BUNDLE_TRANSPORT_ONLY'},'github_surface':{'oneOf':[surface,{'type':'null'}]},
      'trigger_conditions':{'type':'array','items':{'enum':['EVIDENCE_TOO_LARGE_FOR_CHAT','CHAT_TRUNCATION_RISK','BRAIN_REQUIRES_RAW_PACKAGE']},'uniqueItems':True},
      'retention_policy':{'enum':['EPHEMERAL_BY_DEFAULT','EXCEPTIONAL_RETAIN_MATERIAL_NON_REPRODUCIBLE']},'retention_reason':{'oneOf':[{'type':'string','minLength':1},{'type':'null'}]},
      'cleanup':cleanup,'fallback_mode':{'enum':['INLINE','MANUAL_FALLBACK']},'product_pr_promotion_forbidden':{'const':True},'product_main_or_development_branch_forbidden':{'const':True}}}

def current_review_transport_plan_schema():
    surface={'type':'object','additionalProperties':False,'required':['repository_id','temporary_ref','path_prefix','side_effect_status','side_effect_basis'],'properties':{
      'repository_id':{'type':'string','minLength':1},'temporary_ref':{'type':'string','pattern':'^refs/heads/joyflow-evidence/[A-Za-z0-9._/-]+$'},'path_prefix':{'type':'string','minLength':1},
      'side_effect_status':{'enum':['NONE','EXPLICITLY_INCLUDED_IN_APPROVED_EXECUTION_OBJECT']},'side_effect_basis':{'type':'string','minLength':1}}}
    cleanup={'type':'object','additionalProperties':False,'required':['trigger','action','preauthorized','background_service_forbidden'],'properties':{
      'trigger':{'enum':['TASK_TERMINAL','NOT_APPLICABLE_RETAINED']},'action':{'enum':['DELETE_EXACT_TEMPORARY_REF','NO_DELETE_RETAINED']},'preauthorized':{'type':'boolean'},'background_service_forbidden':{'const':True}}}
    return {'type':'object','additionalProperties':False,'required':['mode','transport_role','github_surface','retention_policy','retention_reason','cleanup','fallback_mode','product_pr_promotion_forbidden','product_main_or_development_branch_forbidden'],'properties':{
      'mode':{'enum':['INLINE','GITHUB_EXACT_OBJECT_IF_NEEDED','MANUAL_FALLBACK']},'transport_role':{'const':'CURRENT_PR_REVIEW_INPUT_TRANSPORT'},
      'github_surface':{'oneOf':[surface,{'type':'null'}]},'retention_policy':{'enum':['EPHEMERAL_BY_DEFAULT','EXCEPTIONAL_RETAIN_MATERIAL_NON_REPRODUCIBLE']},
      'retention_reason':{'oneOf':[{'type':'string','minLength':1},{'type':'null'}]},'cleanup':cleanup,'fallback_mode':{'enum':['INLINE','MANUAL_FALLBACK']},
      'product_pr_promotion_forbidden':{'const':True},'product_main_or_development_branch_forbidden':{'const':True}}}

def phase2u_projection_schema(schema):
    schema['$id']='joyflow://codex-handoff-projection-v9'
    trs=schema['properties']['technical_route_space']
    trs['required']=['planning_mode','source_structural_route_binding']+trs['required']
    trs['properties']['planning_mode']={'enum':['BRAIN_BOUNDED_FAST_PATH','CODEX_STRUCTURAL_ROUTE_BRAIN_ACCEPTED']}
    bind={'type':'object','additionalProperties':False,'required':['source_structural_return_digest','structural_question_id','source_route_id','brain_disposition_digest'],'properties':{'source_structural_return_digest':HEX,'structural_question_id':{'type':'string','minLength':1},'source_route_id':{'type':'string','minLength':1},'brain_disposition_digest':HEX}}
    trs['properties']['source_structural_route_binding']={'oneOf':[bind,{'type':'null'}]}
    return schema

def phase2w_projection_schema(schema):
    schema['$id']='joyflow://codex-handoff-projection-v11'
    schema['properties']['delivery']={'type':'object','additionalProperties':False,'required':['execution_mode','mutation_allowed','return_artifact_type','requires_pr','candidate_is_not_canonical','merge_requires_separate_user_decision','automatic_promotion_forbidden','return_contract','evidence_transport'],'properties':{
      'execution_mode':{'enum':['MUTATING','READ_ONLY','NONE']},'mutation_allowed':{'type':'boolean'},'return_artifact_type':{'type':'string','minLength':1},'requires_pr':{'type':'boolean'},
      'candidate_is_not_canonical':{'const':True},'merge_requires_separate_user_decision':{'const':True},'automatic_promotion_forbidden':{'const':True},
      'return_contract':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True},'evidence_transport':evidence_transport_plan_schema(),
      'current_review_transport':current_review_transport_plan_schema()} }
    return schema

def phase2w_codex_return_schema(schema):
    schema['$id']='joyflow://codex-execution-return-v11'
    schema['required'].insert(schema['required'].index('blocker_evidence_refs'),'evidence_transport_receipt')
    schema['properties']['evidence_transport_receipt']={'oneOf':[evidence_transport_receipt_schema(False),{'type':'null'}]}
    return schema

def phase2u_codex_return_schema(schema):
    schema['$id']='joyflow://codex-execution-return-v9'
    result={'type':'object','additionalProperties':False,'required':['status','approved_structural_closure_digest','actual_consequences','deviation_reason'],'properties':{
      'status':{'enum':['NOT_APPLICABLE','PRESERVED','DEVIATION_DETECTED']},
      'approved_structural_closure_digest':{'oneOf':[HEX,{'type':'null'}]},
      'actual_consequences':{'type':'array','items':{'type':'object','additionalProperties':False,'required':['consequence_id','statement','materiality','evidence_refs'],'properties':{'consequence_id':{'type':'string','minLength':1},'statement':{'type':'string','minLength':1},'materiality':{'enum':['MATERIAL','SUPPORTING']},'evidence_refs':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True}}},'uniqueItems':True},
      'deviation_reason':{'oneOf':[{'type':'string','minLength':1},{'type':'null'}]}}}
    schema['required'].insert(schema['required'].index('unresolved_items'),'structural_execution_result')
    schema['properties']['structural_execution_result']=result
    return schema

def phase2u_path_discovery_return_schema(schema):
    schema['$id']='joyflow://path-discovery-return-v7'
    structural=schema['properties']['structural_discovery']
    q=structural['properties']['architecture_question']['oneOf'][0]
    q['required'].append('frame_digest'); q['properties']['frame_digest']=HEX
    closure=structural['properties']['closure_obligations']['items']
    closure['required'].append('applicability_basis')
    closure['properties']['applicability_basis']={'oneOf':[{'type':'string','minLength':1},{'type':'null'}]}
    return schema

def phase2u_long_term_structural_projection_schema(schema):
    schema['$id']='joyflow://long-term-structural-projection-v2'
    schema['required']=[x for x in schema['required'] if x!='review_status']
    schema['required'][schema['required'].index('structural_anchors'):schema['required'].index('structural_anchors')]=['scope','coverage_basis']
    schema['properties'].pop('review_status',None)
    schema['properties']['scope']={'type':'object','additionalProperties':False,'required':['statement','covered_surfaces'],'properties':{'statement':{'type':'string','minLength':1},'covered_surfaces':{'type':'array','items':{'type':'string','minLength':1},'minItems':1,'uniqueItems':True}}}
    schema['properties']['coverage_basis']={'type':'object','additionalProperties':False,'required':['source_structural_closure_digest','source_review_ref'],'properties':{'source_structural_closure_digest':HEX,'source_review_ref':{'type':'string','minLength':1}}}
    return schema

def phase2u_final_path_decision_schema(schema):
    schema['$id']='joyflow://final-path-decision-v4'
    schema['required'].insert(schema['required'].index('decision_digest'),'structural_closure_binding')
    bind={'type':'object','additionalProperties':False,'required':['status','source_structural_return_digest','structural_question_id','source_route_id','brain_disposition_digest'],'properties':{
      'status':{'enum':['NOT_REQUIRED','CLOSED']},
      'source_structural_return_digest':{'oneOf':[HEX,{'type':'null'}]},
      'structural_question_id':{'oneOf':[{'type':'string','minLength':1},{'type':'null'}]},
      'source_route_id':{'oneOf':[{'type':'string','minLength':1},{'type':'null'}]},
      'brain_disposition_digest':{'oneOf':[HEX,{'type':'null'}]}}}
    schema['properties']['structural_closure_binding']=bind
    return schema

def generated_registry(model):
    lines=['# GENERATED DUAL-LAYER MECHANICAL REGISTRY','', '> Generated from `machine/joyflow_dual_layer_model.yaml`. Do not edit manually.','']
    for title,key in [('Architecture','architecture'),('Route profiles','route_profiles'),('Evidence authority','evidence_kinds_by_authority'),('Repository fact slots','repository_fact_slot_policy'),('Risk and domain routing','risk_minimum_route'),('Human semi-automatic merge boundary','merge_boundary'),('Single active task round','single_active_round'),('Hybrid path discovery','path_discovery_policy'),('Codex bounded technical authority','codex_technical_authority'),('Stage gate requirements','stage_gate_requirements'),('Phase 1 stage lineage policy','phase1_stage_policy'),('GitHub CI mechanical gate','github_ci_mechanical_gate'),('Legacy migration truthfulness','legacy_migration_truth_policy'),('Candidate capability claims','candidate_capability_claim_policy')]:
        lines += [f'## {title}','','```yaml',yaml.safe_dump({key:model[key]},sort_keys=False,allow_unicode=True).rstrip(),'```','']
    lines += ['## Mechanical invariants','']
    for row in model['invariants']:
        lines += [f"canonical_rule_id: {row['id']}",f"source_section_id: 03::INVARIANT::{row['id']}",'',f"Generated mechanical invariant implemented by `{row['implementation']}`.",'']
    return '\n'.join(lines)

def generated_rule_index():
    rows=[]
    for path in sorted((ROOT/'project_sources').glob('*.md')):
        text=read_canonical_text(path)
        rules=list(RULE_RE.finditer(text)); sections=list(SECTION_RE.finditer(text))
        if len(rules)!=len(sections):
            raise ValueError(f'{path.name}: rule/section count mismatch')
        rows.extend((rule.group(1),sections[i].group(1).strip(),path.name) for i,rule in enumerate(rules))
    lines=['# GENERATED RULE INDEX','', '> Generated from active Project Sources. Do not edit manually.','', '| canonical_rule_id | source_section_id | source |','|---|---|---|']
    for rid,sec,src in sorted(rows):
        lines.append(f'| `{rid}` | `{sec}` | `{src}` |')
    lines.append('')
    return '\n'.join(lines)

def outputs(model):
    return {
      ROOT/'schemas'/'fibered_task_capsule.schema.json':dump_json(capsule_schema(model)),
      ROOT/'schemas'/'codex_handoff_projection.schema.json':dump_json(phase2w_projection_schema(phase2u_projection_schema(projection_schema(model)))),
      ROOT/'schemas'/'approval_view.schema.json':dump_json(approval_schema(model)),
      ROOT/'schemas'/'codex_execution_return.schema.json':dump_json(phase2w_codex_return_schema(phase2u_codex_return_schema(codex_return_schema()))),
      ROOT/'schemas'/'codex_execution_evidence_bundle.schema.json':dump_json(evidence_bundle_schema(model)),
      ROOT/'schemas'/'path_discovery_return.schema.json':dump_json(phase2u_path_discovery_return_schema(path_discovery_return_schema(model))),
      ROOT/'schemas'/'long_term_structural_projection.schema.json':dump_json(phase2u_long_term_structural_projection_schema(long_term_structural_projection_schema())),
      ROOT/'schemas'/'github_path_evidence.schema.json':dump_json(github_path_evidence_schema()),
      ROOT/'schemas'/'evidence_transport_receipt.schema.json':dump_json(evidence_transport_receipt_schema()),
      ROOT/'schemas'/'evidence_transport_cleanup_continuation.schema.json':dump_json(evidence_transport_cleanup_continuation_schema()),
      ROOT/'schemas'/'current_pr_review_input_transport.schema.json':dump_json(current_pr_review_input_transport_schema()),
      ROOT/'schemas'/'current_pr_review_transport_cleanup_continuation.schema.json':dump_json(current_pr_review_transport_cleanup_continuation_schema()),
      ROOT/'schemas'/'final_path_decision.schema.json':dump_json(phase2u_final_path_decision_schema(final_path_decision_schema())),
      ROOT/'schemas'/'merge_gate_record.schema.json':dump_json(merge_gate_schema()),
      ROOT/'schemas'/'task_completion_pointer.schema.json':dump_json(pointer_schema()),
      ROOT/'project_sources'/'03_GENERATED_DUAL_LAYER_REGISTRY.md':generated_registry(model),
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--check',action='store_true'); args=ap.parse_args(); model=yaml.safe_load(read_canonical_text(MODEL_PATH)); bad=[]
    for path,text in outputs(model).items():
        if args.check:
            if not canonical_text_matches(path,text): bad.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True,exist_ok=True); write_canonical_text(path,text)
    try:
        index_text=generated_rule_index()
    except ValueError as exc:
        print(f'GENERATED_ASSET_SOURCE_ERROR: {exc}',file=sys.stderr); return 2
    index_path=ROOT/'project_sources'/'12_GENERATED_RULE_INDEX.md'
    if args.check:
        if not canonical_text_matches(index_path,index_text):
            bad.append(str(index_path.relative_to(ROOT)))
    else:
        write_canonical_text(index_path,index_text)
    if bad: print('GENERATED_ASSET_DRIFT: '+', '.join(bad),file=sys.stderr); return 2
    return 0
if __name__=='__main__': raise SystemExit(main())
