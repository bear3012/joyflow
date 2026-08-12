from __future__ import annotations
import copy, pathlib, subprocess, sys, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runtime import joyflow_dual_layer as c
from tests import build_fixture as f
from tests import phase1_review_fixture as review_fx

class SingleActiveTaskRoundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._merge_td, cls._merge_repo, cls._merge_base, cls._merge_head = review_fx.create_repository()
        cls._merge_chain = review_fx.full_merge_authorization_chain(cls._merge_repo, cls._merge_base, cls._merge_head)

    @classmethod
    def tearDownClass(cls):
        cls._merge_td.cleanup()

    def test_all_routes_have_legal_initial_capsule(self):
        model=c.load_model()
        for route,profile in model['route_profiles'].items():
            with self.subTest(route=route):
                cap=f.initial_sealed(route,profile['allowed_change_scopes'][0])
                self.assertEqual(cap['task_progress']['stage'],profile['initial_stage'])

    def test_initial_capsule_cannot_start_late(self):
        state=f.new_capsule(); state['task_progress']['stage']='MERGE_DECISION'; state['task_progress']['transition_event']['to_stage']='MERGE_DECISION'
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(state)

    def test_parent_checked_only_when_new_revision_sealed(self):
        first=f.initial_sealed(); second=f.advance(first,'USER_APPROVAL')
        c.validate_capsule(second)
        bad=copy.deepcopy(second); bad['task_progress']['parent_capsule_digest']='0'*64; bad['capsule_digest']=None; bad['derived_gates']={}
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(bad,first)

    def test_model_declares_one_active_task_per_project_round_without_scheduler(self):
        model=c.load_model(); rule=model['single_active_round']
        self.assertTrue(rule['one_active_task_per_project_round'])
        self.assertFalse(rule['global_scheduler_required'])
        self.assertEqual(rule['owner'],'WEB_BRAIN')

    def test_draft_cannot_compile(self):
        with self.assertRaises(c.JoyflowError): c.compile_handoff(f.at_user_approval())

    def test_brain_recorded_exact_approval_compiles(self):
        cap,_,_,_=f.approved_capsule(); projection,prompt=c.compile_handoff(cap); c.verify_prompt(projection,cap['approval_record'],prompt)

    def test_codex_cannot_own_approval(self):
        cap,_,_,_=f.approved_capsule(); cap=copy.deepcopy(cap); cap['approval_record']['owner']='CODEX'; cap['derived_gates']=c.compute_gate_snapshot(cap)
        with self.assertRaises(Exception): c.validate_capsule(cap)

    def test_approval_requires_current_decision_ref(self):
        cap,_,_,_=f.approved_capsule(); cap=copy.deepcopy(cap); cap['approval_record']['decision_ref']=None; cap['derived_gates']=c.compute_gate_snapshot(cap)
        with self.assertRaises(Exception): c.compile_handoff(cap)

    def test_approval_binding_change_blocks(self):
        cap,_,_,_=f.approved_capsule(); cap=copy.deepcopy(cap); cap['approval_record']['binding']['projection_digest']='0'*64; cap['derived_gates']=c.compute_gate_snapshot(cap)
        with self.assertRaises(c.JoyflowError): c.compile_handoff(cap)

    def test_codex_return_validates_for_current_round(self):
        cap,_,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); projection,_=c.compile_handoff(cap); ret,bundle=f.codex_return(projection)
        c.validate_codex_execution_return_structure(ret,projection,bundle)

    def test_codex_return_cannot_change_project_task_or_round(self):
        cap,_,_,_=f.approved_capsule(); projection,_=c.compile_handoff(cap); ret,bundle=f.codex_return(projection)
        for field,value in [('project_id','OTHER'),('task_id','OTHER'),('round_id',projection['round_id']+1)]:
            with self.subTest(field=field):
                bad=copy.deepcopy(ret); bad[field]=value; bad['return_digest']=c.digest(c.strip_digest(bad,'return_digest'))
                with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(bad,projection,bundle)

    def test_evidence_bundle_swap_blocks_without_return_change(self):
        cap,_,_,_=f.approved_capsule(); projection,_=c.compile_handoff(cap); ret,bundle=f.codex_return(projection)
        bad=copy.deepcopy(bundle); bad['evidence_rows'][0]['claim']='Different bundle content'; bad['evidence_rows'][0]['claim_digest']=c.digest(bad['evidence_rows'][0]['claim']); bad['evidence_bundle_digest']=c.digest(c.strip_digest(bad,'evidence_bundle_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(ret,projection,bad)

    def test_codex_return_cannot_fill_brain_or_user_or_merge(self):
        cap,_,_,_=f.approved_capsule(); projection,_=c.compile_handoff(cap); ret,bundle=f.codex_return(projection)
        for field,value in [('brain_review_status','PASS'),('user_acceptance_status','PASS'),('merge_status','MERGE_ALLOWED')]:
            bad=copy.deepcopy(ret); bad[field]=value; bad['return_digest']=c.digest(c.strip_digest(bad,'return_digest'))
            with self.subTest(field=field), self.assertRaises(Exception): c.validate_codex_execution_return_structure(bad,projection,bundle)

    def test_completed_pass_requires_zero_exit(self):
        cap,_,_,_=f.approved_capsule(); projection,_=c.compile_handoff(cap); ret,bundle=f.codex_return(projection); ret['machine_results'][0]['exit_code']=1; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(ret,projection,bundle)

    def test_completed_cannot_contain_failed_check(self):
        cap,_,_,_=f.approved_capsule(); projection,_=c.compile_handoff(cap); ret,bundle=f.codex_return(projection); ret['machine_results'][0]['result']='FAIL'; ret['machine_results'][0]['exit_code']=1; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(ret,projection,bundle)

    def test_completed_cannot_contain_unresolved_items(self):
        cap,_,_,_=f.approved_capsule(); projection,_=c.compile_handoff(cap); ret,bundle=f.codex_return(projection); ret['unresolved_items']=['missing output']; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(ret,projection,bundle)

    def test_blocked_requires_unresolved_item(self):
        cap,_,_,_=f.approved_capsule(); projection,_=c.compile_handoff(cap); ret,bundle=f.codex_return(projection); ret['execution_status']='BLOCKED'; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(ret,projection,bundle)

    def test_machine_evidence_binds_obligation_and_check(self):
        cap,_,_,_=f.approved_capsule(); projection,_=c.compile_handoff(cap); ret,bundle=f.codex_return(projection); bundle=copy.deepcopy(bundle); bundle['evidence_rows'][0]['subject_id']='OTHER'; bundle['evidence_rows'][0]['claim_digest']=c.digest(bundle['evidence_rows'][0]['claim']); bundle['evidence_bundle_digest']=c.digest(c.strip_digest(bundle,'evidence_bundle_digest')); ret['evidence_bundle_digest']=bundle['evidence_bundle_digest']; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(ret,projection,bundle)

    def test_test_result_requires_raw_output_ref(self):
        cap,_,_,_=f.approved_capsule(); projection,_=c.compile_handoff(cap); ret,bundle=f.codex_return(projection); bundle=copy.deepcopy(bundle); bundle['evidence_rows'][0]['raw_output_ref']=None; bundle['evidence_bundle_digest']=c.digest(c.strip_digest(bundle,'evidence_bundle_digest')); ret['evidence_bundle_digest']=bundle['evidence_bundle_digest']; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(ret,projection,bundle)

    def test_repository_return_requires_pr(self):
        cap,_,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); projection,_=c.compile_handoff(cap); ret,bundle=f.codex_return(projection); ret['pr_evidence']=None; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(ret,projection,bundle)

    def test_artifact_return_requires_artifact_and_forbids_pr(self):
        cap,_,_,_=f.approved_capsule('ARTIFACT_REPAIR','ARTIFACT_CHANGE'); projection,_=c.compile_handoff(cap); ret,bundle=f.codex_return(projection); c.validate_codex_execution_return_structure(ret,projection,bundle)
        bad=copy.deepcopy(ret); bad['artifact_evidence']=None; bad['return_digest']=c.digest(c.strip_digest(bad,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(bad,projection,bundle)

    def test_touched_path_outside_allowed_blocks(self):
        cap,_,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); projection,_=c.compile_handoff(cap); ret,bundle=f.codex_return(projection); ret['pr_evidence']['touched_files']=['other/file.txt']; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(ret,projection,bundle)

    def test_repository_change_requires_allowed_path(self):
        state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); state['active_fibers']['semantic']['payload']['semantic_items'][0]['effects']=[x for x in state['active_fibers']['semantic']['payload']['semantic_items'][0]['effects'] if x['effect_type']!='ALLOW_PATH']; state=f.refresh(state)
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(state)

    def test_repository_fact_slot_authority_mismatch_blocks(self):
        state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); state['active_fibers']['repository_evidence']['payload']['fact_slots']['implementation_entry']['evidence_ref']='E_USER_MODEL'
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))

    def test_brain_review_sealing_checks_exact_projection_return_bundle(self):
        approved,projection,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); executing=f.advance(approved,'CODEX_EXECUTION'); ret,bundle=f.codex_return(projection)
        bad=copy.deepcopy(ret); bad['round_id']+=1; bad['return_digest']=c.digest(c.strip_digest(bad,'return_digest'))
        with self.assertRaises(Exception): f.brain_review_capsule(executing,projection,bad,bundle)

    def test_pending_brain_review_cannot_enter_user_acceptance(self):
        approved,projection,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); executing=f.advance(approved,'CODEX_EXECUTION'); ret,bundle=f.codex_return(projection); reviewing=f.brain_review_capsule(executing,projection,ret,bundle)
        with self.assertRaises(Exception): f.revise_review(reviewing,'USER_ACCEPTANCE')

    def test_brain_review_block_cannot_enter_user_acceptance(self):
        approved,projection,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); executing=f.advance(approved,'CODEX_EXECUTION'); ret,bundle=f.codex_return(projection); reviewing=f.brain_review_capsule(executing,projection,ret,bundle,brain_verdict='BLOCK')
        with self.assertRaises(Exception): f.revise_review(reviewing,'USER_ACCEPTANCE')

    def test_pending_user_acceptance_cannot_enter_merge_decision(self):
        *_,user_stage,_=f.full_repository_review_chain()
        with self.assertRaises(Exception): f.revise_review(user_stage,'MERGE_DECISION')

    def test_repository_task_cannot_close_inside_capsule(self):
        *_,merge_stage=f.full_repository_review_chain()
        with self.assertRaises(Exception): f.revise_review(merge_stage,'CLOSED')

    def test_artifact_review_and_closure_need_no_pr(self):
        *_,closed=f.full_artifact_review_chain(); self.assertEqual(closed['task_progress']['stage'],'CLOSED'); self.assertEqual(closed['derived_gates']['artifact_review_gate'],'PASS')

    def test_repository_review_rejects_artifact_target(self):
        approved,projection,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); executing=f.advance(approved,'CODEX_EXECUTION'); ret,bundle=f.codex_return(projection); reviewing=f.brain_review_capsule(executing,projection,ret,bundle)
        bad=copy.deepcopy(reviewing); p=bad['active_fibers']['execution_review']['payload']; p['review_target']={'target_type':'ARTIFACT','artifact_id':'x','artifact_digest':'a'*64,'artifact_validation_evidence_refs':['EXEC_DIFF']}; bad['active_fibers']['execution_review']['fiber_digest']=c.digest(c.strip_digest(bad['active_fibers']['execution_review'],'fiber_digest')); bad['capsule_digest']=c.digest(c.capsule_payload(bad)); bad['derived_gates']=c.compute_gate_snapshot(bad)
        with self.assertRaises(c.JoyflowError): c.validate_capsule(bad)

    def test_merge_ready_is_derived_snapshot_only(self):
        chain=self._merge_chain
        c.validate_merge_gate_record(chain['merge_ready'],chain['merge_candidate_freeze'],chain['user_acceptance'])
        self.assertEqual(chain['merge_ready']['artifact_role'],'DERIVED_GATE_SNAPSHOT_ONLY')

    def test_merge_allowed_is_derived_from_freeze_acceptance_and_user_authorization(self):
        chain=self._merge_chain
        with self.assertRaises(c.JoyflowError): c.validate_merge_gate_record(chain['merge_allowed'])
        c.validate_merge_gate_record(chain['merge_allowed'],chain['merge_candidate_freeze'],chain['user_acceptance'],chain['user_merge_authorization'])
        other=copy.deepcopy(chain['merge_candidate_freeze']); other['head_sha']='f'*40; other['freeze_digest']=c.digest(c.strip_digest(other,'freeze_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_merge_gate_record(chain['merge_allowed'],other,chain['user_acceptance'],chain['user_merge_authorization'])

    def test_completion_pointer_requires_freeze_acceptance_and_user_authorization_not_gate_snapshots(self):
        chain=self._merge_chain; pointer=chain['completion_pointer']
        with self.assertRaises(c.JoyflowError): c.validate_completion_pointer(pointer)
        c.validate_completion_pointer(pointer,chain['merge_candidate_freeze'],chain['user_acceptance'],chain['user_merge_authorization'])

    def test_automatic_promotion_is_blocked(self):
        with self.assertRaises(c.JoyflowError): c.validate_promotion_gate()

    def test_runtime_cli_has_no_automatic_promotion_command(self):
        out=subprocess.run([sys.executable,str(ROOT/'runtime/joyflow_dual_layer.py'),'-h'],capture_output=True,text=True,check=True).stdout
        self.assertNotIn('complete-promotion',out); self.assertNotIn('merge-authorization',out); self.assertIn('verify-codex-return',out)

    def test_prompt_records_current_round_and_no_automatic_promotion(self):
        cap,_,_,_=f.approved_capsule(); projection,prompt=c.compile_handoff(cap)
        self.assertEqual(projection['project_id'],cap['task_anchor']['project_id']); self.assertEqual(projection['round_id'],cap['task_progress']['cycle']); self.assertTrue(projection['delivery']['automatic_promotion_forbidden']); self.assertIn('Do not merge',prompt)

    def test_project_source_change_invalidates_prompt(self):
        cap,_,_,_=f.approved_capsule(); projection,prompt=c.compile_handoff(cap); path=ROOT/'project_sources/01_BRAIN_ROUTE_AUTHORITY.md'; original=path.read_bytes()
        try:
            path.write_bytes(original+b'\n<!-- mutation -->\n')
            with self.assertRaises(c.JoyflowError): c.verify_prompt(projection,cap['approval_record'],prompt)
        finally: path.write_bytes(original)

    def test_github_sufficient_path_discovery_skips_codex_local_discovery(self):
        cap=f.initial_sealed('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        state=cap['active_fibers']['repository_evidence']['payload']['path_discovery']
        self.assertEqual(state['github_discovery_status'],'COMPLETED_SUFFICIENT')
        self.assertFalse(state['local_discovery_required'])
        self.assertEqual(state['final_allowed_paths_status'],'CONFIRMED')

    def test_read_only_discovery_is_executable_only_after_github_insufficient(self):
        cap,projection,_,_=f.approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY')
        self.assertEqual(projection['execution_mode'],'READ_ONLY')
        self.assertFalse(projection['delivery']['mutation_allowed'])
        self.assertEqual(projection['delivery']['return_artifact_type'],'PATH_DISCOVERY_RETURN')
        self.assertEqual(cap['approval_record']['scope'],'READ_ONLY_DISCOVERY_ONLY')
        self.assertEqual(cap['approval_record']['status'],'AUTHORIZED_READ_ONLY_DISCOVERY')
        self.assertEqual(cap['approval_record']['basis'],'WEB_BRAIN_BOUNDED_READ_ONLY_DISCOVERY_AUTHORIZATION')
        self.assertEqual(cap['task_progress']['stage'],'DECISION_CLOSURE')

    def test_read_only_discovery_rejects_github_sufficient_state(self):
        state=f.new_capsule('READ_ONLY_DISCOVERY','READ_ONLY')
        pd=state['active_fibers']['repository_evidence']['payload']['path_discovery']
        pd.update({'github_discovery_status':'COMPLETED_SUFFICIENT','local_discovery_required':False,'local_discovery_reason':None,'local_discovery_status':'NOT_REQUIRED','final_allowed_paths_status':'CONFIRMED'})
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))

    def test_mutating_route_requires_brain_confirmed_final_boundary(self):
        state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        state['active_fibers']['repository_evidence']['payload']['path_discovery']['final_allowed_paths_status']='PENDING'
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))

    def test_path_discovery_return_is_bound_and_non_mutating(self):
        cap,projection,_,_=f.approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY')
        ret=f.path_discovery_return(projection)
        c.validate_path_discovery_return_structure(ret,projection)
        bad=copy.deepcopy(ret); bad['project_id']='OTHER'; bad['return_digest']=c.digest(c.strip_digest(bad,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return_structure(bad,projection)

    def test_path_discovery_return_rejects_path_escape(self):
        cap,projection,_,_=f.approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY')
        ret=f.path_discovery_return(projection); ret['confirmed_paths'][0]['path']='../secret'; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return_structure(ret,projection)

    def test_prompt_states_brain_final_boundary_and_no_mutation(self):
        cap,projection,_,_=f.approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY'); _,prompt=c.compile_handoff(cap)
        self.assertIn('Do not modify files',prompt)
        self.assertIn('do not',prompt.lower())
        self.assertEqual(projection['repository_evidence']['path_discovery']['final_boundary_owner'],'WEB_BRAIN')

    def test_generated_assets_match_model(self):
        r=subprocess.run([sys.executable,str(ROOT/'tools/generate_mechanical_assets.py'),'--check'],cwd=ROOT); self.assertEqual(r.returncode,0)

if __name__=='__main__': unittest.main()
