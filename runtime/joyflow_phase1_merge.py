#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
import joyflow_dual_layer as core  # noqa: E402
import joyflow_phase1_review as review  # noqa: E402

JoyflowError = core.JoyflowError
SCHEMA = ROOT / "schemas/merge_candidate_freeze.schema.json"


def digest(value: Any) -> str:
    return core.digest(value)


def strip_digest(row: dict[str, Any], key: str) -> dict[str, Any]:
    return core.strip_digest(row, key)


def _review_payload(capsule: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = capsule["active_fibers"]["execution_review"]["payload"]
    except (KeyError, TypeError) as exc:
        raise JoyflowError("acceptance Capsule lacks execution_review payload") from exc
    if not isinstance(payload, dict):
        raise JoyflowError("acceptance Capsule execution_review payload is invalid")
    return payload


def build_merge_candidate_freeze(
    *,
    record: dict[str, Any],
    pr_body_digest: str,
    pr_ci_result: dict[str, Any],
    projection: dict[str, Any],
    codex_return: dict[str, Any],
    evidence_bundle: dict[str, Any],
    brain_review_capsule: dict[str, Any],
) -> dict[str, Any]:
    row = {
        "artifact_type": "MERGE_CANDIDATE_FREEZE",
        "freeze_version": 4,
        "owner": "WEB_BRAIN",
        "status": "FROZEN_FOR_USER_DECISIONS",
        "project_id": projection["project_id"],
        "task_id": projection["task_id"],
        "round_id": projection["round_id"],
        "repository_id": record["repository_id"],
        "pr_number": record["pr_number"],
        "base_sha": record["base_sha"],
        "head_sha": record["head_sha"],
        "pr_body_digest": pr_body_digest,
        "pr_record_digest": record["record_digest"],
        "pr_ci_result_digest": pr_ci_result["result_digest"],
        "projection_digest": projection["projection_digest"],
        "codex_return_digest": codex_return["return_digest"],
        "evidence_bundle_digest": evidence_bundle["evidence_bundle_digest"],
        "brain_review_capsule_digest": brain_review_capsule["capsule_digest"],
        "unresolved_items": [],
        "freeze_digest": None,
    }
    row["freeze_digest"] = digest(strip_digest(row, "freeze_digest"))
    core.validate_schema(row, SCHEMA)
    return row


def validate_merge_candidate_freeze(
    row: dict[str, Any],
    *,
    repository: str | pathlib.Path,
    pr_body: str,
    projection: dict[str, Any],
    codex_return: dict[str, Any],
    evidence_bundle: dict[str, Any],
    brain_review_capsule: dict[str, Any],
    pr_ci_result: dict[str, Any],
    current_base_sha: str,
    current_pr_number: int,
) -> dict[str, Any]:
    core.validate_schema(row, SCHEMA)
    if row["freeze_digest"] != digest(strip_digest(row, "freeze_digest")):
        raise JoyflowError("merge candidate freeze digest mismatch")
    record = review.parse_pr_body(pr_body)
    pr_body_digest = hashlib.sha256(pr_body.encode("utf-8")).hexdigest()
    static_paths = record["codex_block"]["execution"]["actual_changed_paths"]
    review.validate_pr_ci_result(
        pr_ci_result,
        record,
        pr_body_digest=pr_body_digest,
        actual_changed_paths=static_paths,
        projection=projection,
        codex_return=codex_return,
        evidence_bundle=evidence_bundle,
        brain_review_capsule=brain_review_capsule,
    )
    expected = {
        "project_id": projection["project_id"],
        "task_id": projection["task_id"],
        "round_id": projection["round_id"],
        "repository_id": record["repository_id"],
        "pr_number": record["pr_number"],
        "base_sha": record["base_sha"],
        "head_sha": record["head_sha"],
        "pr_body_digest": pr_body_digest,
        "pr_record_digest": record["record_digest"],
        "pr_ci_result_digest": pr_ci_result["result_digest"],
        "projection_digest": projection["projection_digest"],
        "codex_return_digest": codex_return["return_digest"],
        "evidence_bundle_digest": evidence_bundle["evidence_bundle_digest"],
        "brain_review_capsule_digest": brain_review_capsule["capsule_digest"],
        "unresolved_items": [],
    }
    if any(row.get(k) != v for k, v in expected.items()):
        raise JoyflowError("merge candidate freeze is stale or bound to another reviewed current object")
    validated = review.validate_pr_record(
        record,
        repository=repository,
        projection=projection,
        codex_return=codex_return,
        evidence_bundle=evidence_bundle,
        brain_review_capsule=brain_review_capsule,
        merged_change_projection=None,
        current_base_sha=current_base_sha,
        current_pr_number=current_pr_number,
        replay_tests=True,
    )
    if validated["record_phase"] != "READY_FOR_USER_DECISION":
        raise JoyflowError("merge candidate freeze requires Brain Review PASS and current PR CI PASS")
    return {"freeze_digest": row["freeze_digest"], **validated}


def validate_post_freeze_user_acceptance(
    capsule: dict[str, Any],
    *,
    merge_candidate_freeze: dict[str, Any],
    repository: str | pathlib.Path,
    projection: dict[str, Any],
    codex_return: dict[str, Any],
    evidence_bundle: dict[str, Any],
    replay_source: bool = True,
) -> dict[str, Any]:
    core.validate_schema(merge_candidate_freeze, SCHEMA)
    if merge_candidate_freeze["freeze_digest"] != digest(strip_digest(merge_candidate_freeze, "freeze_digest")):
        raise JoyflowError("merge candidate freeze digest mismatch")
    core.validate_capsule(capsule)
    if replay_source:
        core.validate_review_input_binding(
            capsule,
            projection,
            codex_return,
            evidence_bundle,
            source_repository=repository,
            replay_tests=True,
        )
    if capsule["task_progress"]["stage"] != "MERGE_DECISION":
        raise JoyflowError("post-freeze acceptance requires the current MERGE_DECISION Capsule")
    payload = _review_payload(capsule)
    target = payload.get("review_target") or {}
    if payload.get("brain_review_verdict") != "PASS":
        raise JoyflowError("post-freeze acceptance requires current Brain Review PASS")
    if target.get("target_type") != "REPOSITORY_PR_HEAD":
        raise JoyflowError("post-freeze acceptance requires a repository PR Head target")
    if target.get("repository_id") != merge_candidate_freeze["repository_id"] or target.get("head_sha") != merge_candidate_freeze["head_sha"]:
        raise JoyflowError("post-freeze acceptance is bound to another frozen PR Head")
    if payload.get("merge_candidate_freeze_digest") != merge_candidate_freeze["freeze_digest"]:
        raise JoyflowError("user acceptance is not bound to the exact Merge Candidate Freeze")
    status = payload.get("user_acceptance")
    refs = payload.get("user_acceptance_evidence_refs") or []
    reason = payload.get("acceptance_not_applicable_reason")
    if status == "PASS":
        if not refs or reason is not None:
            raise JoyflowError("user acceptance PASS requires an exact user decision reference")
    elif status == "NOT_APPLICABLE":
        if refs or not isinstance(reason, str) or not reason:
            raise JoyflowError("NOT_APPLICABLE acceptance requires an explicit reason")
    else:
        raise JoyflowError("pending or blocked user acceptance cannot authorize merge")
    return {"status": status, "capsule_digest": capsule["capsule_digest"], "head_sha": target["head_sha"]}


def load_json(path: str | pathlib.Path) -> dict[str, Any]:
    value = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise JoyflowError(f"{path} must contain one JSON object")
    return value


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repository", required=True)
    ap.add_argument("--pr-body-file", required=True)
    ap.add_argument("--projection", required=True)
    ap.add_argument("--codex-return", required=True)
    ap.add_argument("--evidence-bundle", required=True)
    ap.add_argument("--brain-review-capsule", required=True)
    ap.add_argument("--pr-ci-result", required=True)
    ap.add_argument("--merge-candidate-freeze", required=True)
    ap.add_argument("--base-sha", required=True)
    ap.add_argument("--pr-number", type=int, required=True)
    args = ap.parse_args()
    try:
        before = review.repository_state_snapshot(args.repository)
        result = validate_merge_candidate_freeze(
            load_json(args.merge_candidate_freeze),
            repository=args.repository,
            pr_body=pathlib.Path(args.pr_body_file).read_text(encoding="utf-8"),
            projection=load_json(args.projection),
            codex_return=load_json(args.codex_return),
            evidence_bundle=load_json(args.evidence_bundle),
            brain_review_capsule=load_json(args.brain_review_capsule),
            pr_ci_result=load_json(args.pr_ci_result),
            current_base_sha=args.base_sha,
            current_pr_number=args.pr_number,
        )
        after = review.repository_state_snapshot(args.repository)
        if before != after:
            raise JoyflowError("read-only merge-freeze verification changed the source repository")
        print(json.dumps({"mechanical_gate": "PASS", **result}, ensure_ascii=False, sort_keys=True))
        return 0
    except JoyflowError as exc:
        print(json.dumps({"mechanical_gate": "FAIL", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
