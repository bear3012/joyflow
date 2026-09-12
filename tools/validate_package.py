#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
from typing import Any

sys.dont_write_bytecode = True

PHASE1_STATUS = "PHASE1_REPAIR_CANDIDATE_NOT_BASELINE"
PHASE1_PACKAGE_NAME = "JOYFLOW_PHASE1_COMBINED_CAPABILITY_COVERAGE_REPAIR_CANDIDATE"
PHASE1_MODEL_ID = PHASE1_PACKAGE_NAME + "_MODEL"
STALE_ACTIVE_CANDIDATE = "JOYFLOW_PHASE1F_CONFIRMED_TRANSITION_BOUNDARY_REPAIR_CANDIDATE"
METADATA_FILES = {"PACKAGE_MANIFEST.json", "VALIDATION_REPORT.json", "SHA256SUMS.txt"}
EXPECTED_MIGRATION_STATUSES = {
    "MAPPED_ONLY",
    "SEMANTICALLY_PRESERVED_AND_BEHAVIORALLY_VERIFIED",
    "DEFERRED_BY_EXACT_CURRENT_DECISION",
    "RETIRED_BY_CURRENT_USER_DECISION",
    "RETIRED_BY_CONFIRMED_SEMANTIC_SUPERSESSION",
}


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: pathlib.Path, root: pathlib.Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def package_files(root: pathlib.Path) -> list[pathlib.Path]:
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    )


def load_compiler(root: pathlib.Path):
    spec = importlib.util.spec_from_file_location("joyflow_compiler", root / "runtime/joyflow_dual_layer.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load compiler")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(cmd: list[str], cwd: pathlib.Path) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    return {
        "command": " ".join(str(x) for x in cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def current_candidate_identity(root: pathlib.Path) -> dict[str, Any]:
    manifest_path = root / "PACKAGE_MANIFEST.json"
    if not manifest_path.exists():
        raise RuntimeError("manifest missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    phase2_path = root / "PHASE2_STAGE_LINEAGE.json"
    if phase2_path.exists():
        lineage = json.loads(phase2_path.read_text(encoding="utf-8"))
        if lineage.get("artifact_type") != "PHASE2_STAGE_LINEAGE":
            raise RuntimeError("Phase 2 lineage identity mismatch")
        if manifest.get("artifact_status") != "PHASE2_REPAIR_CANDIDATE_NOT_BASELINE":
            raise RuntimeError("Phase 2 manifest status mismatch")
        if manifest.get("package_name") != lineage.get("package_name"):
            raise RuntimeError("Phase 2 manifest/lineage package mismatch")
        if manifest.get("repair_source_package") != lineage.get("parent_package"):
            raise RuntimeError("Phase 2 manifest/lineage parent mismatch")
        return {
            "layer": "PHASE2_CUMULATIVE_CANDIDATE",
            "artifact_status": manifest["artifact_status"],
            "package_name": manifest["package_name"],
            "stage_id": lineage.get("stage_id"),
            "lineage": lineage,
        }
    if manifest.get("artifact_status") != PHASE1_STATUS or manifest.get("package_name") != PHASE1_PACKAGE_NAME:
        raise RuntimeError("Phase 1 manifest identity mismatch")
    return {
        "layer": "PHASE1_CANDIDATE",
        "artifact_status": PHASE1_STATUS,
        "package_name": PHASE1_PACKAGE_NAME,
        "stage_id": "PR1F_MIGRATION_CLAIM_TRUTHFULNESS",
    }


def verify_manifest(root: pathlib.Path, identity: dict[str, Any] | None = None) -> dict[str, Any]:
    path = root / "PACKAGE_MANIFEST.json"
    if not path.exists():
        return {"status": "FAIL", "error": "manifest missing"}
    data = json.loads(path.read_text(encoding="utf-8"))
    try:
        identity = identity or current_candidate_identity(root)
    except Exception as exc:  # noqa: BLE001
        return {"status": "FAIL", "error": str(exc)}
    if data.get("artifact_status") != identity.get("artifact_status") or data.get("package_name") != identity.get("package_name"):
        return {"status": "FAIL", "error": "manifest identity mismatch"}
    rows = data.get("payload_files")
    metadata = set(data.get("integrity_metadata_files", []))
    if not isinstance(rows, list) or metadata != METADATA_FILES:
        return {"status": "FAIL", "error": "manifest structure or metadata set mismatch"}
    paths = [row.get("path") for row in rows]
    if None in paths or len(paths) != len(set(paths)):
        return {"status": "FAIL", "error": "manifest payload paths missing or duplicated"}
    if data.get("payload_file_count") != len(rows):
        return {"status": "FAIL", "error": "manifest payload count mismatch"}
    actual = {rel(p, root) for p in package_files(root)}
    expected = set(paths) | METADATA_FILES
    if actual != expected:
        return {
            "status": "FAIL", "error": "manifest file set mismatch",
            "missing": sorted(expected - actual), "unexpected": sorted(actual - expected),
        }
    bad = []
    for row in rows:
        target = root / row["path"]
        if row.get("sha256") != sha(target) or row.get("bytes") != target.stat().st_size:
            bad.append(row["path"])
    if bad:
        return {"status": "FAIL", "error": "manifest payload digest mismatch", "bad": bad}
    return {
        "status": "PASS",
        "payload_file_count": len(rows),
        "total_package_files": len(actual),
        "candidate_layer": identity.get("layer"),
        "package_name": identity.get("package_name"),
    }

def verify_sha_file(root: pathlib.Path, *, skip: bool = False) -> dict[str, Any]:
    if skip:
        return {"status": "DEFERRED_TO_FREEZE_STEP"}
    path = root / "SHA256SUMS.txt"
    if not path.exists():
        return {"status": "FAIL", "error": "SHA256SUMS.txt missing"}
    actual_files = {rel(p, root) for p in package_files(root)} - {"SHA256SUMS.txt"}
    listed: dict[str, str] = {}
    malformed: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if "  " not in line:
            malformed.append(line)
            continue
        expected, name = line.split("  ", 1)
        if name in listed:
            malformed.append(f"duplicate:{name}")
        listed[name] = expected
    if malformed:
        return {"status": "FAIL", "error": "malformed checksum file", "details": malformed}
    if set(listed) != actual_files:
        return {
            "status": "FAIL", "error": "checksum file set mismatch",
            "missing": sorted(actual_files - set(listed)), "unexpected": sorted(set(listed) - actual_files),
        }
    bad = [name for name, expected in listed.items() if sha(root / name) != expected]
    return {"status": "PASS" if not bad else "FAIL", "count": len(listed), "bad": bad}



def verify_stage_lineage(root: pathlib.Path) -> dict[str, Any]:
    path = root / "PHASE1_STAGE_LINEAGE.json"
    if not path.exists():
        return {"status": "FAIL", "error": "stage lineage missing"}
    data = json.loads(path.read_text(encoding="utf-8"))
    digest = data.get("lineage_digest")
    body = dict(data); body.pop("lineage_digest", None)
    actual = hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    expected_parent = {"name":"JOYFLOW_PHASE1E_AI_NATIVE_CHANGE_PROJECTION_REPAIR_CANDIDATE.zip","bytes":883786,"sha256":"9cb27a5e3d963cd79f976730697b195dc41d23f3dd74cafd17d7765ae5ddd1bc"}
    expected_stages = ["PR1A_PATH_DISCOVERY","PR1B_SEALED_OBJECT_EXECUTION_AND_REVIEW","PR1C_CURRENT_OBJECT_PR_BODY_CI","PR1D_REVIEW_ACCEPTANCE_FREEZE","PR1E_AI_NATIVE_CHANGE_PROJECTION","PR1F_MIGRATION_CLAIM_TRUTHFULNESS"]
    if data.get("artifact_type") != "PHASE1_STAGE_LINEAGE" or data.get("stage_id") != "PR1F_MIGRATION_CLAIM_TRUTHFULNESS":
        return {"status":"FAIL","error":"stage lineage identity mismatch"}
    if data.get("parent_package") != expected_parent:
        return {"status":"FAIL","error":"stage parent identity mismatch","actual":data.get("parent_package")}
    if data.get("accumulated_stages") != expected_stages:
        return {"status":"FAIL","error":"stage accumulation mismatch"}
    if data.get("repair_source_package") != {"name":"JOYFLOW_PHASE1F_CONFIRMED_TRANSITION_BOUNDARY_REPAIR_CANDIDATE.zip","bytes":989316,"sha256":"f3f8fe65cfc99715a0e56fbf4cdd2a8157ad9f81e75f14b9c8a021b1ca0f2c29"}: return {"status":"FAIL","error":"repair source identity mismatch"}
    if data.get("later_stage_inputs_are_targets_not_implementation_bases") is not True:
        return {"status":"FAIL","error":"later-stage target boundary missing"}
    if digest != actual:
        return {"status":"FAIL","error":"stage lineage digest mismatch","expected":digest,"actual":actual}
    return {"status":"PASS","stage_id":"PR1F_MIGRATION_CLAIM_TRUTHFULNESS","lineage_digest":digest,"parent_package":expected_parent}


def verify_current_candidate_documents(root: pathlib.Path, identity: dict[str, Any]) -> dict[str, Any]:
    expected_bootloader = root / "00_PROJECT_INSTRUCTIONS_BOOTLOADER_PHASE1_COMBINED_CAPABILITY_COVERAGE_REPAIR_CANDIDATE.md"
    stale_bootloaders = [p for p in root.glob("00_PROJECT_INSTRUCTIONS_BOOTLOADER_*.md") if p != expected_bootloader]
    required = {
        "bootloader": expected_bootloader,
        "phase1_scope": root / "PHASE1_SCOPE_AND_STATUS.md",
        "readme": root / "README.md",
        "matrix": root / "COLD_REVIEW_REPAIR_MATRIX.md",
        "repair_record": root / "PROTOCOL_REPAIR_RECORD.md",
        "identity_rule": root / "project_sources/14_PHASE1F_MIGRATION_CLAIM_TRUTHFULNESS.md",
        "authority_rule": root / "project_sources/16_PHASE1F_PRODUCT_DIRECTION_BOUND_DISPOSITION.md",
        "lifecycle_rule": root / "project_sources/17_PHASE1F_INSTANCE_TRANSITION_EVIDENCE_OUTCOME.md",
        "provenance_rule": root / "project_sources/18_PHASE1F_PROVENANCE_OBJECT_BINDING.md",
        "confirmed_boundary_rule": root / "project_sources/19_PHASE1F_CONFIRMED_TRANSITION_BOUNDARY.md",
        "combined_coverage_rule": root / "project_sources/20_PHASE1_COMBINED_CAPABILITY_COVERAGE.md",
    }
    if identity.get("layer") == "PHASE2_CUMULATIVE_CANDIDATE":
        required.update({
            "phase2_scope": root / "PHASE2_SCOPE_AND_STATUS.md",
            "phase2_lineage": root / "PHASE2_STAGE_LINEAGE.json",
            "phase2_truth_transport_rule": root / "project_sources/25_PHASE2_SEMANTIC_TRUTH_TRANSPORT_REPAIR.md",
            "phase2_structural_cognition_rule": root / "project_sources/27_PHASE2_STRUCTURAL_COGNITION_CONTINUITY.md",
        })
    missing = [name for name, path in required.items() if not path.is_file()]
    if missing or stale_bootloaders:
        return {"status":"FAIL","error":"current candidate document set mismatch","missing":missing,"stale_bootloaders":[p.name for p in stale_bootloaders]}
    texts={name:path.read_text(encoding="utf-8") for name,path in required.items() if path.suffix.lower() in {".md", ".yaml", ".yml"}}
    model_text = (root / "machine/joyflow_dual_layer_model.yaml").read_text(encoding="utf-8")
    capsule_schema = json.loads((root / "schemas/fibered_task_capsule.schema.json").read_text(encoding="utf-8"))
    stale_active_identity_files = []
    for candidate in package_files(root):
        if candidate.suffix.lower() not in {".md", ".json", ".yaml", ".yml", ".py"} or candidate.name in METADATA_FILES:
            continue
        body = candidate.read_text(encoding="utf-8")
        stale_active_tokens=(
            STALE_ACTIVE_CANDIDATE + "_MODEL",
            '"package_name": "' + STALE_ACTIVE_CANDIDATE + '"',
            "current_candidate: " + STALE_ACTIVE_CANDIDATE,
            '"object_id": "' + STALE_ACTIVE_CANDIDATE + '.zip"',
            '"subject_id": "' + STALE_ACTIVE_CANDIDATE + '"',
        )
        if any(token in body for token in stale_active_tokens):
            stale_active_identity_files.append(rel(candidate, root))
    checks = {
        "phase1_bootloader_foundation": texts["bootloader"].startswith("# JOYFLOW PHASE 1 COMBINED CAPABILITY COVERAGE REPAIR CANDIDATE BOOTLOADER"),
        "phase1_scope_foundation": "current_candidate: "+PHASE1_PACKAGE_NAME in texts["phase1_scope"],
        "repair_record_foundation": texts["repair_record"].startswith("# Protocol Repair Record — Phase 1 Combined Capability Coverage"),
        "identity_rule": "exact current PACKAGE_MANIFEST package name" in texts["identity_rule"],
        "authority_rule": "RULE_PRODUCT_DIRECTION_BOUND_DISPOSITION_AUTHORITY" in texts["authority_rule"],
        "sparse_user_gate": "RULE_SPARSE_USER_DECISION_GATE" in texts["authority_rule"],
        "phase_scope": "RULE_PR1F_MECHANISM_EFFECT_SCOPE" in texts["authority_rule"],
        "instance_transition_separation": "RULE_CURRENT_MIGRATION_INSTANCE_TRANSITION_CAPABILITY_SEPARATION" in texts["lifecycle_rule"],
        "evidence_outcome_contract": "RULE_DISPOSITION_EVIDENCE_OUTCOME_CONTRACT_COMPLETE" in texts["lifecycle_rule"],
        "public_transition_path": "RULE_PUBLIC_TRANSITION_PATH_POSITIVE_COVERAGE" in texts["lifecycle_rule"],
        "source_set_single_owner": "RULE_MAPPING_SOURCE_SET_SINGLE_OWNER" in texts["provenance_rule"],
        "semantic_evidence_exact_object": "RULE_SEMANTIC_EVIDENCE_EXACT_OBJECT_BINDING" in texts["provenance_rule"],
        "semantic_boundary": "RULE_SEMANTIC_EVIDENCE_MECHANICAL_SEMANTIC_BOUNDARY" in texts["provenance_rule"],
        "defer_status_truthfulness": "RULE_DEFERRED_STATUS_BASIS_TRUTHFULNESS" in texts["provenance_rule"],
        "validated_confirmed_boundary": "RULE_CONFIRMED_TRANSITION_VALIDATED_BOUNDARY" in texts["confirmed_boundary_rule"],
        "confirmed_seal_consumption": "RULE_CONFIRMED_TRANSITION_SEAL_CONSUMPTION" in texts["confirmed_boundary_rule"],
        "package_source_binding": "RULE_PACKAGE_RELATIVE_EXACT_SOURCE_BINDING" in texts["confirmed_boundary_rule"],
        "ordered_section_boundary": "RULE_ORDERED_SECTION_BOUNDARY" in texts["confirmed_boundary_rule"],
        "derived_mapping_status": "RULE_DERIVED_MAPPING_STATUS" in texts["confirmed_boundary_rule"],
        "claim_type_separation": "RULE_CAPABILITY_CLAIM_TYPE_SEPARATION" in texts["combined_coverage_rule"],
        "stage_presence_scope": "RULE_INHERITED_STAGE_PRESENCE_SCOPE" in texts["combined_coverage_rule"],
        "exact_rule_coverage": "RULE_VERIFIED_RULE_COVERAGE_EXACT" in texts["combined_coverage_rule"],
        "cross_stage_chain_scope": "RULE_VERIFIED_CROSS_STAGE_CHAIN_SCOPE" in texts["combined_coverage_rule"],
        "coverage_relation_binding": "RULE_CAPABILITY_COVERAGE_RELATION_BINDING" in texts["combined_coverage_rule"],
        "stale_scope_absent": "PR1C is not entered" not in texts["bootloader"],
        "phase1_model_id_foundation": model_text.startswith("model_id: " + PHASE1_MODEL_ID + "\n"),
        "phase1_capsule_schema_model_id": capsule_schema.get("properties", {}).get("model_id", {}).get("const") == PHASE1_MODEL_ID,
        "no_stale_active_model_or_artifact_identity": not stale_active_identity_files,
    }
    if identity.get("layer") == "PHASE2_CUMULATIVE_CANDIDATE":
        phase2_facts={}
        for line in texts["phase2_scope"].splitlines():
            if ":" in line and not line.lstrip().startswith("#"):
                key,value=line.split(":",1); key=key.strip()
                if key and " " not in key: phase2_facts[key]=value.strip()
        checks.update({
            "current_readme_phase2": texts["readme"].startswith("# Joyflow Phase 2"),
            "current_matrix_phase2_repair": texts["matrix"].startswith("# Stranger Cold Review"),
            "current_phase2_scope": phase2_facts.get("current_candidate")==identity.get("package_name") and phase2_facts.get("status")=="CANDIDATE_NOT_BASELINE",
            "phase2_semantic_truth_transport": "RULE_PHASE2_SEMANTIC_TRUTH_TRANSPORT" in texts["phase2_truth_transport_rule"],
            "phase2_layered_package_identity": "RULE_PHASE2_LAYERED_PACKAGE_IDENTITY" in texts["phase2_truth_transport_rule"],
            "phase2_structural_cognition": "RULE_PHASE2_STRUCTURAL_DISCOVERY_TRIGGER_BOUNDARY" in texts["phase2_structural_cognition_rule"],
        })
    else:
        checks.update({
            "current_readme_phase1": texts["readme"].startswith("# Joyflow Phase 1 Combined Capability Coverage Repair Candidate"),
            "current_matrix_phase1": texts["matrix"].startswith("# Phase 1 Combined Capability Coverage Repair Matrix"),
        })
    active_targets=[]
    for md in root.rglob("*.md"):
        lines=md.read_text(encoding="utf-8").splitlines()
        for idx,line in enumerate(lines):
            if line != "REVIEW_TARGET:":
                continue
            fields={}
            for child in lines[idx+1:]:
                if not child.strip():
                    break
                if not child.startswith((" ", "\t")):
                    break
                stripped=child.strip()
                if ":" in stripped:
                    key,value=stripped.split(":",1); fields[key]=value.strip()
            if fields.get("target_is_authoritative_for_this_review")=="YES" and fields.get("target_name_or_ref"):
                active_targets.append(rel(md,root))
                break
    checks["no_embedded_authoritative_review_target"] = not active_targets
    historical=(root/"DESIGN_DECISION_REPOSITORY_ANCHORED_DUAL_LAYER.md").read_text(encoding="utf-8")
    checks["historical_review_context_marked"]="HISTORICAL_REVIEW_CONTEXT:" in historical and "authoritative_for_current_review: NO" in historical
    bad=[name for name,ok in checks.items() if not ok]
    return {
        "status":"PASS" if not bad else "FAIL",
        "bad":bad,
        "bootloader":expected_bootloader.name,
        "candidate_layer":identity.get("layer"),
        "current_package_name":identity.get("package_name"),
        "active_authoritative_review_targets":active_targets,
        "stale_active_identity_files":stale_active_identity_files,
    }

def duplicate_top_level_functions(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names = [node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return sorted({name for name in names if names.count(name) > 1})


def check_ok(report: dict[str, Any], command: str, action) -> bool:
    try:
        value = action()
    except Exception as exc:  # noqa: BLE001
        report["checks"].append({"command": command, "returncode": 2, "stderr": str(exc)})
        return False
    report["checks"].append({"command": command, "returncode": 0, "stdout": "PASS", "details": value})
    return True


def validate(root: pathlib.Path, *, skip_integrity: bool = False) -> dict[str, Any]:
    try:
        identity = current_candidate_identity(root)
    except Exception as exc:  # noqa: BLE001
        return {
            "artifact_status": "UNKNOWN",
            "package_name": "UNKNOWN",
            "root": str(root),
            "checks": [{"command": "current candidate identity", "returncode": 2, "stderr": str(exc)}],
            "verdict": "BLOCK",
        }
    report: dict[str, Any] = {
        "artifact_status": identity["artifact_status"],
        "package_name": identity["package_name"],
        "candidate_layer": identity["layer"],
        "current_stage_id": identity.get("stage_id"),
        "root": str(root),
        "checks": [],
        "verdict": "BLOCK",
    }

    stale_names = {
        "test_phase1_dual_layer.py", "test_phase1_gate_hardening.py", "test_phase1_human_semiautomatic.py",
        "USER_DECISION_EVENT_EXECUTION.json", "CODEX_EXECUTION_EVIDENCE.json",
        "promotion_candidate.schema.json", "repository_promotion_evidence.schema.json",
        "merge_authorization.schema.json",
    }
    stale = [rel(p, root) for p in package_files(root) if p.name in stale_names]
    if stale:
        report["checks"].append({"command": "stale artifact scan", "returncode": 2, "stderr": str(stale)})
        return report
    report["checks"].append({"command": "stale artifact scan", "returncode": 0, "stdout": "PASS"})

    current_docs = verify_current_candidate_documents(root, identity)
    report["checks"].append({"command":"current candidate document identity","returncode":0 if current_docs.get("status")=="PASS" else 2,"stdout":"PASS" if current_docs.get("status")=="PASS" else "","stderr":"" if current_docs.get("status")=="PASS" else json.dumps(current_docs,ensure_ascii=False),"details":current_docs})
    if current_docs.get("status") != "PASS":
        return report

    duplicates = duplicate_top_level_functions(root / "runtime/joyflow_dual_layer.py")
    if duplicates:
        report["checks"].append({"command": "runtime duplicate function scan", "returncode": 2, "stderr": str(duplicates)})
        return report
    report["checks"].append({"command": "runtime duplicate function scan", "returncode": 0, "stdout": "PASS"})

    commands = []
    if identity.get("layer") == "PHASE2_CUMULATIVE_CANDIDATE":
        commands.append([sys.executable, str(root / "tools/validate_phase2_candidate.py")])
    commands.extend([
        [sys.executable, str(root / "tools/generate_mechanical_assets.py"), "--check"],
        [sys.executable, str(root / "tools/generate_old_rule_migration.py"), "--check"],
        [sys.executable, str(root / "tools/validate_migration_claims.py"), "--root", str(root)],
        [sys.executable, str(root / "tools/generate_all_examples.py"), "--check"],
        [sys.executable, str(root / "runtime/joyflow_source_validator.py"), str(root)],
        [sys.executable, str(root / "tools/run_test_suite.py")],
    ])
    test_result: dict[str, Any] | None = None
    for cmd in commands:
        result = run(cmd, root)
        report["checks"].append(result)
        if any(str(item).endswith("run_test_suite.py") for item in cmd):
            test_result = result
        if result["returncode"] != 0:
            return report

    lineage_result = verify_stage_lineage(root)
    report["stage_lineage"] = lineage_result
    if lineage_result.get("status") != "PASS":
        return report

    compiler = load_compiler(root)

    def validate_examples() -> dict[str, Any]:
        capsule = json.loads((root / "examples/APPROVED_TASK_CAPSULE.json").read_text(encoding="utf-8"))
        projection = json.loads((root / "examples/CODEX_HANDOFF_PROJECTION.json").read_text(encoding="utf-8"))
        approval = json.loads((root / "examples/APPROVAL_RECORD.json").read_text(encoding="utf-8"))
        prompt = (root / "examples/COMPLETE_CODEX_PROMPT.md").read_text(encoding="utf-8")
        codex_return = json.loads((root / "examples/CODEX_EXECUTION_RETURN.json").read_text(encoding="utf-8"))
        evidence_bundle = json.loads((root / "examples/CODEX_EXECUTION_EVIDENCE_BUNDLE.json").read_text(encoding="utf-8"))
        brain_review = json.loads((root / "examples/BRAIN_REVIEW_CAPSULE.json").read_text(encoding="utf-8"))
        merge_decision = json.loads((root / "examples/REPOSITORY_MERGE_DECISION_CAPSULE.json").read_text(encoding="utf-8"))
        merge_ready = json.loads((root / "examples/MERGE_GATE_RECORD_READY.json").read_text(encoding="utf-8"))
        merge_freeze = json.loads((root / "examples/MERGE_CANDIDATE_FREEZE_READY.json").read_text(encoding="utf-8"))
        user_authorization = json.loads((root / "examples/USER_MERGE_AUTHORIZATION.json").read_text(encoding="utf-8"))
        merge_allowed = json.loads((root / "examples/MERGE_GATE_RECORD_ALLOWED.json").read_text(encoding="utf-8"))
        completion = json.loads((root / "examples/TASK_COMPLETION_POINTER.json").read_text(encoding="utf-8"))
        repository_merge_evidence = (root / "examples/RAW_REPOSITORY_MERGE_EVIDENCE.json").read_bytes()
        merged_change_projection = json.loads((root / "examples/MERGED_CHANGE_PROJECTION.json").read_text(encoding="utf-8"))
        pr_record = json.loads((root / "examples/PR_RECORD_READY.json").read_text(encoding="utf-8"))
        pr_ci_result = json.loads((root / "examples/PR_CI_RESULT.json").read_text(encoding="utf-8"))
        artifact_projection = json.loads((root / "examples/ARTIFACT_CODEX_HANDOFF_PROJECTION.json").read_text(encoding="utf-8"))
        artifact_return = json.loads((root / "examples/ARTIFACT_CODEX_EXECUTION_RETURN.json").read_text(encoding="utf-8"))
        artifact_bundle = json.loads((root / "examples/ARTIFACT_CODEX_EXECUTION_EVIDENCE_BUNDLE.json").read_text(encoding="utf-8"))
        artifact_closed = json.loads((root / "examples/ARTIFACT_CLOSED_CAPSULE.json").read_text(encoding="utf-8"))
        discovery_capsule = json.loads((root / "examples/PATH_DISCOVERY_AUTHORIZED_CAPSULE.json").read_text(encoding="utf-8"))
        discovery_projection = json.loads((root / "examples/PATH_DISCOVERY_PROJECTION.json").read_text(encoding="utf-8"))
        discovery_return = json.loads((root / "examples/PATH_DISCOVERY_RETURN.json").read_text(encoding="utf-8"))
        discovery_prompt = (root / "examples/PATH_DISCOVERY_COMPLETE_CODEX_PROMPT.md").read_text(encoding="utf-8")
        compiler.validate_capsule(capsule, require_projection_ready=True)
        compiler.verify_prompt(projection, approval, prompt)
        regenerated, regenerated_prompt = compiler.compile_handoff(capsule)
        if regenerated != projection or regenerated_prompt != prompt:
            raise compiler.JoyflowError("example artifacts are not deterministic")
        compiler.validate_codex_execution_return_structure(codex_return, projection, evidence_bundle)
        compiler.validate_capsule(brain_review)
        compiler.validate_capsule(merge_decision)
        compiler.validate_schema(merged_change_projection, root / "schemas/merged_change_projection.schema.json")
        if merged_change_projection["projection_digest"] != compiler.digest(compiler.strip_digest(merged_change_projection, "projection_digest")):
            raise compiler.JoyflowError("merged change projection example digest mismatch")
        if pr_record["brain_block"]["merged_change_projection"] is not None:
            raise compiler.JoyflowError("pre-merge PR example must not embed a Merged Change Projection")
        if "merged_change_projection_digest" in pr_ci_result:
            raise compiler.JoyflowError("pre-merge PR CI must not consume the post-merge Merged Change Projection")
        if any(k in merge_freeze for k in ("merged_change_projection_digest","user_acceptance_capsule_digest","merge_ready_record_digest")):
            raise compiler.JoyflowError("Merge Candidate Freeze must precede acceptance and derived merge-gate snapshots")
        compiler.validate_user_merge_authorization(user_authorization, merge_freeze, merge_decision)
        compiler.validate_merge_gate_record(merge_ready, merge_freeze, merge_decision)
        compiler.validate_merge_gate_record(merge_allowed, merge_freeze, merge_decision, user_authorization)
        compiler.validate_completion_pointer(completion, merge_freeze, merge_decision, user_authorization, repository_merge_evidence)
        if merged_change_projection.get("provenance",{}).get("task_completion_pointer_digest") != completion["pointer_digest"]:
            raise compiler.JoyflowError("post-merge projection does not bind the observed completion pointer")
        compiler.validate_codex_execution_return_structure(artifact_return, artifact_projection, artifact_bundle)
        compiler.validate_capsule(artifact_closed)
        compiler.validate_capsule(discovery_capsule, require_projection_ready=True)
        compiler.verify_prompt(discovery_projection, discovery_capsule['approval_record'], discovery_prompt)
        compiler.validate_path_discovery_return_structure(discovery_return, discovery_projection)
        try:
            compiler.validate_promotion_gate()
        except compiler.JoyflowError:
            pass
        else:
            raise compiler.JoyflowError("automatic promotion must remain blocked")
        return {"prompt_round_trip": "PASS", "current_round_return_bundle": "PASS", "hybrid_path_discovery": "PASS", "codex_bounded_technical_authority": "PASS", "honest_blocked_return": "PASS", "stage_gates": "PASS", "artifact_repository_review_split": "PASS", "merged_change_projection_chain": "PASS", "merge_record_continuity": "PASS", "completion_pointer_chain": "PASS"}

    if not check_ok(report, "single-active-task and hybrid path-discovery example chains", validate_examples):
        return report

    migration = json.loads((root / "OLD_RULE_MIGRATION.json").read_text(encoding="utf-8"))
    capability_status = json.loads((root / "CAPABILITY_STATUS.json").read_text(encoding="utf-8"))
    allowed_migration_statuses = EXPECTED_MIGRATION_STATUSES
    if len(migration) != 176 or any(
        row.get("migration_status") not in allowed_migration_statuses
        or not row.get("brain_capability_interpretation")
        or not row.get("legacy_source_sha256")
        or not row.get("brain_mapping_id")
        or not row.get("preservation_mechanism")
        or not row.get("verification_refs")
        or not isinstance(row.get("target_verification"), dict)
        for row in migration
    ):
        report["checks"].append({"command":"legacy migration claim truthfulness","returncode":2,"stderr":"migration evidence/status incomplete"})
        return report
    counts = {status: sum(row["migration_status"] == status for row in migration) for status in sorted(allowed_migration_statuses)}
    if capability_status.get("migration_counts") != counts:
        report["checks"].append({"command":"legacy migration claim truthfulness","returncode":2,"stderr":"capability status migration counts mismatch"})
        return report
    if counts.get("SEMANTICALLY_PRESERVED_AND_BEHAVIORALLY_VERIFIED", 0) != 0 or capability_status.get("legacy_semantic_equivalence_confirmed_rows") != 0: report["checks"].append({"command":"legacy migration claim truthfulness","returncode":2,"stderr":"legacy equivalence overstated"}); return report
    report["checks"].append({"command":"legacy migration claim truthfulness","returncode":0,"stdout":f"PASS rows=176 counts={counts}"})

    forbidden = ["CORE_AUTHORITY", "SCHEMA_AUTHORITY", "GOLDEN_CASES_AUTHORITY"]
    found = [rel(p, root) for p in package_files(root) if any(x in p.name for x in forbidden)]
    if found:
        report["checks"].append({"command": "authority aggregator absence", "returncode": 2, "stderr": str(found)})
        return report
    report["checks"].append({"command": "authority aggregator absence", "returncode": 0, "stdout": "PASS"})

    runtime_text = (root / "runtime/joyflow_dual_layer.py").read_text(encoding="utf-8")
    forbidden_cli = ["complete-promotion", "merge-authorization", "--gh-executable"]
    present_cli = [token for token in forbidden_cli if token in runtime_text]
    if present_cli:
        report["checks"].append({"command": "automatic control-plane absence", "returncode": 2, "stderr": str(present_cli)})
        return report
    report["checks"].append({"command": "automatic control-plane absence", "returncode": 0, "stdout": "PASS"})

    model = compiler.load_model()
    stage_policy = model.get("phase1_stage_policy", {})
    expected_parent = lineage_result["parent_package"]
    expected_completed = ["PR1A_PATH_DISCOVERY","PR1B_SEALED_OBJECT_EXECUTION_AND_REVIEW","PR1C_CURRENT_OBJECT_PR_BODY_CI","PR1D_REVIEW_ACCEPTANCE_FREEZE","PR1E_AI_NATIVE_CHANGE_PROJECTION"]
    if (stage_policy.get("current_stage") != "PR1F_MIGRATION_CLAIM_TRUTHFULNESS"
            or stage_policy.get("completed_stages") != expected_completed
            or stage_policy.get("parent_package") != expected_parent
            or stage_policy.get("later_stage_inputs_are_targets_not_implementation_bases") is not True
            or stage_policy.get("repair_source_package") != {"name":"JOYFLOW_PHASE1F_CONFIRMED_TRANSITION_BOUNDARY_REPAIR_CANDIDATE.zip","bytes":989316,"sha256":"f3f8fe65cfc99715a0e56fbf4cdd2a8157ad9f81e75f14b9c8a021b1ca0f2c29"}):
        report["checks"].append({"command":"Phase 1 stage lineage policy","returncode":2,"stderr":"model and lineage object mismatch"})
        return report
    report["checks"].append({"command":"Phase 1 stage lineage policy","returncode":0,"stdout":"PASS exact PR1E parent"})
    migration_policy=model.get("legacy_migration_truth_policy",{})
    required_migration_policy={
      "disposition_decision_set_required":True,
      "generator_may_not_author_disposition":True,
      "current_candidate_all_dispositions":"NOT_EVALUATED",
      "current_candidate_mapped_only_rows":176,
      "current_candidate_legacy_equivalence_confirmed_rows":0,
      "current_target_behavior_status_mechanically_derived":True,
      "legacy_equivalence_unresolved_targets_separate_from_behavior_unverified_targets":True,
      "phase_effect_separate_from_semantic_closure":True,
      "exact_legacy_source_identity_set_required":True,
      "exact_legacy_section_text_required_for_equivalence":True,
      "brain_owned_semantic_mapping_required":True,
      "generator_may_not_derive_or_modify_brain_mapping":True,
      "strict_schema_before_semantic_validation":True,
      "disposition_authority_bound_to_product_direction":True,
      "web_brain_may_close_preserving_technical_dispositions":True,
      "per_row_user_approval_required":False,
      "changed_confirmed_direction_requires_user_decision":True,
      "grouped_user_decision_reference_allowed":True,
      "unresolved_material_effect_remains_open":True,
      "pr1f_mechanism_effect_does_not_determine_phase1_completion":True,
      "historical_review_context_must_be_non_authoritative":True,
      "disposition_transition_contract_single_source":True,
      "schema_validator_and_deriver_share_transition_contract":True,
      "technical_retirement_requires_confirmed_semantic_gate":True,
      "legal_transition_positive_coverage_required":True,
      "current_instance_separate_from_transition_fixture":True,
      "transition_fixture_test_only_non_authoritative":True,
      "confirmed_mapping_requires_exact_source_bytes_and_section_digest":True,
      "transition_contract_evidence_outcome_complete":True,
      "public_transition_path_positive_coverage_required":True,
      "fixture_cannot_modify_current_rows":True,
      "mapping_source_set_identity_single_owner":True,
      "semantic_evidence_exact_object_binding_required":True,
      "semantic_evidence_semantic_sufficiency_owner":"WEB_BRAIN",
      "deferred_status_neutral_exact_decision":True,
      "confirmed_transition_validated_boundary_required":True,
      "confirmed_transition_consumes_mapping_and_disposition_seals":True,
      "bundled_exact_source_root_package_relative":True,
      "exact_section_markers_ordered_nonempty":True,
      "top_level_mapping_status_derived":True,
      "validated_transition_inputs_are_temporary_process_state":True,
    }
    if set(migration_policy.get("allowed_statuses",[])) != EXPECTED_MIGRATION_STATUSES or any(migration_policy.get(k) != v for k,v in required_migration_policy.items()):
        report["checks"].append({"command":"migration evidence-strength policy","returncode":2,"stderr":"migration policy incomplete"})
        return report
    claim_policy=model.get("candidate_capability_claim_policy",{})
    required_claim_policy={
      "artifact_role":"GENERATED_NON_AUTHORITATIVE_NAVIGATION_VIEW",
      "may_satisfy_stage_gate":False,
      "may_satisfy_phase_gate":False,
      "package_may_self_claim_independent_cold_review":False,
      "package_may_self_claim_baseline_or_release":False,
      "exact_capability_claim_registry_required":True,
      "verification_contract_digest_required":True,
      "typed_stage_and_rule_coverage_required":True,
      "capability_claim_type_separation_required":True,
      "inherited_stage_presence_not_behavior_verification":True,
      "verified_rule_coverage_exact_relation_required":True,
      "verified_cross_stage_chain_exact_relation_required":True,
      "cross_stage_chain_does_not_imply_full_stage_coverage":True,
    }
    if any(claim_policy.get(k) != v for k,v in required_claim_policy.items()):
        report["checks"].append({"command":"candidate capability claim boundary","returncode":2,"stderr":"capability claim boundary incomplete"})
        return report
    report["checks"].append({"command":"migration evidence-strength policy","returncode":0,"stdout":"PASS per-target behavior evidence and weaker-claim separation"})
    report["checks"].append({"command":"candidate capability claim boundary","returncode":0,"stdout":"PASS no self-claimed cold review, baseline or release"})
    expected_deferred = {
        "REPOSITORY_CACHE", "CAPSULE_AS_PERSISTENT_PROJECT_STATE", "FEATURE_SLICE_CACHE",
        "LONG_TERM_REPOSITORY_CONTEXT", "JOYKEEP_FULL_REFACTOR", "CROSS_CODEX_UNBYPASSABLE_HOOK",
        "AUTOMATIC_PROMOTION", "USER_IDENTITY_AUTHENTICATION", "IMMUTABLE_PARENT_CHAIN",
        "TRUSTED_GITHUB_OBSERVER",
    }
    if not expected_deferred.issubset(set(model.get("deferred_capabilities", []))):
        report["checks"].append({"command": "deferred and out-of-scope boundary", "returncode": 2, "stderr": "required deferred capabilities missing"})
        return report
    architecture = model.get("architecture", {})
    if architecture.get("automation_boundary") != "HUMAN_SEMIAUTOMATIC_NO_AUTOMATIC_PROMOTION":
        report["checks"].append({"command": "human semi-automatic architecture", "returncode": 2, "stderr": "automation boundary mismatch"})
        return report
    if architecture.get("task_concurrency") != "ONE_ACTIVE_TASK_PER_PROJECT_ROUND" or model.get("single_active_round", {}).get("global_scheduler_required") is not False:
        report["checks"].append({"command": "single-active-task round architecture", "returncode": 2, "stderr": "single task round boundary mismatch"})
        return report
    report["checks"].append({"command": "human semi-automatic architecture", "returncode": 0, "stdout": "PASS"})
    report["checks"].append({"command": "single-active-task round architecture", "returncode": 0, "stdout": "PASS without global scheduler"})
    ci_policy = model.get("github_ci_mechanical_gate", {})
    required_ci = {
        "read_only": True,
        "requires_exact_current_repository": True,
        "requires_base_ancestor_of_head": True,
        "requires_exact_projection_return_bundle_review_capsule": True,
        "requires_complete_current_diff_equality": True,
        "does_not_approve_accept_or_merge": True,
    }
    if any(ci_policy.get(k) is not v for k, v in required_ci.items()):
        report["checks"].append({"command": "current-object PR body and CI gate", "returncode": 2, "stderr": "PR CI mechanical policy incomplete"})
        return report
    report["checks"].append({"command": "current-object PR body and CI gate", "returncode": 0, "stdout": "PASS exact current repository and sealed source chain"})
    freeze_policy = model.get("merge_freeze_policy", {})
    required_freeze = {
        "requires_exact_current_pr_record_and_ci": True,
        "requires_exact_brain_review_capsule": True,
        "occurs_before_user_acceptance_when_applicable": True,
        "requires_merge_gate_record": False,
        "requires_merged_change_projection": False,
        "current_status": "FROZEN_FOR_USER_DECISIONS",
        "user_merge_authorization_active": True,
        "automatic_merge": False,
    }
    if any(freeze_policy.get(k) != v for k, v in required_freeze.items()):
        report["checks"].append({"command": "review acceptance and merge-freeze gate", "returncode": 2, "stderr": "merge freeze policy incomplete"})
        return report
    report["checks"].append({"command": "review acceptance and merge-freeze gate", "returncode": 0, "stdout": "PASS exact Brain Review/CI freeze precedes independent user acceptance and final merge authorization"})
    projection_policy = model.get("merged_change_projection_policy", {})
    required_projection = {
        "owner": "WEB_BRAIN",
        "authority": "NAVIGATION_AND_CONTEXT_ONLY",
        "lifecycle": "CONDITIONAL_POST_MERGE_DERIVED_ARTIFACT",
        "requires_observed_merge_completion_pointer": True,
        "requires_exact_projection_return_bundle_review_sources": True,
        "requires_complete_reviewed_diff_path_set": True,
        "cannot_substitute_current_repository_diff_tests_or_evidence": True,
        "generated_only_when_long_term_continuity_value_justifies_it": True,
        "blocks_pre_merge_gate": False,
        "temporary_goal_conditioned_fibers_are_nonpersistent": True,
    }
    if any(projection_policy.get(k) != v for k, v in required_projection.items()):
        report["checks"].append({"command": "AI-native merged change projection policy", "returncode": 2, "stderr": "projection policy incomplete"})
        return report
    report["checks"].append({"command": "AI-native merged change projection policy", "returncode": 0, "stdout": "PASS conditional post-merge navigation-only projection"})
    completion_policy = model.get("task_completion_policy", {})
    required_completion = {
        "requires_exact_merge_candidate_freeze": True,
        "requires_exact_post_freeze_user_acceptance_when_applicable": True,
        "requires_exact_user_merge_authorization": True,
        "requires_merge_ready_or_merge_allowed_record": False,
        "records_observed_repository_merge_only": True,
        "does_not_merge": True,
    }
    if any(completion_policy.get(k) != v for k, v in required_completion.items()):
        report["checks"].append({"command": "completion pointer exact merge chain", "returncode": 2, "stderr": "completion policy incomplete"})
        return report
    report["checks"].append({"command": "completion pointer exact merge chain", "returncode": 0, "stdout": "PASS binds exact freeze + acceptance + USER authorization and records observed merge without performing merge"})
    if architecture.get('path_discovery_topology') not in {'GITHUB_DEFAULT_WITH_CODEX_GOAL_CONDITIONED_STRUCTURAL_DISCOVERY_BEFORE_FINAL_BOUNDARY','BRAIN_ACCESSIBLE_REPOSITORY_EVIDENCE_WITH_CODEX_GOAL_CONDITIONED_STRUCTURAL_DISCOVERY_BEFORE_FINAL_BOUNDARY'}:
        report['checks'].append({'command':'hybrid path discovery architecture','returncode':2,'stderr':'path discovery topology mismatch'})
        return report
    discovery_profile=model['route_profiles']['READ_ONLY_DISCOVERY']
    if not discovery_profile.get('executable') or discovery_profile.get('execution_mode') != 'READ_ONLY' or model.get('path_discovery_policy',{}).get('final_boundary_owner') != 'WEB_BRAIN':
        report['checks'].append({'command':'hybrid path discovery architecture','returncode':2,'stderr':'read-only discovery or final boundary ownership mismatch'})
        return report
    discovery_policy=model.get('path_discovery_policy',{})
    structural_policy=model.get('structural_cognition_policy',{})
    if identity.get('stage_id') in {'PR2V_READ_ONLY_DISCOVERY_BRAIN_AUTHORIZATION_ALIGNMENT','PR2W_EPHEMERAL_GITHUB_EVIDENCE_TRANSPORT_REPAIR','PR2X_ARCHITECTURE_CONVERGENCE_CLOSURE_REPAIR'}:
        req=model.get('approval_requirements',{})
        if req.get('mutating_requires_user_approval') is not True or req.get('read_only_discovery_requires_separate_user_approval') is not False or req.get('read_only_discovery_authorization_owner')!='WEB_BRAIN' or req.get('read_only_discovery_authorization_status')!='AUTHORIZED_READ_ONLY_DISCOVERY' or req.get('read_only_discovery_authorization_basis')!='WEB_BRAIN_BOUNDED_READ_ONLY_DISCOVERY_AUTHORIZATION':
            report['checks'].append({'command':'read-only discovery authorization boundary','returncode':2,'stderr':'read-only Brain authorization / mutating user approval split mismatch'})
            return report
        report['checks'].append({'command':'read-only discovery authorization boundary','returncode':0,'stdout':'PASS Web Brain may authorize exact bounded pure read-only discovery; mutation/material execution still requires explicit user approval'})
    if identity.get('stage_id')=='PR2X_ARCHITECTURE_CONVERGENCE_CLOSURE_REPAIR':
        role=model.get('role_executability_policy',{}); approval=model.get('mutation_execution_envelope_policy',{}); inv=model.get('global_invariant_policy',{}); pol=model.get('evidence_transport_policy',{})
        if role.get('web_brain_surface')!='WEB_ONLY' or role.get('executor_surface')!='LOCAL_CODEX' or role.get('handoff_topology')!='USER_MEDIATED_SEMIAUTOMATIC' or role.get('logical_authorization_is_not_automatic_invocation') is not True or role.get('connector_specific_dependency_forbidden') is not True or role.get('background_controller_required') is not False:
            report['checks'].append({'command':'PR2X real-role executability','returncode':2,'stderr':'Web Brain / Local Codex physical handoff policy mismatch'}); return report
        if approval.get('stable_across_same_semantic_rework') is not True or approval.get('material_change_invalidates_prior_authorization') is not True or inv.get('residual_risk_acceptance_cannot_waive_active_global_invariant') is not True:
            report['checks'].append({'command':'PR2X approval/invariant convergence','returncode':2,'stderr':'mutation-envelope or global-invariant policy mismatch'}); return report
        if pol.get('transported_object_bytes_are_exact_canonical_evidence_bundle') is not True or pol.get('temporary_ref_namespace')!='refs/heads/joyflow-evidence/' or pol.get('cleanup_continuation_terminal_basis')!='TASK_TERMINAL_EVIDENCE':
            report['checks'].append({'command':'PR2X Evidence transport convergence','returncode':2,'stderr':'exact-byte / namespace / terminal cleanup policy mismatch'}); return report
        schema_expect={
            'codex_handoff_projection.schema.json':'joyflow://codex-handoff-projection-v11',
            'codex_execution_return.schema.json':'joyflow://codex-execution-return-v11',
            'evidence_transport_receipt.schema.json':'joyflow://evidence-transport-receipt-v2',
            'evidence_transport_cleanup_continuation.schema.json':'joyflow://evidence-transport-cleanup-continuation-v2',
        }
        for name,sid in schema_expect.items():
            if json.loads((root / 'schemas' / name).read_text(encoding='utf-8')).get('$id')!=sid:
                report['checks'].append({'command':'PR2X schema identities','returncode':2,'stderr':f'{name} identity mismatch'}); return report
        report['checks'].append({'command':'PR2X architecture convergence','returncode':0,'stdout':'PASS stable mutation envelope, exact Evidence transport, user-mediated real-role handoff, no background controller'})
    if identity.get('stage_id')=='PR2W_EPHEMERAL_GITHUB_EVIDENCE_TRANSPORT_REPAIR':
        pol=model.get('evidence_transport_policy',{}); merge=model.get('merge_boundary',{})
        required_transport={
            'role':'OPTIONAL_TRANSPORT_ADAPTER_FOR_CURRENT_ROUND_EVIDENCE_BUNDLE',
            'github_transport_requires_user_approved_remote_mutation':True,
            'ephemeral_by_default':True,
            'background_cleanup_service_forbidden':True,
            'cleanup_continuation_owner':'WEB_BRAIN',
            'cleanup_continuation_requires_original_user_approved_mutating_projection':True,
            'cleanup_continuation_merged_pr_terminal_basis':'TASK_COMPLETION_POINTER',
            'cleanup_ref_must_still_match_receipt_commit':True,
            'cleanup_scope':'DELETE_EXACT_TEMPORARY_REF_ONLY',
        }
        if any(pol.get(k)!=v for k,v in required_transport.items()) or merge.get('transport_only_evidence_remote_mutation_requires_product_pr') is not False or merge.get('transport_only_evidence_remote_mutation_requires_user_execution_approval') is not True or merge.get('product_or_governance_repository_change_requires_pr') is not True:
            report['checks'].append({'command':'ephemeral GitHub Evidence transport boundary','returncode':2,'stderr':'Evidence transport authority/PR/cleanup boundary mismatch'})
            return report
        schema_expect={
            'codex_handoff_projection.schema.json':'joyflow://codex-handoff-projection-v10',
            'codex_execution_return.schema.json':'joyflow://codex-execution-return-v10',
            'evidence_transport_receipt.schema.json':'joyflow://evidence-transport-receipt-v1',
            'evidence_transport_cleanup_continuation.schema.json':'joyflow://evidence-transport-cleanup-continuation-v1',
        }
        for name,sid in schema_expect.items():
            if json.loads((root / 'schemas' / name).read_text(encoding='utf-8')).get('$id')!=sid:
                report['checks'].append({'command':'ephemeral GitHub Evidence transport boundary','returncode':2,'stderr':f'{name} identity mismatch'})
                return report
        report['checks'].append({'command':'ephemeral GitHub Evidence transport boundary','returncode':0,'stdout':'PASS existing Evidence Bundle only; optional user-approved transport-only GitHub mutation; product PR-first preserved; exact preauthorized terminal cleanup; no background service'})
    required_structural_policy={
        'trigger':'MATERIAL_ARCHITECTURE_UNCERTAINTY',
        'discovery_owner':'CODEX',
        'architecture_proposal_owner':'CODEX',
        'project_level_review_owner':'WEB_BRAIN',
        'final_technical_closure_owner':'WEB_BRAIN',
        'discovery_scope':'GOAL_CONDITIONED_SEMANTIC_RELATION_UNFOLDING',
        'final_mutation_paths_frozen_after_structural_closure':True,
    }
    if discovery_policy.get('structural_discovery_reader')!='CODEX_LOCAL_READ_ONLY' or discovery_policy.get('structural_discovery_may_precede_final_mutation_path_freeze') is not True:
        report['checks'].append({'command':'structural discovery ordering','returncode':2,'stderr':'Codex structural discovery must be read-only and may precede final mutation path freeze'})
        return report
    if any(structural_policy.get(k)!=v for k,v in required_structural_policy.items()):
        report['checks'].append({'command':'structural cognition authority','returncode':2,'stderr':'Codex proposal / Brain closure authority split mismatch'})
        return report
    persistent=structural_policy.get('persistent_projection',{})
    if persistent.get('artifact_role')!='DERIVED_NON_AUTHORITATIVE_STRUCTURAL_NAVIGATION' or persistent.get('sparse_only') is not True or persistent.get('based_on_exact_commit') is not True or persistent.get('stale_or_conflict_never_overrides_repository') is not True:
        report['checks'].append({'command':'structural projection authority','returncode':2,'stderr':'long-term structural projection is not sparse, commit-anchored, derived, and below repository authority'})
        return report
    report['checks'].append({'command':'hybrid path discovery architecture','returncode':0,'stdout':'PASS ordinary GitHub-first; material architecture uncertainty permits Codex read-only structural discovery before Brain final mutation boundary'})
    codex_authority=model.get('codex_technical_authority',{})
    if architecture.get('codex_execution_authority') != 'BOUNDED_ROUTE_SELECTION_WITH_TASK_BOUND_PREFLIGHT_AND_TYPED_FACT_DERIVATION' or codex_authority.get('role') != 'BOUNDED_EXECUTION_TECHNICAL_AUTHORITY':
        report['checks'].append({'command':'Codex bounded technical authority','returncode':2,'stderr':'Codex technical-authority boundary mismatch'})
        return report
    forbidden_codex={'CHANGE_PRODUCT_SEMANTICS','CHANGE_JOYFLOW_AUTHORITY_TOPOLOGY','EXPAND_ALLOWED_PATHS','FILL_BRAIN_REVIEW','FILL_USER_APPROVAL_OR_ACCEPTANCE','AUTHORIZE_MERGE'}
    if not forbidden_codex.issubset(set(codex_authority.get('cannot',[]))):
        report['checks'].append({'command':'Codex bounded technical authority','returncode':2,'stderr':'Codex prohibited authority set incomplete'})
        return report
    route_policy=model.get('codex_technical_evidence_policy',{})
    required_route_flags={
        'brain_candidates_are_non_exhaustive': True,
        'codex_alternative_route_allowed_within_approved_object': True,
        'projection_obligations_must_be_exactly_answered': True,
        'raw_execution_capture_bytes_digest_bound': True,
        'initial_review_seal_requires_exact_projection_return_bundle': True,
        'artifact_route_requires_exact_source_artifact_identity': True,
        'preflight_questions_are_canonical_and_task_bound': True,
        'candidate_pass_requires_approved_expected_paths': True,
        'direct_tool_facts_separated_from_codex_derivations': True,
        'typed_runners_derive_execution_object_identity': True,
        'later_review_preserves_source_derived_snapshot': True,
        'operational_validation_requires_current_source': True,
        'repository_and_artifact_facts_replayed_from_source': True,
        'approved_test_commands_replayed_by_validator_or_ci': True,
        'structural_fixture_validation_has_no_material_authority': True,
        'review_direct_facts_replayed_against_current_source': True,
        'approved_validation_object_is_argv_plus_cwd': True,
        'display_command_is_derived_only': True,
        'operational_test_replay_cannot_be_disabled': True,
        'task_object_lifecycle_is_temporary_and_digest_bound': True,
        'approved_input_result_validation_and_review_objects_are_distinct': True,
        'repository_result_requires_approved_base_ancestry': True,
        'final_repository_tests_run_at_exact_result_head': True,
        'artifact_review_binds_exact_output_set': True,
        'ignored_coverage_uses_typed_exact_or_bounded_recursive_entries': True,
        'repository_and_artifact_reviews_use_dedicated_operational_entries': True,
        'discovery_source_object_binds_original_projection_return_and_selected_items': True,
        'ignored_exact_symlinks_use_lstat_without_target_follow': True,
        'ignored_recursive_exclusions_prune_subtrees_before_read': True,
        'declared_ignored_objects_join_local_direct_fact_set': True,
        'artifact_result_is_canonical_complete_output_set': True,
        'artifact_final_validation_targets_output_set_not_source': True,
        'new_artifact_route_uses_exact_source_material_set': True,
        'boundary_safe_repository_object_resolution': True,
        'final_validation_is_observation_only': True,
        'sealed_inputs_and_results_rechecked_after_each_validation_command': True,
        'validation_workspace_object_set_rechecked_after_each_validation_command': True,
        'artifact_output_root_is_dedicated_complete_namespace': True,
        'review_source_evidence_rows_are_immutable': True,
        'changed_sealed_object_requires_new_identity_and_revalidation': True,
    }
    path_policy=model.get('path_discovery_binding_policy',{})
    required_path_flags={
        'pr_diff_paths_replayed_from_exact_base_head': True,
        'local_semantic_relations_are_codex_derivations': True,
        'declared_ignored_coverage_is_bounded_and_task_relevant': True,
        'full_ignored_or_filesystem_scan_forbidden': True,
        'structural_relations_require_typed_semantic_mapping': True,
        'structural_question_closure_required_before_route_recommendation': True,
        'structural_fold_preserves_counterevidence_unresolved_and_omissions': True,
        'persistent_structural_projection_is_sparse_derived_and_commit_anchored': True,
        'persistent_structural_projection_never_overrides_current_repository': True,
    }
    if any(path_policy.get(k) is not v for k,v in required_path_flags.items()):
        report['checks'].append({'command':'hybrid path source grounding','returncode':2,'stderr':'Diff, derivation or bounded ignored-path policy incomplete'})
        return report
    if any(route_policy.get(k) is not v for k,v in required_route_flags.items()):
        report['checks'].append({'command':'Codex bounded technical authority','returncode':2,'stderr':'route-space or source-bound evidence policy incomplete'})
        return report
    report['checks'].append({'command':'Codex bounded technical authority','returncode':0,'stdout':'PASS non-exhaustive Brain candidates, exact obligations, bounded Codex alternative, source-bound evidence'})
    if architecture.get('temporary_task_object_lifecycle') != 'AUTHORIZED_INPUT_TO_DISCOVERY_TO_BOUNDARY_TO_RESULT_TO_VALIDATION_TO_REVIEW' or architecture.get('operational_route_entries') != 'DEDICATED_REPOSITORY_AND_ARTIFACT_REVIEW' or architecture.get('sealed_object_consumption') != 'BOUNDARY_SAFE_READ_COMPLETE_WORKSPACE_OBSERVATION_IMMUTABLE_REVIEW_SOURCE':
        report['checks'].append({'command':'temporary task-object lifecycle architecture','returncode':2,'stderr':'shared lifecycle or dedicated operational route entry mismatch'})
        return report
    report['checks'].append({'command':'temporary task-object lifecycle architecture','returncode':0,'stdout':'PASS approved input → discovery → boundary → result → validation → review'})

    manifest_result = verify_manifest(root, identity)
    report["manifest"] = manifest_result
    if manifest_result.get("status") != "PASS":
        return report

    sha_result = verify_sha_file(root, skip=skip_integrity)
    report["sha256sums"] = sha_result
    if sha_result.get("status") == "FAIL":
        return report

    rule_count = len(re.findall(
        r"^canonical_rule_id:",
        "\n".join(p.read_text(encoding="utf-8") for p in (root / "project_sources").glob("*.md")),
        re.M,
    ))
    test_output = "" if test_result is None else test_result["stderr"] + test_result["stdout"]
    match = re.search(r"Ran (\d+) tests", test_output)
    report.update({
        "rule_count": rule_count,
        "legacy_migration_rows": len(migration),
        "tests_passed": int(match.group(1)) if match else None,
        "route_profiles": len(model.get("route_profiles", {})),
        "mechanical_invariants": len(model.get("invariants", [])),
        "build_identity": compiler.build_identity(),
        "verdict": "PASS_CANDIDATE_TREE",
    })
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--report")
    parser.add_argument("--skip-integrity", action="store_true")
    args = parser.parse_args()
    root = pathlib.Path(args.root).resolve()
    report = validate(root, skip_integrity=args.skip_integrity)
    if args.report:
        pathlib.Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["verdict"] == "PASS_CANDIDATE_TREE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
