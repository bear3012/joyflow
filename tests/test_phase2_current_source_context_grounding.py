from __future__ import annotations
import copy, unittest
from tests.build_fixture import at_user_approval, new_capsule
from runtime import joyflow_dual_layer as c

class Phase2CurrentSourceContextTests(unittest.TestCase):
    def test_repair_requires_problem_reality(self):
        row=new_capsule('REPAIR_STANDARD','REPOSITORY_CHANGE')
        row['active_fibers']['decision_boundary']['payload']['problem_reality']='NOT_APPLICABLE'
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(row)

    def test_no_change_cannot_enter_mutating_approval(self):
        row=at_user_approval('REPAIR_STANDARD','REPOSITORY_CHANGE')
        row=copy.deepcopy(row); row['active_fibers']['decision_boundary']['payload']['problem_reality']='NO_CHANGE_REQUIRED'; row['capsule_digest']=None
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(row)

    def test_projection_derives_current_source_context_without_second_owner(self):
        cap=at_user_approval('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        proj=c.build_projection(cap)
        original=copy.deepcopy(proj)
        ctx=c.derived_current_source_view(proj)
        self.assertNotIn('current_source_context',proj)
        self.assertEqual(ctx['context_status'],'SUFFICIENT')
        self.assertEqual(ctx['source_binding']['repository_id'],cap['task_anchor']['repository_anchor']['repository_id'])
        self.assertEqual(ctx['source_binding']['execution_object_digest'],proj['execution_object']['physical_object']['digest'])
        self.assertIn('runtime/**',ctx['mutation_paths'])
        self.assertTrue(ctx['historical_retrieval_refs'])
        self.assertEqual(ctx,c.derived_current_source_view(proj))
        ctx['mutation_paths'].append('not-authorized/**')
        self.assertEqual(proj,original)
        self.assertEqual(proj['projection_digest'],c.digest(c.projection_payload(proj)))

    def test_unresolved_impact_blocks_approval(self):
        row=new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        row['active_fibers']['repository_evidence']['payload']['impact_coverage'][0]['status']='UNRESOLVED'
        row=c.prepare_capsule_structural_fixture(row)
        # advancing to approval must fail because current-source context remains incomplete
        from tests.build_fixture import advance
        row=advance(row,'DECISION_CLOSURE')
        with self.assertRaises(Exception): advance(row,'USER_APPROVAL')

class Phase2CurrentSourceTruthBindingTests(unittest.TestCase):
    def test_user_decision_cannot_prove_source_impact_coverage(self):
        row=new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        for item in row['active_fibers']['repository_evidence']['payload']['impact_coverage']:
            item['evidence_refs']=['E_USER_MODEL']
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(row)

    def test_direct_implementation_cannot_be_not_applicable_for_mutation(self):
        row=new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        row['active_fibers']['repository_evidence']['payload']['impact_coverage'][0]['status']='NOT_APPLICABLE'
        row=c.prepare_capsule_structural_fixture(row)
        from tests.build_fixture import advance
        row=advance(row,'DECISION_CLOSURE')
        with self.assertRaises(Exception): advance(row,'USER_APPROVAL')

class Phase2ImpactSupportRelevanceTests(unittest.TestCase):
    def test_generic_tree_snapshot_cannot_prove_every_impact_dimension(self):
        row=new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        for item in row['active_fibers']['repository_evidence']['payload']['impact_coverage']:
            item['evidence_refs']=['E_GITHUB_PATHS']
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(row)
