#!/usr/bin/env python3
"""Shared helpers for Joyflow Phase 1 operational scripts."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]

TASK_STATE_KEYS = [
    "task_id",
    "task_status",
    "target_lane",
    "graph_sync_required",
    "formal_pending",
]

HARD_STOP_KEYWORDS = [
    "auth",
    "authentication",
    "authorize",
    "authorization",
    "permission",
    "permissions",
    "login",
    "password",
    "token",
    "secret",
    "secrets",
    "payment",
    "billing",
    "stripe",
    "database schema",
    "schema migration",
    "migration",
    "drop table",
    "delete data",
    "destructive",
    "production",
    "prod",
    "state machine",
    "routing governance",
    "subject schema",
    "bridge contract",
    "safety boundary",
    "boundary freeze",
]

REVIEW_KEYWORDS = [
    "unclear",
    "unknown",
    "tbd",
    "todo",
    "maybe",
    "not sure",
    "open question",
    "uncertain",
    "ambiguous",
    "risk",
    "refactor",
    "scripts/",
    "runtime/",
    "spec/",
    "subject/",
    "observer/",
    "shadow/",
]

LOW_RISK_HINTS = [
    "readme",
    "docs/",
    "documentation",
    "usage note",
    "typo",
    "copy",
    "text",
]


def read_text(rel: str, default: str = "") -> str:
    path = ROOT / rel
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def write_text(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_json(rel: str, default: Any = None) -> Any:
    path = ROOT / rel
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(rel)
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        if default is not None:
            return default
        raise ValueError(f"empty JSON file: {rel}")
    return json.loads(text)


def write_json(rel: str, data: Any) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def stable_task_id(seed: str) -> str:
    normalized = " ".join(seed.split()) or "joyflow-task"
    return "JF-" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


def canonical_json_hash(data: Any) -> str:
    blob = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def file_hash(rel: str) -> str:
    data = (ROOT / rel).read_bytes()
    return hashlib.sha256(data).hexdigest()


def lower_join(value: Any) -> str:
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, dict):
        return " ".join(f"{k} {lower_join(v)}" for k, v in value.items()).lower()
    if isinstance(value, list):
        return " ".join(lower_join(v) for v in value).lower()
    return str(value).lower()


def keyword_hits(text: str, keywords: Iterable[str]) -> List[str]:
    low = text.lower()
    return sorted({kw for kw in keywords if kw in low})


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").lstrip("./")


def is_within_allowed(path: str, allowed_roots: Iterable[str]) -> bool:
    p = normalize_path(path)
    for root in allowed_roots:
        root = normalize_path(root)
        if not root:
            continue
        if root.endswith("/"):
            if p.startswith(root):
                return True
        elif p == root or p.startswith(root.rstrip("/") + "/"):
            return True
    return False


def git(args: List[str]) -> Tuple[int, str, str]:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def current_branch() -> Tuple[bool, str]:
    code, out, err = git(["branch", "--show-current"])
    if code != 0 or not out:
        return False, err or out or "cannot determine branch"
    return True, out


def changed_files() -> Tuple[bool, List[str], str]:
    code, _, err = git(["rev-parse", "--is-inside-work-tree"])
    if code != 0:
        return False, [], err or "not a git repository"

    files: List[str] = []
    for args in (["diff", "--name-only", "HEAD"], ["diff", "--name-only", "--cached"]):
        code, out, err = git(list(args))
        if code != 0:
            return False, [], err
        if out:
            files.extend(out.splitlines())

    code, out, err = git(["ls-files", "--others", "--exclude-standard"])
    if code != 0:
        return False, [], err
    if out:
        files.extend(out.splitlines())

    return True, sorted({normalize_path(f) for f in files if f.strip()}), ""


def task_state_shape_ok(data: Dict[str, Any]) -> bool:
    return list(data.keys()) == TASK_STATE_KEYS


def ensure_task_state_update(task_id: str, target_lane: str, graph_sync_required: bool = False) -> None:
    state = read_json("subject/task_state.json", default={})
    existing_pending = state.get("formal_pending", []) if isinstance(state, dict) else []
    new_state = {
        "task_id": task_id,
        "task_status": "ROUTED" if target_lane else "IDLE",
        "target_lane": target_lane,
        "graph_sync_required": bool(graph_sync_required),
        "formal_pending": existing_pending if isinstance(existing_pending, list) else [],
    }
    write_json("subject/task_state.json", new_state)


def infer_allowed_paths(contract: Dict[str, Any], target_lane: str) -> List[str]:
    explicit = contract.get("allowed_paths")
    if isinstance(explicit, list) and all(isinstance(x, str) for x in explicit):
        return sorted({normalize_path(x) for x in explicit if x.strip()})

    text = lower_join(contract)
    allowed: List[str] = []

    # Phase 1 preferred first self-task.
    if any(hint in text for hint in ["readme", "usage note", "phase1_usage", "documentation", "docs/"]):
        allowed.extend(["README.md", "docs/phase1_usage.md"])

    # Explicit path hints in natural-language scope.
    for path in [
        "AGENTS.md",
        ".codex/rules.md",
        "docs/",
        "scripts/",
        "tests/",
        "runtime/",
        "observer/",
        "spec/",
        "shadow/",
        "subject/",
    ]:
        if path.lower() in text:
            allowed.append(path)

    if target_lane == "HARD_STOP_LANE":
        return []

    if not allowed:
        allowed = ["README.md", "docs/"]

    return sorted({normalize_path(p) for p in allowed})


def operational_output_paths(bridge: Dict[str, Any]) -> List[str]:
    required = bridge.get("required_output_files", [])
    if not isinstance(required, list):
        required = []
    return sorted({
        "runtime/translation_contract.json",
        "runtime/routing_result.json",
        "runtime/execution_bridge_package.json",
        "runtime/context_palace.md",
        "runtime/codex_task_packet.md",
        "runtime/codex_launch_manifest.json",
        "runtime/contract_red_team_review.md",
        "observer/contract_red_team_receipt.json",
        "observer/raw_check_results.json",
        "observer/acceptance_receipt.json",
        "observer/pr_receipt.json",
        "observer/human_review_packet.md",
        "observer/reconcile_result.json",
        "subject/task_state.json",
        *[normalize_path(p) for p in required if isinstance(p, str)],
    })
