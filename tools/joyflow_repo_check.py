#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator

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


class CurrentReviewPublicationError(core.JoyflowError):
    def __init__(self, message: str, *, partial_state: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.partial_state = partial_state or {}


def _transport_plan(projection: dict[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    core.validate_current_review_transport_plan(projection)
    plan = projection.get("delivery", {}).get("current_review_transport") or {}
    if plan.get("mode") != "GITHUB_EXACT_OBJECT_IF_NEEDED":
        raise core.JoyflowError("current review publication requires the Projection-bound GitHub exact-object transport mode")
    surface = plan.get("github_surface") or {}
    return plan, surface


def _transport_paths(projection: dict[str, object]) -> dict[str, str]:
    _, surface = _transport_plan(projection)
    prefix = str(surface["path_prefix"]).rstrip("/")
    paths = {role: f"{prefix}/{role}.json" for role in review.CURRENT_REVIEW_OBJECTS}
    if len(set(paths.values())) != len(paths) or any(not core._valid_repo_path(path) for path in paths.values()):
        raise core.JoyflowError("current review transport plan produces invalid or duplicate object paths")
    return paths


def _lifecycle_values(
    projection: dict[str, object], codex_return: dict[str, object], evidence_bundle: dict[str, object], brain_review_capsule: dict[str, object],
) -> dict[str, dict[str, object]]:
    return {
        "CODEX_HANDOFF_PROJECTION": projection,
        "CODEX_EXECUTION_RETURN": codex_return,
        "CODEX_EXECUTION_EVIDENCE_BUNDLE": evidence_bundle,
        "BRAIN_REVIEW_CAPSULE": brain_review_capsule,
    }


def create_current_review_transport(
    projection: dict[str, object],
    codex_return: dict[str, object],
    evidence_bundle: dict[str, object],
    brain_review_capsule: dict[str, object],
    *,
    repository: pathlib.Path,
    staging_root: pathlib.Path,
) -> tuple[str, pathlib.Path]:
    """Create and publish an exact four-object transport from an isolated Git repository."""
    before = _source_state(repository)
    plan, surface = _transport_plan(projection)
    paths = _transport_paths(projection)
    values = _lifecycle_values(projection, codex_return, evidence_bundle, brain_review_capsule)
    if set(values) != set(review.CURRENT_REVIEW_OBJECTS):
        raise core.JoyflowError("current review transport input set differs from the exact four required roles")
    transport_repo = staging_root / "transport-work"
    transport_repo.mkdir(parents=True, exist_ok=False)
    _git(transport_repo, "init", "-q")
    _git(transport_repo, "config", "user.name", "Joyflow Current Review Publisher")
    _git(transport_repo, "config", "user.email", "joyflow-current-review@invalid.local")
    for role in sorted(values):
        target = transport_repo / paths[role]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(core.canonical_bytes(values[role]))
    _git(transport_repo, "add", "--", *sorted(paths.values()))
    env = os.environ.copy()
    env.update({
        "GIT_AUTHOR_NAME": "Joyflow Current Review Publisher",
        "GIT_AUTHOR_EMAIL": "joyflow-current-review@invalid.local",
        "GIT_COMMITTER_NAME": "Joyflow Current Review Publisher",
        "GIT_COMMITTER_EMAIL": "joyflow-current-review@invalid.local",
    })
    proc = subprocess.run(
        ["git", "-C", str(transport_repo), "commit", "-qm", "Joyflow current-review transport"],
        capture_output=True,
        env=env,
    )
    if proc.returncode != 0:
        raise core.JoyflowError(proc.stderr.decode("utf-8", "replace").strip() or "current review transport commit creation failed")
    commit = _git(transport_repo, "rev-parse", "HEAD").stdout.decode().strip()
    source_head = _git(repository, "rev-parse", "HEAD").stdout.decode().strip()
    if commit == source_head:
        raise core.JoyflowError("current review transport commit must be distinct from the product source Head")
    tree_paths = sorted(_git(transport_repo, "ls-tree", "-r", "--name-only", commit).stdout.decode().splitlines())
    if tree_paths != sorted(paths.values()):
        raise core.JoyflowError("current review transport commit does not contain exactly the four declared paths")
    for role, (artifact_type, digest_field, _) in review.CURRENT_REVIEW_OBJECTS.items():
        data = _git(transport_repo, "show", f"{commit}:{paths[role]}").stdout
        value = values[role]
        entry = {
            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "artifact_type": artifact_type, "semantic_digest_field_name": digest_field,
            "semantic_digest": value.get(digest_field),
        }
        _validate_transport_object(role, entry, data, commit)
    remote = _transport_remote(repository)
    _git(transport_repo, "remote", "add", "transport", remote)
    push = _git(transport_repo, "push", "transport", f"{commit}:{surface['temporary_ref']}", check=False)
    if push.returncode != 0:
        raise CurrentReviewPublicationError(
            push.stderr.decode("utf-8", "replace").strip() or "current review temporary ref publication failed",
            partial_state={"temporary_ref": surface["temporary_ref"], "transport_commit": None, "remote_mutation": False},
        )
    resolved = _resolve_remote_ref(repository, remote, str(surface["temporary_ref"]))
    if resolved != commit:
        raise CurrentReviewPublicationError(
            "published current review ref does not resolve to the exact transport commit",
            partial_state={"temporary_ref": surface["temporary_ref"], "transport_commit": commit, "remote_mutation": True},
        )
    if _source_state(repository) != before:
        raise CurrentReviewPublicationError(
            "current review transport publication changed source HEAD, status, or tracked paths",
            partial_state={"temporary_ref": surface["temporary_ref"], "transport_commit": commit, "remote_mutation": True},
        )
    return commit, transport_repo


def construct_current_review_transport_locator(
    projection: dict[str, object],
    *,
    repository: pathlib.Path,
    current_base_sha: str,
    current_pr_number: int,
    transport_repository: pathlib.Path,
    exact_transport_commit: str,
) -> dict[str, object]:
    """Construct a locator solely from the Projection plan and observed transport bytes/ref."""
    plan, surface = _transport_plan(projection)
    remote = _transport_remote(repository)
    resolved = _resolve_remote_ref(repository, remote, str(surface["temporary_ref"]))
    if resolved != exact_transport_commit:
        raise core.JoyflowError("current review transport ref moved before locator construction")
    paths = _transport_paths(projection)
    tree_paths = sorted(_git(transport_repository, "ls-tree", "-r", "--name-only", exact_transport_commit).stdout.decode().splitlines())
    if tree_paths != sorted(paths.values()):
        raise core.JoyflowError("current review locator source commit does not contain exactly four declared objects")
    entries = []
    for role, (artifact_type, digest_field, _) in review.CURRENT_REVIEW_OBJECTS.items():
        data = _git(transport_repository, "show", f"{exact_transport_commit}:{paths[role]}").stdout
        try:
            value = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise core.JoyflowError(f"current review transport object is not UTF-8 JSON: {role}") from exc
        entry = {
            "object_role": role,
            "artifact_type": artifact_type,
            "exact_path": paths[role],
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "semantic_digest_field_name": digest_field,
            "semantic_digest": value.get(digest_field),
        }
        _validate_transport_object(role, entry, data, exact_transport_commit)
        entries.append(entry)
    _, repository_id, source_head = review._canonical_repo(repository)
    locator = {
        "artifact_type": "CURRENT_PR_REVIEW_INPUT_TRANSPORT_LOCATOR",
        "locator_version": 1,
        "owner": "TOOL",
        "repository_id": repository_id,
        "pr_number": current_pr_number,
        "base_sha": current_base_sha,
        "source_head_sha": source_head,
        "transport_kind": "CURRENT_PR_REVIEW_INPUT_TRANSPORT",
        "temporary_ref": surface["temporary_ref"],
        "exact_transport_commit": exact_transport_commit,
        "retention_policy": plan["retention_policy"],
        "cleanup_action": plan["cleanup"]["action"],
        "object_entries": sorted(entries, key=lambda row: row["object_role"]),
        "locator_digest": None,
    }
    locator["locator_digest"] = core.digest(core.strip_digest(locator, "locator_digest"))
    review.validate_current_review_transport_locator(
        locator, repository=repository, current_base_sha=current_base_sha, current_pr_number=current_pr_number,
    )
    return locator


def publish_current_review(
    *,
    repository: pathlib.Path,
    existing_pr_body: str,
    projection: dict[str, object],
    codex_return: dict[str, object],
    evidence_bundle: dict[str, object],
    brain_review_capsule: dict[str, object],
    current_base_sha: str,
    current_pr_number: int,
    pr_body_publisher: Callable[[str], None] | None = None,
) -> dict[str, object]:
    """Publish one validated current-review chain; PR-body publication, when supplied, is last."""
    before = _source_state(repository)
    partial: dict[str, object] = {"temporary_ref": None, "transport_commit": None, "remote_mutation": False, "pr_body_mutation": False}
    try:
        record = review.construct_pr_record(
            repository=repository,
            projection=projection,
            codex_return=codex_return,
            evidence_bundle=evidence_bundle,
            brain_review_capsule=brain_review_capsule,
            current_base_sha=current_base_sha,
            current_pr_number=current_pr_number,
            replay_tests=True,
        )
        with tempfile.TemporaryDirectory(prefix="joyflow-current-review-publish-") as td:
            staging_root = pathlib.Path(td)
            commit, transport_repo = create_current_review_transport(
                projection, codex_return, evidence_bundle, brain_review_capsule,
                repository=repository, staging_root=staging_root,
            )
            _, surface = _transport_plan(projection)
            partial.update({"temporary_ref": surface["temporary_ref"], "transport_commit": commit, "remote_mutation": True})
            locator = construct_current_review_transport_locator(
                projection,
                repository=repository,
                current_base_sha=current_base_sha,
                current_pr_number=current_pr_number,
                transport_repository=transport_repo,
                exact_transport_commit=commit,
            )
            materialized = materialize_current_review_transport(
                locator, repository=repository, destination=staging_root / "readback" / str(locator["locator_digest"]),
            )
            values = _lifecycle_values(projection, codex_return, evidence_bundle, brain_review_capsule)
            for role, path in materialized.items():
                if json.loads(path.read_text(encoding="utf-8")) != values[role]:
                    raise core.JoyflowError(f"current review readback differs from source lifecycle object: {role}")
            updated_body = review.update_pr_body(existing_pr_body, locator, record)
            if review.parse_current_review_transport(updated_body) != locator or review.parse_pr_body(updated_body) != record:
                raise core.JoyflowError("updated PR body failed managed-object round trip")
            if _source_state(repository) != before:
                raise core.JoyflowError("current review publication changed source HEAD, status, or tracked paths")
            if pr_body_publisher is not None:
                partial["pr_body_mutation"] = "ATTEMPTED"
                pr_body_publisher(updated_body)
                partial["pr_body_mutation"] = True
            return {
                "publication_status": "PASS",
                "source_head_sha": locator["source_head_sha"],
                "transport_commit": commit,
                "temporary_ref": locator["temporary_ref"],
                "locator": locator,
                "pr_record": record,
                "updated_pr_body": updated_body,
                "object_count": len(locator["object_entries"]),
                "source_state_unchanged": True,
                "pr_body_published": pr_body_publisher is not None,
            }
    except CurrentReviewPublicationError:
        raise
    except (core.JoyflowError, OSError, ValueError, json.JSONDecodeError) as exc:
        raise CurrentReviewPublicationError(str(exc), partial_state=partial) from exc


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


def _publish_current_review_command(argv: list[str]) -> int:
    repository = pathlib.Path(_argument(argv, "--repository")).resolve()
    current_pr_number = int(_argument(argv, "--pr-number"))
    github_repository = _argument(argv, "--github-repository") if "--github-repository" in argv else None

    def publish_body(body: str) -> None:
        if github_repository is None:
            raise core.JoyflowError("--publish-pr-body requires --github-repository")
        payload = json.dumps({"body": body}, ensure_ascii=False).encode("utf-8")
        proc = subprocess.run(
            ["gh", "api", "--method", "PATCH", f"repos/{github_repository}/pulls/{current_pr_number}", "--input", "-"],
            input=payload,
            capture_output=True,
        )
        if proc.returncode != 0:
            raise core.JoyflowError(proc.stderr.decode("utf-8", "replace").strip() or "GitHub PR body publication failed")
        try:
            observed = json.loads(proc.stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise core.JoyflowError("GitHub PR body publication returned invalid JSON") from exc
        if observed.get("body") != body:
            raise core.JoyflowError("GitHub PR body readback differs from the exact published body")

    try:
        result = publish_current_review(
            repository=repository,
            existing_pr_body=pathlib.Path(_argument(argv, "--pr-body-file")).read_text(encoding="utf-8"),
            projection=core.load_json(_argument(argv, "--projection")),
            codex_return=core.load_json(_argument(argv, "--codex-return")),
            evidence_bundle=core.load_json(_argument(argv, "--evidence-bundle")),
            brain_review_capsule=core.load_json(_argument(argv, "--brain-review-capsule")),
            current_base_sha=_argument(argv, "--base-sha"),
            current_pr_number=current_pr_number,
            pr_body_publisher=publish_body if "--publish-pr-body" in argv else None,
        )
        pathlib.Path(_argument(argv, "--updated-pr-body-output")).write_text(str(result.pop("updated_pr_body")), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except CurrentReviewPublicationError as exc:
        print(json.dumps({
            "publication_status": "BLOCK",
            "error": str(exc),
            "partial_state": exc.partial_state,
        }, ensure_ascii=False, sort_keys=True))
        return 2


def main() -> int:
    try:
        argv = sys.argv[1:]
        if argv == ["--help"]:
            print("usage: joyflow_repo_check.py {verify-current-pr,publish-current-review,cleanup-current-review-transport} ...")
            return 0
        if argv and argv[0] == "cleanup-current-review-transport":
            return _cleanup_current_review_transport(argv)
        if argv and argv[0] == "publish-current-review":
            return _publish_current_review_command(argv)
        with _expanded_current_pr(argv) as expanded:
            sys.argv = [sys.argv[0], *expanded]
            return review.main()
    except (core.JoyflowError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"mechanical_gate": "FAIL", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
