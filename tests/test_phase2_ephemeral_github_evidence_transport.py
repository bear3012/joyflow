from __future__ import annotations
import copy, hashlib, json, pathlib, tempfile, unittest
from tests import build_fixture as f
from tests import phase1_review_fixture as rf
c=f.c


def github_plan():
    return {
      'mode':'GITHUB_EXACT_OBJECT_IF_NEEDED','transport_role':'CURRENT_ROUND_EVIDENCE_BUNDLE_TRANSPORT_ONLY',
      'github_surface':{'repository_id':'example/evidence-transport','temporary_ref':'refs/heads/joyflow-evidence/TASK_PHASE1E/round-1','path_prefix':'evidence/TASK_PHASE1E/round-1/','side_effect_status':'NONE','side_effect_basis':'The approved temporary evidence surface has no product deployment/release side effect.'},
      'trigger_conditions':['EVIDENCE_TOO_LARGE_FOR_CHAT','BRAIN_REQUIRES_RAW_PACKAGE'],
      'retention_policy':'EPHEMERAL_BY_DEFAULT','retention_reason':None,
      'cleanup':{'trigger':'TASK_TERMINAL','action':'DELETE_EXACT_TEMPORARY_REF','preauthorized':True,'background_service_forbidden':True},
      'fallback_mode':'MANUAL_FALLBACK','product_pr_promotion_forbidden':True,'product_main_or_development_branch_forbidden':True}


def capsule_with_plan(plan, route='REPAIR_STANDARD', scope='REPOSITORY_CHANGE'):
    cap=f.new_capsule(route,scope)
    cap['active_fibers']['authority']['payload']['evidence_transport']=copy.deepcopy(plan)
    cap=f.refresh(cap); cap=c.prepare_capsule_structural_fixture(cap)
    if cap['task_progress']['stage'] in {'INTENT_DISCUSSION','REPOSITORY_DISCOVERY'}: cap=f.advance(cap,'DECISION_CLOSURE')
    if route!='READ_ONLY_DISCOVERY' and cap['task_progress']['stage']!='USER_APPROVAL': cap=f.advance(cap,'USER_APPROVAL')
    return cap

def approved_with_plan(plan, route='REPAIR_STANDARD', scope='REPOSITORY_CHANGE'):
    cap=capsule_with_plan(plan,route,scope)
    projection,view,binding=c.draft_handoff(cap)
    if route=='READ_ONLY_DISCOVERY':
        cap['approval_record']={'status':'AUTHORIZED_READ_ONLY_DISCOVERY','owner':'WEB_BRAIN','scope':'READ_ONLY_DISCOVERY_ONLY','basis':'WEB_BRAIN_BOUNDED_READ_ONLY_DISCOVERY_AUTHORIZATION','decision_ref':'brain:read-only','binding':binding}
    else:
        cap['approval_record']={'status':'APPROVED_FINAL','owner':'WEB_BRAIN','scope':c.expected_approval_scope(cap),'basis':'CURRENT_EXPLICIT_USER_DECISION','decision_ref':'conversation:user-approved-execution','binding':binding}
    cap['derived_gates']=c.compute_gate_snapshot(cap); c.validate_capsule(cap)
    return cap,projection


def raw_merge_evidence(*, repository_id='example/repo', pr_number=42, head_sha='a'*40, merged=True):
    row={'url':f'https://api.github.com/repos/{repository_id}/pulls/{pr_number}','number':pr_number,
         'merged':merged,'merge_commit_sha':'d'*40,'head':{'sha':head_sha},
         'base':{'repo':{'full_name':repository_id}}}
    return (json.dumps(row,ensure_ascii=False,indent=2)+'\n').encode('utf-8')


def terminal_from_raw(raw):
    facts=c.parse_repository_merge_evidence(raw)
    return {'status':'MERGED','evidence_ref':facts['repository_evidence_ref'],
            'evidence_digest':facts['repository_evidence_sha256']}


def changed_raw(raw, mutate):
    row=json.loads(raw.decode('utf-8')); mutate(row)
    return (json.dumps(row,ensure_ascii=False,indent=2,sort_keys=False)+'\n').encode('utf-8')


class EphemeralGitHubEvidenceTransport(unittest.TestCase):
    def cleanup_inputs(self):
        approved,projection=approved_with_plan(github_plan())
        _,bundle=f.codex_return(projection)
        data=c.evidence_bundle_transport_bytes(bundle)
        receipt={'artifact_type':'EVIDENCE_TRANSPORT_RECEIPT','transport_mode':'GITHUB_EXACT_OBJECT','transport_role':'CURRENT_ROUND_EVIDENCE_BUNDLE_TRANSPORT_ONLY','project_id':projection['project_id'],'task_id':projection['task_id'],'round_id':projection['round_id'],'evidence_bundle_digest':bundle['evidence_bundle_digest'],'repository_id':'example/evidence-transport','exact_commit_sha':'c'*40,'exact_path':'evidence/TASK_PHASE1E/round-1/evidence.json','object_bytes':len(data),'object_sha256':hashlib.sha256(data).hexdigest(),'object_encoding':'CANONICAL_JSON_UTF8','temporary_ref':'refs/heads/joyflow-evidence/TASK_PHASE1E/round-1','retention_policy':'EPHEMERAL_BY_DEFAULT','cleanup_trigger':'TASK_TERMINAL','receipt_digest':None}
        receipt['receipt_digest']=c.digest(c.strip_digest(receipt,'receipt_digest'))
        return approved,projection,receipt,bundle

    def generic_merged_chain(self):
        td,repo,base,head=rf.create_repository()
        chain=rf.full_merge_authorization_chain(repo,base,head,evidence_transport_plan=github_plan())
        return td,chain,chain['codex_return']['evidence_transport_receipt']

    def test_current_review_transport_is_a_distinct_optional_projection_plan(self):
        plan=github_plan(); approved,projection=approved_with_plan(plan)
        self.assertEqual(projection['delivery']['evidence_transport']['transport_role'],'CURRENT_ROUND_EVIDENCE_BUNDLE_TRANSPORT_ONLY')
        self.assertNotIn('current_review_transport',projection['delivery'])
        c.validate_evidence_transport_plan(projection)

    def test_fast_path_inline_transport_remains_valid(self):
        cap,projection,_,_=f.approved_capsule('REPAIR_STANDARD','REPOSITORY_CHANGE')
        self.assertEqual(projection['delivery']['evidence_transport']['mode'],'INLINE')
        ret,bundle=f.codex_return(projection)
        c.validate_codex_execution_return_structure(ret,projection,bundle)

    def test_read_only_brain_authorization_cannot_authorize_github_write(self):
        cap=capsule_with_plan(github_plan(),'READ_ONLY_DISCOVERY','READ_ONLY')
        with self.assertRaises(Exception): c.draft_handoff(cap)

    def test_github_transport_requires_exact_preauthorized_cleanup(self):
        plan=github_plan(); plan['cleanup']['preauthorized']=False
        with self.assertRaises(Exception): approved_with_plan(plan)

    def test_github_transport_rejects_main_ref(self):
        plan=github_plan(); plan['github_surface']['temporary_ref']='refs/heads/main'
        with self.assertRaises(Exception): approved_with_plan(plan)

    def test_github_transport_requires_receipt_and_exact_bundle_binding(self):
        _,projection=approved_with_plan(github_plan())
        ret,bundle=f.codex_return(projection)
        with self.assertRaises(Exception): c.validate_codex_execution_return_structure(ret,projection,bundle)
        data=c.evidence_bundle_transport_bytes(bundle)
        with tempfile.TemporaryDirectory() as td:
            obj=pathlib.Path(td)/'evidence.zip'; obj.write_bytes(data)
            receipt={'artifact_type':'EVIDENCE_TRANSPORT_RECEIPT','transport_mode':'GITHUB_EXACT_OBJECT','transport_role':'CURRENT_ROUND_EVIDENCE_BUNDLE_TRANSPORT_ONLY','project_id':projection['project_id'],'task_id':projection['task_id'],'round_id':projection['round_id'],'evidence_bundle_digest':bundle['evidence_bundle_digest'],'repository_id':'example/evidence-transport','exact_commit_sha':'a'*40,'exact_path':'evidence/TASK_PHASE1E/round-1/evidence.zip','object_bytes':len(data),'object_sha256':hashlib.sha256(data).hexdigest(),'object_encoding':'CANONICAL_JSON_UTF8','temporary_ref':'refs/heads/joyflow-evidence/TASK_PHASE1E/round-1','retention_policy':'EPHEMERAL_BY_DEFAULT','cleanup_trigger':'TASK_TERMINAL','receipt_digest':None}
            receipt['receipt_digest']=c.digest(c.strip_digest(receipt,'receipt_digest'))
            ret['evidence_transport_receipt']=receipt; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
            c.validate_codex_execution_return_structure(ret,projection,bundle)
            c.verify_evidence_transport_receipt_against_object(receipt,obj,bundle)
            bad=copy.deepcopy(receipt); bad['evidence_bundle_digest']='0'*64; bad['receipt_digest']=c.digest(c.strip_digest(bad,'receipt_digest')); ret['evidence_transport_receipt']=bad; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
            with self.assertRaises(Exception): c.validate_codex_execution_return_structure(ret,projection,bundle)
            escaped=copy.deepcopy(receipt); escaped['temporary_ref']='refs/heads/joyflow-evidence/other'; escaped['receipt_digest']=c.digest(c.strip_digest(escaped,'receipt_digest')); ret['evidence_transport_receipt']=escaped; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
            with self.assertRaises(Exception): c.validate_codex_execution_return_structure(ret,projection,bundle)

    def test_transport_object_must_be_exact_evidence_bundle_bytes_and_is_not_semantic_pass(self):
        _,projection=approved_with_plan(github_plan())
        ret,bundle=f.codex_return(projection); data=c.evidence_bundle_transport_bytes(bundle)
        with tempfile.TemporaryDirectory() as td:
            obj=pathlib.Path(td)/'evidence.json'; obj.write_bytes(data)
            receipt={'artifact_type':'EVIDENCE_TRANSPORT_RECEIPT','transport_mode':'GITHUB_EXACT_OBJECT','transport_role':'CURRENT_ROUND_EVIDENCE_BUNDLE_TRANSPORT_ONLY','project_id':projection['project_id'],'task_id':projection['task_id'],'round_id':projection['round_id'],'evidence_bundle_digest':bundle['evidence_bundle_digest'],'repository_id':'example/evidence-transport','exact_commit_sha':'b'*40,'exact_path':'evidence/TASK_PHASE1E/round-1/evidence.json','object_bytes':len(data),'object_sha256':hashlib.sha256(data).hexdigest(),'object_encoding':'CANONICAL_JSON_UTF8','temporary_ref':'refs/heads/joyflow-evidence/TASK_PHASE1E/round-1','retention_policy':'EPHEMERAL_BY_DEFAULT','cleanup_trigger':'TASK_TERMINAL','receipt_digest':None}
            receipt['receipt_digest']=c.digest(c.strip_digest(receipt,'receipt_digest'))
            c.validate_evidence_transport_receipt_structure(receipt,projection,bundle)
            c.verify_evidence_transport_receipt_against_object(receipt,obj,bundle)
            obj.write_bytes(b'NOT_THE_EVIDENCE_BUNDLE')
            with self.assertRaises(Exception): c.verify_evidence_transport_receipt_against_object(receipt,obj,bundle)
            bad=copy.deepcopy(receipt); bad['object_bytes']=len(b'NOT_THE_EVIDENCE_BUNDLE'); bad['object_sha256']=hashlib.sha256(b'NOT_THE_EVIDENCE_BUNDLE').hexdigest(); bad['receipt_digest']=c.digest(c.strip_digest(bad,'receipt_digest'))
            with self.assertRaises(Exception): c.validate_evidence_transport_receipt_structure(bad,projection,bundle)
            self.assertNotIn('PASS',receipt)
            self.assertNotIn('brain_review',receipt)

    def test_ephemeral_cleanup_is_exact_preauthorized_terminal_continuation(self):
        approved,projection=approved_with_plan(github_plan())
        ret,bundle=f.codex_return(projection)
        data=c.evidence_bundle_transport_bytes(bundle)
        receipt={'artifact_type':'EVIDENCE_TRANSPORT_RECEIPT','transport_mode':'GITHUB_EXACT_OBJECT','transport_role':'CURRENT_ROUND_EVIDENCE_BUNDLE_TRANSPORT_ONLY','project_id':projection['project_id'],'task_id':projection['task_id'],'round_id':projection['round_id'],'evidence_bundle_digest':bundle['evidence_bundle_digest'],'repository_id':'example/evidence-transport','exact_commit_sha':'c'*40,'exact_path':'evidence/TASK_PHASE1E/round-1/evidence.json','object_bytes':len(data),'object_sha256':hashlib.sha256(data).hexdigest(),'object_encoding':'CANONICAL_JSON_UTF8','temporary_ref':'refs/heads/joyflow-evidence/TASK_PHASE1E/round-1','retention_policy':'EPHEMERAL_BY_DEFAULT','cleanup_trigger':'TASK_TERMINAL','receipt_digest':None}
        receipt['receipt_digest']=c.digest(c.strip_digest(receipt,'receipt_digest'))
        terminal={'status':'COMPLETED_NO_PR','evidence_ref':'brain:task-terminal','evidence_digest':hashlib.sha256(b'completed-no-pr').hexdigest()}
        continuation=c.build_evidence_transport_cleanup_continuation(
            projection,approved['approval_record'],receipt,bundle,terminal_evidence=terminal)
        self.assertEqual(continuation['cleanup_action'],'DELETE_EXACT_TEMPORARY_REF')
        self.assertEqual(continuation['task_terminal_status'],'COMPLETED_NO_PR')
        self.assertFalse(continuation['background_service_used'])
        self.assertTrue(continuation['user_mediated_handoff_required'])
        c.validate_evidence_transport_cleanup_target(continuation,receipt['exact_commit_sha'])
        with self.assertRaises(Exception): c.validate_evidence_transport_cleanup_target(continuation,'d'*40)
        wrong=copy.deepcopy(terminal); wrong['status']='NOT_TERMINAL'
        with self.assertRaises(Exception): c.build_evidence_transport_cleanup_continuation(
            projection,approved['approval_record'],receipt,bundle,terminal_evidence=wrong)

    def test_t12_pointer_self_digest_cannot_produce_terminal_merged(self):
        td,repo,base,head=rf.create_repository()
        try:
            chain=rf.full_merge_authorization_chain(repo,base,head)
            with self.assertRaises(c.JoyflowError):
                c._task_terminal_evidence_from_merge_pointer(chain['completion_pointer'])
        finally:
            td.cleanup()

    def test_t13_valid_terminal_evidence_is_raw_repository_evidence(self):
        td,repo,base,head=rf.create_repository()
        try:
            chain=rf.full_merge_authorization_chain(repo,base,head)
            terminal=c._task_terminal_evidence_from_merge_pointer(chain['completion_pointer'],chain['repository_merge_evidence'])
            self.assertEqual(terminal['status'],'MERGED')
            self.assertEqual(terminal['evidence_ref'],chain['completion_pointer']['repository_evidence_ref'])
            self.assertEqual(terminal['evidence_digest'],hashlib.sha256(chain['repository_merge_evidence']).hexdigest())
            self.assertNotEqual(terminal['evidence_digest'],chain['completion_pointer']['pointer_digest'])
        finally:
            td.cleanup()

    def test_t14_cleanup_requires_exact_raw_repository_merge_evidence(self):
        td,repo,base,head=rf.create_repository()
        try:
            chain=rf.full_merge_authorization_chain(repo,base,head,evidence_transport_plan=github_plan())
            receipt=chain['codex_return']['evidence_transport_receipt']
            args=(chain['projection'],chain['approved']['approval_record'],receipt,chain['evidence_bundle'],
                  chain['completion_pointer'],chain['merge_candidate_freeze'],chain['user_acceptance'],chain['user_merge_authorization'])
            with self.assertRaises(c.JoyflowError): c.build_evidence_transport_cleanup_continuation(*args)
            continuation=c.build_evidence_transport_cleanup_continuation(*args,repository_merge_evidence=chain['repository_merge_evidence'])
            self.assertEqual(continuation['task_terminal_status'],'MERGED')
            self.assertEqual(continuation['terminal_evidence_ref'],chain['completion_pointer']['repository_evidence_ref'])
            self.assertEqual(continuation['terminal_evidence_digest'],hashlib.sha256(chain['repository_merge_evidence']).hexdigest())
        finally:
            td.cleanup()

    def test_e1_generic_merged_without_raw_repository_merge_evidence_blocks(self):
        td,chain,receipt=self.generic_merged_chain()
        try:
            with self.assertRaises(c.JoyflowError):
                c.build_evidence_transport_cleanup_continuation(
                    chain['projection'],chain['approved']['approval_record'],receipt,chain['evidence_bundle'],
                    merge_candidate_freeze=chain['merge_candidate_freeze'],
                    terminal_evidence=terminal_from_raw(chain['repository_merge_evidence']))
        finally:
            td.cleanup()

    def test_e2_generic_merged_with_exact_raw_repository_merge_evidence_passes_without_completion_ancestry(self):
        td,chain,receipt=self.generic_merged_chain()
        try:
            raw=chain['repository_merge_evidence']
            continuation=c.build_evidence_transport_cleanup_continuation(
                chain['projection'],chain['approved']['approval_record'],receipt,chain['evidence_bundle'],
                merge_candidate_freeze=chain['merge_candidate_freeze'],terminal_evidence=terminal_from_raw(raw),
                repository_merge_evidence=raw)
            self.assertEqual(continuation['task_terminal_status'],'MERGED')
            self.assertEqual(continuation['terminal_evidence_digest'],hashlib.sha256(raw).hexdigest())
        finally:
            td.cleanup()

    def test_e3_generic_merged_with_wrong_raw_sha_blocks(self):
        td,chain,receipt=self.generic_merged_chain()
        try:
            raw=chain['repository_merge_evidence']; terminal=terminal_from_raw(raw)
            with self.assertRaises(c.JoyflowError):
                c.build_evidence_transport_cleanup_continuation(
                    chain['projection'],chain['approved']['approval_record'],receipt,chain['evidence_bundle'],
                    merge_candidate_freeze=chain['merge_candidate_freeze'],terminal_evidence=terminal,
                    repository_merge_evidence=raw+b'\n')
        finally:
            td.cleanup()

    def test_e4_generic_merged_with_wrong_evidence_ref_blocks(self):
        td,chain,receipt=self.generic_merged_chain()
        try:
            raw=chain['repository_merge_evidence']; terminal=terminal_from_raw(raw)
            terminal['evidence_ref']='https://api.github.com/repos/example/repo/pulls/99'
            with self.assertRaises(c.JoyflowError):
                c.build_evidence_transport_cleanup_continuation(
                    chain['projection'],chain['approved']['approval_record'],receipt,chain['evidence_bundle'],
                    merge_candidate_freeze=chain['merge_candidate_freeze'],terminal_evidence=terminal,
                    repository_merge_evidence=raw)
        finally:
            td.cleanup()

    def test_e5_generic_merged_for_wrong_projection_repository_blocks(self):
        td,chain,receipt=self.generic_merged_chain()
        try:
            raw=changed_raw(chain['repository_merge_evidence'],lambda row: row['base']['repo'].__setitem__('full_name','foreign/repo'))
            with self.assertRaises(c.JoyflowError):
                c.build_evidence_transport_cleanup_continuation(
                    chain['projection'],chain['approved']['approval_record'],receipt,chain['evidence_bundle'],
                    merge_candidate_freeze=chain['merge_candidate_freeze'],terminal_evidence=terminal_from_raw(raw),
                    repository_merge_evidence=raw)
        finally:
            td.cleanup()

    def test_g1_generic_merged_without_merge_candidate_freeze_blocks(self):
        td,chain,receipt=self.generic_merged_chain()
        try:
            raw=chain['repository_merge_evidence']
            with self.assertRaises(c.JoyflowError):
                c.build_evidence_transport_cleanup_continuation(
                    chain['projection'],chain['approved']['approval_record'],receipt,chain['evidence_bundle'],
                    terminal_evidence=terminal_from_raw(raw),repository_merge_evidence=raw)
        finally:
            td.cleanup()

    def test_g2_exact_freeze_and_raw_merge_pass_without_completion_or_user_merge_authorization(self):
        td,chain,receipt=self.generic_merged_chain()
        try:
            raw=chain['repository_merge_evidence']
            continuation=c.build_evidence_transport_cleanup_continuation(
                chain['projection'],chain['approved']['approval_record'],receipt,chain['evidence_bundle'],
                merge_candidate_freeze=chain['merge_candidate_freeze'],terminal_evidence=terminal_from_raw(raw),
                repository_merge_evidence=raw)
            self.assertEqual(continuation['task_terminal_status'],'MERGED')
        finally:
            td.cleanup()

    def test_g3_same_repository_foreign_pr_and_head_blocks(self):
        td,chain,receipt=self.generic_merged_chain()
        try:
            raw=changed_raw(chain['repository_merge_evidence'],lambda row: (row.__setitem__('number',99),row['head'].__setitem__('sha','b'*40)))
            with self.assertRaises(c.JoyflowError):
                c.build_evidence_transport_cleanup_continuation(
                    chain['projection'],chain['approved']['approval_record'],receipt,chain['evidence_bundle'],
                    merge_candidate_freeze=chain['merge_candidate_freeze'],terminal_evidence=terminal_from_raw(raw),
                    repository_merge_evidence=raw)
        finally:
            td.cleanup()

    def test_g4_correct_pr_wrong_head_blocks(self):
        td,chain,receipt=self.generic_merged_chain()
        try:
            raw=changed_raw(chain['repository_merge_evidence'],lambda row: row['head'].__setitem__('sha','b'*40))
            with self.assertRaises(c.JoyflowError):
                c.build_evidence_transport_cleanup_continuation(
                    chain['projection'],chain['approved']['approval_record'],receipt,chain['evidence_bundle'],
                    merge_candidate_freeze=chain['merge_candidate_freeze'],terminal_evidence=terminal_from_raw(raw),
                    repository_merge_evidence=raw)
        finally:
            td.cleanup()

    def test_g5_freeze_from_another_project_task_or_round_blocks(self):
        td,chain,receipt=self.generic_merged_chain()
        try:
            raw=chain['repository_merge_evidence']
            cases={'project_id':'OTHER_PROJECT','task_id':'OTHER_TASK','round_id':chain['projection']['round_id']+1}
            for field,value in cases.items():
                with self.subTest(field=field):
                    freeze=copy.deepcopy(chain['merge_candidate_freeze']); freeze[field]=value
                    freeze['freeze_digest']=c.digest(c.strip_digest(freeze,'freeze_digest'))
                    with self.assertRaises(c.JoyflowError):
                        c.build_evidence_transport_cleanup_continuation(
                            chain['projection'],chain['approved']['approval_record'],receipt,chain['evidence_bundle'],
                            merge_candidate_freeze=freeze,terminal_evidence=terminal_from_raw(raw),
                            repository_merge_evidence=raw)
        finally:
            td.cleanup()

    def test_g6_freeze_projection_mismatch_blocks(self):
        td,chain,receipt=self.generic_merged_chain()
        try:
            raw=chain['repository_merge_evidence']; freeze=copy.deepcopy(chain['merge_candidate_freeze'])
            freeze['projection_digest']='0'*64; freeze['freeze_digest']=c.digest(c.strip_digest(freeze,'freeze_digest'))
            with self.assertRaises(c.JoyflowError):
                c.build_evidence_transport_cleanup_continuation(
                    chain['projection'],chain['approved']['approval_record'],receipt,chain['evidence_bundle'],
                    merge_candidate_freeze=freeze,terminal_evidence=terminal_from_raw(raw),repository_merge_evidence=raw)
        finally:
            td.cleanup()

    def test_g7_freeze_evidence_bundle_mismatch_blocks(self):
        td,chain,receipt=self.generic_merged_chain()
        try:
            raw=chain['repository_merge_evidence']; freeze=copy.deepcopy(chain['merge_candidate_freeze'])
            freeze['evidence_bundle_digest']='0'*64; freeze['freeze_digest']=c.digest(c.strip_digest(freeze,'freeze_digest'))
            with self.assertRaises(c.JoyflowError):
                c.build_evidence_transport_cleanup_continuation(
                    chain['projection'],chain['approved']['approval_record'],receipt,chain['evidence_bundle'],
                    merge_candidate_freeze=freeze,terminal_evidence=terminal_from_raw(raw),repository_merge_evidence=raw)
        finally:
            td.cleanup()

    def test_e8_non_merged_generic_terminal_does_not_require_repository_merge_evidence(self):
        approved,projection,receipt,bundle=self.cleanup_inputs()
        terminal={'status':'CANCELLED','evidence_ref':'brain:cancelled',
                  'evidence_digest':hashlib.sha256(b'cancelled').hexdigest()}
        continuation=c.build_evidence_transport_cleanup_continuation(
            projection,approved['approval_record'],receipt,bundle,terminal_evidence=terminal)
        self.assertEqual(continuation['task_terminal_status'],'CANCELLED')

    def test_pointer_driven_completion_still_requires_final_merge_authorization(self):
        td,repo,base,head=rf.create_repository()
        try:
            chain=rf.full_merge_authorization_chain(repo,base,head,evidence_transport_plan=github_plan())
            receipt=chain['codex_return']['evidence_transport_receipt']
            with self.assertRaises(c.JoyflowError):
                c.build_evidence_transport_cleanup_continuation(
                    chain['projection'],chain['approved']['approval_record'],receipt,chain['evidence_bundle'],
                    chain['completion_pointer'],chain['merge_candidate_freeze'],chain['user_acceptance'],None,
                    repository_merge_evidence=chain['repository_merge_evidence'])
        finally:
            td.cleanup()

if __name__=='__main__': unittest.main()
