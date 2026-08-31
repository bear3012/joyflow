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
CURRENT_REVIEW_TRANSPORT_SCHEMA = ROOT / "schemas/current_pr_review_input_transport.schema.json"
BEGIN = "<!-- JOYFLOW_PR_RECORD_BEGIN"
END = "JOYFLOW_PR_RECORD_END -->"
TRANSPORT_BEGIN = "<!-- JOYFLOW_CURRENT_REVIEW_TRANSPORT_BEGIN"
TRANSPORT_END = "JOYFLOW_CURRENT_REVIEW_TRANSPORT_END -->"

CURRENT_REVIEW_OBJECTS = {
    "CODEX_HANDOFF_PROJECTION": ("CODEX_HANDOFF_PROJECTION", "projection_digest", "--projection"),
    "CODEX_EXECUTION_RETURN": ("CODEX_EXECUTION_RETURN", "return_digest", "--codex-return"),
    "CODEX_EXECUTION_EVIDENCE_BUNDLE": ("CODEX_EXECUTION_EVIDENCE_BUNDLE", "evidence_bundle_digest", "--evidence-bundle"),
    "BRAIN_REVIEW_CAPSULE": ("FIBERED_TASK_CAPSULE", "capsule_digest", "--brain-review-capsule"),
}

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


def parse_current_review_transport(body: str) -> dict[str, Any]:
    if body.count(TRANSPORT_BEGIN) != 1 or body.count(TRANSPORT_END) != 1:
        raise JoyflowError("PR body must contain exactly one current review transport locator block")
    content = body.split(TRANSPORT_BEGIN, 1)[1].split(TRANSPORT_END, 1)[0].strip()
    try:
        value = json.loads(content)
    except json.JSONDecodeError as exc:
        raise JoyflowError(f"current review transport locator JSON invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise JoyflowError("current review transport locator must be one JSON object")
    return value


def render_current_review_transport(locator: dict[str, Any]) -> str:
    return f"{TRANSPORT_BEGIN}\n{json.dumps(locator, ensure_ascii=False, indent=2)}\n{TRANSPORT_END}\n"


def render_pr_body(record: dict[str, Any], *, preamble: str = "Joyflow current-object review record.", transport_locator: dict[str, Any] | None = None) -> str:
    transport = f"{render_current_review_transport(transport_locator)}\n" if transport_locator is not None else ""
    return f"{transport}{preamble}\n\n{BEGIN}\n{json.dumps(record, ensure_ascii=False, indent=2)}\n{END}\n"


def _replace_managed_block(body: str, begin: str, end: str, replacement: str) -> tuple[str, bool]:
    begin_count = body.count(begin)
    end_count = body.count(end)
    if begin_count != end_count or begin_count > 1:
        raise JoyflowError(f"PR body contains duplicate or malformed managed block: {begin}")
    if begin_count == 0:
        return body, False
    start = body.index(begin)
    finish = body.index(end, start) + len(end)
    return body[:start] + replacement.rstrip("\n") + body[finish:], True


def update_pr_body(existing_body: str, locator: dict[str, Any], record: dict[str, Any]) -> str:
    """Replace only Joyflow-managed blocks and preserve all other PR-body bytes."""
    core.validate_schema(locator, CURRENT_REVIEW_TRANSPORT_SCHEMA)
    core.validate_schema(record, PR_RECORD_SCHEMA)
    if existing_body.count(TRANSPORT_BEGIN) == 1 and existing_body.count(TRANSPORT_END) == 1:
        previous_locator = parse_current_review_transport(existing_body)
        core.validate_schema(previous_locator, CURRENT_REVIEW_TRANSPORT_SCHEMA)
        if previous_locator["locator_digest"] != digest(strip_digest(previous_locator, "locator_digest")):
            raise JoyflowError("existing current review transport locator digest mismatch")
    if existing_body.count(BEGIN) == 1 and existing_body.count(END) == 1:
        previous_record = parse_pr_body(existing_body)
        core.validate_schema(previous_record, PR_RECORD_SCHEMA)
        previous_brain = previous_record["brain_block"]
        previous_codex = previous_record["codex_block"]
        if previous_brain["brain_block_digest"] != digest(pr_block_payload(previous_brain, "brain_block_digest")):
            raise JoyflowError("existing PR Brain block digest mismatch")
        if previous_codex["codex_block_digest"] != digest(pr_block_payload(previous_codex, "codex_block_digest")):
            raise JoyflowError("existing PR Codex block digest mismatch")
        if previous_record["record_digest"] != digest(strip_digest(previous_record, "record_digest")):
            raise JoyflowError("existing PR record digest mismatch")
    transport = render_current_review_transport(locator).rstrip("\n")
    pr_record = f"{BEGIN}\n{json.dumps(record, ensure_ascii=False, indent=2)}\n{END}"
    updated, transport_replaced = _replace_managed_block(existing_body, TRANSPORT_BEGIN, TRANSPORT_END, transport)
    updated, record_replaced = _replace_managed_block(updated, BEGIN, END, pr_record)
    missing = []
    if not transport_replaced:
        missing.append(transport)
    if not record_replaced:
        missing.append(pr_record)
    if missing:
        prefix = "\n\n".join(missing)
        updated = prefix + (("\n\n" + updated) if updated else "\n")
    if updated.count(TRANSPORT_BEGIN) != 1 or updated.count(TRANSPORT_END) != 1:
        raise JoyflowError("updated PR body does not contain exactly one current review transport block")
    if updated.count(BEGIN) != 1 or updated.count(END) != 1:
        raise JoyflowError("updated PR body does not contain exactly one Joyflow PR record block")
    if parse_current_review_transport(updated) != locator or parse_pr_body(updated) != record:
        raise JoyflowError("updated PR body changed a managed Joyflow object")
    return updated


def _git(repo: pathlib.Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise JoyflowError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc


def _canonical_repo(repo: str | pathlib.Path) -> tuple[pathlib.Path, str, str]:
    root, repository_id, head = core._repository_source_identity(repo)
    return root, repository_id, head


def validate_current_review_transport_locator(
    locator: dict[str, Any], *, repository: str | pathlib.Path, current_base_sha: str, current_pr_number: int,
) -> dict[str, dict[str, Any]]:
    core.validate_schema(locator, CURRENT_REVIEW_TRANSPORT_SCHEMA)
    if locator["locator_digest"] != digest(strip_digest(locator, "locator_digest")):
        raise JoyflowError("current review transport locator digest mismatch")
    root, repository_id, current_head = _canonical_repo(repository)
    expected = {"repository_id": repository_id, "pr_number": current_pr_number, "base_sha": current_base_sha, "source_head_sha": current_head}
    if any(locator.get(key) != value for key, value in expected.items()):
        raise JoyflowError("current review transport locator is bound to another current PR source")
    if locator["exact_transport_commit"] == current_head:
        raise JoyflowError("current review transport commit must be distinct from the product source Head")
    entries = locator["object_entries"]
    by_role = {entry["object_role"]: entry for entry in entries}
    if len(by_role) != len(entries) or set(by_role) != set(CURRENT_REVIEW_OBJECTS):
        raise JoyflowError("current review transport must declare the exact four lifecycle object roles")
    paths = [entry["exact_path"] for entry in entries]
    if len(paths) != len(set(paths)):
        raise JoyflowError("current review transport object paths must be unique")
    for role, (artifact_type, digest_field, _) in CURRENT_REVIEW_OBJECTS.items():
        entry = by_role[role]
        if entry["artifact_type"] != artifact_type or entry["semantic_digest_field_name"] != digest_field:
            raise JoyflowError(f"current review transport entry semantics mismatch: {role}")
    core._require_ancestor(root, current_base_sha, current_head)
    return by_role


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


def _approved_paths(projection: dict[str, Any], *, allow_empty: bool = False) -> list[str]:
    decision = _final_path_decision(projection)
    paths = [x["path"] for x in decision["allowed_path_items"]]
    if (not allow_empty and not paths) or len(paths) != len(set(paths)) or any(not core._valid_repo_path(x) for x in paths):
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
    repository_evidence = core._repository_review_evidence(codex_return)
    if repository_evidence:
        refs.append(repository_evidence["diff_evidence_ref"])
    return sorted(set(refs))


def _record_phase(execution_status: str, review_status: str, codex_unresolved: list[str], review_unresolved: list[str]) -> str:
    if execution_status == "BLOCKED" and codex_unresolved:
        return "BLOCKED"
    if execution_status in {"NOT_STARTED", "IN_PROGRESS"} and review_status == "NOT_STARTED":
        return "EXECUTION_ACTIVE"
    if execution_status == "COMPLETED" and review_status == "NOT_STARTED":
        return "CODEX_COMPLETE"
    if execution_status == "COMPLETED" and review_status in {"PASS", "RETURN_FOR_REPAIR", "BLOCKED"}:
        if review_status == "PASS" and not codex_unresolved and not review_unresolved:
            return "READY_FOR_USER_DECISION"
        return "BRAIN_REVIEWED"
    raise JoyflowError("current execution/review state cannot form a legal PR record phase")


def construct_pr_record(
    *,
    repository: str | pathlib.Path,
    projection: dict[str, Any],
    codex_return: dict[str, Any],
    evidence_bundle: dict[str, Any],
    brain_review_capsule: dict[str, Any],
    current_base_sha: str,
    current_pr_number: int,
    replay_tests: bool = True,
) -> dict[str, Any]:
    """Derive one PR Record from validated current lifecycle objects and repository facts."""
    root, repository_id, current_head = _canonical_repo(repository)
    changed_paths = _repository_changed_paths(root, current_base_sha, current_head)
    decision = _final_path_decision(projection)
    operation = projection.get("task_anchor", {}).get("repository_operation")
    allowed_paths = _approved_paths(projection, allow_empty=operation == "EXISTING_FROZEN_PR_REPLAY")
    review_payload = _review_payload(brain_review_capsule)
    review_status = review_payload.get("brain_review_verdict")
    review_unresolved = list(review_payload.get("unresolved_followups") or [])
    codex_unresolved = list(codex_return.get("unresolved_items") or [])

    local_test_refs = sorted({
        str(row["evidence_ref"])
        for row in codex_return.get("machine_results", [])
        if isinstance(row, dict) and row.get("evidence_ref")
    })
    codex = {
        "block_version": 4,
        "writer_role": "CODEX",
        "technical_preflight_status": codex_return["technical_preflight"]["status"],
        "source_codex_return_digest": codex_return["return_digest"],
        "source_evidence_bundle_digest": evidence_bundle["evidence_bundle_digest"],
        "execution": {
            "status": codex_return["execution_status"],
            "checked_base_sha": current_base_sha,
            "checked_head_sha": current_head,
            "actual_changed_paths": changed_paths,
            "actual_changed_paths_digest": changed_paths_digest(changed_paths),
            "changed_symbols": [],
            "implementation_mechanisms": [],
        },
        "local_test_refs": local_test_refs,
        "evidence_refs": _expected_codex_evidence_refs(codex_return),
        "unresolved_items": codex_unresolved,
        "codex_block_digest": None,
    }
    codex["codex_block_digest"] = digest(pr_block_payload(codex, "codex_block_digest"))

    semantic_context = sorted({
        str(item["meaning"])
        for item in projection.get("material_semantics", [])
        if isinstance(item, dict) and item.get("meaning")
    })
    selected = codex_return.get("technical_preflight", {}).get("selected_route") or {}
    selected_route = [str(selected[key]) for key in ("route_id", "implementation_summary") if selected.get(key)]
    brain = {
        "block_version": 4,
        "writer_role": "WEB_BRAIN",
        "execution_binding": {
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
        },
        "semantic_context": semantic_context,
        "selected_technical_route": selected_route,
        "non_goals": list(projection.get("task_anchor", {}).get("non_goals") or []),
        "preserved_invariants": list(brain_review_capsule.get("refs", {}).get("preserves") or []),
        "brain_review": {
            "status": review_status,
            "reviewed_head_sha": current_head,
            "source_projection_digest": projection["projection_digest"],
            "source_final_path_decision_digest": decision["decision_digest"],
            "source_codex_return_digest": codex_return["return_digest"],
            "source_evidence_bundle_digest": evidence_bundle["evidence_bundle_digest"],
            "source_codex_block_digest": codex["codex_block_digest"],
            "source_brain_review_capsule_digest": brain_review_capsule["capsule_digest"],
            "unresolved_items": review_unresolved,
        },
        "merged_change_projection": None,
        "brain_block_digest": None,
    }
    brain["brain_block_digest"] = digest(pr_block_payload(brain, "brain_block_digest"))
    record = {
        "artifact_type": "JOYFLOW_PR_RECORD",
        "record_version": 4,
        "record_phase": _record_phase(codex_return["execution_status"], str(review_status), codex_unresolved, review_unresolved),
        "repository_id": repository_id,
        "pr_number": current_pr_number,
        "base_sha": current_base_sha,
        "head_sha": current_head,
        "brain_block": brain,
        "codex_block": codex,
        "record_digest": None,
    }
    record["record_digest"] = digest(strip_digest(record, "record_digest"))
    validate_pr_record(
        record,
        repository=root,
        projection=projection,
        codex_return=codex_return,
        evidence_bundle=evidence_bundle,
        brain_review_capsule=brain_review_capsule,
        current_base_sha=current_base_sha,
        current_pr_number=current_pr_number,
        replay_tests=replay_tests,
    )
    return record


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

    if projection["execution_object"]["physical_object"]["kind"] != "REPOSITORY_COMMIT":
        raise JoyflowError("PR record requires a repository execution Projection")
    pr = core._repository_review_evidence(codex_return, projection, evidence_bundle)
    if not pr:
        raise JoyflowError("PR record requires one repository evidence variant from the exact Codex Return")
    expected_pr = {
        "repository_id": repository_id,
        "base_commit": current_base_sha,
        "head_sha": current_head,
        "review_coverage_paths": actual_changed_paths,
    }
    if any(pr.get(k) != v for k, v in expected_pr.items()):
        raise JoyflowError("Codex Return PR evidence differs from the current repository Diff")

    decision = _final_path_decision(projection)
    operation = projection["task_anchor"].get("repository_operation")
    if operation not in {"CURRENT_ROUND_REPOSITORY_CHANGE", "EXISTING_FROZEN_PR_REPLAY"}:
        raise JoyflowError("PR record requires an exact repository operation discriminator")
    allowed_paths = _approved_paths(projection, allow_empty=operation == "EXISTING_FROZEN_PR_REPLAY")
    mutation = codex_return["mutation_summary"]
    if operation == "EXISTING_FROZEN_PR_REPLAY":
        replay = codex_return.get("repository_replay_evidence")
        if codex_return.get("pr_evidence") is not None or not replay or mutation["mutation_performed"] or mutation["residual_changed_paths"]:
            raise JoyflowError("existing PR replay Return violates its zero-mutation evidence branch")
        expected_replay = {"repository_id":repository_id,"pr_number":current_pr_number,"base_commit":current_base_sha,"head_sha":current_head,"review_coverage_paths":actual_changed_paths}
        if any(pr.get(key) != value for key, value in expected_replay.items()):
            raise JoyflowError("existing PR replay evidence differs from the current PR identity or Diff")
        if allowed_paths or sorted(projection["task_anchor"]["repository_anchor"]["review_coverage_paths"]) != actual_changed_paths:
            raise JoyflowError("existing PR replay must keep mutation paths empty and review the exact current PR Diff")
    else:
        if not allowed_paths or not codex_return.get("pr_evidence") or codex_return.get("repository_replay_evidence") is not None or mutation["mutation_performed"] is not True:
            raise JoyflowError("current-round repository change requires non-empty mutation paths and mutation PR evidence")
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
