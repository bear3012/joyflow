from __future__ import annotations
import copy, hashlib, importlib.util, pathlib, subprocess, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('c',ROOT/'runtime/joyflow_dual_layer.py'); c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
spec2=importlib.util.spec_from_file_location('f',ROOT/'tests/build_fixture.py'); f=importlib.util.module_from_spec(spec2); spec2.loader.exec_module(f)

class StructuralCognitionContinuity(unittest.TestCase):
    def _install_frame(self, projection, *, question_id, statement, basis, dims):
        frame={'owner':'WEB_BRAIN','required':True,'question_id':question_id,'statement':statement,'materiality_basis':basis,'goal_binding_digest':c._structural_goal_binding(projection),'required_dimensions':dims,'protected_product_semantics':['Preserve the current product semantics.'],'non_goals':projection['task_anchor']['non_goals'],'discovery_scope_seed':['runtime/**'],'frame_digest':None}
        frame['frame_digest']=c._structural_frame_digest(frame)
        projection['repository_evidence']['path_discovery']['structural_decision_frame']=frame
        projection['projection_digest']=c.digest(c.strip_digest(projection,'projection_digest'))
        return frame
    def test_goal_conditioned_structural_discovery_closes_only_with_semantic_mapping(self):
        _, projection, _, _ = f.approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY')
        frame=self._install_frame(projection,question_id='Q_EXEC_STATE',statement='Can the current execution-state model absorb the requested change without a second authority?',basis='The task touches shared execution state.',dims=['AUTHORITY_BOUNDARY'])
        ret=f.path_discovery_return(projection)
        source_sha='1'*64
        src={'evidence_id':'DISC_STRUCT_SOURCE','authority':'EXECUTION_EVIDENCE','kind':'SOURCE_SNAPSHOT_OBSERVATION','ref':'raw:source','claim':c._source_snapshot_claim('SRC_RUNTIME','runtime/joyflow_dual_layer.py',source_sha),'claim_digest':None,'produced_by':'TOOL','subject_type':'REPOSITORY_SOURCE_SNAPSHOT','subject_id':'SRC_RUNTIME','observed_path':'runtime/joyflow_dual_layer.py','source_sha256':source_sha,'source_evidence_refs':[],'raw_output_ref':'raw:source','raw_output_sha256':source_sha}
        src['claim_digest']=c.digest(src['claim'])
        relation={'relation_id':'REL_AUTHORITY','relation_type':'AUTHORITY_WRITER','subject':'task execution state','source':'runtime/joyflow_dual_layer.py','semantic_claim':'The current runtime is the mutation boundary for task execution state.','basis_evidence_refs':['DISC_STRUCT_SOURCE'],'materiality':'MATERIAL','evidence_ref':'DISC_STRUCT_REL'}
        rel_ev={'evidence_id':'DISC_STRUCT_REL','authority':'EXECUTION_EVIDENCE','kind':'STRUCTURAL_RELATION_DERIVATION','ref':'DISC_STRUCT_REL','claim':c._local_item_claim('STRUCTURAL_RELATION_DERIVATION',relation),'claim_digest':None,'produced_by':'CODEX','subject_type':'STRUCTURAL_RELATION','subject_id':'REL_AUTHORITY','observed_path':None,'source_sha256':None,'source_evidence_refs':['DISC_STRUCT_SOURCE'],'raw_output_ref':None,'raw_output_sha256':None}
        rel_ev['claim_digest']=c.digest(rel_ev['claim'])
        route={'route_id':'ROUTE_KEEP_EXISTING','summary':'Preserve the current single execution-state mutation boundary and extend it without adding a parallel authority.','advantages':['Preserves existing ownership.'],'known_costs':['Requires bounded edits in the current runtime.'],'known_risks':['Current source may reveal a hidden writer.'],'evidence_refs':['DISC_STRUCT_REL'],'evidence_ref':'DISC_STRUCT_ROUTE'}
        route_ev={'evidence_id':'DISC_STRUCT_ROUTE','authority':'EXECUTION_EVIDENCE','kind':'ARCHITECTURE_ROUTE_DERIVATION','ref':'DISC_STRUCT_ROUTE','claim':c._local_item_claim('ARCHITECTURE_ROUTE_DERIVATION',route),'claim_digest':None,'produced_by':'CODEX','subject_type':'ARCHITECTURE_ROUTE','subject_id':'ROUTE_KEEP_EXISTING','observed_path':None,'source_sha256':None,'source_evidence_refs':['DISC_STRUCT_REL'],'raw_output_ref':None,'raw_output_sha256':None}
        route_ev['claim_digest']=c.digest(route_ev['claim'])
        ret['evidence_rows'] += [src,rel_ev,route_ev]
        ret['structural_discovery']={
            'mode':'GOAL_CONDITIONED',
            'architecture_question':{'question_id':'Q_EXEC_STATE','statement':'Can the current execution-state model absorb the requested change without a second authority?','materiality_basis':'The task touches shared execution state.','goal_binding_digest':c._structural_goal_binding(projection),'closure_dimensions':['AUTHORITY_BOUNDARY'],'frame_digest':frame['frame_digest']},
            'semantic_relations':[relation],
            'closure_obligations':[{'dimension':'AUTHORITY_BOUNDARY','status':'CHECKED','evidence_refs':['DISC_STRUCT_REL'],'unresolved_reason':None,'applicability_basis':None}],
            'counterevidence_refs':[],
            'unresolved_structural_questions':[],
            'omitted_material_summary':['Read-only consumers are not expanded because the current question is authority ownership.'],
            'candidate_routes':[route],
            'recommended_route_id':'ROUTE_KEEP_EXISTING',
            'task_structural_projection':{'status':'CLOSED','material_relation_ids':['REL_AUTHORITY'],'counterevidence_refs':[],'unresolved_questions':[],'omitted_material_summary':['Read-only consumers are not expanded because the current question is authority ownership.']},
        }
        ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
        c.validate_path_discovery_return_structure(ret,projection)

        bad=copy.deepcopy(ret); bad['structural_discovery']['task_structural_projection']['material_relation_ids']=[]; bad['return_digest']=c.digest(c.strip_digest(bad,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return_structure(bad,projection)

        bad=copy.deepcopy(ret); bad['structural_discovery']['closure_obligations'][0].update({'status':'UNRESOLVED','unresolved_reason':'Hidden runtime writer not yet checked.'}); bad['structural_discovery']['unresolved_structural_questions']=['Hidden runtime writer not yet checked.']; bad['structural_discovery']['task_structural_projection'].update({'status':'INCOMPLETE','unresolved_questions':['Hidden runtime writer not yet checked.']}); bad['return_digest']=c.digest(c.strip_digest(bad,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return_structure(bad,projection)

        bad=copy.deepcopy(ret); bad['structural_discovery']['architecture_question']['goal_binding_digest']='0'*64; bad['return_digest']=c.digest(c.strip_digest(bad,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return_structure(bad,projection)


    def test_structural_source_snapshot_is_replayed_against_current_repository(self):
        from tests.test_phase1_source_replay_grounding import SourceReplayGrounding
        helper=SourceReplayGrounding()
        with tempfile.TemporaryDirectory() as td:
            repo,base,_=helper.repo(td,second_commit=False); projection,ret=helper.actualize_discovery(repo,base)
            frame=self._install_frame(projection,question_id='Q_RUNTIME',statement='Is the current runtime a shared structural surface for this change?',basis='Runtime structure affects several task contracts.',dims=['SHARED_CORE'])
            ret['projection_digest']=projection['projection_digest']
            data=subprocess.check_output(['git','-C',str(repo),'show',f'{base}:runtime/joyflow_dual_layer.py']); sha=hashlib.sha256(data).hexdigest()
            src={'evidence_id':'DISC_STRUCT_SOURCE','authority':'EXECUTION_EVIDENCE','kind':'SOURCE_SNAPSHOT_OBSERVATION','ref':'raw:git-show-runtime','claim':c._source_snapshot_claim('SRC_RUNTIME','runtime/joyflow_dual_layer.py',sha),'claim_digest':None,'produced_by':'TOOL','subject_type':'REPOSITORY_SOURCE_SNAPSHOT','subject_id':'SRC_RUNTIME','observed_path':'runtime/joyflow_dual_layer.py','source_sha256':sha,'source_evidence_refs':[],'raw_output_ref':'raw:git-show-runtime','raw_output_sha256':sha}; src['claim_digest']=c.digest(src['claim'])
            rel={'relation_id':'REL_RUNTIME','relation_type':'SHARED_CORE','subject':'runtime compiler','source':'runtime/joyflow_dual_layer.py','semantic_claim':'The runtime is a shared mechanical surface for the current architecture question.','basis_evidence_refs':['DISC_STRUCT_SOURCE'],'materiality':'MATERIAL','evidence_ref':'DISC_STRUCT_REL'}
            rel_ev={'evidence_id':'DISC_STRUCT_REL','authority':'EXECUTION_EVIDENCE','kind':'STRUCTURAL_RELATION_DERIVATION','ref':'DISC_STRUCT_REL','claim':c._local_item_claim('STRUCTURAL_RELATION_DERIVATION',rel),'claim_digest':None,'produced_by':'CODEX','subject_type':'STRUCTURAL_RELATION','subject_id':'REL_RUNTIME','observed_path':None,'source_sha256':None,'source_evidence_refs':['DISC_STRUCT_SOURCE'],'raw_output_ref':None,'raw_output_sha256':None}; rel_ev['claim_digest']=c.digest(rel_ev['claim'])
            ret['evidence_rows'] += [src,rel_ev]
            ret['structural_discovery']={'mode':'GOAL_CONDITIONED','architecture_question':{'question_id':'Q_RUNTIME','statement':'Is the current runtime a shared structural surface for this change?','materiality_basis':'Runtime structure affects several task contracts.','goal_binding_digest':c._structural_goal_binding(projection),'closure_dimensions':['SHARED_CORE'],'frame_digest':frame['frame_digest']},'semantic_relations':[rel],'closure_obligations':[{'dimension':'SHARED_CORE','status':'CHECKED','evidence_refs':['DISC_STRUCT_REL'],'unresolved_reason':None,'applicability_basis':None}],'counterevidence_refs':[],'unresolved_structural_questions':[],'omitted_material_summary':[],'candidate_routes':[],'recommended_route_id':None,'task_structural_projection':{'status':'CLOSED','material_relation_ids':['REL_RUNTIME'],'counterevidence_refs':[],'unresolved_questions':[],'omitted_material_summary':[]}}
            ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
            c.validate_path_discovery_return(ret,projection,repository=repo)
            bad=copy.deepcopy(ret); ev=next(x for x in bad['evidence_rows'] if x['evidence_id']=='DISC_STRUCT_SOURCE'); ev['source_sha256']='f'*64; ev['raw_output_sha256']='f'*64; ev['claim']=c._source_snapshot_claim(ev['subject_id'],ev['observed_path'],ev['source_sha256']); ev['claim_digest']=c.digest(ev['claim']); bad['return_digest']=c.digest(c.strip_digest(bad,'return_digest'))
            with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return(bad,projection,repository=repo)

    def test_non_structural_discovery_cannot_smuggle_structural_conclusions(self):
        _, projection, _, _ = f.approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY')
        ret=f.path_discovery_return(projection)
        ret['structural_discovery']['omitted_material_summary']=['hidden architecture claim']
        ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return_structure(ret,projection)

    def _repo(self,td):
        repo=pathlib.Path(td)/'repo'; repo.mkdir()
        subprocess.run(['git','init',str(repo)],check=True,capture_output=True)
        subprocess.run(['git','-C',str(repo),'config','user.email','joyflow@example.invalid'],check=True)
        subprocess.run(['git','-C',str(repo),'config','user.name','Joyflow Test'],check=True)
        subprocess.run(['git','-C',str(repo),'remote','add','origin','https://github.com/example/structural.git'],check=True)
        (repo/'domain').mkdir(); (repo/'domain/order.py').write_text('ORDER_OWNER = "OrderState"\n'); (repo/'domain/payment.py').write_text('PAYMENT_CONSUMER = True\n')
        subprocess.run(['git','-C',str(repo),'add','.'],check=True); subprocess.run(['git','-C',str(repo),'commit','-m','base'],check=True,capture_output=True)
        base=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
        return repo,base

    def _projection(self,repo,base):
        def ref(path):
            data=subprocess.check_output(['git','-C',str(repo),'show',f'{base}:{path}'])
            return {'path':path,'source_sha256':hashlib.sha256(data).hexdigest()}
        row={'artifact_type':'LONG_TERM_STRUCTURAL_PROJECTION','projection_version':1,'artifact_role':'DERIVED_NON_AUTHORITATIVE_STRUCTURAL_NAVIGATION','repository_id':'example/structural','based_on_commit':base,'scope':{'statement':'Reviewed order/payment structural surface only.','covered_surfaces':['order-state','payment-consumer']},'coverage_basis':{'source_structural_closure_digest':'a'*64,'source_review_ref':'BRAIN_REVIEW_TEST'},
             'structural_anchors':[{'anchor_id':'A_ORDER','anchor_type':'AUTHORITY_BOUNDARY','statement':'OrderState is the reviewed order-state authority boundary at the based-on commit.','epistemic_status':'INFERRED','source_refs':[ref('domain/order.py')]},{'anchor_id':'A_PAYMENT','anchor_type':'LIFECYCLE','statement':'Payment consumes order lifecycle state.','epistemic_status':'INFERRED','source_refs':[ref('domain/payment.py')]}],
             'semantic_fibers':[{'fiber_id':'F_PAYMENT_CONSUMES_ORDER','fiber_type':'CONSUMES','from_anchor':'A_PAYMENT','to_anchor':'A_ORDER','statement':'Payment consumes the reviewed order-state boundary.','epistemic_status':'INFERRED','source_refs':[ref('domain/order.py'),ref('domain/payment.py')]}],
             'counterevidence_refs':[],'unresolved':[],'material_omissions':['Function-level implementation details are intentionally omitted.'],'projection_digest':None}
        row['projection_digest']=c.digest(c.strip_digest(row,'projection_digest')); return row

    def test_long_term_projection_is_derived_commit_anchored_and_stales_on_relevant_change(self):
        with tempfile.TemporaryDirectory() as td:
            repo,base=self._repo(td); row=self._projection(repo,base)
            self.assertEqual(c.validate_long_term_structural_projection(row,repository=repo)['freshness'],'CURRENT_AT_HEAD')
            (repo/'README.md').write_text('unrelated\n'); subprocess.run(['git','-C',str(repo),'add','.'],check=True); subprocess.run(['git','-C',str(repo),'commit','-m','unrelated'],check=True,capture_output=True)
            self.assertEqual(c.validate_long_term_structural_projection(row,repository=repo)['freshness'],'CURRENT_FOR_REFERENCED_BASIS')
            (repo/'domain/order.py').write_text('ORDER_OWNER = "OtherState"\n'); subprocess.run(['git','-C',str(repo),'add','.'],check=True); subprocess.run(['git','-C',str(repo),'commit','-m','structural-change'],check=True,capture_output=True)
            result=c.validate_long_term_structural_projection(row,repository=repo)
            self.assertEqual(result['freshness'],'STALE_RELEVANT_SOURCE_CHANGED'); self.assertIn('domain/order.py',result['changed_relevant_sources'])
            bad=copy.deepcopy(row); bad['structural_anchors'][0]['source_refs'][0]['source_sha256']='f'*64; bad['projection_digest']=c.digest(c.strip_digest(bad,'projection_digest'))
            with self.assertRaises(c.JoyflowError): c.validate_long_term_structural_projection(bad,repository=repo)

if __name__=='__main__': unittest.main()
