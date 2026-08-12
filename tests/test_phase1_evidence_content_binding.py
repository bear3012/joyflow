from __future__ import annotations
import copy, importlib.util, json, pathlib, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('c',ROOT/'runtime/joyflow_dual_layer.py'); c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
spec2=importlib.util.spec_from_file_location('f',ROOT/'tests/build_fixture.py'); f=importlib.util.module_from_spec(spec2); spec2.loader.exec_module(f)

class EvidenceContentBinding(unittest.TestCase):
 def discovery_objects(self):
  _,projection,_,_=f.approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY')
  return projection,f.path_discovery_return(projection)

 def local_state(self,projection,ret,path='runtime/joyflow_dual_layer.py',basis='LOCAL_DISCOVERY'):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
  for semantic in c.semantic_items(state):
   for effect in semantic.get('effects',[]):
    if effect.get('effect_type')=='ALLOW_PATH': effect['value']=path
  pd=state['active_fibers']['repository_evidence']['payload']['path_discovery']
  pd.update({'github_discovery_status':'COMPLETED_INSUFFICIENT','local_discovery_required':True,'local_discovery_reason':'RUNTIME_ONLY_FACT','local_discovery_status':'COMPLETED','path_discovery_source':'COMBINED' if basis=='COMBINED' else 'LOCAL_CODEX_DISCOVERED','local_discovery_binding':{'source_projection_digest':projection['projection_digest'],'path_discovery_return_digest':ret['return_digest'],'project_id':state['task_anchor']['project_id'],'task_id':state['task_anchor']['task_id'],'round_id':1}})
  item=pd['final_path_decision']['allowed_path_items'][0]
  item.update({'path':path,'basis_type':basis,'source_github_path_evidence_ids':['E_GITHUB_PATHS'] if basis=='COMBINED' else [],'derived_from_paths':['runtime/**'] if basis=='COMBINED' else [],'supporting_evidence_refs':[],'source_path_discovery_return_digest':ret['return_digest'],'source_return_path_ids':['LOCAL_PATH_RUNTIME'],'source_return_dependency_ids':[],'source_return_validation_ids':[],'source_return_finding_ids':[],'derivation_summary':'Brain uses the exact current typed local path item and, when combined, the current GitHub observation.'})
  pd['final_path_decision']['decision_digest']=c.digest(c.strip_digest(pd['final_path_decision'],'decision_digest'))
  return f.refresh(state)

 def test_github_scope_change_without_backing_claim_blocks(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); ev=state['active_fibers']['repository_evidence']['payload']['path_discovery']['github_path_evidence'][0]
  ev['scope']['observed_paths']=['unrelated/**']; ev['scope']['observed_paths_digest']=c.digest(['unrelated/**']); ev['scope']['scope_digest']=c.digest(c._github_scope_payload(ev)); ev['evidence_digest']=c.digest(c.strip_digest(ev,'evidence_digest'))
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))

 def test_github_raw_object_digest_mismatch_blocks(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); src=next(x for x in state['evidence_registry'] if x['evidence_id']=='E_GITHUB_PATHS'); src['raw_output_sha256']='f'*64
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))

 def test_file_evidence_cannot_claim_directory(self):
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); ev=state['active_fibers']['repository_evidence']['payload']['path_discovery']['github_path_evidence'][0]
  ev['object_type']='FILE'; ev['scope']['scope_type']='EXACT_FILE'; ev['scope']['object_path']='runtime/joyflow_dual_layer.py'; ev['scope']['observed_paths']=['runtime/**']; ev['scope']['observed_paths_digest']=c.digest(['runtime/**']); ev['scope']['scope_digest']=c.digest(c._github_scope_payload(ev)); ev['evidence_digest']=c.digest(c.strip_digest(ev,'evidence_digest'))
  src=next(x for x in state['evidence_registry'] if x['evidence_id']=='E_GITHUB_PATHS'); src.update({'kind':'GITHUB_FILE','claim':c._github_scope_claim(ev),'raw_output_sha256':ev['scope']['raw_object_sha256']}); src['claim_digest']=c.digest(src['claim'])
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state))

 def test_local_path_cannot_use_git_state_evidence(self):
  projection,ret=self.discovery_objects(); ret['confirmed_paths'][0]['evidence_ref']='DISC_STATE_BEFORE'; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
  with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return_structure(ret,projection)

 def test_dependency_cannot_use_path_evidence(self):
  projection,ret=self.discovery_objects(); ret['dependency_edges'][0]['evidence_ref']='DISC_LOCAL_RUNTIME'; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
  with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return_structure(ret,projection)

 def test_local_final_path_must_be_covered_by_selected_return_path(self):
  projection,ret=self.discovery_objects(); state=self.local_state(projection,ret,path='unrelated/**')
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(state,path_discovery_projection=projection,path_discovery_return=ret)

 def test_combined_requires_real_local_path_item(self):
  projection,ret=self.discovery_objects(); state=self.local_state(projection,ret,basis='COMBINED'); item=state['active_fibers']['repository_evidence']['payload']['path_discovery']['final_path_decision']['allowed_path_items'][0]; item['source_return_path_ids']=[]; d=state['active_fibers']['repository_evidence']['payload']['path_discovery']['final_path_decision']; d['decision_digest']=c.digest(c.strip_digest(d,'decision_digest'))
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(f.refresh(state),path_discovery_projection=projection,path_discovery_return=ret)

 def test_unresolved_local_question_blocks_final_seal(self):
  projection,ret=self.discovery_objects(); ret['unresolved_questions']=['Which local path is authoritative?']; ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest')); state=self.local_state(projection,ret)
  with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(state,path_discovery_projection=projection,path_discovery_return=ret)

 def test_before_after_must_be_distinct_captures(self):
  projection,ret=self.discovery_objects(); ret['repository_state_after']=copy.deepcopy(ret['repository_state_before']); ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
  with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return_structure(ret,projection)

 def test_fingerprint_helper_detects_change_and_preserves_unchanged_state(self):
  with tempfile.TemporaryDirectory() as td:
   repo=pathlib.Path(td)/'repo'; repo.mkdir(); subprocess.run(['git','init','-q',str(repo)],check=True); subprocess.run(['git','-C',str(repo),'config','user.email','test@example.com'],check=True); subprocess.run(['git','-C',str(repo),'config','user.name','Test'],check=True)
   (repo/'a.txt').write_text('one\n'); subprocess.run(['git','-C',str(repo),'add','.'],check=True); subprocess.run(['git','-C',str(repo),'commit','-qm','init'],check=True)
   tool=ROOT/'tools/capture_worktree_fingerprint.py'
   def capture(phase,eid,name):
    out=pathlib.Path(td)/name
    proc=subprocess.run([sys.executable,str(tool),'--repo',str(repo),'--phase',phase,'--capture-id',name,'--evidence-ref',eid,'--output-dir',str(out)],capture_output=True,text=True,check=True)
    return json.loads(proc.stdout)
   before=capture('BEFORE','EV_BEFORE','before'); unchanged=capture('AFTER','EV_AFTER','unchanged')
   self.assertEqual(before['record']['state_fingerprint_sha256'],unchanged['record']['state_fingerprint_sha256'])
   (repo/'a.txt').write_text('two\n'); changed=capture('AFTER','EV_CHANGED','changed')
   self.assertNotEqual(before['record']['state_fingerprint_sha256'],changed['record']['state_fingerprint_sha256'])

if __name__=='__main__': unittest.main()
