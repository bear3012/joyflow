from __future__ import annotations
import copy, hashlib, importlib.util, json, os, pathlib, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('compiler',ROOT/'runtime/joyflow_dual_layer.py'); c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
spec2=importlib.util.spec_from_file_location('fixture',ROOT/'tests/build_fixture.py'); f=importlib.util.module_from_spec(spec2); spec2.loader.exec_module(f)

class CodexTechnicalAuthority(unittest.TestCase):
 def base(self,route='DEVELOPMENT_STANDARD',scope='REPOSITORY_CHANGE'):
  _,p,_,_=f.approved_capsule(route,scope); r,b=f.codex_return(p); return p,r,b
 def block(self,fn):
  with self.assertRaises(c.JoyflowError): fn()
 def refresh(self,r,b):
  caps={x['capture_id']:x for x in b['raw_captures']}
  for cap in caps.values(): cap['stdout_sha256']=hashlib.sha256(cap['stdout'].encode('utf-8')).hexdigest(); cap['stderr_sha256']=hashlib.sha256(cap['stderr'].encode('utf-8')).hexdigest(); cap['capture_sha256']=c.digest(c._execution_capture_payload(cap))
  for ev in b['evidence_rows']:
   if ev['raw_output_ref'] in caps:
    ev['claim']=c._direct_capture_claim(caps[ev['raw_output_ref']]); ev['raw_output_sha256']=caps[ev['raw_output_ref']]['capture_sha256']
   ev['claim_digest']=c.digest(ev['claim'])
  for drv in b.get('derivation_rows',[]): drv['claim_digest']=c.digest(drv['claim'])
  b['evidence_bundle_digest']=c.digest(c.strip_digest(b,'evidence_bundle_digest')); r['evidence_bundle_digest']=b['evidence_bundle_digest']; r['return_digest']=c.digest(c.strip_digest(r,'return_digest'))

 def test_complete_preflight_passes(self):
  p,r,b=self.base(); c.validate_codex_execution_return_structure(r,p,b)

 def test_brain_candidates_are_non_exhaustive(self):
  p,_,_=self.base(); self.assertFalse(p['technical_route_space']['candidate_set_exhaustive']); self.assertTrue(p['technical_route_space']['codex_alternative_route_allowed']); self.assertGreaterEqual(len(p['technical_route_space']['candidate_routes']),1)

 def test_codex_cannot_replace_required_obligation_with_unrelated_check(self):
  p,r,b=self.base(); r['technical_preflight']['obligation_results'][0]['obligation_id']='UNRELATED'; self.refresh(r,b); self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_every_candidate_must_be_evaluated(self):
  p,r,b=self.base(); r['technical_preflight']['candidate_evaluations'].pop(); self.refresh(r,b); self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_route_conflict_requires_failed_route_dimension(self):
  p,_,_=self.base(); r,b=f.make_blocked_return(p,status='BRAIN_ROUTE_CONFLICT'); c.validate_codex_execution_return_structure(r,p,b)
  for result in r['technical_preflight']['obligation_results']: result['result']='PASS'
  self.refresh(r,b); self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_scope_gap_requires_failed_path_dimension_and_unapproved_path(self):
  p,_,_=self.base(); r,b=f.make_blocked_return(p,status='APPROVAL_SCOPE_INSUFFICIENT',additional_paths=['generator/**']); c.validate_codex_execution_return_structure(r,p,b)
  r,b=f.make_blocked_return(p,status='APPROVAL_SCOPE_INSUFFICIENT',additional_paths=['runtime/**']); self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_object_mismatch_requires_failed_object_identity(self):
  p,_,_=self.base(); r,b=f.make_blocked_return(p,status='REPOSITORY_STATE_MISMATCH',observed_repository_ref='def456'); c.validate_codex_execution_return_structure(r,p,b)
  result=next(x for x in r['technical_preflight']['obligation_results'] if x['dimension']=='OBJECT_IDENTITY'); result['result']='PASS'; self.refresh(r,b); self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_tool_capture_is_required(self):
  p,r,b=self.base(); ev=b['evidence_rows'][0]; ev['raw_output_ref']='missing-capture'; self.refresh(r,b); self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_codex_self_authored_direct_evidence_is_rejected(self):
  p,r,b=self.base(); b['evidence_rows'][0]['produced_by']='CODEX'; self.refresh(r,b); self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_raw_capture_digest_is_checked(self):
  p,r,b=self.base(); b['raw_captures'][0]['stdout']='tampered without digest update'; b['evidence_bundle_digest']=c.digest(c.strip_digest(b,'evidence_bundle_digest')); r['evidence_bundle_digest']=b['evidence_bundle_digest']; r['return_digest']=c.digest(c.strip_digest(r,'return_digest')); self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_capture_subject_must_match_evidence_subject(self):
  p,r,b=self.base(); b['raw_captures'][0]['subject_id']='other'; self.refresh(r,b); self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_equivalent_codex_alternative_within_boundary_can_execute(self):
  p,r,b=self.base(); alt={'route_id':'CODEX_ALT_MINIMAL','summary':'Use a smaller equivalent helper function.','why_better_than_candidates':'It preserves behavior with less code churn.','product_semantics_unchanged':True,'approved_paths_sufficient':True,'important_tradeoff_changed':False,'protocol_or_compatibility_changed':False,'migration_required':False,'evidence_refs':['DERIVE_ALT_ROUTE']}
  b['derivation_rows'].append(f.exec_derivation('DERIVE_ALT_ROUTE','CODEX_ALTERNATIVE_DERIVATION',c._alternative_route_claim(alt),'TECHNICAL_ROUTE_ALTERNATIVE',alt['route_id'],['EXEC_PREFLIGHT_SOURCE','EXEC_PREFLIGHT_TEST']))
  sel={'source':'CODEX_ALTERNATIVE','route_id':alt['route_id'],'implementation_summary':alt['summary'],'evidence_refs':['DERIVE_ALT_SELECTED']}
  b['derivation_rows'].append(f.exec_derivation('DERIVE_ALT_SELECTED','SELECTED_ROUTE_DERIVATION',c._selected_route_claim(sel),'TECHNICAL_ROUTE_SELECTION',sel['route_id'],['EXEC_PREFLIGHT_SOURCE','EXEC_PREFLIGHT_TEST']))
  r['technical_preflight'].update({'status':'EQUIVALENT_IMPLEMENTATION_ADJUSTMENT','selected_route':sel,'alternative_route':alt,'implementation_decisions':['Use the smaller equivalent helper.']}); self.refresh(r,b); c.validate_codex_execution_return_structure(r,p,b)

 def test_codex_alternative_evidence_must_bind_complete_claim(self):
  p,r,b=self.base(); alt={'route_id':'CODEX_ALT_MINIMAL','summary':'Use a smaller equivalent helper function.','why_better_than_candidates':'It preserves behavior with less code churn.','product_semantics_unchanged':True,'approved_paths_sufficient':True,'important_tradeoff_changed':False,'protocol_or_compatibility_changed':False,'migration_required':False,'evidence_refs':['DERIVE_ALT_ROUTE']}
  b['derivation_rows'].append(f.exec_derivation('DERIVE_ALT_ROUTE','CODEX_ALTERNATIVE_DERIVATION','incomplete alternative claim','TECHNICAL_ROUTE_ALTERNATIVE',alt['route_id'],['EXEC_PREFLIGHT_SOURCE']))
  sel={'source':'CODEX_ALTERNATIVE','route_id':alt['route_id'],'implementation_summary':alt['summary'],'evidence_refs':['DERIVE_ALT_SELECTED']}
  b['derivation_rows'].append(f.exec_derivation('DERIVE_ALT_SELECTED','SELECTED_ROUTE_DERIVATION',c._selected_route_claim(sel),'TECHNICAL_ROUTE_SELECTION',sel['route_id'],['EXEC_PREFLIGHT_SOURCE']))
  r['technical_preflight'].update({'status':'EQUIVALENT_IMPLEMENTATION_ADJUSTMENT','selected_route':sel,'alternative_route':alt,'implementation_decisions':['Use the smaller equivalent helper.']}); self.refresh(r,b); self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_codex_cannot_select_user_owned_candidate_tradeoff(self):
  p,r,b=self.base(); p['technical_route_space']['candidate_routes'][0]['important_tradeoff_owner']='USER'
  self.refresh(r,b); self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_material_codex_alternative_must_stop(self):
  p,r,b=self.base(); r['technical_preflight']['material_change_assessment']['approved_paths_expanded']=True; self.refresh(r,b); self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_machine_result_must_match_raw_capture_command(self):
  p,r,b=self.base(); row=r['machine_results'][0]; cap=next(x for x in b['raw_captures'] if x['capture_id']==next(e for e in b['evidence_rows'] if e['evidence_id']==row['evidence_ref'])['raw_output_ref']); cap['command']='different command'; self.refresh(r,b); self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_existing_artifact_input_identity_is_exact(self):
  p,r,b=self.base('ARTIFACT_REPAIR','ARTIFACT_CHANGE'); self.assertEqual(p['execution_object']['logical_role'],'EXISTING_ARTIFACT'); self.assertEqual(p['execution_object']['physical_object']['kind'],'ARTIFACT'); self.assertRegex(p['execution_object']['physical_object']['digest'],r'^[0-9a-f]{64}$'); c.validate_codex_execution_return_structure(r,p,b)

 def test_wrong_artifact_observation_blocks(self):
  p,r,b=self.base('ARTIFACT_REPAIR','ARTIFACT_CHANGE'); ev=next(x for x in b['evidence_rows'] if x['evidence_id']==r['technical_preflight']['object_observation_evidence_ref']); cap=next(x for x in b['raw_captures'] if x['capture_id']==ev['raw_output_ref']); cap['observed_object']['digest']='f'*64; cap['observation']['artifact_sha256']='f'*64; self.refresh(r,b); self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_initial_review_seal_requires_exact_trio(self):
  approved,p,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); executing=f.advance(approved,'CODEX_EXECUTION'); r,b=f.codex_return(p)
  review=f.brain_review_capsule(executing,p,r,b)
  draft=copy.deepcopy(review); draft['capsule_digest']=None; draft['derived_gates']={}
  # Reconstruct an initial review candidate but omit exact source arguments.
  self.block(lambda:c.prepare_capsule(draft,executing))

 def test_review_with_exact_trio_passes(self):
  approved,p,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); executing=f.advance(approved,'CODEX_EXECUTION'); r,b=f.codex_return(p); review=f.brain_review_capsule(executing,p,r,b); c.validate_execution_review(review)

 def test_blocked_cannot_brain_pass(self):
  approved,p,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); executing=f.advance(approved,'CODEX_EXECUTION'); r,b=f.make_blocked_return(p,status='BRAIN_ROUTE_CONFLICT'); review=f.brain_review_capsule(executing,p,r,b,brain_verdict='BLOCK'); review['active_fibers']['execution_review']['payload']['brain_review_verdict']='PASS'; review=f.refresh(review); self.block(lambda:c.validate_execution_review(review))

 def test_execution_evidence_runner_preserves_raw_output(self):
  with tempfile.TemporaryDirectory() as td:
   repo=pathlib.Path(td)/'repo'; repo.mkdir(); out=pathlib.Path(td)/'capture.json'
   subprocess.run(['git','init',str(repo)],check=True,capture_output=True)
   subprocess.run(['git','-C',str(repo),'config','user.email','joyflow@example.invalid'],check=True)
   subprocess.run(['git','-C',str(repo),'config','user.name','Joyflow Test'],check=True)
   (repo/'a.txt').write_text('a\n')
   subprocess.run(['git','-C',str(repo),'add','a.txt'],check=True); subprocess.run(['git','-C',str(repo),'commit','-m','init'],check=True,capture_output=True)
   subprocess.run(['git','-C',str(repo),'remote','add','origin','https://github.com/example/repo.git'],check=True)
   head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
   cmd=[sys.executable,str(ROOT/'tools/capture_execution_evidence.py'),'test-command','--capture-id','CAP_TOOL_TEST','--subject-type','VALIDATION_CHECK','--subject-id','TEST:CHECK','--repository',str(repo),'--repository-ref',head,'--output',str(out),'--',sys.executable,'-c','print("captured")']
   proc=subprocess.run(cmd,capture_output=True,text=True); self.assertEqual(proc.returncode,0,proc.stderr)
   row=json.loads(out.read_text(encoding='utf-8')); expected=('captured'+os.linesep).encode('utf-8'); self.assertEqual(row['stdout'],expected.decode('utf-8')); self.assertEqual(row['stdout_sha256'],hashlib.sha256(expected).hexdigest()); self.assertEqual(row['stderr_sha256'],hashlib.sha256(b'').hexdigest()); self.assertEqual(row['capture_sha256'],c.digest(c._execution_capture_payload(row))); self.assertEqual(row['observed_object']['object_id'],'example/repo')

 def test_brain_preflight_question_must_be_canonical_and_task_bound(self):
  cap=f.at_user_approval('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
  space=cap['active_fibers']['decision_boundary']['payload']['technical_route_space']
  row=next(x for x in space['obligations'] if x['dimension']=='ROUTE_ASSUMPTION_VALIDITY')
  row['question']='Is one equal to one?'
  self.block(lambda:c.validate_technical_route_space(cap))

 def test_brain_preflight_subject_binding_must_match_current_task(self):
  cap=f.at_user_approval('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
  row=cap['active_fibers']['decision_boundary']['payload']['technical_route_space']['obligations'][0]
  row['subject_binding']['subject_digest']='f'*64
  self.block(lambda:c.validate_technical_route_space(cap))

 def test_passing_candidate_cannot_require_unapproved_path(self):
  p,r,b=self.base(); p['technical_route_space']['candidate_routes'][0]['expected_paths']=['unapproved/**']
  self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_candidate_evaluation_requires_structural_current_object_fact(self):
  p,r,b=self.base(); drv=next(x for x in b['derivation_rows'] if x['kind']=='ROUTE_CANDIDATE_DERIVATION')
  drv['source_evidence_refs']=['EXEC_PREFLIGHT_TEST']; self.refresh(r,b)
  self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_semantic_preflight_cannot_use_arbitrary_test_as_direct_fact(self):
  p,r,b=self.base(); result=next(x for x in r['technical_preflight']['obligation_results'] if x['dimension']=='PRODUCT_SEMANTIC_PRESERVATION')
  drv=next(x for x in b['derivation_rows'] if x['derivation_id']==result['evidence_refs'][0]); drv['source_evidence_refs']=['EXEC_PREFLIGHT_TEST']; self.refresh(r,b)
  self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_preflight_test_command_must_be_in_approved_plan(self):
  p,r,b=self.base(); cap=next(x for x in b['raw_captures'] if x['capture_id']=='CAP_PREFLIGHT_TEST')
  cap['command']='python -c print(42)'; cap['observation']['argv']=['python','-c','print(42)']; self.refresh(r,b)
  self.block(lambda:c.validate_codex_execution_return_structure(r,p,b))

 def test_typed_runner_rejects_caller_supplied_object_identity(self):
  proc=subprocess.run([sys.executable,str(ROOT/'tools/capture_execution_evidence.py'),'repository-head','--capture-id','CAP_BAD','--subject-type','X','--subject-id','Y','--object-id','forged/repo','--ref-or-sha256','abc'],capture_output=True,text=True)
  self.assertNotEqual(proc.returncode,0)

 def test_review_source_snapshot_blocks_later_machine_evidence_substitution(self):
  approved,p,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); executing=f.advance(approved,'CODEX_EXECUTION'); r,b=f.codex_return(p); review=f.brain_review_capsule(executing,p,r,b)
  draft=copy.deepcopy(review); payload=draft['active_fibers']['execution_review']['payload']; payload['validation_results'][0]['machine_results'][0]['evidence_ref']='FAKE_REPLACEMENT'; payload['source_snapshot_digest']=c.source_derived_review_snapshot_digest(payload)
  self.block(lambda:c.validate_review_seal_input(draft,review,None,None,None))

 def test_review_exact_trio_rejects_later_machine_evidence_substitution(self):
  approved,p,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); executing=f.advance(approved,'CODEX_EXECUTION'); r,b=f.codex_return(p); review=f.brain_review_capsule(executing,p,r,b)
  draft=copy.deepcopy(review); payload=draft['active_fibers']['execution_review']['payload']; payload['validation_results'][0]['machine_results'][0]['evidence_ref']='FAKE_REPLACEMENT'; payload['source_snapshot_digest']=c.source_derived_review_snapshot_digest(payload)
  self.block(lambda:c.validate_review_input_binding(draft,p,r,b))

 def test_approval_view_hides_internal_route_space_and_exposes_authorization_boundary(self):
  p,_,_=self.base(); view=c.render_approval_view(p)
  self.assertNotIn('Brain technical route space',view); self.assertNotIn('candidate_set_exhaustive',view)
  self.assertIn('Authorization envelope',view); self.assertIn('## Minimum validation',view); self.assertIn('## Stop / re-closure conditions',view)
  compact=c.compact_execution_view(p); self.assertIn('technical_route_space',compact); self.assertIn('candidate_set_exhaustive',compact['technical_route_space'])

if __name__=='__main__': unittest.main()
