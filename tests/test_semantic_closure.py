#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_semantic_closure as semantic  # noqa: E402


TASK_ID = "TEST_TASK"


def valid_meaning():
    return {
        "artifact_type": "PRODUCT_MEANING_CLOSURE",
        "artifact_version": "1",
        "task_id": TASK_ID,
        "original_user_problem": "Original problem",
        "problem": "Problem",
        "desired_result": "Desired result",
        "user_flow": ["step"],
        "business_rules": ["rule"],
        "must_have": ["must"],
        "must_not_have": ["must not"],
        "non_goals": ["non goal"],
        "important_tradeoffs": ["tradeoff"],
        "acceptance_examples": ["correct"],
        "failure_examples": ["incorrect"],
        "remaining_unknowns": [],
        "material_ambiguity_status": "NO_MATERIAL_AMBIGUITY",
        "product_walkthrough": {
            "entry": "entry",
            "user_action_sequence": ["action"],
            "system_response_sequence": ["response"],
            "success_result": "success",
            "failure_result": "failure",
            "preserved_behavior": ["preserve"],
            "explicitly_absent_behavior": ["absent"],
        },
        "user_confirmation": {"status": "CONFIRMED", "reference": "ref"},
    }


def valid_contract():
    return {
        "task_id": TASK_ID,
        "deterministic_intent": "intent",
        "product_meaning_ref": semantic.MEANING_PATH,
        "meaning_delta_ref": semantic.DELTA_PATH,
        "user_acceptance_plan_ref": semantic.ACCEPTANCE_PATH,
        "golden_case_refs": ["GC1"],
        "deviation_default": "BRAIN_REVIEW_REQUIRED",
        "lean_interpretation_embedded": False,
        "human_semantic_layer": {
            "objective": "objective",
            "expected_user_result": "result",
            "user_flow": ["flow"],
            "business_rules": ["rule"],
            "accepted_tradeoffs": ["tradeoff"],
            "non_goals": ["non goal"],
            "correct_examples": ["correct"],
            "incorrect_examples": ["incorrect"],
        },
        "mechanical_execution_layer": {
            "must_preserve": ["preserve"],
            "allowed_solution_surfaces": ["surface"],
            "forbidden_consequences": ["forbidden"],
            "required_outcomes": ["outcome"],
            "allowed_technical_freedom": ["freedom"],
            "stop_conditions": ["stop"],
            "evidence_requirements": ["evidence"],
        },
    }


def valid_delta():
    return {
        "artifact_type": "MEANING_DELTA",
        "parent_meaning_ref": "parent",
        "added": {},
        "removed": [],
        "changed": {},
        "unchanged": ["unchanged"],
        "unresolved": [],
        "user_confirmation_required": False,
    }


def valid_golden():
    return {
        "artifact_type": "GOLDEN_CASE_SET",
        "cases": [
            {
                "case_id": "GC1",
                "original_problem_ref": "problem-ref",
                "initial_state": {"state": "initial"},
                "action": "action",
                "expected_user_visible_result": "result",
                "expected_state_change": "change",
                "preserved_state": "preserve",
                "forbidden_result": "forbidden",
                "machine_check_mapping": "machine",
                "human_acceptance_mapping": "UA1",
            }
        ],
    }


def valid_acceptance():
    return {
        "artifact_type": "USER_ACCEPTANCE_PLAN",
        "steps": [
            {
                "acceptance_id": "UA1",
                "step": "step",
                "expected": "expected",
                "validates": "validates",
                "failure_meaning": "failure",
                "golden_case_refs": ["GC1"],
            }
        ],
    }


def valid_interpretation():
    return {
        "artifact_type": "CODEX_EXECUTION_INTERPRETATION",
        "task_id": TASK_ID,
        "objective_understood": "objective",
        "user_visible_result": "result",
        "user_flow_understood": ["flow"],
        "must_preserve": ["preserve"],
        "intended_solution_surface": ["surface"],
        "excluded_changes": ["excluded"],
        "golden_cases_understood": ["GC1"],
        "unresolved_items": [],
        "interpretation_status": "ALIGNED",
        "deviation_route": "BRAIN_REVIEW_REQUIRED",
    }


def valid_review():
    return {
        "artifact_type": "BRAIN_SEMANTIC_REVIEW",
        "original_user_problem_ref": "problem",
        "confirmed_product_meaning_ref": "meaning",
        "released_contract_ref": "contract",
        "codex_interpretation_ref": "interpretation",
        "actual_diff_and_evidence_ref": "diff",
        "test_results_ref": "tests",
        "golden_case_results_ref": "golden",
        "user_acceptance_plan_ref": "acceptance",
        "semantic_drift_status": "PASS",
        "scope_drift_status": "PASS",
        "overdesign_status": "PASS",
        "original_problem_actually_solved": True,
        "technically_correct_but_practically_wrong_risk": "NONE_FOUND",
        "review_verdict": "PASS",
    }


class SemanticClosureValidationTests(unittest.TestCase):
    def test_valid_artifacts_have_no_shape_findings(self):
        findings = []
        meaning = valid_meaning()
        contract = valid_contract()
        delta = valid_delta()
        golden = valid_golden()
        acceptance = valid_acceptance()
        interpretation = valid_interpretation()
        semantic.validate_product_meaning(meaning, findings)
        semantic.validate_contract(contract, findings)
        semantic.validate_delta(delta, findings)
        golden_ids = semantic.validate_golden(golden, findings)
        semantic.validate_acceptance(acceptance, findings, golden_ids)
        semantic.validate_interpretation(interpretation, findings, golden_ids)
        semantic.validate_cross_refs(meaning, contract, interpretation, findings, golden_ids)
        semantic.validate_execution_gate(meaning, contract, interpretation, findings)
        semantic.validate_brain_review(valid_review(), findings)
        self.assertEqual([], findings)

    def test_unconfirmed_meaning_blocks_execution_gate(self):
        meaning = valid_meaning()
        meaning["user_confirmation"]["status"] = "DRAFT"
        findings = []
        semantic.validate_execution_gate(meaning, valid_contract(), valid_interpretation(), findings)
        self.assertTrue(any("not user-confirmed" in item for item in findings))

    def test_material_ambiguity_blocks_execution_gate(self):
        meaning = valid_meaning()
        meaning["material_ambiguity_status"] = "MATERIAL_AMBIGUITY_REMAINS"
        meaning["remaining_unknowns"] = ["changes flow"]
        findings = []
        semantic.validate_execution_gate(meaning, valid_contract(), valid_interpretation(), findings)
        self.assertTrue(any("material ambiguity remains" in item for item in findings))

    def test_no_material_ambiguity_cannot_keep_unknowns(self):
        meaning = valid_meaning()
        meaning["remaining_unknowns"] = ["unknown"]
        findings = []
        semantic.validate_product_meaning(meaning, findings)
        self.assertTrue(any("cannot retain unknowns" in item for item in findings))

    def test_missing_contract_layer_is_rejected(self):
        contract = valid_contract()
        del contract["mechanical_execution_layer"]
        findings = []
        semantic.validate_contract(contract, findings)
        self.assertTrue(any("mechanical_execution_layer" in item for item in findings))

    def test_unknown_golden_case_reference_is_rejected(self):
        acceptance = valid_acceptance()
        acceptance["steps"][0]["golden_case_refs"] = ["UNKNOWN"]
        findings = []
        semantic.validate_acceptance(acceptance, findings, ["GC1"])
        self.assertTrue(any("unknown ids" in item for item in findings))

    def test_aligned_interpretation_cannot_keep_unresolved_items(self):
        interpretation = valid_interpretation()
        interpretation["unresolved_items"] = ["may change product flow"]
        findings = []
        semantic.validate_interpretation(interpretation, findings, ["GC1"])
        self.assertTrue(any("ALIGNED cannot retain unresolved" in item for item in findings))

    def test_non_aligned_non_lean_interpretation_blocks(self):
        interpretation = valid_interpretation()
        interpretation["interpretation_status"] = "TECHNICAL_DISCOVERY_REQUIRED"
        findings = []
        semantic.validate_execution_gate(valid_meaning(), valid_contract(), interpretation, findings)
        self.assertTrue(any("not aligned" in item for item in findings))

    def test_lean_embedding_can_avoid_separate_alignment_gate(self):
        contract = valid_contract()
        contract["lean_interpretation_embedded"] = True
        interpretation = valid_interpretation()
        interpretation["interpretation_status"] = "TECHNICAL_DISCOVERY_REQUIRED"
        findings = []
        semantic.validate_execution_gate(valid_meaning(), contract, interpretation, findings)
        self.assertFalse(any("not aligned" in item for item in findings))

    def test_invalid_deviation_route_is_rejected(self):
        interpretation = valid_interpretation()
        interpretation["deviation_route"] = "CODEX_DECIDES_PRODUCT_CHANGE"
        findings = []
        semantic.validate_interpretation(interpretation, findings, ["GC1"])
        self.assertTrue(any("invalid deviation_route" in item for item in findings))

    def test_duplicate_golden_case_ids_are_rejected(self):
        golden = valid_golden()
        golden["cases"].append(dict(golden["cases"][0]))
        findings = []
        semantic.validate_golden(golden, findings)
        self.assertTrue(any("must be unique" in item for item in findings))

    def test_brain_review_requires_original_problem_result(self):
        review = valid_review()
        review["original_problem_actually_solved"] = "yes"
        findings = []
        semantic.validate_brain_review(review, findings)
        self.assertTrue(any("must be boolean" in item for item in findings))


if __name__ == "__main__":
    unittest.main()
