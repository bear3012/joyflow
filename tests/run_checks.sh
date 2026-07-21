#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
python -m unittest -v tests/test_semantic_closure.py
python scripts/run_checks.py
