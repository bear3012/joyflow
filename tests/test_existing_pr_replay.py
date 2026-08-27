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
        return approved, projection, ret, bundle

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
        ret["execution_lifecycle_result"]["transition_digest"] = c.execution_lifecycle_result_digest(ret["execution_lifecycle_result"])
        ret["return_digest"] = c.digest(c.strip_digest(ret, "return_digest"))

    def test_case_a_happy_path_and_truthfulness_guards(self):
        approved, projection, _, _ = fx.repository_approved_projection(self.repo, self.base)
        ret, bundle = fx.repository_return_bundle(projection, self.repo, self.base, self.head)
        c.validate_codex_execution_return(ret, projection, bundle, repository=self.repo)

        bad = copy.deepcopy(ret)
        bad["mutation_summary"]["mutation_performed"] = False
        bad["return_digest"] = c.digest(c.strip_digest(bad, "return_digest"))
        with self.assertRaises(c.JoyflowError):
            c.validate_codex_execution_return_structure(bad, projection, bundle)

        bad = copy.deepcopy(ret)
        bad["pr_evidence"]["touched_files"] = ["runtime/substituted.py"]
        bad["return_digest"] = c.digest(c.strip_digest(bad, "return_digest"))
        with self.assertRaises(c.JoyflowError):
            c.validate_codex_execution_return_structure(bad, projection, bundle)

        with self.assertRaises(review.JoyflowError):
            review._approved_paths({**projection, "repository_evidence": {"path_discovery": {"final_path_decision": {"decision_digest": "x", "allowed_path_items": []}}}})

    def test_replay_zero_mutation_passes_exact_return(self):
        _, projection, ret, bundle = self.replay_chain()
        c.validate_codex_execution_return(ret, projection, bundle, repository=self.repo)
        self.assertEqual(projection["task_object_lifecycle"]["route_type"], "EXISTING_PR_REPLAY")
        self.assertEqual(projection["current_source_context"]["current_product_mutation_paths"], [])
        self.assertEqual(ret["mutation_summary"]["mutation_performed"], False)

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
        self.assertEqual(projection["current_source_context"]["current_product_mutation_paths"], [])
        self.assertEqual(projection["task_object_lifecycle"]["approved_execution_boundary"]["allowed_paths"], [])
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
        self.assertTrue(projection["task_object_lifecycle"]["approved_execution_boundary"]["allowed_paths"])
        self.assertIn("Create or update only the bounded candidate PR. Do not merge.", prompt)

    def test_current_round_repository_mutation_keeps_bounded_debug_wording(self):
        _, projection, _, _ = fx.repository_approved_projection(self.repo, self.base)
        view = c.render_approval_view(projection)
        self.assertEqual(projection["task_anchor"]["repository_operation"], "CURRENT_ROUND_REPOSITORY_CHANGE")
        self.assertTrue(projection["task_object_lifecycle"]["approved_execution_boundary"]["allowed_paths"])
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
        projection["task_object_lifecycle"]["approved_execution_boundary"]["allowed_paths"] = [item["path"]]
        boundary = projection["task_object_lifecycle"]["approved_execution_boundary"]
        boundary["boundary_digest"] = c.digest(c.strip_digest(boundary, "boundary_digest"))
        projection["task_object_lifecycle"]["lifecycle_digest"] = c.digest(c.strip_digest(projection["task_object_lifecycle"], "lifecycle_digest"))
        with self.assertRaises(c.JoyflowError):
            c.validate_task_object_lifecycle(projection)

    def test_replay_evidence_variants_are_mutually_exclusive_and_required(self):
        _, projection, ret, bundle = self.replay_chain()
        bad = copy.deepcopy(ret)
        bad["pr_evidence"] = {"repository_id":"example/repo","base_branch":"main","working_branch":"joyflow/task","pr_url":"https://github.com/example/repo/pull/42","base_commit":self.base,"head_sha":self.head,"touched_files":["runtime/joyflow_dual_layer.py"],"diff_evidence_ref":"EXEC_DIFF"}
        bad["return_digest"] = c.digest(c.strip_digest(bad, "return_digest"))
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(bad, projection, bundle)
        bad = copy.deepcopy(ret); bad["repository_replay_evidence"] = None; bad["return_digest"] = c.digest(c.strip_digest(bad, "return_digest"))
        with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(bad, projection, bundle)

    def test_replay_coverage_omission_and_addition_block(self):
        _, projection, ret, bundle = self.replay_chain()
        for paths in ([], ["runtime/joyflow_dual_layer.py", "extra.py"]):
            bad = copy.deepcopy(ret); bad["repository_replay_evidence"]["review_coverage_paths"] = paths
            bad["return_digest"] = c.digest(c.strip_digest(bad, "return_digest"))
            with self.assertRaises(c.JoyflowError): c.validate_codex_execution_return_structure(bad, projection, bundle)

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


if __name__ == "__main__":
    unittest.main()
