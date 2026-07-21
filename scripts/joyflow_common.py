#!/usr/bin/env python3
"""Shared mechanical helpers for the Joyflow repository candidate."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
TASK_STATE_KEYS = ["task_id", "task_status", "target_lane", "graph_sync_required", "formal_pending"]
HARD_STOP_KEYWORDS = ["auth", "authentication", "authorize", "authorization", "permission", "permissions", "login", "password", "token", "secret", "secrets", "payment", "billing", "stripe", "database schema", "schema migration", "migration", "drop table", "delete data", "destructive", "production", "prod", "state machine", "routing governance", "subject schema", "bridge contract", "safety boundary", "boundary freeze"]
REVIEW_KEYWORDS = ["unclear", "unknown", "tbd", "todo", "maybe", "not sure", "open question", "uncertain", "ambiguous", "risk", "refactor", "scripts/", "runtime/", "spec/", "subject/", "observer/", "shadow/"]
LOW_RISK_HINTS = ["readme", "docs/", "documentation", "usage note", "typo", "copy", "text"]
AUTHORITY_ONLY_PATHS = {"observer/brain_semantic_review.json", "observer/acceptance_receipt.json", "observer/pr_receipt.json", "observer/human_review_packet.md"}
EVIDENCE_ONLY_SUFFIX_PATHS = {"observer/raw_check_results.json", "observer/brain_semantic_review.json", "observer/acceptance_receipt.json", "observer/pr_receipt.json", "observer/human_review_packet.md", "observer/reconcile_result.json"}
DETERMINISTIC_RUNTIME_PATHS = ["runtime/codex_interpretation_request.md", "runtime/routing_result.json", "runtime/execution_bridge_package.json", "runtime/context_palace.md", "runtime/codex_task_packet.md", "runtime/codex_launch_manifest.json", "subject/task_state.json"]
SOURCE_BUNDLE_PATHS = ["AGENTS.md", ".codex/rules.md", ".github/workflows/joyflow-checks.yml", "scripts/joyflow_common.py", "scripts/validate_semantic_closure.py", "scripts/route_task.py", "scripts/build_bridge.py", "scripts/build_codex_interpretation_request.py", "scripts/build_context_palace.py", "scripts/build_codex_packet.py", "scripts/run_checks.py", "scripts/reconcile.py", "scripts/refresh_runtime.sh", "tests/run_checks.sh", "tests/test_semantic_closure.py", "spec/semantic_closure.md", "spec/flow_graph.md", "spec/node_cards.md", "spec/edge_cards.md", "spec/rule_cards.md", "runtime/product_meaning_closure.json", "runtime/translation_contract.json", "runtime/meaning_delta.json", "runtime/golden_cases.json", "runtime/user_acceptance_plan.json", "runtime/codex_execution_interpretation.json", "observer/contract_red_team_receipt.json", "runtime/contract_red_team_review.md"]

def read_text(rel: str, default: str = "") -> str:
    path = ROOT / rel
    return default if not path.exists() else path.read_text(encoding="utf-8")

def write_text(rel: str, text: str) -> None:
    path = ROOT / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text, encoding="utf-8")

def read_json(rel: str, default: Any = None) -> Any:
    path = ROOT / rel
    if not path.exists():
        if default is not None: return default
        raise FileNotFoundError(rel)
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        if default is not None: return default
        raise ValueError(f"empty JSON file: {rel}")
    return json.loads(text)

def write_json(rel: str, data: Any) -> None:
    path = ROOT / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def stable_task_id(seed: str) -> str:
    normalized = " ".join(seed.split()) or "joyflow-task"; return "JF-" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]

def canonical_json_hash(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()

def file_hash(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()

def bundle_hash(paths: Sequence[str]) -> Tuple[str, Dict[str, str]]:
    hashes = {rel: file_hash(rel) for rel in paths if (ROOT / rel).is_file()}; return canonical_json_hash(hashes), hashes

def source_bundle_hash() -> Tuple[str, Dict[str, str]]:
    return bundle_hash(SOURCE_BUNDLE_PATHS)

def lower_join(value: Any) -> str:
    if isinstance(value, str): return value.lower()
    if isinstance(value, dict): return " ".join(f"{k} {lower_join(v)}" for k, v in value.items()).lower()
    if isinstance(value, list): return " ".join(lower_join(v) for v in value).lower()
    return str(value).lower()

def _keyword_pattern(keyword: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![a-z0-9_]){re.escape(keyword.lower())}(?![a-z0-9_])", re.IGNORECASE)

def keyword_hits(text: str, keywords: Iterable[str]) -> List[str]:
    low = text.lower(); return sorted({kw for kw in keywords if _keyword_pattern(kw).search(low)})

def normalize_path(value: str) -> str:
    if not isinstance(value, str): raise TypeError("path must be a string")
    raw = value.replace("\\", "/").strip()
    while raw.startswith("./"): raw = raw[2:]
    if not raw: return ""
    if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw): raise ValueError(f"absolute path is not allowed: {value}")
    parts = PurePosixPath(raw).parts
    if any(part in {"", ".."} for part in parts): raise ValueError(f"unsafe path is not allowed: {value}")
    if any(ord(ch) < 32 for ch in raw): raise ValueError("control characters are not allowed in paths")
    normalized = "/".join(part for part in parts if part != ".")
    return normalized + ("/" if raw.endswith("/") and normalized else "")

def is_within_allowed(path: str, allowed_roots: Iterable[str]) -> bool:
    try: p = normalize_path(path).rstrip("/")
    except (TypeError, ValueError): return False
    for root_value in allowed_roots:
        try: root = normalize_path(root_value).rstrip("/")
        except (TypeError, ValueError): continue
        if root and (p == root or p.startswith(root + "/")): return True
    return False

def git(args: List[str]) -> Tuple[int, str, str]:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE); return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

def current_branch() -> Tuple[bool, str]:
    code, out, err = git(["branch", "--show-current"]); return (False, err or out or "cannot determine branch") if code != 0 or not out else (True, out)

def current_head() -> Tuple[bool, str]:
    code, out, err = git(["rev-parse", "HEAD"]); return (False, err or out or "cannot determine HEAD") if code != 0 or not out else (True, out)

def _ref_exists(ref: str) -> bool:
    return git(["rev-parse", "--verify", "--quiet", ref])[0] == 0

def derive_reviewed_source_head(current_ref: str = "HEAD") -> Tuple[bool, str, List[str], str]:
    if not _ref_exists(current_ref): return False, "", [], "current ref does not exist"
    code, out, err = git(["rev-parse", current_ref])
    if code != 0 or not out: return False, "", [], err or "cannot resolve current ref"
    cursor = out.strip(); evidence_commits: List[str] = []
    while True:
        code, parent, _ = git(["rev-parse", "--verify", "--quiet", f"{cursor}^"])
        if code != 0 or not parent: break
        code, changed, diff_err = git(["diff-tree", "--no-commit-id", "--name-only", "-r", cursor])
        if code != 0: return False, "", evidence_commits, diff_err or f"cannot inspect commit {cursor}"
        try: files = sorted({normalize_path(item) for item in changed.splitlines() if item.strip()})
        except (TypeError, ValueError) as exc: return False, "", evidence_commits, str(exc)
        if not files or any(path not in EVIDENCE_ONLY_SUFFIX_PATHS for path in files): break
        evidence_commits.append(cursor); cursor = parent.strip()
    return True, cursor, evidence_commits, ""

def evidence_suffix_status(source_head: str, current_ref: str = "HEAD") -> Tuple[bool, List[str], List[str], str]:
    if not isinstance(source_head, str) or not source_head.strip(): return False, [], [], "reviewed source head is missing"
    if not _ref_exists(source_head) or not _ref_exists(current_ref): return False, [], [], "reviewed source head or current ref does not exist"
    code, _, err = git(["merge-base", "--is-ancestor", source_head, current_ref])
    if code != 0: return False, [], [], err or "reviewed source head is not an ancestor of current ref"
    code, out, err = git(["diff", "--name-only", "--diff-filter=ACMRD", f"{source_head}..{current_ref}"])
    if code != 0: return False, [], [], err or "cannot inspect evidence-only suffix"
    try: files = sorted({normalize_path(item) for item in out.splitlines() if item.strip()})
    except (TypeError, ValueError) as exc: return False, [], [], str(exc)
    violations = [path for path in files if path not in EVIDENCE_ONLY_SUFFIX_PATHS]
    return not violations, files, violations, ""

def resolve_base_ref() -> Tuple[bool, str, str]:
    candidates: List[str] = []
    explicit = os.environ.get("JOYFLOW_BASE_REF"); github_base = os.environ.get("GITHUB_BASE_REF")
    if explicit: candidates.append(explicit)
    if github_base: candidates.extend([f"origin/{github_base}", github_base])
    candidates.extend(["origin/main", "main", "origin/master", "master", "HEAD^"])
    for candidate in candidates:
        if candidate and _ref_exists(candidate): return True, candidate, ""
    return False, "", "cannot resolve base ref; set JOYFLOW_BASE_REF"

def changed_files() -> Tuple[bool, List[str], str]:
    code, _, err = git(["rev-parse", "--is-inside-work-tree"])
    if code != 0: return False, [], err or "not a git repository"
    files: List[str] = []; base_ok, base_ref, base_err = resolve_base_ref()
    if base_ok:
        code, out, err = git(["diff", "--name-only", "--diff-filter=ACMRD", f"{base_ref}...HEAD"])
        if code != 0: return False, [], err or f"cannot diff {base_ref}...HEAD"
        if out: files.extend(out.splitlines())
    elif os.environ.get("GITHUB_ACTIONS") == "true": return False, [], base_err
    for args in (["diff", "--name-only", "HEAD"], ["diff", "--name-only", "--cached"]):
        code, out, err = git(list(args))
        if code != 0: return False, [], err
        if out: files.extend(out.splitlines())
    code, out, err = git(["ls-files", "--others", "--exclude-standard"])
    if code != 0: return False, [], err
    if out: files.extend(out.splitlines())
    try: normalized = sorted({normalize_path(f) for f in files if f.strip()})
    except (TypeError, ValueError) as exc: return False, [], str(exc)
    return True, normalized, ""

def task_state_shape_ok(data: Dict[str, Any]) -> bool:
    return list(data.keys()) == TASK_STATE_KEYS

def ensure_task_state_update(task_id: str, target_lane: str, graph_sync_required: bool = False) -> None:
    state = read_json("subject/task_state.json", default={}); existing_pending = state.get("formal_pending", []) if isinstance(state, dict) else []
    write_json("subject/task_state.json", {"task_id": task_id, "task_status": "ROUTED" if target_lane else "IDLE", "target_lane": target_lane, "graph_sync_required": bool(graph_sync_required), "formal_pending": existing_pending if isinstance(existing_pending, list) else []})

def infer_allowed_paths(contract: Dict[str, Any], target_lane: str) -> List[str]:
    explicit = contract.get("allowed_paths")
    if isinstance(explicit, list) and all(isinstance(x, str) for x in explicit): return sorted({normalize_path(item) for item in explicit if item.strip()})
    return [] if target_lane == "HARD_STOP_LANE" else ["README.md", "docs/"]

def executor_output_paths(bridge: Dict[str, Any]) -> List[str]:
    values = bridge.get("executor_writable_outputs", [])
    if not isinstance(values, list): return []
    return sorted({normalize_path(value) for value in values if isinstance(value, str) and value.strip()})

def operational_output_paths(bridge: Dict[str, Any]) -> List[str]:
    return executor_output_paths(bridge)
