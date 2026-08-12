from __future__ import annotations
import copy, unittest
from tests.build_fixture import new_capsule
from runtime import joyflow_dual_layer as c

class Phase2PRGoalScenarioGroundingTests(unittest.TestCase):
    def test_repository_change_requires_parent_goal(self):
        row=new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        row['task_anchor']['planning_context']['parent_goal']=None
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(row)

    def test_material_assumption_requires_reopen_trigger(self):
        row=new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        row['task_anchor']['planning_context']['material_operating_assumptions'][0]['reopen_trigger']=''
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(row)

    def test_prior_behavior_ids_must_be_unique(self):
        row=new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        prior=row['task_anchor']['planning_context']['relevant_prior_behaviors'][0]
        row['task_anchor']['planning_context']['relevant_prior_behaviors'].append(copy.deepcopy(prior))
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(row)

    def test_artifact_route_may_have_no_parent_goal(self):
        row=new_capsule('ARTIFACT_REPAIR','ARTIFACT_CHANGE')
        row['task_anchor']['planning_context']['parent_goal']=None
        c.prepare_capsule_structural_fixture(row)

class Phase2PlanningTruthTransportTests(unittest.TestCase):
    def test_prior_behavior_unknown_source_ref_is_rejected(self):
        row=new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        row['task_anchor']['planning_context']['relevant_prior_behaviors'][0]['source_refs']=['E_DOES_NOT_EXIST']
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(row)

    def test_user_approval_view_exposes_stable_mutation_envelope_not_internal_planning_dump(self):
        from tests.build_fixture import at_user_approval
        cap=at_user_approval('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        projection=c.build_projection(cap)
        view=c.render_approval_view(projection)
        self.assertIn('JOYFLOW USER MUTATION APPROVAL VIEW',view)
        self.assertIn('Authorization envelope',view)
        self.assertIn('Minimum validation',view)
        self.assertIn('Stop / re-closure conditions',view)
        self.assertNotIn('Current change-unit planning context',view)
        self.assertNotIn('material_operating_assumptions',view)
        self.assertNotIn(': None',view)

class Phase2ClaimSupportRelevancePlanningTests(unittest.TestCase):
    def test_unrelated_user_decision_cannot_confirm_different_operating_assumption(self):
        row=new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        assumption=row['task_anchor']['planning_context']['material_operating_assumptions'][0]
        assumption['assumption']='This product has 10,000 concurrent users.'
        assumption['material_effect']='Size architecture and validation for 10,000 concurrent users.'
        # Keep the original single-Brain/single-Codex user decision reference on purpose.
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(row)

    def test_unrelated_user_decision_cannot_authorize_prior_behavior_change(self):
        row=new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        prior=row['task_anchor']['planning_context']['relevant_prior_behaviors'][0]
        prior['expected_disposition']='CHANGE_AUTHORIZED'
        prior['authorization_refs']=['E_USER_MODEL']
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(row)
