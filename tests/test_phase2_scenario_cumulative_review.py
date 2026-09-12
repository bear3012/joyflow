from __future__ import annotations
import copy, unittest
from tests.build_fixture import full_repository_review_chain, revise_review
from runtime import joyflow_dual_layer as c

class Phase2ScenarioCumulativeReviewTests(unittest.TestCase):
    def test_brain_pass_requires_scenario_and_cumulative_pass(self):
        _,_,_,_,_,review,_=full_repository_review_chain()
        payload=review['active_fibers']['execution_review']['payload']
        self.assertEqual(payload['brain_review_verdict'],'PASS')
        self.assertEqual(payload['scenario_goal_review']['product_goal_result'],'PASS')
        self.assertEqual(payload['cumulative_review']['verdict'],'PASS')
        c.validate_execution_review(review)

    def test_prior_behavior_exact_set_required(self):
        _,_,_,_,_,review,_=full_repository_review_chain()
        row=copy.deepcopy(review); row['active_fibers']['execution_review']['payload']['cumulative_review']['relevant_prior_behaviors']=[]
        row['active_fibers']['execution_review']['fiber_digest']=None; row['capsule_digest']=None
        with self.assertRaises(Exception): c.prepare_capsule_structural_fixture(row)

    def test_expanded_impact_cannot_pass(self):
        _,_,_,_,_,review,_=full_repository_review_chain()
        row=copy.deepcopy(review); p=row['active_fibers']['execution_review']['payload']; p['cumulative_review']['impact_comparison']['unexpected_paths']=['shared/schema.py']; p['cumulative_review']['impact_comparison']['status']='EXPANDED_REQUIRES_RECLOSURE'; row['active_fibers']['execution_review']['fiber_digest']=None; row['capsule_digest']=None
        with self.assertRaises(Exception): c.prepare_capsule_structural_fixture(row)

    def test_known_limits_required_as_truthful_boundary(self):
        _,_,_,_,_,review,_=full_repository_review_chain()
        self.assertTrue(review['active_fibers']['execution_review']['payload']['scenario_goal_review']['known_limits'])

class Phase2CumulativeTruthBindingTests(unittest.TestCase):
    def _reseal_expect_fail(self,row):
        row['active_fibers']['execution_review']['fiber_digest']=None; row['capsule_digest']=None
        with self.assertRaises(Exception): c.prepare_capsule_structural_fixture(row)

    def test_preserved_behavior_unknown_evidence_is_rejected(self):
        _,_,_,_,_,review,_=full_repository_review_chain()
        row=copy.deepcopy(review)
        row['active_fibers']['execution_review']['payload']['cumulative_review']['relevant_prior_behaviors'][0]['evidence_refs']=['E_DOES_NOT_EXIST']
        self._reseal_expect_fail(row)

    def test_brain_cannot_record_user_risk_acceptance_without_user_decision(self):
        _,_,_,_,_,review,_=full_repository_review_chain()
        row=copy.deepcopy(review); p=row['active_fibers']['execution_review']['payload']
        p['scenario_goal_review']['critical_high_loss_risks']=[{'risk_id':'R_DATA_LOSS','risk':'Permanent data loss','status':'RESIDUAL_ACCEPTED_BY_USER','evidence_refs':['BRAIN_REVIEW_CURRENT'],'affected_global_invariant_ids':[]}]
        self._reseal_expect_fail(row)

    def test_blocked_high_loss_risk_cannot_coexist_with_brain_pass(self):
        _,_,_,_,_,review,_=full_repository_review_chain()
        row=copy.deepcopy(review); p=row['active_fibers']['execution_review']['payload']
        p['scenario_goal_review']['critical_high_loss_risks']=[{'risk_id':'R_DATA_LOSS','risk':'Permanent data loss','status':'BLOCKED','evidence_refs':['BRAIN_REVIEW_CURRENT'],'affected_global_invariant_ids':[]}]
        self._reseal_expect_fail(row)

    def test_impact_comparison_must_match_exact_pr_diff(self):
        _,_,_,_,_,review,_=full_repository_review_chain()
        row=copy.deepcopy(review); p=row['active_fibers']['execution_review']['payload']
        p['cumulative_review']['impact_comparison']['observed_paths']=[]
        self._reseal_expect_fail(row)

class Phase2UserAuthorityPositiveTests(unittest.TestCase):
    def test_brain_may_record_user_risk_acceptance_when_exact_user_decision_exists(self):
        _,_,_,_,_,review,_=full_repository_review_chain()
        row=copy.deepcopy(review)
        ev={'evidence_id':'USER_ACCEPT_RISK_R1','authority':'USER_DECISION','kind':'PRODUCT_DECISION','ref':'conversation:risk-r1','claim':'User accepts residual risk R1 for the current bounded scenario.','claim_digest':None,'produced_by':'WEB_BRAIN','subject_type':'RISK','subject_id':'R1','raw_output_ref':None}
        ev['claim_digest']=c.digest(ev['claim']); row['evidence_registry'].append(ev)
        row['active_fibers']['execution_review']['payload']['scenario_goal_review']['critical_high_loss_risks']=[{'risk_id':'R1','risk':'Residual bounded risk','status':'RESIDUAL_ACCEPTED_BY_USER','evidence_refs':['USER_ACCEPT_RISK_R1'],'affected_global_invariant_ids':[]}]
        c.validate_scenario_cumulative_review(c.load_model(),row)

class Phase2AuthorizedEvolutionTests(unittest.TestCase):
    def test_user_authorized_prior_behavior_change_can_close_with_reclosure(self):
        _,_,_,_,_,review,_=full_repository_review_chain()
        row=copy.deepcopy(review)
        planned=row['task_anchor']['planning_context']['relevant_prior_behaviors'][0]
        planned['expected_disposition']='CHANGE_AUTHORIZED'
        ev={'evidence_id':'USER_AUTHORIZE_PHASE1_OBJECT_CHANGE','authority':'USER_DECISION','kind':'PRODUCT_DECISION','ref':'conversation:authorize-phase1-object-change','claim':'User authorizes changing prior behavior PHASE1_OBJECT_TRUTH in the current bounded change unit.','claim_digest':None,'produced_by':'WEB_BRAIN','subject_type':'PRIOR_BEHAVIOR_DISPOSITION','subject_id':'PHASE1_OBJECT_TRUTH:CHANGE_AUTHORIZED','raw_output_ref':None}
        ev['claim_digest']=c.digest(ev['claim']); row['evidence_registry'].append(ev); planned['authorization_refs']=[ev['evidence_id']]
        actual=row['active_fibers']['execution_review']['payload']['cumulative_review']['relevant_prior_behaviors'][0]
        actual['status']='CHANGED_WITH_RECLOSURE'
        c.validate_pr_goal_scenario_grounding(c.load_model(),row)
        c.validate_scenario_cumulative_review(c.load_model(),row)

class Phase2ClaimSupportRelevanceReviewTests(unittest.TestCase):
    def _expect_fail(self,row):
        row['active_fibers']['execution_review']['fiber_digest']=None; row['capsule_digest']=None
        with self.assertRaises(Exception): c.prepare_capsule_structural_fixture(row)

    def _first_machine_ref(self,review):
        for item in review['active_fibers']['execution_review']['payload']['validation_results']:
            if item['machine_results']:
                return item['machine_results'][0]['evidence_ref']
        raise AssertionError('fixture lacks machine evidence')

    def test_unrelated_test_cannot_control_high_loss_risk(self):
        _,_,_,_,_,review,_=full_repository_review_chain()
        row=copy.deepcopy(review); machine_ref=self._first_machine_ref(row)
        row['active_fibers']['execution_review']['payload']['scenario_goal_review']['critical_high_loss_risks']=[{'risk_id':'R_DATA_LOSS','risk':'Permanent data loss','status':'CONTROLLED_FOR_CURRENT_SCENARIO','evidence_refs':[machine_ref],'affected_global_invariant_ids':[]}]
        self._expect_fail(row)

    def test_unrelated_test_cannot_prove_prior_behavior_preserved(self):
        _,_,_,_,_,review,_=full_repository_review_chain()
        row=copy.deepcopy(review); machine_ref=self._first_machine_ref(row)
        row['active_fibers']['execution_review']['payload']['cumulative_review']['relevant_prior_behaviors'][0]['evidence_refs']=[machine_ref]
        self._expect_fail(row)

    def test_unrelated_evidence_cannot_satisfy_exit_condition(self):
        _,_,_,_,_,review,_=full_repository_review_chain()
        row=copy.deepcopy(review)
        row['active_fibers']['execution_review']['payload']['cumulative_review']['exit_condition_results'][0]['evidence_refs']=['E_USER_MODEL']
        self._expect_fail(row)

class Phase2CanonicalDispositionProseTests(unittest.TestCase):
    def test_canonical_phase2c_prose_does_not_require_all_relevant_behaviors_preserved(self):
        from pathlib import Path
        text=(Path(__file__).resolve().parents[1]/'project_sources/23_PHASE2C_SCENARIO_CUMULATIVE_REVIEW.md').read_text(encoding="utf-8")
        self.assertNotIn('requires those behaviors to remain preserved', text)
        self.assertIn('close according to its approved expected disposition', text)
