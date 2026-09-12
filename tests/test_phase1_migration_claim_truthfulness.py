import copy,importlib.util,json,pathlib,unittest,hashlib,jsonschema
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("g",ROOT/"tools/generate_old_rule_migration.py"); g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
class MigrationClaimTruthfulness(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.rows=json.loads((ROOT/"OLD_RULE_MIGRATION.json").read_text(encoding="utf-8")); c.reg=json.loads((ROOT/"machine/verification_registry.json").read_text(encoding="utf-8")); c.cap=json.loads((ROOT/"CAPABILITY_STATUS.json").read_text(encoding="utf-8")); c.bound=g.load_bound_inputs(); c.current=g.current_rule_ids()
  c.fixture_root=ROOT/"tests/fixtures/phase1f_transition"
  load=lambda name: json.loads((c.fixture_root/name).read_text(encoding="utf-8"))
  c.fixture_raw_bound=(load("inventory.json"),load("source_set.json"),load("mapping.json"),load("mapping_seal.json"),load("decisions.json"),load("decision_seal.json"),copy.deepcopy(c.bound[6]))
  c.fixture_bound=g.validate_confirmed_transition_inputs(c.fixture_raw_bound,expected_count=1,expected_sources=1)
 def val(s,rows=None): return g.validate_migration_rows(rows or copy.deepcopy(s.rows),copy.deepcopy(s.reg),s.current,s.bound)
 def resign_fixture(s,bound):
  b=list(copy.deepcopy(bound)); source,mapping,decisions,claims=b[1],b[2],b[4],b[6]
  source.pop("source_set_digest",None); source["source_set_digest"]=g._digest(source)
  mapping["source_set_id"]=source["source_set_id"]; mapping["source_set_digest"]=source["source_set_digest"]; mapping["mapping_status"]=g._derived_mapping_status(mapping["mappings"]); mapping.pop("mapping_set_digest",None); mapping["mapping_set_digest"]=g._digest(mapping)
  decisions["source_mapping_set_id"]=mapping["mapping_set_id"]; decisions["source_mapping_set_digest"]=mapping["mapping_set_digest"]; decisions.pop("decision_set_digest",None); decisions["decision_set_digest"]=g._digest(decisions)
  b[3]={"artifact_type":"BRAIN_LEGACY_SEMANTIC_MAPPING_SEAL","seal_version":2,"owner":"WEB_BRAIN","repair_source_package":g.REPAIR_SOURCE,"mapping_set_id":mapping["mapping_set_id"],"mapping_set_digest":mapping["mapping_set_digest"],"legacy_source_set_id":source["source_set_id"],"legacy_source_set_digest":source["source_set_digest"],"capability_claim_registry_id":claims["registry_id"],"capability_claim_registry_digest":claims["registry_digest"]}; b[3]["seal_digest"]=g._digest(b[3])
  b[5]={"artifact_type":"LEGACY_DISPOSITION_DECISION_SEAL","seal_version":1,"owner":"WEB_BRAIN","repair_source_package":g.REPAIR_SOURCE,"decision_set_id":decisions["decision_set_id"],"decision_set_digest":decisions["decision_set_digest"],"mapping_set_id":mapping["mapping_set_id"],"mapping_set_digest":mapping["mapping_set_digest"]}; b[5]["seal_digest"]=g._digest(b[5])
  return tuple(b)
 def test_active_candidate_model_and_artifact_identity_is_current(s):
  expected="JOYFLOW_PHASE1_COMBINED_CAPABILITY_COVERAGE_REPAIR_CANDIDATE"; stale="JOYFLOW_PHASE1F_CONFIRMED_TRANSITION_BOUNDARY_REPAIR_CANDIDATE"
  model=(ROOT/"machine/joyflow_dual_layer_model.yaml").read_text(encoding="utf-8"); s.assertTrue(model.startswith("model_id: "+expected+"_MODEL\n"))
  schema=json.loads((ROOT/"schemas/fibered_task_capsule.schema.json").read_text(encoding="utf-8")); s.assertEqual(schema["properties"]["model_id"]["const"],expected+"_MODEL")
  for p in (ROOT/"examples").glob("*.json"):
   text=p.read_text(encoding="utf-8"); s.assertNotIn(stale+"_MODEL",text,p.name); s.assertNotIn(stale+".zip",text,p.name)
 def test_every_target_rule_exists(s): s.assertTrue(all(set(r["target_rule_ids"])<=s.current for r in s.rows))
 def test_all_concrete_verification_refs_resolve(s): s.assertTrue(g.validate_verification_registry(copy.deepcopy(s.reg)))
 def test_former_conflated_capability_input_removed(s): s.assertFalse((ROOT/"machine/legacy_rule_capabilities_v1_7_6.json").exists())
 def test_current_candidate_has_no_legacy_equivalence_claim(s): s.assertEqual(sum(r["migration_status"]=="SEMANTICALLY_PRESERVED_AND_BEHAVIORALLY_VERIFIED" for r in s.rows),0); s.assertTrue(all(not r["behavioral_equivalence_claimed"] for r in s.rows))
 def test_all_dispositions_are_not_evaluated(s): s.assertTrue(all(r["disposition_decision"]["decision"]=="NOT_EVALUATED" for r in s.rows))
 def test_all_current_product_direction_effects_are_unresolved(s): s.assertTrue(all(r["disposition_decision"]["product_direction_effect"]=="UNRESOLVED_MATERIAL_EFFECT" for r in s.rows))
 def test_behavior_status_requires_exact_text_and_confirmed_brain_mapping(s):
  rows=copy.deepcopy(s.rows); r=rows[0]; r["migration_status"]="SEMANTICALLY_PRESERVED_AND_BEHAVIORALLY_VERIFIED"; r["behavioral_equivalence_claimed"]=True; s.assertRaises(ValueError,s.val,rows)
 def test_brain_interpretation_mutation_without_digest_blocks(s):
  b=list(copy.deepcopy(s.bound)); b[2]["mappings"][0]["brain_capability_interpretation"]="opposite"; s.assertRaises(ValueError,g.validate_brain_mapping,b[0],b[1],b[2])
 def test_wrong_inventory_section_blocks(s):
  b=list(copy.deepcopy(s.bound)); b[2]["mappings"][0]["old_section"]="WRONG"; s.assertRaises(ValueError,g.validate_brain_mapping,b[0],b[1],b[2])
 def test_wrong_legacy_source_hash_blocks(s):
  b=list(copy.deepcopy(s.bound)); b[2]["mappings"][0]["legacy_source_sha256"]="0"*64; s.assertRaises(ValueError,g.validate_brain_mapping,b[0],b[1],b[2])
 def test_semantic_mapping_cannot_contain_disposition(s):
  b=list(copy.deepcopy(s.bound)); b[2]["mappings"][0]["legacy_migration_status"]="EXPLICITLY_DEFERRED"; s.assertRaises(ValueError,g.validate_brain_mapping,b[0],b[1],b[2])
 def test_unsealed_disposition_mutation_blocks(s):
  b=list(copy.deepcopy(s.bound)); b[4]["decisions"][0]["decision"]="DEFER"; s.assertRaises(ValueError,g._verify_embedded_digest,b[4],"decision_set_digest")
 def test_defer_requires_exact_current_basis(s):
  d=copy.deepcopy(s.bound[4]); row=d["decisions"][0]; row.update(decision="DEFER",basis="EXACT_LEGACY_SEMANTICS_UNAVAILABLE"); s.assertRaises(ValueError,g.validate_disposition_decisions,s.bound[2],d)
 def test_retire_by_product_requires_user_owner_and_ref(s):
  d=copy.deepcopy(s.bound[4]); row=d["decisions"][0]; row.update(decision="RETIRE",basis="CURRENT_PRODUCT_DECISION",owner="WEB_BRAIN",user_decision_ref=None,product_direction_effect="CHANGES_CONFIRMED_DIRECTION",affects_product_requirement="YES",affects_important_tradeoff="NO"); s.assertRaises(ValueError,g.validate_disposition_decisions,s.bound[2],d)
 def test_brain_technical_defer_does_not_require_user_row_approval(s):
  d=copy.deepcopy(s.bound[4]); row=d["decisions"][0]; row.update(decision="DEFER",basis="CURRENT_PHASE_SCOPE",owner="WEB_BRAIN",decision_ref="PHASE1F_CURRENT_SCOPE",user_decision_ref=None,product_direction_effect="PRESERVES_CONFIRMED_DIRECTION",affects_product_requirement="NO",affects_important_tradeoff="NO"); s.assertTrue(g.validate_disposition_decisions(s.bound[2],d))
 def test_brain_cannot_close_unknown_material_effect(s):
  d=copy.deepcopy(s.bound[4]); row=d["decisions"][0]; row.update(decision="DEFER",basis="CURRENT_PHASE_SCOPE",owner="WEB_BRAIN",decision_ref="PHASE1F_CURRENT_SCOPE",user_decision_ref=None,product_direction_effect="UNRESOLVED_MATERIAL_EFFECT",affects_product_requirement="UNKNOWN",affects_important_tradeoff="UNKNOWN"); s.assertRaises(ValueError,g.validate_disposition_decisions,s.bound[2],d)
 def test_brain_cannot_change_confirmed_product_direction(s):
  d=copy.deepcopy(s.bound[4]); row=d["decisions"][0]; row.update(decision="RETIRE",basis="TECHNICAL_DUPLICATION_ANALYSIS",owner="WEB_BRAIN",decision_ref="BRAIN_TECHNICAL_ANALYSIS",user_decision_ref=None,product_direction_effect="CHANGES_CONFIRMED_DIRECTION",affects_product_requirement="YES",affects_important_tradeoff="NO"); s.assertRaises(ValueError,g.validate_disposition_decisions,s.bound[2],d)
 def test_current_product_decision_requires_exact_user_ref(s):
  d=copy.deepcopy(s.bound[4]); row=d["decisions"][0]; row.update(decision="CARRY_FORWARD",basis="CURRENT_PRODUCT_DECISION",owner="USER",decision_ref="CURRENT_USER_DIRECTION",user_decision_ref="",product_direction_effect="PRESERVES_CONFIRMED_DIRECTION",affects_product_requirement="YES",affects_important_tradeoff="NO"); s.assertRaises(ValueError,g.validate_disposition_decisions,s.bound[2],d)
 def test_technical_duplication_retirement_requires_confirmed_semantic_gate(s):
  d=copy.deepcopy(s.bound[4]); row=d["decisions"][0]; row.update(decision="RETIRE",basis="TECHNICAL_DUPLICATION_ANALYSIS",owner="WEB_BRAIN",decision_ref="BRAIN_CONFIRMED_DUPLICATION",user_decision_ref=None,product_direction_effect="PRESERVES_CONFIRMED_DIRECTION",affects_product_requirement="NO",affects_important_tradeoff="NO"); s.assertRaisesRegex(ValueError,"technical duplication retirement requires",g.validate_disposition_decisions,s.bound[2],d)
 def test_legacy_semantic_retirement_requires_confirmed_semantic_gate(s):
  d=copy.deepcopy(s.bound[4]); row=d["decisions"][0]; row.update(decision="RETIRE",basis="LEGACY_SEMANTIC_ANALYSIS",owner="WEB_BRAIN",decision_ref="BRAIN_CONFIRMED_SUPERSESSION",user_decision_ref=None,product_direction_effect="PRESERVES_CONFIRMED_DIRECTION",affects_product_requirement="NO",affects_important_tradeoff="NO"); s.assertRaisesRegex(ValueError,"semantic supersession retirement requires",g.validate_disposition_decisions,s.bound[2],d)
 def test_current_instance_and_transition_fixture_lifecycles_are_separate(s):
  s.assertTrue(all(not r["exact_source_text_in_package"] and r["exact_source_section_sha256"] is None and r["semantic_evidence_ref"] is None for r in s.bound[2]["mappings"]))
  s.assertTrue(s.fixture_bound[1]["source_bytes_bundled"]); s.assertEqual(len(s.fixture_bound[2]["mappings"]),1)
 def test_exact_transition_fixture_uses_public_generation_path(s):
  rows=g.render_confirmed_transition_rows(copy.deepcopy(s.fixture_raw_bound),expected_count=1,expected_sources=1)
  s.assertEqual(rows[0]["migration_status"],"RETIRED_BY_CONFIRMED_SEMANTIC_SUPERSESSION")
  s.assertTrue(rows[0]["verification_state"]["legacy_source_replayed"]); s.assertTrue(rows[0]["verification_state"]["legacy_semantic_mapping_confirmed"])
 def test_exact_transition_fixture_tampered_source_bytes_block(s):
  source=s.fixture_root/"legacy_source_fixture.md"; original=source.read_bytes()
  try:
   source.write_bytes(original+b"tamper")
   with s.assertRaisesRegex(ValueError,"bytes or SHA mismatch"): g.render_confirmed_transition_rows(copy.deepcopy(s.fixture_raw_bound),expected_count=1,expected_sources=1)
  finally: source.write_bytes(original)
 def test_exact_transition_fixture_wrong_section_digest_blocks(s):
  bound=copy.deepcopy(s.fixture_raw_bound); bound[2]["mappings"][0]["exact_source_section_sha256"]="0"*64; bound=s.resign_fixture(bound)
  with s.assertRaisesRegex(ValueError,"section digest mismatch"): g.render_confirmed_transition_rows(bound,expected_count=1,expected_sources=1)
 def test_confirmed_mapping_without_source_root_blocks(s):
  bound=copy.deepcopy(s.fixture_raw_bound); bound[1]["package_relative_source_root"]=None; bound=s.resign_fixture(bound)
  with s.assertRaisesRegex(ValueError,"requires package-relative source root"): g.render_confirmed_transition_rows(bound,expected_count=1,expected_sources=1)
 def test_mapping_rows_cannot_independently_own_source_set_identity(s):
  bound=list(copy.deepcopy(s.fixture_bound)); bound[2]["mappings"][0]["legacy_source_set_id"]="WRONG_SOURCE_SET"
  with s.assertRaisesRegex(ValueError,"cannot independently own source-set identity"): g.validate_brain_mapping(bound[0],bound[1],bound[2],expected_count=1)
 def test_migration_row_derives_source_set_identity_from_top_level(s):
  s.assertNotIn("legacy_source_set_id",s.fixture_bound[2]["mappings"][0])
  rows=g.render_confirmed_transition_rows(copy.deepcopy(s.fixture_raw_bound),expected_count=1,expected_sources=1)
  s.assertEqual(rows[0]["legacy_source_set_id"],s.fixture_bound[1]["source_set_id"])
 def test_semantic_evidence_wrong_section_id_blocks(s):
  bound=copy.deepcopy(s.fixture_raw_bound); bound[2]["mappings"][0]["semantic_evidence_ref"]["section_id"]="DOES_NOT_EXIST"; bound=s.resign_fixture(bound)
  with s.assertRaisesRegex(ValueError,"section markers missing or duplicated"): g.render_confirmed_transition_rows(bound,expected_count=1,expected_sources=1)
 def test_semantic_evidence_file_digest_mismatch_blocks(s):
  bound=copy.deepcopy(s.fixture_raw_bound); bound[2]["mappings"][0]["semantic_evidence_ref"]["file_sha256"]="0"*64; bound=s.resign_fixture(bound)
  with s.assertRaisesRegex(ValueError,"evidence file digest mismatch"): g.render_confirmed_transition_rows(bound,expected_count=1,expected_sources=1)
 def test_semantic_evidence_section_digest_mismatch_blocks(s):
  bound=copy.deepcopy(s.fixture_raw_bound); bound[2]["mappings"][0]["semantic_evidence_ref"]["section_sha256"]="0"*64; bound=s.resign_fixture(bound)
  with s.assertRaisesRegex(ValueError,"evidence section digest mismatch"): g.render_confirmed_transition_rows(bound,expected_count=1,expected_sources=1)
 def test_product_defer_uses_neutral_exact_decision_status(s):
  decision=copy.deepcopy(s.fixture_bound[4]["decisions"][0]); decision.update(decision="DEFER",basis="CURRENT_PRODUCT_DECISION",owner="USER",decision_ref="EXACT_PRODUCT_DEFER",user_decision_ref="USER_DECISION_GROUP",product_direction_effect="PRESERVES_CONFIRMED_DIRECTION",affects_product_requirement="NO",affects_important_tradeoff="NO")
  s.assertEqual(g._derive_disposition_status(decision,True,True),("DEFERRED_BY_EXACT_CURRENT_DECISION",False))
 def test_transition_contract_all_legal_combinations_align_schema_validator_and_deriver(s):
  current_mapping=copy.deepcopy(s.bound[2]); current_mapping["mappings"]=current_mapping["mappings"][:1]
  fixture_mapping=copy.deepcopy(s.fixture_bound[2])
  for (decision,basis),contract in g.DISPOSITION_TRANSITION_CONTRACT.items():
   for (semantic_state,behavior_state),expected in contract["outcomes"].items():
    mapping=copy.deepcopy(fixture_mapping if semantic_state=="CONFIRMED" else current_mapping)
    old_rule_id=mapping["mappings"][0]["old_rule_id"]
    decisions={"artifact_type":"LEGACY_DISPOSITION_DECISION_SET","decision_set_version":2,"decision_set_id":"TEST_TRANSITION_DECISIONS","owner":"WEB_BRAIN","source_mapping_set_id":mapping["mapping_set_id"],"source_mapping_set_digest":mapping["mapping_set_digest"],"generator_may_modify":False,"decision_scope":"TEST_ONLY","decisions":[]}
    effect="PRESERVES_CONFIRMED_DIRECTION" if "PRESERVES_CONFIRMED_DIRECTION" in contract["effects"] else sorted(contract["effects"])[0]
    product=sorted(contract["product_values"])[0] if contract["product_values"] is not None else "NO"; tradeoff=sorted(contract["tradeoff_values"])[0] if contract["tradeoff_values"] is not None else "NO"
    row={"decision_id":"LDD::"+old_rule_id,"old_rule_id":old_rule_id,"owner":contract["owner"],"decision":decision,"basis":basis,"decision_ref":"EXACT_TRANSITION_DECISION_REF","user_decision_ref":"USER_GROUP_DECISION_REF" if contract["user_ref"]=="REQUIRED" else None,"affects_product_requirement":product,"affects_important_tradeoff":tradeoff,"product_direction_effect":effect,"rationale":"Test exact transition contract outcome."}
    decisions["decisions"]=[row]; decisions["decision_set_digest"]=g._digest(decisions)
    jsonschema.validate(row,g.disposition_item_schema()); s.assertTrue(g.validate_disposition_decisions(mapping,decisions,expected_count=1))
    result=g._derive_disposition_status(row,semantic_state=="CONFIRMED",behavior_state=="COMPLETE")
    s.assertEqual(result,(expected["migration_status"],expected["behavioral_equivalence_claimed"]),(decision,basis,semantic_state,behavior_state))
 def test_carry_forward_public_path_uses_contract_for_complete_and_incomplete_behavior(s):
  for complete,expected in [(False,"MAPPED_ONLY"),(True,"SEMANTICALLY_PRESERVED_AND_BEHAVIORALLY_VERIFIED")]:
   bound=copy.deepcopy(s.fixture_raw_bound); row=bound[4]["decisions"][0]; row.update(decision="CARRY_FORWARD",basis="LEGACY_SEMANTIC_ANALYSIS",decision_ref="FIXTURE_CARRY_FORWARD")
   bound=s.resign_fixture(bound); behavior_map=g.TARGET_TO_BEHAVIOR if complete else {}
   rows=g.render_confirmed_transition_rows(bound,target_to_behavior=behavior_map,expected_count=1,expected_sources=1)
   s.assertEqual(rows[0]["migration_status"],expected)
 def test_transition_contract_schema_rejects_unsupported_combination(s):
  row=copy.deepcopy(s.bound[4]["decisions"][0]); row.update(decision="RETIRE",basis="CURRENT_PHASE_SCOPE",owner="WEB_BRAIN",user_decision_ref=None,product_direction_effect="PRESERVES_CONFIRMED_DIRECTION",affects_product_requirement="NO",affects_important_tradeoff="NO"); s.assertRaises(jsonschema.ValidationError,jsonschema.validate,row,g.disposition_item_schema())
 def test_technical_duplication_retirement_derives_confirmed_semantic_supersession(s):
  d=copy.deepcopy(s.bound[4]["decisions"][0]); d.update(decision="RETIRE",basis="TECHNICAL_DUPLICATION_ANALYSIS",owner="WEB_BRAIN",decision_ref="BRAIN_CONFIRMED_DUPLICATION",user_decision_ref=None,product_direction_effect="PRESERVES_CONFIRMED_DIRECTION",affects_product_requirement="NO",affects_important_tradeoff="NO"); s.assertEqual(g._derive_disposition_status(d,True,False),("RETIRED_BY_CONFIRMED_SEMANTIC_SUPERSESSION",False))
 def test_confirmed_transition_public_path_consumes_both_seals(s):
  validated=g.validate_confirmed_transition_inputs(copy.deepcopy(s.fixture_raw_bound),expected_count=1,expected_sources=1)
  s.assertIsInstance(validated,g.ValidatedTransitionInputs); s.assertEqual(g.render_migration_rows(validated,expected_count=1,expected_sources=1)[0]["migration_status"],"RETIRED_BY_CONFIRMED_SEMANTIC_SUPERSESSION")
 def test_unsealed_mapping_mutation_blocks_formal_boundary(s):
  bound=list(copy.deepcopy(s.fixture_raw_bound)); row=bound[2]["mappings"][0]; row["brain_capability_interpretation"]+=" changed"; row["brain_capability_interpretation_digest"]=hashlib.sha256(row["brain_capability_interpretation"].encode()).hexdigest(); bound[2].pop("mapping_set_digest"); bound[2]["mapping_set_digest"]=g._digest(bound[2]); bound[4]["source_mapping_set_digest"]=bound[2]["mapping_set_digest"]; bound[4].pop("decision_set_digest"); bound[4]["decision_set_digest"]=g._digest(bound[4])
  with s.assertRaisesRegex(ValueError,"Brain input seal mismatch"): g.validate_confirmed_transition_inputs(tuple(bound),expected_count=1,expected_sources=1)
 def test_unsealed_disposition_mutation_blocks_formal_boundary(s):
  bound=list(copy.deepcopy(s.fixture_raw_bound)); bound[4]["decisions"][0]["rationale"]+=" changed"; bound[4].pop("decision_set_digest"); bound[4]["decision_set_digest"]=g._digest(bound[4])
  with s.assertRaisesRegex(ValueError,"disposition decision seal mismatch"): g.validate_confirmed_transition_inputs(tuple(bound),expected_count=1,expected_sources=1)
 def test_package_relative_source_root_escape_blocks(s):
  bound=copy.deepcopy(s.fixture_raw_bound); bound[1]["package_relative_source_root"]="../../outside"; bound=s.resign_fixture(bound)
  with s.assertRaisesRegex(ValueError,"escapes package"): g.validate_confirmed_transition_inputs(bound,expected_count=1,expected_sources=1)
 def test_reversed_exact_section_markers_block(s):
  text="<!-- /JOYFLOW_SECTION:X -->\n<!-- JOYFLOW_SECTION:X -->\nvalue\n"
  with s.assertRaisesRegex(ValueError,"reversed or section empty"): g._extract_exact_section(text,"X")
 def test_reversed_evidence_section_markers_block(s):
  text="<!-- /JOYFLOW_EVIDENCE_SECTION:X -->\n<!-- JOYFLOW_EVIDENCE_SECTION:X -->\nvalue\n"
  with s.assertRaisesRegex(ValueError,"reversed or section empty"): g._extract_evidence_section(text,"X")
 def test_mapping_status_must_be_derived_from_rows(s):
  bound=list(copy.deepcopy(s.fixture_raw_bound)); bound[2]["mapping_status"]="BLOCKED"; bound[2].pop("mapping_set_digest"); bound[2]["mapping_set_digest"]=g._digest(bound[2]); bound[4]["source_mapping_set_digest"]=bound[2]["mapping_set_digest"]; bound[4].pop("decision_set_digest"); bound[4]["decision_set_digest"]=g._digest(bound[4]); claims=bound[6]
  bound[3]={"artifact_type":"BRAIN_LEGACY_SEMANTIC_MAPPING_SEAL","seal_version":2,"owner":"WEB_BRAIN","repair_source_package":g.REPAIR_SOURCE,"mapping_set_id":bound[2]["mapping_set_id"],"mapping_set_digest":bound[2]["mapping_set_digest"],"legacy_source_set_id":bound[1]["source_set_id"],"legacy_source_set_digest":bound[1]["source_set_digest"],"capability_claim_registry_id":claims["registry_id"],"capability_claim_registry_digest":claims["registry_digest"]}; bound[3]["seal_digest"]=g._digest(bound[3])
  bound[5]={"artifact_type":"LEGACY_DISPOSITION_DECISION_SEAL","seal_version":1,"owner":"WEB_BRAIN","repair_source_package":g.REPAIR_SOURCE,"decision_set_id":bound[4]["decision_set_id"],"decision_set_digest":bound[4]["decision_set_digest"],"mapping_set_id":bound[2]["mapping_set_id"],"mapping_set_digest":bound[2]["mapping_set_digest"]}; bound[5]["seal_digest"]=g._digest(bound[5])
  with s.assertRaisesRegex(ValueError,"status is not derived"): g.validate_confirmed_transition_inputs(tuple(bound),expected_count=1,expected_sources=1)
 def test_structural_or_source_evidence_cannot_support_behavior_status(s):
  rows=copy.deepcopy(s.rows); r=rows[0]; r["target_verification"]={t:[] for t in r["target_rule_ids"]}; s.assertRaises(ValueError,s.val,rows)
 def test_multi_target_missing_one_behavior_ref_is_derived_partial(s):
  rows=copy.deepcopy(s.rows); r=next(x for x in rows if len(x["target_rule_ids"])>1 and x["verification_state"]["current_target_behavior_status"]=="VERIFIED_FOR_ALL_TARGETS"); t=r["target_rule_ids"][-1]; r["target_verification"][t]=[]; s.assertRaises(ValueError,s.val,rows)
 def test_behavior_verified_targets_and_unverified_targets_are_disjoint(s):
  for r in s.rows: s.assertFalse(set(r["verification_state"]["behavior_verified_target_rule_ids"]) & set(r["verification_state"]["behavior_unverified_target_rule_ids"]))
 def test_verified_behavior_does_not_close_legacy_equivalence(s):
  r=next(x for x in s.rows if x["verification_state"]["current_target_behavior_status"]=="VERIFIED_FOR_ALL_TARGETS"); s.assertEqual(r["verification_state"]["behavior_unverified_target_rule_ids"],[]); s.assertEqual(r["verification_state"]["legacy_equivalence_unresolved_target_rule_ids"],r["target_rule_ids"])
 def test_phase_effect_keeps_disposition_open(s):
  s.assertTrue(all(not r["phase_effect"]["disposition_closed"] and not r["phase_effect"]["legacy_semantics_closed"] for r in s.rows))
 def test_phase_effect_does_not_block_truthful_mechanism(s): s.assertTrue(all(not r["phase_effect"]["blocks_pr1f_truthful_classification"] for r in s.rows))
 def test_phase_effect_does_not_decide_phase1_completion(s): s.assertTrue(all(r["phase_effect"]["phase1_completion_effect"]=="NOT_DETERMINED_BY_THIS_ARTIFACT" for r in s.rows))
 def test_retirement_policy_cannot_be_target_behavior_evidence(s):
  rows=copy.deepcopy(s.rows); r=rows[0]; r["target_verification"]={t:["E_RETIREMENT_RATIONALE"] for t in r["target_rule_ids"]}; r["verification_refs"]=sorted(set(r["verification_refs"]+["E_RETIREMENT_RATIONALE"])); s.assertRaises(ValueError,s.val,rows)
 def test_legacy_source_schema_rejects_unknown_field(s):
  doc=copy.deepcopy(s.bound[1]); doc["unexpected_semantic_authority"]=True; schema=json.loads((ROOT/"schemas/legacy_source_set.schema.json").read_text(encoding="utf-8")); s.assertRaises(jsonschema.ValidationError,jsonschema.validate,doc,schema)
 def test_brain_mapping_schema_rejects_wrong_owner_type(s):
  doc=copy.deepcopy(s.bound[2]); doc["mappings"][0]["owner"]="CODEX"; schema=json.loads((ROOT/"schemas/brain_legacy_semantic_mapping.schema.json").read_text(encoding="utf-8")); s.assertRaises(jsonschema.ValidationError,jsonschema.validate,doc,schema)
 def test_disposition_schema_rejects_unknown_field(s):
  doc=copy.deepcopy(s.bound[4]); doc["decisions"][0]["automatic_retirement"]=True; schema=json.loads((ROOT/"schemas/legacy_disposition_decisions.schema.json").read_text(encoding="utf-8")); s.assertRaises(jsonschema.ValidationError,jsonschema.validate,doc,schema)
 def test_migration_schema_rejects_old_ambiguous_field(s):
  rows=copy.deepcopy(s.rows); rows[0]["unverified_target_rule_ids"]=[]; schema=json.loads((ROOT/"schemas/legacy_rule_migration.schema.json").read_text(encoding="utf-8")); s.assertRaises(jsonschema.ValidationError,jsonschema.validate,rows,schema)
 def test_nonexistent_test_symbol_blocks(s):
  reg=copy.deepcopy(s.reg); next(x for x in reg if x["kind"]=="UNIT_TEST")["concrete_refs"]=["tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::nope"]; s.assertRaises(ValueError,g.validate_verification_registry,reg)
 def test_inherited_stage_presence_is_not_behavioral_verification(s):
  claims=copy.deepcopy(s.bound[6]); row=next(x for x in claims["claims"] if x["claim_type"]=="INHERITED_STAGE_PRESENCE"); s.assertEqual(row["exact_status"],"PRESENT_AND_IDENTITY_BOUND"); s.assertNotIn("covered_rule_ids",row); s.assertTrue(g.validate_capability_claim_registry(claims,s.reg)); row["exact_status"]="ADVERSARIAL_CASE_VERIFIED"; s.assertRaises(ValueError,g.validate_capability_claim_registry,claims,s.reg)
 def test_verified_rule_coverage_matches_exact_evidence_union(s):
  claims=copy.deepcopy(s.bound[6]); row=next(x for x in claims["claims"] if x["capability_id"]=="PR1A_TO_PR1E_SELECTED_RULE_COVERAGE"); by={x["verification_id"]:x for x in s.reg}; expected=sorted({r for ref in row["exact_verification_refs"] for r in by[ref]["covered_target_rule_ids"]}); s.assertEqual(row["covered_rule_ids"],expected); row["covered_rule_ids"]=sorted(expected+["JF_PHASE1E_COMPLETION_EXACT_CHAIN"]); s.assertRaises(ValueError,g.validate_capability_claim_registry,claims,s.reg)
 def test_cross_stage_chain_matches_exact_stage_and_rule_scope(s):
  claims=copy.deepcopy(s.bound[6]); row=next(x for x in claims["claims"] if x["claim_type"]=="VERIFIED_CROSS_STAGE_CHAIN"); by={x["verification_id"]:x for x in s.reg}; expected_stages=sorted({st for ref in row["exact_verification_refs"] for st in by[ref].get("covered_stage_ids",[])}); expected_rules=sorted({r for ref in row["exact_verification_refs"] for r in by[ref]["covered_target_rule_ids"]}); s.assertEqual(sorted(row["participating_stage_ids"]),expected_stages); s.assertEqual(sorted(row["covered_rule_ids"]),expected_rules); row["participating_stage_ids"]=sorted(set(row["participating_stage_ids"]+["PR1A_PATH_DISCOVERY"])); s.assertRaises(ValueError,g.validate_capability_claim_registry,claims,s.reg)
 def test_five_stage_zero_rule_behavior_claim_blocks(s):
  claims=copy.deepcopy(s.bound[6]); row=next(x for x in claims["claims"] if x["capability_id"]=="PR1A_TO_PR1E_SELECTED_RULE_COVERAGE"); row["covered_rule_ids"]=[]; row["covered_stage_ids"]=["PR1A_PATH_DISCOVERY","PR1B_SEALED_OBJECT_EXECUTION_AND_REVIEW","PR1C_CURRENT_OBJECT_PR_BODY_CI","PR1D_REVIEW_ACCEPTANCE_FREEZE","PR1E_AI_NATIVE_CHANGE_PROJECTION"]; s.assertRaises(ValueError,g.validate_capability_claim_registry,claims,s.reg)
 def test_cross_stage_chain_does_not_imply_full_stage_coverage(s):
  row=next(x for x in s.bound[6]["claims"] if x["claim_type"]=="VERIFIED_CROSS_STAGE_CHAIN"); s.assertNotIn("covered_stage_ids",row); s.assertEqual(row["participating_stage_ids"],["PR1B_SEALED_OBJECT_EXECUTION_AND_REVIEW","PR1C_CURRENT_OBJECT_PR_BODY_CI","PR1D_REVIEW_ACCEPTANCE_FREEZE","PR1E_AI_NATIVE_CHANGE_PROJECTION"])
 def test_capability_status_is_navigation_only(s): s.assertEqual(s.cap["artifact_role"],"GENERATED_NON_AUTHORITATIVE_NAVIGATION_VIEW"); s.assertFalse(s.cap["may_satisfy_stage_gate"]); s.assertFalse(s.cap["may_satisfy_phase_gate"])
 def test_capability_status_exact_registry_subjects(s): s.assertTrue(g.validate_capability_status(copy.deepcopy(s.cap),s.reg,s.bound[6]))
 def test_arbitrary_capability_name_blocks_even_in_view(s):
  c=copy.deepcopy(s.cap); c["capabilities"][0]["capability_id"]="FULL_PHASE2_AUTOMATIC_MERGE_AND_RELEASE"; s.assertRaises(ValueError,g.validate_capability_status,c,s.reg,s.bound[6])
 def test_unrelated_concrete_ref_breaks_capability_contract(s):
  reg=copy.deepcopy(s.reg); r=next(x for x in reg if x["verification_id"]=="E_MERGE_AUTHORITY_BEHAVIOR"); r["concrete_refs"]=["tests/test_phase1_migration_claim_truthfulness.py::MigrationClaimTruthfulness::test_package_cannot_self_claim_independent_cold_review"]; s.assertRaises(ValueError,g.validate_capability_status,copy.deepcopy(s.cap),reg,s.bound[6])
 def test_package_cannot_self_claim_independent_cold_review(s):
  c=copy.deepcopy(s.cap); c["independent_stranger_cold_review_for_this_frozen_zip"]="PASS"; s.assertRaises(ValueError,g.validate_capability_status,c,s.reg,s.bound[6])
 def test_capability_view_cannot_be_promoted_to_gate(s):
  c=copy.deepcopy(s.cap); c["may_satisfy_phase_gate"]=True; s.assertRaises(ValueError,g.validate_capability_status,c,s.reg,s.bound[6])
 def test_generated_outputs_are_deterministic(s):
  for n,t in g.render_outputs().items(): s.assertEqual((ROOT/n).read_text(encoding="utf-8"),t)
 def test_all_176_rows_have_one_truthful_status(s):
  c={x:sum(r["migration_status"]==x for r in s.rows) for x in g.ALLOWED_STATUSES}; s.assertEqual(sum(c.values()),176); s.assertEqual(c["MAPPED_ONLY"],176)
  package_validator=(ROOT/"tools/validate_package.py").read_text(encoding="utf-8"); s.assertNotIn("counts.get(\"BEHAVIORALLY_VERIFIED\")",package_validator); s.assertIn("SEMANTICALLY_PRESERVED_AND_BEHAVIORALLY_VERIFIED",package_validator); s.assertIn("EXPECTED_MIGRATION_STATUSES",package_validator); s.assertIn("disposition_decision_set_required",package_validator); s.assertIn("GENERATED_NON_AUTHORITATIVE_NAVIGATION_VIEW",package_validator)
if __name__=="__main__": unittest.main()
