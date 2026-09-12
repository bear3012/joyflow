from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location("build_fixture", ROOT / "tests/build_fixture.py")
f = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(f)
c = f.c

_review_spec = importlib.util.spec_from_file_location("phase1_review", ROOT / "runtime/joyflow_phase1_review.py")
review = importlib.util.module_from_spec(_review_spec)
assert _review_spec.loader is not None
_review_spec.loader.exec_module(review)

_projection_spec = importlib.util.spec_from_file_location("phase1_projection", ROOT / "runtime/joyflow_phase1_projection.py")
change_projection = importlib.util.module_from_spec(_projection_spec)
assert _projection_spec.loader is not None
_projection_spec.loader.exec_module(change_projection)

_merge_spec = importlib.util.spec_from_file_location("phase1_merge", ROOT / "runtime/joyflow_phase1_merge.py")
merge = importlib.util.module_from_spec(_merge_spec)
assert _merge_spec.loader is not None
_merge_spec.loader.exec_module(merge)


def git(repo: pathlib.Path, *args: str) -> str:
    env = dict(os.environ)
    if args and args[0] == "commit":
        message = args[-1] if args else "commit"
        stamp = {"base": "2000-01-01T00:00:00Z", "head": "2000-01-02T00:00:00Z", "other": "2000-01-03T00:00:00Z", "divergent": "2000-01-04T00:00:00Z"}.get(message, "2000-01-05T00:00:00Z")
        env["GIT_AUTHOR_DATE"] = stamp
        env["GIT_COMMITTER_DATE"] = stamp
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)
    return proc.stdout.strip()


def _unset_local_config_if_present(repo: pathlib.Path, key: str) -> None:
    probe = subprocess.run(
        ["git", "-C", str(repo), "config", "--local", "--get-all", key],
        capture_output=True,
        text=True,
    )
    if probe.returncode == 0:
        git(repo, "config", "--local", "--unset-all", key)
    elif probe.returncode != 1:
        raise RuntimeError(probe.stderr)


def create_repository(*, divergent: bool = False) -> tuple[tempfile.TemporaryDirectory[str], pathlib.Path, str, str]:
    td = tempfile.TemporaryDirectory()
    repo = pathlib.Path(td.name) / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "--local", "core.filemode", "true")
    _unset_local_config_if_present(repo, "core.symlinks")
    _unset_local_config_if_present(repo, "core.ignorecase")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Joyflow Test")
    git(repo, "remote", "add", "origin", "https://github.com/example/repo.git")
    (repo / "runtime").mkdir()
    (repo / "tests").mkdir()
    (repo / "runtime/joyflow_dual_layer.py").write_text("print('base')\n", encoding="utf-8")
    (repo / "tests/test_placeholder.py").write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "base")
    base = git(repo, "rev-parse", "HEAD")
    if divergent:
        git(repo, "checkout", "-qb", "other")
        (repo / "other.txt").write_text("other\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "other")
        head = git(repo, "rev-parse", "HEAD")
        git(repo, "checkout", "-q", "master")
        return td, repo, base, head
    (repo / "runtime/joyflow_dual_layer.py").write_text("print('head')\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "head")
    head = git(repo, "rev-parse", "HEAD")
    return td, repo, base, head


def _patch_github_evidence(state: dict[str, Any], repo: pathlib.Path, base: str) -> None:
    path_state = state["active_fibers"]["repository_evidence"]["payload"]["path_discovery"]
    row = path_state["github_path_evidence"][0]
    row["object_ref"] = f"github:example/repo@{base}"
    row["observed_commit_or_head"] = base
    row["raw_evidence_ref"] = f"github:example/repo@{base}:path-discovery"
    row["scope"]["raw_object_sha256"] = hashlib.sha256(c.canonical_bytes(c._github_source_capture_payload(row, repo))).hexdigest()
    row["scope"]["scope_digest"] = c.digest(c._github_scope_payload(row))
    row["evidence_digest"] = c.digest(c.strip_digest(row, "evidence_digest"))
    path_state["github_ref"] = f"github:example/repo@{base}"
    source = next(x for x in state["evidence_registry"] if x["evidence_id"] == "E_GITHUB_PATHS")
    source["ref"] = row["raw_evidence_ref"]
    source["claim"] = c._github_scope_claim(row)
    source["claim_digest"] = c.digest(source["claim"])
    source["subject_id"] = row["object_ref"]
    source["raw_output_ref"] = row["raw_evidence_ref"]
    source["raw_output_sha256"] = row["scope"]["raw_object_sha256"]


def repository_approved_projection(repo: pathlib.Path, base: str, evidence_transport_plan: dict[str, Any] | None = None, current_review_transport_plan: dict[str, Any] | None = None):
    state = f.new_capsule("DEVELOPMENT_STANDARD", "REPOSITORY_CHANGE")
    if evidence_transport_plan is not None:
        state["active_fibers"]["authority"]["payload"]["evidence_transport"] = copy.deepcopy(evidence_transport_plan)
    if current_review_transport_plan is not None:
        state["active_fibers"]["authority"]["payload"]["current_review_transport"] = copy.deepcopy(current_review_transport_plan)
    state["task_anchor"]["repository_anchor"]["baseline_commit"] = base
    repo_payload = state["active_fibers"]["repository_evidence"]["payload"]
    repo_payload["baseline_commit"] = base
    path_state = repo_payload["path_discovery"]
    final = path_state["final_path_decision"]
    final["baseline_commit"] = base
    final["decision_digest"] = c.digest(c.strip_digest(final, "decision_digest"))
    state["active_fibers"]["decision_boundary"]["payload"]["repository_binding"]["expected_base_commit"] = base
    _patch_github_evidence(state, repo, base)
    state = f.refresh(state)
    initial = c.prepare_capsule_structural_fixture(state)
    current = initial
    if current["task_progress"]["stage"] in {"INTENT_DISCUSSION", "REPOSITORY_DISCOVERY"}:
        current = f.advance(current, "DECISION_CLOSURE")
    if current["task_progress"]["stage"] != "USER_APPROVAL":
        current = f.advance(current, "USER_APPROVAL")
    projection, view, binding = c.draft_handoff(current)
    approved = copy.deepcopy(current)
    approved["approval_record"] = {
        "status": "APPROVED_FINAL",
        "owner": "WEB_BRAIN",
        "scope": c.expected_approval_scope(approved),
        "basis": "CURRENT_EXPLICIT_USER_DECISION",
        "decision_ref": "conversation:current-explicit-execution-approval",
        "binding": binding,
    }
    approved["derived_gates"] = c.compute_gate_snapshot(approved)
    c.validate_capsule(approved)
    projection, _ = c.compile_handoff(approved)
    return approved, projection, view, binding


def repository_replay_approved_projection(repo: pathlib.Path, base: str, head: str, *, pr_number: int=42, current_review_transport_plan: dict[str,Any] | None=None):
    touched=sorted(x for x in git(repo,"diff","--name-only",base,head).splitlines() if x)
    state=f.new_capsule("DEVELOPMENT_STANDARD","REPOSITORY_CHANGE")
    state["task_anchor"]["repository_operation"]="EXISTING_FROZEN_PR_REPLAY"
    state["task_anchor"]["repository_anchor"]={"repository_id":"example/repo","baseline_commit":base,"pr_number":pr_number,"pr_url":f"https://github.com/example/repo/pull/{pr_number}","base_branch":"main","working_branch":"joyflow/task","frozen_head_sha":head,"review_coverage_paths":touched}
    repo_payload=state["active_fibers"]["repository_evidence"]["payload"]; repo_payload["baseline_commit"]=base
    final=repo_payload["path_discovery"]["final_path_decision"]; final["baseline_commit"]=base; final["allowed_path_items"]=[]; final["decision_digest"]=c.digest(c.strip_digest(final,"decision_digest"))
    decision=state["active_fibers"]["decision_boundary"]["payload"]
    decision["repository_binding"].update({"expected_base_commit":base,"default_branch":"main","working_branch":"joyflow/task"})
    for item in state["active_fibers"]["semantic"]["payload"]["semantic_items"]:
        item["effects"]=[effect for effect in item.get("effects",[]) if effect.get("effect_type")!="ALLOW_PATH"]
    for route in decision["technical_route_space"]["candidate_routes"]: route["expected_paths"]=[]
    if current_review_transport_plan is not None: state["active_fibers"]["authority"]["payload"]["current_review_transport"]=copy.deepcopy(current_review_transport_plan)
    _patch_github_evidence(state,repo,base)
    state=f.refresh(state); initial=c.prepare_capsule_structural_fixture(state); current=initial
    if current["task_progress"]["stage"] in {"INTENT_DISCUSSION","REPOSITORY_DISCOVERY"}: current=f.advance(current,"DECISION_CLOSURE")
    if current["task_progress"]["stage"]!="USER_APPROVAL": current=f.advance(current,"USER_APPROVAL")
    projection,view,binding=c.draft_handoff(current); approved=copy.deepcopy(current)
    approved["approval_record"]={"status":"APPROVED_FINAL","owner":"WEB_BRAIN","scope":c.expected_approval_scope(approved),"basis":"CURRENT_EXPLICIT_USER_DECISION","decision_ref":"conversation:current-explicit-existing-pr-replay-approval","binding":binding}
    approved["derived_gates"]=c.compute_gate_snapshot(approved); c.validate_capsule(approved); projection,_=c.compile_handoff(approved)
    return approved,projection,view,binding


def _capture_refresh(capture: dict[str, Any], *, stdout_bytes: bytes | None = None, stderr_bytes: bytes | None = None) -> None:
    if stdout_bytes is None:
        stdout_bytes = capture["stdout"].encode("utf-8")
    if stderr_bytes is None:
        stderr_bytes = capture["stderr"].encode("utf-8")
    capture["stdout_bytes_base64"] = base64.b64encode(stdout_bytes).decode("ascii")
    capture["stderr_bytes_base64"] = base64.b64encode(stderr_bytes).decode("ascii")
    capture["stdout_sha256"] = hashlib.sha256(stdout_bytes).hexdigest()
    capture["stderr_sha256"] = hashlib.sha256(stderr_bytes).hexdigest()
    capture["capture_sha256"] = c.digest(c._execution_capture_payload(capture))


def repository_return_bundle(projection: dict[str, Any], repo: pathlib.Path, base: str, head: str):
    ret, bundle = f.codex_return(projection)
    remote = git(repo, "config", "--get", "remote.origin.url")
    touched = [x for x in git(repo, "diff", "--name-only", base, head).splitlines() if x]
    diff_bytes = subprocess.run(["git", "-C", str(repo), "diff", "--binary", base, head], capture_output=True).stdout
    source_target=head if c._route_type(projection)=="EXISTING_PR_REPLAY" else base
    source_bytes = subprocess.run(["git", "-C", str(repo), "show", f"{source_target}:runtime/joyflow_dual_layer.py"], capture_output=True, check=True).stdout
    test_proc = subprocess.run(f.VALIDATION_ARGV, cwd=repo, capture_output=True)

    captures = {x["capture_id"]: x for x in bundle["raw_captures"]}
    captures["CAP_PREFLIGHT_OBJECT"]["observed_object"]["digest"] = source_target
    captures["CAP_PREFLIGHT_OBJECT"]["observation"] = {"repository_id": "example/repo", "remote_url": remote, "commit_sha": source_target, "role": "EXECUTION_RESULT" if source_target==head else "APPROVED_INPUT"}
    captures["CAP_PREFLIGHT_OBJECT"]["stdout"] = source_target + "\n"
    captures["CAP_PREFLIGHT_SOURCE"]["observed_object"]["digest"] = source_target
    captures["CAP_PREFLIGHT_SOURCE"]["observation"] = {"path": "runtime/joyflow_dual_layer.py", "file_sha256": hashlib.sha256(source_bytes).hexdigest(), "bytes": len(source_bytes)}
    captures["CAP_PREFLIGHT_SOURCE"]["stdout"] = source_bytes.decode("utf-8", "replace")
    captures["CAP_PREFLIGHT_TEST"]["observed_object"]["digest"] = source_target
    captures["CAP_PREFLIGHT_TEST"]["observation"]["target_ref"] = source_target
    captures["CAP_PREFLIGHT_TEST"]["stdout"] = test_proc.stdout.decode()
    captures["CAP_PREFLIGHT_TEST"]["stderr"] = test_proc.stderr.decode()
    captures["CAP_PREFLIGHT_TEST"]["exit_code"] = test_proc.returncode
    captures["CAP_EXEC_RESULT"]["observed_object"]["digest"] = head
    captures["CAP_EXEC_RESULT"]["observation"] = {"repository_id": "example/repo", "remote_url": remote, "commit_sha": head, "role": "EXECUTION_RESULT"}
    captures["CAP_EXEC_RESULT"]["stdout"] = head + "\n"
    captures["CAP_EXEC_DIFF"]["observed_object"]["digest"] = head
    captures["CAP_EXEC_DIFF"]["subject_id"] = head
    captures["CAP_EXEC_DIFF"]["observation"] = {"base_ref": base, "head_ref": head, "changed_paths": sorted(touched), "diff_sha256": hashlib.sha256(diff_bytes).hexdigest()}
    captures["CAP_EXEC_DIFF"]["stdout"] = diff_bytes.decode("utf-8", "replace")
    for phase in ("BEFORE","AFTER"):
        capture=captures.get(f"CAP_REPLAY_STATE_{phase}")
        if capture is not None:
            observation=c._repository_source_state_observation(repo,phase,[])
            capture["observed_object"]={"kind":"REPOSITORY_COMMIT","object_id":"example/repo","digest":head}
            capture["observation"]=observation
            capture["subject_id"]=f"{head}:{phase}"
            capture["stdout"]=(json.dumps(observation,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
    for capture in captures.values():
        if capture["capture_kind"] == "TEST_COMMAND" and capture["subject_type"] == "VALIDATION_CHECK":
            capture["observed_object"]["digest"] = head
            capture["observation"]["target_ref"] = head
            capture["stdout"] = test_proc.stdout.decode()
            capture["stderr"] = test_proc.stderr.decode()
            capture["exit_code"] = test_proc.returncode
        if capture["capture_id"] in {"CAP_PREFLIGHT_TEST"} or (capture["capture_kind"] == "TEST_COMMAND" and capture["subject_type"] == "VALIDATION_CHECK"):
            _capture_refresh(capture, stdout_bytes=test_proc.stdout, stderr_bytes=test_proc.stderr)
        elif capture["capture_id"] == "CAP_EXEC_DIFF":
            _capture_refresh(capture, stdout_bytes=diff_bytes, stderr_bytes=b"")
        elif capture["capture_kind"] == "REPOSITORY_STATE":
            _capture_refresh(capture,stdout_bytes=c.canonical_bytes(capture["observation"])+b"\n",stderr_bytes=b"")
        elif capture["capture_id"] == "CAP_PREFLIGHT_SOURCE":
            _capture_refresh(capture, stdout_bytes=source_bytes, stderr_bytes=b"")
        else:
            _capture_refresh(capture)

    evidence = {x["evidence_id"]: x for x in bundle["evidence_rows"]}
    for row in evidence.values():
        capture = captures[row["raw_output_ref"]]
        row["claim"] = c._direct_capture_claim(capture)
        row["claim_digest"] = c.digest(row["claim"])
        row["raw_output_sha256"] = capture["capture_sha256"]
    evidence["EXEC_DIFF"]["subject_id"] = head
    for phase in ("BEFORE","AFTER"):
        row=evidence.get(f"EXEC_REPLAY_STATE_{phase}")
        if row is not None: row["subject_id"]=f"{head}:{phase}"

    bundle["evidence_bundle_digest"] = c.digest(c.strip_digest(bundle, "evidence_bundle_digest"))
    ret["evidence_bundle_digest"] = bundle["evidence_bundle_digest"]
    lifecycle=ret["execution_lifecycle_result"]
    lifecycle["result_binding_digest"]=c._route_result_binding_digest(ret)
    lifecycle["validation_binding_digest"]=c._validation_binding_digest(ret)
    lifecycle["transition_digest"] = c.execution_lifecycle_result_digest(lifecycle)
    plan=projection.get("delivery",{}).get("evidence_transport") or {}
    if plan.get("mode")=="GITHUB_EXACT_OBJECT_IF_NEEDED":
        surface=plan["github_surface"]; transport_bytes=json.dumps(bundle,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
        receipt={"artifact_type":"EVIDENCE_TRANSPORT_RECEIPT","transport_mode":"GITHUB_EXACT_OBJECT","transport_role":"CURRENT_ROUND_EVIDENCE_BUNDLE_TRANSPORT_ONLY",
                 "project_id":projection["project_id"],"task_id":projection["task_id"],"round_id":projection["round_id"],"evidence_bundle_digest":bundle["evidence_bundle_digest"],
                 "repository_id":surface["repository_id"],"exact_commit_sha":"c"*40,"exact_path":surface["path_prefix"].rstrip("/")+"/evidence.zip",
                 "object_bytes":len(transport_bytes),"object_sha256":hashlib.sha256(transport_bytes).hexdigest(),"object_encoding":"CANONICAL_JSON_UTF8","temporary_ref":surface["temporary_ref"],
                 "retention_policy":plan["retention_policy"],"cleanup_trigger":plan["cleanup"]["trigger"],"receipt_digest":None}
        receipt["receipt_digest"]=c.digest(c.strip_digest(receipt,"receipt_digest")); ret["evidence_transport_receipt"]=receipt
    ret["return_digest"] = c.digest(c.strip_digest(ret, "return_digest"))
    return ret, bundle


def full_current_repository_chain(repo: pathlib.Path, base: str, head: str, evidence_transport_plan: dict[str, Any] | None = None):
    approved, projection, _, _ = repository_approved_projection(repo, base, evidence_transport_plan)
    executing = f.advance(approved, "CODEX_EXECUTION")
    ret, bundle = repository_return_bundle(projection, repo, base, head)
    reviewing = f.brain_review_capsule(executing, projection, ret, bundle)
    reviewed = f.revise_review(reviewing, "BRAIN_REVIEW", brain_verdict="PASS")
    return approved, projection, ret, bundle, reviewing, reviewed, None


def pr_record(projection: dict[str, Any], ret: dict[str, Any], bundle: dict[str, Any], brain_review_capsule: dict[str, Any], *, base: str, head: str, pr_number: int = 42) -> dict[str, Any]:
    decision = projection["repository_evidence"]["path_discovery"]["final_path_decision"]
    review_payload = brain_review_capsule["active_fibers"]["execution_review"]["payload"]
    touched = sorted(c._repository_review_evidence(ret,projection,bundle)["review_coverage_paths"])
    codex = {
        "block_version": 4,
        "writer_role": "CODEX",
        "technical_preflight_status": ret["technical_preflight"]["status"],
        "source_codex_return_digest": ret["return_digest"],
        "source_evidence_bundle_digest": bundle["evidence_bundle_digest"],
        "execution": {
            "status": ret["execution_status"],
            "checked_base_sha": base,
            "checked_head_sha": head,
            "actual_changed_paths": touched,
            "actual_changed_paths_digest": review.changed_paths_digest(touched),
            "changed_symbols": ["joyflow_phase1_review"],
            "implementation_mechanisms": ["current_repository_source_replay", "sealed_object_consumption"],
        },
        "local_test_refs": ["python tools/run_test_suite.py"],
        "evidence_refs": review._expected_codex_evidence_refs(ret),
        "unresolved_items": list(ret["unresolved_items"]),
        "codex_block_digest": None,
    }
    codex["codex_block_digest"] = review.digest(review.pr_block_payload(codex, "codex_block_digest"))
    brain = {
        "block_version": 4,
        "writer_role": "WEB_BRAIN",
        "execution_binding": {
            "repository_id": "example/repo",
            "project_id": projection["project_id"],
            "task_id": projection["task_id"],
            "round_id": projection["round_id"],
            "expected_base_commit": base,
            "current_head_sha": head,
            "projection_digest": projection["projection_digest"],
            "final_path_decision_digest": decision["decision_digest"],
            "approval_binding_digest": review.digest(c.approval_binding(projection)),
            "approved_allowed_paths": [x["path"] for x in decision["allowed_path_items"]],
        },
        "semantic_context": ["Current PR is reviewed against the exact approved Projection and repository source."],
        "selected_technical_route": ["Retain Codex bounded technical choice inside the approved paths."],
        "non_goals": ["No automatic approval, acceptance, merge or promotion."],
        "preserved_invariants": ["Single Web Brain, single Codex execution layer, user key gates and repository fact source."],
        "brain_review": {
            "status": review_payload["brain_review_verdict"],
            "reviewed_head_sha": head,
            "source_projection_digest": projection["projection_digest"],
            "source_final_path_decision_digest": decision["decision_digest"],
            "source_codex_return_digest": ret["return_digest"],
            "source_evidence_bundle_digest": bundle["evidence_bundle_digest"],
            "source_codex_block_digest": codex["codex_block_digest"],
            "source_brain_review_capsule_digest": brain_review_capsule["capsule_digest"],
            "unresolved_items": list(review_payload["unresolved_followups"]),
        },
        "merged_change_projection": None,
        "brain_block_digest": None,
    }
    brain["brain_block_digest"] = review.digest(review.pr_block_payload(brain, "brain_block_digest"))
    row = {
        "artifact_type": "JOYFLOW_PR_RECORD",
        "record_version": 4,
        "record_phase": "READY_FOR_USER_DECISION",
        "repository_id": "example/repo",
        "pr_number": pr_number,
        "base_sha": base,
        "head_sha": head,
        "brain_block": brain,
        "codex_block": codex,
        "record_digest": None,
    }
    row["record_digest"] = review.digest(review.strip_digest(row, "record_digest"))
    return row


def full_merge_authorization_chain(repo: pathlib.Path, base: str, head: str, evidence_transport_plan: dict[str, Any] | None = None) -> dict[str, Any]:
    approved, projection, ret, bundle, reviewing, reviewed, _ = full_current_repository_chain(repo, base, head, evidence_transport_plan)
    record = pr_record(projection, ret, bundle, reviewed, base=base, head=head)
    body = review.render_pr_body(record)
    before = review.repository_state_snapshot(repo)
    validated = review.validate_pr_record(
        record, repository=repo, projection=projection, codex_return=ret, evidence_bundle=bundle,
        brain_review_capsule=reviewed, merged_change_projection=None, current_base_sha=base,
        current_pr_number=42, replay_tests=True,
    )
    after = review.repository_state_snapshot(repo)
    ci = review.build_pr_ci_result(
        validated, pr_body_digest=hashlib.sha256(body.encode("utf-8")).hexdigest(),
        source_state_before=before, source_state_after=after, raw_output_ref="test:joyflow-pr-ci:stdout",
    )
    freeze = merge.build_merge_candidate_freeze(
        record=record, pr_body_digest=hashlib.sha256(body.encode("utf-8")).hexdigest(), pr_ci_result=ci,
        projection=projection, codex_return=ret, evidence_bundle=bundle, brain_review_capsule=reviewed,
    )
    merge.validate_merge_candidate_freeze(
        freeze, repository=repo, pr_body=body, projection=projection, codex_return=ret, evidence_bundle=bundle,
        brain_review_capsule=reviewed, pr_ci_result=ci, current_base_sha=base, current_pr_number=42,
    )
    acceptance_stage = f.revise_review(
        reviewed, "USER_ACCEPTANCE", merge_candidate_freeze_digest=freeze["freeze_digest"]
    )
    accepted = f.revise_review(
        acceptance_stage, "MERGE_DECISION", user_acceptance="PASS", merge_candidate_freeze_digest=freeze["freeze_digest"]
    )
    merge.validate_post_freeze_user_acceptance(
        accepted, merge_candidate_freeze=freeze, repository=repo, projection=projection,
        codex_return=ret, evidence_bundle=bundle, replay_source=True,
    )
    authorization = {
        "artifact_type": "USER_MERGE_AUTHORIZATION", "authorization_version": 2, "owner": "USER",
        "decision": "ALLOW_MERGE", "merge_candidate_freeze_digest": freeze["freeze_digest"],
        "user_acceptance_capsule_digest": accepted["capsule_digest"],
        "decision_ref": "conversation:current-explicit-user-merge-authorization", "authorization_digest": None,
    }
    authorization["authorization_digest"] = c.digest(c.strip_digest(authorization, "authorization_digest"))
    c.validate_user_merge_authorization(authorization, freeze, accepted)
    ready = f.merge_gate_record(accepted, freeze, "MERGE_READY")
    allowed = f.merge_gate_record(accepted, freeze, "MERGE_ALLOWED", authorization)
    c.validate_merge_gate_record(ready, freeze, accepted)
    c.validate_merge_gate_record(allowed, freeze, accepted, authorization)
    repository_merge_evidence = f.repository_merge_evidence(freeze)
    pointer = f.completion_pointer(freeze, accepted, authorization, repository_merge_evidence)
    c.validate_completion_pointer(pointer, freeze, accepted, authorization, repository_merge_evidence)
    merged = change_projection.build_merged_change_projection(
        pr_record=record, projection=projection, codex_return=ret, evidence_bundle=bundle,
        brain_review_capsule=reviewed, actual_changed_paths=record["codex_block"]["execution"]["actual_changed_paths"],
        completion_pointer=pointer, repository_merge_evidence=repository_merge_evidence,
    )
    return {
        "approved": approved, "projection": projection, "codex_return": ret, "evidence_bundle": bundle,
        "reviewing": reviewing, "brain_review": reviewed, "user_acceptance": accepted, "pr_record": record,
        "merged_change_projection": merged, "pr_body": body, "pr_ci_result": ci, "merge_ready": ready,
        "merge_candidate_freeze": freeze, "user_merge_authorization": authorization,
        "merge_allowed": allowed, "completion_pointer": pointer,
        "repository_merge_evidence": repository_merge_evidence,
    }
