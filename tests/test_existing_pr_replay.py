from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import subprocess
import tempfile
import unittest

from tests import build_fixture as f
from tests import phase1_review_fixture as fx
from tools import joyflow_repo_check as repo_check

c = f.c
review = fx.review


class ExistingPRReplayTests(unittest.TestCase):
    def setUp(self):
        self.holder, self.repo, self.base, self.head = fx.create_repository()

    def tearDown(self):
        self.holder.cleanup()

    def replay_chain(self):
        approved, projection, _, _ = fx.repository_replay_approved_projection(self.repo, self.base, self.head)
        ret, bundle = fx.repository_return_bundle(projection, self.repo, self.base, self.head)
        self.normalize_physical_captures(ret, bundle)
        return approved, projection, ret, bundle

    def local_approved_projection(self):
        base=self.head
        state=f.new_capsule('DEVELOPMENT_STANDARD','REPOSITORY_CHANGE','NONE')
        state['task_anchor']['repository_anchor']['baseline_commit']=base
        repo_payload=state['active_fibers']['repository_evidence']['payload']; repo_payload['baseline_commit']=base
        final=repo_payload['path_discovery']['final_path_decision']; final['baseline_commit']=base; final['decision_digest']=c.digest(c.strip_digest(final,'decision_digest'))
        state['active_fibers']['decision_boundary']['payload']['repository_binding']['expected_base_commit']=base
        fx._patch_github_evidence(state,self.repo,base)
        state=f.refresh(state); current=c.prepare_capsule_structural_fixture(state)
        if current['task_progress']['stage'] in {'INTENT_DISCUSSION','REPOSITORY_DISCOVERY'}: current=f.advance(current,'DECISION_CLOSURE')
        if current['task_progress']['stage']!='USER_APPROVAL': current=f.advance(current,'USER_APPROVAL')
        projection,_,binding=c.draft_handoff(current); approved=copy.deepcopy(current)
        approved['approval_record']={'status':'APPROVED_FINAL','owner':'WEB_BRAIN','scope':c.expected_approval_scope(approved),'basis':'CURRENT_EXPLICIT_USER_DECISION','decision_ref':'conversation:local-result-test-approval','binding':binding}
        approved['derived_gates']=c.compute_gate_snapshot(approved); c.validate_capsule(approved); projection,_=c.compile_handoff(approved)
        return approved,projection

    def local_chain(self, ignored_paths=None):
        approved,projection=self.local_approved_projection()
        before=c._repository_source_state_observation(self.repo,'BEFORE',ignored_paths or [])
        (self.repo/'runtime/joyflow_dual_layer.py').write_text("print('local result')\n",encoding='utf-8')
        ret,bundle=f.local_repository_return_bundle(projection,self.repo,before)
        executing=f.advance(approved,'CODEX_EXECUTION')
        return approved,projection,ret,bundle,executing

    def ignored_local_chain(self):
        (self.repo/'.gitignore').write_text('ignored-local.txt\n',encoding='utf-8')
        fx.git(self.repo,'add','.gitignore'); fx.git(self.repo,'commit','-qm','ignored-base'); self.head=fx.git(self.repo,'rev-parse','HEAD')
        (self.repo/'ignored-local.txt').write_bytes(b'sealed ignored object\n')
        self.assertEqual(fx.git(self.repo,'check-ignore','ignored-local.txt'),'ignored-local.txt')
        return self.local_chain(['ignored-local.txt'])

    def operational_local_review(self):
        approved,projection,ret,bundle,executing=self.local_chain()
        draft=f.brain_review_capsule(executing,projection,ret,bundle)
        reviewing=c.prepare_repository_review_capsule(draft,executing,review_projection=projection,codex_return=ret,evidence_bundle=bundle,source_repository=self.repo)
        return approved,projection,ret,bundle,executing,reviewing

    @staticmethod
    def normalize_physical_captures(ret, bundle):
        for capture in bundle["raw_captures"]:
            obj = capture["observed_object"]
            if "ref_or_sha256" in obj:
                obj["digest"] = obj.pop("ref_or_sha256")
            if "object_type" in obj:
                obj["kind"] = "REPOSITORY_COMMIT" if obj.pop("object_type") == "REPOSITORY" else "ARTIFACT"
            obj.pop("source_mode", None)
            capture["capture_sha256"] = c.digest(c._execution_capture_payload(capture))
        captures = {row["capture_id"]: row for row in bundle["raw_captures"]}
        for evidence in bundle["evidence_rows"]:
            capture = captures[evidence["raw_output_ref"]]
            evidence["claim"] = c._direct_capture_claim(capture)
            evidence["claim_digest"] = c.digest(evidence["claim"])
            evidence["raw_output_sha256"] = capture["capture_sha256"]
        ExistingPRReplayTests.reseal_return(ret, bundle)

    @staticmethod
    def current_review_plan():
        return {
            "mode": "GITHUB_EXACT_OBJECT_IF_NEEDED",
            "transport_role": "CURRENT_PR_REVIEW_INPUT_TRANSPORT",
            "github_surface": {
                "repository_id": "example/repo",
                "temporary_ref": "refs/heads/joyflow-evidence/current-review/round-1",
                "path_prefix": "current-review/round-1/",
                "side_effect_status": "NONE",
                "side_effect_basis": "Synthetic transport has no product side effect.",
            },
            "retention_policy": "EPHEMERAL_BY_DEFAULT",
            "retention_reason": None,
            "cleanup": {"trigger": "TASK_TERMINAL", "action": "DELETE_EXACT_TEMPORARY_REF", "preauthorized": True, "background_service_forbidden": True},
            "fallback_mode": "MANUAL_FALLBACK",
            "product_pr_promotion_forbidden": True,
            "product_main_or_development_branch_forbidden": True,
        }

    @staticmethod
    def reseal_return(ret, bundle):
        bundle["evidence_bundle_digest"] = c.digest(c.strip_digest(bundle, "evidence_bundle_digest"))
        ret["evidence_bundle_digest"] = bundle["evidence_bundle_digest"]
        ret["execution_lifecycle_result"]["result_binding_digest"] = c._route_result_binding_digest(ret)
        ret["execution_lifecycle_result"]["validation_binding_digest"] = c._validation_binding_digest(ret)
        ret["execution_lifecycle_result"]["transition_digest"] = c.execution_lifecycle_result_digest(ret["execution_lifecycle_result"])
        ret["return_digest"] = c.digest(c.strip_digest(ret, "return_digest"))

    def test_case_a_happy_path_and_truthfulness_guards(self):
        approved, projection, _, _ = fx.repository_approved_projection(self.repo, self.base)
        ret, bundle = fx.repository_return_bundle(projection, self.repo, self.base, self.head)
        self.normalize_physical_captures(ret, bundle)
        c.validate_codex_execution_return(ret, projection, bundle, repository=self.repo)

        bad = copy.deepcopy(ret)
        bad["mutation_summary"]["mutation_performed"] = False
        bad["return_digest"] = c.digest(c.strip_digest(bad, "return_digest"))
        with self.assertRaises(c.JoyflowError):
            c.validate_codex_execution_return_structure(bad, projection, bundle)

        bad = copy.deepcopy(ret); bad_bundle=copy.deepcopy(bundle)
        cap=next(x for x in bad_bundle["raw_captures"] if x["capture_kind"]=="REPOSITORY_DIFF"); cap["observation"]["changed_paths"]=["other/substituted.py"]; cap["capture_sha256"]=c.digest(c._execution_capture_payload(cap))
        ev=next(x for x in bad_bundle["evidence_rows"] if x["evidence_id"]==bad["pr_evidence"]["result_evidence_ref"]); ev["claim"]=c._direct_capture_claim(cap); ev["claim_digest"]=c.digest(ev["claim"]); ev["raw_output_sha256"]=cap["capture_sha256"]; self.reseal_return(bad,bad_bundle)
        with self.assertRaises(c.JoyflowError):
            c.validate_codex_execution_return_structure(bad, projection, bad_bundle)

        with self.assertRaises(review.JoyflowError):
            review._approved_paths({**projection, "repository_evidence": {"path_discovery": {"final_path_decision": {"decision_digest": "x", "allowed_path_items": []}}}})

    def test_replay_zero_mutation_passes_exact_return(self):
        _, projection, ret, bundle = self.replay_chain()
        c.validate_codex_execution_return(ret, projection, bundle, repository=self.repo)
        self.assertEqual(projection["execution_object"]["logical_role"], "EXISTING_PR_HEAD")
        ref=ret["technical_preflight"]["object_observation_evidence_ref"]; ev=next(x for x in bundle["evidence_rows"] if x["evidence_id"]==ref); observed=next(x for x in bundle["raw_captures"] if x["capture_id"]==ev["raw_output_ref"])["observed_object"]
        self.assertEqual(observed, {"kind": "REPOSITORY_COMMIT", "object_id": "example/repo", "digest": self.head})
        self.assertEqual(c._route_type(projection), "EXISTING_PR_REPLAY")
        self.assertNotIn("current_source_context", projection)
        self.assertEqual(c.derived_current_source_view(projection)["mutation_paths"], [])
        self.assertEqual(ret["mutation_summary"]["mutation_performed"], False)

    def test_projection_source_preflight_accepts_frozen_replay_head(self):
        _, projection, _, _ = self.replay_chain()
        c.validate_execution_projection_sources(projection, repository=self.repo)

    def test_projection_source_preflight_blocks_moved_frozen_replay_head(self):
        _, projection, _, _ = self.replay_chain()
        (self.repo / "moved-after-approval.txt").write_text("moved\n", encoding="utf-8")
        fx.git(self.repo, "add", "moved-after-approval.txt")
        fx.git(self.repo, "commit", "-qm", "moved")
        with self.assertRaises(c.JoyflowError):
            c.validate_execution_projection_sources(projection, repository=self.repo)

    def test_replay_baseline_cannot_replace_canonical_execution_head(self):
        _, projection, _, _ = self.replay_chain()
        self.assertNotEqual(self.base, self.head)
        projection["execution_object"]["physical_object"]["digest"] = self.base
        projection["projection_digest"] = c.digest(c.projection_payload(projection))
        with self.assertRaises(c.JoyflowError):
            c.validate_execution_projection_sources(projection, repository=self.repo)

    def test_projection_source_preflight_blocks_nonancestor_replay_base(self):
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td) / "repo"
            repo.mkdir()
            fx.git(repo, "init", "-q")
            fx.git(repo, "config", "user.email", "test@example.com")
            fx.git(repo, "config", "user.name", "Joyflow Test")
            fx.git(repo, "remote", "add", "origin", "https://github.com/example/repo.git")
            (repo / "runtime").mkdir()
            (repo / "runtime/joyflow_dual_layer.py").write_text("root\n", encoding="utf-8")
            fx.git(repo, "add", ".")
            fx.git(repo, "commit", "-qm", "root")
            root = fx.git(repo, "rev-parse", "HEAD")
            fx.git(repo, "checkout", "-qb", "base")
            (repo / "base.txt").write_text("base\n", encoding="utf-8")
            fx.git(repo, "add", ".")
            fx.git(repo, "commit", "-qm", "base")
            base = fx.git(repo, "rev-parse", "HEAD")
            fx.git(repo, "checkout", "-qb", "head", root)
            (repo / "runtime/joyflow_dual_layer.py").write_text("head\n", encoding="utf-8")
            fx.git(repo, "add", ".")
            fx.git(repo, "commit", "-qm", "head")
            head = fx.git(repo, "rev-parse", "HEAD")
            _, projection, _, _ = fx.repository_replay_approved_projection(repo, base, head)
            with self.assertRaises(c.JoyflowError):
                c.validate_execution_projection_sources(projection, repository=repo)

    def test_projection_source_preflight_preserves_current_round_base(self):
        _, projection, _, _ = fx.repository_approved_projection(self.repo, self.base)
        fx.git(self.repo, "checkout", "-q", self.base)
        c.validate_execution_projection_sources(projection, repository=self.repo)
        fx.git(self.repo, "checkout", "-q", self.head)
        with self.assertRaises(c.JoyflowError):
            c.validate_execution_projection_sources(projection, repository=self.repo)

    def test_zero_product_replay_uses_material_execution_approval_wording(self):
        _, projection, _, _ = self.replay_chain()
        original = copy.deepcopy(projection)
        projection_digest = projection["projection_digest"]
        envelope_digest = c.digest(c.execution_authorization_envelope(projection))
        first = c.render_approval_view(projection)
        second = c.render_approval_view(projection)

        self.assertIn("# JOYFLOW USER MATERIAL EXECUTION APPROVAL VIEW", first)
        self.assertNotIn("# JOYFLOW USER MUTATION APPROVAL VIEW", first)
        self.assertNotIn("Local Codex may adapt implementation details, debug, refactor locally", first)
        self.assertIn("No product/source file modification, implementation change", first)
        self.assertIn("product commit, product push, or PR source mutation is authorized", first)
        self.assertIn("may not be converted into product mutation paths", first)
        self.assertIn("stop and return for Brain re-closure and a new explicit user authorization", first)
        self.assertIn("Validation may be executed only as listed in the exact envelope", first)
        self.assertIn("## Minimum validation", first)
        self.assertEqual(projection["execution_mode"], "MUTATING")
        self.assertEqual([row["argv"] for row in projection["validation"]["checks"]], [row["argv"] for row in original["validation"]["checks"]])
        self.assertEqual(projection, original)
        self.assertEqual(projection["projection_digest"], projection_digest)
        self.assertEqual(c.digest(c.execution_authorization_envelope(projection)), envelope_digest)
        self.assertEqual(first, second)
        self.assertNotEqual(hashlib.sha256(first.encode()).hexdigest(), "3d47e9153d699e0006ae95c6659c17675dd2b6eab912516d5943cf4b41e6663d")

    def test_zero_product_replay_preserves_conditional_current_review_transport(self):
        plan = self.current_review_plan()
        _, projection, view, _ = fx.repository_replay_approved_projection(
            self.repo, self.base, self.head, current_review_transport_plan=plan)
        self.assertEqual(projection["delivery"]["current_review_transport"], plan)
        self.assertIn("Conditional current-review transport may be used only", view)
        self.assertIn("this view does not represent that transport as already created", view)

    def test_zero_product_replay_prompt_does_not_authorize_pr_or_publication_mutation(self):
        approved, projection, _, _ = fx.repository_replay_approved_projection(
            self.repo, self.base, self.head)
        prompt = c.render_prompt(projection, approved["approval_record"])

        self.assertEqual(projection["task_anchor"]["repository_operation"], "EXISTING_FROZEN_PR_REPLAY")
        self.assertEqual(c.derived_current_source_view(projection)["mutation_paths"], [])
        self.assertEqual([r for r in projection["decision_boundary"]["boundary_obligations"] if r["kind"]=="ALLOW_PATH"], [])
        self.assertIsNone(projection["delivery"].get("current_review_transport"))
        self.assertNotIn("Create or update only the bounded candidate PR", prompt)
        self.assertNotIn("place only the four exact current-review inputs", prompt)
        self.assertIn(f"already-existing frozen PR #42 Head {self.head}", prompt)
        self.assertIn("No product/source mutation, new product commit, product push, PR creation or update, PR body mutation, or PR metadata mutation is authorized.", prompt)
        self.assertIn("No current-review remote GitHub transport or publication is authorized unless a future exact Projection separately contains that user-approved authority.", prompt)
        self.assertIn("Execute only the exact approved replay and validation operations.", prompt)
        self.assertIn("Produce the required CODEX_EXECUTION_RETURN and CODEX_EXECUTION_EVIDENCE_BUNDLE", prompt)
        self.assertIn("leave Brain Review pending", prompt)
        self.assertIn("stop before publication. Do not merge.", prompt)

    def test_current_round_repository_mutation_prompt_keeps_bounded_pr_delivery(self):
        approved, projection, _, _ = fx.repository_approved_projection(self.repo, self.base)
        prompt = c.render_prompt(projection, approved["approval_record"])

        self.assertEqual(projection["task_anchor"]["repository_operation"], "CURRENT_ROUND_REPOSITORY_CHANGE")
        self.assertTrue([r for r in projection["decision_boundary"]["boundary_obligations"] if r["kind"]=="ALLOW_PATH"])
        self.assertIn("bounded local commit, bounded push", prompt)
        self.assertIn("bounded candidate PR creation or update", prompt)
        self.assertIn("Do not merge.", prompt)

    def test_current_round_repository_mutation_keeps_bounded_debug_wording(self):
        _, projection, _, _ = fx.repository_approved_projection(self.repo, self.base)
        view = c.render_approval_view(projection)
        self.assertEqual(projection["task_anchor"]["repository_operation"], "CURRENT_ROUND_REPOSITORY_CHANGE")
        self.assertTrue([r for r in projection["decision_boundary"]["boundary_obligations"] if r["kind"]=="ALLOW_PATH"])
        self.assertIn("# JOYFLOW USER MUTATION APPROVAL VIEW", view)
        self.assertIn("Local Codex may adapt implementation details, debug, refactor locally", view)

    def test_read_only_approval_view_wording_is_unchanged(self):
        _, projection, view, _ = f.approved_capsule("READ_ONLY_DISCOVERY", "READ_ONLY")
        self.assertEqual(projection["execution_mode"], "READ_ONLY")
        self.assertIn("# JOYFLOW BRAIN READ-ONLY DISCOVERY AUTHORIZATION VIEW", view)
        self.assertIn("bounded pure read-only Technical Discovery only", view)
        self.assertIn("No file/data mutation, Commit, Push, PR mutation, or material side effect is authorized", view)

    def test_replay_nonempty_mutation_paths_block(self):
        _, projection, ret, bundle = self.replay_chain()
        projection = copy.deepcopy(projection)
        item = fx.f.new_capsule("DEVELOPMENT_STANDARD", "REPOSITORY_CHANGE")["active_fibers"]["repository_evidence"]["payload"]["path_discovery"]["final_path_decision"]["allowed_path_items"][0]
        projection["repository_evidence"]["path_discovery"]["final_path_decision"]["allowed_path_items"] = [item]
        with self.assertRaises(c.JoyflowError):
            c.validate_task_object_lifecycle(projection)

    def test_replay_evidence_variants_are_mutually_exclusive_and_required(self):
        _, projection, ret, bundle = self.replay_chain()
        bad = copy.deepcopy(ret)
        bad["pr_evidence"] = {"pr_url":"https://github.com/example/repo/pull/42","result_evidence_ref":"EXEC_DIFF"}
        bad["return_digest"] = c.digest(c.strip_digest(bad, "return_digest"))
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(bad, projection, bundle)
        bad = copy.deepcopy(ret); bad["repository_replay_evidence"] = None; bad["return_digest"] = c.digest(c.strip_digest(bad, "return_digest"))
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(bad, projection, bundle)

    def test_replay_coverage_omission_and_addition_block(self):
        _, projection, ret, bundle = self.replay_chain()
        for paths in ([], ["runtime/joyflow_dual_layer.py", "extra.py"]):
            bad=copy.deepcopy(ret); bad_bundle=copy.deepcopy(bundle); cap=next(x for x in bad_bundle["raw_captures"] if x["capture_kind"]=="REPOSITORY_DIFF"); cap["observation"]["changed_paths"]=paths; cap["capture_sha256"]=c.digest(c._execution_capture_payload(cap)); ev=next(x for x in bad_bundle["evidence_rows"] if x["evidence_id"]==bad["repository_replay_evidence"]["diff_evidence_ref"]); ev["claim"]=c._direct_capture_claim(cap); ev["claim_digest"]=c.digest(ev["claim"]); ev["raw_output_sha256"]=cap["capture_sha256"]; self.reseal_return(bad,bad_bundle)
            with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(bad, projection, bad_bundle)

    def test_replay_source_state_change_blocks(self):
        _, projection, ret, bundle = self.replay_chain()
        bad_bundle = copy.deepcopy(bundle); captures={x["capture_id"]:x for x in bad_bundle["raw_captures"]}
        after=captures["CAP_REPLAY_STATE_AFTER"]; after["observation"]["worktree_diff_sha256"]="f"*64
        components={key:after["observation"][key] for key in ("head_commit","index_diff_sha256","worktree_diff_sha256","tracked_source_set_sha256","untracked_manifest_sha256","declared_ignored_coverage_sha256")}
        after["observation"]["state_fingerprint_sha256"]=c.digest(components)
        after["stdout"]=json.dumps(after["observation"],ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n"
        after["stdout_sha256"]=c.hashlib.sha256(after["stdout"].encode()).hexdigest(); after["capture_sha256"]=c.digest(c._execution_capture_payload(after))
        evidence=next(x for x in bad_bundle["evidence_rows"] if x["evidence_id"]=="EXEC_REPLAY_STATE_AFTER")
        evidence["claim"]=c._direct_capture_claim(after); evidence["claim_digest"]=c.digest(evidence["claim"]); evidence["raw_output_sha256"]=after["capture_sha256"]
        bad=copy.deepcopy(ret); self.reseal_return(bad,bad_bundle)
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(bad,projection,bad_bundle)

    def test_replay_moved_head_blocks(self):
        _, projection, ret, bundle = self.replay_chain()
        (self.repo/"moved.txt").write_text("moved\n",encoding="utf-8")
        fx.git(self.repo,"add","moved.txt"); fx.git(self.repo,"commit","-qm","moved")
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return(ret,projection,bundle,repository=self.repo)

    def test_replay_base_must_be_ancestor(self):
        with tempfile.TemporaryDirectory() as td:
            repo=pathlib.Path(td)/"repo"; repo.mkdir(); fx.git(repo,"init","-q"); fx.git(repo,"config","user.email","test@example.com"); fx.git(repo,"config","user.name","Joyflow Test"); fx.git(repo,"remote","add","origin","https://github.com/example/repo.git")
            (repo/"runtime").mkdir(); (repo/"runtime/joyflow_dual_layer.py").write_text("root\n"); fx.git(repo,"add","."); fx.git(repo,"commit","-qm","root"); root=fx.git(repo,"rev-parse","HEAD")
            fx.git(repo,"checkout","-qb","base"); (repo/"base.txt").write_text("base\n"); fx.git(repo,"add","."); fx.git(repo,"commit","-qm","base"); base=fx.git(repo,"rev-parse","HEAD")
            fx.git(repo,"checkout","-qb","head",root); (repo/"runtime/joyflow_dual_layer.py").write_text("head\n"); fx.git(repo,"add","."); fx.git(repo,"commit","-qm","head"); head=fx.git(repo,"rev-parse","HEAD")
            approved,projection,_,_=fx.repository_replay_approved_projection(repo,base,head); ret,bundle=fx.repository_return_bundle(projection,repo,base,head)
            with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return(ret,projection,bundle,repository=repo)

    def test_replay_brain_review_and_pr_record_pass_exact_chain(self):
        approved, projection, ret, bundle = self.replay_chain()
        executing=f.advance(approved,"CODEX_EXECUTION")
        reviewing=f.brain_review_capsule(executing,projection,ret,bundle)
        reviewed=f.revise_review(reviewing,"BRAIN_REVIEW",brain_verdict="PASS")
        record=fx.pr_record(projection,ret,bundle,reviewed,base=self.base,head=self.head)
        result=review.validate_pr_record(record,repository=self.repo,projection=projection,codex_return=ret,evidence_bundle=bundle,brain_review_capsule=reviewed,current_base_sha=self.base,current_pr_number=42,replay_tests=True)
        self.assertEqual(result["head_sha"],self.head)
        self.assertEqual(record["brain_block"]["execution_binding"]["approved_allowed_paths"],[])

    def test_existing_transport_consumer_accepts_replay_object_chain(self):
        approved, projection, ret, bundle = self.replay_chain()
        executing=f.advance(approved,"CODEX_EXECUTION")
        reviewed=f.revise_review(f.brain_review_capsule(executing,projection,ret,bundle),"BRAIN_REVIEW",brain_verdict="PASS")
        locator={"source_head_sha":self.head,"base_sha":self.base}
        repo_check._validate_current_review_object_chain({"CODEX_HANDOFF_PROJECTION":projection,"CODEX_EXECUTION_RETURN":ret,"CODEX_EXECUTION_EVIDENCE_BUNDLE":bundle,"BRAIN_REVIEW_CAPSULE":reviewed},locator)

    def test_regression_18_none_local_result_passes_strict_operational_return_validation(self):
        _,projection,ret,bundle,_=self.local_chain()
        c.validate_codex_execution_return(ret,projection,bundle,repository=self.repo)

    def test_regression_19_local_after_source_drift_fails_strict_operational_validation(self):
        _,projection,ret,bundle,_=self.local_chain()
        (self.repo/'runtime/joyflow_dual_layer.py').write_text("print('drift')\n",encoding='utf-8')
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return(ret,projection,bundle,repository=self.repo)

    def test_regression_20_none_local_result_enters_operational_repository_brain_review(self):
        *_,reviewing=self.operational_local_review()
        self.assertEqual(reviewing['task_progress']['stage'],'BRAIN_REVIEW')

    def test_regression_21_local_review_target_binds_exact_non_pr_result(self):
        _,projection,ret,bundle,_,reviewing=self.operational_local_review()
        target=reviewing['active_fibers']['execution_review']['payload']['review_target']
        after_ref=ret['local_repository_evidence']['source_state_after_evidence_ref']; evidence={x['evidence_id']:x for x in bundle['evidence_rows']}; captures={x['capture_id']:x for x in bundle['raw_captures']}
        after=captures[evidence[after_ref]['raw_output_ref']]['observation']
        self.assertEqual(target['target_type'],'REPOSITORY_LOCAL_STATE'); self.assertEqual(target['after_state_fingerprint'],after['state_fingerprint_sha256'])
        self.assertEqual(target['actual_changed_paths'],['runtime/joyflow_dual_layer.py']); self.assertEqual(target['source_projection_digest'],projection['projection_digest']); self.assertEqual(target['source_codex_return_digest'],ret['return_digest']); self.assertEqual(target['source_evidence_bundle_digest'],bundle['evidence_bundle_digest'])
        self.assertNotIn('head_sha',target); self.assertNotIn('pr_url',target)

    def test_regression_22_local_review_rejects_source_diff_path_and_packet_substitution(self):
        _,projection,ret,bundle,executing,reviewing=self.operational_local_review()
        bad_bundle=copy.deepcopy(bundle); cap=next(x for x in bad_bundle['raw_captures'] if x['capture_id']=='CAP_EXEC_LOCAL_DIFF'); cap['observation']['changed_paths']=['tests/substituted.py']; cap['capture_sha256']=c.digest(c._execution_capture_payload(cap)); ev=next(x for x in bad_bundle['evidence_rows'] if x['evidence_id']=='EXEC_LOCAL_DIFF'); ev['claim']=c._direct_capture_claim(cap); ev['claim_digest']=c.digest(ev['claim']); ev['raw_output_sha256']=cap['capture_sha256']; bad_ret=copy.deepcopy(ret); self.reseal_return(bad_ret,bad_bundle)
        with self.assertRaises(c.JoyflowError): c.validate_review_input_binding(reviewing,projection,bad_ret,bad_bundle,source_repository=self.repo)
        bad_bundle=copy.deepcopy(bundle); cap=next(x for x in bad_bundle['raw_captures'] if x['capture_id']=='CAP_EXEC_LOCAL_DIFF'); substituted=b'substituted repository Diff\n'; cap['observation']['diff_sha256']=hashlib.sha256(substituted).hexdigest(); f._refresh_raw_capture(cap,substituted); ev=next(x for x in bad_bundle['evidence_rows'] if x['evidence_id']=='EXEC_LOCAL_DIFF'); ev['claim']=c._direct_capture_claim(cap); ev['claim_digest']=c.digest(ev['claim']); ev['raw_output_sha256']=cap['capture_sha256']; bad_ret=copy.deepcopy(ret); self.reseal_return(bad_ret,bad_bundle)
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return(bad_ret,projection,bad_bundle,repository=self.repo)
        bad_bundle=copy.deepcopy(bundle); cap=next(x for x in bad_bundle['raw_captures'] if x['capture_id']=='CAP_LOCAL_STATE_AFTER'); cap['observation']['worktree_diff_sha256']='f'*64; components={k:cap['observation'][k] for k in ('head_commit','index_diff_sha256','worktree_diff_sha256','tracked_source_set_sha256','untracked_manifest_sha256','declared_ignored_coverage_sha256')}; cap['observation']['state_fingerprint_sha256']=c.digest(components); f._refresh_raw_capture(cap,c.canonical_bytes(cap['observation'])+b'\n'); ev=next(x for x in bad_bundle['evidence_rows'] if x['evidence_id']=='EXEC_LOCAL_STATE_AFTER'); ev['claim']=c._direct_capture_claim(cap); ev['claim_digest']=c.digest(ev['claim']); ev['raw_output_sha256']=cap['capture_sha256']; bad_ret=copy.deepcopy(ret); self.reseal_return(bad_ret,bad_bundle)
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return(bad_ret,projection,bad_bundle,repository=self.repo)
        bad_ret=copy.deepcopy(ret); bad_ret['return_digest']='0'*64
        with self.assertRaises(c.JoyflowError): c.validate_review_input_binding_structure(reviewing,projection,bad_ret,bundle)
        bad_projection=copy.deepcopy(projection); bad_projection['projection_digest']='1'*64
        with self.assertRaises(c.JoyflowError): c.validate_review_input_binding_structure(reviewing,bad_projection,ret,bundle)
        bad_bundle=copy.deepcopy(bundle); bad_bundle['evidence_bundle_digest']='2'*64
        with self.assertRaises(c.JoyflowError): c.validate_review_input_binding_structure(reviewing,projection,ret,bad_bundle)
        (self.repo/'runtime/joyflow_dual_layer.py').write_text("print('substituted after')\n",encoding='utf-8')
        with self.assertRaises(c.JoyflowError): c.validate_review_input_binding(reviewing,projection,ret,bundle,source_repository=self.repo)

    def test_regression_23_candidate_pr_and_frozen_replay_operational_consumers_remain_valid(self):
        _,projection,_,_=fx.repository_approved_projection(self.repo,self.base); ret,bundle=fx.repository_return_bundle(projection,self.repo,self.base,self.head); self.normalize_physical_captures(ret,bundle); c.validate_codex_execution_return(ret,projection,bundle,repository=self.repo)
        _,projection,ret,bundle=self.replay_chain(); c.validate_codex_execution_return(ret,projection,bundle,repository=self.repo)

    def test_regression_24_local_brain_pass_cannot_imply_publication_acceptance_or_promotion(self):
        *_,reviewing=self.operational_local_review(); reviewed=f.revise_review(reviewing,'BRAIN_REVIEW',brain_verdict='PASS'); payload=reviewed['active_fibers']['execution_review']['payload']; gates=reviewed['derived_gates']
        self.assertEqual(payload['user_acceptance'],'PENDING_USER_ACCEPTANCE'); self.assertIsNone(payload['merge_candidate_freeze_digest']); self.assertEqual(payload['merge_status'],'NOT_AUTHORIZED')
        self.assertEqual(gates['user_acceptance_gate'],'NOT_ACTIVE'); self.assertEqual(gates['pr_review_gate'],'NOT_ACTIVE'); self.assertEqual(gates['merge_gate'],'NOT_ACTIVE')

    def test_regression_25_local_review_target_cannot_enter_pr_acceptance_or_merge_lifecycle(self):
        *_,reviewing=self.operational_local_review(); reviewed=f.revise_review(reviewing,'BRAIN_REVIEW',brain_verdict='PASS')
        with self.assertRaises(c.JoyflowError): f.revise_review(reviewed,'USER_ACCEPTANCE')
        illegal=copy.deepcopy(reviewed); illegal['task_progress']['stage']='MERGE_DECISION'; illegal['derived_gates']=c.compute_gate_snapshot(illegal)
        with self.assertRaises(c.JoyflowError): c.validate_capsule(illegal)

    def test_regression_26_none_local_result_with_nonempty_ignored_coverage_passes_strict_operational_validation(self):
        _,projection,ret,bundle,_=self.ignored_local_chain()
        refs=ret['local_repository_evidence']; evidence={x['evidence_id']:x for x in bundle['evidence_rows']}; captures={x['capture_id']:x for x in bundle['raw_captures']}
        for ref in (refs['source_state_before_evidence_ref'],refs['source_state_after_evidence_ref']):
            observation=captures[evidence[ref]['raw_output_ref']]['observation']
            self.assertEqual(observation['declared_ignored_paths'],['ignored-local.txt'])
            self.assertNotEqual(observation['declared_ignored_coverage_sha256'],c.digest(observation['declared_ignored_paths']))
        c.validate_codex_execution_return(ret,projection,bundle,repository=self.repo)

    def test_regression_27_none_local_result_ignored_object_drift_fails_strict_operational_validation(self):
        _,projection,ret,bundle,_=self.ignored_local_chain()
        (self.repo/'ignored-local.txt').write_bytes(b'drifted ignored object\n')
        with self.assertRaisesRegex(c.JoyflowError,'sealed local AFTER state'):
            c.validate_codex_execution_return(ret,projection,bundle,repository=self.repo)


if __name__ == "__main__":
    unittest.main()
