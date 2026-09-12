from __future__ import annotations
import copy, unittest
from tests import build_fixture as f
compiler=f.c

class ReadOnlyDiscoveryAuthorizationTests(unittest.TestCase):
    def test_read_only_discovery_compiles_with_brain_authorization_without_user_approval_state(self):
        cap,projection,view,_=f.approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY')
        self.assertEqual(cap['task_progress']['stage'],'DECISION_CLOSURE')
        self.assertEqual(cap['approval_record']['status'],'AUTHORIZED_READ_ONLY_DISCOVERY')
        self.assertEqual(cap['approval_record']['basis'],'WEB_BRAIN_BOUNDED_READ_ONLY_DISCOVERY_AUTHORIZATION')
        self.assertNotEqual(cap['approval_record']['basis'],'CURRENT_EXPLICIT_USER_DECISION')
        projection2,prompt=compiler.compile_handoff(cap)
        self.assertEqual(projection2['execution_mode'],'READ_ONLY')
        self.assertIn('BRAIN READ-ONLY DISCOVERY AUTHORIZATION VIEW',view)
        self.assertIn('Logical authorization does not automatically invoke Local Codex',view)
        self.assertIn('Do not modify files',prompt)

    def test_read_only_discovery_rejects_forged_user_approval_semantics(self):
        cap,_,_,_=f.approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY')
        bad=copy.deepcopy(cap)
        bad['approval_record'].update({'status':'APPROVED_FINAL','basis':'CURRENT_EXPLICIT_USER_DECISION','decision_ref':'conversation:fake-read-only-user-approval'})
        bad=f.refresh(bad)
        with self.assertRaises(compiler.JoyflowError): compiler.compile_handoff(bad)

    def test_read_only_brain_authorization_cannot_authorize_mutation(self):
        cap,_,_,_=f.approved_capsule('PROTOCOL_CHANGE','ARTIFACT_CHANGE')
        bad=copy.deepcopy(cap)
        bad['approval_record'].update({'status':'AUTHORIZED_READ_ONLY_DISCOVERY','scope':'READ_ONLY_DISCOVERY_ONLY','basis':'WEB_BRAIN_BOUNDED_READ_ONLY_DISCOVERY_AUTHORIZATION','decision_ref':'brain:read-only-only'})
        bad=f.refresh(bad)
        with self.assertRaises(compiler.JoyflowError): compiler.compile_handoff(bad)

    def test_mutating_execution_still_requires_current_explicit_user_approval(self):
        cap=f.at_user_approval('PROTOCOL_CHANGE','ARTIFACT_CHANGE')
        self.assertEqual(cap['approval_record']['status'],'NEEDS_USER_APPROVAL')
        with self.assertRaises(compiler.JoyflowError): compiler.compile_handoff(cap)

    def test_read_only_route_cannot_enter_user_approval_stage(self):
        initial=f.initial_sealed('READ_ONLY_DISCOVERY','READ_ONLY')
        decision=f.advance(initial,'DECISION_CLOSURE')
        with self.assertRaises(compiler.JoyflowError):
            f.advance(decision,'USER_APPROVAL')

if __name__=='__main__': unittest.main()
