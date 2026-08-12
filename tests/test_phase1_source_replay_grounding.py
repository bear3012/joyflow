from __future__ import annotations
import copy, hashlib, importlib.util, json, pathlib, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('c',ROOT/'runtime/joyflow_dual_layer.py'); c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
spec2=importlib.util.spec_from_file_location('f',ROOT/'tests/build_fixture.py'); f=importlib.util.module_from_spec(spec2); spec2.loader.exec_module(f)

class SourceReplayGrounding(unittest.TestCase):
 def repo(self, td: str, *, second_commit: bool=True):
  repo=pathlib.Path(td)/'repo'; repo.mkdir()
  subprocess.run(['git','init',str(repo)],check=True,capture_output=True)
  subprocess.run(['git','-C',str(repo),'config','user.email','joyflow@example.invalid'],check=True)
  subprocess.run(['git','-C',str(repo),'config','user.name','Joyflow Test'],check=True)
  subprocess.run(['git','-C',str(repo),'remote','add','origin','https://github.com/example/repo.git'],check=True)
  for rel,text in {
   'runtime/joyflow_dual_layer.py':'VALUE = 1\n',
   'machine/joyflow_dual_layer_model.yaml':'model: 1\n',
   'tests/test_phase1_single_active_task_round.py':'import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n',
  }.items():
   p=repo/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)
  subprocess.run(['git','-C',str(repo),'add','.'],check=True); subprocess.run(['git','-C',str(repo),'commit','-m','base'],check=True,capture_output=True)
  base=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
  head=base
  if second_commit:
   (repo/'runtime/joyflow_dual_layer.py').write_text('VALUE = 2\n')
   subprocess.run(['git','-C',str(repo),'add','.'],check=True); subprocess.run(['git','-C',str(repo),'commit','-m','change'],check=True,capture_output=True)
   head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
  return repo,base,head

 def refresh_lifecycle(self, p):
  lifecycle=p['task_object_lifecycle']; anchor=p['task_anchor']
  if anchor.get('repository_anchor') is not None:
   a=anchor['repository_anchor']; approved={'object_type':'REPOSITORY_BASE','repository_id':a['repository_id'],'base_commit':a['baseline_commit']}
  else:
   a=anchor['artifact_anchor']
   if a['source_mode']=='NEW_ARTIFACT':
    materials=c._canonical_source_materials(a.get('source_materials',[])); approved={'object_type':'SOURCE_MATERIAL_SET','source_mode':'NEW_ARTIFACT','source_materials':materials,'source_material_set_digest':c._source_material_set_digest(materials),'source_material_refs':copy.deepcopy(a.get('source_material_refs',[]))}
   else: approved={'object_type':'ARTIFACT_SOURCE','source_mode':'EXISTING_ARTIFACT','artifact_id':a.get('artifact_id'),'artifact_sha256':a.get('artifact_sha256'),'source_material_refs':copy.deepcopy(a.get('source_material_refs',[]))}
  approved['object_digest']=c.digest(approved); lifecycle['approved_input_object']=approved
  discovery=lifecycle['discovery_object']; discovery['source_object_digest']=approved['object_digest']
  pd=p.get('repository_evidence',{}).get('path_discovery',{}); final=pd.get('final_path_decision') if isinstance(pd,dict) else None
  discovery['final_path_decision_digest']=final.get('decision_digest') if isinstance(final,dict) else None
  if discovery.get('discovery_mode')=='GITHUB_PLUS_LOCAL' and isinstance(final,dict):
   binding=pd.get('local_discovery_binding') or {}; source=discovery.get('discovery_source_object') or {}
   source.update({'discovery_projection_digest':binding.get('source_projection_digest'),'path_discovery_return_digest':binding.get('path_discovery_return_digest'),'selected_item_ids':c._selected_discovery_item_ids(final)}); source['source_digest']=c.digest(c.strip_digest(source,'source_digest')); discovery['discovery_source_object']=source
  discovery['discovery_digest']=c.digest(c.strip_digest(discovery,'discovery_digest'))
  boundary=lifecycle['approved_execution_boundary']
  boundary['validation_commands']=sorted([{'check_id':r['check_id'],'argv':copy.deepcopy(r['argv']),'cwd_scope':r['cwd_scope']} for r in p['validation']['checks']],key=lambda r:r['check_id'])
  boundary['allowed_paths']=sorted(r['statement'] for r in p['decision_boundary'].get('boundary_obligations',[]) if r.get('kind')=='ALLOW_PATH')
  boundary['boundary_digest']=c.digest(c.strip_digest(boundary,'boundary_digest'))
  lifecycle['lifecycle_digest']=c.digest(c.strip_digest(lifecycle,'lifecycle_digest'))
  p['projection_digest']=c.digest(c.projection_payload(p)); return p

 def actualize_projection(self, projection, base, repo=None):
  p=copy.deepcopy(projection)
  p['task_anchor']['repository_anchor']['baseline_commit']=base
  p['execution_object']['expected_ref_or_sha256']=base
  if p['decision_boundary'].get('repository_binding'):
   p['decision_boundary']['repository_binding']['expected_base_commit']=base
  pd=p['repository_evidence']['path_discovery']; pd['github_ref']=f'github:example/repo@{base}'
  for row in pd['github_path_evidence']:
   row['object_ref']=f'github:example/repo@{base}'; row['observed_commit_or_head']=base
   if repo is not None: row['scope']['raw_object_sha256']=__import__('hashlib').sha256(c.canonical_bytes(c._github_source_capture_payload(row,repo))).hexdigest()
   row['scope']['scope_digest']=c.digest(c._github_scope_payload(row)); row['evidence_digest']=c.digest(c.strip_digest(row,'evidence_digest'))
  if pd.get('final_path_decision'):
   pd['final_path_decision']['baseline_commit']=base; pd['final_path_decision']['decision_digest']=c.digest(c.strip_digest(pd['final_path_decision'],'decision_digest'))
  return self.refresh_lifecycle(p)


 def actual_approved_capsule(self, base, repo):
  self._current_repo_for_helper=repo
  state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
  state['task_anchor']['repository_anchor']['baseline_commit']=base
  state['active_fibers']['decision_boundary']['payload']['repository_binding']['expected_base_commit']=base
  repo_payload=state['active_fibers']['repository_evidence']['payload']
  repo_payload['baseline_commit']=base
  path_state=repo_payload['path_discovery']
  path_state['github_ref']=f'github:example/repo@{base}'
  path_state['final_path_decision']['baseline_commit']=base
  typed,source=f.github_path_fixture()
  typed['object_ref']=f'github:example/repo@{base}'
  typed['observed_commit_or_head']=base
  typed['scope']['raw_object_sha256']=__import__('hashlib').sha256(c.canonical_bytes(c._github_source_capture_payload(typed,self._current_repo_for_helper))).hexdigest()
  typed['scope']['scope_digest']=c.digest(c._github_scope_payload(typed))
  typed['evidence_digest']=c.digest(c.strip_digest(typed,'evidence_digest'))
  source['ref']=typed['raw_evidence_ref']=f'github:example/repo@{base}:path-discovery'
  typed['evidence_digest']=c.digest(c.strip_digest(typed,'evidence_digest'))
  source['raw_output_ref']=typed['raw_evidence_ref']
  source['raw_output_sha256']=typed['scope']['raw_object_sha256']
  source['subject_id']=typed['object_ref']
  source['claim']=c._github_scope_claim(typed)
  source['claim_digest']=c.digest(source['claim'])
  path_state['github_path_evidence']=[copy.deepcopy(typed)]
  path_state['final_path_decision']['decision_digest']=c.digest(c.strip_digest(path_state['final_path_decision'],'decision_digest'))
  for i,row in enumerate(state['evidence_registry']):
   if row['evidence_id']=='E_GITHUB_PATHS': state['evidence_registry'][i]=source
  state=f.refresh(state)
  current=c.prepare_capsule_structural_fixture(state)
  if current['task_progress']['stage'] in {'INTENT_DISCUSSION','REPOSITORY_DISCOVERY'}: current=f.advance(current,'DECISION_CLOSURE')
  if current['task_progress']['stage']!='USER_APPROVAL': current=f.advance(current,'USER_APPROVAL')
  projection,view,binding=c.draft_handoff(current)
  current=copy.deepcopy(current)
  current['approval_record']={'status':'APPROVED_FINAL','owner':'WEB_BRAIN','scope':c.expected_approval_scope(current),'basis':'CURRENT_EXPLICIT_USER_DECISION','decision_ref':'conversation:test-execution-approval','binding':binding}
  current['derived_gates']=c.compute_gate_snapshot(current)
  c.validate_capsule(current)
  return current,projection

 def refresh_bundle(self,bundle):
  by={x['capture_id']:x for x in bundle['raw_captures']}
  for cap in by.values(): cap['stdout_sha256']=hashlib.sha256(cap['stdout'].encode('utf-8')).hexdigest(); cap['stderr_sha256']=hashlib.sha256(cap['stderr'].encode('utf-8')).hexdigest(); cap['capture_sha256']=c.digest(c._execution_capture_payload(cap))
  for ev in bundle['evidence_rows']:
   cap=by[ev['raw_output_ref']]; ev['claim']=c._direct_capture_claim(cap); ev['claim_digest']=c.digest(ev['claim']); ev['raw_output_sha256']=cap['capture_sha256']; ev['ref']=cap['capture_id']
  bundle['evidence_bundle_digest']=c.digest(c.strip_digest(bundle,'evidence_bundle_digest'))

 def real_return(self, repo, base, head, projection=None):
  if projection is None:
   _,projection,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
  p=self.actualize_projection(projection,base,repo) if projection.get('execution_object',{}).get('expected_ref_or_sha256')!=base else copy.deepcopy(projection)
  p=self.refresh_lifecycle(p)
  r,b=f.codex_return(p)
  base_obj={'object_type':'REPOSITORY','source_mode':'REPOSITORY_REF','object_id':'example/repo','ref_or_sha256':base}
  head_obj={'object_type':'REPOSITORY','source_mode':'REPOSITORY_REF','object_id':'example/repo','ref_or_sha256':head}
  test_cmd=copy.deepcopy(p['validation']['checks'][0]['argv'])
  with c._detached_validation_worktree(repo,head) as wt:
   final_proc=subprocess.run(test_cmd,cwd=wt,capture_output=True)
  with c._detached_validation_worktree(repo,base) as wt:
   pre_proc=subprocess.run(test_cmd,cwd=wt,capture_output=True)
  base_data=subprocess.check_output(['git','-C',str(repo),'show',f'{base}:runtime/joyflow_dual_layer.py'])
  diff=subprocess.check_output(['git','-C',str(repo),'diff','--binary',base,head])
  names=subprocess.check_output(['git','-C',str(repo),'diff','--name-only',base,head],text=True).splitlines()
  for cap in b['raw_captures']:
   if cap['capture_kind']=='REPOSITORY_COMMIT':
    role=cap['observation']['role']; ref=base if role=='APPROVED_INPUT' else head; obj=base_obj if role=='APPROVED_INPUT' else head_obj
    cap.update({'command':f'git rev-parse {ref}^{{commit}}','exit_code':0,'stdout':ref+'\n','stderr':'','observed_object':copy.deepcopy(obj),'observation':{'repository_id':'example/repo','remote_url':'https://github.com/example/repo.git','commit_sha':ref,'role':role}})
   elif cap['capture_kind']=='REPOSITORY_FILE':
    cap.update({'command':f'git show {base}:runtime/joyflow_dual_layer.py','exit_code':0,'stdout':base_data.decode('utf-8','replace'),'stderr':'','observed_object':copy.deepcopy(base_obj),'observation':{'path':'runtime/joyflow_dual_layer.py','file_sha256':__import__('hashlib').sha256(base_data).hexdigest(),'bytes':len(base_data)}})
   elif cap['capture_kind']=='TEST_COMMAND':
    is_final=cap['subject_type']=='VALIDATION_CHECK'; proc=final_proc if is_final else pre_proc; obj=head_obj if is_final else base_obj; target=head if is_final else base
    cap.update({'command':c._canonical_argv(test_cmd),'exit_code':proc.returncode,'stdout':proc.stdout.decode('utf-8','replace'),'stderr':proc.stderr.decode('utf-8','replace'),'observed_object':copy.deepcopy(obj),'observation':{'argv':test_cmd,'cwd_scope':'SOURCE_ROOT','target_ref':target}})
   elif cap['capture_kind']=='REPOSITORY_DIFF':
    cap.update({'command':f'git diff --binary {base} {head}','exit_code':0,'stdout':diff.decode('utf-8','replace'),'stderr':'','observed_object':copy.deepcopy(head_obj),'observation':{'base_ref':base,'head_ref':head,'changed_paths':sorted(names),'diff_sha256':__import__('hashlib').sha256(diff).hexdigest()}})
  r['pr_evidence'].update({'base_commit':base,'head_sha':head,'touched_files':sorted(names)})
  result=r['execution_lifecycle_result']; result['execution_result_object'].update({'base_commit':base,'head_commit':head}); result['final_validation_object']['target_commit']=head; result['transition_digest']=c.execution_lifecycle_result_digest(result)
  for cap in b['raw_captures']:
   if cap['capture_kind']=='REPOSITORY_DIFF': cap['subject_id']=head
  next(x for x in b['evidence_rows'] if x['kind']=='REPOSITORY_DIFF')['subject_id']=head
  self.refresh_bundle(b); r['evidence_bundle_digest']=b['evidence_bundle_digest']; r['return_digest']=c.digest(c.strip_digest(r,'return_digest'))
  return p,r,b

 def actualize_discovery(self, repo, base):
  _,projection,_,_=f.approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY'); p=self.actualize_projection(projection,base,repo)
  r=f.path_discovery_return(p); r['repository']['github_ref']=f'github:example/repo@{base}'
  components=c._source_worktree_components(repo)
  for key,phase,eid in [('repository_state_before','BEFORE','DISC_STATE_BEFORE'),('repository_state_after','AFTER','DISC_STATE_AFTER')]:
   row=r[key]; row.update(components); row['capture_phase']=phase; row['evidence_ref']=eid; row['state_fingerprint_sha256']=c.digest(c._state_fingerprint_payload(row)); row['capture_record_digest']=c.digest(c._capture_record_payload(row))
  evs={x['evidence_id']:x for x in r['evidence_rows']}
  for key in ('repository_state_before','repository_state_after'):
   row=r[key]; ev=evs[row['evidence_ref']]; ev['claim']=c._git_state_claim(row); ev['claim_digest']=c.digest(ev['claim'])
  r['return_digest']=c.digest(c.strip_digest(r,'return_digest'))
  return p,r


 def actual_artifact_approved_capsule(self, source, artifact_argv):
  state=f.new_capsule('ARTIFACT_REPAIR','ARTIFACT_CHANGE')
  sha=__import__('hashlib').sha256(source.read_bytes()).hexdigest()
  state['task_anchor']['artifact_anchor'].update({'artifact_id':source.name,'artifact_sha256':sha})
  check=state['active_fibers']['validation']['payload']['checks'][0]; check['argv']=copy.deepcopy(artifact_argv); check['command']=c._canonical_argv(artifact_argv); check['cwd_scope']='SOURCE_ROOT'
  state=f.refresh(state); current=c.prepare_capsule_structural_fixture(state)
  if current['task_progress']['stage'] in {'INTENT_DISCUSSION','REPOSITORY_DISCOVERY'}: current=f.advance(current,'DECISION_CLOSURE')
  if current['task_progress']['stage']!='USER_APPROVAL': current=f.advance(current,'USER_APPROVAL')
  projection,view,binding=c.draft_handoff(current); current=copy.deepcopy(current)
  current['approval_record']={'status':'APPROVED_FINAL','owner':'WEB_BRAIN','scope':c.expected_approval_scope(current),'basis':'CURRENT_EXPLICIT_USER_DECISION','decision_ref':'conversation:test-artifact-execution-approval','binding':binding}
  current['derived_gates']=c.compute_gate_snapshot(current); c.validate_capsule(current)
  return current,projection

 def actual_artifact_return(self, td):
  source_root=pathlib.Path(td)/'source'; source_root.mkdir()
  output_root=pathlib.Path(td)/'outputs'; output_root.mkdir()
  source=source_root/'source-artifact.zip'; source.write_bytes(b'approved source bytes')
  output=output_root/'repaired-artifact.zip'; output.write_bytes(b'repaired output bytes')
  tests_dir=source_root/'tests'; tests_dir.mkdir(); (tests_dir/'test_artifact_validation.py').write_text('import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n')
  artifact_argv=[sys.executable,'-c','print("artifact validation pass")']
  approved,p=self.actual_artifact_approved_capsule(source,artifact_argv); self._actual_artifact_approved=approved
  source_sha=__import__('hashlib').sha256(source.read_bytes()).hexdigest(); output_sha=__import__('hashlib').sha256(output.read_bytes()).hexdigest()
  r,b=f.codex_return(p)
  input_obj={'object_type':'ARTIFACT','source_mode':'EXISTING_ARTIFACT','object_id':source.name,'ref_or_sha256':source_sha}
  output_obj={'object_type':'ARTIFACT','source_mode':'NEW_ARTIFACT','object_id':output.name,'ref_or_sha256':output_sha}
  test_proc=subprocess.run(artifact_argv,cwd=source.parent,capture_output=True)
  for cap in b['raw_captures']:
   if cap['capture_kind']=='ARTIFACT_SHA256':
    is_output=cap['capture_id']=='CAP_EXEC_ARTIFACT'; path=output if is_output else source; obj=output_obj if is_output else input_obj
    cap.update({'command':f'sha256 {path}','exit_code':0,'stdout':'','stderr':'','observed_object':copy.deepcopy(obj),'observation':{'artifact_id':path.name,'artifact_path':str(path.resolve()),'artifact_sha256':obj['ref_or_sha256'],'bytes':path.stat().st_size}})
    if is_output: cap['subject_type']='ARTIFACT'; cap['subject_id']=output_sha
   elif cap['capture_kind']=='TEST_COMMAND':
    argv=cap['observation']['argv']; final=cap['subject_type']=='VALIDATION_CHECK'; obj=output_obj if final else input_obj
    cap.update({'command':c._canonical_argv(argv),'exit_code':test_proc.returncode,'stdout':test_proc.stdout.decode('utf-8','replace'),'stderr':test_proc.stderr.decode('utf-8','replace'),'observed_object':copy.deepcopy(obj),'observation':{'argv':argv,'cwd_scope':'SOURCE_ROOT','target_ref':obj['ref_or_sha256']}})
  r['technical_preflight']['expected_execution_object']=copy.deepcopy(input_obj); r['technical_preflight']['observed_execution_object']=copy.deepcopy(input_obj)
  outrow=r['artifact_evidence']['outputs'][0]; outrow.update({'artifact_id':output.name,'artifact_digest':output_sha,'bytes':output.stat().st_size,'media_type':'application/zip','role':'PRIMARY'})
  r['artifact_evidence']['output_set_digest']=c._artifact_output_set_digest(r['artifact_evidence']['outputs'])
  outputs=c._canonical_artifact_outputs(r['artifact_evidence']['outputs']); output_set_digest=r['artifact_evidence']['output_set_digest']
  refs=sorted(outrow['validation_evidence_refs']); coverage=[{'artifact_id':output.name,'validation_evidence_refs':refs}]
  lr=r['execution_lifecycle_result']; lr['execution_result_object']={'result_type':'ARTIFACT_OUTPUT_SET','outputs':outputs,'output_set_digest':output_set_digest}; lr['final_validation_object']={'target_type':'ARTIFACT_OUTPUT_SET','target_digest':output_set_digest,'validation_environment':'EXACT_OUTPUT_FILES','machine_result_evidence_refs':sorted({x['evidence_ref'] for x in r['machine_results']}),'artifact_validation_evidence_refs':refs,'output_validation_coverage':coverage,'uncovered_output_ids':[]}; lr['transition_digest']=c.execution_lifecycle_result_digest(lr)
  out_ev=next(x for x in b['evidence_rows'] if x['evidence_id']=='EXEC_ARTIFACT'); out_ev['subject_id']=output_sha
  self.refresh_bundle(b); r['evidence_bundle_digest']=b['evidence_bundle_digest']; r['return_digest']=c.digest(c.strip_digest(r,'return_digest'))
  return source,output,p,r,b

 def test_strict_execution_replay_accepts_real_source(self):
  with tempfile.TemporaryDirectory() as td:
   repo,base,head=self.repo(td); p,r,b=self.real_return(repo,base,head)
   c.validate_codex_execution_return(r,p,b,repository=repo)

 def test_repository_validation_git_admin_mutation_blocks_without_touching_source(self):
  with tempfile.TemporaryDirectory() as td:
   repo,base,head=self.repo(td)
   code=("import hashlib,pathlib,subprocess; "
         "name='VALIDATION_MUTATION_'+hashlib.sha256(str(pathlib.Path.cwd()).encode()).hexdigest()[:12]; "
         "subprocess.run(['git','tag','-f',name],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); "
         "print('joyflow-validation-ok')")
   argv=[sys.executable,'-c',code]
   old_argv,old_command=f.VALIDATION_ARGV,f.VALIDATION_COMMAND
   f.VALIDATION_ARGV=copy.deepcopy(argv); f.VALIDATION_COMMAND=c._canonical_argv(argv)
   try:
    approved,p=self.actual_approved_capsule(base,repo)
   finally:
    f.VALIDATION_ARGV,f.VALIDATION_COMMAND=old_argv,old_command
   p,r,b=self.real_return(repo,base,head,p)
   refs_before=subprocess.check_output(['git','-C',str(repo),'for-each-ref','--format=%(refname):%(objectname)'],text=True).splitlines()
   with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return(r,p,b,repository=repo)
   refs_after=subprocess.check_output(['git','-C',str(repo),'for-each-ref','--format=%(refname):%(objectname)'],text=True).splitlines()
   self.assertEqual(refs_before,refs_after)

 def test_fabricated_repository_head_capture_blocks(self):
  with tempfile.TemporaryDirectory() as td:
   repo,base,head=self.repo(td); p,r,b=self.real_return(repo,base,head)
   cap=next(x for x in b['raw_captures'] if x['capture_kind']=='REPOSITORY_COMMIT' and x['observation'].get('role')=='APPROVED_INPUT'); cap['stdout']='fabricated\n'; self.refresh_bundle(b); r['evidence_bundle_digest']=b['evidence_bundle_digest']; r['return_digest']=c.digest(c.strip_digest(r,'return_digest'))
   with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return(r,p,b,repository=repo)

 def test_fabricated_test_pass_blocks_by_replay(self):
  with tempfile.TemporaryDirectory() as td:
   repo,base,head=self.repo(td); p,r,b=self.real_return(repo,base,head)
   cap=next(x for x in b['raw_captures'] if x['capture_kind']=='TEST_COMMAND'); cap['stdout']='tests were never run\n'; self.refresh_bundle(b); r['evidence_bundle_digest']=b['evidence_bundle_digest']; r['return_digest']=c.digest(c.strip_digest(r,'return_digest'))
   with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return(r,p,b,repository=repo)

 def test_strict_path_discovery_replay_accepts_current_repository(self):
  with tempfile.TemporaryDirectory() as td:
   repo,base,_=self.repo(td,second_commit=False); p,r=self.actualize_discovery(repo,base)
   c.validate_path_discovery_return(r,p,repository=repo)

 def test_fabricated_local_path_blocks_by_source_replay(self):
  with tempfile.TemporaryDirectory() as td:
   repo,base,_=self.repo(td,second_commit=False); p,r=self.actualize_discovery(repo,base)
   r['confirmed_paths'][0]['path']='invented/by-codex.py'; ev=next(x for x in r['evidence_rows'] if x['evidence_id']=='DISC_OBS_RUNTIME'); ev['observed_path']='invented/by-codex.py'; ev['claim']=c._path_observation_claim(r['confirmed_paths'][0]['path_id'],r['confirmed_paths'][0]['path']); ev['claim_digest']=c.digest(ev['claim']); r['return_digest']=c.digest(c.strip_digest(r,'return_digest'))
   with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return(r,p,repository=repo)

 def test_fabricated_fingerprint_blocks_by_source_replay(self):
  with tempfile.TemporaryDirectory() as td:
   repo,base,_=self.repo(td,second_commit=False); p,r=self.actualize_discovery(repo,base)
   for key in ('repository_state_before','repository_state_after'):
    row=r[key]; row['worktree_diff_sha256']='f'*64; row['state_fingerprint_sha256']=c.digest(c._state_fingerprint_payload(row)); row['capture_record_digest']=c.digest(c._capture_record_payload(row)); ev=next(x for x in r['evidence_rows'] if x['evidence_id']==row['evidence_ref']); ev['claim']=c._git_state_claim(row); ev['claim_digest']=c.digest(ev['claim'])
   r['return_digest']=c.digest(c.strip_digest(r,'return_digest'))
   with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return(r,p,repository=repo)

 def test_fabricated_github_path_blocks_before_execution(self):
  with tempfile.TemporaryDirectory() as td:
   repo,base,_=self.repo(td,second_commit=False); _,projection,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); p=self.actualize_projection(projection,base,repo)
   row=p['repository_evidence']['path_discovery']['github_path_evidence'][0]; row['scope']['observed_paths']=['invented/**']; row['scope']['observed_paths_digest']=c.digest(['invented/**']); row['scope']['scope_digest']=c.digest(c._github_scope_payload(row)); row['evidence_digest']=c.digest(c.strip_digest(row,'evidence_digest')); p['projection_digest']=c.digest(c.projection_payload(p))
   with self.assertRaises(c.JoyflowError): c.verify_projection_path_sources_against_repository(p,repo,require_current_head=True)

 def test_strict_review_replays_exact_source(self):
  with tempfile.TemporaryDirectory() as td:
   repo,base,head=self.repo(td); approved,p=self.actual_approved_capsule(base,repo); p,r,b=self.real_return(repo,base,head,p)
   executing=f.advance(approved,'CODEX_EXECUTION'); review=f.brain_review_capsule(executing,p,r,b)
   c.validate_review_input_binding(review,p,r,b,source_repository=repo)

 def test_strict_artifact_replay_accepts_exact_input_and_output(self):
  with tempfile.TemporaryDirectory() as td:
   source,output,p,r,b=self.actual_artifact_return(td)
   c.validate_codex_execution_return(r,p,b,artifact=source,artifact_outputs=[output],artifact_output_root=output.parent)

 def test_fabricated_artifact_output_blocks(self):
  with tempfile.TemporaryDirectory() as td:
   source,output,p,r,b=self.actual_artifact_return(td)
   cap=next(x for x in b['raw_captures'] if x['capture_id']=='CAP_EXEC_ARTIFACT'); cap['observation']['bytes']+=1
   self.refresh_bundle(b); r['evidence_bundle_digest']=b['evidence_bundle_digest']; r['return_digest']=c.digest(c.strip_digest(r,'return_digest'))
   with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return(r,p,b,artifact=source,artifact_outputs=[output],artifact_output_root=output.parent)

 def test_pr_diff_replay_uses_actual_base_head_changed_paths(self):
  with tempfile.TemporaryDirectory() as td:
   repo,base,head=self.repo(td)
   row,_=f.github_path_fixture()
   row.update({'object_type':'PR_DIFF','object_ref':f'github:example/repo@{head}','observed_commit_or_head':head,'base_ref':base,'head_ref':head})
   row['scope'].update({'scope_type':'PATH_SET','object_path':None,'observed_paths':['runtime/**']})
   row['scope']['observed_paths_digest']=c.digest(row['scope']['observed_paths'])
   row['scope']['raw_object_sha256']=__import__('hashlib').sha256(c.canonical_bytes(c._github_source_capture_payload(row,repo))).hexdigest()
   row['scope']['scope_digest']=c.digest(c._github_scope_payload(row)); row['evidence_digest']=c.digest(c.strip_digest(row,'evidence_digest'))
   c.verify_github_path_evidence_against_repository(row,repo)
   bad=copy.deepcopy(row); bad['scope']['observed_paths']=['tests/**']; bad['scope']['observed_paths_digest']=c.digest(bad['scope']['observed_paths']); bad['scope']['raw_object_sha256']=__import__('hashlib').sha256(c.canonical_bytes(c._github_source_capture_payload(bad,repo))).hexdigest(); bad['scope']['scope_digest']=c.digest(c._github_scope_payload(bad)); bad['evidence_digest']=c.digest(c.strip_digest(bad,'evidence_digest'))
   with self.assertRaises(c.JoyflowError): c.verify_github_path_evidence_against_repository(bad,repo)

 def test_local_semantic_derivation_cannot_masquerade_as_tool_fact(self):
  _,projection,_,_=f.approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY'); ret=f.path_discovery_return(projection)
  ev=next(x for x in ret['evidence_rows'] if x['kind']=='DEPENDENCY_DERIVATION')
  ev.update({'produced_by':'TOOL','raw_output_ref':'raw:invented-dependency','raw_output_sha256':'a'*64,'source_evidence_refs':[]})
  ev['claim_digest']=c.digest(ev['claim']); ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
  with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return_structure(ret,projection)

 def test_declared_ignored_runtime_path_change_is_detected(self):
  with tempfile.TemporaryDirectory() as td:
   repo,base,_=self.repo(td,second_commit=False)
   (repo/'.gitignore').write_text('ignored.cfg\n'); subprocess.run(['git','-C',str(repo),'add','.gitignore'],check=True); subprocess.run(['git','-C',str(repo),'commit','-m','ignore'],check=True,capture_output=True)
   base=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
   (repo/'ignored.cfg').write_text('VALUE=A\n')
   coverage={'mode':'DECLARED_EXECUTION_RELEVANT_ONLY','exact_files':['ignored.cfg'],'exact_symlinks':[],'recursive_directories':[],'coverage_status':'COMPLETE_FOR_DECLARED_EXECUTION_RELEVANT_PATHS','full_local_filesystem_unchanged_claim':False}; before=c._source_worktree_components(repo,coverage)
   tool=ROOT/'tools/capture_worktree_fingerprint.py'
   out_before=pathlib.Path(td)/'ignored-before'; raw_before=subprocess.check_output([sys.executable,str(tool),'--repo',str(repo),'--phase','BEFORE','--capture-id','IGN_BEFORE','--evidence-ref','EV_IGN_BEFORE','--include-ignored-file','ignored.cfg','--output-dir',str(out_before)],text=True)
   helper_before=json.loads(raw_before)
   self.assertEqual(helper_before['record']['declared_ignored_manifest_sha256'],before['declared_ignored_manifest_sha256'])
   (repo/'ignored.cfg').write_text('VALUE=B\n')
   after=c._source_worktree_components(repo,coverage)
   out_after=pathlib.Path(td)/'ignored-after'; raw_after=subprocess.check_output([sys.executable,str(tool),'--repo',str(repo),'--phase','AFTER','--capture-id','IGN_AFTER','--evidence-ref','EV_IGN_AFTER','--include-ignored-file','ignored.cfg','--output-dir',str(out_after)],text=True)
   helper_after=json.loads(raw_after)
   self.assertEqual(helper_after['record']['declared_ignored_manifest_sha256'],after['declared_ignored_manifest_sha256'])
   self.assertNotEqual(before['declared_ignored_manifest_sha256'],after['declared_ignored_manifest_sha256'])
   _,projection,_,_=f.approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY'); p=self.actualize_projection(projection,base,repo); ret=f.path_discovery_return(p)
   ret['repository']['github_ref']=f'github:example/repo@{base}'; ret['ignored_path_coverage']['exact_files']=['ignored.cfg']
   for key,phase,eid in [('repository_state_before','BEFORE','DISC_STATE_BEFORE'),('repository_state_after','AFTER','DISC_STATE_AFTER')]:
    row=ret[key]; row.update(before); row['capture_phase']=phase; row['evidence_ref']=eid; row['state_fingerprint_sha256']=c.digest(c._state_fingerprint_payload(row)); row['capture_record_digest']=c.digest(c._capture_record_payload(row))
    ev=next(x for x in ret['evidence_rows'] if x['evidence_id']==eid); ev['claim']=c._git_state_claim(row); ev['claim_digest']=c.digest(ev['claim'])
   ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
   with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return(ret,p,repository=repo)

 def test_approved_argv_cannot_be_replaced_by_display_string(self):
  with tempfile.TemporaryDirectory() as td:
   repo,base,head=self.repo(td); p,r,b=self.real_return(repo,base,head)
   cap=next(x for x in b['raw_captures'] if x['capture_kind']=='TEST_COMMAND')
   fake=[sys.executable,'-c','print("FAKE_PASS")']; proc=subprocess.run(fake,cwd=repo,capture_output=True)
   cap.update({'command':c._canonical_argv(fake),'exit_code':proc.returncode,'stdout':proc.stdout.decode(),'stderr':proc.stderr.decode(),'observation':{'argv':fake,'cwd':str(repo)}})
   self.refresh_bundle(b); r['evidence_bundle_digest']=b['evidence_bundle_digest']; r['return_digest']=c.digest(c.strip_digest(r,'return_digest'))
   with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return(r,p,b,repository=repo)

 def test_operational_validation_cannot_disable_test_replay(self):
  with tempfile.TemporaryDirectory() as td:
   repo,base,head=self.repo(td); p,r,b=self.real_return(repo,base,head)
   with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return(r,p,b,repository=repo,replay_tests=False)
   help_text=subprocess.check_output([sys.executable,str(ROOT/'runtime/joyflow_dual_layer.py'),'verify-codex-return','--help'],text=True)
   seal_help=subprocess.check_output([sys.executable,str(ROOT/'runtime/joyflow_dual_layer.py'),'seal','--help'],text=True)
   self.assertNotIn('--no-replay-tests',help_text); self.assertNotIn('--no-replay-tests',seal_help)

 def test_cli_exposes_operational_source_replay(self):
  help_text=subprocess.check_output([sys.executable,str(ROOT/'runtime/joyflow_dual_layer.py'),'verify-codex-return','--help'],text=True)
  self.assertIn('--repository',help_text); self.assertIn('--artifact',help_text); self.assertIn('--path-discovery-return',help_text); self.assertNotIn('--no-replay-tests',help_text)
  projection_help=subprocess.check_output([sys.executable,str(ROOT/'runtime/joyflow_dual_layer.py'),'verify-execution-projection','--help'],text=True)
  self.assertIn('--repository',projection_help)


if __name__=='__main__': unittest.main()
