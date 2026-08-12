from __future__ import annotations
import copy, json, re, unittest, zlib, base64
from tests import build_fixture as f
from runtime import joyflow_dual_layer as c

class Phase2CompactHandoffDeltaResumeTests(unittest.TestCase):
    def test_compact_prompt_round_trip_keeps_exact_sealed_projection(self):
        cap,_,_,_=f.approved_capsule(); projection,prompt=c.compile_handoff(cap)
        parsed_projection,parsed_approval,parsed_view=c.parse_prompt(prompt)
        self.assertEqual(parsed_projection,projection)
        self.assertEqual(parsed_approval,cap['approval_record'])
        self.assertEqual(parsed_view,c.compact_execution_view(projection))
        self.assertNotIn('<JF_FIELD',prompt)
        self.assertNotIn('<JF_ITEMS',prompt)
        self.assertNotIn('<JF_LIST',prompt)
        self.assertEqual(prompt.count('<JOYFLOW_COMPACT_EXECUTION_VIEW encoding="json">'),1)
        c.verify_prompt(projection,cap['approval_record'],prompt)

    def test_compressed_envelope_is_exact_but_model_view_is_dynamic_only(self):
        cap,_,_,_=f.approved_capsule(); projection,prompt=c.compile_handoff(cap)
        m=c.ENVELOPE_RE.findall(prompt); self.assertEqual(len(m),1)
        envelope=c.compressed_envelope_decode(m[0])
        self.assertEqual(envelope['projection'],projection)
        self.assertEqual(envelope['approval_record'],cap['approval_record'])
        compact=c.compact_execution_view(projection)
        self.assertIn('current_source_context',compact)
        self.assertNotIn('traceability',compact)
        self.assertNotIn('task_object_lifecycle',compact)
        self.assertNotIn('codex_technical_authority',compact)

    def test_resume_view_is_derived_only_and_binds_current_capsule(self):
        cap,_,_,_=f.approved_capsule(); projection,_=c.compile_handoff(cap)
        view=c.current_resume_view(cap,projection)
        self.assertEqual(view['artifact_type'],'CURRENT_RESUME_VIEW')
        self.assertEqual(view['persistence'],'DERIVED_VIEW_ONLY')
        self.assertEqual(view['source_digests']['capsule_digest'],cap['capsule_digest'])
        self.assertEqual(view['source_digests']['projection_digest'],projection['projection_digest'])
        self.assertTrue(view['next_allowed_action'])

    def test_resume_view_collects_only_current_remaining_delta(self):
        _,_,_,_,review,_,_=f.full_repository_review_chain()
        view=c.current_resume_view(review)
        self.assertEqual(view['current_exact_object']['stage'],'BRAIN_REVIEW')
        self.assertEqual(view['parent_goal'],review['task_anchor']['planning_context']['parent_goal'])
        # A normal passing review has no invented backlog.
        self.assertEqual(view['remaining'],[])


class Phase2ResumeTruthBindingTests(unittest.TestCase):
    def test_resume_rejects_fake_projection_digest(self):
        cap,_,_,_=f.approved_capsule(); projection,_=c.compile_handoff(cap)
        fake=copy.deepcopy(projection); fake['projection_digest']='f'*64
        with self.assertRaises(c.JoyflowError): c.current_resume_view(cap,fake)

    def test_resume_uses_actual_user_acceptance_field(self):
        *_,merge=f.full_repository_review_chain()
        view=c.current_resume_view(merge)
        self.assertEqual(view['settled']['user_acceptance_status'],'PASS')

    def test_brain_block_requires_and_surfaces_rework_delta(self):
        approved,projection,ret,bundle,review,_,_=f.full_repository_review_chain()
        blocked=f.revise_review(review,'BRAIN_REVIEW',brain_verdict='BLOCK')
        view=c.current_resume_view(blocked)
        self.assertTrue(any(x['kind']=='REWORK_DELTA' for x in view['remaining']))
        self.assertEqual(view['next_allowed_action'],'RECLOSE_RECORDED_REWORK_DELTA')

class Phase2FailureDeltaNegativeTests(unittest.TestCase):
    def test_brain_block_without_rework_delta_is_rejected(self):
        _,_,_,_,_,review,_=f.full_repository_review_chain()
        row=copy.deepcopy(review); p=row['active_fibers']['execution_review']['payload']
        p['brain_review_verdict']='BLOCK'; p['scenario_goal_review']['product_goal_result']='BLOCK'; p['cumulative_review']['verdict']='BLOCK'; p['rework_delta']=[]
        for x in p['cumulative_review']['exit_condition_results']:
            x['status']='BLOCKED'; x['evidence_refs']=['BRAIN_REVIEW_CURRENT']
        with self.assertRaises(c.JoyflowError): c.validate_execution_review(row)
