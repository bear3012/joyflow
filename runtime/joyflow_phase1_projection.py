#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
import joyflow_dual_layer as core  # noqa: E402

SCHEMA = ROOT / "schemas/merged_change_projection.schema.json"
JoyflowError = core.JoyflowError


def digest(value: Any) -> str:
    return core.digest(value)


def strip_digest(row: dict[str, Any], field: str) -> dict[str, Any]:
    return core.strip_digest(row, field)


def changed_paths_digest(paths: list[str]) -> str:
    return digest(sorted(set(paths)))


def _final_path_decision(projection: dict[str, Any]) -> dict[str, Any]:
    try:
        row = projection["repository_evidence"]["path_discovery"]["final_path_decision"]
    except (KeyError, TypeError) as exc:
        raise JoyflowError("Projection lacks the exact final path decision") from exc
    if not isinstance(row, dict) or not row.get("decision_digest"):
        raise JoyflowError("Projection final path decision is incomplete")
    return row


def _reference_set(row: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for values in row["retrieval_anchors"].values():
        refs.update(values)
    refs.update(row["technical_route"]["mechanism_ids"])
    refs.update(x["invariant_id"] for x in row["preserved_invariants"])
    for values in row["verification_map"].values():
        refs.update(values)
    refs.update(x["failure_signature"] for x in row["diagnostic_map"])
    return refs


def build_merged_change_projection(
    *,
    pr_record: dict[str, Any],
    projection: dict[str, Any],
    codex_return: dict[str, Any],
    evidence_bundle: dict[str, Any],
    brain_review_capsule: dict[str, Any],
    actual_changed_paths: list[str],
    completion_pointer: dict[str, Any],
    repository_merge_evidence: bytes,
) -> dict[str, Any]:
    paths = sorted(set(actual_changed_paths))
    if not paths:
        raise JoyflowError("merged change projection requires a non-empty current Diff")
    codex = pr_record["codex_block"]
    binding = pr_record["brain_block"]["execution_binding"]
    route = codex["execution"].get("implementation_mechanisms") or ["current_repository_source_replay"]
    path_roots = sorted(set(paths))
    test_ref = "TEST_MERGED_CHANGE_PROJECTION_CURRENT_SOURCE"
    invariant_id = "INV_CURRENT_REPOSITORY_OVERRIDES_HISTORICAL_PROJECTION"
    failure = "STALE_OR_SUBSTITUTED_MERGED_CHANGE_PROJECTION"
    rule_id = "RULE_MERGED_CHANGE_PROJECTION_AI_NATIVE"
    row: dict[str, Any] = {
        "artifact_type": "MERGED_CHANGE_PROJECTION",
        "projection_version": 2,
        "authority": "NAVIGATION_AND_CONTEXT_ONLY",
        "lifecycle": {"timing": "POST_MERGE_ONLY", "generation_basis": "CONDITIONAL_LONG_TERM_CONTINUITY_VALUE", "pre_merge_gate_role": "NONE"},
        "identity": {
            "repository_id": pr_record["repository_id"],
            "pr_number": pr_record["pr_number"],
            "base_sha": pr_record["base_sha"],
            "reviewed_head_sha": pr_record["head_sha"],
            "actual_changed_paths_digest": changed_paths_digest(paths),
            "merge_commit": completion_pointer["merge_commit"],
            "repository_evidence_ref": completion_pointer["repository_evidence_ref"],
        },
        "historical_semantics": {
            "supports_retrieval": True,
            "supports_context_recovery": True,
            "substitutes_current_repository": False,
            "substitutes_current_diff": False,
            "substitutes_current_tests": False,
        },
        "retrieval_anchors": {
            "semantic_topics": ["current PR semantic change", "AI-native change recovery"],
            "affected_domains": ["pr_review", "merge_continuity"],
            "affected_path_roots": path_roots,
            "key_paths": paths,
            "symbols": sorted(set(codex["execution"].get("changed_symbols") or ["current_pr_result"])),
            "rule_ids": [rule_id],
            "schema_ids": ["merged_change_projection.schema.json"],
            "test_ids": [test_ref],
            "failure_signatures": [failure],
        },
        "semantic_delta": {
            "before": ["Current Diff required repeated semantic reconstruction from repository facts."],
            "after": ["Current Diff has a digest-bound navigation projection while repository facts remain authoritative."],
            "unchanged_non_goals": ["No automatic approval, acceptance, merge or promotion."],
        },
        "technical_route": {
            "mechanism_ids": sorted(set(route)),
            "selected_route": "Bind one navigation-only semantic projection to the exact current PR source chain.",
            "rationale": ["Preserve current repository, Diff, tests and sealed evidence as direct authority."],
            "rejected_routes": [
                {
                    "route_id": "UNBOUND_NARRATIVE_SUMMARY",
                    "rejection_reason": "An unbound summary can silently describe another PR or stale evidence.",
                }
            ],
        },
        "impact_map": {
            "inputs": ["CURRENT_PR_DIFF", "CURRENT_CODEX_RETURN", "CURRENT_EVIDENCE_BUNDLE", "CURRENT_BRAIN_REVIEW"],
            "affected_components": ["POST_MERGE_CONTEXT_RECOVERY"],
            "outputs": ["MERGED_CHANGE_PROJECTION"],
            "downstream_checks": ["POST_MERGE_PROJECTION_VALIDATION"],
        },
        "preserved_invariants": [
            {
                "invariant_id": invariant_id,
                "statement": "Historical projection cannot substitute the current repository, Diff, tests or source evidence.",
                "verification_refs": [test_ref],
            }
        ],
        "verification_map": {
            "local_test_refs": [test_ref],
            "ci_check_refs": ["POST_MERGE_PROJECTION_VALIDATION"],
            "positive_case_refs": ["CASE_PROJECTION_EXACT_CURRENT_SOURCE"],
            "failure_case_refs": [failure],
            "mismatch_case_refs": ["CASE_PROJECTION_PROVENANCE_MISMATCH"],
            "adversarial_case_refs": ["CASE_PR_CI_FORGED_RETURN_DIGEST"],
        },
        "diagnostic_map": [
            {
                "failure_signature": failure,
                "likely_components": ["POST_MERGE_CONTEXT_RECOVERY"],
                "inspect_first": paths,
                "validating_test_refs": [test_ref],
                "recovery_boundary": "Regenerate from the exact observed completion pointer and reviewed PR sources; pre-merge gates are unaffected.",
            }
        ],
        "residual_state": {
            "known_limits": ["Projection is retrieval context, not repository fact authority."],
            "deferred_items": ["Persistent control plane and competing truth source remain out of scope."],
            "unresolved_questions": [],
        },
        "evidence_links": [
            {"relation": "VERIFIES", "from_ref": test_ref, "to_ref": invariant_id},
            {"relation": "AFFECTS", "from_ref": failure, "to_ref": rule_id},
        ],
        "fiber_anchors": {
            "PATH_BOUNDARY": paths,
            "FAILURE_DIAGNOSTIC": [failure],
            "INVARIANT_IMPACT": [invariant_id],
            "PROVENANCE_REVIEW": [test_ref],
            "RULE_MIGRATION": [rule_id],
        },
        "provenance": {
            "final_path_decision_digest": binding["final_path_decision_digest"],
            "codex_return_digest": codex_return["return_digest"],
            "evidence_bundle_digest": evidence_bundle["evidence_bundle_digest"],
            "source_codex_block_digest": codex["codex_block_digest"],
            "reviewed_head_sha": pr_record["head_sha"],
            "task_completion_pointer_digest": completion_pointer["pointer_digest"],
        },
        "projection_digest": None,
    }
    row["projection_digest"] = digest(strip_digest(row, "projection_digest"))
    validate_merged_change_projection(
        row,
        projection=projection,
        codex_return=codex_return,
        evidence_bundle=evidence_bundle,
        brain_review_capsule=brain_review_capsule,
        pr_record=pr_record,
        actual_changed_paths=paths,
        completion_pointer=completion_pointer,
        repository_merge_evidence=repository_merge_evidence,
    )
    return row


def validate_merged_change_projection(
    row: dict[str, Any],
    *,
    projection: dict[str, Any],
    codex_return: dict[str, Any],
    evidence_bundle: dict[str, Any],
    brain_review_capsule: dict[str, Any],
    pr_record: dict[str, Any],
    actual_changed_paths: list[str],
    completion_pointer: dict[str, Any],
    repository_merge_evidence: bytes,
) -> None:
    core.validate_schema(row, SCHEMA)
    if row["projection_digest"] != digest(strip_digest(row, "projection_digest")):
        raise JoyflowError("merged change projection digest mismatch")
    core.validate_schema(completion_pointer, ROOT / "schemas/task_completion_pointer.schema.json")
    if completion_pointer["pointer_digest"] != digest(strip_digest(completion_pointer, "pointer_digest")):
        raise JoyflowError("task completion pointer digest mismatch")
    merge_facts = core.validate_completion_pointer_repository_evidence(completion_pointer, repository_merge_evidence)
    if row.get("lifecycle") != {"timing": "POST_MERGE_ONLY", "generation_basis": "CONDITIONAL_LONG_TERM_CONTINUITY_VALUE", "pre_merge_gate_role": "NONE"}:
        raise JoyflowError("Merged Change Projection may only be a conditional post-merge navigation artifact")
    paths = sorted(set(actual_changed_paths))
    brain = pr_record["brain_block"]
    codex = pr_record["codex_block"]
    binding = brain["execution_binding"]
    expected_identity = {
        "repository_id": pr_record["repository_id"],
        "pr_number": pr_record["pr_number"],
        "base_sha": pr_record["base_sha"],
        "reviewed_head_sha": pr_record["head_sha"],
        "actual_changed_paths_digest": changed_paths_digest(paths),
        "merge_commit": completion_pointer["merge_commit"],
        "repository_evidence_ref": completion_pointer["repository_evidence_ref"],
    }
    if row["identity"] != expected_identity:
        raise JoyflowError("merged change projection identity differs from current PR facts")
    if merge_facts["repository_id"] != pr_record["repository_id"] or merge_facts["pr_number"] != pr_record["pr_number"] or merge_facts["reviewed_head_sha"] != pr_record["head_sha"]:
        raise JoyflowError("raw repository merge evidence differs from current PR facts")
    expected_provenance = {
        "final_path_decision_digest": binding["final_path_decision_digest"],
        "codex_return_digest": codex_return["return_digest"],
        "evidence_bundle_digest": evidence_bundle["evidence_bundle_digest"],
        "source_codex_block_digest": codex["codex_block_digest"],
        "reviewed_head_sha": pr_record["head_sha"],
        "task_completion_pointer_digest": completion_pointer["pointer_digest"],
    }
    if row["provenance"] != expected_provenance:
        raise JoyflowError("merged change projection provenance differs from exact current sources")
    review_payload = brain_review_capsule["active_fibers"]["execution_review"]["payload"]
    if review_payload.get("brain_review_verdict") != "PASS":
        raise JoyflowError("merged change projection requires the exact current Brain review PASS")
    if brain["brain_review"].get("source_brain_review_capsule_digest") != brain_review_capsule.get("capsule_digest"):
        raise JoyflowError("merged change projection PR record is bound to another Brain Review Capsule")
    if row["authority"] != "NAVIGATION_AND_CONTEXT_ONLY" or any(
        row["historical_semantics"][key]
        for key in ("substitutes_current_repository", "substitutes_current_diff", "substitutes_current_tests")
    ):
        raise JoyflowError("historical projection may not substitute current repository facts")
    roots = row["retrieval_anchors"]["affected_path_roots"]
    keys = row["retrieval_anchors"]["key_paths"]
    if sorted(keys) != paths:
        raise JoyflowError("merged change projection key paths differ from the complete current Diff")
    for path in paths:
        if not any(fnmatch.fnmatch(path, root) or path == root.rstrip("/**") or path.startswith(root.rstrip("/**") + "/") for root in roots):
            raise JoyflowError("affected path roots do not cover the complete current Diff")
    refs = _reference_set(row)
    for invariant in row["preserved_invariants"]:
        if not invariant["verification_refs"] or any(ref not in refs for ref in invariant["verification_refs"]):
            raise JoyflowError("projection invariant verification refs are unresolved")
    for link in row["evidence_links"]:
        if link["from_ref"] not in refs or link["to_ref"] not in refs:
            raise JoyflowError("projection evidence link endpoint is unresolved")
    for values in row["fiber_anchors"].values():
        if any(ref not in refs for ref in values):
            raise JoyflowError("temporary fiber anchor is unresolved")
    if row["residual_state"]["unresolved_questions"]:
        raise JoyflowError("unresolved projection questions block this optional post-merge navigation projection")
    # Revalidate the exact sealed sources. This is deliberately not a substitute
    # for current repository replay performed by the PR entry point.
    core.validate_codex_execution_return_structure(codex_return, projection, evidence_bundle)


def build_temporary_evidence_fiber(
    projection: dict[str, Any], profile: str, anchors: list[str], *, closure: dict[str, Any] | None = None
) -> dict[str, Any]:
    core.validate_schema(projection, SCHEMA)
    if projection["projection_digest"] != digest(strip_digest(projection, "projection_digest")):
        raise JoyflowError("temporary fiber source projection digest mismatch")
    refs = _reference_set(projection)
    requested = set(anchors)
    missing = sorted(requested - refs)
    selected = sorted(requested & refs)
    state = {
        "current_object_bound": False,
        "direct_evidence_refs": [],
        "derived_steps_marked": False,
        "authority_boundary_present": False,
        "verification_refs": [],
        "counterevidence_checked": False,
        "unresolved_items": [],
        **(closure or {}),
    }
    required = [
        bool(state["current_object_bound"]),
        bool(state["direct_evidence_refs"]),
        bool(state["derived_steps_marked"]),
        bool(state["authority_boundary_present"]),
        bool(state["verification_refs"]),
        bool(state["counterevidence_checked"]),
    ]
    status = "BLOCKED" if state["unresolved_items"] else ("CLOSED" if not missing and all(required) else "NEEDS_FACTS")
    return {
        "artifact_type": "TEMPORARY_EVIDENCE_FIBER",
        "persistent": False,
        "profile": profile,
        "source_projection_digest": projection["projection_digest"],
        "anchors": anchors,
        "selected_refs": selected,
        "missing_refs": missing,
        "closure": state,
        "final_status": status,
    }


def load_json(path: str | pathlib.Path) -> dict[str, Any]:
    value = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise JoyflowError(f"{path} must contain one JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged-change-projection", required=True)
    parser.add_argument("--source-projection", required=True)
    parser.add_argument("--codex-return", required=True)
    parser.add_argument("--evidence-bundle", required=True)
    parser.add_argument("--brain-review-capsule", required=True)
    parser.add_argument("--pr-record", required=True)
    parser.add_argument("--changed-path", action="append", default=[])
    parser.add_argument("--completion-pointer", required=True)
    parser.add_argument("--repository-merge-evidence", required=True)
    args = parser.parse_args()
    try:
        validate_merged_change_projection(
            load_json(args.merged_change_projection),
            projection=load_json(args.source_projection),
            codex_return=load_json(args.codex_return),
            evidence_bundle=load_json(args.evidence_bundle),
            brain_review_capsule=load_json(args.brain_review_capsule),
            pr_record=load_json(args.pr_record),
            actual_changed_paths=args.changed_path,
            completion_pointer=load_json(args.completion_pointer),
            repository_merge_evidence=pathlib.Path(args.repository_merge_evidence).read_bytes(),
        )
    except (JoyflowError, OSError, json.JSONDecodeError) as exc:
        print(f"JOYFLOW_BLOCK: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
