#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
import joyflow_phase1_review  # noqa: E402

CURRENT_OBJECTS = {
    "--projection": ".joyflow/current/CODEX_HANDOFF_PROJECTION.json",
    "--codex-return": ".joyflow/current/CODEX_EXECUTION_RETURN.json",
    "--evidence-bundle": ".joyflow/current/CODEX_EXECUTION_EVIDENCE_BUNDLE.json",
    "--brain-review-capsule": ".joyflow/current/BRAIN_REVIEW_CAPSULE.json",
}


def _expand_current_pr(argv: list[str]) -> list[str]:
    if not argv or argv[0] != "verify-current-pr":
        return argv
    if "--repository" not in argv:
        return ["verify-pr", *argv[1:]]
    repo_index = argv.index("--repository") + 1
    if repo_index >= len(argv):
        return ["verify-pr", *argv[1:]]
    repo = pathlib.Path(argv[repo_index]).resolve()
    missing = [rel for rel in CURRENT_OBJECTS.values() if not (repo / rel).is_file()]
    if missing:
        print(json.dumps({"mechanical_gate": "FAIL", "error": "missing exact current Joyflow objects", "missing": missing}, sort_keys=True))
        raise SystemExit(2)
    expanded = ["verify-pr", *argv[1:]]
    for flag, rel in CURRENT_OBJECTS.items():
        expanded.extend([flag, str(repo / rel)])
    return expanded


def main() -> int:
    sys.argv = [sys.argv[0], *_expand_current_pr(sys.argv[1:])]
    return joyflow_phase1_review.main()


if __name__ == "__main__":
    raise SystemExit(main())
