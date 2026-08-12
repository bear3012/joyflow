from __future__ import annotations
import copy, unittest
from tests import build_fixture as f
c=f.c


def reseal_snapshot(row):
    row=copy.deepcopy(row)
    fiber=row['active_fibers']['execution_review']
    fiber['fiber_digest']=c.digest(c.strip_digest(fiber,'fiber_digest'))
    row['capsule_digest']=c.digest(c.capsule_payload(row))
    row['derived_gates']=c.compute_gate_snapshot(row)
    return row


class ArchitectureConvergenceFreezeBindingTests(unittest.TestCase):
    def test_repository_user_acceptance_stage_without_freeze_blocks(self):
        *_, user_stage, _ = f.full_repository_review_chain()
        row=copy.deepcopy(user_stage)
        row['active_fibers']['execution_review']['payload']['merge_candidate_freeze_digest']=None
        row=reseal_snapshot(row)
        with self.assertRaises(c.JoyflowError):
            c.validate_capsule(row)

    def test_repository_acceptance_pass_without_freeze_blocks(self):
        *_, merge_stage = f.full_repository_review_chain()
        row=copy.deepcopy(merge_stage)
        row['active_fibers']['execution_review']['payload']['merge_candidate_freeze_digest']=None
        row=reseal_snapshot(row)
        with self.assertRaises(c.JoyflowError):
            c.validate_capsule(row)

    def test_repository_acceptance_not_applicable_without_freeze_blocks(self):
        *_, user_stage, _ = f.full_repository_review_chain()
        row=copy.deepcopy(user_stage)
        payload=row['active_fibers']['execution_review']['payload']
        payload['user_acceptance']='NOT_APPLICABLE'
        payload['user_acceptance_evidence_refs']=[]
        payload['acceptance_not_applicable_reason']='No separate user-visible acceptance surface applies to this frozen PR candidate.'
        payload['merge_candidate_freeze_digest']=None
        row['task_progress']['stage']='MERGE_DECISION'
        row['task_progress']['transition_event']['to_stage']='MERGE_DECISION'
        row=reseal_snapshot(row)
        with self.assertRaises(c.JoyflowError):
            c.validate_capsule(row)

    def test_merge_ready_cannot_be_derived_without_freeze(self):
        *_, merge_stage = f.full_repository_review_chain()
        row=copy.deepcopy(merge_stage)
        row['active_fibers']['execution_review']['payload']['merge_candidate_freeze_digest']=None
        row=reseal_snapshot(row)
        self.assertNotEqual(row['derived_gates']['merge_gate'],'MERGE_READY')

if __name__=='__main__': unittest.main()
