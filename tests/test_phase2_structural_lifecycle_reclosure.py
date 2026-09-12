from __future__ import annotations
import copy, importlib.util, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('c',ROOT/'runtime/joyflow_dual_layer.py'); c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
spec2=importlib.util.spec_from_file_location('f',ROOT/'tests/build_fixture.py'); f=importlib.util.module_from_spec(spec2); spec2.loader.exec_module(f)

class StructuralLifecycleReclosure(unittest.TestCase):
    def frame(self, projection, dims=('AUTHORITY_BOUNDARY',)):
        fr={'owner':'WEB_BRAIN','required':True,'question_id':'Q_OWNER','statement':'Which current repository boundary owns the reviewed state?','materiality_basis':'A material architecture uncertainty affects shared state ownership.','goal_binding_digest':c._structural_goal_binding(projection),'required_dimensions':list(dims),'protected_product_semantics':['Preserve current product behavior.'],'non_goals':projection['task_anchor']['non_goals'],'discovery_scope_seed':['runtime/**'],'frame_digest':None}; fr['frame_digest']=c._structural_frame_digest(fr)
        projection['repository_evidence']['path_discovery']['structural_decision_frame']=fr; projection['projection_digest']=c.digest(c.strip_digest(projection,'projection_digest')); return fr
    def structural_return(self):
        _,projection,_,_=f.approved_capsule('READ_ONLY_DISCOVERY','READ_ONLY'); fr=self.frame(projection); ret=f.path_discovery_return(projection)
        sha='1'*64
        src={'evidence_id':'SRC','authority':'EXECUTION_EVIDENCE','kind':'SOURCE_SNAPSHOT_OBSERVATION','ref':'raw:src','claim':c._source_snapshot_claim('SRCID','runtime/joyflow_dual_layer.py',sha),'claim_digest':None,'produced_by':'TOOL','subject_type':'REPOSITORY_SOURCE_SNAPSHOT','subject_id':'SRCID','observed_path':'runtime/joyflow_dual_layer.py','source_sha256':sha,'source_evidence_refs':[],'raw_output_ref':'raw:src','raw_output_sha256':sha}; src['claim_digest']=c.digest(src['claim'])
        rel={'relation_id':'REL','relation_type':'AUTHORITY_WRITER','subject':'task state','source':'runtime/joyflow_dual_layer.py','semantic_claim':'The reviewed runtime source contains the current task-state writer boundary.','basis_evidence_refs':['SRC'],'materiality':'MATERIAL','evidence_ref':'REL_EV'}
        rev={'evidence_id':'REL_EV','authority':'EXECUTION_EVIDENCE','kind':'STRUCTURAL_RELATION_DERIVATION','ref':'REL_EV','claim':c._local_item_claim('STRUCTURAL_RELATION_DERIVATION',rel),'claim_digest':None,'produced_by':'CODEX','subject_type':'STRUCTURAL_RELATION','subject_id':'REL','observed_path':None,'source_sha256':None,'source_evidence_refs':['SRC'],'raw_output_ref':None,'raw_output_sha256':None}; rev['claim_digest']=c.digest(rev['claim'])
        route={'route_id':'ROUTE_A','summary':'Preserve the existing writer boundary.','advantages':['No parallel authority.'],'known_costs':[],'known_risks':['Hidden runtime writer remains a discovery risk.'],'evidence_refs':['REL_EV'],'evidence_ref':'ROUTE_EV'}
        route_ev={'evidence_id':'ROUTE_EV','authority':'EXECUTION_EVIDENCE','kind':'ARCHITECTURE_ROUTE_DERIVATION','ref':'ROUTE_EV','claim':c._local_item_claim('ARCHITECTURE_ROUTE_DERIVATION',route),'claim_digest':None,'produced_by':'CODEX','subject_type':'ARCHITECTURE_ROUTE','subject_id':'ROUTE_A','observed_path':None,'source_sha256':None,'source_evidence_refs':['REL_EV'],'raw_output_ref':None,'raw_output_sha256':None}; route_ev['claim_digest']=c.digest(route_ev['claim'])
        ret['evidence_rows'] += [src,rev,route_ev]
        ret['structural_discovery']={'mode':'GOAL_CONDITIONED','architecture_question':{'question_id':fr['question_id'],'statement':fr['statement'],'materiality_basis':fr['materiality_basis'],'goal_binding_digest':fr['goal_binding_digest'],'closure_dimensions':fr['required_dimensions'],'frame_digest':fr['frame_digest']},'semantic_relations':[rel],'closure_obligations':[{'dimension':'AUTHORITY_BOUNDARY','status':'CHECKED','evidence_refs':['REL_EV'],'unresolved_reason':None,'applicability_basis':None}],'counterevidence_refs':[],'unresolved_structural_questions':[],'omitted_material_summary':[],'candidate_routes':[route],'recommended_route_id':'ROUTE_A','task_structural_projection':{'status':'CLOSED','material_relation_ids':['REL'],'counterevidence_refs':[],'unresolved_questions':[],'omitted_material_summary':[]}}
        ret['return_digest']=c.digest(c.strip_digest(ret,'return_digest')); return projection,ret
    def test_brain_question_cannot_be_rewritten_or_downgraded(self):
        p,r=self.structural_return(); c.validate_path_discovery_return_structure(r,p)
        bad=copy.deepcopy(r); bad['structural_discovery']['architecture_question']['closure_dimensions']=['DEPENDENCY']; bad['return_digest']=c.digest(c.strip_digest(bad,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return_structure(bad,p)
        bad=copy.deepcopy(r); bad['structural_discovery']={'mode':'NOT_APPLICABLE','architecture_question':None,'semantic_relations':[],'closure_obligations':[],'counterevidence_refs':[],'unresolved_structural_questions':[],'omitted_material_summary':[],'candidate_routes':[],'recommended_route_id':None,'task_structural_projection':{'status':'NOT_APPLICABLE','material_relation_ids':[],'counterevidence_refs':[],'unresolved_questions':[],'omitted_material_summary':[]}}; bad['return_digest']=c.digest(c.strip_digest(bad,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return_structure(bad,p)
    def test_checked_and_not_applicable_require_real_basis(self):
        p,r=self.structural_return()
        bad=copy.deepcopy(r); bad['structural_discovery']['closure_obligations'][0]['evidence_refs']=[]; bad['return_digest']=c.digest(c.strip_digest(bad,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return_structure(bad,p)
        bad=copy.deepcopy(r); row=bad['structural_discovery']['closure_obligations'][0]; row.update({'status':'NOT_APPLICABLE','evidence_refs':[],'applicability_basis':None}); bad['structural_discovery']['semantic_relations']=[]; bad['structural_discovery']['candidate_routes']=[]; bad['structural_discovery']['recommended_route_id']=None; bad['structural_discovery']['task_structural_projection']['material_relation_ids']=[]; bad['return_digest']=c.digest(c.strip_digest(bad,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return_structure(bad,p)
    def test_path_observation_cannot_prove_authority(self):
        p,r=self.structural_return(); bad=copy.deepcopy(r)
        # replace relation source basis with ordinary path observation from the base fixture
        path_ev=next(x for x in bad['evidence_rows'] if x['kind']=='PATH_OBSERVATION')
        rel=bad['structural_discovery']['semantic_relations'][0]; rel['basis_evidence_refs']=[path_ev['evidence_id']]
        rev=next(x for x in bad['evidence_rows'] if x['evidence_id']=='REL_EV'); rev['source_evidence_refs']=[path_ev['evidence_id']]; rev['claim']=c._local_item_claim('STRUCTURAL_RELATION_DERIVATION',rel); rev['claim_digest']=c.digest(rev['claim']); bad['return_digest']=c.digest(c.strip_digest(bad,'return_digest'))
        with self.assertRaises(c.JoyflowError): c.validate_path_discovery_return_structure(bad,p)

    def test_structural_frame_blocks_ordinary_final_path_until_closed(self):
        cap=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE')
        proj={'task_anchor':cap['task_anchor']}
        fr={'owner':'WEB_BRAIN','required':True,'question_id':'Q_OWNER','statement':'Which current repository boundary owns the reviewed state?','materiality_basis':'A material architecture uncertainty affects shared state ownership.','goal_binding_digest':c._structural_goal_binding(proj),'required_dimensions':['AUTHORITY_BOUNDARY'],'protected_product_semantics':['Preserve current product behavior.'],'non_goals':cap['task_anchor']['non_goals'],'discovery_scope_seed':['runtime/**'],'frame_digest':None}
        fr['frame_digest']=c._structural_frame_digest(fr)
        cap['active_fibers']['repository_evidence']['payload']['path_discovery']['structural_decision_frame']=fr
        with self.assertRaises(c.JoyflowError): c.prepare_capsule_structural_fixture(cap)

    def test_ordinary_review_cannot_invent_structural_consequence(self):
        _,_,_,_,_,review,_=f.full_repository_review_chain()
        bad=copy.deepcopy(review)
        sr=bad['active_fibers']['execution_review']['payload']['structural_review']
        sr.update({'status':'PRESERVED','approved_closure_digest':'a'*64,'actual_consequence_ids':['C1'],'dispositions':[{'consequence_id':'C1','result':'PRESERVED','review_basis':'invented'}]})
        bad=f.refresh(bad)
        with self.assertRaises(c.JoyflowError): c.validate_execution_review(bad)

