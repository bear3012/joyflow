#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tests")); sys.path.insert(0,str(ROOT/"runtime")); sys.path.insert(0,str(ROOT/"tools"))
import phase1_review_fixture as fx  # noqa:E402
from canonical_text import canonical_text_matches, write_canonical_text  # noqa:E402

def dump(value): return json.dumps(value,ensure_ascii=False,indent=2,sort_keys=False)+"\n"

def outputs():
    td,repo,base,head=fx.create_repository()
    try:
        c=fx.full_merge_authorization_chain(repo,base,head)
        return {
            ROOT/"examples/REPOSITORY_CODEX_HANDOFF_PROJECTION.json":dump(c["projection"]),
            ROOT/"examples/REPOSITORY_CODEX_EXECUTION_RETURN.json":dump(c["codex_return"]),
            ROOT/"examples/REPOSITORY_CODEX_EXECUTION_EVIDENCE_BUNDLE.json":dump(c["evidence_bundle"]),
            ROOT/"examples/REPOSITORY_BRAIN_REVIEW_CAPSULE.json":dump(c["brain_review"]),
            ROOT/"examples/REPOSITORY_MERGE_DECISION_CAPSULE.json":dump(c["user_acceptance"]),
            ROOT/"examples/REPOSITORY_MERGE_GATE_RECORD_READY.json":dump(c["merge_ready"]),
            ROOT/"examples/MERGE_GATE_RECORD_READY.json":dump(c["merge_ready"]),
            ROOT/"examples/MERGED_CHANGE_PROJECTION.json":dump(c["merged_change_projection"]),
            ROOT/"examples/MERGE_CANDIDATE_FREEZE_READY.json":dump(c["merge_candidate_freeze"]),
            ROOT/"examples/USER_MERGE_AUTHORIZATION.json":dump(c["user_merge_authorization"]),
            ROOT/"examples/MERGE_GATE_RECORD_ALLOWED.json":dump(c["merge_allowed"]),
            ROOT/"examples/TASK_COMPLETION_POINTER.json":dump(c["completion_pointer"]),
            ROOT/"examples/RAW_REPOSITORY_MERGE_EVIDENCE.json":c["repository_merge_evidence"].decode("utf-8"),
            ROOT/"examples/PR_RECORD_READY.json":dump(c["pr_record"]),
            ROOT/"examples/PR_BODY_READY.md":c["pr_body"],
            ROOT/"examples/PR_CI_RESULT.json":dump(c["pr_ci_result"]),
        }
    finally: td.cleanup()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--check",action="store_true"); args=ap.parse_args(); bad=[]
    for path,text in outputs().items():
        if args.check:
            if not canonical_text_matches(path,text): bad.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True,exist_ok=True); write_canonical_text(path,text)
    if bad:
        print("PHASE1_REVIEW_EXAMPLE_DRIFT: "+", ".join(bad),file=sys.stderr); return 2
    print("GENERATED phase1_review_examples=16"); return 0
if __name__=="__main__": raise SystemExit(main())
