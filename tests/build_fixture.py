from __future__ import annotations
import argparse, base64, copy, hashlib, importlib.util, json, pathlib, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('compiler',ROOT/'runtime/joyflow_dual_layer.py')
c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
canonical_spec=importlib.util.spec_from_file_location('canonical_text',ROOT/'tools/canonical_text.py')
canonical_text=importlib.util.module_from_spec(canonical_spec); canonical_spec.loader.exec_module(canonical_text)
write_canonical_text=canonical_text.write_canonical_text

VALIDATION_ARGV=['python','-c',"import pathlib,sys; assert pathlib.Path('runtime/joyflow_dual_layer.py').is_file(); sys.stdout.buffer.write(b'joyflow-validation-ok\\n')"]
VALIDATION_COMMAND=c._canonical_argv(VALIDATION_ARGV)
_ACTIVE_SOURCE_MATERIALS=[]


def evidence(eid, authority, kind, ref, claim, produced_by, subject_type, subject_id, raw_output_ref=None):
    return {'evidence_id':eid,'authority':authority,'kind':kind,'ref':ref,'claim':claim,'claim_digest':None,
            'produced_by':produced_by,'subject_type':subject_type,'subject_id':subject_id,'raw_output_ref':raw_output_ref}


def ev(effect_id, kind, value, check_ids=None):
    row={'effect_id':effect_id,'effect_type':kind,'value':value,'effect_digest':None}
    if kind=='VALIDATE':
        row.update({'evidence_kind':'MACHINE','validation_mode':'MACHINE','check_ids':check_ids or ['CHECK_UNIT'],'human_validation_ids':[]})
    return row


def item(i,t,m,effects,prov,status='USER_CONFIRMED',material='CURRENT_SLICE',derivation=None):
    row={'item_id':i,'item_type':t,'meaning':m,'meaning_digest':None,'status':status,'provenance_refs':[prov],
         'material_class':material,'risk_markers':['NONE'],'domain_lanes':['GENERAL'],'effects':effects,'relations':{}}
    if derivation: row['derivation']=derivation
    return row


def base_items():
    rows=[
      item('GOAL_DUAL_LAYER','GOAL','Joyflow uses repository canonical state for long-term project truth and a temporary task capsule for current-task closure.',[
        ev('E_GOAL_VISIBLE','USER_VISIBLE_RESULT','The repaired package expresses a repository-anchored dual-layer closure model.'),
        ev('E_GOAL_DO','MUST_DO','Implement the Repository Canonical State, temporary Fibered Task Capsule, and high-fidelity Projection Gate.'),
        ev('E_GOAL_VALIDATE','VALIDATE','The package mechanically separates persistent repository truth from temporary task state.')],'E_USER_MODEL'),
      item('RULE_TEMP_CAPSULE','PRODUCT_RULE','The task capsule is temporary and must not become a second project truth source.',[
        ev('E_TEMP_PRESERVE','MUST_PRESERVE','The repository remains the only persistent project truth.'),
        ev('E_TEMP_NOT','MUST_NOT_DO','Do not persist the full task capsule as project canonical state.'),
        ev('E_TEMP_VALIDATE','VALIDATE','Post-merge retention is limited to a minimal result pointer when useful.')],'E_USER_TEMP'),
      item('RULE_CONTINUITY','PRODUCT_RULE','Task continuity prevents ordinary packet mismatch but does not claim an immutable or adversary-proof history.',[
        ev('E_CONT_DO','MUST_DO','Bind revisions and repairs to the exact prior packet when a new revision is sealed.'),
        ev('E_CONT_VALIDATE','VALIDATE','A changed packet cannot silently reuse the prior packet identity or approval binding.')],'E_USER_CONTINUITY'),
      item('RULE_TRANSPORT','PRODUCT_RULE','Material semantics must generate exact boundary and validation obligations through typed effects.',[
        ev('E_TRANSPORT_DO','MUST_DO','Generate boundary obligations and validation obligations as digest-bound projections of semantic effects.'),
        ev('E_TRANSPORT_VALIDATE','VALIDATE','Contradictory or unbound boundaries and validation cases are rejected.')],'E_COLD_REVIEW','BRAIN_INFERENCE',derivation='Derived from prior stranger cold review and the confirmed high-fidelity transport goal.'),
      item('RULE_REPOSITORY_READINESS','PRODUCT_RULE','Repository execution requires confirmed repository-relative paths and task-specific evidence slots.',[
        ev('E_REPO_DO','MUST_DO','Require confirmed allowed paths and task-specific repository fact slots before repository execution.'),
        ev('E_REPO_VALIDATE','VALIDATE','Brain reads GitHub first; only materially missing local or runtime path facts route to bounded Codex read-only discovery; missing or authority-mismatched repository evidence blocks execution.')],'E_COLD_REVIEW','BRAIN_INFERENCE',derivation='Derived from repository boundary bypasses and the approved minimal fact-slot compromise.'),
      item('RULE_HYBRID_PATH_DISCOVERY','PRODUCT_RULE','Path discovery is GitHub-first; Codex supplements only materially missing local or runtime facts, and the Brain owns the final path boundary.',[
        ev('E_PATH_DISCOVERY_DO','MUST_DO','Use current GitHub repository evidence first; request bounded local read-only discovery only when GitHub is insufficient or unavailable.'),
        ev('E_PATH_DISCOVERY_NOT','MUST_NOT_DO','Codex must not mutate the repository or decide final allowed paths during local discovery.'),
        ev('E_PATH_DISCOVERY_VALIDATE','VALIDATE','A read-only Path Discovery Return binds the current Projection and declares mutation_performed false.')],'E_USER_PATH_DISCOVERY'),
      item('RULE_CODEX_TECHNICAL_AUTHORITY','PRODUCT_RULE','Codex is the bounded execution technical authority for current repository and runtime facts; it may choose equivalent implementation details within the approved semantics and paths, and must stop with evidence when the Brain route is technically wrong or the approved scope is insufficient.',[
        ev('E_CODEX_AUTHORITY_DO','MUST_DO','Perform an internal technical preflight in the same execution turn and record any equivalent implementation decisions.'),
        ev('E_CODEX_AUTHORITY_NOT','MUST_NOT_DO','Do not change product semantics, architecture, approved paths, Brain review, user states or merge authority.'),
        ev('E_CODEX_AUTHORITY_VALIDATE','VALIDATE','A blocked technical objection is source-bound, may omit PR or artifact evidence, and cannot be promoted by Brain review to PASS.')],'E_USER_CODEX_AUTHORITY'),
      item('RULE_APPROVAL','PRODUCT_RULE','Mutation/material execution requires explicit user approval of the exact current object; bounded pure read-only Codex discovery instead uses exact Web Brain authorization and creates no user approval state. Codex may never elevate either authorization state.',[
        ev('E_APPROVAL_DO','MUST_DO','Bind mutation/material execution as APPROVED_FINAL/CURRENT_EXPLICIT_USER_DECISION, while READ_ONLY_DISCOVERY binds AUTHORIZED_READ_ONLY_DISCOVERY/WEB_BRAIN_BOUNDED_READ_ONLY_DISCOVERY_AUTHORIZATION.'),
        ev('E_APPROVAL_VALIDATE','VALIDATE','The Runtime validates route-appropriate authorization ownership and exact binding; read-only Brain authorization cannot authorize mutation and mutation still requires current explicit user approval.')],'E_USER_AUTHORIZATION_POLICY'),
      item('RULE_MERGE','PRODUCT_RULE','Execution approval does not authorize merge; Brain review, user acceptance and a separate user merge decision remain human semi-automatic gates.',[
        ev('E_MERGE_PRESERVE','MUST_PRESERVE','A candidate PR is never treated as repository canonical state.'),
        ev('E_MERGE_NOT','MUST_NOT_DO','Codex and the execution compiler must not merge or set MERGE_ALLOWED.'),
        ev('E_MERGE_VALIDATE','VALIDATE','Merge records are owned by the Web Brain and bind the exact reviewed PR head and current user merge decision.')],'E_USER_MERGE'),
      item('RULE_SINGLE_ACTIVE_ROUND','PRODUCT_RULE','Each material reclosure / authorization cycle has one current task; each same-cycle execution attempt has one current Projection, Codex Return and Evidence Bundle.',[
        ev('E_SINGLE_ROUND_DO','MUST_DO','Bind project, task, round, Projection, Codex Return and Evidence Bundle as one current-round object chain.'),
        ev('E_SINGLE_ROUND_VALIDATE','VALIDATE','An earlier round or different packet cannot substitute for the current round, and no global scheduler is introduced.')],'E_USER_SINGLE_TASK'),
      item('RULE_GATE_BLOCKING','PRODUCT_RULE','Derived Gates must block illegal stage progress rather than merely display status.',[
        ev('E_GATE_DO','MUST_DO','Require the corresponding PASS gates before entering Brain review, user acceptance, merge decision or task closure.'),
        ev('E_GATE_VALIDATE','VALIDATE','A BLOCK, NEEDS_BRAIN_REVIEW or NEEDS_USER_ACCEPTANCE state prevents the next material stage.')],'E_COLD_REVIEW','BRAIN_INFERENCE',derivation='Derived from the latest stranger cold review finding that blocked gates could still advance.'),
      item('RULE_EVIDENCE_BUNDLE','PRODUCT_RULE','Codex Return and raw execution evidence form one digest-bound current-round Evidence Bundle.',[
        ev('E_BUNDLE_DO','MUST_DO','Bind the Codex Return to the exact current-round Evidence Bundle digest and validation-check subjects.'),
        ev('E_BUNDLE_VALIDATE','VALIDATE','Replacing the Evidence Bundle or using a prior-round object invalidates the Return and Brain review binding.')],'E_COLD_REVIEW','BRAIN_INFERENCE',derivation='Derived from ordinary Return/Evidence file mismatch risk.'),
      item('RULE_REVIEW_SPLIT','PRODUCT_RULE','Repository and Artifact execution use different review targets without changing Brain or user authority.',[
        ev('E_REVIEW_SPLIT_DO','MUST_DO','Review repository work against a PR head and Artifact work against artifact identity, digest and validation evidence.'),
        ev('E_REVIEW_SPLIT_VALIDATE','VALIDATE','Artifact repair closes without fabricated PR evidence; repository work cannot use an Artifact target.')],'E_COLD_REVIEW','BRAIN_INFERENCE',derivation='Derived from the Artifact review dead-end in the prior candidate.'),
      item('RULE_MERGE_CONTINUITY','PRODUCT_RULE','Final USER merge authorization binds the exact Merge Candidate Freeze and applicable post-freeze User Acceptance; a changed PR head invalidates the prior freeze and authorization.',[
        ev('E_MERGE_CONT_DO','MUST_DO','Carry the exact current Projection, Return, Evidence Bundle, Brain Review and PR CI into the Merge Candidate Freeze, then bind applicable User Acceptance and final USER merge authorization to that exact freeze.'),
        ev('E_MERGE_CONT_VALIDATE','VALIDATE','A merge authorization bound to another freeze, acceptance disposition or PR head is rejected; MERGE_READY / MERGE_ALLOWED are derived results only.')],'E_COLD_REVIEW','BRAIN_INFERENCE',derivation='Derived from ordinary merge object-binding mismatch risk.'),
      item('NON_GOAL_AUTOMATION','NON_GOAL','User identity authentication, immutable event chains, trusted observer services and automatic promotion are outside the current Joyflow architecture.',[
        ev('E_AUTO_NOT','MUST_NOT_DO','Do not add user signatures, immutable event databases, trusted GitHub observers or automatic merge/promotion.'),
        ev('E_AUTO_VALIDATE','VALIDATE','The package explicitly marks these mechanisms outside the current threat model and makes no completion claim for them.')],'E_USER_AUTOMATION'),
      item('NON_GOAL_CONTEXT','NON_GOAL','Repository Cache, persistent capsule memory and long-term repository context remain deferred.',[
        ev('E_CONTEXT_NOT','MUST_NOT_DO','Do not implement Repository Cache, persistent capsule memory or long-term repository context in Phase 1.'),
        ev('E_CONTEXT_VALIDATE','VALIDATE','The package marks repository-context systems as deferred and makes no completion claim for them.')],'E_USER_DEFER')
    ]
    for row in rows:
        if row['item_id'].startswith('RULE_'): row['relations']={'required_by':['GOAL_DUAL_LAYER']}
    rows[0]['relations']={'depends_on':[r['item_id'] for r in rows if r['item_id'].startswith('RULE_')], 'validated_by':['RULE_TRANSPORT']}
    return rows


def github_path_fixture():
    scope={'scope_type':'PATH_SET','object_path':None,'observed_paths':['runtime/**','tests/**'],'observed_paths_digest':None,'raw_object_sha256':c.digest('fixture-github-tree-object'),'scope_digest':None}
    scope['observed_paths_digest']=c.digest(sorted(scope['observed_paths']))
    row={'artifact_type':'GITHUB_PATH_EVIDENCE','evidence_id':'E_GITHUB_PATHS','repository_id':'example/repo','object_type':'REPOSITORY_TREE','object_ref':'github:example/repo@abc123','observed_commit_or_head':'abc123','base_ref':None,'head_ref':None,'scope':scope,'raw_evidence_ref':'github:example/repo@abc123:path-discovery','evidence_digest':None}
    scope['scope_digest']=c.digest(c._github_scope_payload(row))
    row['evidence_digest']=c.digest(c.strip_digest(row,'evidence_digest'))
    source=evidence('E_GITHUB_PATHS','REPOSITORY_EVIDENCE','GITHUB_TREE_SNAPSHOT',row['raw_evidence_ref'],c._github_scope_claim(row),'WEB_BRAIN','GITHUB_OBJECT',row['object_ref'],row['raw_evidence_ref'])
    source['claim_digest']=c.digest(source['claim']); source['raw_output_sha256']=scope['raw_object_sha256']
    return row,source

def evidence_registry():
    rows=[
      evidence('E_USER_MODEL','USER_DECISION','PRODUCT_DECISION','conversation:dual-layer-model','User approved the repository-anchored dual-layer direction.','WEB_BRAIN','TASK','TASK_PHASE1_HUMAN_SEMIAUTOMATIC'),
      evidence('E_USER_TEMP','USER_DECISION','PRODUCT_DECISION','conversation:temporary-fibers','Fibers are temporary task activity views.','WEB_BRAIN','TASK','TASK_PHASE1_HUMAN_SEMIAUTOMATIC'),
      evidence('E_USER_CONTINUITY','USER_DECISION','PRODUCT_DECISION','conversation:ordinary-consistency','Packet continuity is ordinary consistency, not an immutable adversarial history.','WEB_BRAIN','TASK','TASK_PHASE1_HUMAN_SEMIAUTOMATIC'),
      evidence('E_USER_AUTHORIZATION_POLICY','USER_DECISION','PRODUCT_DECISION','conversation:approval-boundary','User confirmed the authorization policy: mutation/material execution requires current explicit user approval; bounded pure read-only discovery may be authorized directly by the Web Brain without creating user approval state; execution approval does not authorize final merge, which requires a separate exact-object user decision.','WEB_BRAIN','TASK','TASK_PHASE1_HUMAN_SEMIAUTOMATIC'),
      evidence('E_USER_MERGE','USER_DECISION','PRODUCT_DECISION','conversation:merge-boundary','Execution approval and merge approval are separate human gates.','WEB_BRAIN','TASK','TASK_PHASE1_HUMAN_SEMIAUTOMATIC'),
      evidence('E_USER_PATH_DISCOVERY','USER_DECISION','PRODUCT_DECISION','conversation:github-first-path-discovery','Brain reads GitHub first; Codex only supplements local or runtime facts; Brain owns final allowed paths.','WEB_BRAIN','TASK','TASK_PHASE1E_AI_NATIVE_CHANGE_PROJECTION_REPAIR'),
      evidence('E_USER_SINGLE_TASK','USER_DECISION','PRODUCT_DECISION','conversation:single-active-task-round','Each project executes one current task per round; no same-round competing task model is needed.','WEB_BRAIN','TASK','TASK_PHASE1E_AI_NATIVE_CHANGE_PROJECTION_REPAIR'),
      evidence('E_USER_CODEX_AUTHORITY','USER_DECISION','PRODUCT_DECISION','conversation:codex-bounded-technical-authority','Codex must retain bounded technical judgment, may choose equivalent implementation details, and must stop rather than blindly follow a Brain route that conflicts with direct repository evidence or approved scope.','WEB_BRAIN','TASK','TASK_PHASE1E_AI_NATIVE_CHANGE_PROJECTION_REPAIR'),
      evidence('E_USER_AUTOMATION','USER_DECISION','PRODUCT_DECISION','conversation:no-automatic-promotion','Joyflow is human semi-automatic and does not require identity authentication or automatic promotion.','WEB_BRAIN','TASK','TASK_PHASE1_HUMAN_SEMIAUTOMATIC'),
      evidence('E_USER_DEFER','USER_DECISION','PRODUCT_DECISION','conversation:deferred-context','Repository context systems remain deferred.','WEB_BRAIN','TASK','TASK_PHASE1_HUMAN_SEMIAUTOMATIC'),
      evidence('E_USER_SCENARIO','USER_DECISION','PRODUCT_DECISION','conversation:phase2-operating-scenario','User confirmed that this Joyflow candidate is operated by one Web Brain and one bounded Codex execution layer.','WEB_BRAIN','OPERATING_ASSUMPTION',c.support_subject_id('This candidate is used by one Web Brain and one bounded Codex execution layer.')),
      evidence('E_PRIOR_PHASE1_OBJECT_TRUTH','BRAIN_DERIVATION','COLD_REVIEW','review:phase1-object-truth','Current repository and exact current objects remain authoritative over historical navigation.','WEB_BRAIN','PRIOR_BEHAVIOR','PHASE1_OBJECT_TRUTH'),
      evidence('E_COLD_REVIEW','BRAIN_DERIVATION','COLD_REVIEW','JOYFLOW_PR1A_PR1B_TASK_OBJECT_LIFECYCLE_COMPLETE_STRANGER_COLD_REVIEW_BLOCK.md','The exact shared-lifecycle stranger cold review confirmed the Repository route but found local Discovery source transition, ignored symlink/exclusion facts, complete Artifact output-set continuity and NEW_ARTIFACT execution were not yet closed.','WEB_BRAIN','REVIEW_TARGET','7333ee92ed913cb0f56eb732595c13457eae553289fc532d2d967471fff8a799'),
      github_path_fixture()[1],
      evidence('E_TEST_PLAN','REPOSITORY_EVIDENCE','TEST_DEFINITION','tests/test_phase1_single_active_task_round.py','The candidate defines bounded mechanical tests for its current claims.','TOOL','PACKAGE','JOYFLOW_PHASE1_COMBINED_CAPABILITY_COVERAGE_REPAIR_CANDIDATE'),
    ]
    for dim in ['DIRECT_IMPLEMENTATION','DIRECT_CALLERS','INTERFACES_SCHEMA','DATA_STATE_BOUNDARIES','SHARED_CORE','RELEVANT_TESTS','RUNTIME_CHAIN']:
        rows.append(evidence(f'E_IMPACT_{dim}','REPOSITORY_EVIDENCE','GITHUB_TREE_SNAPSHOT','github:example/repo@abc123:path-discovery',f'Current repository discovery explicitly evaluated impact dimension {dim} for the bounded current task.','WEB_BRAIN','IMPACT_DIMENSION',dim))
    for row in rows: row['claim_digest']=c.digest(row['claim'])
    return rows


def refresh(state):
    for row in state['evidence_registry']: row['claim_digest']=c.digest(row['claim'])
    for row in c.semantic_items(state):
        row['meaning_digest']=c.digest(row['meaning'])
        for eff in row.get('effects',[]): eff['effect_digest']=c.digest(c.strip_digest(eff,'effect_digest'))
    if 'decision_boundary' in state['active_fibers']:
        state['active_fibers']['decision_boundary']['payload']['boundary_obligations']=c.expected_boundary_obligations(state)
    if 'validation' in state['active_fibers']:
        p=state['active_fibers']['validation']['payload']
        p['acceptance_cases']=c.expected_validation_cases(state)
        p['obligation_registry']=c.expected_validation_obligations(state)
        p['mechanical_walkthrough']=c.expected_mechanical_walkthrough(state)
    state['task_classification']=c.expected_classification(c.load_model(),state)
    if 'decision_boundary' in state['active_fibers']:
        model=c.load_model(); space=state['active_fibers']['decision_boundary']['payload'].get('technical_route_space')
        if space:
            for row in space['obligations']:
                row['question']=model['technical_preflight_question_templates'][row['dimension']]
                row['subject_binding']=c.expected_preflight_subject_binding(state,row['dimension'])
    return state


def draft_approval_record(route='PROTOCOL_CHANGE'):
    model=c.load_model(); mode=model['route_profiles'][route]['execution_mode']; scope=model['approval_requirements']['scope_by_execution_mode'][mode]
    if mode=='READ_ONLY':
        return {'status':'NEEDS_BRAIN_READ_ONLY_AUTHORIZATION','owner':'WEB_BRAIN','scope':scope,'basis':'NOT_YET_AUTHORIZED','decision_ref':None,'binding':None}
    return {'status':'NEEDS_USER_APPROVAL','owner':'WEB_BRAIN','scope':scope,'basis':'NOT_YET_APPROVED','decision_ref':None,'binding':None}

def technical_route_space(scope='ARTIFACT_CHANGE'):
    model=c.load_model(); dims=model['technical_preflight_dimensions']; questions=model['technical_preflight_question_templates']
    obligations=[{'obligation_id':f'PREFLIGHT_{d}','dimension':d,'question':questions[d],'blocking':True,'source_refs':['E_USER_CODEX_AUTHORITY'],'subject_binding':{'subject_type':'PENDING','subject_refs':['PENDING'],'subject_digest':'0'*64}} for d in dims]
    paths=['runtime/**'] if scope=='REPOSITORY_CHANGE' else []
    routes=[
      {'route_id':'BRAIN_ROUTE_SOURCE_BOUND_EXTENSION','summary':'Extend the current preflight with task-bound Brain questions, non-exhaustive candidates, typed direct facts, Codex derivations and exact review-source continuity.','expected_mechanisms':['TASK_BOUND_PREFLIGHT','TYPED_DIRECT_FACT','CODEX_TECHNICAL_DERIVATION','EXACT_REVIEW_SNAPSHOT'],'expected_paths':paths,'advantages':['Preserves the existing architecture and limits the change to PR1B.'],'known_costs':['Adds structured subject bindings and typed evidence captures.'],'known_risks':['Schema and fixture drift if generated assets are not rebuilt.'],'important_tradeoff_owner':'CODEX_WITHIN_BOUNDARY'},
      {'route_id':'BRAIN_ROUTE_CONTRACT_REPLACEMENT','summary':'Replace free-form assumption checks with task-bound route evaluation and source-derived review continuity while keeping the same single Brain and Codex layer.','expected_mechanisms':['ROUTE_CANDIDATE_DERIVATION','CODEX_ALTERNATIVE_GATE','SOURCE_DERIVED_REVIEW_SNAPSHOT'],'expected_paths':paths,'advantages':['Prevents unrelated checks and evidence substitution while preserving technical choice.'],'known_costs':['Requires Return and Evidence Bundle schema migration within the candidate package.'],'known_risks':['Overly broad alternative routes must be stopped for Brain re-closure.'],'important_tradeoff_owner':'CODEX_WITHIN_BOUNDARY'},
    ]
    return {'planning_mode':'BRAIN_BOUNDED_FAST_PATH','source_structural_route_binding':None,'owner':'WEB_BRAIN','candidate_set_exhaustive':False,'codex_alternative_route_allowed':True,'required_dimensions':dims,'obligations':obligations,'candidate_routes':routes,'route_change_boundaries':{'may_execute_without_reclosure':['SELECT_FEASIBLE_BRAIN_CANDIDATE','PROPOSE_EQUIVALENT_ALTERNATIVE_WITHIN_APPROVED_PATHS_AND_SEMANTICS'],'must_return_for_reclosure':['CHANGE_PRODUCT_BEHAVIOR_OR_PROTOCOL','EXPAND_ALLOWED_PATHS','CHANGE_IMPORTANT_TRADEOFF','INTRODUCE_MIGRATION_OR_COMPATIBILITY_COMMITMENT']}}

def new_capsule(route='PROTOCOL_CHANGE', scope='ARTIFACT_CHANGE'):
    model=c.load_model(); profile=model['route_profiles'][route]; items=base_items()
    active={
      'semantic':{'fiber_type':'semantic','status':'FROZEN','revision':1,'previous_digest':None,'payload':{'semantic_items':items,'classification_review':{'risk_review_complete':True,'domain_review_complete':True,'reviewer_basis':['Reviewed active meanings, typed effects, risk markers and lanes.']}},'fiber_digest':None},
      'decision_boundary':{'fiber_type':'decision_boundary','status':'FROZEN','revision':1,'previous_digest':None,'payload':{'mode':'PROTOCOL' if route=='PROTOCOL_CHANGE' else 'IMPLEMENTATION','problem_reality':'CHANGE_REQUIRED' if route=='REPAIR_STANDARD' else 'NOT_APPLICABLE','technical_decisions':[],'technical_route_space':technical_route_space(scope),'boundary_obligations':[],'repository_binding':None,'risk_controls':[],'repair_extension':None},'fiber_digest':None},
      'validation':{'fiber_type':'validation','status':'FROZEN','revision':1,'previous_digest':None,'payload':{
        'acceptance_cases':[],
        'checks':[{'check_id':'CHECK_UNIT','command':VALIDATION_COMMAND,'argv':copy.deepcopy(VALIDATION_ARGV),'cwd_scope':'SOURCE_ROOT','required':True,'evidence_kind':'EXIT_CODE_AND_RAW_OUTPUT'}],
        'human_validation':[], 'obligation_registry':[],
        'adversarial_review':[{'category':x,'verdict':'PASS','evidence_refs':['E_COLD_REVIEW']} for x in model['validation_requirements']['strict_adversarial_categories']] if profile['validation_depth']=='STRICT' else [],
        'mechanical_walkthrough':[]},'fiber_digest':None},
      'authority':{'fiber_type':'authority','status':'FROZEN','revision':1,'previous_digest':None,'payload':{'approval_required':True,'brain_read_only_authorization_required':False,'user_decisions':['Adopt the single-active-task-per-project-round repair.','Codex retains bounded technical judgment and must object instead of blindly executing a conflicting Brain route.'],'return_contract':['Return the frozen candidate ZIP or bounded repository PR.','Return a digest-bound Evidence Bundle and Codex Return for the current project/task/round.','Leave Brain review, user acceptance and merge authorization pending.','If the route conflicts with direct evidence or approved scope, return a source-bound technical objection and BLOCKED without inventing PR or artifact completion.'],'evidence_transport':c._default_evidence_transport_plan()},'fiber_digest':None},
    }
    wanted=set(profile['required_fibers']); active={k:v for k,v in active.items() if k in wanted}
    if route=='READ_ONLY_DISCOVERY':
        active['decision_boundary']['payload']['mode']='READ_ONLY_DISCOVERY'
        active['authority']['payload']['approval_required']=False
        active['authority']['payload']['brain_read_only_authorization_required']=True
        active['authority']['payload']['user_decisions']=[]
        active['authority']['payload']['return_contract']=['Return PATH_DISCOVERY_RETURN with stable item IDs and typed Evidence for every path, dependency, validation entry and local finding.','Capture distinct BEFORE and AFTER worktree records with tools/capture_worktree_fingerprint.py and preserve raw-output references and SHA-256 values.','Do not mutate files, create commits or PRs, or decide final allowed paths.','Leave final path-boundary selection to the Web Brain; unresolved questions must remain explicit and block final mutating closure.']

    repo_anchor=None
    if scope=='REPOSITORY_CHANGE' or profile['requires_repository_binding'] is True:
        repo_anchor={'repository_id':'example/repo','baseline_commit':'abc123'}; slots={}
        required=profile.get('required_repository_fact_slots',[])
        if route=='PROTOCOL_CHANGE' and scope=='REPOSITORY_CHANGE': required=profile.get('required_repository_fact_slots_when_repository_change',[])
        for slot in required:
            slots[slot]={'status':'PROVEN','claim':f'{slot} is confirmed for the current baseline.','evidence_ref':'E_TEST_PLAN','not_applicable_reason':''}
        github_path_evidence,_=github_path_fixture()
        final_decision={'artifact_type':'FINAL_PATH_DECISION','owner':'WEB_BRAIN','project_id':'JOYFLOW_DEVELOPMENT','task_id':'TASK_PHASE1E_AI_NATIVE_CHANGE_PROJECTION_REPAIR','round_id':1,'repository_id':'example/repo','baseline_commit':'abc123','allowed_path_items':[{'path':'runtime/**','basis_type':'GITHUB_CONFIRMED','source_github_path_evidence_ids':['E_GITHUB_PATHS'],'derived_from_paths':[],'supporting_evidence_refs':[],'source_path_discovery_return_digest':None,'source_return_path_ids':[],'source_return_dependency_ids':[],'source_return_validation_ids':[],'source_return_finding_ids':[],'derivation_summary':'The current typed GitHub repository tree directly covers the approved runtime change root.'}],'unresolved_path_questions':[],'structural_closure_binding':{'status':'NOT_REQUIRED','source_structural_return_digest':None,'structural_question_id':None,'source_route_id':None,'brain_disposition_digest':None},'decision_digest':None}
        final_decision['decision_digest']=c.digest(c.strip_digest(final_decision,'decision_digest'))
        path_state={'github_discovery_status':'COMPLETED_SUFFICIENT','github_ref':'github:example/repo@abc123','github_path_evidence':[github_path_evidence],'confirmed_paths':[{'path':'runtime/**','role':'implementation','evidence_ref':'E_GITHUB_PATHS'},{'path':'tests/**','role':'validation','evidence_ref':'E_GITHUB_PATHS'}],'candidate_paths':[],'local_discovery_required':False,'local_discovery_reason':None,'local_discovery_status':'NOT_REQUIRED','local_discovery_binding':None,'path_discovery_source':'GITHUB_CONFIRMED','final_boundary_owner':'WEB_BRAIN','final_allowed_paths_status':'CONFIRMED','final_path_decision':final_decision,'structural_decision_frame':None,'brain_architecture_disposition':None}
        if route=='READ_ONLY_DISCOVERY':
            path_state={'github_discovery_status':'COMPLETED_INSUFFICIENT','github_ref':'github:example/repo@abc123','github_path_evidence':[github_path_evidence],'confirmed_paths':[],'candidate_paths':[{'path':'runtime/**','why_relevant':'GitHub shows the broad module but cannot establish the local runtime entry.','evidence_ref':'E_GITHUB_PATHS'}],'local_discovery_required':True,'local_discovery_reason':'RUNTIME_ONLY_FACT','local_discovery_status':'PENDING','local_discovery_binding':None,'path_discovery_source':'GITHUB_DERIVED','final_boundary_owner':'WEB_BRAIN','final_allowed_paths_status':'PENDING','final_path_decision':None,'structural_decision_frame':None,'brain_architecture_disposition':None}
        active['repository_evidence']={'fiber_type':'repository_evidence','status':'FROZEN','revision':1,'previous_digest':None,'payload':{'baseline_commit':'abc123','fact_slots':slots,'path_discovery':path_state,'impact_coverage':[{'dimension':d,'status':'CHECKED' if d!='RUNTIME_CHAIN' else 'NOT_APPLICABLE','evidence_refs':[f'E_IMPACT_{d}'],'applicability_basis':'Current repository discovery explicitly binds evidence to this impact dimension for the bounded task; runtime chain is not material to this static package repair.'} for d in ['DIRECT_IMPLEMENTATION','DIRECT_CALLERS','INTERFACES_SCHEMA','DATA_STATE_BOUNDARIES','SHARED_CORE','RELEVANT_TESTS','RUNTIME_CHAIN']],'context_exclusions':[{'item':'docs/**','basis':'No current task dependency, validation, state or failure relation was observed.','reopen_when':'A current dependency, test or runtime observation links docs/** to the task.'}],'unresolved_repository_questions':[]},'fiber_digest':None}
    state={
      'artifact_type':'FIBERED_TASK_CAPSULE','model_id':'','model_version':0,'capsule_id':'CAPSULE_PHASE1E_AI_NATIVE_CHANGE_PROJECTION_REPAIR',
      'task_anchor':{'project_id':'JOYFLOW_DEVELOPMENT','task_id':'TASK_PHASE1E_AI_NATIVE_CHANGE_PROJECTION_REPAIR','task_version':1,'goal':'Extend the exact passed PR1D chain with AI-native change continuity while preserving current repository truth, exact Brain Review and PR CI, exact Merge Candidate Freeze, applicable User Acceptance, separate final merge authorization, and optional post-merge navigation.','desired_result':'Deliver a cold-reviewable cumulative PR1E candidate where Brain Review PASS plus current PR CI PASS produces an exact Merge Candidate Freeze, applicable User Acceptance binds that Freeze, final merge authorization is a separate exact-object user decision, and any Merged Change Projection is optional post-merge navigation that cannot replace or gate current repository facts.','non_goals':['Do not create a persistent task-lifecycle service, path-discovery service, repository cache, global scheduler or multi-task isolation system.','Do not implement user identity authentication or cryptographic approval.','Do not implement immutable parent history or trusted observer services.','Do not implement automatic merge/promotion.','Do not implement Repository Cache or long-term repository context.','Do not declare a formal Joyflow baseline.'],'planning_context':{'parent_goal':'Improve Joyflow while preserving the human semi-automatic authority topology.','material_operating_assumptions':[{'condition_type':'DESCRIPTIVE_CONDITION','assumption':'This candidate is used by one Web Brain and one bounded Codex execution layer.','material_effect':'Do not introduce multi-agent authority or autonomous promotion.','source_basis':'USER_CONFIRMED','epistemic_status':'CONFIRMED','source_refs':['E_USER_SCENARIO'],'reopen_trigger':'The user explicitly authorizes an architecture change.'}],'relevant_prior_behaviors':[{'behavior_id':'PHASE1_OBJECT_TRUTH','statement':'Current repository and exact current objects remain authoritative over historical navigation.','source_refs':['E_PRIOR_PHASE1_OBJECT_TRUTH'],'why_relevant':'PR2 planning must preserve Phase 1 current-object truth while extending continuity.','expected_disposition':'PRESERVE_REQUIRED','authorization_refs':[]}],'exit_conditions':['The current change-unit goal is closed without changing authority topology.','Any material residual is explicitly declared rather than silently deferred.']},'change_scope':scope,'repository_operation':'CURRENT_ROUND_REPOSITORY_CHANGE' if scope=='REPOSITORY_CHANGE' else 'NOT_APPLICABLE','repository_anchor':repo_anchor,'artifact_anchor':({'source_mode':'EXISTING_ARTIFACT','artifact_id':'JOYFLOW_PHASE1D_REVIEW_ACCEPTANCE_FREEZE_REPAIR_CANDIDATE.zip','artifact_sha256':'e527513547d7275f73ed3ef4a9928cef240c2b4f6af3f81b65242942596e45c9','source_material_refs':['E_COLD_REVIEW'],'source_materials':[]} if scope=='ARTIFACT_CHANGE' else None),'anchor_digest':None},
      'task_progress':{'stage':profile['initial_stage'],'cycle':1,'previous_stage':None,'cycle_trigger':'NONE','parent_capsule_digest':None,'transition_event':{'event_id':'EV_CREATE','event_type':'CREATE_TASK','from_stage':None,'to_stage':profile['initial_stage'],'changed_anchor_fields':[],'added_fibers':sorted(active),'changed_fibers':[],'removed_fibers':[],'evidence_refs':['E_USER_MODEL'],'reason':'Create the bounded Codex technical-authority repair task while preserving the completed PR1A path-discovery evidence chain.'}},
      'route_profile':route,'task_classification':{'risk_markers':['NONE'],'domain_lanes':['GENERAL']},'active_fibers':active,'evidence_registry':evidence_registry(),
      'refs':{'depends_on':[],'affects':[],'preserves':['REPOSITORY_CANONICAL_STATE','HUMAN_SEMIAUTOMATIC_AUTHORITY_TOPOLOGY','ONE_ACTIVE_TASK_PER_PROJECT_ROUND','WEB_BRAIN_FINAL_PATH_BOUNDARY','CODEX_BOUNDED_TECHNICAL_AUTHORITY'],'conflicts_with':[],'validated_by':['E_TEST_PLAN'],'supersedes':['JOYFLOW_PHASE1D_REVIEW_ACCEPTANCE_FREEZE_REPAIR_CANDIDATE']},
      'derived_gates':{},'unresolved_blockers':[],'approval_record':draft_approval_record(route),
      'stop_conditions':['GitHub evidence was not inspected before local discovery was requested.','Codex local discovery mutates files, creates a commit or PR, or decides final allowed paths.','A mutating repository task proceeds before the Brain confirms the final allowed-path boundary.','A local Path Discovery Return is bound to another task round or Projection.','Codex continues after a Brain-route conflict, expands allowed paths, changes product semantics, or invents completion evidence for a blocked task.','Brain review promotes a BLOCKED Codex Return to PASS.'],'capsule_digest':None}
    if 'decision_boundary' in active and scope=='REPOSITORY_CHANGE':
        active['decision_boundary']['payload']['repository_binding']={'repository_id':'example/repo','default_branch':'main','working_branch':'joyflow/task','expected_base_commit':'abc123'}
        items[0]['effects'].append(ev('E_ALLOW_RUNTIME','ALLOW_PATH','runtime/**'))
    if 'decision_boundary' in active and route=='REPAIR_STANDARD':
        active['decision_boundary']['payload']['mode']='REPAIR'
        active['decision_boundary']['payload']['repair_extension']={'failure_source_refs':['E_COLD_REVIEW'],'root_cause':'The prior candidate displayed derived gates but did not make post-execution stage entry depend on them.','source_projection_digest':'a'*64,'retained_boundary_digest':'b'*64,'compatibility_verdict':'PASS'}
    return refresh(state)


def advance(previous, stage, event_type='ADVANCE_STAGE', trigger='NONE', evidence_refs=None, reason='Advance after the previous human or technical gate completed.'):
    state=copy.deepcopy(previous)
    state['approval_record']=copy.deepcopy(previous['approval_record']) if trigger=='NONE' else draft_approval_record()
    state['capsule_digest']=None; state['derived_gates']={}
    state['task_progress']={'stage':stage,'cycle':previous['task_progress']['cycle']+(0 if trigger=='NONE' else 1),'previous_stage':previous['task_progress']['stage'],'cycle_trigger':trigger,'parent_capsule_digest':previous['capsule_digest'],'transition_event':{'event_id':f'EV_{stage}','event_type':event_type,'from_stage':previous['task_progress']['stage'],'to_stage':stage,'changed_anchor_fields':[],'added_fibers':[],'changed_fibers':[],'removed_fibers':[],'evidence_refs':evidence_refs or ['E_USER_MODEL'],'reason':reason}}
    return c.prepare_capsule_structural_fixture(state,previous)


def initial_sealed(route='PROTOCOL_CHANGE',scope='ARTIFACT_CHANGE'): return c.prepare_capsule_structural_fixture(new_capsule(route,scope))


def at_user_approval(route='PROTOCOL_CHANGE',scope='ARTIFACT_CHANGE'):
    current=initial_sealed(route,scope)
    if current['task_progress']['stage'] in {'INTENT_DISCUSSION','REPOSITORY_DISCOVERY'}: current=advance(current,'DECISION_CLOSURE')
    if route=='READ_ONLY_DISCOVERY':
        return current
    if current['task_progress']['stage']!='USER_APPROVAL': current=advance(current,'USER_APPROVAL')
    return current

def approved_capsule(route='PROTOCOL_CHANGE',scope='ARTIFACT_CHANGE'):
    cap=at_user_approval(route,scope); projection,view,binding=c.draft_handoff(cap)
    cap=copy.deepcopy(cap)
    if route=='READ_ONLY_DISCOVERY':
        cap['approval_record']={'status':'AUTHORIZED_READ_ONLY_DISCOVERY','owner':'WEB_BRAIN','scope':'READ_ONLY_DISCOVERY_ONLY','basis':'WEB_BRAIN_BOUNDED_READ_ONLY_DISCOVERY_AUTHORIZATION','decision_ref':'brain:bounded-read-only-discovery-authorization','binding':binding}
    else:
        cap['approval_record']={'status':'APPROVED_FINAL','owner':'WEB_BRAIN','scope':c.expected_approval_scope(cap),'basis':'CURRENT_EXPLICIT_USER_DECISION','decision_ref':'conversation:current-explicit-execution-approval','binding':binding}
    cap['derived_gates']=c.compute_gate_snapshot(cap); c.validate_capsule(cap)
    return cap,projection,view,binding

def raw_capture(capture_id, capture_kind, command, exit_code, stdout, stderr, observed_object, observation, subject_type, subject_id):
    stdout_bytes=stdout.encode('utf-8'); stderr_bytes=stderr.encode('utf-8')
    row={'capture_id':capture_id,'tool':'joyflow-typed-execution-evidence-runner','capture_kind':capture_kind,'command':command,'exit_code':exit_code,'stdout':stdout,'stderr':stderr,'stdout_bytes_base64':base64.b64encode(stdout_bytes).decode('ascii'),'stderr_bytes_base64':base64.b64encode(stderr_bytes).decode('ascii'),'stdout_sha256':hashlib.sha256(stdout_bytes).hexdigest(),'stderr_sha256':hashlib.sha256(stderr_bytes).hexdigest(),'observed_object':copy.deepcopy(observed_object),'observation':copy.deepcopy(observation),'subject_type':subject_type,'subject_id':subject_id,'capture_sha256':None}
    row['capture_sha256']=c.digest(c._execution_capture_payload(row)); return row


def exec_evidence(eid,subject_type,subject_id,capture):
    claim=c._direct_capture_claim(capture)
    return {'evidence_id':eid,'authority':'EXECUTION_EVIDENCE','kind':c._DIRECT_KIND_BY_CAPTURE[capture['capture_kind']],'ref':capture['capture_id'],'claim':claim,'claim_digest':c.digest(claim),'produced_by':'TOOL','subject_type':subject_type,'subject_id':subject_id,'raw_output_ref':capture['capture_id'],'raw_output_sha256':capture['capture_sha256']}


def exec_derivation(did,kind,claim,subject_type,subject_id,source_refs):
    return {'derivation_id':did,'authority':'EXECUTION_EVIDENCE','kind':kind,'claim':claim,'claim_digest':c.digest(claim),'produced_by':'CODEX','subject_type':subject_type,'subject_id':subject_id,'source_evidence_refs':list(source_refs)}


def _object_capture(expected_obj, subject):
    if expected_obj['object_type']=='REPOSITORY':
        role='EXECUTION_RESULT' if expected_obj['source_mode']=='EXISTING_PR_HEAD' else 'APPROVED_INPUT'
        observation={'repository_id':expected_obj['object_id'],'remote_url':f"https://github.com/{expected_obj['object_id']}.git",'commit_sha':expected_obj['ref_or_sha256'],'role':role}
        return raw_capture('CAP_PREFLIGHT_OBJECT','REPOSITORY_COMMIT',f"git rev-parse {expected_obj['ref_or_sha256']}^{{commit}}",0,expected_obj['ref_or_sha256']+'\n','',expected_obj,observation,'TECHNICAL_PREFLIGHT',subject)
    if expected_obj['source_mode']=='NEW_ARTIFACT':
        observation={'materials':copy.deepcopy(_ACTIVE_SOURCE_MATERIALS),'source_material_set_digest':expected_obj['ref_or_sha256']}
        return raw_capture('CAP_PREFLIGHT_OBJECT','SOURCE_MATERIAL_SET','source-material-set',0,expected_obj['ref_or_sha256']+'\n','',expected_obj,observation,'TECHNICAL_PREFLIGHT',subject)
    observation={'artifact_id':expected_obj['object_id'],'artifact_path':f"/bounded/{expected_obj['object_id']}",'artifact_sha256':expected_obj['ref_or_sha256'],'bytes':1}
    return raw_capture('CAP_PREFLIGHT_OBJECT','ARTIFACT_SHA256',f"sha256 /bounded/{expected_obj['object_id']}",0,'','',expected_obj,observation,'TECHNICAL_PREFLIGHT',subject)

def _support_capture(expected_obj):
    if expected_obj['object_type']=='REPOSITORY':
        observation={'path':'runtime/joyflow_dual_layer.py','file_sha256':'1'*64,'bytes':100}
        return raw_capture('CAP_PREFLIGHT_SOURCE','REPOSITORY_FILE','read-file runtime/joyflow_dual_layer.py',0,'source snapshot','',expected_obj,observation,'TECHNICAL_PREFLIGHT_SOURCE','CURRENT_OBJECT_SOURCE')
    if expected_obj['source_mode']=='NEW_ARTIFACT':
        observation={'materials':copy.deepcopy(_ACTIVE_SOURCE_MATERIALS),'source_material_set_digest':expected_obj['ref_or_sha256']}
        return raw_capture('CAP_PREFLIGHT_SOURCE','SOURCE_MATERIAL_SET','source-material-set',0,expected_obj['ref_or_sha256']+'\n','',expected_obj,observation,'TECHNICAL_PREFLIGHT_SOURCE','CURRENT_OBJECT_SOURCE')
    observation={'artifact_id':expected_obj['object_id'],'artifact_path':f"/bounded/{expected_obj['object_id']}",'artifact_sha256':expected_obj['ref_or_sha256'],'bytes':1}
    return raw_capture('CAP_PREFLIGHT_SOURCE','ARTIFACT_SHA256',f"sha256 /bounded/{expected_obj['object_id']}",0,'','',expected_obj,observation,'TECHNICAL_PREFLIGHT_SOURCE','CURRENT_OBJECT_SOURCE')

def _preflight_test_capture(expected_obj, argv):
    argv=copy.deepcopy(argv); observation={'argv':argv,'cwd_scope':'SOURCE_ROOT','target_ref':expected_obj['ref_or_sha256']}
    return raw_capture('CAP_PREFLIGHT_TEST','TEST_COMMAND',c._canonical_argv(argv),0,'tests passed','',expected_obj,observation,'TECHNICAL_PREFLIGHT_TEST','CURRENT_TEST_PLAN')

def codex_return(projection):
    global _ACTIVE_SOURCE_MATERIALS
    _ACTIVE_SOURCE_MATERIALS=copy.deepcopy(projection['task_object_lifecycle']['approved_input_object'].get('source_materials',[]))
    captures=[]; evidence_rows=[]; derivation_rows=[]; machine=[]; expected_obj=c._return_object_shape(projection['execution_object']); subject=c._technical_preflight_subject(projection)
    objcap=_object_capture(expected_obj,subject); captures.append(objcap); evidence_rows.append(exec_evidence('EXEC_PREFLIGHT_OBJECT','TECHNICAL_PREFLIGHT',subject,objcap))
    sourcecap=_support_capture(expected_obj); captures.append(sourcecap); evidence_rows.append(exec_evidence('EXEC_PREFLIGHT_SOURCE','TECHNICAL_PREFLIGHT_SOURCE','CURRENT_OBJECT_SOURCE',sourcecap))
    approved_test_argv=copy.deepcopy(projection['validation']['checks'][0]['argv']); testcap=_preflight_test_capture(expected_obj,approved_test_argv); captures.append(testcap); evidence_rows.append(exec_evidence('EXEC_PREFLIGHT_TEST','TECHNICAL_PREFLIGHT_TEST','CURRENT_TEST_PLAN',testcap))
    obligation_results=[]
    for obligation in projection['technical_route_space']['obligations']:
        result={'obligation_id':obligation['obligation_id'],'dimension':obligation['dimension'],'subject_digest':obligation['subject_binding']['subject_digest'],'result':'PASS','finding_summary':f"{obligation['dimension']} passed for the exact task-bound subject.",'evidence_refs':[f"DERIVE_{obligation['obligation_id']}"]}
        if obligation['dimension']=='OBJECT_IDENTITY': refs=['EXEC_PREFLIGHT_OBJECT']
        elif obligation['dimension'] in {'ACCEPTANCE_FEASIBILITY','TEST_CONTRADICTION'}: refs=['EXEC_PREFLIGHT_TEST']
        else: refs=['EXEC_PREFLIGHT_SOURCE']
        derivation_rows.append(exec_derivation(result['evidence_refs'][0],'PREFLIGHT_OBLIGATION_DERIVATION',c._obligation_result_claim(result),'TECHNICAL_PREFLIGHT_OBLIGATION',obligation['obligation_id'],refs)); obligation_results.append(result)
    candidate_evaluations=[]
    for i,route in enumerate(projection['technical_route_space']['candidate_routes']):
        feasibility='PASS' if i==0 else 'PARTIAL'; reason=None if i==0 else 'Feasible only after replacing more of the existing contract than the minimum repair requires.'
        result={'route_id':route['route_id'],'feasibility':feasibility,'evidence_refs':[f"DERIVE_ROUTE_EVAL_{i+1}"],'rejection_reason':reason}
        derivation_rows.append(exec_derivation(result['evidence_refs'][0],'ROUTE_CANDIDATE_DERIVATION',c._candidate_evaluation_claim(result),'TECHNICAL_ROUTE_CANDIDATE',route['route_id'],['EXEC_PREFLIGHT_SOURCE','EXEC_PREFLIGHT_TEST'])); candidate_evaluations.append(result)
    selected={'source':'BRAIN_CANDIDATE','route_id':projection['technical_route_space']['candidate_routes'][0]['route_id'],'implementation_summary':'Use the first Brain candidate while retaining equivalent implementation freedom inside the approved lifecycle boundary.','evidence_refs':['DERIVE_SELECTED_ROUTE']}
    derivation_rows.append(exec_derivation('DERIVE_SELECTED_ROUTE','SELECTED_ROUTE_DERIVATION',c._selected_route_claim(selected),'TECHNICAL_ROUTE_SELECTION',selected['route_id'],['EXEC_PREFLIGHT_SOURCE','EXEC_PREFLIGHT_TEST']))
    pr=None; replay=None; artifact=None
    if projection['delivery']['requires_pr']:
        base=projection['task_object_lifecycle']['approved_input_object']['base_commit']
        is_replay=projection['task_object_lifecycle']['route_type']=='EXISTING_PR_REPLAY'
        anchor=projection['task_anchor']['repository_anchor']; head=anchor['frozen_head_sha'] if is_replay else 'deadbeef42'; touched=sorted(anchor['review_coverage_paths']) if is_replay else ['runtime/joyflow_dual_layer.py']
        if is_replay:
            replay={'evidence_role':'EXISTING_FROZEN_PR_REVIEW_TARGET','repository_id':anchor['repository_id'],'pr_number':anchor['pr_number'],'pr_url':anchor['pr_url'],'base_branch':anchor['base_branch'],'working_branch':anchor['working_branch'],'base_commit':base,'frozen_head_sha':head,'review_coverage_paths':touched,'diff_evidence_ref':'EXEC_DIFF','source_state_before_evidence_ref':'EXEC_REPLAY_STATE_BEFORE','source_state_after_evidence_ref':'EXEC_REPLAY_STATE_AFTER'}
        else:
            pr={'repository_id':'example/repo','base_branch':'main','working_branch':'joyflow/task','pr_url':'https://github.com/example/repo/pull/42','base_commit':base,'head_sha':head,'touched_files':touched,'diff_evidence_ref':'EXEC_DIFF'}
        result_obj={'object_type':'REPOSITORY','source_mode':'EXISTING_PR_HEAD' if is_replay else 'REPOSITORY_REF','object_id':'example/repo','ref_or_sha256':head}
        result_commit=raw_capture('CAP_EXEC_RESULT','REPOSITORY_COMMIT',f"git rev-parse {head}^{{commit}}",0,head+'\n','',result_obj,{'repository_id':'example/repo','remote_url':'https://github.com/example/repo.git','commit_sha':head,'role':'EXECUTION_RESULT'},'EXECUTION_RESULT','REPOSITORY_HEAD')
        captures.append(result_commit); evidence_rows.append(exec_evidence('EXEC_RESULT_HEAD','EXECUTION_RESULT','REPOSITORY_HEAD',result_commit))
        cap=raw_capture('CAP_EXEC_DIFF','REPOSITORY_DIFF',f"git diff --binary {base} {head}",0,'diff bytes','',result_obj,{'base_ref':base,'head_ref':head,'changed_paths':touched,'diff_sha256':'2'*64},'PR_HEAD',head); captures.append(cap); evidence_rows.append(exec_evidence('EXEC_DIFF','PR_HEAD',head,cap))
        if is_replay:
            zero=hashlib.sha256(b'').hexdigest(); components={'head_commit':head,'index_diff_sha256':zero,'worktree_diff_sha256':zero,'tracked_source_set_sha256':zero,'untracked_manifest_sha256':c.digest([]),'declared_ignored_coverage_sha256':c.digest([])}
            for phase,eid in (('BEFORE','EXEC_REPLAY_STATE_BEFORE'),('AFTER','EXEC_REPLAY_STATE_AFTER')):
                observation={'capture_phase':phase,**components,'declared_ignored_paths':[],'state_fingerprint_sha256':c.digest(components)}; state_cap=raw_capture(f'CAP_REPLAY_STATE_{phase}','REPOSITORY_STATE',f'joyflow repository-state {phase}',0,json.dumps(observation,ensure_ascii=False,sort_keys=True,separators=(",",":"))+'\n','',result_obj,observation,'REPOSITORY_REPLAY_SOURCE_STATE',f'{head}:{phase}'); captures.append(state_cap); evidence_rows.append(exec_evidence(eid,'REPOSITORY_REPLAY_SOURCE_STATE',f'{head}:{phase}',state_cap))
        validation_obj=result_obj
    else:
        artifact_id='JOYFLOW_PHASE1_COMBINED_CAPABILITY_COVERAGE_REPAIR_CANDIDATE.zip'; artifact_digest=c.digest({'artifact_id':artifact_id,'projection_digest':projection['projection_digest']})
        validation_obj={'object_type':'ARTIFACT','source_mode':'NEW_ARTIFACT','object_id':artifact_id,'ref_or_sha256':artifact_digest}
        cap=raw_capture('CAP_EXEC_ARTIFACT','ARTIFACT_SHA256',f'sha256 /bounded/{artifact_id}',0,'','',validation_obj,{'artifact_id':artifact_id,'artifact_path':f'/bounded/{artifact_id}','artifact_sha256':artifact_digest,'bytes':1},'ARTIFACT',artifact_digest); captures.append(cap); evidence_rows.append(exec_evidence('EXEC_ARTIFACT','ARTIFACT',artifact_digest,cap))
        artifact={'outputs':[{'artifact_id':artifact_id,'artifact_digest':artifact_digest,'bytes':1,'media_type':'application/zip','role':'PRIMARY','validation_evidence_refs':['EXEC_ARTIFACT']}],'output_set_digest':None}
    checks={x['check_id']:x for x in projection['validation']['checks']}
    for obligation in projection['validation']['obligation_registry']:
        for cid in obligation['check_ids']:
            eid=f"EXEC_{obligation['obligation_id']}_{cid}"; subject_id=f"{obligation['obligation_id']}:{cid}"; cmd=checks[cid]['command']; argv=copy.deepcopy(checks[cid]['argv'])
            cap=raw_capture(f"CAP_{eid}",'TEST_COMMAND',c._canonical_argv(argv),0,f"{cid} passed for {obligation['obligation_id']}",'',validation_obj,{'argv':argv,'cwd_scope':'SOURCE_ROOT','target_ref':validation_obj['ref_or_sha256']},'VALIDATION_CHECK',subject_id); captures.append(cap)
            evidence_rows.append(exec_evidence(eid,'VALIDATION_CHECK',subject_id,cap)); machine.append({'obligation_id':obligation['obligation_id'],'check_id':cid,'actual_command':cmd,'actual_argv':argv,'actual_cwd_scope':'SOURCE_ROOT','exit_code':0,'result':'PASS','evidence_ref':eid})
            if artifact is not None: artifact['outputs'][0]['validation_evidence_refs'].append(eid)
    bundle={'artifact_type':'CODEX_EXECUTION_EVIDENCE_BUNDLE','project_id':projection['project_id'],'task_id':projection['task_id'],'round_id':projection['round_id'],'capsule_digest':projection['capsule_digest'],'projection_digest':projection['projection_digest'],'raw_captures':captures,'evidence_rows':evidence_rows,'derivation_rows':derivation_rows,'evidence_bundle_digest':None}; bundle['evidence_bundle_digest']=c.digest(c.strip_digest(bundle,'evidence_bundle_digest'))
    material={k:False for k in ['product_behavior_changed','protocol_or_schema_semantics_changed','approved_paths_expanded','migration_required','compatibility_commitment_changed','user_visible_result_changed','important_tradeoff_changed']}
    preflight={'status':'ROUTE_CONFIRMED','expected_execution_object':expected_obj,'observed_execution_object':expected_obj,'object_observation_evidence_ref':'EXEC_PREFLIGHT_OBJECT','obligation_results':obligation_results,'candidate_evaluations':candidate_evaluations,'selected_route':selected,'alternative_route':None,'material_change_assessment':material,'execution_decision':'EXECUTE','implementation_decisions':[],'objection':None}
    if pr:
        result_object={'result_type':'REPOSITORY_HEAD','repository_id':pr['repository_id'],'base_commit':pr['base_commit'],'head_commit':pr['head_sha'],'pr_url':pr['pr_url']}
        validation_object={'target_type':'REPOSITORY_HEAD','repository_id':pr['repository_id'],'target_commit':pr['head_sha'],'validation_environment':'TEMPORARY_DETACHED_WORKTREE','machine_result_evidence_refs':sorted({r['evidence_ref'] for r in machine}),'diff_evidence_ref':pr['diff_evidence_ref']}
    elif replay:
        result_object={'result_type':'VALIDATED_EXISTING_PR_HEAD','repository_id':replay['repository_id'],'pr_number':replay['pr_number'],'base_commit':replay['base_commit'],'head_commit':replay['frozen_head_sha']}
        validation_object={'target_type':'REPOSITORY_HEAD','repository_id':replay['repository_id'],'target_commit':replay['frozen_head_sha'],'validation_environment':'TEMPORARY_DETACHED_WORKTREE','machine_result_evidence_refs':sorted({r['evidence_ref'] for r in machine}),'diff_evidence_ref':replay['diff_evidence_ref']}
    else:
        artifact['output_set_digest']=c._artifact_output_set_digest(artifact['outputs'])
        outputs=c._canonical_artifact_outputs(artifact['outputs']); output_set_digest=artifact['output_set_digest']
        result_object={'result_type':'ARTIFACT_OUTPUT_SET','outputs':outputs,'output_set_digest':output_set_digest}
        all_refs=sorted({ref for row in artifact['outputs'] for ref in row['validation_evidence_refs']})
        coverage=sorted([{'artifact_id':row['artifact_id'],'validation_evidence_refs':sorted(row['validation_evidence_refs'])} for row in artifact['outputs']],key=lambda r:r['artifact_id'])
        validation_object={'target_type':'ARTIFACT_OUTPUT_SET','target_digest':output_set_digest,'validation_environment':'EXACT_OUTPUT_FILES','machine_result_evidence_refs':sorted({r['evidence_ref'] for r in machine}),'artifact_validation_evidence_refs':all_refs,'output_validation_coverage':coverage,'uncovered_output_ids':[]}
    lifecycle_result={'approved_lifecycle_digest':projection['task_object_lifecycle']['lifecycle_digest'],'transition_status':'RESULT_VALIDATED','execution_result_object':result_object,'final_validation_object':validation_object,'transition_digest':None}; lifecycle_result['transition_digest']=c.execution_lifecycle_result_digest(lifecycle_result)
    ret={'artifact_type':'CODEX_EXECUTION_RETURN','project_id':projection['project_id'],'task_id':projection['task_id'],'round_id':projection['round_id'],'capsule_digest':projection['capsule_digest'],'projection_digest':projection['projection_digest'],'evidence_bundle_digest':bundle['evidence_bundle_digest'],'technical_preflight':preflight,'execution_status':'COMPLETED','execution_lifecycle_result':lifecycle_result,'machine_results':machine,'pr_evidence':pr,'repository_replay_evidence':replay,'artifact_evidence':artifact,'evidence_transport_receipt':None,'blocker_evidence_refs':[],'mutation_summary':{'mutation_performed':False if replay else True,'cleanup_status':'NOT_REQUIRED','residual_changed_paths':[]},'structural_execution_result':{'status':'NOT_APPLICABLE','approved_structural_closure_digest':None,'actual_consequences':[],'deviation_reason':None},'unresolved_items':[],'brain_review_status':'PENDING_BRAIN_REVIEW','user_acceptance_status':'PENDING_USER_ACCEPTANCE','merge_status':'NOT_AUTHORIZED','return_digest':None}; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest')); return ret,bundle

def make_blocked_return(projection, *, status='BRAIN_ROUTE_CONFLICT', observed_repository_ref=None, additional_paths=None, mutation_performed=False, with_pr=False):
    ret,bundle=codex_return(projection); expected=ret['technical_preflight']['expected_execution_object']; observed=copy.deepcopy(expected)
    if status=='REPOSITORY_STATE_MISMATCH': observed['ref_or_sha256']=observed_repository_ref or 'def456'
    dim={'BRAIN_ROUTE_CONFLICT':'ROUTE_ASSUMPTION_VALIDITY','APPROVAL_SCOPE_INSUFFICIENT':'PATH_SUFFICIENCY','REPOSITORY_STATE_MISMATCH':'OBJECT_IDENTITY'}[status]
    failed=next(r for r in ret['technical_preflight']['obligation_results'] if r['dimension']==dim); failed['result']='FAIL'; failed['finding_summary']={'BRAIN_ROUTE_CONFLICT':'Brain route conflicts with current-object direct facts.','APPROVAL_SCOPE_INSUFFICIENT':'Approved paths are insufficient for the required implementation.','REPOSITORY_STATE_MISMATCH':'Observed execution object differs from the approved object.'}[status]
    drv=next(x for x in bundle['derivation_rows'] if x['derivation_id']==failed['evidence_refs'][0]); drv['claim']=c._obligation_result_claim(failed); drv['claim_digest']=c.digest(drv['claim'])
    if status=='REPOSITORY_STATE_MISMATCH':
        obj_ev=next(x for x in bundle['evidence_rows'] if x['evidence_id']=='EXEC_PREFLIGHT_OBJECT'); obj_cap=next(x for x in bundle['raw_captures'] if x['capture_id']==obj_ev['raw_output_ref'])
        obj_cap['observed_object']=copy.deepcopy(observed)
        if observed['object_type']=='REPOSITORY': obj_cap['observation']['commit_sha']=observed['ref_or_sha256']
        else: obj_cap['observation']['artifact_sha256']=observed['ref_or_sha256']
        obj_cap['capture_sha256']=c.digest(c._execution_capture_payload(obj_cap)); obj_ev['claim']=c._direct_capture_claim(obj_cap); obj_ev['claim_digest']=c.digest(obj_ev['claim']); obj_ev['raw_output_sha256']=obj_cap['capture_sha256']
        for result in ret['technical_preflight']['obligation_results']:
            if result['dimension']=='OBJECT_IDENTITY':
                continue
            result['result']='NOT_APPLICABLE'; result['finding_summary']='Not evaluated because the observed execution object differs from the approved object.'
            drv_row=next(x for x in bundle['derivation_rows'] if x['derivation_id']==result['evidence_refs'][0])
            drv_row['source_evidence_refs']=['EXEC_PREFLIGHT_OBJECT']; drv_row['claim']=c._obligation_result_claim(result); drv_row['claim_digest']=c.digest(drv_row['claim'])
        for evaluation in ret['technical_preflight']['candidate_evaluations']:
            evaluation['feasibility']='NOT_EVALUATED'; evaluation['rejection_reason']='Not evaluated because the observed execution object differs from the approved object.'
            drv_row=next(x for x in bundle['derivation_rows'] if x['derivation_id']==evaluation['evidence_refs'][0])
            drv_row['source_evidence_refs']=['EXEC_PREFLIGHT_OBJECT']; drv_row['claim']=c._candidate_evaluation_claim(evaluation); drv_row['claim_digest']=c.digest(drv_row['claim'])
        ret['technical_preflight']['selected_route']=None
        ret['technical_preflight']['alternative_route']=None
    finding_id=f'FINDING_{status}'; requested=list(additional_paths or []); conflict=failed['finding_summary']
    objection={'finding_id':finding_id,'failed_obligation_ids':[failed['obligation_id']],'finding_derivation_refs':['DERIVE_PREFLIGHT_BLOCKER'],'technical_conflict':conflict,'minimum_correct_route':'Return to Web Brain for route re-closure.','additional_paths_required':requested}
    source_refs=['EXEC_PREFLIGHT_OBJECT'] if status=='REPOSITORY_STATE_MISMATCH' else ['EXEC_PREFLIGHT_SOURCE']
    bundle['derivation_rows'].append(exec_derivation('DERIVE_PREFLIGHT_BLOCKER','TECHNICAL_OBJECTION_DERIVATION',c._technical_objection_claim(status,objection,expected,observed),'TECHNICAL_PREFLIGHT_FINDING',finding_id,source_refs))
    ret['execution_status']='BLOCKED'; ret['technical_preflight'].update({'status':status,'observed_execution_object':observed,'execution_decision':'STOP_FOR_BRAIN_RECLOSURE','objection':objection}); ret['machine_results']=[]
    if with_pr:
        touched=list(ret['pr_evidence']['touched_files']); ret['mutation_summary']={'mutation_performed':True,'cleanup_status':'PENDING','residual_changed_paths':touched}
    else:
        ret['pr_evidence']=None; ret['repository_replay_evidence']=None; ret['artifact_evidence']=None; ret['mutation_summary']={'mutation_performed':mutation_performed,'cleanup_status':'COMPLETED' if mutation_performed else 'NOT_REQUIRED','residual_changed_paths':[]}
    ret['blocker_evidence_refs']=['DERIVE_PREFLIGHT_BLOCKER']; ret['unresolved_items']=[conflict]
    ret['execution_lifecycle_result']={'approved_lifecycle_digest':projection['task_object_lifecycle']['lifecycle_digest'],'transition_status':'BLOCKED_BEFORE_VALIDATED_RESULT','execution_result_object':None,'final_validation_object':None,'transition_digest':None}
    ret['execution_lifecycle_result']['transition_digest']=c.execution_lifecycle_result_digest(ret['execution_lifecycle_result'])
    bundle['evidence_bundle_digest']=c.digest(c.strip_digest(bundle,'evidence_bundle_digest')); ret['evidence_bundle_digest']=bundle['evidence_bundle_digest']; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest')); return ret,bundle

def path_discovery_return(projection):
    confirmed={'path_id':'LOCAL_PATH_RUNTIME','path':'runtime/joyflow_dual_layer.py','role':'local runtime entry','evidence_ref':'DISC_OBS_RUNTIME'}
    candidate={'path_id':'LOCAL_CANDIDATE_TEST','path':'tests/test_phase1_single_active_task_round.py','why_relevant':'Existing local validation entry for the runtime.','confidence':'HIGH','evidence_ref':'DISC_DERIVE_CANDIDATE_TEST'}
    edge={'edge_id':'LOCAL_EDGE_MODEL','from':'runtime/joyflow_dual_layer.py','to':'machine/joyflow_dual_layer_model.yaml','relation':'loads mechanical model','evidence_ref':'DISC_DERIVE_DEP_EDGE'}
    validation={'validation_id':'LOCAL_VALIDATION_TEST','path':'tests/test_phase1_single_active_task_round.py','command':VALIDATION_COMMAND,'evidence_ref':'DISC_DERIVE_VALIDATION'}
    zero='0'*64
    before={'capture_id':'CAPTURE_BEFORE','capture_phase':'BEFORE','head_commit':'abc123','index_diff_sha256':zero,'worktree_diff_sha256':zero,'untracked_manifest_sha256':zero,'declared_ignored_manifest_sha256':c.digest([]),'evidence_ref':'DISC_STATE_BEFORE','state_fingerprint_sha256':None,'capture_record_digest':None}
    before['state_fingerprint_sha256']=c.digest(c._state_fingerprint_payload(before)); before['capture_record_digest']=c.digest(c._capture_record_payload(before))
    after=copy.deepcopy(before); after.update({'capture_id':'CAPTURE_AFTER','capture_phase':'AFTER','evidence_ref':'DISC_STATE_AFTER'}); after['capture_record_digest']=c.digest(c._capture_record_payload(after))
    def direct_ev(eid,kind,subject_type,subject_id,claim,raw,observed_path=None):
        return {'evidence_id':eid,'authority':'EXECUTION_EVIDENCE','kind':kind,'ref':raw,'claim':claim,'claim_digest':c.digest(claim),'produced_by':'TOOL','subject_type':subject_type,'subject_id':subject_id,'observed_path':observed_path,'source_sha256':None,'source_evidence_refs':[],'raw_output_ref':raw,'raw_output_sha256':c.digest(raw)}
    def derive_ev(eid,kind,subject_type,subject_id,claim,source_refs):
        return {'evidence_id':eid,'authority':'EXECUTION_EVIDENCE','kind':kind,'ref':eid,'claim':claim,'claim_digest':c.digest(claim),'produced_by':'CODEX','subject_type':subject_type,'subject_id':subject_id,'observed_path':None,'source_sha256':None,'source_evidence_refs':list(source_refs),'raw_output_ref':None,'raw_output_sha256':None}
    evidence_rows=[
      direct_ev('DISC_STATE_BEFORE','GIT_STATE_FINGERPRINT','PATH_DISCOVERY_CAPTURE',before['capture_id'],c._git_state_claim(before),'raw:git-state-before'),
      direct_ev('DISC_STATE_AFTER','GIT_STATE_FINGERPRINT','PATH_DISCOVERY_CAPTURE',after['capture_id'],c._git_state_claim(after),'raw:git-state-after'),
      direct_ev('DISC_OBS_RUNTIME','PATH_OBSERVATION','REPOSITORY_PATH',confirmed['path_id'],c._path_observation_claim(confirmed['path_id'],confirmed['path']),'raw:git-ls-files-runtime',confirmed['path']),
      direct_ev('DISC_OBS_TEST','PATH_OBSERVATION','REPOSITORY_PATH','OBS_TEST',c._path_observation_claim('OBS_TEST',candidate['path']),'raw:git-ls-files-test',candidate['path']),
      direct_ev('DISC_OBS_MODEL','PATH_OBSERVATION','REPOSITORY_PATH','OBS_MODEL',c._path_observation_claim('OBS_MODEL',edge['to']),'raw:git-ls-files-model',edge['to']),
      derive_ev('DISC_DERIVE_CANDIDATE_TEST','PATH_CANDIDATE_DERIVATION','REPOSITORY_PATH_CANDIDATE',candidate['path_id'],c._local_item_claim('PATH_CANDIDATE_DERIVATION',candidate),['DISC_OBS_TEST']),
      derive_ev('DISC_DERIVE_DEP_EDGE','DEPENDENCY_DERIVATION','DEPENDENCY_EDGE',edge['edge_id'],c._local_item_claim('DEPENDENCY_DERIVATION',edge),['DISC_OBS_RUNTIME','DISC_OBS_MODEL']),
      derive_ev('DISC_DERIVE_VALIDATION','VALIDATION_ENTRY_DERIVATION','VALIDATION_ENTRY',validation['validation_id'],c._local_item_claim('VALIDATION_ENTRY_DERIVATION',validation),['DISC_OBS_TEST']),
    ]
    ret={'artifact_type':'PATH_DISCOVERY_RETURN','project_id':projection['project_id'],'task_id':projection['task_id'],'round_id':projection['round_id'],'capsule_digest':projection['capsule_digest'],'projection_digest':projection['projection_digest'],
      'repository':{'repository_id':'example/repo','github_ref':'github:example/repo@abc123'},
      'ignored_path_coverage':{'mode':'DECLARED_EXECUTION_RELEVANT_ONLY','exact_files':[],'exact_symlinks':[],'recursive_directories':[],'coverage_status':'COMPLETE_FOR_DECLARED_EXECUTION_RELEVANT_PATHS','full_local_filesystem_unchanged_claim':False},
      'repository_state_before':before,'repository_state_after':after,
      'confirmed_paths':[confirmed],'candidate_paths':[candidate],'dependency_edges':[edge],'validation_entries':[validation],
      'local_only_findings':[],'structural_discovery':{'mode':'NOT_APPLICABLE','architecture_question':None,'semantic_relations':[],'closure_obligations':[],'counterevidence_refs':[],'unresolved_structural_questions':[],'omitted_material_summary':[],'candidate_routes':[],'recommended_route_id':None,'task_structural_projection':{'status':'NOT_APPLICABLE','material_relation_ids':[],'counterevidence_refs':[],'unresolved_questions':[],'omitted_material_summary':[]}},'unresolved_questions':[],'evidence_rows':evidence_rows,'mutation_performed':False,'return_digest':None}
    ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
    return ret

def _add_evidence_rows(state, rows):
    existing={r['evidence_id'] for r in state['evidence_registry']}
    for row in rows:
        if row['evidence_id'] not in existing:
            state['evidence_registry'].append(copy.deepcopy(row)); existing.add(row['evidence_id'])


def brain_review_capsule(previous, projection, ret, bundle, *, brain_verdict='PENDING_BRAIN_REVIEW'):
    state=copy.deepcopy(previous); state['capsule_digest']=None; state['derived_gates']={}
    _add_evidence_rows(state,bundle['evidence_rows'])
    derivation_evidence=[{'evidence_id':r['derivation_id'],'authority':r['authority'],'kind':r['kind'],'ref':r['source_evidence_refs'][0],'claim':r['claim'],'claim_digest':r['claim_digest'],'produced_by':r['produced_by'],'subject_type':r['subject_type'],'subject_id':r['subject_id'],'raw_output_ref':None} for r in bundle['derivation_rows']]
    _add_evidence_rows(state,derivation_evidence)
    packet_subject=c._round_packet_subject(projection['project_id'],projection['task_id'],projection['round_id'],projection['projection_digest'])
    ret_ev=evidence('EXEC_RETURN_BIND','EXECUTION_EVIDENCE','CODEX_RETURN',ret['return_digest'],'Codex Return for the current active round.','CODEX','ROUND_PACKET',packet_subject)
    bundle_ev=evidence('EXEC_BUNDLE_BIND','EXECUTION_EVIDENCE','EVIDENCE_BUNDLE',bundle['evidence_bundle_digest'],'Evidence Bundle for the current active round.','TOOL','ROUND_PACKET',packet_subject)
    if ret['execution_status']=='BLOCKED':
        target={'target_type':'BLOCKED_EXECUTION_RETURN','source_codex_return_digest':ret['return_digest'],'technical_preflight_status':ret['technical_preflight']['status'],'objection_finding_id':ret['technical_preflight']['objection']['finding_id'],'blocker_evidence_refs':copy.deepcopy(ret['blocker_evidence_refs']),'mutation_summary':copy.deepcopy(ret['mutation_summary']),'unresolved_items':copy.deepcopy(ret['unresolved_items'])}
        subject_type='CODEX_RETURN'; subject_id=ret['return_digest']; brain_kind='TECHNICAL_INFERENCE'
    elif c._repository_review_evidence(ret):
        pr=c._repository_review_evidence(ret); target={'target_type':'REPOSITORY_PR_HEAD','repository_id':pr['repository_id'],'pr_url':pr['pr_url'],'head_sha':pr['head_sha'],'actual_changed_paths':pr['review_coverage_paths'],'changed_paths_evidence_ref':pr['diff_evidence_ref']}
        subject_type='PR_HEAD'; subject_id=pr['head_sha']; brain_kind='PR_REVIEW'
    else:
        art=ret['artifact_evidence']; lifecycle_result=ret['execution_lifecycle_result']['execution_result_object']; validation=ret['execution_lifecycle_result']['final_validation_object']; target={'target_type':'ARTIFACT_OUTPUT_SET','output_set_digest':lifecycle_result['output_set_digest'],'outputs':copy.deepcopy(lifecycle_result['outputs']),'artifact_validation_evidence_refs':copy.deepcopy(validation['artifact_validation_evidence_refs']),'output_validation_coverage':copy.deepcopy(validation['output_validation_coverage'])}
        subject_type='ARTIFACT_OUTPUT_SET'; subject_id=lifecycle_result['output_set_digest']; brain_kind='TECHNICAL_INFERENCE'
    prior_support_refs={}
    prior_support_rows=[]
    machine_ref=(ret['machine_results'][0]['evidence_ref'] if ret.get('machine_results') else (target.get('blocker_evidence_refs') or ['EXEC_RETURN_BIND'])[0])
    support_kind='PR_REVIEW' if subject_type=='PR_HEAD' else 'TECHNICAL_INFERENCE'
    for planned in projection['task_anchor']['planning_context'].get('relevant_prior_behaviors',[]):
        eid=f"BRAIN_PRIOR_{planned['behavior_id']}"
        row=evidence(eid,'BRAIN_DERIVATION',support_kind,machine_ref,f"Brain mapped current execution/review evidence to prior behavior {planned['behavior_id']} for this bounded change unit.",'WEB_BRAIN','PRIOR_BEHAVIOR',planned['behavior_id'])
        row['claim_digest']=c.digest(row['claim']); prior_support_rows.append(row); prior_support_refs[planned['behavior_id']]=eid
    _add_evidence_rows(state,prior_support_rows)
    brain_refs=[]
    extra=[ret_ev,bundle_ev]
    if brain_verdict in {'PASS','BLOCK'}:
        brain=evidence('BRAIN_REVIEW_CURRENT','BRAIN_DERIVATION',brain_kind,'brain-review:current-round',f'Brain review verdict {brain_verdict} for the current round target.','WEB_BRAIN',subject_type,subject_id)
        extra.append(brain); brain_refs=[brain['evidence_id']]
    for row in extra: row['claim_digest']=c.digest(row['claim'])
    _add_evidence_rows(state,extra)
    by={}
    for row in ret['machine_results']: by.setdefault(row['obligation_id'],[]).append(copy.deepcopy(row))
    validation_results=[]
    for obligation in projection['validation']['obligation_registry']:
        if ret['execution_status']=='BLOCKED':
            validation_results.append({'obligation_id':obligation['obligation_id'],'machine_results':by.get(obligation['obligation_id'],[]),'human_results':[],'verdict':'BLOCKED'})
        else:
            verdict='PASS' if not obligation.get('human_validation_ids') else 'PENDING_USER_ACCEPTANCE'
            validation_results.append({'obligation_id':obligation['obligation_id'],'machine_results':by.get(obligation['obligation_id'],[]),'human_results':[],'verdict':verdict})
    source_structural=ret.get('structural_execution_result') or {'status':'NOT_APPLICABLE','approved_structural_closure_digest':None,'actual_consequences':[],'deviation_reason':None}
    if source_structural['status']=='NOT_APPLICABLE':
        structural_review={'status':'NOT_REQUIRED','approved_closure_digest':None,'actual_consequence_ids':[],'dispositions':[],'long_term_projection_disposition':'NO_REFOLD_REQUIRED'}
    else:
        consequence_ids=[r['consequence_id'] for r in source_structural.get('actual_consequences',[])]
        structural_review={'status':'RECLOSURE_REQUIRED' if source_structural['status']=='DEVIATION_DETECTED' else 'PRESERVED','approved_closure_digest':source_structural['approved_structural_closure_digest'],'actual_consequence_ids':consequence_ids,'dispositions':[{'consequence_id':cid,'result':'RECLOSURE_REQUIRED' if source_structural['status']=='DEVIATION_DETECTED' else 'PRESERVED','review_basis':'Brain review preserves the exact Codex-reported structural consequence for the current review target.'} for cid in consequence_ids],'long_term_projection_disposition':'NO_REFOLD_REQUIRED'}
    payload={'project_id':projection['project_id'],'task_id':projection['task_id'],'round_id':projection['round_id'],'source_execution_status':ret['execution_status'],'source_projection_digest':projection['projection_digest'],'source_codex_return_digest':ret['return_digest'],'source_evidence_bundle_digest':bundle['evidence_bundle_digest'],'source_task_object_lifecycle_digest':projection['task_object_lifecycle']['lifecycle_digest'],'source_execution_lifecycle_result_digest':ret['execution_lifecycle_result']['transition_digest'],'source_codex_return_evidence_ref':'EXEC_RETURN_BIND','source_evidence_bundle_ref':'EXEC_BUNDLE_BIND','source_evidence_row_digests':c.source_evidence_row_digest_map(bundle),'validation_results':validation_results,'review_target':target,'structural_review':structural_review,'brain_review_verdict':brain_verdict,'brain_review_evidence_refs':brain_refs,'user_acceptance':'PENDING_USER_ACCEPTANCE','user_acceptance_evidence_refs':[],'acceptance_not_applicable_reason':None,'merge_candidate_freeze_digest':None,'merge_status':'NOT_AUTHORIZED','unresolved_followups':copy.deepcopy(ret['unresolved_items']) if ret['execution_status']=='BLOCKED' else [],
      'scenario_goal_review':{'material_operating_assumptions':copy.deepcopy(projection['task_anchor']['planning_context']['material_operating_assumptions']),'product_goal_result':'PENDING_BRAIN_REVIEW' if brain_verdict=='PENDING_BRAIN_REVIEW' else brain_verdict,'machine_validation_status':'BLOCKED' if ret['execution_status']=='BLOCKED' else 'PASS','human_acceptance_required':any(o.get('human_validation_ids') for o in projection['validation']['obligation_registry']),'critical_high_loss_risks':[],'known_limits':['Current validation supports the frozen product goal and scenario; it does not claim exhaustive absence of unknown defects.']},
      'cumulative_review':{'relevant_prior_behaviors':[{'behavior_id':r['behavior_id'],'status':(({'PRESERVE_REQUIRED':'PRESERVED','CHANGE_AUTHORIZED':'CHANGED_WITH_RECLOSURE','SUPERSEDE_AUTHORIZED':'SUPERSEDED_WITH_RECLOSURE'}[r['expected_disposition']]) if ret['execution_status']!='BLOCKED' else 'BROKEN'),'evidence_refs':[prior_support_refs[r['behavior_id']]],'review_basis':'Review only the prior behavior explicitly relevant to the current PR and enforce its approved disposition; do not reopen unrelated project history.'} for r in projection['task_anchor']['planning_context'].get('relevant_prior_behaviors',[])], 'impact_comparison':{'expected_paths':copy.deepcopy(projection['current_source_context']['review_coverage_paths'] if projection['task_anchor'].get('repository_operation')=='EXISTING_FROZEN_PR_REPLAY' else projection['current_source_context']['selected_paths']) if target.get('target_type')=='REPOSITORY_PR_HEAD' else [],'observed_paths':copy.deepcopy((c._repository_review_evidence(ret) or {}).get('review_coverage_paths',[])),'unexpected_paths':[],'status':'WITHIN_EXPECTED'},'exit_condition_results':[{'condition':x,'status':'PENDING','evidence_refs':[],'review_basis':'Brain review must explicitly close this current change-unit exit condition.'} for x in projection['task_anchor']['planning_context']['exit_conditions']],'residuals':[{'issue':x,'material_risk':'Unresolved execution item remains outside the closed result.','reopen_trigger':'Reopen when the blocker is resolved or the affected goal is attempted again.'} for x in ret['unresolved_items']],'verdict':'PENDING_BRAIN_REVIEW' if brain_verdict=='PENDING_BRAIN_REVIEW' else brain_verdict},
      'rework_delta':([{'failure_source':'CODEX_BLOCK','affected_subject':'Current bounded execution','remaining_gap':x,'evidence_refs':copy.deepcopy(target.get('blocker_evidence_refs',[])),'next_allowed_action':'Resolve the recorded Codex blocker and recalculate the current bounded execution context.','reopen_scope':'Only the blocker-related current task fiber and affected paths.'} for x in (ret['unresolved_items'] or ['Codex execution was blocked before closure.'])] if ret['execution_status']=='BLOCKED' else []),
      'source_snapshot_digest':None}
    if brain_verdict in {'PASS','BLOCK'}:
        exit_results=[]; exit_support=[]
        for idx,x in enumerate(projection['task_anchor']['planning_context']['exit_conditions'],start=1):
            eid=f'BRAIN_EXIT_{idx}'
            row=evidence(eid,'BRAIN_DERIVATION',support_kind,'BRAIN_REVIEW_CURRENT',f'Brain review evaluated exit condition {x!r} as {"SATISFIED" if brain_verdict=="PASS" else "BLOCKED"} for the exact current review target.','WEB_BRAIN','EXIT_CONDITION',c.support_subject_id(x)); row['claim_digest']=c.digest(row['claim']); exit_support.append(row)
            exit_results.append({'condition':x,'status':'SATISFIED' if brain_verdict=='PASS' else 'BLOCKED','evidence_refs':[eid],'review_basis':'Brain review explicitly evaluated this current change-unit exit condition against the exact review target.'})
        _add_evidence_rows(state,exit_support); payload['cumulative_review']['exit_condition_results']=exit_results
    if brain_verdict=='BLOCK':
        payload['rework_delta'].append({'failure_source':'BRAIN_REVIEW_BLOCK','affected_subject':f'{subject_type}:{subject_id}','remaining_gap':'Brain review blocked the current change-unit closure.','evidence_refs':['BRAIN_REVIEW_CURRENT'],'next_allowed_action':'Re-close the Brain-identified gap before any further promotion.','reopen_scope':'Only the Brain-blocked current change-unit delta.'})
    payload['source_snapshot_digest']=c.source_derived_review_snapshot_digest(payload)
    state['active_fibers']['execution_review']={'fiber_type':'execution_review','status':'FROZEN','revision':1,'previous_digest':None,'payload':payload,'fiber_digest':None}
    state['task_progress']={'stage':'BRAIN_REVIEW','cycle':previous['task_progress']['cycle'],'previous_stage':previous['task_progress']['stage'],'cycle_trigger':'NONE','parent_capsule_digest':previous['capsule_digest'],'transition_event':{'event_id':'EV_BRAIN_REVIEW','event_type':'ADVANCE_STAGE','from_stage':previous['task_progress']['stage'],'to_stage':'BRAIN_REVIEW','changed_anchor_fields':[],'added_fibers':['execution_review'],'changed_fibers':[],'removed_fibers':[],'evidence_refs':['EXEC_RETURN_BIND','EXEC_BUNDLE_BIND'],'reason':'Codex returned the current-round Return and Evidence Bundle; begin Brain review.'}}
    return c.prepare_capsule_structural_fixture(state,previous,review_projection=projection,codex_return=ret,evidence_bundle=bundle)

def revise_review(previous, stage, *, brain_verdict=None, user_acceptance=None, acceptance_not_applicable_reason=None, merge_candidate_freeze_digest=None):
    state=copy.deepcopy(previous); state['capsule_digest']=None; state['derived_gates']={}
    fiber=state['active_fibers']['execution_review']; payload=fiber['payload']; old_digest=fiber['fiber_digest']; old_payload=copy.deepcopy(payload)
    subject=payload['review_target']
    if subject['target_type']=='REPOSITORY_PR_HEAD': st='PR_HEAD'; sid=subject['head_sha']
    elif subject['target_type']=='ARTIFACT_OUTPUT_SET': st='ARTIFACT_OUTPUT_SET'; sid=subject['output_set_digest']
    else: st='CODEX_RETURN'; sid=payload['source_codex_return_digest']
    added=[]
    if brain_verdict is not None:
        payload['brain_review_verdict']=brain_verdict; payload['brain_review_evidence_refs']=[]; payload['scenario_goal_review']['product_goal_result']=brain_verdict; payload['cumulative_review']['verdict']=brain_verdict
        if brain_verdict in {'PASS','BLOCK'}:
            kind='PR_REVIEW' if st=='PR_HEAD' else 'TECHNICAL_INFERENCE'
            row=evidence('BRAIN_REVIEW_CURRENT','BRAIN_DERIVATION',kind,'brain-review:current-round',f'Brain review verdict {brain_verdict} for current target.','WEB_BRAIN',st,sid); row['claim_digest']=c.digest(row['claim']); added.append(row); payload['brain_review_evidence_refs']=[row['evidence_id']]
            exit_results=[]
            for idx,x in enumerate(state['task_anchor']['planning_context']['exit_conditions'],start=1):
                eid=f'BRAIN_EXIT_{idx}'
                exit_ev=evidence(eid,'BRAIN_DERIVATION',kind,'BRAIN_REVIEW_CURRENT',f'Brain review evaluated exit condition {x!r} as {"SATISFIED" if brain_verdict=="PASS" else "BLOCKED"} for the exact current review target.','WEB_BRAIN','EXIT_CONDITION',c.support_subject_id(x))
                exit_ev['claim_digest']=c.digest(exit_ev['claim']); added.append(exit_ev)
                exit_results.append({'condition':x,'status':'SATISFIED' if brain_verdict=='PASS' else 'BLOCKED','evidence_refs':[eid],'review_basis':'Brain review explicitly evaluated this current change-unit exit condition against the exact review target.'})
            payload['cumulative_review']['exit_condition_results']=exit_results
            if brain_verdict=='BLOCK':
                payload['rework_delta']=[{'failure_source':'BRAIN_REVIEW_BLOCK','affected_subject':f'{st}:{sid}','remaining_gap':'Brain review blocked the current change-unit closure.','evidence_refs':['BRAIN_REVIEW_CURRENT'],'next_allowed_action':'Re-close the Brain-identified gap before any further promotion.','reopen_scope':'Only the Brain-blocked current change-unit delta.'}]
            elif payload.get('source_execution_status')!='BLOCKED':
                payload['rework_delta']=[]
    if merge_candidate_freeze_digest is not None:
        payload['merge_candidate_freeze_digest']=merge_candidate_freeze_digest
    if user_acceptance is not None:
        payload['user_acceptance']=user_acceptance; payload['user_acceptance_evidence_refs']=[]; payload['acceptance_not_applicable_reason']=acceptance_not_applicable_reason
        if user_acceptance in {'PASS','BLOCK'}:
            row=evidence('USER_ACCEPT_CURRENT','USER_DECISION','USER_ACCEPTANCE','conversation:current-user-acceptance',f'User acceptance verdict {user_acceptance} for current target.','WEB_BRAIN',st,sid); row['claim_digest']=c.digest(row['claim']); added.append(row); payload['user_acceptance_evidence_refs']=[row['evidence_id']]
            if user_acceptance=='BLOCK':
                payload['rework_delta']=[{'failure_source':'USER_ACCEPTANCE_BLOCK','affected_subject':f'{st}:{sid}','remaining_gap':'User acceptance blocked the current user-visible result.','evidence_refs':['USER_ACCEPT_CURRENT'],'next_allowed_action':'Re-close only the user-rejected acceptance delta.','reopen_scope':'Only the user-acceptance-failed behavior and directly affected implementation.'}]
    _add_evidence_rows(state,added)
    changed = payload != old_payload
    if changed:
        fiber['revision']+=1; fiber['previous_digest']=old_digest; fiber['fiber_digest']=None
    state['task_progress']={'stage':stage,'cycle':previous['task_progress']['cycle'],'previous_stage':previous['task_progress']['stage'],'cycle_trigger':'NONE','parent_capsule_digest':previous['capsule_digest'],'transition_event':{'event_id':f'EV_{stage}','event_type':'ADVANCE_STAGE','from_stage':previous['task_progress']['stage'],'to_stage':stage,'changed_anchor_fields':[],'added_fibers':[],'changed_fibers':['execution_review'] if changed else [],'removed_fibers':[],'evidence_refs':[r['evidence_id'] for r in added] or ['E_USER_MODEL'],'reason':f'Advance current active round to {stage} after required review gate.'}}
    return c.prepare_capsule_structural_fixture(state,previous)


def _structural_merge_freeze_digest(brain_pass_capsule):
    payload=brain_pass_capsule['active_fibers']['execution_review']['payload']; target=payload['review_target']
    return c.digest({'artifact_type':'TEST_ONLY_STRUCTURAL_MERGE_CANDIDATE_FREEZE_BINDING','project_id':payload['project_id'],'task_id':payload['task_id'],'round_id':payload['round_id'],'repository_id':target['repository_id'],'head_sha':target['head_sha'],'brain_review_capsule_digest':brain_pass_capsule['capsule_digest']})

def full_repository_review_chain():
    approved,projection,_,_=approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
    executing=advance(approved,'CODEX_EXECUTION')
    ret,bundle=codex_return(projection)
    reviewing=brain_review_capsule(executing,projection,ret,bundle)
    brain_pass=revise_review(reviewing,'BRAIN_REVIEW',brain_verdict='PASS')
    freeze_digest=_structural_merge_freeze_digest(brain_pass)
    user_stage=revise_review(brain_pass,'USER_ACCEPTANCE',merge_candidate_freeze_digest=freeze_digest)
    merge_stage=revise_review(user_stage,'MERGE_DECISION',user_acceptance='PASS',merge_candidate_freeze_digest=freeze_digest)
    return approved,projection,ret,bundle,reviewing,user_stage,merge_stage


def full_artifact_review_chain():
    approved,projection,_,_=approved_capsule('ARTIFACT_REPAIR','ARTIFACT_CHANGE')
    executing=advance(approved,'CODEX_EXECUTION')
    ret,bundle=codex_return(projection)
    reviewing=brain_review_capsule(executing,projection,ret,bundle)
    user_stage=revise_review(reviewing,'USER_ACCEPTANCE',brain_verdict='PASS')
    closed=revise_review(user_stage,'CLOSED',user_acceptance='NOT_APPLICABLE',acceptance_not_applicable_reason='The frozen protocol artifact has no separate user-operable validation surface in this bounded repair.')
    return approved,projection,ret,bundle,reviewing,user_stage,closed


def merge_gate_record(review_capsule, freeze, status='MERGE_READY', user_authorization=None):
    payload=review_capsule['active_fibers']['execution_review']['payload']; target=payload['review_target']
    row={'artifact_type':'MERGE_GATE_RECORD','artifact_role':'DERIVED_GATE_SNAPSHOT_ONLY','status':status,'owner':'WEB_BRAIN','project_id':freeze['project_id'],'task_id':freeze['task_id'],'round_id':freeze['round_id'],'repository_id':freeze['repository_id'],'pr_url':target['pr_url'],'reviewed_head_sha':freeze['head_sha'],'merge_candidate_freeze_digest':freeze['freeze_digest'],'user_acceptance_status':payload['user_acceptance'],'user_acceptance_capsule_digest':review_capsule['capsule_digest'],'user_merge_authorization_digest':None,'derivation_basis':'CURRENT_FREEZE_AND_ACCEPTANCE','record_digest':None}
    if status=='MERGE_ALLOWED':
        if user_authorization is None: raise ValueError('MERGE_ALLOWED snapshot requires user_authorization')
        row['user_merge_authorization_digest']=user_authorization['authorization_digest']; row['derivation_basis']='CURRENT_FREEZE_ACCEPTANCE_AND_USER_AUTHORIZATION'
    row['record_digest']=c.digest(c.strip_digest(row,'record_digest'))
    return row


def completion_pointer(freeze, acceptance_capsule, user_authorization):
    target=acceptance_capsule['active_fibers']['execution_review']['payload']['review_target']
    row={'artifact_type':'TASK_COMPLETION_POINTER','status':'MERGE_OBSERVED','owner':'WEB_BRAIN','project_id':freeze['project_id'],'task_id':freeze['task_id'],'round_id':freeze['round_id'],'task_capsule_id':'CAPSULE_PHASE1E_AI_NATIVE_CHANGE_PROJECTION_REPAIR','repository_id':freeze['repository_id'],'pr_url':target['pr_url'],'reviewed_head_sha':freeze['head_sha'],'merge_candidate_freeze_digest':freeze['freeze_digest'],'user_acceptance_capsule_digest':acceptance_capsule['capsule_digest'],'user_merge_authorization_digest':user_authorization['authorization_digest'],'merge_commit':'0123456789abcdef','repository_evidence_ref':'github:example/repo:pr/42:merged','result':'MERGED_REPOSITORY_RESULT','pointer_digest':None}
    row['pointer_digest']=c.digest(c.strip_digest(row,'pointer_digest'))
    return row


def _write_example_jsons(rows):
    examples=ROOT/'examples'; examples.mkdir(exist_ok=True)
    for name,obj in rows:
        c.write_json(examples/name,obj)


def write_examples_group(group: str):
    examples=ROOT/'examples'; examples.mkdir(exist_ok=True)
    if group=='core':
        initial=initial_sealed(); approval=at_user_approval(); approved,projection,view,binding=approved_capsule(); projection2,prompt=c.compile_handoff(approved); ret,bundle=codex_return(projection2)
        _write_example_jsons([
          ('INITIAL_TASK_CAPSULE.json',initial),('SEALED_TASK_CAPSULE_DRAFT.json',approval),
          ('CODEX_HANDOFF_PROJECTION_DRAFT.json',projection),('APPROVAL_BINDING.json',binding),
          ('APPROVAL_RECORD.json',approved['approval_record']),('APPROVED_TASK_CAPSULE.json',approved),
          ('CODEX_HANDOFF_PROJECTION.json',projection2),('CODEX_EXECUTION_RETURN.json',ret),
          ('CODEX_EXECUTION_EVIDENCE_BUNDLE.json',bundle)])
        write_canonical_text(examples/'USER_APPROVAL_VIEW.md',view)
        write_canonical_text(examples/'COMPLETE_CODEX_PROMPT.md',prompt)
        c.write_json(ROOT/'tests'/'fixture_task_capsule_unsealed.json',new_capsule())
        stale=examples/'CODEX_EXECUTION_EVIDENCE.json'
        if stale.exists(): stale.unlink()
        return
    if group=='discovery':
        approved,projection,view,_=approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY'); prompt=c.compile_handoff(approved)[1]; ret=path_discovery_return(projection)
        _write_example_jsons([('PATH_DISCOVERY_AUTHORIZED_CAPSULE.json',approved),('PATH_DISCOVERY_PROJECTION.json',projection),('PATH_DISCOVERY_RETURN.json',ret)])
        write_canonical_text(examples/'PATH_DISCOVERY_AUTHORIZATION_VIEW.md',view)
        write_canonical_text(examples/'PATH_DISCOVERY_COMPLETE_CODEX_PROMPT.md',prompt)
        for stale_name in ('PATH_DISCOVERY_APPROVED_CAPSULE.json','PATH_DISCOVERY_APPROVAL_VIEW.md'):
            stale=examples/stale_name
            if stale.exists(): stale.unlink()
        return
    if group=='repository':
        _,projection,ret,bundle,brain_review,user_stage,_=full_repository_review_chain()
        _write_example_jsons([
          ('BRAIN_REVIEW_CAPSULE.json',brain_review),('USER_ACCEPTANCE_CAPSULE.json',user_stage)])
        return
    if group=='artifact':
        _,projection,ret,bundle,review,user_stage,closed=full_artifact_review_chain()
        _write_example_jsons([
          ('ARTIFACT_CODEX_HANDOFF_PROJECTION.json',projection),('ARTIFACT_CODEX_EXECUTION_RETURN.json',ret),
          ('ARTIFACT_CODEX_EXECUTION_EVIDENCE_BUNDLE.json',bundle),('ARTIFACT_BRAIN_REVIEW_CAPSULE.json',review),
          ('ARTIFACT_USER_ACCEPTANCE_CAPSULE.json',user_stage),('ARTIFACT_CLOSED_CAPSULE.json',closed)])
        return
    raise ValueError(f'unknown example group: {group}')


def write_examples():
    # Generate independent example families without creating any new authority or
    # background control plane. These are short-lived mechanical fixture builds.
    for group in ('artifact','repository','discovery','core'):
        write_examples_group(group)


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--group',choices=['core','discovery','repository','artifact'])
    args=ap.parse_args()
    if args.group: write_examples_group(args.group)
    else: write_examples()
