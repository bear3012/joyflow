#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
from collections.abc import Iterator

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
import joyflow_dual_layer as core  # noqa: E402
import joyflow_phase1_review as review  # noqa: E402


def _argument(argv: list[str], flag: str) -> str:
    if flag not in argv or argv.index(flag) + 1 >= len(argv):
        raise core.JoyflowError(f"{flag} is required")
    return argv[argv.index(flag) + 1]


def _git(repo: pathlib.Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if check and proc.returncode != 0:
        raise core.JoyflowError(proc.stderr.decode("utf-8", "replace").strip() or f"git {' '.join(args)} failed")
    return proc


def _source_state(repo: pathlib.Path) -> dict[str, object]:
    return {
        "head": _git(repo, "rev-parse", "HEAD").stdout.decode().strip(),
        "status": _git(repo, "status", "--porcelain=v1", "--untracked-files=all").stdout.decode("utf-8", "replace"),
        "tracked_paths": _git(repo, "ls-files", "-z").stdout.split(b"\0"),
    }


def _transport_remote(repo: pathlib.Path) -> str:
    configured = _git(repo, "config", "--get", "joyflow.currentReviewTransportRemote", check=False)
    return configured.stdout.decode().strip() if configured.returncode == 0 and configured.stdout.strip() else "origin"


def _resolve_remote_ref(repo: pathlib.Path, remote: str, temporary_ref: str, *, required: bool = True) -> str | None:
    proc = _git(repo, "ls-remote", "--exit-code", remote, temporary_ref, check=False)
    if proc.returncode == 2 and not required:
        return None
    if proc.returncode != 0:
        raise core.JoyflowError("current review transport temporary ref is missing or unreadable")
    rows = [line.split() for line in proc.stdout.decode().splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) != 2 or rows[0][1] != temporary_ref:
        raise core.JoyflowError("current review transport temporary ref did not resolve uniquely")
    return rows[0][0]


def _validate_transport_object(role: str, entry: dict[str, object], data: bytes, exact_commit: str) -> dict[str, object]:
    if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
        raise core.JoyflowError(f"current review transport bytes or SHA-256 mismatch: {role}")
    if exact_commit.encode("ascii") in data:
        raise core.JoyflowError("current review transport object reintroduces transport-commit self-reference")
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise core.JoyflowError(f"current review transport object is not UTF-8 JSON: {role}") from exc
    if not isinstance(value, dict) or value.get("artifact_type") != entry["artifact_type"]:
        raise core.JoyflowError(f"current review transport object substitution detected: {role}")
    digest_field = str(entry["semantic_digest_field_name"])
    digest_payload = core.capsule_payload(value) if role == "BRAIN_REVIEW_CAPSULE" else core.strip_digest(value, digest_field)
    if value.get(digest_field) != entry["semantic_digest"] or core.digest(digest_payload) != entry["semantic_digest"]:
        raise core.JoyflowError(f"current review transport semantic digest mismatch: {role}")
    return value


def _validate_current_review_object_chain(values: dict[str, dict[str, object]], locator: dict[str, object]) -> None:
    projection = values["CODEX_HANDOFF_PROJECTION"]
    codex_return = values["CODEX_EXECUTION_RETURN"]
    evidence = values["CODEX_EXECUTION_EVIDENCE_BUNDLE"]
    brain = values["BRAIN_REVIEW_CAPSULE"]
    identity = {key: projection.get(key) for key in ("project_id", "task_id", "round_id")}
    for role, value in (("Return", codex_return), ("Evidence Bundle", evidence)):
        if any(value.get(key) != expected for key, expected in identity.items()):
            raise core.JoyflowError(f"current review {role} belongs to another project/task/round")
    if codex_return.get("projection_digest") != projection.get("projection_digest") or evidence.get("projection_digest") != projection.get("projection_digest"):
        raise core.JoyflowError("current review Return or Evidence Bundle belongs to another Projection")
    if codex_return.get("evidence_bundle_digest") != evidence.get("evidence_bundle_digest"):
        raise core.JoyflowError("current review Return belongs to another Evidence Bundle")
    pr_evidence = core._repository_review_evidence(codex_return) or {}
    if pr_evidence.get("head_sha") != locator.get("source_head_sha") or pr_evidence.get("base_commit") != locator.get("base_sha"):
        raise core.JoyflowError("current review Return belongs to another source Head")
    review_payload = brain.get("active_fibers", {}).get("execution_review", {}).get("payload", {})
    review_target = review_payload.get("review_target") or {}
    expected_review = {
        "source_projection_digest": projection.get("projection_digest"),
        "source_codex_return_digest": codex_return.get("return_digest"),
        "source_evidence_bundle_digest": evidence.get("evidence_bundle_digest"),
    }
    if any(review_payload.get(key) != expected for key, expected in expected_review.items()) or review_target.get("head_sha") != locator.get("source_head_sha"):
        raise core.JoyflowError("current Brain Review belongs to another source Head or lifecycle object chain")


def materialize_current_review_transport(
    locator: dict[str, object], *, repository: pathlib.Path, destination: pathlib.Path,
) -> dict[str, pathlib.Path]:
    before = _source_state(repository)
    try:
        entries = review.validate_current_review_transport_locator(
            locator,
            repository=repository,
            current_base_sha=str(locator["base_sha"]),
            current_pr_number=int(locator["pr_number"]),
        )
        remote = _transport_remote(repository)
        current_ref_commit = _resolve_remote_ref(repository, remote, str(locator["temporary_ref"]))
        exact_commit = str(locator["exact_transport_commit"])
        if current_ref_commit != exact_commit:
            raise core.JoyflowError("current review transport temporary ref moved away from the locator commit")
        _git(repository, "fetch", "--no-tags", "--no-write-fetch-head", remote, str(locator["temporary_ref"]))
        resolved = _git(repository, "rev-parse", f"{exact_commit}^{{commit}}").stdout.decode().strip()
        if resolved != exact_commit:
            raise core.JoyflowError("current review transport commit could not be resolved exactly")
        tree_paths = [row for row in _git(repository, "ls-tree", "-r", "--name-only", exact_commit).stdout.decode("utf-8", "strict").splitlines() if row]
        declared_paths = sorted(str(entry["exact_path"]) for entry in entries.values())
        if sorted(tree_paths) != declared_paths:
            raise core.JoyflowError("current review transport commit must contain exactly the four declared lifecycle objects")

        destination.mkdir(parents=True, exist_ok=False)
        materialized: dict[str, pathlib.Path] = {}
        parsed: dict[str, dict[str, object]] = {}
        for role, entry in entries.items():
            data = _git(repository, "show", f"{exact_commit}:{entry['exact_path']}").stdout
            parsed[role] = _validate_transport_object(role, entry, data, exact_commit)
            target = destination / f"{role}.json"
            target.write_bytes(data)
            materialized[role] = target
        _validate_current_review_object_chain(parsed, locator)
        return materialized
    finally:
        if _source_state(repository) != before:
            raise core.JoyflowError("current review transport materialization changed source HEAD, status, or tracked paths")


@contextlib.contextmanager
def _expanded_current_pr(argv: list[str]) -> Iterator[list[str]]:
    if not argv or argv[0] != "verify-current-pr":
        yield argv
        return
    repository = pathlib.Path(_argument(argv, "--repository")).resolve()
    body_path = pathlib.Path(_argument(argv, "--pr-body-file"))
    base_sha = _argument(argv, "--base-sha")
    pr_number = int(_argument(argv, "--pr-number"))
    body = body_path.read_text(encoding="utf-8")
    locator = review.parse_current_review_transport(body)
    review.validate_current_review_transport_locator(
        locator, repository=repository, current_base_sha=base_sha, current_pr_number=pr_number,
    )
    with tempfile.TemporaryDirectory(prefix="joyflow-current-review-") as td:
        destination = pathlib.Path(td) / str(locator["locator_digest"])
        objects = materialize_current_review_transport(locator, repository=repository, destination=destination)
        expanded = ["verify-pr", *argv[1:]]
        for role, (_, _, flag) in review.CURRENT_REVIEW_OBJECTS.items():
            expanded.extend([flag, str(objects[role])])
        yield expanded


def _cleanup_current_review_transport(argv: list[str]) -> int:
    repository = pathlib.Path(_argument(argv, "--repository")).resolve()
    continuation = json.loads(pathlib.Path(_argument(argv, "--continuation")).read_text(encoding="utf-8"))
    core.validate_schema(continuation, core.CURRENT_PR_REVIEW_TRANSPORT_CLEANUP_CONTINUATION_SCHEMA)
    if continuation["continuation_digest"] != core.digest(core.strip_digest(continuation, "continuation_digest")):
        raise core.JoyflowError("current review transport cleanup continuation digest mismatch")
    remote = _transport_remote(repository)
    current = _resolve_remote_ref(repository, remote, continuation["temporary_ref"])
    core.validate_current_review_transport_cleanup_target(continuation, current)
    _git(repository, "push", remote, f":{continuation['temporary_ref']}")
    if _resolve_remote_ref(repository, remote, continuation["temporary_ref"], required=False) is not None:
        raise core.JoyflowError("current review transport ref still exists after cleanup")
    print(json.dumps({"cleanup": "PASS", "deleted_ref": continuation["temporary_ref"], "deleted_commit": current}, sort_keys=True))
    return 0


def main() -> int:
    try:
        argv = sys.argv[1:]
        if argv and argv[0] == "cleanup-current-review-transport":
            return _cleanup_current_review_transport(argv)
        with _expanded_current_pr(argv) as expanded:
            sys.argv = [sys.argv[0], *expanded]
            return review.main()
    except (core.JoyflowError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"mechanical_gate": "FAIL", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
