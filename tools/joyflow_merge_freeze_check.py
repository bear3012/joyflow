#!/usr/bin/env python3
from __future__ import annotations
import pathlib
import sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
from joyflow_phase1_merge import main
if __name__ == "__main__":
    raise SystemExit(main())
