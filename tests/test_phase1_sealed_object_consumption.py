from __future__ import annotations
import copy, hashlib, importlib.util, json, pathlib, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('c',ROOT/'runtime/joyflow_dual_layer.py'); c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
spec2=importlib.util.spec_from_file_location('f',ROOT/'tests/build_fixture.py'); f=importlib.util.module_from_spec(spec2); spec2.loader.exec_module(f)
spec3=importlib.util.spec_from_file_location('sr',ROOT/'tests/test_phase1_source_replay_grounding.py'); sr=importlib.util.module_from_spec(spec3); spec3.loader.exec_module(sr)
from tests.platform_capabilities import probe_symlink_capability

class SealedObjectConsumptionTests(unittest.TestCase):
 def coverage(self,**updates):
  row={'mode':'DECLARED_EXECUTION_RELEVANT_ONLY','exact_files':[],'exact_symlinks':[],'recursive_directories':[],'coverage_status':'COMPLETE_FOR_DECLARED_EXECUTION_RELEVANT_PATHS','full_local_filesystem_unchanged_claim':False}; row.update(updates); return row

 def test_parent_symlink_cannot_escape_repository_boundary(self):
  capability=probe_symlink_capability()
  if not capability['supported']:
   print('PLATFORM_CAPABILITY_NA '+repr(capability)); return
  h=sr.SourceReplayGrounding()
  with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside_td:
   repo,_,_=h.repo(td,second_commit=False); outside=pathlib.Path(outside_td); (outside/'secret.txt').write_text('outside')
   (repo/'linkdir').symlink_to(outside,target_is_directory=True)
   with self.assertRaises(c.JoyflowError): c._declared_ignored_manifest(repo,self.coverage(exact_files=['linkdir/secret.txt']))

 def test_exact_final_symlink_is_consumed_without_following_target(self):
  capability=probe_symlink_capability()
  if not capability['supported']:
   print('PLATFORM_CAPABILITY_NA '+repr(capability)); return
  h=sr.SourceReplayGrounding()
  with tempfile.TemporaryDirectory() as td:
   repo,_,_=h.repo(td,second_commit=False); target=repo/'target.cfg'; target.write_text('secret'); (repo/'current.cfg').symlink_to(target.name)
   rows=json.loads(c._declared_ignored_manifest(repo,self.coverage(exact_symlinks=['current.cfg'])))
   self.assertEqual(rows[0]['kind'],'SYMLINK'); self.assertEqual(rows[0]['link_target'],target.name); self.assertFalse(rows[0]['target_followed'])
   self.assertNotEqual(rows[0]['sha256'],hashlib.sha256(target.read_bytes()).hexdigest())

 def _mutating_artifact_case(self,td):
  td=pathlib.Path(td); srcdir=td/'src'; outdir=td/'out'; srcdir.mkdir(); outdir.mkdir()
  source=srcdir/'source-artifact.zip'; source.write_bytes(b'approved source bytes')
  output=outdir/'repaired-artifact.zip'; initial=b'repaired output bytes'; output.write_bytes(initial)
  argv=[sys.executable,'-c',"from pathlib import Path; p=Path('repaired-artifact.zip'); p.write_bytes(p.read_bytes()+b'X'); print('mutated')"]
  h=sr.SourceReplayGrounding(); approved,p=h.actual_artifact_approved_capsule(source,argv)
  r,b=f.codex_return(p); source_sha=hashlib.sha256(source.read_bytes()).hexdigest(); output_sha=hashlib.sha256(initial).hexdigest()
  input_obj={'object_type':'ARTIFACT','source_mode':'EXISTING_ARTIFACT','object_id':source.name,'ref_or_sha256':source_sha}; output_obj={'object_type':'ARTIFACT','source_mode':'NEW_ARTIFACT','object_id':output.name,'ref_or_sha256':output_sha}
  pre=subprocess.run(argv,cwd=source.parent,capture_output=True); output.write_bytes(initial)
  fin=subprocess.run(argv,cwd=output.parent,capture_output=True); output.write_bytes(initial)
  for cap in b['raw_captures']:
   if cap['capture_kind']=='ARTIFACT_SHA256':
    is_output=cap['capture_id']=='CAP_EXEC_ARTIFACT'; path=output if is_output else source; obj=output_obj if is_output else input_obj
    cap.update({'command':f'sha256 {path}','exit_code':0,'stdout':'','stderr':'','observed_object':copy.deepcopy(obj),'observation':{'artifact_id':path.name,'artifact_path':str(path.absolute()),'artifact_sha256':obj['ref_or_sha256'],'bytes':path.stat().st_size}})
    if is_output: cap['subject_type']='ARTIFACT'; cap['subject_id']=output_sha
   elif cap['capture_kind']=='TEST_COMMAND':
    final=cap['subject_type']=='VALIDATION_CHECK'; proc=fin if final else pre; obj=output_obj if final else input_obj
    cap.update({'command':c._canonical_argv(argv),'exit_code':proc.returncode,'stdout':proc.stdout.decode(),'stderr':proc.stderr.decode(),'observed_object':copy.deepcopy(obj),'observation':{'argv':argv,'cwd_scope':'SOURCE_ROOT','target_ref':obj['ref_or_sha256']}})
  r['technical_preflight']['expected_execution_object']=copy.deepcopy(input_obj); r['technical_preflight']['observed_execution_object']=copy.deepcopy(input_obj)
  outrow=r['artifact_evidence']['outputs'][0]; outrow.update({'artifact_id':output.name,'artifact_digest':output_sha,'bytes':len(initial),'media_type':'application/zip','role':'PRIMARY'}); r['artifact_evidence']['output_set_digest']=c._artifact_output_set_digest(r['artifact_evidence']['outputs'])
  outputs=c._canonical_artifact_outputs(r['artifact_evidence']['outputs']); refs=sorted(outrow['validation_evidence_refs']); lr=r['execution_lifecycle_result']
  lr['execution_result_object']={'result_type':'ARTIFACT_OUTPUT_SET','outputs':outputs,'output_set_digest':r['artifact_evidence']['output_set_digest']}; lr['final_validation_object']={'target_type':'ARTIFACT_OUTPUT_SET','target_digest':r['artifact_evidence']['output_set_digest'],'validation_environment':'EXACT_OUTPUT_FILES','machine_result_evidence_refs':sorted({x['evidence_ref'] for x in r['machine_results']}),'artifact_validation_evidence_refs':refs,'output_validation_coverage':[{'artifact_id':output.name,'validation_evidence_refs':refs}],'uncovered_output_ids':[]}; lr['transition_digest']=c.execution_lifecycle_result_digest(lr)
  next(x for x in b['evidence_rows'] if x['evidence_id']=='EXEC_ARTIFACT')['subject_id']=output_sha
  h.refresh_bundle(b); r['evidence_bundle_digest']=b['evidence_bundle_digest']; r['return_digest']=c.digest(c.strip_digest(r,'return_digest'))
  return source,output,p,r,b

 def test_final_artifact_validation_cannot_mutate_sealed_result(self):
  with tempfile.TemporaryDirectory() as td:
   source,output,p,r,b=self._mutating_artifact_case(td)
   with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return(r,p,b,artifact=source,artifact_outputs=[output],artifact_output_root=output.parent)

 def test_repository_validation_rejects_new_untracked_workspace_object(self):
  h=sr.SourceReplayGrounding()
  with tempfile.TemporaryDirectory() as td:
   repo,base,head=h.repo(td,second_commit=True)
   argv=[sys.executable,'-c',"from pathlib import Path; Path('VALIDATION_MUTATION.tmp').write_text('created'); assert Path('runtime/joyflow_dual_layer.py').is_file(); print('joyflow-validation-ok')"]
   old_argv,old_command=sr.f.VALIDATION_ARGV,sr.f.VALIDATION_COMMAND
   sr.f.VALIDATION_ARGV=copy.deepcopy(argv); sr.f.VALIDATION_COMMAND=c._canonical_argv(argv)
   try:
    _,p=h.actual_approved_capsule(base,repo)
   finally:
    sr.f.VALIDATION_ARGV, sr.f.VALIDATION_COMMAND = old_argv, old_command
   p,r,b=h.real_return(repo,base,head,p)
   with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return(r,p,b,repository=repo)

 def test_artifact_validation_rejects_new_undeclared_workspace_object(self):
  with tempfile.TemporaryDirectory() as td:
   td=pathlib.Path(td); srcdir=td/'src'; outdir=td/'out'; srcdir.mkdir(); outdir.mkdir()
   source=srcdir/'source-artifact.zip'; output=outdir/'repaired-artifact.zip'; extra=outdir/'UNDECLARED_VALIDATION_OUTPUT.bin'
   source.write_bytes(b'approved source bytes'); output.write_bytes(b'repaired output bytes')
   argv=[sys.executable,'-c',"from pathlib import Path; p=Path('repaired-artifact.zip'); p.is_file() and Path('UNDECLARED_VALIDATION_OUTPUT.bin').write_bytes(b'extra'); print('artifact validation pass')"]
   h=sr.SourceReplayGrounding(); _,p=h.actual_artifact_approved_capsule(source,argv); r,b=f.codex_return(p)
   source_sha=hashlib.sha256(source.read_bytes()).hexdigest(); output_sha=hashlib.sha256(output.read_bytes()).hexdigest()
   input_obj={'object_type':'ARTIFACT','source_mode':'EXISTING_ARTIFACT','object_id':source.name,'ref_or_sha256':source_sha}; output_obj={'object_type':'ARTIFACT','source_mode':'NEW_ARTIFACT','object_id':output.name,'ref_or_sha256':output_sha}
   proc=subprocess.run(argv,cwd=outdir,capture_output=True); extra.unlink(missing_ok=True)
   for cap in b['raw_captures']:
    if cap['capture_kind']=='ARTIFACT_SHA256':
     is_output=cap['capture_id']=='CAP_EXEC_ARTIFACT'; path=output if is_output else source; obj=output_obj if is_output else input_obj
     cap.update({'command':f'sha256 {path}','exit_code':0,'stdout':'','stderr':'','observed_object':copy.deepcopy(obj),'observation':{'artifact_id':path.name,'artifact_path':str(path.absolute()),'artifact_sha256':obj['ref_or_sha256'],'bytes':path.stat().st_size}})
     if is_output: cap['subject_type']='ARTIFACT'; cap['subject_id']=output_sha
    elif cap['capture_kind']=='TEST_COMMAND':
     final=cap['subject_type']=='VALIDATION_CHECK'; obj=output_obj if final else input_obj
     cap.update({'command':c._canonical_argv(argv),'exit_code':proc.returncode,'stdout':proc.stdout.decode(),'stderr':proc.stderr.decode(),'observed_object':copy.deepcopy(obj),'observation':{'argv':argv,'cwd_scope':'SOURCE_ROOT','target_ref':obj['ref_or_sha256']}})
   r['technical_preflight']['expected_execution_object']=copy.deepcopy(input_obj); r['technical_preflight']['observed_execution_object']=copy.deepcopy(input_obj)
   outrow=r['artifact_evidence']['outputs'][0]; outrow.update({'artifact_id':output.name,'artifact_digest':output_sha,'bytes':output.stat().st_size,'media_type':'application/zip','role':'PRIMARY'}); r['artifact_evidence']['output_set_digest']=c._artifact_output_set_digest(r['artifact_evidence']['outputs'])
   outputs=c._canonical_artifact_outputs(r['artifact_evidence']['outputs']); refs=sorted(outrow['validation_evidence_refs']); lr=r['execution_lifecycle_result']
   lr['execution_result_object']={'result_type':'ARTIFACT_OUTPUT_SET','outputs':outputs,'output_set_digest':r['artifact_evidence']['output_set_digest']}
   lr['final_validation_object']={'target_type':'ARTIFACT_OUTPUT_SET','target_digest':r['artifact_evidence']['output_set_digest'],'validation_environment':'EXACT_OUTPUT_FILES','machine_result_evidence_refs':sorted({x['evidence_ref'] for x in r['machine_results']}),'artifact_validation_evidence_refs':refs,'output_validation_coverage':[{'artifact_id':output.name,'validation_evidence_refs':refs}],'uncovered_output_ids':[]}
   lr['transition_digest']=c.execution_lifecycle_result_digest(lr); next(x for x in b['evidence_rows'] if x['evidence_id']=='EXEC_ARTIFACT')['subject_id']=output_sha
   h.refresh_bundle(b); r['evidence_bundle_digest']=b['evidence_bundle_digest']; r['return_digest']=c.digest(c.strip_digest(r,'return_digest'))
   with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return(r,p,b,artifact=source,artifact_outputs=[output],artifact_output_root=output.parent)

 def test_artifact_validation_rejects_preexisting_undeclared_output_root_object(self):
  h=sr.SourceReplayGrounding()
  with tempfile.TemporaryDirectory() as td:
   source,output,p,r,b=h.actual_artifact_return(td)
   (output.parent/'PREEXISTING_UNDECLARED.bin').write_bytes(b'extra')
   with self.assertRaises(c.JoyflowError):
    c.validate_codex_execution_return(r,p,b,artifact=source,artifact_outputs=[output],artifact_output_root=output.parent)

 def test_review_cannot_replace_one_source_evidence_row(self):
  h=sr.SourceReplayGrounding()
  with tempfile.TemporaryDirectory() as td:
   source,output,p,r,b=h.actual_artifact_return(td); approved=h._actual_artifact_approved; executing=f.advance(approved,'CODEX_EXECUTION'); fixture=f.brain_review_capsule(executing,p,r,b)
   target_ref=r['artifact_evidence']['outputs'][0]['validation_evidence_refs'][0]; ev=next(x for x in fixture['evidence_registry'] if x['evidence_id']==target_ref); ev['raw_output_ref']='fabricated'; ev['raw_output_sha256']='f'*64
   with self.assertRaises(c.JoyflowError): c.prepare_artifact_review_capsule(fixture,executing,review_projection=p,codex_return=r,evidence_bundle=b,source_artifact=source,artifact_outputs=[output],artifact_output_root=output.parent)

 def test_positive_artifact_review_still_closes(self):
  h=sr.SourceReplayGrounding()
  with tempfile.TemporaryDirectory() as td:
   source,output,p,r,b=h.actual_artifact_return(td); approved=h._actual_artifact_approved; executing=f.advance(approved,'CODEX_EXECUTION'); fixture=f.brain_review_capsule(executing,p,r,b)
   review=c.prepare_artifact_review_capsule(fixture,executing,review_projection=p,codex_return=r,evidence_bundle=b,source_artifact=source,artifact_outputs=[output],artifact_output_root=output.parent)
   self.assertEqual(review['active_fibers']['execution_review']['payload']['source_evidence_row_digests'],c.source_evidence_row_digest_map(b))

if __name__=='__main__': unittest.main()
