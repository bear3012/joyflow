#!/usr/bin/env python3
import argparse,importlib.util,json,pathlib,sys,jsonschema
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("g",ROOT/"tools/generate_old_rule_migration.py"); g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--root",default=str(ROOT)); a=ap.parse_args(); root=pathlib.Path(a.root).resolve()
 try:
  if root!=ROOT: raise ValueError("root must be exact package")
  rows=load(root/"OLD_RULE_MIGRATION.json"); reg=load(root/"machine/verification_registry.json"); cap=load(root/"CAPABILITY_STATUS.json")
  source_set=load(root/"machine/legacy_source_set_v1_7_6.json"); mapping=load(root/"machine/brain_legacy_semantic_mapping_v1_7_6.json"); decisions=load(root/"machine/legacy_disposition_decisions_v1_7_6.json"); claims=load(root/"machine/capability_claim_registry.json")
  jsonschema.validate(source_set,load(root/"schemas/legacy_source_set.schema.json")); jsonschema.validate(mapping,load(root/"schemas/brain_legacy_semantic_mapping.schema.json")); jsonschema.validate(decisions,load(root/"schemas/legacy_disposition_decisions.schema.json")); jsonschema.validate(claims,load(root/"schemas/capability_claim_registry.schema.json")); jsonschema.validate(rows,load(root/"schemas/legacy_rule_migration.schema.json")); jsonschema.validate(reg,load(root/"schemas/migration_verification_registry.schema.json")); jsonschema.validate(cap,load(root/"schemas/candidate_capability_status.schema.json"))
  bound=g.load_bound_inputs(); g.validate_migration_rows(rows,reg,g.current_rule_ids(),bound); g.validate_capability_status(cap,reg,bound[6])
 except Exception as e: print(f"MIGRATION_CLAIM_BLOCK: {e}",file=sys.stderr); return 2
 c={k:sum(r["migration_status"]==k for r in rows) for k in sorted(g.ALLOWED_STATUSES)}; print("PASS migration_claim_truthfulness rows=176 counts="+json.dumps(c,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
