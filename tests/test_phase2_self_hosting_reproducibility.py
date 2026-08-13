from __future__ import annotations

import contextlib
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


canonical = load_module("joyflow_canonical_text", ROOT / "tools/canonical_text.py")
capture_tool = load_module("joyflow_capture_execution_evidence", ROOT / "tools/capture_execution_evidence.py")
repo_check = load_module("joyflow_repo_check", ROOT / "tools/joyflow_repo_check.py")


class Phase2SelfHostingReproducibilityTests(unittest.TestCase):
    def test_canonical_text_writer_is_utf8_lf_no_bom(self):
        with tempfile.TemporaryDirectory() as td:
            target = pathlib.Path(td) / "generated.md"
            canonical.write_canonical_text(target, "标题\nline\n")
            data = target.read_bytes()
            self.assertEqual(data, "标题\nline\n".encode("utf-8"))
            self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
            self.assertNotIn(b"\r", data)
            with self.assertRaises(ValueError):
                canonical.write_canonical_text(target, "bad\r\n")

    def test_raw_capture_digest_distinguishes_lossy_utf8_collision(self):
        common = dict(capture_id="CAP", capture_kind="TEST_COMMAND", command="example", exit_code=0, stderr=b"", observed_object={"object_type":"ARTIFACT","source_mode":"EXISTING_ARTIFACT","object_id":"x","ref_or_sha256":"0"*64}, observation={"argv":["example"],"cwd_scope":"SOURCE_ROOT","target_ref":"0"*64}, subject_type="VALIDATION_CHECK", subject_id="CHECK")
        first = capture_tool.build_capture(stdout=b"\xff", **common)
        second = capture_tool.build_capture(stdout=b"\xfe", **common)
        self.assertEqual(first["stdout"], second["stdout"])
        self.assertNotEqual(first["stdout_sha256"], second["stdout_sha256"])
        self.assertNotEqual(first["capture_sha256"], second["capture_sha256"])

    def test_current_pr_public_entry_uses_separate_transport_locator_not_source_paths(self):
        source = pathlib.Path(repo_check.__file__).read_text(encoding="utf-8")
        self.assertIn("parse_current_review_transport", source)
        self.assertIn("TemporaryDirectory", source)
        self.assertNotIn(".joyflow/current/", source)
        self.assertNotIn("--merged-change-projection", source)

    def test_current_pr_public_entry_blocks_when_transport_locator_is_missing(self):
        with self.assertRaisesRegex(repo_check.core.JoyflowError, "exactly one current review transport"):
            repo_check.review.parse_current_review_transport("ordinary PR body")

    def test_workflow_uses_existing_current_pr_entry_and_dependency_contract(self):
        workflow = (ROOT / ".github/workflows/joyflow-pr-mechanical.yml").read_text(encoding="utf-8")
        self.assertIn("actions/setup-python@v5", workflow)
        self.assertIn("requirements-validation.txt", workflow)
        self.assertIn("tools/joyflow_repo_check.py verify-current-pr", workflow)
        self.assertNotIn("--merged-change-projection .joyflow/current", workflow)

    def test_validation_dependency_contract_matches_reference_environment(self):
        lines = [line.strip() for line in (ROOT / "requirements-validation.txt").read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
        self.assertEqual(lines, ["PyYAML==6.0.3", "jsonschema==4.26.0"])
        self.assertEqual(importlib.metadata.version("PyYAML"), "6.0.3")
        self.assertEqual(importlib.metadata.version("jsonschema"), "4.26.0")

    def test_phase2_scope_is_structured_projection_not_prose_identity_gate(self):
        scope = (ROOT / "PHASE2_SCOPE_AND_STATUS.md").read_text(encoding="utf-8")
        validator = (ROOT / "tools/validate_package.py").read_text(encoding="utf-8")
        facts = {}
        for line in scope.splitlines():
            if ":" in line and not line.lstrip().startswith("#"):
                key, value = line.split(":", 1)
                if key.strip() and " " not in key.strip(): facts[key.strip()] = value.strip()
        manifest = json.loads((ROOT / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
        lineage = json.loads((ROOT / "PHASE2_STAGE_LINEAGE.json").read_text(encoding="utf-8"))
        self.assertEqual(facts["current_candidate"], manifest["package_name"])
        self.assertEqual(facts["current_candidate"], lineage["package_name"])
        self.assertEqual(facts["status"], "CANDIDATE_NOT_BASELINE")
        self.assertNotIn("cumulative Phase 2 repair candidate", validator)


if __name__ == "__main__": unittest.main()
