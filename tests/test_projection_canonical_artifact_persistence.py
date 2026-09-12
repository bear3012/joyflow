import json
import pathlib
import tempfile
import unittest

from tests import build_fixture as fixture
from runtime import joyflow_dual_layer as compiler


class ProjectionCanonicalArtifactPersistenceTests(unittest.TestCase):
    def test_projection_persistence_exists_and_round_trips_exact_digest(self):
        projection = compiler.build_projection(fixture.at_user_approval())
        with tempfile.TemporaryDirectory() as td:
            target = pathlib.Path(td) / "CODEX_HANDOFF_PROJECTION.json"
            persisted_path = compiler.persist_projection_artifact(projection, target)

            self.assertEqual(persisted_path, target)
            self.assertTrue(target.is_file())
            self.assertNotIn(b"\r", target.read_bytes())
            persisted = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(persisted, projection)
            self.assertEqual(
                persisted["projection_digest"],
                compiler.digest(compiler.projection_payload(persisted)),
            )

    def test_projection_artifact_adds_no_authority(self):
        projection = compiler.build_projection(fixture.at_user_approval())
        with tempfile.TemporaryDirectory() as td:
            target = pathlib.Path(td) / "CODEX_HANDOFF_PROJECTION.json"
            compiler.persist_projection_artifact(projection, target)
            persisted = compiler.load_json(target)

        forbidden_authority_objects = {
            "approval_record",
            "approval_permission",
            "automatic_execution_permission",
            "merge_gate_record",
            "merge_permission",
            "user_merge_authorization",
        }
        self.assertTrue(forbidden_authority_objects.isdisjoint(persisted))
        static_authority_flags = {
            "candidate_is_not_canonical",
            "merge_requires_separate_user_decision",
            "automatic_promotion_forbidden",
        }
        self.assertTrue(static_authority_flags.isdisjoint(persisted["delivery"]))
        with self.assertRaises(compiler.JoyflowError):
            compiler.validate_promotion_gate()

    def test_invalid_projection_is_not_persisted(self):
        projection = compiler.build_projection(fixture.at_user_approval())
        projection["projection_digest"] = "0" * 64
        with tempfile.TemporaryDirectory() as td:
            target = pathlib.Path(td) / "CODEX_HANDOFF_PROJECTION.json"
            with self.assertRaises(compiler.JoyflowError):
                compiler.persist_projection_artifact(projection, target)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
