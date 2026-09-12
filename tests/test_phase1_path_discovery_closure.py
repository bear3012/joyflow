from __future__ import annotations
import copy, importlib.util, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('c',ROOT/'runtime/joyflow_dual_layer.py'); c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
spec2=importlib.util.spec_from_file_location('f',ROOT/'tests/build_fixture.py'); f=importlib.util.module_from_spec(spec2); spec2.loader.exec_module(f)
class PathClosure(unittest.TestCase):
 def test_non_repository_evidence_cannot_confirm_github_path(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); pd=state['active_fibers']['repository_evidence']['payload']['path_discovery']; pd['confirmed_paths'][0]['evidence_ref']='E_USER_MODEL'
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))
 def test_other_repository_github_evidence_blocks(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); ev=state['active_fibers']['repository_evidence']['payload']['path_discovery']['github_path_evidence'][0]; ev['repository_id']='other/repo'; ev['evidence_digest']=c.digest(c.strip_digest(ev,'evidence_digest'))
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))
 def test_final_path_without_source_blocks(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); item=state['active_fibers']['repository_evidence']['payload']['path_discovery']['final_path_decision']['allowed_path_items'][0]; item['source_github_path_evidence_ids']=[]; d=state['active_fibers']['repository_evidence']['payload']['path_discovery']['final_path_decision']; d['decision_digest']=c.digest(c.strip_digest(d,'decision_digest'))
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))
 def test_completed_local_discovery_requires_exact_binding(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); pd=state['active_fibers']['repository_evidence']['payload']['path_discovery']; pd.update({'github_discovery_status':'COMPLETED_INSUFFICIENT','local_discovery_required':True,'local_discovery_reason':'RUNTIME_ONLY_FACT','local_discovery_status':'COMPLETED','path_discovery_source':'COMBINED'})
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))
 def test_combined_global_wildcards_rejected(self):
  for path in ('*/**','**/**','src/*/**','src/**/file.py'):
   self.assertFalse(c._valid_repo_path(path),path)
 def test_literal_prefix_recursive_path_allowed(self): self.assertTrue(c._valid_repo_path('src/runtime/**'))
 def test_read_only_fingerprint_change_blocks(self):
  _,projection,_,_=f.approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY'); ret=f.path_discovery_return(projection); ret['repository_state_after']['worktree_diff_sha256']='1'*64; ret['repository_state_after']['state_fingerprint_sha256']=c.digest(c._state_fingerprint_payload(ret['repository_state_after'])); ret['repository_state_after']['capture_record_digest']=c.digest(c._capture_record_payload(ret['repository_state_after'])); ev=next(x for x in ret['evidence_rows'] if x['evidence_id']==ret['repository_state_after']['evidence_ref']); ev['claim']=c._git_state_claim(ret['repository_state_after']); ev['claim_digest']=c.digest(ev['claim']); ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
  with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return_structure(ret,projection)

 def test_typed_github_evidence_must_match_registry_subject(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); row=state['evidence_registry'][[r['evidence_id'] for r in state['evidence_registry']].index('E_GITHUB_PATHS')]; row['subject_id']='example/repo@old'; row['claim_digest']=c.digest(row['claim'])
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))
 def test_github_final_path_cannot_use_user_decision_evidence(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); d=state['active_fibers']['repository_evidence']['payload']['path_discovery']['final_path_decision']; d['allowed_path_items'][0]['source_github_path_evidence_ids']=['E_USER_MODEL']; d['decision_digest']=c.digest(c.strip_digest(d,'decision_digest'))
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))
 def test_completed_local_discovery_must_supply_exact_return_when_sealed(self):
  _,projection,_,_=f.approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY'); ret=f.path_discovery_return(projection)
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE');
  for semantic in c.semantic_items(state):
   for effect in semantic.get('effects',[]):
    if effect.get('effect_type')=='ALLOW_PATH': effect['value']='runtime/joyflow_dual_layer.py'
  pd=state['active_fibers']['repository_evidence']['payload']['path_discovery']; pd.update({'github_discovery_status':'COMPLETED_INSUFFICIENT','local_discovery_required':True,'local_discovery_reason':'RUNTIME_ONLY_FACT','local_discovery_status':'COMPLETED','path_discovery_source':'COMBINED','local_discovery_binding':{'source_projection_digest':projection['projection_digest'],'path_discovery_return_digest':ret['return_digest'],'project_id':state['task_anchor']['project_id'],'task_id':state['task_anchor']['task_id'],'round_id':1}}); item=pd['final_path_decision']['allowed_path_items'][0]; item.update({'path':'runtime/joyflow_dual_layer.py','basis_type':'COMBINED','source_github_path_evidence_ids':['E_GITHUB_PATHS'],'derived_from_paths':['runtime/**'],'supporting_evidence_refs':[],'source_path_discovery_return_digest':ret['return_digest'],'source_return_path_ids':['LOCAL_PATH_RUNTIME'],'source_return_dependency_ids':[],'source_return_validation_ids':[],'source_return_finding_ids':[],'derivation_summary':'Brain combines the exact current local Return path with the current typed GitHub path observation.'}); pd['final_path_decision']['decision_digest']=c.digest(c.strip_digest(pd['final_path_decision'],'decision_digest'))
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))
  sealed=c.prepare_capsule_structural_fixture(f.refresh(state),path_discovery_projection=projection,path_discovery_return=ret); self.assertEqual(sealed['active_fibers']['repository_evidence']['payload']['path_discovery']['local_discovery_binding']['path_discovery_return_digest'],ret['return_digest'])


 def test_github_confirmed_unrelated_path_blocks(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
  for semantic in c.semantic_items(state):
   for effect in semantic.get('effects',[]):
    if effect.get('effect_type')=='ALLOW_PATH': effect['value']='unrelated/**'
  d=state['active_fibers']['repository_evidence']['payload']['path_discovery']['final_path_decision']; d['allowed_path_items'][0]['path']='unrelated/**'; d['decision_digest']=c.digest(c.strip_digest(d,'decision_digest'))
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))

 def test_generic_repository_evidence_cannot_source_github_confirmed_path(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); d=state['active_fibers']['repository_evidence']['payload']['path_discovery']['final_path_decision']; item=d['allowed_path_items'][0]
  item['source_github_path_evidence_ids']=['E_TEST_PLAN']; d['decision_digest']=c.digest(c.strip_digest(d,'decision_digest'))
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))

 def test_mixed_non_path_evidence_cannot_source_github_confirmed_path(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); d=state['active_fibers']['repository_evidence']['payload']['path_discovery']['final_path_decision']; item=d['allowed_path_items'][0]
  item['source_github_path_evidence_ids']=['E_USER_MODEL','E_TEST_PLAN']; d['decision_digest']=c.digest(c.strip_digest(d,'decision_digest'))
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))

 def test_github_confirmed_may_narrow_within_observed_directory(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
  for semantic in c.semantic_items(state):
   for effect in semantic.get('effects',[]):
    if effect.get('effect_type')=='ALLOW_PATH': effect['value']='runtime/submodule/**'
  d=state['active_fibers']['repository_evidence']['payload']['path_discovery']['final_path_decision']; d['allowed_path_items'][0]['path']='runtime/submodule/**'; d['decision_digest']=c.digest(c.strip_digest(d,'decision_digest'))
  sealed=c.prepare_capsule_structural_fixture(f.refresh(state)); self.assertEqual(c.path_readiness_gate(sealed),'PASS')

 def test_github_confirmed_cannot_widen_exact_file_observation(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); pd=state['active_fibers']['repository_evidence']['payload']['path_discovery']; ev=pd['github_path_evidence'][0]
  ev['object_type']='FILE'; ev['scope']={'scope_type':'EXACT_FILE','object_path':'runtime/joyflow_dual_layer.py','observed_paths':['runtime/joyflow_dual_layer.py'],'observed_paths_digest':c.digest(['runtime/joyflow_dual_layer.py']),'raw_object_sha256':c.digest('exact-file'),'scope_digest':None}; ev['scope']['scope_digest']=c.digest(c._github_scope_payload(ev)); ev['evidence_digest']=c.digest(c.strip_digest(ev,'evidence_digest'))
  src=next(x for x in state['evidence_registry'] if x['evidence_id']=='E_GITHUB_PATHS'); src.update({'kind':'GITHUB_FILE','claim':c._github_scope_claim(ev),'subject_type':'GITHUB_OBJECT','subject_id':ev['object_ref'],'ref':ev['raw_evidence_ref'],'raw_output_ref':ev['raw_evidence_ref']}); src['claim_digest']=c.digest(src['claim'])
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))

 def test_github_derived_requires_typed_source_and_covered_start_path(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); d=state['active_fibers']['repository_evidence']['payload']['path_discovery']['final_path_decision']; item=d['allowed_path_items'][0]
  item.update({'basis_type':'GITHUB_DERIVED','source_github_path_evidence_ids':['E_GITHUB_PATHS'],'derived_from_paths':['runtime/**'],'supporting_evidence_refs':[],'derivation_summary':'Brain narrows a current GitHub-observed runtime root.'}); d['decision_digest']=c.digest(c.strip_digest(d,'decision_digest'))
  self.assertEqual(c.path_readiness_gate(c.prepare_capsule_structural_fixture(f.refresh(state))),'PASS')
  bad=copy.deepcopy(state); bd=bad['active_fibers']['repository_evidence']['payload']['path_discovery']['final_path_decision']; bd['allowed_path_items'][0]['derived_from_paths']=['unrelated/**']; bd['decision_digest']=c.digest(c.strip_digest(bd,'decision_digest'))
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(bad))

 def test_github_derived_cannot_use_generic_repository_evidence(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); d=state['active_fibers']['repository_evidence']['payload']['path_discovery']['final_path_decision']; item=d['allowed_path_items'][0]
  item.update({'basis_type':'GITHUB_DERIVED','source_github_path_evidence_ids':['E_TEST_PLAN'],'derived_from_paths':['runtime/**'],'supporting_evidence_refs':[]}); d['decision_digest']=c.digest(c.strip_digest(d,'decision_digest'))
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))

 def test_typed_path_sources_are_separate_from_supporting_evidence(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); d=state['active_fibers']['repository_evidence']['payload']['path_discovery']['final_path_decision']; item=d['allowed_path_items'][0]
  item['supporting_evidence_refs']=['E_GITHUB_PATHS']; d['decision_digest']=c.digest(c.strip_digest(d,'decision_digest'))
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))


 def test_cli_exposes_exact_local_discovery_seal_inputs(self):
  import subprocess,sys
  out=subprocess.run([sys.executable,str(ROOT/'runtime/joyflow_dual_layer.py'),'seal','-h'],capture_output=True,text=True,check=True).stdout
  self.assertIn('--path-discovery-projection',out); self.assertIn('--path-discovery-return',out)

if __name__=='__main__': unittest.main()
