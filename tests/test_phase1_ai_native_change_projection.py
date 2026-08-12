from __future__ import annotations
import copy, json, pathlib, subprocess, sys, tempfile, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "runtime")]
import phase1_review_fixture as fx  # noqa: E402
import joyflow_phase1_projection as projection_runtime  # noqa: E402
import joyflow_phase1_review as review  # noqa: E402

class AINativeChangeProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td, cls.repo, cls.base, cls.head = fx.create_repository()
        cls.chain = fx.full_merge_authorization_chain(cls.repo, cls.base, cls.head)
    @classmethod
    def tearDownClass(cls): cls.td.cleanup()

    def validate_projection(self, row=None, paths=None, pointer=None):
        c=self.chain
        return projection_runtime.validate_merged_change_projection(
            row or c["merged_change_projection"], projection=c["projection"], codex_return=c["codex_return"],
            evidence_bundle=c["evidence_bundle"], brain_review_capsule=c["brain_review"], pr_record=c["pr_record"],
            actual_changed_paths=paths or c["pr_record"]["codex_block"]["execution"]["actual_changed_paths"],
            completion_pointer=pointer or c["completion_pointer"])

    def test_exact_post_merge_navigation_projection_passes(self):
        self.validate_projection()
        row=self.chain["merged_change_projection"]
        self.assertEqual(row["lifecycle"]["timing"],"POST_MERGE_ONLY")
        self.assertEqual(row["lifecycle"]["pre_merge_gate_role"],"NONE")

    def test_resealed_foreign_return_provenance_blocks(self):
        changed=copy.deepcopy(self.chain["merged_change_projection"]); changed["provenance"]["codex_return_digest"]="0"*64
        changed["projection_digest"]=projection_runtime.digest(projection_runtime.strip_digest(changed,"projection_digest"))
        with self.assertRaises(projection_runtime.JoyflowError): self.validate_projection(changed)

    def test_foreign_completion_pointer_blocks(self):
        pointer=copy.deepcopy(self.chain["completion_pointer"]); pointer["merge_commit"]="abcdef0123456789"; pointer["pointer_digest"]=fx.c.digest(fx.c.strip_digest(pointer,"pointer_digest"))
        with self.assertRaises(projection_runtime.JoyflowError): self.validate_projection(pointer=pointer)

    def test_complete_current_diff_path_set_is_required(self):
        with self.assertRaises(projection_runtime.JoyflowError): self.validate_projection(paths=["tests/test_placeholder.py"])

    def test_navigation_projection_cannot_become_fact_authority(self):
        changed=copy.deepcopy(self.chain["merged_change_projection"]); changed["historical_semantics"]["substitutes_current_repository"]=True
        changed["projection_digest"]=projection_runtime.digest(projection_runtime.strip_digest(changed,"projection_digest"))
        with self.assertRaises(projection_runtime.JoyflowError): self.validate_projection(changed)

    def test_temporary_fiber_is_nonpersistent(self):
        row=self.chain["merged_change_projection"]; anchor=row["retrieval_anchors"]["test_ids"][0]
        pending=projection_runtime.build_temporary_evidence_fiber(row,"PROVENANCE_REVIEW",[anchor]); self.assertFalse(pending["persistent"])
        closed=projection_runtime.build_temporary_evidence_fiber(row,"PROVENANCE_REVIEW",[anchor],closure={"current_object_bound":True,"direct_evidence_refs":["current:repository"],"derived_steps_marked":True,"authority_boundary_present":True,"verification_refs":[anchor],"counterevidence_checked":True,"unresolved_items":[]})
        self.assertEqual(closed["final_status"],"CLOSED"); self.assertFalse(closed["persistent"])

    def _write(self,d):
        c=self.chain
        rows={"source_projection.json":c["projection"],"return.json":c["codex_return"],"bundle.json":c["evidence_bundle"],"review.json":c["brain_review"],"record.json":c["pr_record"],"change.json":c["merged_change_projection"],"freeze.json":c["merge_candidate_freeze"],"acceptance.json":c["user_acceptance"],"auth.json":c["user_merge_authorization"],"pointer.json":c["completion_pointer"]}
        for n,v in rows.items(): (d/n).write_text(json.dumps(v),encoding="utf-8")
        (d/"body.md").write_text(c["pr_body"],encoding="utf-8")

    def test_public_projection_entry_consumes_completion_pointer(self):
        with tempfile.TemporaryDirectory() as td:
            td=pathlib.Path(td); self._write(td); paths=self.chain["pr_record"]["codex_block"]["execution"]["actual_changed_paths"]
            cmd=[sys.executable,str(ROOT/"runtime/joyflow_phase1_projection.py"),"--merged-change-projection",str(td/"change.json"),"--source-projection",str(td/"source_projection.json"),"--codex-return",str(td/"return.json"),"--evidence-bundle",str(td/"bundle.json"),"--brain-review-capsule",str(td/"review.json"),"--pr-record",str(td/"record.json"),"--completion-pointer",str(td/"pointer.json")]
            for path in paths: cmd += ["--changed-path",path]
            proc=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True); self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)

    def test_pr_ci_does_not_consume_post_merge_projection(self):
        with tempfile.TemporaryDirectory() as td:
            td=pathlib.Path(td); self._write(td)
            before=review.repository_state_snapshot(self.repo)
            proc=subprocess.run([sys.executable,str(ROOT/"tools/joyflow_repo_check.py"),"verify-pr","--repository",str(self.repo),"--pr-body-file",str(td/"body.md"),"--projection",str(td/"source_projection.json"),"--codex-return",str(td/"return.json"),"--evidence-bundle",str(td/"bundle.json"),"--brain-review-capsule",str(td/"review.json"),"--base-sha",self.base,"--pr-number","42"],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr); self.assertEqual(before,review.repository_state_snapshot(self.repo))

    def test_user_authorization_bound_to_exact_freeze_acceptance_and_head(self):
        c=self.chain
        fx.c.validate_user_merge_authorization(c["user_merge_authorization"],c["merge_candidate_freeze"],c["user_acceptance"])
        foreign=copy.deepcopy(c["merge_candidate_freeze"]); foreign["head_sha"]="f"*40; foreign["freeze_digest"]=fx.c.digest(fx.c.strip_digest(foreign,"freeze_digest"))
        with self.assertRaises(fx.c.JoyflowError): fx.c.validate_user_merge_authorization(c["user_merge_authorization"],foreign,c["user_acceptance"])

    def test_public_completion_entry_requires_freeze_acceptance_authorization(self):
        with tempfile.TemporaryDirectory() as td:
            td=pathlib.Path(td); self._write(td)
            cmd=[sys.executable,str(ROOT/"runtime/joyflow_dual_layer.py"),"verify-completion-pointer",str(td/"pointer.json"),"--merge-freeze",str(td/"freeze.json"),"--user-acceptance-capsule",str(td/"acceptance.json"),"--user-authorization",str(td/"auth.json")]
            proc=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True); self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)

if __name__=="__main__": unittest.main()
