from __future__ import annotations

import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "runtime"))
sys.path.insert(0, str(ROOT / "tools"))

import phase1_review_fixture as fx  # noqa: E402
import joyflow_dual_layer as core  # noqa: E402
import joyflow_phase1_review as review  # noqa: E402
import joyflow_repo_check as publisher  # noqa: E402


def current_review_plan() -> dict:
    return {
        "mode": "GITHUB_EXACT_OBJECT_IF_NEEDED",
        "transport_role": "CURRENT_PR_REVIEW_INPUT_TRANSPORT",
        "github_surface": {
            "repository_id": "example/repo",
            "temporary_ref": "refs/heads/joyflow-evidence/current-review/publication-test",
            "path_prefix": "current-review/publication-test/",
            "side_effect_status": "NONE",
            "side_effect_basis": "Isolated current-review publication test has no product side effect.",
        },
        "retention_policy": "EPHEMERAL_BY_DEFAULT",
        "retention_reason": None,
        "cleanup": {
            "trigger": "TASK_TERMINAL",
            "action": "DELETE_EXACT_TEMPORARY_REF",
            "preauthorized": True,
            "background_service_forbidden": True,
        },
        "fallback_mode": "MANUAL_FALLBACK",
        "product_pr_promotion_forbidden": True,
        "product_main_or_development_branch_forbidden": True,
    }


class CurrentReviewPublicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.td, self.repo, self.base, self.head = fx.create_repository()
        self.approved, self.projection, _, _ = fx.repository_replay_approved_projection(
            self.repo, self.base, self.head, current_review_transport_plan=current_review_plan()
        )
        executing = fx.f.advance(self.approved, "CODEX_EXECUTION")
        self.codex_return, self.evidence_bundle = fx.repository_return_bundle(
            self.projection, self.repo, self.base, self.head
        )
        reviewing = fx.f.brain_review_capsule(executing, self.projection, self.codex_return, self.evidence_bundle)
        self.brain_review = fx.f.revise_review(reviewing, "BRAIN_REVIEW", brain_verdict="PASS")
        self.remote = pathlib.Path(self.td.name) / "transport.git"
        subprocess.run(["git", "init", "--bare", str(self.remote)], check=True, capture_output=True)
        fx.git(self.repo, "config", "joyflow.currentReviewTransportRemote", str(self.remote))
        self.original_body = "Historical PR context.\n\nThis text is not Joyflow-managed."

    def tearDown(self) -> None:
        self.td.cleanup()

    def publish(self, **overrides):
        args = {
            "repository": self.repo,
            "existing_pr_body": self.original_body,
            "projection": self.projection,
            "codex_return": self.codex_return,
            "evidence_bundle": self.evidence_bundle,
            "brain_review_capsule": self.brain_review,
            "current_base_sha": self.base,
            "current_pr_number": 42,
        }
        args.update(overrides)
        return publisher.publish_current_review(**args)

    def test_production_publisher_round_trips_exact_chain_and_gate(self):
        before = publisher._source_state(self.repo)
        result = self.publish()
        after = publisher._source_state(self.repo)
        self.assertEqual(result["publication_status"], "PASS")
        self.assertEqual(result["object_count"], 4)
        self.assertEqual(before, after)
        self.assertIn(self.original_body, result["updated_pr_body"])
        self.assertEqual(result["updated_pr_body"].count(review.TRANSPORT_BEGIN), 1)
        self.assertEqual(result["updated_pr_body"].count(review.BEGIN), 1)
        tree = subprocess.run(
            ["git", "--git-dir", str(self.remote), "ls-tree", "-r", "--name-only", result["transport_commit"]],
            check=True, capture_output=True, text=True,
        ).stdout.splitlines()
        self.assertEqual(sorted(tree), sorted(row["exact_path"] for row in result["locator"]["object_entries"]))
        self.assertEqual(set(row["object_role"] for row in result["locator"]["object_entries"]), set(review.CURRENT_REVIEW_OBJECTS))
        self.assertNotIn("user_acceptance", result)
        self.assertNotIn("merge_authorization", result)
        self.assertNotIn("stable_baseline", result)
        self.assertEqual(
            result["pr_record"]["brain_block"]["execution_binding"]["approved_allowed_paths"],
            [row["path"] for row in self.projection["repository_evidence"]["path_discovery"]["final_path_decision"]["allowed_path_items"]],
        )
        body = pathlib.Path(self.td.name) / "body.md"
        body.write_text(result["updated_pr_body"], encoding="utf-8")
        proc = subprocess.run([
            sys.executable, str(ROOT / "tools/joyflow_repo_check.py"), "verify-current-pr",
            "--repository", str(self.repo), "--pr-body-file", str(body),
            "--base-sha", self.base, "--pr-number", "42",
        ], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["result"], "PASS")

    def test_pr_body_update_is_bounded_idempotent_and_preserves_history(self):
        result = self.publish()
        updated = result["updated_pr_body"]
        self.assertIn(self.original_body, updated)
        self.assertEqual(review.update_pr_body(updated, result["locator"], result["pr_record"]), updated)
        corrupt = updated.replace('"locator_version": 1', '"locator_version": 2', 1)
        with self.assertRaises(core.JoyflowError):
            review.update_pr_body(corrupt, result["locator"], result["pr_record"])

    def test_duplicate_or_malformed_managed_blocks_block(self):
        result = self.publish()
        duplicate = result["updated_pr_body"] + "\n" + review.render_current_review_transport(result["locator"])
        with self.assertRaisesRegex(core.JoyflowError, "duplicate or malformed"):
            review.update_pr_body(duplicate, result["locator"], result["pr_record"])
        malformed = self.original_body + "\n" + review.BEGIN
        with self.assertRaisesRegex(core.JoyflowError, "duplicate or malformed"):
            review.update_pr_body(malformed, result["locator"], result["pr_record"])

    def test_pr_record_constructor_rejects_wrong_base_pr_and_stale_projection(self):
        cases = [
            {"current_base_sha": "0" * 40},
            {"current_pr_number": 43},
            {"projection": {**self.projection, "projection_digest": "0" * 64}},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                args = {
                    "repository": self.repo,
                    "projection": self.projection,
                    "codex_return": self.codex_return,
                    "evidence_bundle": self.evidence_bundle,
                    "brain_review_capsule": self.brain_review,
                    "current_base_sha": self.base,
                    "current_pr_number": 42,
                    "replay_tests": False,
                }
                args.update(changes)
                with self.assertRaises(core.JoyflowError):
                    review.construct_pr_record(**args)

    def test_publisher_rejects_mismatched_return_and_does_not_create_ref(self):
        wrong = copy.deepcopy(self.codex_return)
        wrong["projection_digest"] = "0" * 64
        wrong["return_digest"] = core.digest(core.strip_digest(wrong, "return_digest"))
        with self.assertRaises(core.JoyflowError):
            self.publish(codex_return=wrong)
        self.assertIsNone(publisher._resolve_remote_ref(
            self.repo, str(self.remote), current_review_plan()["github_surface"]["temporary_ref"], required=False,
        ))

    def test_publisher_cannot_promote_pending_brain_review_to_pass(self):
        executing = fx.f.advance(self.approved, "CODEX_EXECUTION")
        pending = fx.f.brain_review_capsule(executing, self.projection, self.codex_return, self.evidence_bundle)
        with self.assertRaises(core.JoyflowError):
            self.publish(brain_review_capsule=pending)
        payload = pending["active_fibers"]["execution_review"]["payload"]
        self.assertNotEqual(payload["brain_review_verdict"], "PASS")

    def test_pr_body_callback_runs_only_after_validated_transport_and_body(self):
        observed = []

        def callback(body: str) -> None:
            ref = publisher._resolve_remote_ref(
                self.repo, str(self.remote), current_review_plan()["github_surface"]["temporary_ref"]
            )
            observed.append((ref, review.parse_current_review_transport(body), review.parse_pr_body(body)))

        result = self.publish(pr_body_publisher=callback)
        self.assertTrue(result["pr_body_published"])
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0][0], result["transport_commit"])
        self.assertEqual(observed[0][1], result["locator"])
        self.assertEqual(observed[0][2], result["pr_record"])

    def test_moved_ref_and_extra_fifth_object_block_after_publication(self):
        result = self.publish()
        work = pathlib.Path(self.td.name) / "tamper"
        subprocess.run(["git", "clone", "-q", str(self.remote), str(work)], check=True, capture_output=True)
        fx.git(work, "config", "user.email", "test@example.com")
        fx.git(work, "config", "user.name", "Joyflow Test")
        fx.git(work, "checkout", "-q", result["transport_commit"])
        extra = work / "current-review/publication-test/EXTRA_AUTHORITY.json"
        extra.write_text('{"artifact_type":"USER_MERGE_AUTHORIZATION"}', encoding="utf-8")
        fx.git(work, "add", ".")
        fx.git(work, "commit", "-qm", "other")
        moved_commit = fx.git(work, "rev-parse", "HEAD")
        fx.git(work, "push", "-f", "origin", f"HEAD:{result['temporary_ref']}")
        with self.assertRaisesRegex(core.JoyflowError, "moved"):
            publisher.materialize_current_review_transport(
                result["locator"], repository=self.repo,
                destination=pathlib.Path(self.td.name) / "moved-readback",
            )
        extra_locator = copy.deepcopy(result["locator"])
        extra_locator["exact_transport_commit"] = moved_commit
        extra_locator["locator_digest"] = core.digest(core.strip_digest(extra_locator, "locator_digest"))
        with self.assertRaisesRegex(core.JoyflowError, "exactly the four"):
            publisher.materialize_current_review_transport(
                extra_locator, repository=self.repo,
                destination=pathlib.Path(self.td.name) / "extra-readback",
            )

    def test_wrong_source_head_and_stale_pr_record_block(self):
        result = self.publish()
        (self.repo / "later.txt").write_text("later\n", encoding="utf-8")
        fx.git(self.repo, "add", "later.txt")
        fx.git(self.repo, "commit", "-qm", "other")
        with self.assertRaises(core.JoyflowError):
            self.publish()
        with self.assertRaisesRegex(core.JoyflowError, "stale"):
            review.validate_pr_record(
                result["pr_record"], repository=self.repo, projection=self.projection,
                codex_return=self.codex_return, evidence_bundle=self.evidence_bundle,
                brain_review_capsule=self.brain_review, current_base_sha=self.base,
                current_pr_number=42, replay_tests=True,
            )

    def test_high_level_cli_publishes_isolated_chain_and_emits_result(self):
        inputs = pathlib.Path(self.td.name) / "inputs"
        inputs.mkdir()
        files = {
            "projection.json": self.projection,
            "return.json": self.codex_return,
            "bundle.json": self.evidence_bundle,
            "brain.json": self.brain_review,
        }
        for name, value in files.items():
            (inputs / name).write_text(json.dumps(value), encoding="utf-8")
        body = inputs / "body.md"
        output = inputs / "updated-body.md"
        body.write_text(self.original_body, encoding="utf-8")
        before = publisher._source_state(self.repo)
        proc = subprocess.run([
            sys.executable, str(ROOT / "tools/joyflow_repo_check.py"), "publish-current-review",
            "--repository", str(self.repo), "--pr-body-file", str(body),
            "--projection", str(inputs / "projection.json"),
            "--codex-return", str(inputs / "return.json"),
            "--evidence-bundle", str(inputs / "bundle.json"),
            "--brain-review-capsule", str(inputs / "brain.json"),
            "--base-sha", self.base, "--pr-number", "42",
            "--updated-pr-body-output", str(output),
        ], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["publication_status"], "PASS")
        self.assertEqual(result["object_count"], 4)
        self.assertTrue(output.is_file())
        self.assertEqual(review.parse_current_review_transport(output.read_text(encoding="utf-8")), result["locator"])
        self.assertEqual(publisher._source_state(self.repo), before)

    def test_locator_identity_comes_from_validated_pr_record(self):
        result = self.publish()
        fake_transport_repo = pathlib.Path(self.td.name) / "not-needed-for-identity-rejection"
        for changes, message in (
            ({"current_pr_number": 43}, "caller PR number"),
            ({"current_base_sha": "0" * 40}, "caller base SHA"),
        ):
            args = {
                "projection": self.projection,
                "repository": self.repo,
                "validated_pr_record": result["pr_record"],
                "current_base_sha": self.base,
                "current_pr_number": 42,
                "transport_repository": fake_transport_repo,
                "exact_transport_commit": result["transport_commit"],
            }
            args.update(changes)
            with self.subTest(changes=changes), self.assertRaisesRegex(core.JoyflowError, message):
                publisher.construct_current_review_transport_locator(**args)

        (self.repo / "later.txt").write_text("later\n", encoding="utf-8")
        fx.git(self.repo, "add", "later.txt")
        fx.git(self.repo, "commit", "-qm", "later")
        with self.assertRaisesRegex(core.JoyflowError, "observed current repository object"):
            publisher.construct_current_review_transport_locator(
                self.projection, repository=self.repo, validated_pr_record=result["pr_record"],
                current_base_sha=self.base, current_pr_number=42,
                transport_repository=fake_transport_repo, exact_transport_commit=result["transport_commit"],
            )

    def test_push_success_then_first_readback_failure_preserves_remote_effect(self):
        with mock.patch.object(publisher, "_resolve_remote_ref", side_effect=core.JoyflowError("readback unavailable")):
            with self.assertRaises(publisher.CurrentReviewPublicationError) as caught:
                self.publish()
        state = caught.exception.partial_state
        self.assertEqual(state["remote_effect"], "PERFORMED")
        self.assertTrue(state["remote_mutation"])
        self.assertFalse(state["remote_verified"])
        self.assertEqual(state["temporary_ref"], current_review_plan()["github_surface"]["temporary_ref"])
        self.assertEqual(state["transport_commit"], state["intended_transport_commit"])
        observed = subprocess.run(
            ["git", "--git-dir", str(self.remote), "rev-parse", state["temporary_ref"]],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        self.assertEqual(observed, state["transport_commit"])

    def test_output_paths_through_authoritative_repository_block_before_publication(self):
        tracked = self.repo / "runtime/joyflow_dual_layer.py"
        traversal = self.repo / "nested" / ".." / "untracked-output.md"
        for output in (self.repo, tracked, self.repo / "untracked-output.md", traversal):
            with self.subTest(output=output), self.assertRaisesRegex(core.JoyflowError, "outside the authoritative repository"):
                self.publish(updated_pr_body_output=output)
            self.assertIsNone(publisher._resolve_remote_ref(
                self.repo, str(self.remote), current_review_plan()["github_surface"]["temporary_ref"], required=False,
            ))

    def test_symlink_output_boundary_and_external_output(self):
        external = pathlib.Path(self.td.name) / "external-output.md"
        before = publisher._source_state(self.repo)
        result = self.publish(updated_pr_body_output=external)
        self.assertTrue(result["updated_pr_body_written"])
        self.assertEqual(external.read_text(encoding="utf-8"), result["updated_pr_body"])
        self.assertEqual(publisher._source_state(self.repo), before)

        link = pathlib.Path(self.td.name) / "link-into-repository"
        try:
            link.symlink_to(self.repo, target_is_directory=True)
        except (OSError, NotImplementedError):
            return
        with self.assertRaisesRegex(core.JoyflowError, "outside the authoritative repository"):
            publisher._external_output_path(self.repo, link / "linked-output.md")

    def test_callback_success_then_output_failure_preserves_pr_mutation_truth(self):
        callback_bodies = []
        output_directory = pathlib.Path(self.td.name) / "output-directory"
        output_directory.mkdir()
        with self.assertRaises(publisher.CurrentReviewPublicationError) as caught:
            self.publish(
                pr_body_publisher=callback_bodies.append,
                updated_pr_body_output=output_directory,
            )
        self.assertEqual(len(callback_bodies), 1)
        self.assertTrue(caught.exception.partial_state["pr_body_mutation"])
        self.assertEqual(caught.exception.partial_state["output_write"], "ATTEMPTED")


if __name__ == "__main__":
    unittest.main()
