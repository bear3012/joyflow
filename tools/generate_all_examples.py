#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run_generators(root: pathlib.Path) -> None:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for cmd in (
        [sys.executable, str(root / "tools/generate_mechanical_assets.py")],
        [sys.executable, str(root / "tools/generate_old_rule_migration.py")],
        [sys.executable, str(root / "tests/build_fixture.py")],
        [sys.executable, str(root / "tools/generate_phase1_review_examples.py")],
    ):
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, env=env)
        if proc.returncode != 0:
            raise RuntimeError((proc.stdout + proc.stderr).strip() or f"generator failed: {cmd}")


def generated_paths(root: pathlib.Path) -> set[pathlib.Path]:
    paths = {p.relative_to(root) for p in (root / "examples").rglob("*") if p.is_file()}
    paths.add(pathlib.Path("tests/fixture_task_capsule_unsealed.json"))
    paths.update({
        pathlib.Path("OLD_RULE_MIGRATION.json"),
        pathlib.Path("OLD_RULE_MIGRATION.md"),
        pathlib.Path("CAPABILITY_STATUS.json"),
        pathlib.Path("machine/verification_registry.json"),
        pathlib.Path("schemas/legacy_rule_migration.schema.json"),
        pathlib.Path("schemas/migration_verification_registry.schema.json"),
        pathlib.Path("schemas/candidate_capability_status.schema.json"),
        pathlib.Path("schemas/legacy_source_set.schema.json"),
        pathlib.Path("schemas/brain_legacy_semantic_mapping.schema.json"),
        pathlib.Path("schemas/legacy_disposition_decisions.schema.json"),
        pathlib.Path("machine/legacy_disposition_decisions_v1_7_6.json"),
        pathlib.Path("machine/legacy_disposition_decisions_seal.json"),
        pathlib.Path("schemas/capability_claim_registry.schema.json"),
        pathlib.Path("schemas/brain_capsule_semantic_manifest.schema.json"),
        pathlib.Path("schemas/fibered_task_capsule.schema.json"),
        pathlib.Path("schemas/codex_handoff_projection.schema.json"),
        pathlib.Path("schemas/approval_view.schema.json"),
        pathlib.Path("schemas/codex_execution_return.schema.json"),
        pathlib.Path("schemas/codex_execution_evidence_bundle.schema.json"),
        pathlib.Path("schemas/path_discovery_return.schema.json"),
        pathlib.Path("schemas/github_path_evidence.schema.json"),
        pathlib.Path("schemas/final_path_decision.schema.json"),
        pathlib.Path("schemas/merge_gate_record.schema.json"),
        pathlib.Path("schemas/task_completion_pointer.schema.json"),
        pathlib.Path("project_sources/03_GENERATED_DUAL_LAYER_REGISTRY.md"),
        pathlib.Path("project_sources/12_GENERATED_RULE_INDEX.md"),
    })
    return paths


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    try:
        if not args.check:
            run_generators(ROOT)
            print(f"PASS unified_example_generation files={len(generated_paths(ROOT))}")
            return 0
        with tempfile.TemporaryDirectory(prefix="joyflow-example-check-") as td:
            clone = pathlib.Path(td) / "package"
            shutil.copytree(ROOT, clone, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            run_generators(clone)
            current = generated_paths(ROOT)
            regenerated = generated_paths(clone)
            if current != regenerated:
                missing = sorted(str(p) for p in regenerated - current)
                unexpected = sorted(str(p) for p in current - regenerated)
                raise RuntimeError(f"generated example set drift missing={missing} unexpected={unexpected}")
            drift = [str(p) for p in sorted(current) if (ROOT / p).read_bytes() != (clone / p).read_bytes()]
            if drift:
                raise RuntimeError("generated example byte drift: " + ", ".join(drift))
        print(f"PASS unified_example_generation_check files={len(current)}")
        return 0
    except (OSError, RuntimeError) as exc:
        print(f"UNIFIED_EXAMPLE_GENERATION_BLOCK: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
