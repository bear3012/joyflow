#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import os
import pathlib
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.platform_capabilities import probe_symlink_capability

BATCH_SIZE = 8
EXECUTION_UNIT_TIMEOUT_SECONDS = 120
MODULE_TIMEOUT_SECONDS = EXECUTION_UNIT_TIMEOUT_SECONDS
BATCH_TIMEOUT_SECONDS = EXECUTION_UNIT_TIMEOUT_SECONDS
MODULE_FIRST_MAX_TESTS = 12
LIVENESS_BOUND_SOURCE = "tools/run_test_suite.py:EXECUTION_UNIT_TIMEOUT_SECONDS"
PROGRESS_HOST_ENV = "JOYFLOW_PROGRESS_HOST"
PROGRESS_PORT_ENV = "JOYFLOW_PROGRESS_PORT"
PROGRESS_BINDING_ENV = "JOYFLOW_PROGRESS_BINDING"
PROGRESS_INDEX_MAP_ENV = "JOYFLOW_PROGRESS_INDEX_MAP"
PROGRESS_TOTAL_ENV = "JOYFLOW_PROGRESS_TEST_TOTAL"

_TEST_INDEX_BY_ID: dict[str, int] = {}
_TEST_TOTAL = 0


def _progress_request(message: dict) -> dict | None:
    host = os.environ.get(PROGRESS_HOST_ENV)
    port_text = os.environ.get(PROGRESS_PORT_ENV)
    if not host or not port_text:
        return None
    try:
        with socket.create_connection((host, int(port_text))) as connection:
            connection.sendall(json.dumps(message, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n")
            connection.shutdown(socket.SHUT_WR)
            raw = b""
            while not raw.endswith(b"\n"):
                chunk = connection.recv(4096)
                if not chunk:
                    break
                raw += chunk
        response = json.loads(raw)
        return response if isinstance(response, dict) else None
    except (OSError, ValueError, json.JSONDecodeError):
        # Observability never changes unittest result or its formal output bytes.
        return None


def _machine_binding() -> dict | None:
    text = os.environ.get(PROGRESS_BINDING_ENV)
    if not text:
        return None
    try:
        binding = json.loads(text)
    except json.JSONDecodeError:
        return None
    return binding if isinstance(binding, dict) else None


def announce_test_command_started(test_total: int) -> None:
    binding = _machine_binding()
    if binding is None:
        return
    _progress_request({
        **binding,
        "event_type": "test_command_started",
        "test_total": test_total,
        "liveness_bound_source": LIVENESS_BOUND_SOURCE,
        "liveness_bound_value": EXECUTION_UNIT_TIMEOUT_SECONDS,
    })


def emit_test_completed(test_id: str) -> None:
    binding = _machine_binding()
    if binding is None:
        return
    try:
        index_map = json.loads(os.environ[PROGRESS_INDEX_MAP_ENV])
        test_index = index_map[test_id]
        test_total = int(os.environ[PROGRESS_TOTAL_ENV])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return
    requested = _progress_request({**binding, "event_type": "sequence_request"})
    if not requested or not isinstance(requested.get("next_sequence"), int):
        return
    _progress_request({
        **binding,
        "event_type": "test_completed",
        "sequence": requested["next_sequence"],
        "test_id": test_id,
        "test_index": test_index,
        "test_total": test_total,
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "liveness_bound_source": LIVENESS_BOUND_SOURCE,
        "liveness_bound_value": EXECUTION_UNIT_TIMEOUT_SECONDS,
    })


class ProgressTextTestResult(unittest.TextTestResult):
    def stopTest(self, test: unittest.case.TestCase) -> None:
        super().stopTest(test)
        emit_test_completed(test.id())


def unit_child_main(test_ids: list[str]) -> int:
    suite = unittest.defaultTestLoader.loadTestsFromNames(test_ids)
    result = unittest.TextTestRunner(
        stream=sys.stderr, verbosity=0, resultclass=ProgressTextTestResult,
    ).run(suite)
    return 0 if result.wasSuccessful() else 1


def discover_test_ids(path: pathlib.Path) -> list[str]:
    """Discover unittest test methods without importing the test module."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    module = f"tests.{path.stem}"
    ids: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_"):
                ids.append(f"{module}.{node.name}.{item.name}")
    return sorted(ids)


def _run_unittest(label: str, test_ids: list[str], timeout_seconds: int) -> tuple[int, int, str, str]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env[PROGRESS_INDEX_MAP_ENV] = json.dumps(
        {test_id: _TEST_INDEX_BY_ID[test_id] for test_id in test_ids if test_id in _TEST_INDEX_BY_ID},
        sort_keys=True,
    )
    env[PROGRESS_TOTAL_ENV] = str(_TEST_TOTAL)
    with tempfile.TemporaryDirectory(prefix="joyflow-test-run-") as td:
        stdout_path = pathlib.Path(td) / "stdout.txt"
        stderr_path = pathlib.Path(td) / "stderr.txt"
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            proc = subprocess.Popen(
                [sys.executable, str(pathlib.Path(__file__).resolve()), "--joyflow-unit-child", *test_ids],
                cwd=ROOT,
                stdout=stdout_file,
                stderr=stderr_file,
                env=env,
                start_new_session=(os.name == "posix"),
            )
            timed_out = False
            try:
                returncode = proc.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                if os.name == "posix":
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
                returncode = proc.wait()
        stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
        stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
    if timed_out:
        stderr += f"\nTEST_TIMEOUT label={label} after={timeout_seconds}s\n"
        return 124, 0, stdout, stderr
    text = stderr + stdout
    matches = re.findall(r"Ran (\d+) tests?", text)
    count = int(matches[-1]) if matches else 0
    skipped = [int(value) for value in re.findall(r"skipped=(\d+)", text)]
    if skipped and skipped[-1] > 0:
        stderr += f"\nUNEXPECTED_UNITTEST_SKIP label={label} skipped={skipped[-1]}\n"
        return 2, count, stdout, stderr
    return returncode, count, stdout, stderr


def run_batch(module: str, batch_index: int, test_ids: list[str]) -> tuple[int, int, str, str]:
    returncode, count, stdout, stderr = _run_unittest(f"{module}:batch={batch_index}", test_ids, BATCH_TIMEOUT_SECONDS)
    if returncode == 124 and len(test_ids) > 1:
        method_rc, method_count, method_stdout, method_stderr = run_methods(
            module, test_ids, f"BATCH_TIMEOUT_METHOD_FALLBACK batch={batch_index}"
        )
        return method_rc, method_count, stdout + method_stdout, stderr + method_stderr
    return returncode, count, stdout, stderr


def run_methods(module: str, test_ids: list[str], reason: str) -> tuple[int, int, str, str]:
    total = 0
    stdout_parts: list[str] = []
    stderr_parts: list[str] = [f"{reason} module={module} methods={len(test_ids)}\n"]
    for method_index, test_id in enumerate(test_ids, start=1):
        returncode, count, stdout, stderr = _run_unittest(
            f"{module}:method={method_index}", [test_id], BATCH_TIMEOUT_SECONDS
        )
        stdout_parts.append(stdout)
        stderr_parts.append(stderr)
        stderr_parts.append(
            f"METHOD_FALLBACK_RESULT module={module} method={test_id} rc={returncode} tests={count}\n"
        )
        total += count
        if returncode != 0:
            return returncode, total, "".join(stdout_parts), "".join(stderr_parts)
        if count != 1:
            stderr_parts.append(
                f"METHOD_TEST_COUNT_MISMATCH module={module} method={test_id} expected=1 observed={count}\n"
            )
            return 2, total, "".join(stdout_parts), "".join(stderr_parts)
    if total != len(test_ids):
        stderr_parts.append(
            f"METHOD_FALLBACK_COUNT_MISMATCH module={module} expected={len(test_ids)} observed={total}\n"
        )
        return 2, total, "".join(stdout_parts), "".join(stderr_parts)
    return 0, total, "".join(stdout_parts), "".join(stderr_parts)


def run_batches(module: str, test_ids: list[str]) -> tuple[int, int, str, str]:
    total = 0
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    for batch_index, start in enumerate(range(0, len(test_ids), BATCH_SIZE), start=1):
        batch = test_ids[start:start + BATCH_SIZE]
        returncode, count, stdout, stderr = run_batch(module, batch_index, batch)
        stdout_parts.append(stdout)
        stderr_parts.append(stderr)
        total += count
        if returncode != 0:
            return returncode, total, "".join(stdout_parts), "".join(stderr_parts)
    if total != len(test_ids):
        stderr_parts.append(
            f"BATCH_TEST_COUNT_MISMATCH module={module} expected={len(test_ids)} observed={total}\n"
        )
        return 2, total, "".join(stdout_parts), "".join(stderr_parts)
    return 0, total, "".join(stdout_parts), "".join(stderr_parts)


def run_module(path: pathlib.Path) -> tuple[str, int, int, str, str]:
    module = f"tests.{path.stem}"
    test_ids = discover_test_ids(path)
    expected_count = len(test_ids)
    module_targets = test_ids or [module]
    batch_ids = test_ids or module_targets
    # Large historical modules stay on the proven isolated-batch path; otherwise a slow module-first attempt can add an entire timeout before fallback.
    if expected_count > MODULE_FIRST_MAX_TESTS:
        batch_rc, batch_count, batch_stdout, batch_stderr = run_batches(module, batch_ids)
        return module, batch_rc, batch_count, batch_stdout, f"LARGE_MODULE_BATCH_PATH module={module} tests={expected_count} threshold={MODULE_FIRST_MAX_TESTS}\n" + batch_stderr

    returncode, count, stdout, stderr = _run_unittest(f"{module}:module", module_targets, MODULE_TIMEOUT_SECONDS)

    # Fast normal path: one process, exact discovered test count, all PASS.
    if returncode == 0 and (expected_count == 0 or count == expected_count):
        return module, 0, count, stdout, stderr

    if returncode == 124:
        # A timeout must strictly reduce execution granularity. Modules no larger than one batch go directly to methods.
        if test_ids and expected_count <= BATCH_SIZE:
            fallback_rc, fallback_count, fallback_stdout, fallback_stderr = run_methods(
                module, test_ids, "MODULE_TIMEOUT_METHOD_FALLBACK"
            )
        else:
            fallback_rc, fallback_count, fallback_stdout, fallback_stderr = run_batches(module, batch_ids)
        combined_stdout = stdout + fallback_stdout
        combined_stderr = stderr + f"\nMODULE_FIRST_FALLBACK module={module} module_rc={returncode} module_tests={count} expected={expected_count}\n" + fallback_stderr
        # A module-level timeout may be safely recovered only if every discovered test passes at smaller bounded granularity.
        return module, fallback_rc, fallback_count, combined_stdout, combined_stderr

    # Non-timeout failures and count mismatches retain the existing isolated-batch diagnostic path.
    batch_rc, batch_count, batch_stdout, batch_stderr = run_batches(module, batch_ids)
    combined_stdout = stdout + batch_stdout
    combined_stderr = stderr + f"\nMODULE_FIRST_FALLBACK module={module} module_rc={returncode} module_tests={count} expected={expected_count}\n" + batch_stderr

    if returncode != 0:
        # Preserve a real module-level failure even if isolated batches happen to pass; this can expose order/shared-state failures.
        return module, returncode if returncode != 0 else 2, batch_count, combined_stdout, combined_stderr
    if expected_count and count != expected_count:
        # Count mismatch is diagnostic uncertainty. Accept only exact full fallback coverage.
        if batch_rc == 0 and batch_count == expected_count:
            return module, 0, batch_count, combined_stdout, combined_stderr
        return module, 2, batch_count, combined_stdout, combined_stderr
    return module, batch_rc, batch_count, combined_stdout, combined_stderr


def main() -> int:
    global _TEST_INDEX_BY_ID, _TEST_TOTAL
    capability = probe_symlink_capability()
    print("PLATFORM_CAPABILITY " + repr(capability), flush=True)
    paths = sorted((ROOT / "tests").glob("test_*.py"))
    all_test_ids = [test_id for path in paths for test_id in discover_test_ids(path)]
    expected_total = len(all_test_ids)
    _TEST_INDEX_BY_ID = {test_id: index for index, test_id in enumerate(all_test_ids, start=1)}
    _TEST_TOTAL = expected_total
    announce_test_command_started(expected_total)
    started = time.monotonic()
    results = []
    for path in paths:
        print(f"RUNNING {path.stem}", flush=True)
        result = run_module(path)
        print(f"FINISHED {path.stem} rc={result[1]} tests={result[2]}", flush=True)
        results.append(result)
    results.sort(key=lambda row: row[0])
    failed = [row for row in results if row[1] != 0]
    if failed:
        for module, code, _, stdout, stderr in failed:
            print(f"=== {module} FAILED rc={code} ===", file=sys.stderr)
            if stdout:
                print(stdout, file=sys.stderr, end="")
            if stderr:
                print(stderr, file=sys.stderr, end="")
        return 2
    total = sum(row[2] for row in results)
    if total != expected_total:
        print(f"TEST_COUNT_MISMATCH expected={expected_total} observed={total}", file=sys.stderr)
        return 2
    elapsed = time.monotonic() - started
    print(f"Ran {total} tests in {elapsed:.3f}s")
    print()
    print("OK")
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--joyflow-unit-child":
        raise SystemExit(unit_child_main(sys.argv[2:]))
    raise SystemExit(main())
