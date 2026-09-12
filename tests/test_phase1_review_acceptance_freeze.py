from __future__ import annotations
import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "runtime")]
import phase1_review_fixture as fx  # noqa: E402
import joyflow_phase1_review as review  # noqa: E402
import joyflow_phase1_merge as merge  # noqa: E402


class ReviewAcceptanceFreezeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td, cls.repo, cls.base, cls.head = fx.create_repository()
        cls.chain = fx.full_merge_authorization_chain(cls.repo, cls.base, cls.head)

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def validate_freeze(self, freeze=None, ci=None):
        c = self.chain
        return merge.validate_merge_candidate_freeze(
            freeze or c["merge_candidate_freeze"], repository=self.repo, pr_body=c["pr_body"],
            projection=c["projection"], codex_return=c["codex_return"], evidence_bundle=c["evidence_bundle"],
            brain_review_capsule=c["brain_review"], pr_ci_result=ci or c["pr_ci_result"],
            current_base_sha=self.base, current_pr_number=42,
        )

    def test_exact_review_ci_freeze_passes_before_acceptance(self):
        result = self.validate_freeze()
        self.assertEqual(result["freeze_digest"], self.chain["merge_candidate_freeze"]["freeze_digest"])
        self.assertNotIn("user_acceptance_capsule_digest", self.chain["merge_candidate_freeze"])
        self.assertNotIn("merge_ready_record_digest", self.chain["merge_candidate_freeze"])
        self.assertNotIn("merged_change_projection_digest", self.chain["merge_candidate_freeze"])

    def test_post_freeze_acceptance_binds_exact_freeze(self):
        c = self.chain
        result = merge.validate_post_freeze_user_acceptance(
            c["user_acceptance"], merge_candidate_freeze=c["merge_candidate_freeze"], repository=self.repo,
            projection=c["projection"], codex_return=c["codex_return"], evidence_bundle=c["evidence_bundle"],
        )
        self.assertEqual(result["status"], "PASS")

    def test_acceptance_bound_to_other_freeze_blocks(self):
        c = self.chain
        changed = copy.deepcopy(c["merge_candidate_freeze"])
        changed["head_sha"] = "0" * 40
        changed["freeze_digest"] = merge.digest(merge.strip_digest(changed, "freeze_digest"))
        with self.assertRaises(merge.JoyflowError):
            merge.validate_post_freeze_user_acceptance(
                c["user_acceptance"], merge_candidate_freeze=changed, repository=self.repo,
                projection=c["projection"], codex_return=c["codex_return"], evidence_bundle=c["evidence_bundle"], replay_source=False,
            )

    def test_ci_substitution_blocks_freeze(self):
        changed = copy.deepcopy(self.chain["pr_ci_result"])
        changed["projection_digest"] = "0" * 64
        changed["result_digest"] = review.digest(review.strip_digest(changed, "result_digest"))
        with self.assertRaises(merge.JoyflowError):
            self.validate_freeze(ci=changed)

    def test_public_freeze_entry_needs_no_acceptance_or_projection(self):
        c = self.chain
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            rows = {
                "projection.json": c["projection"], "return.json": c["codex_return"], "bundle.json": c["evidence_bundle"],
                "review.json": c["brain_review"], "ci.json": c["pr_ci_result"], "freeze.json": c["merge_candidate_freeze"],
            }
            for name, obj in rows.items(): (td/name).write_text(json.dumps(obj), encoding="utf-8")
            (td/"body.md").write_text(c["pr_body"], encoding="utf-8")
            before = review.repository_state_snapshot(self.repo)
            cmd = [sys.executable, str(ROOT/"tools/joyflow_merge_freeze_check.py"), "--repository", str(self.repo),
                   "--pr-body-file", str(td/"body.md"), "--projection", str(td/"projection.json"),
                   "--codex-return", str(td/"return.json"), "--evidence-bundle", str(td/"bundle.json"),
                   "--brain-review-capsule", str(td/"review.json"), "--pr-ci-result", str(td/"ci.json"),
                   "--merge-candidate-freeze", str(td/"freeze.json"), "--base-sha", self.base, "--pr-number", "42"]
            proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertEqual(before, review.repository_state_snapshot(self.repo))


if __name__ == "__main__": unittest.main()
