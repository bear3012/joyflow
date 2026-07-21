#!/usr/bin/env python3
"""Render the short pre-implementation Codex interpretation request.

This prompt authorizes no repository mutation. Human transfers the response to Brain,
and Brain decides whether the interpretation is aligned.
"""
from __future__ import annotations

from typing import Any, Dict, List

from joyflow_common import read_json, write_text

MEANING_PATH = "runtime/product_meaning_closure.json"
CONTRACT_PATH = "runtime/translation_contract.json"
GOLDEN_PATH = "runtime/golden_cases.json"
OUTPUT_PATH = "runtime/codex_interpretation_request.md"


def bullets(values: Any) -> str:
    if isinstance(values, list) and values:
        return "\n".join(f"- {value}" for value in values)
    return "- NONE"


def main() -> int:
    meaning: Dict[str, Any] = read_json(MEANING_PATH, default={})
    contract: Dict[str, Any] = read_json(CONTRACT_PATH, default={})
    golden: Dict[str, Any] = read_json(GOLDEN_PATH, default={})
    semantic = contract.get("human_semantic_layer", {}) if isinstance(contract.get("human_semantic_layer"), dict) else {}
    mechanical = contract.get("mechanical_execution_layer", {}) if isinstance(contract.get("mechanical_execution_layer"), dict) else {}
    case_ids: List[str] = []
    for case in golden.get("cases", []) if isinstance(golden.get("cases"), list) else []:
        if isinstance(case, dict) and isinstance(case.get("case_id"), str):
            case_ids.append(case["case_id"])

    text = f"""# Joyflow Codex Execution Interpretation Request

This is read-only semantic handshake work. Do not modify repository files, create commits, push, or open a PR.

## Original problem

{meaning.get('original_user_problem', '')}

## Objective

{semantic.get('objective', '')}

## Expected user-visible result

{semantic.get('expected_user_result', '')}

## User flow

{bullets(semantic.get('user_flow', []))}

## Must preserve

{bullets(mechanical.get('must_preserve', []))}

## Allowed solution surfaces

{bullets(mechanical.get('allowed_solution_surfaces', []))}

## Forbidden consequences

{bullets(mechanical.get('forbidden_consequences', []))}

## Golden Case IDs

{bullets(case_ids)}

Return exactly one short artifact:

```text
CODEX_EXECUTION_INTERPRETATION:
  artifact_type: CODEX_EXECUTION_INTERPRETATION
  task_id: {contract.get('task_id', '')}
  objective_understood:
  user_visible_result:
  user_flow_understood:
  must_preserve:
  intended_solution_surface:
  excluded_changes:
  golden_cases_understood:
  unresolved_items:
  interpretation_status: ALIGNED | TECHNICAL_DISCOVERY_REQUIRED | MATERIAL_UNCERTAINTY | CONTRACT_CONFLICT
  deviation_route: AUTO_ACCEPTABLE_TECHNICAL_VARIATION | BRAIN_REVIEW_REQUIRED | USER_DECISION_REQUIRED
```

Use `ALIGNED` only when no unresolved item could change product result, user flow, data meaning, scope, risk, tradeoff, or acceptance. Otherwise stop at the matching non-execution status.
"""
    write_text(OUTPUT_PATH, text)
    print("JOYFLOW_CODEX_INTERPRETATION_REQUEST_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
