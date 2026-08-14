from __future__ import annotations

import copy
import hashlib
import pathlib
import subprocess
import unittest

from tests import build_fixture as fixture

c = fixture.c
ROOT = pathlib.Path(__file__).resolve().parents[1]


def manifest_from_capsule(capsule: dict, *, capsule_id: str | None = None) -> dict:
    anchor = copy.deepcopy(capsule["task_anchor"])
    anchor.pop("anchor_digest", None)
    progress = copy.deepcopy(capsule["task_progress"])
    progress.pop("previous_stage", None)
    progress.pop("parent_capsule_digest", None)
    progress["transition_event"].pop("from_stage", None)
    progress["transition_event"].pop("to_stage", None)
    fibers = {}
    for name, fiber in capsule["active_fibers"].items():
        payload = copy.deepcopy(fiber["payload"])
        if name == "semantic":
            for item in payload["semantic_items"]:
                item.pop("meaning_digest", None)
                for effect in item["effects"]:
                    effect.pop("effect_digest", None)
        fibers[name] = {"status": fiber["status"], "payload": payload}
    evidence = copy.deepcopy(capsule["evidence_registry"])
    for row in evidence:
        row.pop("claim_digest", None)
    return {
        "artifact_type": "BRAIN_CAPSULE_SEMANTIC_MANIFEST",
        "manifest_version": 1,
        "capsule_id": capsule_id or capsule["capsule_id"],
        "task_anchor": anchor,
        "task_progress": progress,
        "route_profile": capsule["route_profile"],
        "task_classification": copy.deepcopy(capsule["task_classification"]),
        "active_fibers": fibers,
        "evidence_registry": evidence,
        "refs": copy.deepcopy(capsule["refs"]),
        "unresolved_blockers": copy.deepcopy(capsule["unresolved_blockers"]),
        "approval_state": "NEEDS_USER_APPROVAL",
        "stop_conditions": copy.deepcopy(capsule["stop_conditions"]),
    }


def next_manifest(previous: dict, stage: str, revision: int) -> dict:
    manifest = manifest_from_capsule(previous, capsule_id=f"{previous['capsule_id']}_R{revision}")
    manifest["task_progress"] = {
        "stage": stage,
        "cycle": previous["task_progress"]["cycle"],
        "cycle_trigger": "NONE",
        "transition_event": {
            "event_id": f"EVENT_R{revision}",
            "event_type": "ADVANCE_STAGE",
            "changed_anchor_fields": [],
            "added_fibers": [],
            "changed_fibers": [],
            "removed_fibers": [],
            "evidence_refs": [previous["evidence_registry"][0]["evidence_id"]],
            "reason": f"Advance the exact current task to {stage}.",
        },
    }
    return manifest


def replay_manifest(paths: list[str]) -> dict:
    manifest = manifest_from_capsule(fixture.new_capsule("DEVELOPMENT_STRICT", "REPOSITORY_CHANGE"))
    old_anchor = manifest["task_anchor"]["repository_anchor"]
    base = old_anchor["baseline_commit"]
    binding = manifest["active_fibers"]["decision_boundary"]["payload"]["repository_binding"]
    manifest["task_anchor"]["repository_operation"] = "EXISTING_FROZEN_PR_REPLAY"
    manifest["task_anchor"]["repository_anchor"] = {
        "repository_id": old_anchor["repository_id"], "baseline_commit": base,
        "pr_number": 4, "pr_url": "https://github.com/example/repo/pull/4",
        "base_branch": binding["default_branch"], "working_branch": binding["working_branch"],
        "frozen_head_sha": "b" * 40, "review_coverage_paths": paths,
    }
    final = manifest["active_fibers"]["repository_evidence"]["payload"]["path_discovery"]["final_path_decision"]
    final["allowed_path_items"] = []
    final["decision_digest"] = c.digest(c.strip_digest(final, "decision_digest"))
    for item in manifest["active_fibers"]["semantic"]["payload"]["semantic_items"]:
        item["effects"] = [effect for effect in item["effects"] if effect["effect_type"] != "ALLOW_PATH"]
    for route in manifest["active_fibers"]["decision_boundary"]["payload"]["technical_route_space"]["candidate_routes"]:
        route["expected_paths"] = []
    return manifest


def real_stage_c_replay_manifest() -> tuple[dict, list[str]]:
    base = "fabbfbc4be3adf3b873e76312cf925c2d7edc7cb"
    head = "0279941677631a1cc5bf1ea3a26589ac9e23fd7f"
    paths = sorted(subprocess.run(["git", "diff", "--name-only", "--no-renames", base, head], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines())
    manifest = replay_manifest(paths)
    manifest["task_anchor"]["repository_anchor"].update({
        "repository_id": "bear3012/joyflow", "baseline_commit": base,
        "pr_url": "https://github.com/bear3012/joyflow/pull/4",
        "base_branch": "main", "working_branch": "agent/r6-stable-baseline-integration",
        "frozen_head_sha": head,
    })
    repository = manifest["active_fibers"]["repository_evidence"]["payload"]
    repository["baseline_commit"] = base
    final = repository["path_discovery"]["final_path_decision"]
    final.update({"repository_id": "bear3012/joyflow", "baseline_commit": base})
    final["decision_digest"] = c.digest(c.strip_digest(final, "decision_digest"))
    binding = manifest["active_fibers"]["decision_boundary"]["payload"]["repository_binding"]
    binding.update({"repository_id": "bear3012/joyflow", "expected_base_commit": base, "default_branch": "main", "working_branch": "agent/r6-stable-baseline-integration"})
    path_state = repository["path_discovery"]
    row = path_state["github_path_evidence"][0]
    row["repository_id"] = "bear3012/joyflow"
    row["object_ref"] = f"github:bear3012/joyflow@{base}"
    row["observed_commit_or_head"] = base
    row["raw_evidence_ref"] = f"github:bear3012/joyflow@{base}:path-discovery"
    row["scope"]["raw_object_sha256"] = hashlib.sha256(c.canonical_bytes(c._github_source_capture_payload(row, ROOT))).hexdigest()
    row["scope"]["scope_digest"] = c.digest(c._github_scope_payload(row))
    row["evidence_digest"] = c.digest(c.strip_digest(row, "evidence_digest"))
    path_state["github_ref"] = f"github:bear3012/joyflow@{base}"
    evidence = next(item for item in manifest["evidence_registry"] if item["evidence_id"] == "E_GITHUB_PATHS")
    evidence.update({"ref": row["raw_evidence_ref"], "claim": c._github_scope_claim(row), "subject_id": row["object_ref"], "raw_output_ref": row["raw_evidence_ref"], "raw_output_sha256": row["scope"]["raw_object_sha256"]})
    return manifest, paths


class BrainCapsuleSemanticManifestCompilerTests(unittest.TestCase):
    def initial_manifest(self, route: str = "DEVELOPMENT_STANDARD") -> dict:
        return manifest_from_capsule(fixture.new_capsule(route, "REPOSITORY_CHANGE"))

    def approval_chain(self) -> tuple[dict, dict, dict]:
        first = c.build_capsule_from_brain_manifest(self.initial_manifest())
        second = c.build_capsule_from_brain_manifest(next_manifest(first, "DECISION_CLOSURE", 2), first)
        third = c.build_capsule_from_brain_manifest(next_manifest(second, "USER_APPROVAL", 3), second)
        return first, second, third

    def test_complete_manifest_compiles_capsule_projection_and_view(self):
        _, _, capsule = self.approval_chain()
        projection, view, binding = c.draft_handoff(capsule)
        self.assertEqual(projection["capsule_digest"], capsule["capsule_digest"])
        self.assertIn("# JOYFLOW USER MUTATION APPROVAL VIEW", view)
        self.assertEqual(binding, c.approval_binding(projection))

    def test_missing_brain_owned_field_blocks_without_guessing(self):
        manifest = self.initial_manifest()
        del manifest["task_anchor"]["goal"]
        with self.assertRaisesRegex(c.JoyflowError, "schema validation failed"):
            c.build_capsule_from_brain_manifest(manifest)

    def test_empty_allowed_paths_stay_empty(self):
        manifest = replay_manifest(["runtime/joyflow_dual_layer.py"])
        capsule = c.build_capsule_from_brain_manifest(manifest)
        self.assertEqual(c._allow_paths(capsule), [])
        self.assertEqual(capsule["active_fibers"]["repository_evidence"]["payload"]["path_discovery"]["final_path_decision"]["allowed_path_items"], [])

    def test_goal_non_goals_and_effects_are_lossless(self):
        manifest = self.initial_manifest()
        capsule = c.build_capsule_from_brain_manifest(manifest)
        self.assertEqual(capsule["task_anchor"]["goal"], manifest["task_anchor"]["goal"])
        self.assertEqual(capsule["task_anchor"]["non_goals"], manifest["task_anchor"]["non_goals"])
        actual = capsule["active_fibers"]["semantic"]["payload"]["semantic_items"]
        expected = manifest["active_fibers"]["semantic"]["payload"]["semantic_items"]
        for left, right in zip(actual, expected, strict=True):
            self.assertEqual(left["meaning"], right["meaning"])
            self.assertEqual([(x["effect_id"], x["effect_type"], x["value"]) for x in left["effects"]], [(x["effect_id"], x["effect_type"], x["value"]) for x in right["effects"]])

    def test_lifecycle_parent_digests_are_exact(self):
        first, second, third = self.approval_chain()
        self.assertEqual(second["task_progress"]["parent_capsule_digest"], first["capsule_digest"])
        self.assertEqual(third["task_progress"]["parent_capsule_digest"], second["capsule_digest"])
        self.assertEqual([first["task_progress"]["stage"], second["task_progress"]["stage"], third["task_progress"]["stage"]], ["INTENT_DISCUSSION", "DECISION_CLOSURE", "USER_APPROVAL"])

    def test_compiler_cannot_create_approved_final(self):
        manifest = self.initial_manifest()
        manifest["approval_state"] = "APPROVED_FINAL"
        with self.assertRaises(c.JoyflowError):
            c.build_capsule_from_brain_manifest(manifest)
        _, _, capsule = self.approval_chain()
        self.assertEqual(capsule["approval_record"]["status"], "NEEDS_USER_APPROVAL")

    def test_compilation_is_deterministic(self):
        manifest = self.initial_manifest()
        left = c.build_capsule_from_brain_manifest(copy.deepcopy(manifest))
        right = c.build_capsule_from_brain_manifest(copy.deepcopy(manifest))
        self.assertEqual(left["capsule_digest"], right["capsule_digest"])
        lp, lv, _ = c.draft_handoff(c.build_capsule_from_brain_manifest(next_manifest(c.build_capsule_from_brain_manifest(next_manifest(left, "DECISION_CLOSURE", 2), left), "USER_APPROVAL", 3), c.build_capsule_from_brain_manifest(next_manifest(left, "DECISION_CLOSURE", 2), left)))
        rp, rv, _ = c.draft_handoff(c.build_capsule_from_brain_manifest(next_manifest(c.build_capsule_from_brain_manifest(next_manifest(right, "DECISION_CLOSURE", 2), right), "USER_APPROVAL", 3), c.build_capsule_from_brain_manifest(next_manifest(right, "DECISION_CLOSURE", 2), right)))
        self.assertEqual(lp["projection_digest"], rp["projection_digest"])
        self.assertEqual(hashlib.sha256(lv.encode()).hexdigest(), hashlib.sha256(rv.encode()).hexdigest())

    def test_existing_frozen_pr_replay_manifest_preserves_review_coverage(self):
        manifest, paths = real_stage_c_replay_manifest()
        capsule = c.build_capsule_from_brain_manifest(manifest)
        self.assertEqual(len(paths), 231)
        self.assertEqual(c.digest(paths), "6e451ca17c677cfe1bedbfce3f62761613ee5f475b35d74f5cbfb98b815d98c4")
        self.assertEqual(capsule["task_anchor"]["repository_anchor"]["review_coverage_paths"], paths)
        self.assertEqual(c._allow_paths(capsule), [])
        decision = c.build_capsule_from_brain_manifest(next_manifest(capsule, "DECISION_CLOSURE", 2), capsule)
        approval = c.build_capsule_from_brain_manifest(next_manifest(decision, "USER_APPROVAL", 3), decision)
        projection, view, _ = c.draft_handoff(approval)
        self.assertEqual(projection["current_source_context"]["review_coverage_paths"], paths)
        self.assertEqual(projection["current_source_context"]["current_product_mutation_paths"], [])
        self.assertIn("# JOYFLOW USER MATERIAL EXECUTION APPROVAL VIEW", view)
        self.assertNotIn("# JOYFLOW USER MUTATION APPROVAL VIEW", view)
        self.assertNotIn("Local Codex may adapt implementation details, debug, refactor locally", view)

    def test_production_runtime_does_not_import_test_fixture(self):
        source = (ROOT / "runtime/joyflow_dual_layer.py").read_text(encoding="utf-8")
        self.assertNotIn("tests.build_fixture", source)

    def test_current_round_repository_change_still_compiles(self):
        manifest = self.initial_manifest("DEVELOPMENT_STANDARD")
        capsule = c.build_capsule_from_brain_manifest(manifest)
        self.assertEqual(capsule["task_anchor"]["repository_operation"], "CURRENT_ROUND_REPOSITORY_CHANGE")


if __name__ == "__main__":
    unittest.main()
