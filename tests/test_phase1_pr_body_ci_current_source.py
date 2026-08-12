from __future__ import annotations

import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "runtime"))
import phase1_review_fixture as fx  # noqa: E402
import joyflow_phase1_review as r  # noqa: E402


class PRBodyCurrentSourceTests(unittest.TestCase):
    def setUp(self):
        self.td, self.repo, self.base, self.head = fx.create_repository()
        _, self.projection, self.ret, self.bundle, _, self.reviewed, _ = fx.full_current_repository_chain(self.repo, self.base, self.head)
        self.record = fx.pr_record(self.projection, self.ret, self.bundle, self.reviewed, base=self.base, head=self.head)

    def tearDown(self):
        self.td.cleanup()

    def validate(self, record=None):
        return r.validate_pr_record(
            record or self.record,
            repository=self.repo,
            projection=self.projection,
            codex_return=self.ret,
            evidence_bundle=self.bundle,
            brain_review_capsule=self.reviewed,
            merged_change_projection=(record or self.record)["brain_block"]["merged_change_projection"],
            current_base_sha=self.base,
            current_pr_number=42,
            replay_tests=True,
        )

    def reseal(self, record):
        record["codex_block"]["codex_block_digest"] = r.digest(r.pr_block_payload(record["codex_block"], "codex_block_digest"))
        record["brain_block"]["brain_review"]["source_codex_block_digest"] = record["codex_block"]["codex_block_digest"]
        record["brain_block"]["brain_block_digest"] = r.digest(r.pr_block_payload(record["brain_block"], "brain_block_digest"))
        record["record_digest"] = r.digest(r.strip_digest(record, "record_digest"))
        return record

    def test_current_exact_source_chain_passes(self):
        result = self.validate()
        self.assertEqual(result["head_sha"], self.head)

    def test_premerge_merged_change_projection_input_blocks(self):
        with self.assertRaisesRegex(r.JoyflowError, 'post-merge navigation context'):
            r.validate_pr_record(
                self.record, repository=self.repo, projection=self.projection, codex_return=self.ret,
                evidence_bundle=self.bundle, brain_review_capsule=self.reviewed,
                merged_change_projection={'unexpected': 'pre-merge'}, current_base_sha=self.base,
                current_pr_number=42, replay_tests=True,
            )

    def test_non_ancestor_base_blocks(self):
        other = fx.git(self.repo, "rev-parse", "HEAD")
        fx.git(self.repo, "checkout", "-qb", "divergent", self.base)
        (self.repo / "divergent.txt").write_text("divergent\n", encoding="utf-8")
        fx.git(self.repo, "add", ".")
        fx.git(self.repo, "commit", "-qm", "divergent")
        divergent_head = fx.git(self.repo, "rev-parse", "HEAD")
        fx.git(self.repo, "checkout", "-q", "master")
        record = copy.deepcopy(self.record)
        record["base_sha"] = divergent_head
        record["brain_block"]["execution_binding"]["expected_base_commit"] = divergent_head
        record["codex_block"]["execution"]["checked_base_sha"] = divergent_head
        self.reseal(record)
        with self.assertRaises(r.JoyflowError):
            r.validate_pr_record(record, repository=self.repo, projection=self.projection, codex_return=self.ret, evidence_bundle=self.bundle, brain_review_capsule=self.reviewed, merged_change_projection=record["brain_block"]["merged_change_projection"], current_base_sha=divergent_head, current_pr_number=42, replay_tests=True)
        self.assertEqual(other, self.head)

    def test_diff_mismatch_blocks_even_when_record_resealed(self):
        record = copy.deepcopy(self.record)
        record["codex_block"]["execution"]["actual_changed_paths"] = ["tests/test_placeholder.py"]
        record["codex_block"]["execution"]["actual_changed_paths_digest"] = r.changed_paths_digest(["tests/test_placeholder.py"])
        self.reseal(record)
        with self.assertRaises(r.JoyflowError):
            self.validate(record)

    def test_projection_substitution_blocks(self):
        projection = copy.deepcopy(self.projection)
        projection["projection_digest"] = "0" * 64
        with self.assertRaises(r.JoyflowError):
            r.validate_pr_record(self.record, repository=self.repo, projection=projection, codex_return=self.ret, evidence_bundle=self.bundle, brain_review_capsule=self.reviewed, merged_change_projection=self.record["brain_block"]["merged_change_projection"], current_base_sha=self.base, current_pr_number=42, replay_tests=True)

    def test_brain_review_capsule_substitution_blocks(self):
        capsule = copy.deepcopy(self.reviewed)
        capsule["active_fibers"]["execution_review"]["payload"]["unresolved_followups"] = ["substituted"]
        with self.assertRaises(r.JoyflowError):
            r.validate_pr_record(self.record, repository=self.repo, projection=self.projection, codex_return=self.ret, evidence_bundle=self.bundle, brain_review_capsule=capsule, current_base_sha=self.base, current_pr_number=42, replay_tests=True)

    def test_public_entry_real_repository_passes_and_is_observation_only(self):
        objects = pathlib.Path(self.td.name) / "objects"
        objects.mkdir()
        for name, value in (("projection.json", self.projection), ("return.json", self.ret), ("bundle.json", self.bundle), ("review.json", self.reviewed)):
            (objects / name).write_text(json.dumps(value), encoding="utf-8")
        (objects / "body.md").write_text(r.render_pr_body(self.record), encoding="utf-8")
        before = r.repository_state_snapshot(self.repo)
        proc = subprocess.run([
            sys.executable, str(ROOT / "tools/joyflow_repo_check.py"), "verify-pr",
            "--repository", str(self.repo), "--pr-body-file", str(objects / "body.md"),
            "--projection", str(objects / "projection.json"), "--codex-return", str(objects / "return.json"),
            "--evidence-bundle", str(objects / "bundle.json"), "--brain-review-capsule", str(objects / "review.json"),
            "--base-sha", self.base, "--pr-number", "42",
        ], capture_output=True, text=True)
        after = r.repository_state_snapshot(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(before, after)
        result = json.loads(proc.stdout)
        self.assertEqual(result["result"], "PASS")

    def test_public_entry_nonancestor_blocks(self):
        fx.git(self.repo, "checkout", "-qb", "other", self.base)
        (self.repo / "other.txt").write_text("other\n", encoding="utf-8")
        fx.git(self.repo, "add", ".")
        fx.git(self.repo, "commit", "-qm", "other")
        other = fx.git(self.repo, "rev-parse", "HEAD")
        fx.git(self.repo, "checkout", "-q", "master")
        objects = pathlib.Path(self.td.name) / "objects2"
        objects.mkdir()
        record = copy.deepcopy(self.record)
        record["base_sha"] = other
        record["brain_block"]["execution_binding"]["expected_base_commit"] = other
        record["codex_block"]["execution"]["checked_base_sha"] = other
        self.reseal(record)
        for name, value in (("projection.json", self.projection), ("return.json", self.ret), ("bundle.json", self.bundle), ("review.json", self.reviewed)):
            (objects / name).write_text(json.dumps(value), encoding="utf-8")
        (objects / "body.md").write_text(r.render_pr_body(record), encoding="utf-8")
        proc = subprocess.run([
            sys.executable, str(ROOT / "tools/joyflow_repo_check.py"), "verify-pr", "--repository", str(self.repo),
            "--pr-body-file", str(objects / "body.md"), "--projection", str(objects / "projection.json"),
            "--codex-return", str(objects / "return.json"), "--evidence-bundle", str(objects / "bundle.json"),
            "--brain-review-capsule", str(objects / "review.json"), "--base-sha", other, "--pr-number", "42",
        ], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("ancestor", proc.stdout)


if __name__ == "__main__":
    unittest.main()
