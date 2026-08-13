from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "runtime"))
sys.path.insert(0, str(ROOT / "tools"))
import phase1_review_fixture as fx  # noqa: E402
import joyflow_dual_layer as core  # noqa: E402
import joyflow_phase1_review as review  # noqa: E402
import joyflow_repo_check as repo_check  # noqa: E402


def current_review_plan() -> dict:
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


class CurrentPRReviewInputTransportTests(unittest.TestCase):
    def setUp(self):
        self.td, self.repo, self.base, self.head = fx.create_repository()
        self.approved, self.projection, _, _ = fx.repository_approved_projection(
            self.repo, self.base, current_review_transport_plan=current_review_plan()
        )
        executing = fx.f.advance(self.approved, "CODEX_EXECUTION")
        self.ret, self.bundle = fx.repository_return_bundle(self.projection, self.repo, self.base, self.head)
        reviewing = fx.f.brain_review_capsule(executing, self.projection, self.ret, self.bundle)
        self.reviewed = fx.f.revise_review(reviewing, "BRAIN_REVIEW", brain_verdict="PASS")
        self.record = fx.pr_record(self.projection, self.ret, self.bundle, self.reviewed, base=self.base, head=self.head)
        self.transport_root = pathlib.Path(self.td.name) / "transport"
        self.transport_work = self.transport_root / "work"
        self.transport_bare = self.transport_root / "remote.git"
        self.transport_ref = current_review_plan()["github_surface"]["temporary_ref"]
        self.transport_root.mkdir()
        subprocess.run(["git", "init", "--bare", str(self.transport_bare)], check=True, capture_output=True)
        self.transport_work.mkdir()
        fx.git(self.transport_work, "init", "-q")
        fx.git(self.transport_work, "config", "user.email", "test@example.com")
        fx.git(self.transport_work, "config", "user.name", "Joyflow Test")
        fx.git(self.transport_work, "remote", "add", "origin", str(self.transport_bare))
        fx.git(self.repo, "config", "joyflow.currentReviewTransportRemote", str(self.transport_bare))
        self.transport_count = 0
        self.materialize_count = 0
        self.values = {
            "CODEX_HANDOFF_PROJECTION": self.projection,
            "CODEX_EXECUTION_RETURN": self.ret,
            "CODEX_EXECUTION_EVIDENCE_BUNDLE": self.bundle,
            "BRAIN_REVIEW_CAPSULE": self.reviewed,
        }
        self.commit, self.object_bytes = self._commit_values(self.values)
        self.locator = self._locator(self.commit, self.object_bytes)

    def tearDown(self):
        self.td.cleanup()

    def _commit_values(self, values: dict[str, dict], *, extra: bool = False, missing_role: str | None = None) -> tuple[str, dict[str, bytes]]:
        paths = {
            "CODEX_HANDOFF_PROJECTION": "current-review/CODEX_HANDOFF_PROJECTION.json",
            "CODEX_EXECUTION_RETURN": "current-review/CODEX_EXECUTION_RETURN.json",
            "CODEX_EXECUTION_EVIDENCE_BUNDLE": "current-review/CODEX_EXECUTION_EVIDENCE_BUNDLE.json",
            "BRAIN_REVIEW_CAPSULE": "current-review/BRAIN_REVIEW_CAPSULE.json",
        }
        data_by_role = {}
        for role, value in values.items():
            if role == missing_role:
                continue
            data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            target = self.transport_work / paths[role]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            data_by_role[role] = data
        if missing_role:
            target = self.transport_work / paths[missing_role]
            if target.exists():
                target.unlink()
        extra_path = self.transport_work / "current-review/EXTRA_AUTHORITY.json"
        if extra:
            extra_path.write_text('{"artifact_type":"USER_MERGE_AUTHORIZATION"}', encoding="utf-8")
        elif extra_path.exists():
            extra_path.unlink()
        fx.git(self.transport_work, "add", "-A")
        self.transport_count += 1
        fx.git(self.transport_work, "commit", "-qm", f"transport-{self.transport_count}")
        commit = fx.git(self.transport_work, "rev-parse", "HEAD")
        fx.git(self.transport_work, "push", "-f", "origin", f"HEAD:{self.transport_ref}")
        return commit, data_by_role

    def _locator(self, commit: str, data_by_role: dict[str, bytes]) -> dict:
        fields = {
            "CODEX_HANDOFF_PROJECTION": ("CODEX_HANDOFF_PROJECTION", "projection_digest"),
            "CODEX_EXECUTION_RETURN": ("CODEX_EXECUTION_RETURN", "return_digest"),
            "CODEX_EXECUTION_EVIDENCE_BUNDLE": ("CODEX_EXECUTION_EVIDENCE_BUNDLE", "evidence_bundle_digest"),
            "BRAIN_REVIEW_CAPSULE": ("FIBERED_TASK_CAPSULE", "capsule_digest"),
        }
        entries = []
        for role, data in data_by_role.items():
            artifact_type, digest_field = fields[role]
            value = json.loads(data)
            entries.append({
                "object_role": role, "artifact_type": artifact_type,
                "exact_path": f"current-review/{role}.json", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "semantic_digest_field_name": digest_field, "semantic_digest": value[digest_field],
            })
        locator = {
            "artifact_type": "CURRENT_PR_REVIEW_INPUT_TRANSPORT_LOCATOR", "locator_version": 1, "owner": "TOOL",
            "repository_id": "example/repo", "pr_number": 42, "base_sha": self.base, "source_head_sha": self.head,
            "transport_kind": "CURRENT_PR_REVIEW_INPUT_TRANSPORT", "temporary_ref": self.transport_ref,
            "exact_transport_commit": commit, "retention_policy": "EPHEMERAL_BY_DEFAULT", "cleanup_action": "DELETE_EXACT_TEMPORARY_REF",
            "object_entries": sorted(entries, key=lambda row: row["object_role"]), "locator_digest": None,
        }
        locator["locator_digest"] = core.digest(core.strip_digest(locator, "locator_digest"))
        return locator

    def _reseal(self, locator: dict) -> dict:
        locator["locator_digest"] = core.digest(core.strip_digest(locator, "locator_digest"))
        return locator

    def _run_gate(self, locator: dict, record: dict | None = None) -> subprocess.CompletedProcess[str]:
        body = pathlib.Path(self.td.name) / "body.md"
        body.write_text(review.render_pr_body(record or self.record, transport_locator=locator), encoding="utf-8")
        return subprocess.run([
            sys.executable, str(ROOT / "tools/joyflow_repo_check.py"), "verify-current-pr",
            "--repository", str(self.repo), "--pr-body-file", str(body), "--base-sha", self.base, "--pr-number", "42",
        ], capture_output=True, text=True)

    def _materialize(self, locator: dict):
        self.materialize_count += 1
        return repo_check.materialize_current_review_transport(
            locator, repository=self.repo, destination=pathlib.Path(self.td.name) / f"materialized-{self.materialize_count}",
        )

    def test_external_materialization_passes_existing_verify_pr_without_source_change(self):
        before = repo_check._source_state(self.repo)
        proc = self._run_gate(self.locator)
        after = repo_check._source_state(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["result"], "PASS")
        self.assertEqual(before, after)
        self.assertFalse((self.repo / ".joyflow/current").exists())

    def test_locator_current_pr_identity_mismatches_block(self):
        cases = {"source_head_sha": "0" * 40, "base_sha": "1" * 40, "pr_number": 43}
        for field, value in cases.items():
            with self.subTest(field=field):
                locator = copy.deepcopy(self.locator); locator[field] = value; self._reseal(locator)
                with self.assertRaises(core.JoyflowError):
                    review.validate_current_review_transport_locator(locator, repository=self.repo, current_base_sha=self.base, current_pr_number=42)

    def test_missing_moved_and_wrong_transport_commit_block(self):
        missing = copy.deepcopy(self.locator); missing["temporary_ref"] += "-missing"; self._reseal(missing)
        with self.assertRaises(core.JoyflowError): self._materialize(missing)
        wrong = copy.deepcopy(self.locator); wrong["exact_transport_commit"] = "a" * 40; self._reseal(wrong)
        with self.assertRaises(core.JoyflowError): self._materialize(wrong)
        new_commit, _ = self._commit_values(self.values, extra=True)
        self.assertNotEqual(new_commit, self.commit)
        with self.assertRaises(core.JoyflowError): self._materialize(self.locator)

    def test_path_missing_extra_bytes_sha_digest_and_substitution_block(self):
        mutations = []
        for field, value in (("exact_path", "current-review/missing.json"), ("bytes", 1), ("sha256", "0" * 64), ("semantic_digest", "0" * 64)):
            locator = copy.deepcopy(self.locator); locator["object_entries"][0][field] = value; mutations.append(self._reseal(locator))
        locator = copy.deepcopy(self.locator); locator["object_entries"][0]["artifact_type"] = "CODEX_EXECUTION_RETURN"; mutations.append(self._reseal(locator))
        for locator in mutations:
            with self.subTest(locator=locator["locator_digest"]):
                with self.assertRaises(core.JoyflowError): self._materialize(locator)
        missing_commit, missing_bytes = self._commit_values(self.values, missing_role="BRAIN_REVIEW_CAPSULE")
        missing_locator = self._locator(missing_commit, {**missing_bytes, "BRAIN_REVIEW_CAPSULE": self.object_bytes["BRAIN_REVIEW_CAPSULE"]})
        with self.assertRaises(core.JoyflowError): self._materialize(missing_locator)
        extra_commit, extra_bytes = self._commit_values(self.values, extra=True)
        with self.assertRaises(core.JoyflowError): self._materialize(self._locator(extra_commit, extra_bytes))

    def test_other_task_round_return_head_and_brain_head_revisions_block(self):
        variants = []
        projection = copy.deepcopy(self.projection); projection["task_id"] = "OTHER_TASK"; projection["projection_digest"] = core.digest(core.strip_digest(projection, "projection_digest"))
        variants.append({**self.values, "CODEX_HANDOFF_PROJECTION": projection})
        ret = copy.deepcopy(self.ret); ret["pr_evidence"]["head_sha"] = "2" * 40; ret["return_digest"] = core.digest(core.strip_digest(ret, "return_digest"))
        variants.append({**self.values, "CODEX_EXECUTION_RETURN": ret})
        brain = copy.deepcopy(self.reviewed); brain["active_fibers"]["execution_review"]["payload"]["review_target"]["head_sha"] = "3" * 40
        variants.append({**self.values, "BRAIN_REVIEW_CAPSULE": brain})
        for values in variants:
            commit, data = self._commit_values(values)
            with self.subTest(commit=commit):
                with self.assertRaises(core.JoyflowError): self._materialize(self._locator(commit, data))

    def test_windows_ubuntu_transport_revision_mismatch_blocks(self):
        windows_locator = copy.deepcopy(self.locator)
        new_commit, new_data = self._commit_values(self.values, extra=True)
        ubuntu_locator = self._locator(new_commit, new_data)
        self.assertNotEqual(windows_locator["locator_digest"], ubuntu_locator["locator_digest"])
        with self.assertRaises(core.JoyflowError): self._materialize(windows_locator)

    def test_transport_commit_self_reference_is_rejected(self):
        exact = "4" * 40
        data = json.dumps({"artifact_type": "CODEX_HANDOFF_PROJECTION", "projection_digest": exact}).encode()
        entry = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "artifact_type": "CODEX_HANDOFF_PROJECTION", "semantic_digest_field_name": "projection_digest", "semantic_digest": exact}
        with self.assertRaisesRegex(core.JoyflowError, "self-reference"):
            repo_check._validate_transport_object("CODEX_HANDOFF_PROJECTION", entry, data, exact)

    def test_exact_terminal_cleanup_deletes_only_unmoved_synthetic_ref(self):
        terminal = {"status": "REJECTED", "evidence_ref": "brain:terminal", "evidence_digest": hashlib.sha256(b"terminal").hexdigest()}
        continuation = core.build_current_review_transport_cleanup_continuation(
            self.projection, self.approved["approval_record"], self.locator, terminal_evidence=terminal,
        )
        continuation_path = pathlib.Path(self.td.name) / "continuation.json"
        continuation_path.write_text(json.dumps(continuation), encoding="utf-8")
        proc = subprocess.run([
            sys.executable, str(ROOT / "tools/joyflow_repo_check.py"), "cleanup-current-review-transport",
            "--repository", str(self.repo), "--continuation", str(continuation_path),
        ], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIsNone(repo_check._resolve_remote_ref(self.repo, str(self.transport_bare), self.transport_ref, required=False))


if __name__ == "__main__":
    unittest.main()
