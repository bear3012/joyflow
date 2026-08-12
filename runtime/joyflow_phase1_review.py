#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
import joyflow_dual_layer as core  # noqa: E402
import joyflow_phase1_projection as change_projection  # noqa: E402

PR_RECORD_SCHEMA = ROOT / "schemas/pr_record.schema.json"
PR_CI_RESULT_SCHEMA = ROOT / "schemas/pr_ci_result.schema.json"
BEGIN = "<!-- JOYFLOW_PR_RECORD_BEGIN"
END = "JOYFLOW_PR_RECORD_END -->"

JoyflowError = core.JoyflowError


def canonical_bytes(value: Any) -> bytes:
    return core.canonical_bytes(value)


def digest(value: Any) -> str:
    return core.digest(value)


def strip_digest(value: dict[str, Any], field: str) -> dict[str, Any]:
    return core.strip_digest(value, field)


def changed_paths_digest(paths: list[str]) -> str:
    return digest(sorted(set(paths)))


def pr_block_payload(block: dict[str, Any], digest_field: str) -> dict[str, Any]:
    return strip_digest(block, digest_field)


def parse_pr_body(body: str) -> dict[str, Any]:
    if body.count(BEGIN) != 1 or body.count(END) != 1:
        raise JoyflowError("PR body must contain exactly one Joyflow PR record block")
    content = body.split(BEGIN, 1)[1].split(END, 1)[0].strip()
    try:
        value = json.loads(content)
    except json.JSONDecodeError as exc:
        raise JoyflowError(f"PR record JSON invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise JoyflowError("PR record must be one JSON object")
    return value


def render_pr_body(record: dict[str, Any], *, preamble: str = "Joyflow current-object review record.") -> str:
    return f"{preamble}\n\n{BEGIN}\n{json.dumps(record, ensure_ascii=False, indent=2)}\n{END}\n"


def _git(repo: pathlib.Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise JoyflowError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc


def _canonical_repo(repo: str | pathlib.Path) -> tuple[pathlib.Path, str, str]:
    root, repository_id, head = core._repository_source_identity(repo)
    return root, repository_id, head


def _normalized_worktree_blocks(root: pathlib.Path, lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines + [""]:
        if line:
            current.append(line)
            continue
        if not current:
            continue
        normalized: list[str] = []
        for item in current:
            if item.startswith("worktree "):
                raw_path = pathlib.Path(item.removeprefix("worktree ")).resolve()
                normalized.append("worktree PRIMARY" if raw_path == root else "worktree AUXILIARY")
            else:
                normalized.append(item)
        blocks.append(normalized)
        current = []
    return sorted(blocks, key=lambda row: "\n".join(row))

def repository_state_snapshot(repo: str | pathlib.Path) -> dict[str, Any]:
    root, repository_id, head = _canonical_repo(repo)
    refs = _git(root, "for-each-ref", "--format=%(refname)%00%(objectname)").stdout.splitlines()
    status = _git(root, "status", "--porcelain=v2", "--untracked-files=all", "--ignored=matching").stdout.splitlines()
    config = _git(root, "config", "--local", "--list", "--show-origin").stdout.splitlines()
    worktree_lines = _git(root, "worktree", "list", "--porcelain").stdout.splitlines()
    semantic = {
        "repository_id": repository_id,
        "head": head,
        "refs": sorted(refs),
        "status": status,
        "local_config": sorted(config),
        "worktrees": _normalized_worktree_blocks(root, worktree_lines),
    }
    payload = {"root": str(root), **semantic}
    payload["snapshot_digest"] = digest(semantic)
    return payload


def _repository_changed_paths(repo: pathlib.Path, base: str, head: str) -> list[str]:
    core._require_ancestor(repo, base, head)
    raw = _git(repo, "diff", "--name-only", "--no-renames", f"{base}..{head}").stdout
    rows = [x for x in raw.splitlines() if x]
    if len(rows) != len(set(rows)):
        raise JoyflowError("current PR Diff contains duplicate paths")
    for path in rows:
        if not core._valid_repo_path(path):
            raise JoyflowError(f"current PR Diff contains unsafe path: {path}")
    return sorted(rows)


def _final_path_decision(projection: dict[str, Any]) -> dict[str, Any]:
    try:
        row = projection["repository_evidence"]["path_discovery"]["final_path_decision"]
    except (KeyError, TypeError) as exc:
        raise JoyflowError("repository Projection lacks final path decision") from exc
    if not isinstance(row, dict) or not row.get("decision_digest"):
        raise JoyflowError("repository Projection final path decision is incomplete")
    return row


def _approved_paths(projection: dict[str, Any]) -> list[str]:
    decision = _final_path_decision(projection)
    paths = [x["path"] for x in decision["allowed_path_items"]]
    if not paths or len(paths) != len(set(paths)) or any(not core._valid_repo_path(x) for x in paths):
        raise JoyflowError("final path decision contains invalid approved paths")
    return paths


def _approval_binding_digest(projection: dict[str, Any]) -> str:
    return digest(core.approval_binding(projection))


def _review_payload(capsule: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = capsule["active_fibers"]["execution_review"]["payload"]
    except (KeyError, TypeError) as exc:
        raise JoyflowError("Brain review Capsule lacks execution_review payload") from exc
    if not isinstance(payload, dict):
        raise JoyflowError("Brain review payload is invalid")
    return payload


def _expected_codex_evidence_refs(codex_return: dict[str, Any]) -> list[str]:
    refs = [x["evidence_ref"] for x in codex_return.get("machine_results", [])]
    refs += list(codex_return.get("blocker_evidence_refs", []))
    pr = codex_return.get("pr_evidence")
    if pr:
        refs.append(pr["diff_evidence_ref"])
    return sorted(set(refs))


def validate_pr_record(
    record: dict[str, Any],
    *,
    repository: str | pathlib.Path,
    projection: dict[str, Any],
    codex_return: dict[str, Any],
    evidence_bundle: dict[str, Any],
    brain_review_capsule: dict[str, Any],
    merged_change_projection: dict[str, Any] | None = None,
    current_base_sha: str,
    current_pr_number: int,
    replay_tests: bool = False,
) -> dict[str, Any]:
    core.validate_schema(record, PR_RECORD_SCHEMA)
    brain = record["brain_block"]
    codex = record["codex_block"]
    execution = codex["execution"]
    review = brain["brain_review"]
    if brain["brain_block_digest"] != digest(pr_block_payload(brain, "brain_block_digest")):
        raise JoyflowError("PR Brain block digest mismatch")
    if codex["codex_block_digest"] != digest(pr_block_payload(codex, "codex_block_digest")):
        raise JoyflowError("PR Codex block digest mismatch")
    if record["record_digest"] != digest(strip_digest(record, "record_digest")):
        raise JoyflowError("PR record digest mismatch")

    root, repository_id, current_head = _canonical_repo(repository)
    if repository_id != record["repository_id"]:
        raise JoyflowError("PR record repository differs from current repository source")
    if current_pr_number != record["pr_number"]:
        raise JoyflowError("PR record is bound to another pull request")
    if current_base_sha != record["base_sha"]:
        raise JoyflowError("PR record is bound to another current base SHA")
    if current_head != record["head_sha"]:
        raise JoyflowError("PR record is stale for the current repository Head")
    actual_changed_paths = _repository_changed_paths(root, current_base_sha, current_head)

    # Revalidate the exact PR1A/PR1B execution chain against the current source.
    core.validate_codex_execution_return(
        codex_return,
        projection,
        evidence_bundle,
        repository=root,
        replay_tests=replay_tests,
    )
    core.validate_capsule(brain_review_capsule)
    core.validate_review_input_binding(
        brain_review_capsule,
        projection,
        codex_return,
        evidence_bundle,
        source_repository=root,
        replay_tests=replay_tests,
    )

    if projection["execution_object"]["object_type"] != "REPOSITORY":
        raise JoyflowError("PR record requires a repository execution Projection")
    pr = codex_return.get("pr_evidence")
    if not pr:
        raise JoyflowError("PR record requires repository PR evidence from the exact Codex Return")
    expected_pr = {
        "repository_id": repository_id,
        "base_commit": current_base_sha,
        "head_sha": current_head,
        "touched_files": actual_changed_paths,
    }
    if any(pr.get(k) != v for k, v in expected_pr.items()):
        raise JoyflowError("Codex Return PR evidence differs from the current repository Diff")

    decision = _final_path_decision(projection)
    allowed_paths = _approved_paths(projection)
    for path in actual_changed_paths:
        if not any(core._path_within_allowed(path, [allowed]) for allowed in allowed_paths):
            raise JoyflowError(f"current PR Diff path is outside approved final paths: {path}")

    binding = brain["execution_binding"]
    expected_binding = {
        "repository_id": repository_id,
        "project_id": projection["project_id"],
        "task_id": projection["task_id"],
        "round_id": projection["round_id"],
        "expected_base_commit": current_base_sha,
        "current_head_sha": current_head,
        "projection_digest": projection["projection_digest"],
        "final_path_decision_digest": decision["decision_digest"],
        "approval_binding_digest": _approval_binding_digest(projection),
        "approved_allowed_paths": allowed_paths,
    }
    if binding != expected_binding:
        raise JoyflowError("PR Brain execution binding differs from exact current execution objects")

    if codex["source_codex_return_digest"] != codex_return["return_digest"] or codex["source_evidence_bundle_digest"] != evidence_bundle["evidence_bundle_digest"]:
        raise JoyflowError("PR Codex block is not bound to the exact Return and Evidence Bundle")
    if codex["technical_preflight_status"] != codex_return["technical_preflight"]["status"]:
        raise JoyflowError("PR Codex block changed technical preflight status")
    expected_execution = {
        "status": codex_return["execution_status"],
        "checked_base_sha": current_base_sha,
        "checked_head_sha": current_head,
        "actual_changed_paths": actual_changed_paths,
        "actual_changed_paths_digest": changed_paths_digest(actual_changed_paths),
    }
    if any(execution.get(k) != v for k, v in expected_execution.items()):
        raise JoyflowError("PR Codex execution block differs from current repository result")
    if codex["evidence_refs"] != _expected_codex_evidence_refs(codex_return):
        raise JoyflowError("PR Codex evidence refs differ from exact Codex Return")
    if codex_return["execution_status"] == "COMPLETED" and (not codex["local_test_refs"] or codex["unresolved_items"]):
        raise JoyflowError("completed PR Codex block requires tests and no unresolved items")

    review_payload = _review_payload(brain_review_capsule)
    expected_review = {
        "reviewed_head_sha": current_head,
        "source_projection_digest": projection["projection_digest"],
        "source_final_path_decision_digest": decision["decision_digest"],
        "source_codex_return_digest": codex_return["return_digest"],
        "source_evidence_bundle_digest": evidence_bundle["evidence_bundle_digest"],
        "source_codex_block_digest": codex["codex_block_digest"],
        "source_brain_review_capsule_digest": brain_review_capsule["capsule_digest"],
    }
    if any(review.get(k) != v for k, v in expected_review.items()):
        raise JoyflowError("PR Brain review does not bind the exact current review sources")
    if review["status"] != review_payload["brain_review_verdict"]:
        raise JoyflowError("PR Brain review verdict differs from current Brain Review Capsule")
    if review["unresolved_items"] != review_payload["unresolved_followups"]:
        raise JoyflowError("PR Brain review unresolved items differ from current Brain Review Capsule")

    embedded_change_projection = brain["merged_change_projection"]
    if embedded_change_projection is not None:
        raise JoyflowError("pre-merge PR record may not embed a Merged Change Projection")
    if merged_change_projection is not None:
        raise JoyflowError("Merged Change Projection is post-merge navigation context, not a PR review input")

    phase = record["record_phase"]
    if phase == "READY_FOR_USER_DECISION":
        if execution["status"] != "COMPLETED" or review["status"] != "PASS" or review["unresolved_items"] or codex["unresolved_items"]:
            raise JoyflowError("READY_FOR_USER_DECISION is not fully reviewed")
    elif phase == "BRAIN_REVIEWED":
        if execution["status"] != "COMPLETED" or review["status"] not in {"PASS", "RETURN_FOR_REPAIR", "BLOCKED"}:
            raise JoyflowError("BRAIN_REVIEWED phase is inconsistent")
    elif phase == "CODEX_COMPLETE":
        if execution["status"] != "COMPLETED" or review["status"] != "NOT_STARTED":
            raise JoyflowError("CODEX_COMPLETE phase is inconsistent")
    elif phase == "EXECUTION_ACTIVE":
        if execution["status"] not in {"NOT_STARTED", "IN_PROGRESS"} or review["status"] != "NOT_STARTED":
            raise JoyflowError("EXECUTION_ACTIVE phase is inconsistent")
    elif phase == "BLOCKED":
        if execution["status"] != "BLOCKED" or not codex["unresolved_items"]:
            raise JoyflowError("BLOCKED phase lacks truthful blocker state")

    return {
        "record_phase": phase,
        "repository_id": repository_id,
        "pr_number": current_pr_number,
        "base_sha": current_base_sha,
        "head_sha": current_head,
        "actual_changed_paths": actual_changed_paths,
        "actual_changed_paths_digest": changed_paths_digest(actual_changed_paths),
        "brain_block_digest": brain["brain_block_digest"],
        "codex_block_digest": codex["codex_block_digest"],
        "record_digest": record["record_digest"],
        "projection_digest": projection["projection_digest"],
        "codex_return_digest": codex_return["return_digest"],
        "evidence_bundle_digest": evidence_bundle["evidence_bundle_digest"],
        "brain_review_capsule_digest": brain_review_capsule["capsule_digest"],
    }



def build_pr_ci_result(
    validation: dict[str, Any],
    *,
    pr_body_digest: str,
    source_state_before: dict[str, Any],
    source_state_after: dict[str, Any],
    raw_output_ref: str,
) -> dict[str, Any]:
    if source_state_before != source_state_after:
        raise JoyflowError("read-only PR CI changed the source repository")
    checks = [
        {"check_id": "CURRENT_REPOSITORY_IDENTITY", "status": "PASS", "evidence": validation["repository_id"]},
        {"check_id": "BASE_IS_ANCESTOR_OF_HEAD", "status": "PASS", "evidence": f"{validation['base_sha']}..{validation['head_sha']}"},
        {"check_id": "CURRENT_DIFF_EQUALS_CODEX_RETURN", "status": "PASS", "evidence": validation["actual_changed_paths_digest"]},
        {"check_id": "CURRENT_SEALED_SOURCE_CHAIN", "status": "PASS", "evidence": validation["brain_review_capsule_digest"]},
    ]
    row = {
        "artifact_type": "PR_CI_RESULT",
        "result_version": 3,
        "owner": "TOOL",
        "repository_id": validation["repository_id"],
        "pr_number": validation["pr_number"],
        "base_sha": validation["base_sha"],
        "head_sha": validation["head_sha"],
        "pr_body_digest": pr_body_digest,
        "pr_record_digest": validation["record_digest"],
        "brain_block_digest": validation["brain_block_digest"],
        "codex_block_digest": validation["codex_block_digest"],
        "projection_digest": validation["projection_digest"],
        "codex_return_digest": validation["codex_return_digest"],
        "evidence_bundle_digest": validation["evidence_bundle_digest"],
        "brain_review_capsule_digest": validation["brain_review_capsule_digest"],
        "actual_changed_paths_digest": validation["actual_changed_paths_digest"],
        "checks": checks,
        "result": "PASS",
        "raw_output_ref": raw_output_ref,
        "source_state_before_digest": source_state_before["snapshot_digest"],
        "source_state_after_digest": source_state_after["snapshot_digest"],
        "result_digest": None,
    }
    row["result_digest"] = digest(strip_digest(row, "result_digest"))
    core.validate_schema(row, PR_CI_RESULT_SCHEMA)
    return row


def validate_pr_ci_result(
    row: dict[str, Any],
    record: dict[str, Any],
    *,
    pr_body_digest: str,
    actual_changed_paths: list[str],
    projection: dict[str, Any],
    codex_return: dict[str, Any],
    evidence_bundle: dict[str, Any],
    brain_review_capsule: dict[str, Any],
) -> None:
    core.validate_schema(row, PR_CI_RESULT_SCHEMA)
    if row["result_digest"] != digest(strip_digest(row, "result_digest")):
        raise JoyflowError("PR CI result digest mismatch")
    expected = {
        "repository_id": record["repository_id"],
        "pr_number": record["pr_number"],
        "base_sha": record["base_sha"],
        "head_sha": record["head_sha"],
        "pr_body_digest": pr_body_digest,
        "pr_record_digest": record["record_digest"],
        "brain_block_digest": record["brain_block"]["brain_block_digest"],
        "codex_block_digest": record["codex_block"]["codex_block_digest"],
        "projection_digest": projection["projection_digest"],
        "codex_return_digest": codex_return["return_digest"],
        "evidence_bundle_digest": evidence_bundle["evidence_bundle_digest"],
        "brain_review_capsule_digest": brain_review_capsule["capsule_digest"],
        "actual_changed_paths_digest": changed_paths_digest(actual_changed_paths),
    }
    if any(row.get(k) != v for k, v in expected.items()):
        raise JoyflowError("PR CI result is stale or bound to another current object")
    if row["source_state_before_digest"] != row["source_state_after_digest"]:
        raise JoyflowError("PR CI result reports source repository mutation")
    if row["owner"] != "TOOL" or row["result"] != "PASS" or not row["checks"] or not row["raw_output_ref"]:
        raise JoyflowError("PR CI result is not a complete read-only mechanical PASS")



def load_json(path: str | pathlib.Path) -> dict[str, Any]:
    value = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise JoyflowError(f"{path} must contain one JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    pr = sub.add_parser("verify-pr")
    pr.add_argument("--repository", required=True)
    pr.add_argument("--pr-body-file", required=True)
    pr.add_argument("--projection", required=True)
    pr.add_argument("--codex-return", required=True)
    pr.add_argument("--evidence-bundle", required=True)
    pr.add_argument("--brain-review-capsule", required=True)
    pr.add_argument("--base-sha", required=True)
    pr.add_argument("--pr-number", type=int, required=True)
    pr.add_argument("--raw-output-ref", default="current:joyflow-pr-ci:stdout")
    args = parser.parse_args()
    try:
        if args.command == "verify-pr":
            body = pathlib.Path(args.pr_body_file).read_text(encoding="utf-8")
            record = parse_pr_body(body)
            before = repository_state_snapshot(args.repository)
            validation = validate_pr_record(
                record,
                repository=args.repository,
                projection=load_json(args.projection),
                codex_return=load_json(args.codex_return),
                evidence_bundle=load_json(args.evidence_bundle),
                brain_review_capsule=load_json(args.brain_review_capsule),
                merged_change_projection=None,
                current_base_sha=args.base_sha,
                current_pr_number=args.pr_number,
                replay_tests=True,
            )
            after = repository_state_snapshot(args.repository)
            result = build_pr_ci_result(
                validation,
                pr_body_digest=hashlib.sha256(body.encode("utf-8")).hexdigest(),
                source_state_before=before,
                source_state_after=after,
                raw_output_ref=args.raw_output_ref,
            )
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except JoyflowError as exc:
        print(json.dumps({"mechanical_gate": "FAIL", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
