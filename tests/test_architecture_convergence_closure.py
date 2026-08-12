from __future__ import annotations
import copy, unittest
from tests import build_fixture as f
c=f.c

class ArchitectureConvergenceClosureTests(unittest.TestCase):
    def test_active_development_instruction_activation_is_consistent(self):
        import json, pathlib
        root=pathlib.Path(__file__).resolve().parents[1]
        model=c.load_model()
        lineage=json.loads((root/'PHASE2_STAGE_LINEAGE.json').read_text(encoding='utf-8'))
        self.assertEqual(model['phase2_extension']['architecture_change_activation'],'ACTIVE_BY_EXPLICIT_USER_CONFIRMATION')
        self.assertEqual(lineage['project_instruction_change_status']['active_instruction']['status'],'ACTIVE_BY_EXPLICIT_USER_CONFIRMATION')

    def test_current_merge_projection_semantics_are_converged_across_surfaces(self):
        import pathlib
        root=pathlib.Path(__file__).resolve().parents[1]
        boot=(root/'00_PROJECT_INSTRUCTIONS_BOOTLOADER_PHASE1_COMBINED_CAPABILITY_COVERAGE_REPAIR_CANDIDATE.md').read_text(encoding='utf-8')
        source=(root/'project_sources/13_PHASE1E_AI_NATIVE_CHANGE_PROJECTION.md').read_text(encoding='utf-8')
        runtime=(root/'runtime/joyflow_phase1_review.py').read_text(encoding='utf-8')
        lower=boot.lower()
        self.assertNotIn('public pr ci must consume the exact external merged change projection', lower)
        self.assertNotIn('only after the exact merged change projection, current pr ci result', lower)
        self.assertIn('without consuming a Merged Change Projection', boot)
        self.assertIn('does not require a Merged Change Projection', boot)
        self.assertIn('without consuming a Merged Change Projection', source)
        self.assertIn('Merged Change Projection is post-merge navigation context, not a PR review input', runtime)

    def test_generated_surfaces_use_converged_merge_semantics(self):
        initial=f.initial_sealed('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        approval=f.at_user_approval('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        projection,view,_=c.draft_handoff(approval)
        approved,_,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        _,prompt=c.compile_handoff(approved)
        materials=[initial['task_anchor']['goal'],initial['task_anchor']['desired_result'],projection['task_anchor']['goal'],projection['task_anchor']['desired_result'],view,prompt]
        for material in materials:
            lower=material.lower()
            self.assertNotIn('pr ci and merge freeze consume the exact projection',lower)
            self.assertNotIn('pr ci must consume the exact external merged change projection',lower)
        self.assertIn('Brain Review PASS plus current PR CI PASS produces an exact Merge Candidate Freeze',initial['task_anchor']['desired_result'])
        self.assertIn('Merged Change Projection is optional post-merge navigation',initial['task_anchor']['desired_result'])
        self.assertIn('final merge authorization is a separate exact-object user decision',initial['task_anchor']['desired_result'])

    def test_initial_capsule_contains_policy_not_premature_task_approval(self):
        initial=f.initial_sealed('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        self.assertEqual(initial['approval_record']['status'],'NEEDS_USER_APPROVAL')
        rows={r['evidence_id']:r for r in initial['evidence_registry']}
        self.assertNotIn('E_USER_APPROVAL',rows)
        policy=rows['E_USER_AUTHORIZATION_POLICY']
        self.assertEqual(policy['authority'],'USER_DECISION')
        self.assertEqual(policy['kind'],'PRODUCT_DECISION')
        self.assertIn('mutation/material execution requires current explicit user approval',policy['claim'])
        self.assertIn('execution approval does not authorize final merge',policy['claim'])
        for row in initial['evidence_registry']:
            if row['authority']=='USER_DECISION':
                self.assertNotIn('User explicitly approves mutation/material Codex execution',row['claim'])

    def test_task_execution_approval_does_not_claim_final_merge_authorization(self):
        approved,_,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        self.assertEqual(approved['approval_record']['status'],'APPROVED_FINAL')
        self.assertEqual(approved['approval_record']['basis'],'CURRENT_EXPLICIT_USER_DECISION')
        rows={r['evidence_id']:r for r in approved['evidence_registry']}
        self.assertIn('E_USER_AUTHORIZATION_POLICY',rows)
        self.assertIn('Execution approval and merge approval are separate human gates.',rows['E_USER_MERGE']['claim'])
        for row in approved['evidence_registry']:
            if row['authority']=='USER_DECISION':
                self.assertNotIn('User explicitly approves mutation/material Codex execution and final merge',row['claim'])

    def test_same_envelope_rework_is_attempt_not_cycle_trigger(self):
        model=c.load_model()
        self.assertNotIn('REEXECUTION_REQUIRED',model['cycle_triggers'])
        policy=model['mutation_execution_envelope_policy']
        self.assertEqual(policy['approval_cycle_semantics'],'MATERIAL_RECLOSURE_OR_NEW_AUTHORIZATION_BOUNDARY')
        self.assertEqual(policy['execution_attempt_semantics'],'CURRENT_IMPLEMENTATION_ATTEMPT_WITHIN_STABLE_AUTHORIZATION_ENVELOPE')

    def test_product_tolerance_must_be_user_confirmed(self):
        row=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        a=row['task_anchor']['planning_context']['material_operating_assumptions'][0]
        a['condition_type']='PRODUCT_TOLERANCE'
        a['source_basis']='BRAIN_INFERENCE'
        a['epistemic_status']='INFERRED'
        with self.assertRaises(c.JoyflowError):
            c.prepare_capsule_structural_fixture(row)

    def _storage_capsule(self, route: str, required_depth: str):
        row=f.new_capsule(route,'REPOSITORY_CHANGE')
        semantic=row['active_fibers']['semantic']['payload']['semantic_items'][0]
        semantic['risk_markers']=['STORAGE']
        assumption=row['task_anchor']['planning_context']['material_operating_assumptions'][0]
        row['active_fibers']['decision_boundary']['payload']['risk_controls']=[{
            'control_id':'RISK_STORAGE_CONTEXT','marker':'STORAGE',
            'statement':'Storage risk is evaluated from the bounded operating condition and recovery path rather than a static route label.',
            'evidence_refs':['E_COLD_REVIEW'],
            'failure_mechanism':'A write can fail after local state has begun changing.',
            'technical_consequence':'The bounded task could leave incomplete local state if the implementation lacks rollback.',
            'recoverability':'The approved implementation must rollback or reconstruct the bounded local state.',
            'operating_condition_refs':[c.support_subject_id(assumption['assumption'])],
            'required_assurance_depth':required_depth,'hard_floor_applied':False,
        }]
        return f.refresh(row)

    def test_contextual_storage_risk_can_use_standard_depth(self):
        row=self._storage_capsule('DEVELOPMENT_STANDARD','STANDARD')
        c.prepare_capsule_structural_fixture(row)

    def test_contextual_storage_risk_cannot_silently_weaken_required_depth(self):
        row=self._storage_capsule('DEVELOPMENT_LIGHT','STANDARD')
        with self.assertRaises(c.JoyflowError):
            c.prepare_capsule_structural_fixture(row)

    def test_approval_binding_is_stable_across_nonmaterial_implementation_route_change(self):
        _,projection,_,binding=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        changed=copy.deepcopy(projection)
        changed['technical_route_space']['candidate_routes'][0]['summary']='Equivalent repository-grounded implementation alternative inside the same approved outcome boundary.'
        self.assertEqual(binding,c.approval_binding(changed))

    def test_approval_binding_changes_when_product_result_changes(self):
        _,projection,_,binding=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        changed=copy.deepcopy(projection)
        changed['task_anchor']['desired_result'] += ' MATERIAL PRODUCT CHANGE'
        self.assertNotEqual(binding,c.approval_binding(changed))

    def test_active_global_invariant_cannot_be_waived_as_residual_risk(self):
        _,_,_,_,_,review,_=f.full_repository_review_chain()
        row=copy.deepcopy(review)
        invariant=row['active_fibers']['semantic']['payload']['semantic_items'][0]
        invariant['material_class']='GLOBAL_INVARIANT'
        ev={'evidence_id':'USER_ACCEPT_RISK_INV','authority':'USER_DECISION','kind':'PRODUCT_DECISION','ref':'conversation:risk-invariant','claim':'User accepts residual risk R_INV for the current bounded scenario.','claim_digest':None,'produced_by':'WEB_BRAIN','subject_type':'RISK','subject_id':'R_INV','raw_output_ref':None}
        ev['claim_digest']=c.digest(ev['claim']); row['evidence_registry'].append(ev)
        row['active_fibers']['execution_review']['payload']['scenario_goal_review']['critical_high_loss_risks']=[{
            'risk_id':'R_INV','risk':'Residual risk conflicts with an active global invariant','status':'RESIDUAL_ACCEPTED_BY_USER','evidence_refs':['USER_ACCEPT_RISK_INV'],'affected_global_invariant_ids':[invariant['item_id']]}]
        with self.assertRaises(c.JoyflowError):
            c.validate_scenario_cumulative_review(c.load_model(),row)

    def test_brain_review_failure_same_envelope_is_same_cycle_and_same_approval(self):
        approved,_,_,_,review,_,_=f.full_repository_review_chain()
        blocked=f.revise_review(review,'BRAIN_REVIEW',brain_verdict='BLOCK')
        rework=f.advance(blocked,'CODEX_EXECUTION',event_type='BRAIN_REVIEW_FAILED',trigger='NONE',
            evidence_refs=['BRAIN_REVIEW_CURRENT'],reason='Same-envelope implementation defect requires bounded rework.')
        self.assertEqual(rework['task_progress']['cycle'],blocked['task_progress']['cycle'])
        _,_,binding=c.draft_handoff(rework)
        self.assertEqual(binding,approved['approval_record']['binding'])
        self.assertEqual(rework['approval_record']['binding'],approved['approval_record']['binding'])

    def test_user_acceptance_failure_same_envelope_is_same_cycle_and_same_approval(self):
        approved,_,_,_,_,user_stage,_=f.full_repository_review_chain()
        blocked=f.revise_review(user_stage,'USER_ACCEPTANCE',user_acceptance='BLOCK')
        rework=f.advance(blocked,'CODEX_EXECUTION',event_type='USER_ACCEPTANCE_FAILED',trigger='NONE',
            evidence_refs=['USER_ACCEPT_CURRENT'],reason='Same-envelope user-visible defect requires bounded rework.')
        self.assertEqual(rework['task_progress']['cycle'],blocked['task_progress']['cycle'])
        _,_,binding=c.draft_handoff(rework)
        self.assertEqual(binding,approved['approval_record']['binding'])
        self.assertEqual(rework['approval_record']['binding'],approved['approval_record']['binding'])

    def test_role_executability_policy_requires_real_web_local_handoff(self):
        p=c.load_model()['role_executability_policy']
        self.assertEqual(p['web_brain_surface'],'WEB_ONLY')
        self.assertEqual(p['executor_surface'],'LOCAL_CODEX')
        self.assertTrue(p['logical_authorization_is_not_automatic_invocation'])
        self.assertEqual(p['handoff_topology'],'USER_MEDIATED_SEMIAUTOMATIC')
        self.assertTrue(p['connector_specific_dependency_forbidden'])
        self.assertFalse(p['background_controller_required'])

if __name__=='__main__': unittest.main()
