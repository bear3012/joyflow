from __future__ import annotations
import copy, json, pathlib, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runtime import joyflow_dual_layer as c
try:
    import build_fixture as f
    import test_phase1_source_replay_grounding as replay
except ModuleNotFoundError:
    from tests import build_fixture as f
    from tests import test_phase1_source_replay_grounding as replay

class TaskObjectLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.h=replay.SourceReplayGrounding()

    def write_json(self,path,obj):
        pathlib.Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')

    def test_projection_carries_typed_route_lifecycle(self):
        _,repo,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        _,disc,_,_=f.approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY')
        _,art,_,_=f.approved_capsule('ARTIFACT_REPAIR','ARTIFACT_CHANGE')
        self.assertEqual(c._route_type(repo),'REPOSITORY_CHANGE')
        self.assertEqual(c._route_type(disc),'REPOSITORY_DISCOVERY')
        self.assertEqual(c._route_type(art),'ARTIFACT_REPAIR')
        for p in (repo,disc,art):
            self.assertEqual(set(p['task_object_lifecycle']),{'lifecycle_version','input_binding_digest','discovery_binding_digest','authorization_envelope_digest','lifecycle_digest'})
            c.validate_task_object_lifecycle(p)

    def divergent_repo(self,td):
        repo=pathlib.Path(td)/'repo'; repo.mkdir()
        subprocess.run(['git','init',str(repo)],check=True,capture_output=True)
        subprocess.run(['git','-C',str(repo),'config','user.email','joyflow@example.invalid'],check=True)
        subprocess.run(['git','-C',str(repo),'config','user.name','Joyflow Test'],check=True)
        subprocess.run(['git','-C',str(repo),'remote','add','origin','https://github.com/example/repo.git'],check=True)
        for rel,text in {'runtime/joyflow_dual_layer.py':'VALUE = 1\n','machine/joyflow_dual_layer_model.yaml':'model: 1\n','tests/test_phase1_single_active_task_round.py':'import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n'}.items():
            p=repo/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)
        subprocess.run(['git','-C',str(repo),'add','.'],check=True); subprocess.run(['git','-C',str(repo),'commit','-m','root'],check=True,capture_output=True)
        root=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
        subprocess.run(['git','-C',str(repo),'checkout','-b','approved'],check=True,capture_output=True)
        (repo/'runtime/joyflow_dual_layer.py').write_text('VALUE = 2\n'); subprocess.run(['git','-C',str(repo),'add','.'],check=True); subprocess.run(['git','-C',str(repo),'commit','-m','approved'],check=True,capture_output=True)
        base=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
        subprocess.run(['git','-C',str(repo),'checkout','-b','result',root],check=True,capture_output=True)
        (repo/'runtime/joyflow_dual_layer.py').write_text('VALUE = 3\n'); subprocess.run(['git','-C',str(repo),'add','.'],check=True); subprocess.run(['git','-C',str(repo),'commit','-m','result'],check=True,capture_output=True)
        head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
        return repo,base,head

    def test_divergent_base_and_result_head_are_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            repo,base,head=self.divergent_repo(td)
            p,r,b=self.h.real_return(repo,base,head)
            with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return(r,p,b,repository=repo)

    def test_final_validation_runs_on_exact_result_head(self):
        with tempfile.TemporaryDirectory() as td:
            repo=pathlib.Path(td)/'repo'; repo.mkdir()
            subprocess.run(['git','init',str(repo)],check=True,capture_output=True)
            subprocess.run(['git','-C',str(repo),'config','user.email','joyflow@example.invalid'],check=True); subprocess.run(['git','-C',str(repo),'config','user.name','Joyflow Test'],check=True); subprocess.run(['git','-C',str(repo),'remote','add','origin','https://github.com/example/repo.git'],check=True)
            (repo/'runtime').mkdir(); (repo/'tests').mkdir(); (repo/'machine').mkdir()
            (repo/'runtime/joyflow_dual_layer.py').write_text('VALUE = 1\n')
            (repo/'machine/joyflow_dual_layer_model.yaml').write_text('model: 1\n')
            (repo/'tests/test_phase1_single_active_task_round.py').write_text("import pathlib,unittest\nclass T(unittest.TestCase):\n def test_value(self): self.assertIn('VALUE = 1',pathlib.Path('runtime/joyflow_dual_layer.py').read_text())\n")
            subprocess.run(['git','-C',str(repo),'add','.'],check=True); subprocess.run(['git','-C',str(repo),'commit','-m','base'],check=True,capture_output=True)
            base=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
            (repo/'runtime/joyflow_dual_layer.py').write_text('VALUE = 2\n'); subprocess.run(['git','-C',str(repo),'add','.'],check=True); subprocess.run(['git','-C',str(repo),'commit','-m','break'],check=True,capture_output=True)
            head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
            subprocess.run(['git','-C',str(repo),'checkout','--detach',base],check=True,capture_output=True)
            _,projection,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
            check=projection['validation']['checks'][0]
            check['argv']=['python','-c',"import pathlib; assert 'VALUE = 1' in pathlib.Path('runtime/joyflow_dual_layer.py').read_text()"]
            check['command']=c._canonical_argv(check['argv'])
            projection=self.h.refresh_lifecycle(projection)
            p,r,b=self.h.real_return(repo,base,head,projection)
            # The helper records the actual failing result-head execution. It must not be accepted as completed PASS.
            with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return(r,p,b,repository=repo)

    def test_typed_recursive_ignored_directory_detects_internal_change(self):
        with tempfile.TemporaryDirectory() as td:
            repo,_,_=self.h.repo(td,second_commit=False)
            (repo/'.gitignore').write_text('local-fixtures/\n'); subprocess.run(['git','-C',str(repo),'add','.gitignore'],check=True); subprocess.run(['git','-C',str(repo),'commit','-m','ignore'],check=True,capture_output=True)
            d=repo/'local-fixtures'; d.mkdir(); (d/'a.cfg').write_text('A\n')
            coverage={'mode':'DECLARED_EXECUTION_RELEVANT_ONLY','exact_files':[],'exact_symlinks':[],'recursive_directories':[{'root':'local-fixtures','exclusions':[]}],'coverage_status':'COMPLETE_FOR_DECLARED_EXECUTION_RELEVANT_PATHS','full_local_filesystem_unchanged_claim':False}
            before=c._source_worktree_components(repo,coverage); (d/'a.cfg').write_text('B\n'); after=c._source_worktree_components(repo,coverage)
            self.assertNotEqual(before['declared_ignored_manifest_sha256'],after['declared_ignored_manifest_sha256'])
            bad=copy.deepcopy(coverage); bad['recursive_directories']=[]; bad['exact_files']=['local-fixtures']
            with self.assertRaises(c.JoyflowError): c._source_worktree_components(repo,bad)

    def test_repository_dedicated_review_entry_passes_exact_chain(self):
        with tempfile.TemporaryDirectory() as td:
            repo,base,head=self.h.repo(td); approved,p=self.h.actual_approved_capsule(base,repo); p,r,b=self.h.real_return(repo,base,head,p)
            executing=f.advance(approved,'CODEX_EXECUTION'); fixture_review=f.brain_review_capsule(executing,p,r,b)
            review=c.prepare_repository_review_capsule(fixture_review,executing,review_projection=p,codex_return=r,evidence_bundle=b,source_repository=repo)
            self.assertEqual(review['active_fibers']['execution_review']['payload']['review_target']['head_sha'],head)

    def test_artifact_dedicated_review_entry_passes_exact_output_set(self):
        with tempfile.TemporaryDirectory() as td:
            source,output,p,r,b=self.h.actual_artifact_return(td); approved=self.h._actual_artifact_approved
            executing=f.advance(approved,'CODEX_EXECUTION'); fixture_review=f.brain_review_capsule(executing,p,r,b)
            review=c.prepare_artifact_review_capsule(fixture_review,executing,review_projection=p,codex_return=r,evidence_bundle=b,source_artifact=source,artifact_outputs=[output],artifact_output_root=output.parent)
            target=review['active_fibers']['execution_review']['payload']['review_target']
            self.assertEqual(target['target_type'],'ARTIFACT_OUTPUT_SET'); self.assertEqual(target['outputs'][0]['artifact_id'],output.name)

    def test_artifact_review_missing_output_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            source,output,p,r,b=self.h.actual_artifact_return(td); approved=self.h._actual_artifact_approved
            executing=f.advance(approved,'CODEX_EXECUTION'); fixture_review=f.brain_review_capsule(executing,p,r,b)
            with self.assertRaises(c.JoyflowError): c.prepare_artifact_review_capsule(fixture_review,executing,review_projection=p,codex_return=r,evidence_bundle=b,source_artifact=source,artifact_outputs=[],artifact_output_root=output.parent)

    def test_artifact_review_cli_carries_output_set(self):
        with tempfile.TemporaryDirectory() as td:
            source,output,p,r,b=self.h.actual_artifact_return(td); approved=self.h._actual_artifact_approved
            executing=f.advance(approved,'CODEX_EXECUTION'); fixture_review=f.brain_review_capsule(executing,p,r,b)
            paths={name:pathlib.Path(td)/name for name in ('input.json','previous.json','projection.json','return.json','bundle.json','review.json')}
            for name,obj in [('input.json',fixture_review),('previous.json',executing),('projection.json',p),('return.json',r),('bundle.json',b)]: self.write_json(paths[name],obj)
            proc=subprocess.run([sys.executable,str(ROOT/'runtime/joyflow_dual_layer.py'),'seal-artifact-review',str(paths['input.json']),str(paths['review.json']),'--previous',str(paths['previous.json']),'--projection',str(paths['projection.json']),'--codex-return',str(paths['return.json']),'--evidence-bundle',str(paths['bundle.json']),'--source-artifact',str(source),'--artifact-output',str(output),'--artifact-output-root',str(output.parent)],capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stderr); review=json.loads(paths['review.json'].read_text(encoding="utf-8")); self.assertEqual(review['active_fibers']['execution_review']['payload']['review_target']['target_type'],'ARTIFACT_OUTPUT_SET')

    def test_later_review_cannot_change_lifecycle_source_digest(self):
        approved,p,_,_=f.approved_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE'); executing=f.advance(approved,'CODEX_EXECUTION'); r,b=f.codex_return(p); review=f.brain_review_capsule(executing,p,r,b)
        tampered=copy.deepcopy(review); payload=tampered['active_fibers']['execution_review']['payload']; payload['source_execution_lifecycle_result_digest']='f'*64; payload['source_snapshot_digest']=c.source_derived_review_snapshot_digest(payload); tampered['active_fibers']['execution_review']['fiber_digest']=None; tampered['capsule_digest']=None; tampered['derived_gates']={}
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(tampered,review)

if __name__=='__main__': unittest.main()
