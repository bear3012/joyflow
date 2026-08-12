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

    def test_projection_contains_current_source_context(self):
        cap=at_user_approval('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        proj=c.build_projection(cap)
        ctx=proj['current_source_context']
        self.assertEqual(ctx['context_status'],'SUFFICIENT')
        self.assertEqual(ctx['source_binding']['baseline_commit'],'abc123')
        self.assertIn('runtime/**',ctx['selected_paths'])
        self.assertTrue(ctx['historical_retrieval_refs'])

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
