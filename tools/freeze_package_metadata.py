#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
from typing import Iterable

METADATA_FILES = ("PACKAGE_MANIFEST.json", "SHA256SUMS.txt", "VALIDATION_REPORT.json")
METADATA_SET = set(METADATA_FILES)


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: pathlib.Path, *args: str) -> bytes:
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def repo_root(start: pathlib.Path) -> pathlib.Path:
    out = subprocess.run(["git", "-C", str(start), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("package freeze requires a Git repository")
    return pathlib.Path(out.stdout.strip()).resolve()


def clean_source_commit(root: pathlib.Path, source_commit: str) -> str:
    resolved = git(root, "rev-parse", "--verify", f"{source_commit}^{{commit}}").decode().strip()
    if resolved != source_commit:
        raise RuntimeError("source commit must be an exact full commit SHA")
    return resolved


def tracked_paths(root: pathlib.Path, source_commit: str) -> list[str]:
    raw = git(root, "ls-tree", "-r", "--name-only", "-z", source_commit)
    paths = [p.decode("utf-8") for p in raw.split(b"\0") if p]
    if len(paths) != len(set(paths)):
        raise RuntimeError("duplicate tracked path")
    return sorted(paths)


def source_file_bytes(root: pathlib.Path, source_commit: str, path: str) -> bytes:
    return git(root, "show", f"{source_commit}:{path}")


def load_lineage(root: pathlib.Path, source_commit: str) -> dict[str, object]:
    raw = source_file_bytes(root, source_commit, "PHASE2_STAGE_LINEAGE.json")
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("PHASE2_STAGE_LINEAGE.json is not valid UTF-8 JSON") from exc
    if value.get("artifact_type") != "PHASE2_STAGE_LINEAGE":
        raise RuntimeError("Phase 2 lineage identity mismatch")
    if not isinstance(value.get("package_name"), str) or not value["package_name"]:
        raise RuntimeError("Phase 2 lineage package name missing")
    if value.get("status") != "CANDIDATE_NOT_BASELINE":
        raise RuntimeError("Phase 2 lineage status mismatch")
    if not isinstance(value.get("parent_package"), dict):
        raise RuntimeError("Phase 2 lineage parent package missing")
    return value


def build_payload_rows(root: pathlib.Path, source_commit: str, paths: Iterable[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(paths):
        if path in METADATA_SET:
            continue
        data = source_file_bytes(root, source_commit, path)
        rows.append({"path": path, "bytes": len(data), "sha256": sha256_bytes(data)})
    return rows


def build_manifest(lineage: dict[str, object], rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "artifact_type": "JOYFLOW_PACKAGE_MANIFEST",
        "manifest_version": 1,
        "package_name": lineage["package_name"],
        "artifact_status": "PHASE2_REPAIR_CANDIDATE_NOT_BASELINE",
        "repair_source_package": lineage["parent_package"],
        "integrity_metadata_files": list(METADATA_FILES),
        "payload_file_count": len(rows),
        "payload_files": rows,
    }


def build_validation_report(lineage: dict[str, object], source_commit: str, rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "artifact_type": "JOYFLOW_VALIDATION_REPORT",
        "candidate_package_name": lineage["package_name"],
        "candidate_status": "CANDIDATE_NOT_BASELINE",
        "stage_id": lineage.get("stage_id"),
        "report_status": "PACKAGE_CURRENTNESS_FROZEN_VALIDATION_REQUIRED",
        "current_repair": "DETERMINISTIC_PACKAGE_CURRENTNESS_FREEZE",
        "current_source_object": source_commit,
        "package_currentness_freeze": {
            "generator": "tools/freeze_package_metadata.py",
            "source_commit": source_commit,
            "payload_file_count": len(rows),
            "integrity_metadata_files": list(METADATA_FILES),
            "source_payload_basis": "EXACT_GIT_TREE_EXCLUDING_INTEGRITY_METADATA",
            "metadata_authority": "NONE_GENERATOR_IS_MECHANISM_ONLY",
            "post_freeze_validation": "REQUIRED",
        },
        "lifecycle_state": {
            "brain_review_pass": "NOT_CLAIMED",
            "user_acceptance": "NOT_OCCURRED",
            "final_merge_authorization": "NOT_GRANTED",
            "stable_baseline": "NO",
        },
    }


def build_sha_file(root: pathlib.Path, source_commit: str, paths: list[str], manifest_bytes: bytes, report_bytes: bytes) -> bytes:
    virtual = {
        "PACKAGE_MANIFEST.json": manifest_bytes,
        "VALIDATION_REPORT.json": report_bytes,
    }
    names = sorted((set(paths) - {"SHA256SUMS.txt"}) | {"PACKAGE_MANIFEST.json", "VALIDATION_REPORT.json"})
    lines: list[str] = []
    for path in names:
        if path in virtual:
            data = virtual[path]
        elif path in METADATA_SET:
            raise RuntimeError(f"unexpected integrity metadata path: {path}")
        else:
            data = source_file_bytes(root, source_commit, path)
        lines.append(f"{sha256_bytes(data)}  {path}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_outputs(root: pathlib.Path, source_commit: str) -> dict[str, bytes]:
    source_commit = clean_source_commit(root, source_commit)
    paths = tracked_paths(root, source_commit)
    missing = [name for name in ("PHASE2_STAGE_LINEAGE.json", *METADATA_FILES) if name not in paths]
    if missing:
        raise RuntimeError(f"required tracked package files missing: {missing}")
    lineage = load_lineage(root, source_commit)
    rows = build_payload_rows(root, source_commit, paths)
    manifest = canonical_json_bytes(build_manifest(lineage, rows))
    report = canonical_json_bytes(build_validation_report(lineage, source_commit, rows))
    sums = build_sha_file(root, source_commit, paths, manifest, report)
    return {
        "PACKAGE_MANIFEST.json": manifest,
        "VALIDATION_REPORT.json": report,
        "SHA256SUMS.txt": sums,
    }


def write_outputs(outputs: dict[str, bytes], output_dir: pathlib.Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in METADATA_FILES:
        (output_dir / name).write_bytes(outputs[name])


def _git_diff_quiet(root: pathlib.Path, *prefix: str) -> bool:
    proc = subprocess.run(
        [
            "git", "-C", str(root), "diff", "--quiet", *prefix, "--", ".",
            ":(exclude)PACKAGE_MANIFEST.json", ":(exclude)SHA256SUMS.txt", ":(exclude)VALIDATION_REPORT.json",
        ]
    )
    return proc.returncode == 0


def source_payload_matches(root: pathlib.Path, source_commit: str) -> bool:
    head = git(root, "rev-parse", "HEAD").decode().strip()
    if not _git_diff_quiet(root, source_commit, head):
        return False
    if not _git_diff_quiet(root):
        return False
    if not _git_diff_quiet(root, "--cached"):
        return False
    return True


def check_existing(root: pathlib.Path) -> None:
    try:
        report = json.loads((root / "VALIDATION_REPORT.json").read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("existing VALIDATION_REPORT.json is unreadable") from exc
    source_commit = report.get("current_source_object")
    if not isinstance(source_commit, str) or len(source_commit) != 40:
        raise RuntimeError("validation report current_source_object missing")
    clean_source_commit(root, source_commit)
    if not source_payload_matches(root, source_commit):
        raise RuntimeError("current tracked non-metadata payload differs from frozen source commit")
    expected = build_outputs(root, source_commit)
    bad = [name for name, data in expected.items() if not (root / name).is_file() or (root / name).read_bytes() != data]
    if bad:
        raise RuntimeError("package metadata drift: " + ", ".join(bad))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", default=".")
    parser.add_argument("--source-commit")
    parser.add_argument("--output-dir")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = repo_root(pathlib.Path(args.repository).resolve())
    if args.check:
        if args.source_commit or args.output_dir:
            parser.error("--check cannot be combined with --source-commit/--output-dir")
        check_existing(root)
        print("PASS package_currentness_freeze_check")
        return 0
    if not args.source_commit or not args.output_dir:
        parser.error("write/preview mode requires --source-commit and --output-dir")
    outputs = build_outputs(root, args.source_commit)
    write_outputs(outputs, pathlib.Path(args.output_dir).resolve())
    print(f"PASS package_currentness_freeze files={len(outputs)} source_commit={args.source_commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
