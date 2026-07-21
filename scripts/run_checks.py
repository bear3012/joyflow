#!/usr/bin/env python3
"""Run Joyflow mechanical checks and bind the result to current inputs and git state."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
from joyflow_common import ROOT, AUTHORITY_ONLY_PATHS, bundle_hash, canonical_json_hash, changed_files, current_branch, current_head, derive_reviewed_source_head, evidence_suffix_status, executor_output_paths, file_hash, is_within_allowed, read_json, resolve_base_ref, source_bundle_hash, task_state_shape_ok, write_json
from validate_semantic_closure import execution_release_allowed, validate_all as validate_semantic_closure

RESULTS: List[Dict[str, Any]] = []
def add(name: str, passed: bool, detail: Any = "") -> None: RESULTS.append({"name": name, "passed": bool(passed), "detail": detail})
def exists(rel: str) -> bool: return (ROOT / rel).exists()

def main() -> int:
    contract=read_json("runtime/translation_contract.json",default={}); interpretation=read_json("runtime/codex_execution_interpretation.json",default={}); bridge=read_json("runtime/execution_bridge_package.json",default={}); manifest=read_json("runtime/codex_launch_manifest.json",default={}); routing=read_json("runtime/routing_result.json",default={})
    required=["subject/task_state.json","runtime/product_meaning_closure.json","runtime/translation_contract.json","runtime/meaning_delta.json","runtime/golden_cases.json","runtime/user_acceptance_plan.json","runtime/codex_execution_interpretation.json","runtime/routing_result.json","runtime/execution_bridge_package.json","runtime/context_palace.md","runtime/codex_task_packet.md","runtime/codex_launch_manifest.json","runtime/contract_red_team_review.md","observer/contract_red_team_receipt.json","observer/brain_semantic_review.json","observer/acceptance_receipt.json","observer/pr_receipt.json","observer/human_review_packet.md","spec/semantic_closure.md"]
    for rel in required: add(f"exists:{rel}",exists(rel),rel)
    state=read_json("subject/task_state.json",default={}); add("task_state_shape_exact",isinstance(state,dict) and task_state_shape_ok(state),list(state.keys()) if isinstance(state,dict) else type(state).__name__)
    semantic_ok,semantic_findings=validate_semantic_closure(include_review=True); add("semantic_closure_artifacts_valid",semantic_ok,semantic_findings)
    task_id=contract.get("task_id"); add("task_identity_matches_bridge",bridge.get("task_identity",{}).get("task_id")==task_id,bridge.get("task_identity")); add("task_identity_matches_routing",routing.get("task_id")==task_id,routing.get("task_id")); add("task_identity_matches_state",state.get("task_id")==task_id,state.get("task_id"))
    bridge_hash=canonical_json_hash(bridge); add("manifest_bridge_hash_matches",manifest.get("bridge_hash")==bridge_hash,{"expected":bridge_hash,"actual":manifest.get("bridge_hash")})
    input_hashes=manifest.get("input_hashes") if isinstance(manifest.get("input_hashes"),dict) else {}; actual={}; errors=[]
    for rel in input_hashes:
        try: actual[rel]=file_hash(rel)
        except Exception as exc: errors.append(f"{rel}: {exc}")
    add("manifest_input_hashes_match",not errors and actual==input_hashes,{"errors":errors,"expected":input_hashes,"actual":actual}); expected_bundle=canonical_json_hash(input_hashes); add("manifest_input_bundle_hash_matches",manifest.get("input_bundle_hash")==expected_bundle,{"expected":expected_bundle,"actual":manifest.get("input_bundle_hash")})
    packet=(ROOT/"runtime/codex_task_packet.md").read_text(encoding="utf-8") if exists("runtime/codex_task_packet.md") else ""; add("packet_contains_bridge_hash",f"BRIDGE_HASH: {bridge_hash}" in packet,bridge_hash); add("packet_contains_input_bundle_hash",f"INPUT_BUNDLE_HASH: {expected_bundle}" in packet,expected_bundle)
    authority_paths=list(bridge.get("protected_authority_artifacts",[])) if isinstance(bridge.get("protected_authority_artifacts"),list) else []; authority_bundle,authority_hashes=bundle_hash(authority_paths); truth=bridge.get("truth_fingerprint",{}) if isinstance(bridge.get("truth_fingerprint"),dict) else {}
    add("bridge_authority_hashes_match",bridge.get("authority_input_hashes")==authority_hashes); add("bridge_authority_bundle_matches",truth.get("authority_bundle_sha256")==authority_bundle)
    source_bundle,source_hashes=source_bundle_hash(); add("bridge_source_hashes_match",bridge.get("source_input_hashes")==source_hashes,{"expected_count":len(source_hashes),"actual_count":len(bridge.get("source_input_hashes",{})) if isinstance(bridge.get("source_input_hashes"),dict) else -1}); add("bridge_source_bundle_matches",truth.get("source_bundle_sha256")==source_bundle,{"expected":source_bundle,"actual":truth.get("source_bundle_sha256")})
    executor=set(executor_output_paths(bridge)); brain=set(bridge.get("brain_only_outputs",[])) if isinstance(bridge.get("brain_only_outputs"),list) else set(); human=set(bridge.get("human_only_outputs",[])) if isinstance(bridge.get("human_only_outputs"),list) else set(); add("executor_outputs_exclude_brain_and_human_authority",not(executor&(brain|human|AUTHORITY_ONLY_PATHS)),sorted(executor&(brain|human|AUTHORITY_ONLY_PATHS))); add("required_outputs_equal_executor_outputs",set(bridge.get("required_output_files",[]))==executor)
    mode=contract.get("lifecycle_mode"); release=execution_release_allowed(contract,interpretation)
    if mode=="REFERENCE_CANDIDATE": add("reference_candidate_non_executable",bridge.get("execution_allowed") is False and bridge.get("target_lane")=="HARD_STOP_LANE"); add("reference_candidate_packet_halts","HALT" in packet and "Do not modify repository files" in packet)
    else: add("active_task_release_is_authentic",release,interpretation); add("active_task_bridge_executable",bridge.get("execution_allowed") is True and bridge.get("target_lane")!="HARD_STOP_LANE"); add("active_task_packet_not_halt","\nHALT\n" not in packet)
    red=read_json("observer/contract_red_team_receipt.json",default={}); add("contract_red_team_not_blocking",red.get("verdict") in {"PASS","WARN"} and not bool(red.get("execution_blocked")),red)
    branch_ok,branch=current_branch(); head_ok,head=current_head(); source_ok,source_head,stripped,source_err=derive_reviewed_source_head("HEAD"); suffix_ok,suffix_files,suffix_violations,suffix_err=evidence_suffix_status(source_head,"HEAD") if source_ok else (False,[],[],source_err); base_ok,base_ref,base_err=resolve_base_ref()
    add("git_branch_detected",branch_ok,branch); add("git_head_detected",head_ok,head); add("reviewed_source_head_derived",source_ok,{"reviewed_source_head_sha":source_head,"stripped_evidence_commits":stripped,"error":source_err}); add("current_head_is_evidence_only_suffix",source_ok and suffix_ok,{"files":suffix_files,"violations":suffix_violations,"error":suffix_err}); add("git_base_ref_detected",base_ok,base_ref if base_ok else base_err)
    changed_ok,changed,changed_err=changed_files(); add("git_changed_files_detected",changed_ok,changed if changed_ok else changed_err); allowed=bridge.get("allowed_paths",[]) if isinstance(bridge.get("allowed_paths"),list) else []
    if changed_ok:
        filtered=[p for p in changed if "__pycache__/" not in p and not p.endswith(".pyc")]; violations=[p for p in filtered if not is_within_allowed(p,allowed)]; add("pr_diff_within_allowed_paths",not violations,{"base_ref":base_ref,"changed_files":filtered,"violations":violations,"allowed_paths":allowed}); add("non_main_for_repo_changing_task",not filtered or(branch_ok and branch not in {"main","master"}),branch)
    else: add("pr_diff_within_allowed_paths",False,changed_err); add("non_main_for_repo_changing_task",False,changed_err)
    pr=read_json("observer/pr_receipt.json",default={}); add("pr_receipt_shape",isinstance(pr,dict) and {"branch_name","pr_url","pr_required","pr_present","base_sha","verified_source_head_sha"}.issubset(pr.keys()),pr); add("pr_receipt_branch_matches",not branch_ok or pr.get("branch_name")==branch)
    review=read_json("observer/brain_semantic_review.json",default={}); add("brain_review_source_bundle_bound",review.get("reviewed_source_bundle_sha256")==source_bundle if review.get("review_verdict")=="PASS" else True,review.get("review_verdict"))
    exit_code=0 if all(x["passed"] for x in RESULTS) else 1
    out={"artifact_type":"JOYFLOW_RAW_CHECK_RESULTS","artifact_version":"2","task_id":task_id,"command":"bash tests/run_checks.sh","exit_code":exit_code,"git_binding":{"branch":branch,"current_head_sha":head,"reviewed_source_head_sha":source_head,"evidence_only_suffix_files":suffix_files,"stripped_evidence_commits":stripped,"head_sha":head,"base_ref":base_ref},"bridge_hash":bridge_hash,"input_bundle_hash":expected_bundle,"source_bundle_sha256":source_bundle,"checks":RESULTS}
    write_json("observer/raw_check_results.json",out); print("JOYFLOW_CHECKS_PASS" if exit_code==0 else "JOYFLOW_CHECKS_FAIL"); return exit_code
if __name__=="__main__": raise SystemExit(main())
