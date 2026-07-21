#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_bridge  # noqa: E402
import joyflow_common as common  # noqa: E402
import reconcile  # noqa: E402
import route_task  # noqa: E402
import validate_semantic_closure as semantic  # noqa: E402

TASK_ID = "TEST_TASK"


def valid_contract(mode: str = "ACTIVE_TASK"):
    return {
        "artifact_type": "DUAL_LAYER_TRANSLATION_CONTRACT",
        "artifact_version": "1",
        "task_id": TASK_ID,
        "deterministic_intent": "Maintain product behavior without changing authentication.",
        "lifecycle_mode": mode,
        "product_meaning_ref": semantic.MEANING_PATH,
        "meaning_delta_ref": semantic.DELTA_PATH,
        "user_acceptance_plan_ref": semantic.ACCEPTANCE_PATH,
        "golden_case_refs": ["GC1"],
        "deviation_default": "BRAIN_REVIEW_REQUIRED",
        "lean_interpretation_embedded": False,
        "lean_eligibility": {
            "low_risk": False,
            "known_paths": True,
            "technical_only_or_precisely_bounded": True,
            "no_product_meaning_change": False,
            "no_user_flow_change": False,
            "no_data_meaning_change": True,
            "no_shared_state_change": False,
            "exact_expected_result": True,
            "basis": "non-lean",
        },
        "human_semantic_layer": {
            "objective": "objective",
            "expected_user_result": "result",
            "user_flow": ["flow"],
            "business_rules": ["rule"],
            "accepted_tradeoffs": ["tradeoff"],
            "non_goals": ["non goal"],
            "correct_examples": ["correct"],
            "incorrect_examples": ["incorrect"],
        },
        "mechanical_execution_layer": {
            "must_preserve": ["preserve"],
            "allowed_solution_surfaces": ["scripts/"],
            "forbidden_consequences": ["forbidden"],
            "required_outcomes": ["outcome"],
            "allowed_technical_freedom": ["freedom"],
            "stop_conditions": ["stop"],
            "evidence_requirements": ["evidence"],
        },
        "allowed_paths": ["scripts/"],
        "risk_level": "medium",
        "risk_surfaces": [],
    }


def interpretation(origin="CODEX_EXECUTION_RETURN", status="ALIGNED"):
    return {
        "artifact_type": "CODEX_EXECUTION_INTERPRETATION",
        "artifact_version": "1",
        "task_id": TASK_ID,
        "artifact_origin": origin,
        "objective_understood": "objective",
        "user_visible_result": "result",
        "user_flow_understood": ["flow"],
        "must_preserve": ["preserve"],
        "intended_solution_surface": ["scripts/"],
        "excluded_changes": ["excluded"],
        "golden_cases_understood": ["GC1"],
        "unresolved_items": [],
        "interpretation_status": status,
        "deviation_route": "BRAIN_REVIEW_REQUIRED",
        "brain_alignment_status": "ALIGNED_CONFIRMED",
        "brain_alignment_ref": "brain-review-ref",
    }


class AntiDriftRepairTests(unittest.TestCase):
    def test_keyword_matching_does_not_match_substrings(self):
        self.assertEqual([], common.keyword_hits("product authority authorized workflow", ["prod", "auth", "authorize"]))
        self.assertEqual(["prod"], common.keyword_hits("deploy to prod", ["prod"]))
        self.assertEqual(["auth"], common.keyword_hits("change auth flow", ["auth"]))

    def test_routing_risk_surface_excludes_negative_examples(self):
        contract = valid_contract()
        contract["human_semantic_layer"]["non_goals"] = ["Do not add payment or authentication"]
        text = common.lower_join(route_task.routing_risk_surface(contract))
        self.assertNotIn("payment", text)
        self.assertNotIn("authentication", text)

    def test_dot_paths_are_preserved(self):
        self.assertEqual(".github/workflows/x.yml", common.normalize_path(".github/workflows/x.yml"))
        self.assertEqual(".gitignore", common.normalize_path("./.gitignore"))
        self.assertEqual(".codex/rules.md", common.normalize_path(".codex\\rules.md"))

    def test_unsafe_paths_are_rejected(self):
        for value in ["../x", "/tmp/x", "C:/tmp/x"]:
            with self.assertRaises(ValueError):
                common.normalize_path(value)

    def test_reference_fixture_cannot_release_active_execution(self):
        fixture = interpretation("PROTOCOL_REPAIR_REFERENCE_FIXTURE")
        fixture["not_codex_execution_evidence"] = True
        self.assertFalse(semantic.interpretation_is_authentic_execution_return(fixture))
        self.assertFalse(semantic.execution_release_allowed(valid_contract(), fixture))

    def test_authentic_reviewed_codex_return_releases_active_task(self):
        self.assertTrue(semantic.execution_release_allowed(valid_contract(), interpretation()))

    def test_reference_candidate_never_releases(self):
        self.assertFalse(semantic.execution_release_allowed(valid_contract("REFERENCE_CANDIDATE"), interpretation()))

    def test_lean_requires_all_facts_and_embedded_origin(self):
        contract = valid_contract()
        contract["lean_interpretation_embedded"] = True
        contract["lean_eligibility"] = {field: True for field in semantic.LEAN_REQUIRED_TRUE_FIELDS}
        contract["lean_eligibility"]["basis"] = "all facts proven"
        embedded = interpretation("CONTRACT_EMBEDDED_LEAN")
        embedded.pop("brain_alignment_status")
        embedded.pop("brain_alignment_ref")
        contract["embedded_codex_interpretation"] = embedded
        self.assertTrue(semantic.lean_interpretation_allowed(contract))
        contract["lean_eligibility"]["no_shared_state_change"] = False
        self.assertFalse(semantic.lean_interpretation_allowed(contract))

    def test_executor_outputs_exclude_brain_and_human_receipts(self):
        protected = set(build_bridge.BRAIN_ONLY_OUTPUTS + build_bridge.HUMAN_ONLY_OUTPUTS)
        self.assertFalse(set(build_bridge.EXECUTOR_WRITABLE_OUTPUTS) & protected)
        self.assertNotIn("observer/brain_semantic_review.json", build_bridge.EXECUTOR_WRITABLE_OUTPUTS)
        self.assertNotIn("observer/acceptance_receipt.json", build_bridge.EXECUTOR_WRITABLE_OUTPUTS)

    def test_hard_stop_and_halt_always_block_closure(self):
        blockers = reconcile.execution_state_blockers(
            {"lifecycle_mode": "ACTIVE_TASK"},
            {"target_lane": "HARD_STOP_LANE", "execution_allowed": False},
            "# Packet\n\nHALT\n",
        )
        self.assertIn("HARD_STOP task cannot close", blockers)
        self.assertIn("execution was not released", blockers)
        self.assertIn("execution packet is HALT", blockers)

    def test_reference_candidate_always_blocks_closure(self):
        blockers = reconcile.execution_state_blockers(
            {"lifecycle_mode": "REFERENCE_CANDIDATE"},
            {"target_lane": "HARD_STOP_LANE", "execution_allowed": False},
            "# Packet\n\nHALT\n",
        )
        self.assertTrue(any("reference candidate" in item for item in blockers))

    def test_changed_files_include_committed_base_to_head_diff(self):
        old_root = common.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "base.txt").write_text("base\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "base"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "checkout", "-b", "feature"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
            (repo / "committed.txt").write_text("changed\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "change"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
            common.ROOT = repo
            try:
                ok, files, error = common.changed_files()
            finally:
                common.ROOT = old_root
            self.assertTrue(ok, error)
            self.assertIn("committed.txt", files)

    def test_reviewed_source_head_is_derived_by_stripping_consecutive_evidence_commits(self):
        old_root = common.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "source.py").write_text("source\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "source"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
            source_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            (repo / "observer").mkdir()
            for name in ["brain_semantic_review.json", "pr_receipt.json"]:
                (repo / "observer" / name).write_text("{}\n")
                subprocess.run(["git", "add", "."], cwd=repo, check=True)
                subprocess.run(["git", "commit", "-m", name], cwd=repo, check=True, stdout=subprocess.DEVNULL)
            common.ROOT = repo
            try:
                ok, derived, commits, error = common.derive_reviewed_source_head()
            finally:
                common.ROOT = old_root
            self.assertTrue(ok, error)
            self.assertEqual(source_head, derived)
            self.assertEqual(2, len(commits))

    def test_evidence_only_suffix_accepts_observer_evidence_and_rejects_source_changes(self):
        old_root = common.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "source.py").write_text("source\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "source"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
            source_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            (repo / "observer").mkdir()
            (repo / "observer" / "brain_semantic_review.json").write_text("{}\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "evidence"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
            common.ROOT = repo
            try:
                ok, files, violations, error = common.evidence_suffix_status(source_head)
                self.assertTrue(ok, (files, violations, error))
                self.assertEqual(["observer/brain_semantic_review.json"], files)
                (repo / "source.py").write_text("changed\n")
                subprocess.run(["git", "add", "."], cwd=repo, check=True)
                subprocess.run(["git", "commit", "-m", "source-after-review"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
                ok, files, violations, error = common.evidence_suffix_status(source_head)
                self.assertFalse(ok)
                self.assertIn("source.py", violations)
            finally:
                common.ROOT = old_root


if __name__ == "__main__":
    unittest.main()
