#!/usr/bin/env python3
"""Seal, detach, and execute a bounded Joyflow mechanical validation job.

The worker has evidence-only authority.  It never creates a Codex Return,
repairs source, publishes repository state, or resumes Codex.
"""

from __future__ import annotations

import argparse
import base64
import copy
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import selectors
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid


TOOL = "joyflow-typed-execution-evidence-runner"
JOB_TYPE = "P0_MECHANICAL_JOB"
EVIDENCE_TYPE = "P0_MECHANICAL_EXECUTION_EVIDENCE"
COMPLETION_TYPE = "P0_MECHANICAL_COMPLETION"
FAILURE_TYPE = "P0_MECHANICAL_INFRASTRUCTURE_FAILURE"
CONTINUATION_TYPE = "P0_CONTRACT_CLOSED_CONTINUATION"
CLAIM_TYPE = "P0_CONTINUATION_CLAIM"
ALLOWED_RESUME_MODE = "SAME_CONTRACT_CONTINUATION"
RESULT_AVAILABLE = "RESULT_AVAILABLE"
MACHINE_INFRASTRUCTURE_FAILED = "MACHINE_INFRASTRUCTURE_FAILED"
CLAIMED = "CLAIMED"
DISPATCH_CONFIRMED = "DISPATCH_CONFIRMED"
DISPATCH_UNKNOWN = "DISPATCH_UNKNOWN"
STOP_CONTINUATION_WRONG_THREAD = "STOP_CONTINUATION_WRONG_THREAD"
MANUAL_ACKNOWLEDGED = "MANUAL_ACKNOWLEDGED"
ACTIVE_AWAITING_FIRST_PROGRESS = "ACTIVE_AWAITING_FIRST_PROGRESS"
ACTIVE_PROGRESSING = "ACTIVE_PROGRESSING"
ACTIVE_NO_RECENT_PROGRESS = "ACTIVE_NO_RECENT_PROGRESS"
CONTINUATION_NOT_REACHED = "CONTINUATION_NOT_REACHED"
CONTINUATION_DISPATCHING = "CONTINUATION_DISPATCHING"
TEST_COMMAND_INDEX = 6
PROGRESS_ARTIFACT = "machine-progress.jsonl"
STATUS_ARTIFACT = "machine-status.json"
PROBE_ARTIFACT = "machine-probes.jsonl"
INITIAL_LAUNCH_CLAIM_ARTIFACT = "initial-launch-claim.json"
SESSION_BINDING_ARTIFACT = "codex-session-binding.json"
INITIAL_TERMINAL_ARTIFACT = "initial-process-terminal.json"
CLI_OWNED_PRODUCTION = "CLI_OWNED_PRODUCTION"
LEGACY_EXPLICIT = "LEGACY_EXPLICIT"
TARGETED_CHECK = ("CHECK_P0_TARGETED", [
    "python", "-m", "unittest",
    "tests.test_runner_module_first", "tests.test_p0_mechanical_continuation",
])
APPROVED_COMMANDS = (
    ("CHECK_P0_MACHINE_01", ["python", "tools/generate_mechanical_assets.py", "--check"]),
    ("CHECK_P0_MACHINE_02", ["python", "tools/generate_old_rule_migration.py", "--check"]),
    ("CHECK_P0_MACHINE_03", ["python", "tools/validate_migration_claims.py", "--root", "."]),
    ("CHECK_P0_MACHINE_04", ["python", "tools/generate_all_examples.py", "--check"]),
    ("CHECK_P0_MACHINE_05", ["python", "runtime/joyflow_source_validator.py", "."]),
    ("CHECK_P0_MACHINE_06", ["python", "tools/run_test_suite.py"]),
    ("CHECK_P0_MACHINE_07", ["git", "diff", "--check"]),
)
JOB_KEYS = {
    "artifact_type", "version", "execution_id", "projection_digest",
    "execution_authorization_envelope_digest", "repository", "execution_workspace",
    "observed_object", "expected_before", "formal_target_ref", "turn_a_provenance",
    "commands", "repository_publication_mode", "execution_event_id", "attempt_id",
    "continuation_binding",
    "job_digest",
}

CONTINUATION_BINDING_KEYS = {
    "contract_digest", "continuation_id", "codex_session_id", "codex_thread_id",
    "predecessor_turn_id", "allowed_resume_mode", "binding_mode",
    "execution_material_sha256", "codex_runtime_identity", "initial_process_binding",
}

TURN_A_KEYS = {
    "approved_input_capture", "mutation_before_capture", "mutation_after_capture",
    "mutation_diff_capture", "targeted_validation_capture", "allowed_changed_paths",
}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest_object(value: dict, digest_field: str) -> str:
    body = dict(value)
    body.pop(digest_field, None)
    return hashlib.sha256(canonical_bytes(body)).hexdigest()


def _run_bytes(argv: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess:
    completed = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {argv!r}: {completed.stderr.decode('utf-8', 'replace')}")
    return completed


def _git_text(repository: Path, *args: str) -> str:
    return _run_bytes(["git", *args], repository).stdout.decode("utf-8").strip()


def repository_snapshot(repository: Path) -> dict:
    repository = repository.resolve()
    raw = _run_bytes(["git", "status", "--porcelain=v1", "-z", "-uall"], repository).stdout
    fields = raw.split(b"\0")
    records: list[str] = []
    statuses: list[str] = []
    index = 0
    while index < len(fields) and fields[index]:
        entry = fields[index].decode("utf-8")
        if len(entry) < 4 or entry[2] != " ":
            raise RuntimeError(f"unexpected porcelain record: {entry!r}")
        status, path = entry[:2], entry[3:]
        index += 1
        if status[0] in "RC" or status[1] in "RC":
            if index >= len(fields) or not fields[index]:
                raise RuntimeError("truncated rename/copy porcelain record")
            index += 1
        data = (repository / PurePosixPath(path)).read_bytes()
        records.append(f"{path}|{status}|{hashlib.sha256(data).hexdigest()}|{len(data)}")
        statuses.append(status)
    records.sort(key=lambda item: item.encode("utf-8"))
    joined = "\n".join(records).encode("utf-8")
    return {
        "branch": _git_text(repository, "branch", "--show-current"),
        "HEAD": _git_text(repository, "rev-parse", "HEAD"),
        "tracked_modified": sum(status != "??" for status in statuses),
        "untracked": sum(status == "??" for status in statuses),
        "staged": sum(status[0] not in " ?" for status in statuses),
        "total_candidate_paths": len(statuses),
        "canonical_snapshot": hashlib.sha256(joined).hexdigest(),
        "records": records,
    }


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _load_named_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module cannot be loaded: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_capture_module(repository: Path):
    path = repository / "tools" / "capture_execution_evidence.py"
    spec = importlib.util.spec_from_file_location("joyflow_capture_execution_evidence", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("production capture module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_runtime_module(repository: Path):
    path = repository / "runtime" / "joyflow_dual_layer.py"
    spec = importlib.util.spec_from_file_location("joyflow_formal_runtime", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("production runtime module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _capture_payload(capture: dict) -> dict:
    return {key: value for key, value in capture.items() if key != "capture_sha256"}


def _validate_capture_digest(capture: dict) -> None:
    if capture.get("capture_sha256") != hashlib.sha256(canonical_bytes(_capture_payload(capture))).hexdigest():
        raise ValueError("Turn-A capture digest mismatch")


def _path_allowed(path: str, allowed_paths: list[str]) -> bool:
    return any(path == allowed or (allowed.endswith("/**") and path.startswith(allowed[:-2])) for allowed in allowed_paths)


def _resubject_capture(capture: dict, capture_id: str, subject_type: str, subject_id: str) -> dict:
    result = copy.deepcopy(capture)
    result.update({"capture_id": capture_id, "subject_type": subject_type, "subject_id": subject_id})
    result["capture_sha256"] = digest_object(result, "capture_sha256")
    return result


def _capture_repository_state(repository: Path, phase: str, capture_id: str) -> dict:
    capture_module = _load_capture_module(repository)
    root, repository_id, head, _ = capture_module.repo_identity(str(repository))
    observation = capture_module.repository_state_observation(root, phase, [])
    return capture_module.build_capture(
        capture_id=capture_id,
        capture_kind="REPOSITORY_STATE",
        command=f"joyflow repository-state {phase} {shlex.quote(str(root))}",
        exit_code=0,
        stdout=capture_module.canonical_bytes(observation) + b"\n",
        stderr=b"",
        observed_object=capture_module.repository_object(repository_id, head),
        observation=observation,
        subject_type="LOCAL_REPOSITORY_SOURCE_STATE",
        subject_id=f"{head}:{phase}",
    )


def _capture_current_test(repository: Path, target_ref: str) -> dict:
    check_id, argv = TARGETED_CHECK
    started = time.perf_counter()
    completed = _run_bytes(argv, repository, check=False)
    elapsed = time.perf_counter() - started
    capture_module = _load_capture_module(repository)
    _, repository_id, head, _ = capture_module.repo_identity(str(repository))
    capture = capture_module.build_capture(
        capture_id="CAP_TURN_A_TARGETED",
        capture_kind="TEST_COMMAND",
        command=shlex.join(argv),
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        observed_object=capture_module.repository_object(repository_id, head),
        observation={"argv": argv, "cwd_scope": "SOURCE_ROOT", "target_ref": target_ref},
        subject_type="VALIDATION_CHECK",
        subject_id=check_id,
    )
    capture["elapsed_seconds"] = elapsed
    capture["capture_sha256"] = digest_object(capture, "capture_sha256")
    if completed.returncode != 0:
        raise RuntimeError("targeted Turn-A validation failed")
    return capture


def _local_diff_capture(repository: Path, before_source: Path, before_fp: str, after_fp: str) -> dict:
    candidates = (
        "tools/run_mechanical_continuation.py",
        "tools/run_test_suite.py",
        "tests/test_p0_mechanical_continuation.py",
        "tests/test_runner_module_first.py",
        "tools/generate_mechanical_assets.py",
    )
    temporary = Path(tempfile.mkdtemp(prefix="joyflow-local-diff-"))
    try:
        (temporary / ".gitattributes").write_text(
            "".join(f"{relative} -text -diff\n" for relative in candidates),
            encoding="utf-8", newline="\n",
        )
        for relative in candidates:
            source = before_source / PurePosixPath(relative)
            if source.exists():
                destination = temporary / PurePosixPath(relative)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
        _run_bytes(["git", "init", "-q"], temporary)
        _run_bytes(["git", "config", "user.email", "joyflow@invalid"], temporary)
        _run_bytes(["git", "config", "user.name", "Joyflow Capture"], temporary)
        _run_bytes(["git", "config", "core.autocrlf", "false"], temporary)
        _run_bytes(["git", "config", "core.safecrlf", "false"], temporary)
        _run_bytes(["git", "add", "--all"], temporary)
        _run_bytes(["git", "commit", "-qm", "sealed before"], temporary)
        for relative in candidates:
            source = repository / PurePosixPath(relative)
            destination = temporary / PurePosixPath(relative)
            if source.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
            elif destination.exists():
                destination.unlink()
        patch = _run_bytes(["git", "diff", "--binary", "--no-ext-diff", "--no-textconv", "HEAD"], temporary).stdout
        names = _run_bytes(["git", "diff", "--name-only", "HEAD"], temporary).stdout.decode("utf-8").splitlines()
    finally:
        shutil.rmtree(temporary, ignore_errors=True)
    changed_paths = sorted(path for path in names if path)
    if not patch or not changed_paths:
        raise ValueError("formal mutation Diff is empty")
    capture_module = _load_capture_module(repository)
    _, repository_id, head, _ = capture_module.repo_identity(str(repository))
    return capture_module.build_capture(
        capture_id="CAP_TURN_A_LOCAL_DIFF",
        capture_kind="REPOSITORY_DIFF",
        command="joyflow local-repository-diff",
        exit_code=0,
        stdout=patch,
        stderr=b"",
        observed_object=capture_module.repository_object(repository_id, head),
        observation={
            "base_ref": before_fp,
            "head_ref": after_fp,
            "changed_paths": changed_paths,
            "diff_sha256": hashlib.sha256(patch).hexdigest(),
        },
        subject_type="LOCAL_REPOSITORY_RESULT",
        subject_id=after_fp,
    )


@contextlib.contextmanager
def _exact_git_bytes_environment():
    keys = ("GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0")
    previous = {key: os.environ.get(key) for key in keys}
    os.environ.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.autocrlf", "GIT_CONFIG_VALUE_0": "false"})
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def verify_turn_a_diff(job: dict) -> list[str]:
    validate_job(job)
    repository = Path(job["repository"])
    runtime = _load_runtime_module(repository)
    provenance = job["turn_a_provenance"]
    before = provenance["mutation_before_capture"]["observation"]
    after = provenance["mutation_after_capture"]["observation"]
    with _exact_git_bytes_environment(), runtime._isolated_local_repository_result(repository, after) as target:
        return runtime._verify_local_repository_diff(target, provenance["mutation_diff_capture"], before, after)


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(canonical_bytes(value))
    os.replace(temporary, path)


def _exclusive_json(path: Path, value: dict) -> None:
    """Acquire a one-shot filesystem claim; partial creation still fails closed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        # The path deliberately remains claimed if publication becomes uncertain.
        raise


def _artifact_digest(value: dict) -> str:
    return digest_object(value, "artifact_digest")


def _validate_artifact_digest(value: dict, artifact_type: str) -> None:
    if value.get("artifact_type") != artifact_type or value.get("artifact_digest") != _artifact_digest(value):
        raise ValueError(f"invalid {artifact_type} artifact or digest")


def _codex_runtime_identity() -> dict:
    located = shutil.which("codex")
    if not located:
        raise RuntimeError("Codex executable cannot be resolved")
    executable = Path(located).resolve()
    executable_bytes = executable.read_bytes()
    version = _run_bytes([str(executable), "--version"], Path.cwd()).stdout.decode("utf-8", "strict").strip()
    raw_home = os.environ.get("CODEX_HOME")
    if raw_home:
        state_root = str(Path(raw_home).resolve())
        state_mode = "EXPLICIT_CODEX_HOME"
    else:
        profile = os.environ.get("USERPROFILE") or str(Path.home())
        state_root = str((Path(profile) / ".codex").resolve())
        state_mode = "DEFAULT_FROM_USERPROFILE"
    identity = {
        "resolved_codex_executable": str(executable),
        "executable_sha256": hashlib.sha256(executable_bytes).hexdigest(),
        "codex_version": version,
        "state_root_identity": {
            "mode": state_mode,
            "CODEX_HOME": raw_home,
            "effective_state_root": state_root,
            "USERPROFILE": os.environ.get("USERPROFILE"),
            "APPDATA": os.environ.get("APPDATA"),
            "LOCALAPPDATA": os.environ.get("LOCALAPPDATA"),
        },
    }
    identity["runtime_identity"] = digest_object(identity, "runtime_identity")
    return identity


def _runtime_artifact_fields(identity: dict) -> dict:
    return {
        "resolved_codex_executable": identity["resolved_codex_executable"],
        "executable_sha256": identity["executable_sha256"],
        "codex_version": identity["codex_version"],
        "state_root_identity": identity["state_root_identity"],
        "runtime_identity": identity["runtime_identity"],
    }


def _new_lifecycle_listener() -> tuple[socket.socket, dict]:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    host, port = listener.getsockname()
    return listener, {"host": host, "port": port, "nonce": uuid.uuid4().hex}


def _recv_json_line(connection: socket.socket) -> dict:
    raw = b""
    while not raw.endswith(b"\n"):
        chunk = connection.recv(65536)
        if not chunk:
            raise RuntimeError("lifecycle channel closed before a complete event")
        raw += chunk
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("lifecycle channel event must be a JSON object")
    return value


def _channel_request(coordinate: dict, event_type: str, execution_event_id: str, attempt_id: str) -> dict:
    return {
        "event_type": event_type,
        "execution_event_id": execution_event_id,
        "attempt_id": attempt_id,
        "nonce": coordinate["nonce"],
    }


def _wait_for_binding_wakeup(coordinate: dict, execution_event_id: str, attempt_id: str) -> dict:
    with socket.create_connection((coordinate["host"], coordinate["port"])) as connection:
        request = _channel_request(coordinate, "WAIT_BINDING_READY", execution_event_id, attempt_id)
        connection.sendall(canonical_bytes(request) + b"\n")
        return _recv_json_line(connection)


def _validate_session_binding(
    binding: dict, *, execution_event_id: str, attempt_id: str, contract_digest: str,
    repository: Path, workspace: Path,
) -> None:
    _validate_artifact_digest(binding, "P0_CODEX_SESSION_BINDING")
    expected = {
        "execution_event_id": execution_event_id,
        "attempt_id": attempt_id,
        "execution_material_sha256": contract_digest,
        "source_root": str(repository.resolve()),
        "lifecycle_workspace": str(workspace.resolve()),
    }
    for key, value in expected.items():
        if binding.get(key) != value:
            raise ValueError(f"Codex session binding {key} mismatch")
    session_id = binding.get("codex_session_id")
    thread_id = binding.get("codex_thread_id")
    if not isinstance(session_id, str) or session_id != thread_id:
        raise ValueError("Codex session binding lacks one authoritative thread")
    try:
        uuid.UUID(thread_id)
    except (TypeError, ValueError):
        raise ValueError("Codex session binding thread is not a UUID") from None
    runtime_identity = binding.get("codex_runtime_identity")
    if not isinstance(runtime_identity, dict) or runtime_identity.get("runtime_identity") != digest_object(runtime_identity, "runtime_identity"):
        raise ValueError("Codex session binding runtime identity mismatch")
    for key, value in _runtime_artifact_fields(runtime_identity).items():
        if binding.get(key) != value:
            raise ValueError(f"Codex session binding {key} mismatch")
    initial = binding.get("initial_process_binding")
    if not isinstance(initial, dict) or initial.get("initial_pid") != binding.get("initial_pid"):
        raise ValueError("Codex session binding initial process mismatch")
    channel = initial.get("terminal_channel")
    if not isinstance(channel, dict) or set(channel) != {"host", "port", "nonce"}:
        raise ValueError("Codex session binding terminal wake route missing")


def _production_session_binding(
    *, execution_event_id: str, attempt_id: str, contract_digest: str,
    repository: Path, workspace: Path,
) -> dict | None:
    if os.environ.get("JOYFLOW_CONTINUATION_MODE") != CLI_OWNED_PRODUCTION:
        return None
    bootstrap = {
        "source_root": os.environ.get("JOYFLOW_SOURCE_ROOT"),
        "lifecycle_workspace": os.environ.get("JOYFLOW_LIFECYCLE_WORKSPACE"),
        "execution_event_id": os.environ.get("JOYFLOW_EXECUTION_EVENT_ID"),
        "attempt_id": os.environ.get("JOYFLOW_ATTEMPT_ID"),
        "execution_material_sha256": os.environ.get("JOYFLOW_CONTRACT_DIGEST"),
    }
    expected = {
        "source_root": str(repository.resolve()),
        "lifecycle_workspace": str(workspace.resolve()),
        "execution_event_id": execution_event_id,
        "attempt_id": attempt_id,
        "execution_material_sha256": contract_digest,
    }
    if bootstrap != expected:
        raise ValueError("production Codex bootstrap binding mismatch")
    coordinate = json.loads(os.environ.get("JOYFLOW_BINDING_CHANNEL", "null"))
    if not isinstance(coordinate, dict) or set(coordinate) != {"host", "port", "nonce"}:
        raise ValueError("production Codex binding channel is invalid")
    binding_path = workspace / SESSION_BINDING_ARTIFACT
    if not binding_path.is_file():
        wake = _wait_for_binding_wakeup(coordinate, execution_event_id, attempt_id)
        if (wake.get("event_type") != "BINDING_READY" or
                wake.get("execution_event_id") != execution_event_id or
                wake.get("attempt_id") != attempt_id or
                wake.get("nonce") != coordinate["nonce"]):
            raise ValueError("invalid BINDING_READY wake event")
    if not binding_path.is_file():
        raise RuntimeError("Codex session binding unavailable after wake")
    binding = _load_json(binding_path)
    _validate_session_binding(
        binding, execution_event_id=execution_event_id, attempt_id=attempt_id,
        contract_digest=contract_digest, repository=repository, workspace=workspace,
    )
    return binding


def _resolve_seal_codex_binding(
    *, codex_session_id: str | None, codex_thread_id: str | None,
    execution_event_id: str, attempt_id: str, contract_digest: str,
    repository: Path, workspace: Path,
) -> dict:
    if (codex_session_id is None) != (codex_thread_id is None):
        raise ValueError("partial explicit Codex identity is forbidden")
    production = _production_session_binding(
        execution_event_id=execution_event_id, attempt_id=attempt_id,
        contract_digest=contract_digest, repository=repository, workspace=workspace,
    )
    if production is not None:
        authoritative = production["codex_thread_id"]
        if codex_session_id is not None and (
            codex_session_id != authoritative or codex_thread_id != authoritative
        ):
            raise ValueError("explicit Codex identity differs from authoritative production thread")
        return {
            "codex_session_id": authoritative,
            "codex_thread_id": authoritative,
            "binding_mode": CLI_OWNED_PRODUCTION,
            "codex_runtime_identity": production["codex_runtime_identity"],
            "initial_process_binding": production["initial_process_binding"],
        }
    if codex_session_id is None or codex_thread_id is None:
        raise ValueError("Codex identity is required without production binding")
    if codex_session_id != codex_thread_id:
        raise ValueError("explicit Codex session and thread must identify the same thread")
    return {
        "codex_session_id": codex_session_id,
        "codex_thread_id": codex_thread_id,
        "binding_mode": LEGACY_EXPLICIT,
        "codex_runtime_identity": None,
        "initial_process_binding": None,
    }


def _append_jsonl(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as stream:
        stream.write(canonical_bytes(value) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())


class ProgressMonitor:
    """Exact-bound transient projection; it has no terminal or repair authority."""

    def __init__(
        self, job: dict, supervisor_pid: int, worker_pid: int, *,
        clock=time.monotonic, bound_binding: tuple[str, int] | None = None,
    ):
        self.job = job
        self.workspace = Path(job["execution_workspace"])
        self.supervisor_pid = supervisor_pid
        self.worker_pid = worker_pid
        self.clock = clock
        self.bound_source, self.bound_value = (
            bound_binding if bound_binding is not None else _runner_liveness_binding(Path(job["repository"]))
        )
        self.started_at = clock()
        self.deadline: float | None = None
        self.last_sequence = 0
        self.current_event: dict | None = None
        self.current_epoch: str | int | None = None
        self.probed_epochs: set[str | int] = set()

    def _binding_matches(self, event: dict) -> bool:
        return (
            event.get("execution_event_id") == self.job["execution_event_id"] and
            event.get("attempt_id") == self.job["attempt_id"] and
            event.get("job_digest") == self.job["job_digest"] and
            event.get("command_index") == TEST_COMMAND_INDEX and
            event.get("liveness_bound_source") == self.bound_source and
            event.get("liveness_bound_value") == self.bound_value
        )

    def _status(self, state: str, **extra: object) -> dict:
        value = {
            "artifact_type": "P0_TRANSIENT_MACHINE_STATUS",
            "version": 1,
            "state": state,
            "execution_event_id": self.job["execution_event_id"],
            "attempt_id": self.job["attempt_id"],
            "job_digest": self.job["job_digest"],
            "command_index": TEST_COMMAND_INDEX,
            "last_accepted_sequence": self.last_sequence,
            "supervisor_pid": self.supervisor_pid,
            "worker_pid": self.worker_pid,
            "continuation_state": CONTINUATION_NOT_REACHED,
            "liveness_bound_source": self.bound_source,
            "liveness_bound_value": self.bound_value,
            **extra,
        }
        _atomic_json(self.workspace / STATUS_ARTIFACT, value)
        return value

    def next_sequence(self, event: dict) -> int | None:
        if event.get("event_type") != "sequence_request" or not self._binding_matches(event):
            return None
        return self.last_sequence + 1

    def accept(self, event: dict, *, now: float | None = None) -> bool:
        now = self.clock() if now is None else now
        if not self._binding_matches(event):
            return False
        if event.get("event_type") == "test_command_started":
            if self.current_epoch is not None:
                return False
            total = event.get("test_total")
            if not isinstance(total, int) or isinstance(total, bool) or total < 1:
                return False
            self.current_epoch = "INITIAL"
            self.deadline = now + self.bound_value
            self._status(
                ACTIVE_AWAITING_FIRST_PROGRESS,
                test_total=total,
                inactivity_epoch="INITIAL",
            )
            return True
        if event.get("event_type") != "test_completed" or self.current_epoch is None:
            return False
        sequence = event.get("sequence")
        test_id = event.get("test_id")
        test_index = event.get("test_index")
        test_total = event.get("test_total")
        if (
            not isinstance(sequence, int) or isinstance(sequence, bool) or sequence <= self.last_sequence or
            not isinstance(test_id, str) or not test_id or
            not isinstance(test_index, int) or isinstance(test_index, bool) or
            not isinstance(test_total, int) or isinstance(test_total, bool) or
            test_index < 1 or test_total < test_index or
            not isinstance(event.get("completed_at"), str) or not event["completed_at"]
        ):
            return False
        self.last_sequence = sequence
        self.current_event = dict(event)
        self.current_epoch = sequence
        self.deadline = now + self.bound_value
        _append_jsonl(self.workspace / PROGRESS_ARTIFACT, self.current_event)
        self._status(
            ACTIVE_PROGRESSING,
            sequence=sequence,
            test_id=test_id,
            test_index=test_index,
            test_total=test_total,
            completed_at=event["completed_at"],
            inactivity_epoch=sequence,
        )
        return True

    def expire(self, worker_process: subprocess.Popen, *, now: float | None = None) -> bool:
        now = self.clock() if now is None else now
        epoch = self.current_epoch
        if self.deadline is None or now < self.deadline or epoch in self.probed_epochs:
            return False
        self.probed_epochs.add(epoch)
        self.deadline = None
        worker_running = worker_process.poll() is None
        probe = {
            "artifact_type": "P0_READ_ONLY_MACHINE_PROBE",
            "version": 1,
            "probe_result": "INCOMPLETE",
            "execution_event_id": self.job["execution_event_id"],
            "attempt_id": self.job["attempt_id"],
            "job_digest": self.job["job_digest"],
            "command_index": TEST_COMMAND_INDEX,
            "inactivity_epoch": epoch,
            "last_accepted_sequence": self.last_sequence,
            "supervisor_pid": self.supervisor_pid,
            "supervisor_state": "RUNNING",
            "worker_pid": self.worker_pid,
            "worker_state": "RUNNING" if worker_running else "TERMINATED",
            "worker_descendants": "UNKNOWN",
            "current_leaf": "UNKNOWN",
            "current_test": self.current_event.get("test_id") if self.current_event else None,
            "elapsed_seconds": max(0.0, now - self.started_at),
            "available_workspace_artifacts": sorted(path.name for path in self.workspace.iterdir()),
            "read_only": True,
        }
        _append_jsonl(self.workspace / PROBE_ARTIFACT, probe)
        self._status(
            ACTIVE_NO_RECENT_PROGRESS,
            inactivity_epoch=epoch,
            probe_result=probe["probe_result"],
            probe_file=PROBE_ARTIFACT,
        )
        return True

    def publish_terminal(self, state: str) -> None:
        self.deadline = None
        extra: dict[str, object] = {"terminal_observed": True}
        if self.current_event is not None:
            extra.update({
                "sequence": self.last_sequence,
                "test_id": self.current_event["test_id"],
                "test_index": self.current_event["test_index"],
                "test_total": self.current_event["test_total"],
            })
        self._status(state, **extra)

    def publish_continuation(self, state: str) -> None:
        current = _load_json(self.workspace / STATUS_ARTIFACT)
        current["continuation_state"] = state
        _atomic_json(self.workspace / STATUS_ARTIFACT, current)


def validate_job(job: dict, expected_digest: str | None = None) -> None:
    if set(job) != JOB_KEYS or job.get("artifact_type") != JOB_TYPE or job.get("version") != 1:
        raise ValueError("invalid mechanical job shape")
    actual_digest = digest_object(job, "job_digest")
    if job.get("job_digest") != actual_digest:
        raise ValueError("mechanical job digest mismatch")
    if expected_digest is not None and actual_digest != expected_digest:
        raise ValueError("launched mechanical job identity mismatch")
    if job.get("repository_publication_mode") != "NONE":
        raise ValueError("repository publication is not authorized")
    for key in ("execution_event_id", "attempt_id", "execution_id"):
        if not isinstance(job.get(key), str) or not job[key]:
            raise ValueError(f"invalid {key}")
    continuation = job.get("continuation_binding")
    if not isinstance(continuation, dict) or set(continuation) != CONTINUATION_BINDING_KEYS:
        raise ValueError("invalid continuation binding")
    string_binding_keys = {
        "contract_digest", "continuation_id", "codex_session_id", "codex_thread_id",
        "predecessor_turn_id", "execution_material_sha256",
    }
    for key in string_binding_keys:
        if not isinstance(continuation.get(key), str) or not continuation[key]:
            raise ValueError(f"invalid continuation {key}")
    if continuation.get("allowed_resume_mode") != ALLOWED_RESUME_MODE:
        raise ValueError("invalid continuation resume mode")
    if continuation.get("execution_material_sha256") != continuation.get("contract_digest"):
        raise ValueError("continuation execution material digest mismatch")
    binding_mode = continuation.get("binding_mode")
    if binding_mode not in {LEGACY_EXPLICIT, CLI_OWNED_PRODUCTION}:
        raise ValueError("invalid continuation binding mode")
    if binding_mode == CLI_OWNED_PRODUCTION:
        if continuation["codex_session_id"] != continuation["codex_thread_id"]:
            raise ValueError("production continuation must bind one authoritative Codex thread")
        runtime_identity = continuation.get("codex_runtime_identity")
        if (not isinstance(runtime_identity, dict) or
                runtime_identity.get("runtime_identity") != digest_object(runtime_identity, "runtime_identity")):
            raise ValueError("invalid production Codex runtime identity")
        initial = continuation.get("initial_process_binding")
        if not isinstance(initial, dict) or not isinstance(initial.get("initial_pid"), int):
            raise ValueError("invalid production initial process binding")
        channel = initial.get("terminal_channel")
        if not isinstance(channel, dict) or set(channel) != {"host", "port", "nonce"}:
            raise ValueError("invalid production initial terminal wake route")
    elif continuation.get("codex_runtime_identity") is not None or continuation.get("initial_process_binding") is not None:
        raise ValueError("legacy continuation cannot claim production runtime ownership")
    if continuation["codex_session_id"] in {"--last", "last"}:
        raise ValueError("heuristic Codex session targeting is forbidden")
    provenance = job.get("turn_a_provenance")
    if not isinstance(provenance, dict) or set(provenance) != TURN_A_KEYS:
        raise ValueError("missing Turn-A mutation provenance")
    approved = provenance["approved_input_capture"]
    before = provenance["mutation_before_capture"]
    after = provenance["mutation_after_capture"]
    diff = provenance["mutation_diff_capture"]
    targeted = provenance["targeted_validation_capture"]
    for capture in (approved, before, after, diff, targeted):
        if not isinstance(capture, dict):
            raise ValueError("invalid Turn-A mutation provenance capture")
        _validate_capture_digest(capture)
    before_observation = before.get("observation", {})
    after_observation = after.get("observation", {})
    before_fp = before_observation.get("state_fingerprint_sha256")
    after_fp = after_observation.get("state_fingerprint_sha256")
    if before.get("capture_kind") != "REPOSITORY_STATE" or before_observation.get("capture_phase") != "BEFORE":
        raise ValueError("invalid formal mutation BEFORE capture")
    if after.get("capture_kind") != "REPOSITORY_STATE" or after_observation.get("capture_phase") != "AFTER":
        raise ValueError("invalid formal mutation AFTER capture")
    if not before_fp or before_fp == after_fp:
        raise ValueError("completed mutation formal BEFORE fingerprint equals formal AFTER fingerprint")
    if job.get("formal_target_ref") != after_fp:
        raise ValueError("sealed formal target_ref differs from mutation AFTER fingerprint")
    diff_observation = diff.get("observation", {})
    changed_paths = diff_observation.get("changed_paths")
    allowed = provenance.get("allowed_changed_paths")
    if (diff.get("capture_kind") != "REPOSITORY_DIFF" or
            diff_observation.get("base_ref") != before_fp or
            diff_observation.get("head_ref") != after_fp or
            not isinstance(changed_paths, list) or not changed_paths or
            not isinstance(allowed, list) or any(not _path_allowed(path, allowed) for path in changed_paths)):
        raise ValueError("formal repository Diff binding or scope mismatch")
    target_observation = targeted.get("observation", {})
    if (targeted.get("capture_kind") != "TEST_COMMAND" or
            target_observation.get("argv") != TARGETED_CHECK[1] or
            target_observation.get("target_ref") != after_fp or
            targeted.get("command") != shlex.join(TARGETED_CHECK[1]) or
            targeted.get("exit_code") != 0):
        raise ValueError("mutation AFTER fingerprint differs from validation target_ref")
    if approved.get("capture_kind") != "REPOSITORY_COMMIT" or approved.get("observed_object") != job.get("observed_object"):
        raise ValueError("approved-input repository object capture mismatch")
    if not isinstance(job.get("commands"), list) or not job["commands"]:
        raise ValueError("sealed commands are required")
    for command in job["commands"]:
        if set(command) != {"check_id", "argv", "cwd_scope"} or command["cwd_scope"] != "SOURCE_ROOT":
            raise ValueError("invalid sealed command")
        if not isinstance(command["argv"], list) or not all(isinstance(item, str) and item for item in command["argv"]):
            raise ValueError("invalid sealed argv")


def _projection_commands(projection: dict) -> list[dict]:
    plan = projection.get("validation", {}).get("checks")
    if not isinstance(plan, list):
        raise ValueError("Projection validation_plan is absent")
    by_id = {item.get("check_id"): item for item in plan if isinstance(item, dict)}
    commands = []
    for check_id, argv in APPROVED_COMMANDS:
        item = by_id.get(check_id)
        if item is None or item.get("argv") != argv or item.get("cwd_scope") != "SOURCE_ROOT":
            raise ValueError(f"Projection does not bind approved command {check_id}")
        commands.append({"check_id": check_id, "argv": argv, "cwd_scope": "SOURCE_ROOT"})
    return commands


def seal_job(
    projection_path: Path,
    envelope_path: Path,
    repository: Path,
    workspace: Path,
    execution_id: str,
    approved_input_capture_path: Path,
    mutation_before_capture_path: Path,
    before_source: Path,
    execution_event_id: str,
    attempt_id: str,
    contract_digest: str,
    continuation_id: str,
    codex_session_id: str | None,
    codex_thread_id: str | None,
    predecessor_turn_id: str,
) -> tuple[dict, Path]:
    projection = _load_json(projection_path)
    declared_projection_digest = projection.get("projection_digest")
    if declared_projection_digest != digest_object(projection, "projection_digest"):
        raise ValueError("Projection digest mismatch")
    envelope_bytes = envelope_path.read_bytes()
    envelope = json.loads(envelope_bytes)
    if envelope.get("repository_publication_mode") != "NONE":
        raise ValueError("authorization envelope publication mode is not NONE")
    envelope_digest = hashlib.sha256(envelope_bytes).hexdigest()
    if projection.get("task_object_lifecycle", {}).get("authorization_envelope_digest") != envelope_digest:
        raise ValueError("Projection does not bind the authorization envelope bytes")
    repository = repository.resolve()
    workspace = workspace.resolve()
    if workspace == repository or repository in workspace.parents:
        raise ValueError("execution workspace must be outside the repository")
    resolved_codex_binding = _resolve_seal_codex_binding(
        codex_session_id=codex_session_id, codex_thread_id=codex_thread_id,
        execution_event_id=execution_event_id, attempt_id=attempt_id,
        contract_digest=contract_digest, repository=repository, workspace=workspace,
    )
    physical = projection.get("execution_object", {}).get("physical_object", {})
    binding = projection.get("decision_boundary", {}).get("repository_binding", {})
    expected_repository = binding.get("repository_id")
    if expected_repository != physical.get("object_id") or physical.get("kind") != "REPOSITORY_COMMIT":
        raise ValueError("Projection repository execution object is inconsistent")
    expected_after = repository_snapshot(repository)
    if expected_after["HEAD"] != physical.get("digest") or expected_after["branch"] != binding.get("working_branch"):
        raise ValueError("repository does not match the Projection execution object")
    approved_capture = _load_json(approved_input_capture_path)
    before_capture = _load_json(mutation_before_capture_path)
    _validate_capture_digest(approved_capture)
    _validate_capture_digest(before_capture)
    if approved_capture.get("observed_object") != physical:
        raise ValueError("approved-input capture is bound to another repository object")
    after_capture = _capture_repository_state(repository, "AFTER", "CAP_TURN_A_LOCAL_STATE_AFTER")
    before_fp = before_capture.get("observation", {}).get("state_fingerprint_sha256")
    after_fp = after_capture["observation"]["state_fingerprint_sha256"]
    if not before_fp or before_fp == after_fp:
        raise ValueError("completed mutation formal BEFORE fingerprint equals formal AFTER fingerprint")
    diff_capture = _local_diff_capture(repository, before_source.resolve(), before_fp, after_fp)
    allowed_paths = [item["statement"] for item in projection["decision_boundary"]["boundary_obligations"] if item.get("kind") == "ALLOW_PATH"]
    changed_paths = diff_capture["observation"]["changed_paths"]
    if any(not _path_allowed(path, allowed_paths) for path in changed_paths):
        raise ValueError("formal mutation Diff contains a path outside the Projection boundary")
    targeted_capture = _capture_current_test(repository, after_fp)
    job = {
        "artifact_type": JOB_TYPE,
        "version": 1,
        "execution_id": execution_id,
        "projection_digest": declared_projection_digest,
        "execution_authorization_envelope_digest": envelope_digest,
        "repository": str(repository),
        "execution_workspace": str(workspace),
        "observed_object": {
            "kind": physical["kind"],
            "object_id": physical["object_id"],
            "digest": physical["digest"],
        },
        "expected_before": expected_after,
        "formal_target_ref": after_fp,
        "turn_a_provenance": {
            "approved_input_capture": approved_capture,
            "mutation_before_capture": before_capture,
            "mutation_after_capture": after_capture,
            "mutation_diff_capture": diff_capture,
            "targeted_validation_capture": targeted_capture,
            "allowed_changed_paths": allowed_paths,
        },
        "commands": _projection_commands(projection),
        "repository_publication_mode": "NONE",
        "execution_event_id": execution_event_id,
        "attempt_id": attempt_id,
        "continuation_binding": {
            "contract_digest": contract_digest,
            "continuation_id": continuation_id,
            "codex_session_id": resolved_codex_binding["codex_session_id"],
            "codex_thread_id": resolved_codex_binding["codex_thread_id"],
            "predecessor_turn_id": predecessor_turn_id,
            "allowed_resume_mode": ALLOWED_RESUME_MODE,
            "binding_mode": resolved_codex_binding["binding_mode"],
            "execution_material_sha256": contract_digest,
            "codex_runtime_identity": resolved_codex_binding["codex_runtime_identity"],
            "initial_process_binding": resolved_codex_binding["initial_process_binding"],
        },
    }
    job["job_digest"] = digest_object(job, "job_digest")
    validate_job(job)
    verify_turn_a_diff(job)
    job_path = workspace / "job.json"
    if job_path.exists():
        raise FileExistsError(f"execution workspace is already sealed: {job_path}")
    _atomic_json(job_path, job)
    continuation = continuation_artifact(job)
    _atomic_json(workspace / "continuation.json", continuation)
    return job, job_path


def continuation_artifact(job: dict) -> dict:
    """Create the immutable, job-bound continuation transport description."""
    validate_job(job)
    binding = job["continuation_binding"]
    artifact = {
        "artifact_type": CONTINUATION_TYPE,
        "version": 1,
        "execution_event_id": job["execution_event_id"],
        "attempt_id": job["attempt_id"],
        "execution_id": job["execution_id"],
        "job_digest": job["job_digest"],
        **binding,
    }
    artifact["continuation_digest"] = digest_object(artifact, "continuation_digest")
    return artifact


def _capture(command: dict, repository: Path, formal_target_ref: str, observed_object: dict, ordinal: int) -> dict:
    started = time.perf_counter()
    completed = _run_bytes(command["argv"], repository, check=False)
    elapsed = time.perf_counter() - started
    stdout, stderr = completed.stdout, completed.stderr
    capture = {
        "capture_id": f"P0_MACHINE_CAPTURE_{ordinal:02d}",
        "tool": TOOL,
        "capture_kind": "TEST_COMMAND",
        "command": shlex.join(command["argv"]),
        "exit_code": completed.returncode,
        "stdout": stdout.decode("utf-8", "replace"),
        "stderr": stderr.decode("utf-8", "replace"),
        "stdout_bytes_base64": base64.b64encode(stdout).decode("ascii"),
        "stderr_bytes_base64": base64.b64encode(stderr).decode("ascii"),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "observed_object": observed_object,
        "observation": {
            "argv": command["argv"],
            "cwd_scope": command["cwd_scope"],
            "target_ref": formal_target_ref,
        },
        "subject_type": "VALIDATION_CHECK",
        "subject_id": command["check_id"],
        "elapsed_seconds": elapsed,
    }
    capture["capture_sha256"] = digest_object(capture, "capture_sha256")
    return capture


def execute_job(job: dict, expected_digest: str | None = None) -> dict:
    validate_job(job, expected_digest)
    repository = Path(job["repository"])
    observed_before = repository_snapshot(repository)
    captures: list[dict] = []
    execution_error = None
    if observed_before != job["expected_before"]:
        result = "BEFORE_MISMATCH"
        observed_after = observed_before
    else:
        try:
            for ordinal, command in enumerate(job["commands"], 1):
                captures.append(
                    _capture(command, repository, job["formal_target_ref"], job["observed_object"], ordinal)
                )
        except Exception as exc:  # preserve a truthful incomplete result; never repair
            execution_error = f"{type(exc).__name__}: {exc}"
        observed_after = repository_snapshot(repository)
        if observed_after != observed_before:
            result = "INVALIDATED_BY_SOURCE_DRIFT"
        elif execution_error is not None or len(captures) != len(job["commands"]):
            result = "INCOMPLETE"
        elif any(capture["exit_code"] != 0 for capture in captures):
            result = "FAILED"
        else:
            result = "PASSED"
    evidence = {
        "artifact_type": EVIDENCE_TYPE,
        "version": 1,
        "execution_id": job["execution_id"],
        "projection_digest": job["projection_digest"],
        "execution_authorization_envelope_digest": job["execution_authorization_envelope_digest"],
        "job_digest": job["job_digest"],
        "observed_object": job["observed_object"],
        "before": observed_before,
        "raw_captures": captures,
        "after": observed_after,
        "source_drift": observed_after != observed_before,
        "result": result,
        "execution_error": execution_error,
    }
    evidence["mechanical_evidence_digest"] = digest_object(evidence, "mechanical_evidence_digest")
    return evidence


def _notify_best_effort(result: str, evidence_path: Path) -> None:
    message = f"Joyflow mechanical continuation {result}: {evidence_path}"
    try:
        if os.name == "nt":
            subprocess.run(
                ["msg.exe", "*", message], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=5, check=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        elif sys.platform == "darwin":
            escaped = message.replace("\\", "\\\\").replace('"', '\\"')
            subprocess.run(
                ["osascript", "-e", f'display notification "{escaped}" with title "Joyflow"'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False,
            )
    except Exception:
        pass


def worker(job_path: Path, expected_digest: str) -> int:
    job = _load_json(job_path)
    workspace = Path(job["execution_workspace"])
    evidence = execute_job(job, expected_digest)
    evidence_path = workspace / "evidence.json"
    _atomic_json(evidence_path, evidence)
    return 0


def validate_consumable_evidence(evidence: dict, job: dict) -> None:
    """Validate raw Machine truth without turning validation failure into infrastructure failure."""
    validate_job(job)
    if evidence.get("artifact_type") != EVIDENCE_TYPE or evidence.get("version") != 1:
        raise ValueError("invalid mechanical Evidence type")
    if evidence.get("mechanical_evidence_digest") != digest_object(evidence, "mechanical_evidence_digest"):
        raise ValueError("mechanical Evidence digest mismatch")
    for key in ("execution_id", "projection_digest", "execution_authorization_envelope_digest", "job_digest", "observed_object"):
        if evidence.get(key) != job.get(key):
            raise ValueError(f"mechanical Evidence {key} binding mismatch")
    if evidence.get("result") not in {"PASSED", "FAILED", "INCOMPLETE", "BEFORE_MISMATCH", "INVALIDATED_BY_SOURCE_DRIFT"}:
        raise ValueError("invalid mechanical Evidence result")
    captures = evidence.get("raw_captures")
    if not isinstance(captures, list):
        raise ValueError("invalid mechanical Evidence captures")
    before, after = evidence.get("before"), evidence.get("after")
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise ValueError("invalid mechanical Evidence repository snapshots")
    if evidence.get("source_drift") is not (after != before):
        raise ValueError("mechanical Evidence source-drift decision mismatch")
    if evidence["result"] == "BEFORE_MISMATCH" and (captures or before == job["expected_before"]):
        raise ValueError("invalid BEFORE_MISMATCH Evidence")
    if evidence["result"] == "INVALIDATED_BY_SOURCE_DRIFT" and after == before:
        raise ValueError("invalid source-drift Evidence")
    if evidence["result"] in {"PASSED", "FAILED"} and len(captures) != len(job["commands"]):
        raise ValueError("complete mechanical result lacks sealed captures")
    for capture, command in zip(captures, job["commands"]):
        if (capture.get("subject_id") != command["check_id"] or
                capture.get("observation", {}).get("argv") != command["argv"] or
                capture.get("command") != shlex.join(command["argv"]) or
                capture.get("capture_sha256") != digest_object(capture, "capture_sha256")):
            raise ValueError("mechanical capture differs from sealed argv")
        elapsed = capture.get("elapsed_seconds")
        if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool) or elapsed < 0:
            raise ValueError("mechanical capture lacks nonnegative elapsed_seconds")
    exit_codes = [capture.get("exit_code") for capture in captures]
    if evidence["result"] == "PASSED" and any(code != 0 for code in exit_codes):
        raise ValueError("PASSED mechanical Evidence contains a failed command")
    if evidence["result"] == "FAILED" and not any(code != 0 for code in exit_codes):
        raise ValueError("FAILED mechanical Evidence lacks a failed command")


def _completion_artifact(job: dict, evidence_path: Path) -> dict:
    evidence_bytes = evidence_path.read_bytes()
    evidence = json.loads(evidence_bytes)
    validate_consumable_evidence(evidence, job)
    artifact = {
        "artifact_type": COMPLETION_TYPE, "version": 1,
        "terminal_semantics": RESULT_AVAILABLE,
        "execution_event_id": job["execution_event_id"], "attempt_id": job["attempt_id"],
        "execution_id": job["execution_id"], "job_digest": job["job_digest"],
        "projection_digest": job["projection_digest"], "result": evidence["result"],
        "evidence_file": evidence_path.name,
        "evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
    }
    artifact["terminal_artifact_digest"] = digest_object(artifact, "terminal_artifact_digest")
    return artifact


def _failure_artifact(job: dict, stage: str, worker_exit_code: int | None, error: BaseException | None) -> dict:
    evidence_exists = (Path(job["execution_workspace"]) / "evidence.json").exists()
    artifact = {
        "artifact_type": FAILURE_TYPE, "version": 1,
        "terminal_semantics": MACHINE_INFRASTRUCTURE_FAILED,
        "execution_event_id": job["execution_event_id"], "attempt_id": job["attempt_id"],
        "execution_id": job["execution_id"], "job_digest": job["job_digest"],
        "failure_stage": stage, "worker_exit_code": worker_exit_code,
        "exception_type": type(error).__name__ if error is not None else None,
        "exception_message": str(error) if error is not None else None,
        "evidence_exists": evidence_exists,
        "evidence_published": evidence_exists, "completed_published": False,
    }
    artifact["terminal_artifact_digest"] = digest_object(artifact, "terminal_artifact_digest")
    return artifact


def validate_terminal_artifact(terminal: dict, job: dict) -> None:
    validate_job(job)
    if terminal.get("artifact_type") not in {COMPLETION_TYPE, FAILURE_TYPE}:
        raise ValueError("invalid terminal artifact type")
    if terminal.get("terminal_artifact_digest") != digest_object(terminal, "terminal_artifact_digest"):
        raise ValueError("terminal artifact digest mismatch")
    for key in ("execution_event_id", "attempt_id", "execution_id", "job_digest"):
        if terminal.get(key) != job.get(key):
            raise ValueError(f"terminal artifact {key} binding mismatch")
    expected = RESULT_AVAILABLE if terminal["artifact_type"] == COMPLETION_TYPE else MACHINE_INFRASTRUCTURE_FAILED
    if terminal.get("terminal_semantics") != expected:
        raise ValueError("terminal artifact semantics mismatch")


def _terminal_from_workspace(workspace: Path) -> tuple[Path, dict]:
    paths = [workspace / "completed.json", workspace / "failed.json"]
    existing = [path for path in paths if path.exists()]
    if len(existing) != 1:
        raise ValueError("exactly one terminal artifact is required")
    return existing[0], _load_json(existing[0])


def _serve_lifecycle_event(
    listener: socket.socket, coordinate: dict, request_type: str,
    execution_event_id: str, attempt_id: str, ready: threading.Event,
    event_holder: dict, connected: threading.Event, errors: list[str],
) -> None:
    try:
        connection, _ = listener.accept()
        with connection:
            request = _recv_json_line(connection)
            expected = _channel_request(coordinate, request_type, execution_event_id, attempt_id)
            if request != expected:
                raise ValueError(f"invalid {request_type} lifecycle request")
            connected.set()
            ready.wait()
            event = event_holder.get("event")
            if not isinstance(event, dict):
                raise RuntimeError(f"{request_type} event became ready without evidence")
            connection.sendall(canonical_bytes(event) + b"\n")
    except OSError as exc:
        # Closing an unused one-shot listener is the valid artifact-fast-path case.
        if connected.is_set():
            errors.append(f"{request_type}: {type(exc).__name__}: {exc}")
    except BaseException as exc:
        errors.append(f"{request_type}: {type(exc).__name__}: {exc}")


def _spawn_initial_codex(
    argv: list[str], repository: Path, workspace: Path, prompt_bytes: bytes, env: dict[str, str],
) -> tuple[subprocess.Popen, object]:
    stderr_stream = (workspace / "initial-stderr.log").open("xb")
    try:
        process = subprocess.Popen(
            argv, cwd=repository, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=stderr_stream, close_fds=True,
        )
        process.stdin.write(prompt_bytes)
        process.stdin.close()
        return process, stderr_stream
    except BaseException:
        stderr_stream.close()
        raise


def initial_launch(
    prompt_file: Path, repository: Path, workspace: Path,
    execution_event_id: str, attempt_id: str,
) -> dict:
    repository = repository.resolve()
    if Path(_git_text(repository, "rev-parse", "--show-toplevel")).resolve() != repository:
        raise ValueError("SOURCE_ROOT is not the exact Git worktree root")
    workspace = workspace.resolve()
    if workspace == repository or repository in workspace.parents:
        raise ValueError("LIFECYCLE_WORKSPACE must be outside SOURCE_ROOT")
    workspace.mkdir(parents=True, exist_ok=True)

    ownership = {
        "artifact_type": "P0_INITIAL_LAUNCH_CLAIM",
        "version": 1,
        "execution_event_id": execution_event_id,
        "attempt_id": attempt_id,
        "lifecycle_workspace": str(workspace),
    }
    ownership["artifact_digest"] = _artifact_digest(ownership)
    try:
        _exclusive_json(workspace / INITIAL_LAUNCH_CLAIM_ARTIFACT, ownership)
    except BaseException:
        raise RuntimeError("STOP_DUPLICATE_INITIAL_LAUNCH") from None

    # Contractual READ_ONCE: these exact bytes are hashed and supplied to the child.
    execution_material = prompt_file.read_bytes()
    execution_material_sha256 = hashlib.sha256(execution_material).hexdigest()
    runtime_identity = _codex_runtime_identity()
    binding_listener, binding_channel = _new_lifecycle_listener()
    try:
        terminal_listener, terminal_channel = _new_lifecycle_listener()
    except BaseException:
        binding_listener.close()
        raise

    binding_ready = threading.Event()
    terminal_ready = threading.Event()
    binding_connected = threading.Event()
    terminal_connected = threading.Event()
    binding_holder: dict[str, object] = {}
    terminal_holder: dict[str, object] = {}
    channel_errors: list[str] = []
    binding_thread = threading.Thread(
        target=_serve_lifecycle_event,
        args=(binding_listener, binding_channel, "WAIT_BINDING_READY", execution_event_id,
              attempt_id, binding_ready, binding_holder, binding_connected, channel_errors),
        name="joyflow-binding-ready", daemon=True,
    )
    terminal_thread = threading.Thread(
        target=_serve_lifecycle_event,
        args=(terminal_listener, terminal_channel, "WAIT_INITIAL_PROCESS_TERMINAL", execution_event_id,
              attempt_id, terminal_ready, terminal_holder, terminal_connected, channel_errors),
        name="joyflow-initial-terminal-ready", daemon=True,
    )
    binding_thread.start()
    terminal_thread.start()

    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    env.update({
        "JOYFLOW_CONTINUATION_MODE": CLI_OWNED_PRODUCTION,
        "JOYFLOW_SOURCE_ROOT": str(repository),
        "JOYFLOW_LIFECYCLE_WORKSPACE": str(workspace),
        "JOYFLOW_EXECUTION_EVENT_ID": execution_event_id,
        "JOYFLOW_ATTEMPT_ID": attempt_id,
        "JOYFLOW_CONTRACT_DIGEST": execution_material_sha256,
        "JOYFLOW_BINDING_CHANNEL": json.dumps(binding_channel, sort_keys=True),
    })
    initial_last_message = workspace / "initial-last-message.txt"
    initial_argv = [
        runtime_identity["resolved_codex_executable"], "exec", "--json",
        "--output-last-message", str(initial_last_message), "-",
    ]
    process = None
    stderr_stream = None
    thread_ids: list[str] = []
    turn_completed_observed = False
    initial_events = workspace / "initial-events.jsonl"
    try:
        process, stderr_stream = _spawn_initial_codex(
            initial_argv, repository, workspace, execution_material, env,
        )
        with initial_events.open("xb") as events_stream:
            for raw_line in process.stdout:
                events_stream.write(raw_line)
                events_stream.flush()
                try:
                    event = json.loads(raw_line)
                except (ValueError, json.JSONDecodeError):
                    continue
                if event.get("type") == "thread.started":
                    thread_id = event.get("thread_id")
                    if thread_id not in thread_ids:
                        thread_ids.append(thread_id)
                    if len(thread_ids) == 1 and _valid_uuid(thread_id):
                        binding = {
                            "artifact_type": "P0_CODEX_SESSION_BINDING",
                            "version": 1,
                            "execution_event_id": execution_event_id,
                            "attempt_id": attempt_id,
                            "execution_material_sha256": execution_material_sha256,
                            "source_root": str(repository),
                            "lifecycle_workspace": str(workspace),
                            "initial_pid": process.pid,
                            "codex_session_id": thread_id,
                            "codex_thread_id": thread_id,
                            "codex_runtime_identity": runtime_identity,
                            "initial_process_binding": {
                                "initial_pid": process.pid,
                                "terminal_channel": terminal_channel,
                            },
                            **_runtime_artifact_fields(runtime_identity),
                        }
                        binding["artifact_digest"] = _artifact_digest(binding)
                        binding_path = workspace / SESSION_BINDING_ARTIFACT
                        if not binding_path.exists():
                            _atomic_json(binding_path, binding)
                            binding_holder["event"] = {
                                "event_type": "BINDING_READY",
                                "execution_event_id": execution_event_id,
                                "attempt_id": attempt_id,
                                "nonce": binding_channel["nonce"],
                                "artifact_digest": binding["artifact_digest"],
                            }
                            binding_ready.set()
                elif event.get("type") == "turn.completed":
                    turn_completed_observed = True
        initial_exit_code = process.wait()
    finally:
        if stderr_stream is not None:
            stderr_stream.close()

    frozen_thread_id = thread_ids[0] if len(thread_ids) == 1 and _valid_uuid(thread_ids[0]) else None
    terminal = {
        "artifact_type": "P0_INITIAL_PROCESS_TERMINAL",
        "version": 1,
        "execution_event_id": execution_event_id,
        "attempt_id": attempt_id,
        "execution_material_sha256": execution_material_sha256,
        "source_root": str(repository),
        "lifecycle_workspace": str(workspace),
        "initial_pid": process.pid,
        "frozen_thread_id": frozen_thread_id,
        "initial_exit_code": initial_exit_code,
        "initial_process_terminal_at": time.time(),
        "initial_turn_completed_observed": turn_completed_observed,
        "codex_runtime_identity": runtime_identity,
        **_runtime_artifact_fields(runtime_identity),
    }
    terminal["artifact_digest"] = _artifact_digest(terminal)
    _atomic_json(workspace / INITIAL_TERMINAL_ARTIFACT, terminal)
    terminal_holder["event"] = {
        "event_type": "INITIAL_PROCESS_TERMINAL_READY",
        "execution_event_id": execution_event_id,
        "attempt_id": attempt_id,
        "nonce": terminal_channel["nonce"],
        "artifact_digest": terminal["artifact_digest"],
    }
    terminal_ready.set()
    if binding_connected.is_set():
        binding_thread.join()
    if terminal_connected.is_set():
        terminal_thread.join()
    binding_listener.close()
    terminal_listener.close()
    if channel_errors:
        raise RuntimeError("; ".join(channel_errors))
    result = {
        "launch": "TERMINAL",
        "execution_event_id": execution_event_id,
        "attempt_id": attempt_id,
        "execution_material_sha256": execution_material_sha256,
        "initial_pid": process.pid,
        "initial_exit_code": initial_exit_code,
        "frozen_thread_id": frozen_thread_id,
        "initial_turn_completed_observed": turn_completed_observed,
        "initial_terminal_artifact_digest": terminal["artifact_digest"],
    }
    if frozen_thread_id is None:
        raise RuntimeError("initial Codex did not report one authoritative thread")
    if initial_exit_code != 0:
        raise RuntimeError("initial Codex process failed")
    if not turn_completed_observed:
        raise RuntimeError("initial Codex turn completion was not observed")
    return result


def _valid_uuid(value: object) -> bool:
    try:
        return isinstance(value, str) and str(uuid.UUID(value)) == value.lower()
    except (TypeError, ValueError):
        return False


def _continuation_payload(job: dict, terminal: dict) -> str:
    binding = job["continuation_binding"]
    return "\n".join([
        "继续 SAME approved execution event。先执行下列 mechanical acknowledgement，然后消费 terminal artifact；",
        "仅当下一 material action 仍由 SAME contract 授权时继续，否则 STOP_CONTRACT_BOUNDARY_REACHED。",
        f"execution_event_id={job['execution_event_id']}", f"contract_digest={binding['contract_digest']}",
        f"continuation_id={binding['continuation_id']}", f"attempt_id={job['attempt_id']}",
        f"codex_session_id={binding['codex_session_id']}",
        f"codex_thread_id={binding['codex_thread_id']}",
        f"predecessor_turn_id={binding['predecessor_turn_id']}",
        f"job_digest={job['job_digest']}",
        f"terminal_state={terminal['terminal_semantics']}",
        f"terminal_artifact_digest={terminal['terminal_artifact_digest']}",
        f"execution_workspace={job['execution_workspace']}",
        "ack_command=" + shlex.join([
            sys.executable, "-B", str(Path(__file__).resolve()), "ack", "--job",
            str((Path(job["execution_workspace"]) / "job.json").resolve()),
            "--terminal-artifact-digest", terminal["terminal_artifact_digest"],
            "--codex-session-id", binding["codex_session_id"],
            "--codex-thread-id", binding["codex_thread_id"],
        ]),
    ])


def _continuation_argv(job: dict, last_message_path: Path) -> list[str]:
    binding = job["continuation_binding"]
    executable = "codex"
    if binding["binding_mode"] == CLI_OWNED_PRODUCTION:
        executable = binding["codex_runtime_identity"]["resolved_codex_executable"]
    return [
        executable, "exec", "resume", "--json", "--output-last-message",
        str(last_message_path.resolve()), binding["codex_session_id"], "-",
    ]


def _production_resume_environment(binding: dict) -> dict[str, str]:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    if binding["binding_mode"] != CLI_OWNED_PRODUCTION:
        return env
    identity = binding["codex_runtime_identity"]
    executable = Path(identity["resolved_codex_executable"])
    if hashlib.sha256(executable.read_bytes()).hexdigest() != identity["executable_sha256"]:
        raise RuntimeError("frozen Codex executable digest changed")
    version = _run_bytes([str(executable), "--version"], Path.cwd()).stdout.decode("utf-8", "strict").strip()
    if version != identity["codex_version"]:
        raise RuntimeError("frozen Codex version changed")
    state = identity["state_root_identity"]
    for key in ("CODEX_HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA"):
        value = state.get(key)
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    return env


def _parse_continuation_events(events_path: Path) -> dict:
    reported_thread_id = None
    turn_started = False
    assistant_observed = False
    turn_completed = False
    event_count = 0
    with events_path.open("rb") as stream:
        for raw_line in stream:
            if not raw_line.strip():
                continue
            event = json.loads(raw_line)
            if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                raise ValueError("invalid continuation JSONL event")
            event_count += 1
            event_type = event["type"]
            if event_type == "thread.started":
                thread_id = event.get("thread_id")
                if not isinstance(thread_id, str) or not thread_id:
                    raise ValueError("thread.started lacks thread_id")
                if reported_thread_id is not None and reported_thread_id != thread_id:
                    raise ValueError("continuation reports multiple thread ids")
                reported_thread_id = thread_id
            elif event_type == "turn.started":
                turn_started = True
            elif event_type == "item.completed":
                item = event.get("item")
                if isinstance(item, dict) and item.get("type") == "agent_message":
                    assistant_observed = True
            elif event_type == "turn.completed":
                turn_completed = True
    return {
        "event_count": event_count,
        "reported_thread_id": reported_thread_id,
        "automatic_resume_user_turn_observed": turn_started,
        "automatic_resume_assistant_turn_observed": assistant_observed,
        "automatic_resume_turn_completed_observed": turn_completed,
    }


def _spawn_continuation(
    job: dict, payload_path: Path, argv: list[str], events_path: Path, stderr_path: Path,
) -> subprocess.Popen:
    workspace = Path(job["execution_workspace"])
    stdin = payload_path.open("rb")
    stdout = events_path.open("xb")
    stderr = stderr_path.open("xb")
    try:
        return subprocess.Popen(
            argv, stdin=stdin, stdout=stdout, stderr=stderr, close_fds=True,
            cwd=Path(job["repository"]), env=_production_resume_environment(job["continuation_binding"]),
        )
    finally:
        stdin.close(); stdout.close(); stderr.close()


def dispatch_continuation(job: dict, terminal: dict) -> str:
    validate_terminal_artifact(terminal, job)
    workspace = Path(job["execution_workspace"])
    binding = job["continuation_binding"]
    claim_path = workspace / "continuation-claim.json"
    payload_path = workspace / "continuation-payload.txt"
    events_path = workspace / "continuation-events.jsonl"
    stderr_path = workspace / "continuation-stderr.log"
    last_message_path = workspace / "continuation-last-message.txt"
    argv = _continuation_argv(job, last_message_path)
    claim = {
        "artifact_type": CLAIM_TYPE, "version": 1, "status": CLAIMED,
        "execution_event_id": job["execution_event_id"], "attempt_id": job["attempt_id"],
        "job_digest": job["job_digest"], "continuation_id": binding["continuation_id"],
        "terminal_artifact_digest": terminal["terminal_artifact_digest"],
        "codex_session_id": binding["codex_session_id"], "codex_thread_id": binding["codex_thread_id"],
        "requested_thread_id": binding["codex_thread_id"], "resume_argv": argv,
        "automatic_resume_process_executed": False, "process_id": None, "process_exit_code": None,
        "events_file": events_path.name, "stderr_file": stderr_path.name,
        "last_message_file": last_message_path.name, "event_count": 0,
        "reported_thread_id": None, "same_thread_confirmed": False,
        "automatic_resume_user_turn_observed": False,
        "automatic_resume_assistant_turn_observed": False,
        "automatic_resume_turn_completed_observed": False,
        "stop_reason": None,
    }
    claim["claim_digest"] = digest_object(claim, "claim_digest")
    _exclusive_json(claim_path, claim)
    payload_path.write_text(_continuation_payload(job, terminal), encoding="utf-8", newline="\n")
    claim["status"] = DISPATCH_UNKNOWN
    claim["claim_digest"] = digest_object(claim, "claim_digest")
    _atomic_json(claim_path, claim)
    try:
        process = _spawn_continuation(job, payload_path, argv, events_path, stderr_path)
        claim["automatic_resume_process_executed"] = True
        claim["process_id"] = process.pid
        claim["claim_digest"] = digest_object(claim, "claim_digest")
        _atomic_json(claim_path, claim)
        process.wait()
        claim["process_exit_code"] = process.returncode
        parsed = _parse_continuation_events(events_path)
        claim.update(parsed)
        claim["same_thread_confirmed"] = (
            parsed["reported_thread_id"] == binding["codex_thread_id"]
        )
        last_message_observed = last_message_path.is_file() and last_message_path.stat().st_size > 0
        claim["automatic_resume_assistant_turn_observed"] = (
            parsed["automatic_resume_assistant_turn_observed"] and last_message_observed
        )
        if parsed["reported_thread_id"] is not None and not claim["same_thread_confirmed"]:
            claim["stop_reason"] = STOP_CONTINUATION_WRONG_THREAD
        elif (
            process.returncode == 0 and parsed["event_count"] > 0 and
            claim["same_thread_confirmed"] and
            claim["automatic_resume_user_turn_observed"] and
            claim["automatic_resume_assistant_turn_observed"] and
            claim["automatic_resume_turn_completed_observed"]
        ):
            claim["status"] = DISPATCH_CONFIRMED
    except BaseException as exc:
        claim["dispatch_error"] = f"{type(exc).__name__}: {exc}"
    claim["claim_digest"] = digest_object(claim, "claim_digest")
    _atomic_json(claim_path, claim)
    return claim["stop_reason"] or claim["status"]


def acknowledge_continuation(
    job_path: Path, terminal_artifact_digest: str, codex_session_id: str, codex_thread_id: str,
) -> dict:
    job = _load_json(job_path)
    validate_job(job)
    workspace = Path(job["execution_workspace"])
    _, terminal = _terminal_from_workspace(workspace)
    validate_terminal_artifact(terminal, job)
    if terminal["terminal_artifact_digest"] != terminal_artifact_digest:
        raise ValueError("continuation terminal binding mismatch")
    binding = job["continuation_binding"]
    if codex_session_id != binding["codex_session_id"] or codex_thread_id != binding["codex_thread_id"]:
        raise ValueError("continuation Codex identity mismatch")
    claim_path = workspace / "continuation-claim.json"
    claim = _load_json(claim_path)
    if claim.get("claim_digest") != digest_object(claim, "claim_digest"):
        raise ValueError("continuation claim digest mismatch")
    expected = job["continuation_binding"]
    for key, value in (("execution_event_id", job["execution_event_id"]), ("attempt_id", job["attempt_id"]),
                       ("job_digest", job["job_digest"]), ("continuation_id", expected["continuation_id"]),
                       ("terminal_artifact_digest", terminal_artifact_digest),
                       ("codex_session_id", expected["codex_session_id"]), ("codex_thread_id", expected["codex_thread_id"])):
        if claim.get(key) != value:
            raise ValueError(f"continuation claim {key} mismatch")
    if claim.get("status") not in {DISPATCH_UNKNOWN, DISPATCH_CONFIRMED}:
        raise ValueError("continuation dispatch was not attempted")
    manual = {
        "artifact_type": "P0_CONTINUATION_MANUAL_ACKNOWLEDGEMENT", "version": 1,
        "status": MANUAL_ACKNOWLEDGED,
        "execution_event_id": job["execution_event_id"], "attempt_id": job["attempt_id"],
        "job_digest": job["job_digest"], "continuation_id": expected["continuation_id"],
        "terminal_artifact_digest": terminal_artifact_digest,
        "codex_session_id": codex_session_id, "codex_thread_id": codex_thread_id,
        "automatic_dispatch_status_at_ack": claim["status"],
    }
    manual["manual_ack_digest"] = digest_object(manual, "manual_ack_digest")
    _exclusive_json(workspace / "continuation-manual-ack.json", manual)
    return manual


def authorize_in_contract_repair(job: dict, next_attempt_id: str, changed_paths: list[str], contract_digest: str) -> str:
    validate_job(job)
    allowed = job["turn_a_provenance"]["allowed_changed_paths"]
    if (contract_digest != job["continuation_binding"]["contract_digest"] or
            not next_attempt_id or next_attempt_id == job["attempt_id"] or
            any(not _path_allowed(path, allowed) for path in changed_paths)):
        return "STOP_CONTRACT_BOUNDARY_REACHED"
    return "CONTINUE_SAME_EXECUTION_EVENT"


def _progress_binding(job: dict, monitor: ProgressMonitor) -> dict:
    return {
        "execution_event_id": job["execution_event_id"],
        "attempt_id": job["attempt_id"],
        "job_digest": job["job_digest"],
        "command_index": TEST_COMMAND_INDEX,
        "liveness_bound_source": monitor.bound_source,
        "liveness_bound_value": monitor.bound_value,
    }


def _runner_liveness_binding(repository: Path) -> tuple[str, int]:
    runner_module = _load_named_module(
        "joyflow_progress_test_runner", repository / "tools" / "run_test_suite.py"
    )
    return runner_module.LIVENESS_BOUND_SOURCE, runner_module.EXECUTION_UNIT_TIMEOUT_SECONDS


def _serve_progress_connection(listener: socket.socket, monitor: ProgressMonitor) -> None:
    connection, _ = listener.accept()
    with connection:
        connection.setblocking(True)
        raw = b""
        while not raw.endswith(b"\n"):
            chunk = connection.recv(65536)
            if not chunk:
                break
            raw += chunk
        try:
            event = json.loads(raw)
        except (ValueError, json.JSONDecodeError):
            event = None
        response: dict[str, object] = {"accepted": False}
        if isinstance(event, dict):
            if event.get("event_type") == "sequence_request":
                next_sequence = monitor.next_sequence(event)
                if next_sequence is not None:
                    response = {"accepted": True, "next_sequence": next_sequence}
            else:
                response = {"accepted": monitor.accept(event)}
        connection.sendall(canonical_bytes(response) + b"\n")


def _validate_initial_process_terminal(job: dict, terminal: dict) -> None:
    _validate_artifact_digest(terminal, "P0_INITIAL_PROCESS_TERMINAL")
    binding = job["continuation_binding"]
    initial = binding["initial_process_binding"]
    expected = {
        "execution_event_id": job["execution_event_id"],
        "attempt_id": job["attempt_id"],
        "execution_material_sha256": binding["execution_material_sha256"],
        "source_root": str(Path(job["repository"]).resolve()),
        "lifecycle_workspace": str(Path(job["execution_workspace"]).resolve()),
        "initial_pid": initial["initial_pid"],
        "frozen_thread_id": binding["codex_thread_id"],
        "codex_runtime_identity": binding["codex_runtime_identity"],
        **_runtime_artifact_fields(binding["codex_runtime_identity"]),
    }
    for key, value in expected.items():
        if terminal.get(key) != value:
            raise ValueError(f"initial process terminal {key} mismatch")
    if terminal.get("initial_exit_code") != 0 or terminal.get("initial_turn_completed_observed") is not True:
        raise ValueError("initial process terminal does not permit continuation")


def _initial_terminal_fast_path(job: dict) -> bool:
    if job["continuation_binding"]["binding_mode"] != CLI_OWNED_PRODUCTION:
        return True
    path = Path(job["execution_workspace"]) / INITIAL_TERMINAL_ARTIFACT
    if not path.is_file():
        return False
    _validate_initial_process_terminal(job, _load_json(path))
    return True


def _connect_initial_terminal_channel(job: dict) -> socket.socket:
    binding = job["continuation_binding"]
    coordinate = binding["initial_process_binding"]["terminal_channel"]
    connection = socket.create_connection((coordinate["host"], coordinate["port"]))
    request = _channel_request(
        coordinate, "WAIT_INITIAL_PROCESS_TERMINAL", job["execution_event_id"], job["attempt_id"],
    )
    connection.sendall(canonical_bytes(request) + b"\n")
    connection.setblocking(False)
    return connection


def _await_initial_process_terminal_gate(job: dict) -> None:
    if job["continuation_binding"]["binding_mode"] != CLI_OWNED_PRODUCTION:
        return
    if _initial_terminal_fast_path(job):
        return
    try:
        connection = _connect_initial_terminal_channel(job)
    except OSError:
        # One bounded revalidation closes the artifact-publication/listener-close race.
        # It is not a periodic polling loop.
        if _initial_terminal_fast_path(job):
            return
        raise RuntimeError("initial process terminal gate is unavailable") from None
    try:
        _consume_initial_terminal_wakeup(job, connection)
    finally:
        connection.close()


def _consume_initial_terminal_wakeup(job: dict, connection: socket.socket) -> None:
    connection.setblocking(True)
    event = _recv_json_line(connection)
    coordinate = job["continuation_binding"]["initial_process_binding"]["terminal_channel"]
    expected = {
        "event_type": "INITIAL_PROCESS_TERMINAL_READY",
        "execution_event_id": job["execution_event_id"],
        "attempt_id": job["attempt_id"],
        "nonce": coordinate["nonce"],
    }
    for key, value in expected.items():
        if event.get(key) != value:
            raise ValueError(f"initial terminal wake {key} mismatch")
    terminal = _load_json(Path(job["execution_workspace"]) / INITIAL_TERMINAL_ARTIFACT)
    if event.get("artifact_digest") != terminal.get("artifact_digest"):
        raise ValueError("initial terminal wake artifact digest mismatch")
    _validate_initial_process_terminal(job, terminal)


def _start_worker(job: dict, job_path: Path, listener: socket.socket, monitor_holder: list[ProgressMonitor]) -> subprocess.Popen:
    host, port = listener.getsockname()
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    bound_source, bound_value = _runner_liveness_binding(Path(job["repository"]))
    binding = {
        "execution_event_id": job["execution_event_id"],
        "attempt_id": job["attempt_id"],
        "job_digest": job["job_digest"],
        "command_index": TEST_COMMAND_INDEX,
        "liveness_bound_source": bound_source,
        "liveness_bound_value": bound_value,
    }
    env.update({
        "JOYFLOW_PROGRESS_HOST": str(host),
        "JOYFLOW_PROGRESS_PORT": str(port),
        "JOYFLOW_PROGRESS_BINDING": json.dumps(binding, sort_keys=True),
    })
    process = subprocess.Popen([
        sys.executable, "-B", str(Path(__file__).resolve()), "worker", "--job",
        str(job_path.resolve()), "--job-digest", job["job_digest"],
    ], cwd=Path(job["repository"]), env=env)
    monitor_holder.append(ProgressMonitor(
        job, os.getpid(), process.pid, bound_binding=(bound_source, bound_value),
    ))
    return process


def _wait_for_worker_events(job: dict, job_path: Path) -> tuple[int, ProgressMonitor]:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    listener.setblocking(False)
    wake_reader, wake_writer = socket.socketpair()
    monitor_holder: list[ProgressMonitor] = []
    try:
        process = _start_worker(job, job_path, listener, monitor_holder)
    except BaseException:
        listener.close()
        wake_reader.close()
        wake_writer.close()
        raise
    monitor = monitor_holder[0]
    worker_result: list[int] = []

    def wait_for_terminal() -> None:
        worker_result.append(process.wait())
        try:
            wake_writer.send(b"1")
        except OSError:
            pass

    waiter = threading.Thread(target=wait_for_terminal, name="joyflow-worker-terminal-wait", daemon=True)
    waiter.start()
    selector = selectors.DefaultSelector()
    selector.register(listener, selectors.EVENT_READ, "progress")
    selector.register(wake_reader, selectors.EVENT_READ, "terminal")
    try:
        terminal_observed = False
        while not terminal_observed:
            timeout = None if monitor.deadline is None else max(0.0, monitor.deadline - time.monotonic())
            events = selector.select(timeout)
            if not events:
                monitor.expire(process)
                continue
            for key, _ in events:
                if key.data == "progress":
                    _serve_progress_connection(listener, monitor)
                elif key.data == "terminal":
                    wake_reader.recv(4096)
                    terminal_observed = True
                    monitor.deadline = None
    finally:
        selector.close()
        listener.close()
        wake_reader.close()
        wake_writer.close()
    waiter.join()
    return worker_result[0], monitor


def supervisor(job_path: Path, expected_digest: str) -> int:
    job = _load_json(job_path)
    validate_job(job, expected_digest)
    workspace = Path(job["execution_workspace"])
    _exclusive_json(workspace / "supervisor-claim.json", {
        "execution_event_id": job["execution_event_id"], "attempt_id": job["attempt_id"],
        "execution_id": job["execution_id"], "job_digest": job["job_digest"],
    })
    worker_exit = None
    error = None
    monitor = None
    try:
        worker_exit, monitor = _wait_for_worker_events(job, job_path)
        terminal = _completion_artifact(job, workspace / "evidence.json")
        terminal_path = workspace / "completed.json"
    except BaseException as exc:
        error = exc
        terminal = _failure_artifact(job, "WORKER_OR_EVIDENCE", worker_exit, error)
        terminal_path = workspace / "failed.json"
    if (workspace / "completed.json").exists() or (workspace / "failed.json").exists():
        raise RuntimeError("terminal artifact already exists")
    _exclusive_json(terminal_path, terminal)
    if monitor is not None:
        monitor.publish_terminal(terminal["terminal_semantics"])
    _notify_best_effort(terminal["terminal_semantics"], terminal_path)
    _await_initial_process_terminal_gate(job)
    if monitor is not None:
        monitor.publish_continuation(CONTINUATION_DISPATCHING)
    dispatch_result = dispatch_continuation(job, terminal)
    if monitor is not None:
        monitor.publish_continuation(
            DISPATCH_CONFIRMED if dispatch_result == DISPATCH_CONFIRMED else DISPATCH_UNKNOWN
        )
    return 0 if terminal["artifact_type"] == COMPLETION_TYPE else 1


def consume_completed_evidence(workspace: Path, projection_digest: str, job_digest: str) -> dict:
    """Fail-closed Turn B intake; it validates Evidence but does not create a Return."""
    completion = _load_json(workspace / "completed.json")
    evidence_path = workspace / completion.get("evidence_file", "")
    evidence_bytes = evidence_path.read_bytes()
    evidence = json.loads(evidence_bytes)
    job = _load_json(workspace / "job.json")
    validate_job(job, job_digest)
    validate_terminal_artifact(completion, job)
    if completion.get("evidence_sha256") != hashlib.sha256(evidence_bytes).hexdigest():
        raise ValueError("completion does not bind Evidence bytes")
    validate_consumable_evidence(evidence, job)
    if evidence.get("projection_digest") != projection_digest or evidence.get("job_digest") != job_digest:
        raise ValueError("completed Evidence binding mismatch")
    if completion.get("projection_digest") != projection_digest or completion.get("job_digest") != job_digest:
        raise ValueError("completion binding mismatch")
    if completion.get("result") != "PASSED" or evidence.get("result") != "PASSED" or evidence.get("source_drift") is not False:
        raise ValueError("completed Evidence is not a drift-free PASS")
    if evidence.get("before") != job["expected_before"]:
        raise ValueError("Machine candidate differs from sealed expected post-implementation candidate")
    if evidence.get("after") != evidence.get("before"):
        raise ValueError("Machine AFTER differs from Machine BEFORE")
    captures = evidence.get("raw_captures")
    if not isinstance(captures, list) or len(captures) != len(APPROVED_COMMANDS):
        raise ValueError("completed P0 Evidence does not contain all captures")
    for capture, (check_id, argv) in zip(captures, APPROVED_COMMANDS):
        elapsed = capture.get("elapsed_seconds")
        if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool) or elapsed < 0:
            raise ValueError("completed P0 capture lacks nonnegative elapsed_seconds")
        if capture.get("subject_id") != check_id or capture.get("observation", {}).get("argv") != argv:
            raise ValueError("completed P0 capture argv binding mismatch")
        if capture.get("observation", {}).get("target_ref") != job["formal_target_ref"]:
            raise ValueError("mutation AFTER fingerprint differs from validation target_ref")
        if capture.get("command") != shlex.join(argv):
            raise ValueError("completed P0 capture command binding mismatch")
        if capture.get("capture_sha256") != digest_object(capture, "capture_sha256"):
            raise ValueError("completed P0 capture digest mismatch")
    return evidence


def _direct_evidence(runtime, evidence_id: str, capture: dict) -> dict:
    claim = runtime._direct_capture_claim(capture)
    return {
        "evidence_id": evidence_id,
        "authority": "EXECUTION_EVIDENCE",
        "kind": runtime._DIRECT_KIND_BY_CAPTURE[capture["capture_kind"]],
        "ref": capture["capture_id"],
        "claim": claim,
        "claim_digest": runtime.digest(claim),
        "produced_by": "TOOL",
        "subject_type": capture["subject_type"],
        "subject_id": capture["subject_id"],
        "raw_output_ref": capture["capture_id"],
        "raw_output_sha256": capture["capture_sha256"],
    }


def _derivation(runtime, derivation_id: str, kind: str, claim: str, subject_type: str, subject_id: str, refs: list[str]) -> dict:
    return {
        "derivation_id": derivation_id,
        "authority": "EXECUTION_EVIDENCE",
        "kind": kind,
        "claim": claim,
        "claim_digest": runtime.digest(claim),
        "produced_by": "CODEX",
        "subject_type": subject_type,
        "subject_id": subject_id,
        "source_evidence_refs": refs,
    }


def construct_formal_artifacts(projection: dict, job: dict, mechanical_evidence: dict) -> tuple[dict, dict]:
    """Turn B only: fold sealed Turn-A facts and Machine facts into formal objects."""
    validate_job(job)
    if projection.get("projection_digest") != job["projection_digest"]:
        raise ValueError("formal construction Projection mismatch")
    if (mechanical_evidence.get("mechanical_evidence_digest") !=
            digest_object(mechanical_evidence, "mechanical_evidence_digest")):
        raise ValueError("mechanical Evidence digest mismatch")
    if mechanical_evidence.get("job_digest") != job["job_digest"]:
        raise ValueError("mechanical Evidence job binding mismatch")
    if mechanical_evidence.get("before") != job["expected_before"]:
        raise ValueError("Machine candidate differs from sealed expected post-implementation candidate")
    if mechanical_evidence.get("after") != mechanical_evidence.get("before") or mechanical_evidence.get("source_drift") is not False:
        raise ValueError("Machine source drift prevents formal construction")
    repository = Path(job["repository"])
    runtime = _load_runtime_module(repository)
    provenance = job["turn_a_provenance"]
    raw_captures: list[dict] = []
    evidence_rows: list[dict] = []
    derivation_rows: list[dict] = []

    def add_direct(evidence_id: str, capture: dict) -> None:
        raw_captures.append(capture)
        evidence_rows.append(_direct_evidence(runtime, evidence_id, capture))

    object_capture = _resubject_capture(
        provenance["approved_input_capture"], "CAP_TURN_B_PREFLIGHT_OBJECT",
        "TECHNICAL_PREFLIGHT", runtime._technical_preflight_subject(projection),
    )
    add_direct("EXEC_PREFLIGHT_OBJECT", object_capture)
    support_capture = _resubject_capture(
        object_capture, "CAP_TURN_B_PREFLIGHT_SOURCE", "TECHNICAL_PREFLIGHT_SOURCE", "CURRENT_OBJECT_SOURCE"
    )
    add_direct("EXEC_PREFLIGHT_SOURCE", support_capture)
    machine_by_id = {capture["subject_id"]: capture for capture in mechanical_evidence["raw_captures"]}
    preflight_check_id = TARGETED_CHECK[0] if TARGETED_CHECK[0] in {item["check_id"] for item in projection["validation"]["checks"]} else projection["validation"]["checks"][0]["check_id"]
    preflight_source = provenance["targeted_validation_capture"] if preflight_check_id == TARGETED_CHECK[0] else machine_by_id[preflight_check_id]
    preflight_test = _resubject_capture(
        preflight_source, "CAP_TURN_B_PREFLIGHT_TEST",
        "TECHNICAL_PREFLIGHT_TEST", "CURRENT_TEST_PLAN",
    )
    add_direct("EXEC_PREFLIGHT_TEST", preflight_test)
    approved_base = job["observed_object"]["digest"]
    add_direct("EXEC_LOCAL_STATE_BEFORE", _resubject_capture(
        provenance["mutation_before_capture"], "CAP_TURN_B_LOCAL_STATE_BEFORE",
        "LOCAL_REPOSITORY_SOURCE_STATE", f"{approved_base}:BEFORE",
    ))
    add_direct("EXEC_LOCAL_STATE_AFTER", _resubject_capture(
        provenance["mutation_after_capture"], "CAP_TURN_B_LOCAL_STATE_AFTER",
        "LOCAL_REPOSITORY_SOURCE_STATE", f"{approved_base}:AFTER",
    ))
    add_direct("EXEC_LOCAL_DIFF", copy.deepcopy(provenance["mutation_diff_capture"]))

    obligation_results = []
    for obligation in projection["technical_route_space"]["obligations"]:
        obligation_id = obligation["obligation_id"]
        result = {
            "obligation_id": obligation_id,
            "dimension": obligation["dimension"],
            "subject_digest": obligation["subject_binding"]["subject_digest"],
            "result": "PASS",
            "finding_summary": f"{obligation['dimension']} passed for the exact task-bound subject.",
            "evidence_refs": [f"DERIVE_{obligation_id}"],
        }
        if obligation["dimension"] == "OBJECT_IDENTITY":
            refs = ["EXEC_PREFLIGHT_OBJECT"]
        elif obligation["dimension"] in {"ACCEPTANCE_FEASIBILITY", "TEST_CONTRADICTION"}:
            refs = ["EXEC_PREFLIGHT_TEST"]
        else:
            refs = ["EXEC_PREFLIGHT_SOURCE"]
        derivation_rows.append(_derivation(
            runtime, result["evidence_refs"][0], "PREFLIGHT_OBLIGATION_DERIVATION",
            runtime._obligation_result_claim(result), "TECHNICAL_PREFLIGHT_OBLIGATION", obligation_id, refs,
        ))
        obligation_results.append(result)

    evaluations = []
    routes = projection["technical_route_space"]["candidate_routes"]
    for ordinal, route in enumerate(routes, 1):
        passed = ordinal == 1
        result = {
            "route_id": route["route_id"],
            "feasibility": "PASS" if passed else "PARTIAL",
            "evidence_refs": [f"DERIVE_ROUTE_EVAL_{ordinal}"],
            "rejection_reason": None if passed else "The route is not the minimum approved implementation path.",
        }
        derivation_rows.append(_derivation(
            runtime, result["evidence_refs"][0], "ROUTE_CANDIDATE_DERIVATION",
            runtime._candidate_evaluation_claim(result), "TECHNICAL_ROUTE_CANDIDATE", route["route_id"],
            ["EXEC_PREFLIGHT_SOURCE", "EXEC_PREFLIGHT_TEST"],
        ))
        evaluations.append(result)
    selected = {
        "source": "BRAIN_CANDIDATE",
        "route_id": routes[0]["route_id"],
        "implementation_summary": "Use the approved sealed one-shot continuation route within the exact boundary.",
        "evidence_refs": ["DERIVE_SELECTED_ROUTE"],
    }
    derivation_rows.append(_derivation(
        runtime, "DERIVE_SELECTED_ROUTE", "SELECTED_ROUTE_DERIVATION",
        runtime._selected_route_claim(selected), "TECHNICAL_ROUTE_SELECTION", selected["route_id"],
        ["EXEC_PREFLIGHT_SOURCE", "EXEC_PREFLIGHT_TEST"],
    ))

    checks = {item["check_id"]: item for item in projection["validation"]["checks"]}
    machine_by_id[TARGETED_CHECK[0]] = provenance["targeted_validation_capture"]
    machine_results = []
    ordinal = 0
    for obligation in projection["validation"]["obligation_registry"]:
        for check_id in obligation["check_ids"]:
            ordinal += 1
            source = machine_by_id.get(check_id)
            if source is None or source.get("exit_code") != 0:
                raise ValueError(f"missing passing capture for {check_id}")
            subject_id = f"{obligation['obligation_id']}:{check_id}"
            capture = _resubject_capture(
                source, f"CAP_TURN_B_VALIDATION_{ordinal:03d}", "VALIDATION_CHECK", subject_id
            )
            if (capture["observation"].get("target_ref") != job["formal_target_ref"] or
                    capture["observation"].get("argv") != checks[check_id]["argv"] or
                    capture.get("command") != checks[check_id]["command"]):
                raise ValueError("validation capture differs from formal AFTER or approved command")
            evidence_id = f"EXEC_VALIDATION_{ordinal:03d}"
            add_direct(evidence_id, capture)
            machine_results.append({
                "obligation_id": obligation["obligation_id"],
                "check_id": check_id,
                "result": "PASS",
                "evidence_ref": evidence_id,
            })

    bundle = {
        "artifact_type": "CODEX_EXECUTION_EVIDENCE_BUNDLE",
        "projection_digest": projection["projection_digest"],
        "raw_captures": raw_captures,
        "evidence_rows": evidence_rows,
        "derivation_rows": derivation_rows,
        "evidence_bundle_digest": None,
    }
    bundle["evidence_bundle_digest"] = runtime.digest(runtime.strip_digest(bundle, "evidence_bundle_digest"))
    material = {key: False for key in (
        "product_behavior_changed", "protocol_or_schema_semantics_changed", "approved_paths_expanded",
        "migration_required", "compatibility_commitment_changed", "user_visible_result_changed",
        "important_tradeoff_changed",
    )}
    preflight = {
        "status": "ROUTE_CONFIRMED",
        "object_observation_evidence_ref": "EXEC_PREFLIGHT_OBJECT",
        "obligation_results": obligation_results,
        "candidate_evaluations": evaluations,
        "selected_route": selected,
        "alternative_route": None,
        "material_change_assessment": material,
        "execution_decision": "EXECUTE",
        "implementation_decisions": [],
        "objection": None,
    }
    lifecycle = {
        "approved_lifecycle_digest": projection["task_object_lifecycle"]["lifecycle_digest"],
        "transition_status": "RESULT_VALIDATED",
        "result_binding_digest": None,
        "validation_binding_digest": None,
        "transition_digest": None,
    }
    result = {
        "artifact_type": "CODEX_EXECUTION_RETURN",
        "projection_digest": projection["projection_digest"],
        "evidence_bundle_digest": bundle["evidence_bundle_digest"],
        "technical_preflight": preflight,
        "execution_status": "COMPLETED",
        "execution_lifecycle_result": lifecycle,
        "machine_results": machine_results,
        "pr_evidence": None,
        "repository_replay_evidence": None,
        "local_repository_evidence": {
            "approved_base_commit": job["observed_object"]["digest"],
            "diff_evidence_ref": "EXEC_LOCAL_DIFF",
            "source_state_before_evidence_ref": "EXEC_LOCAL_STATE_BEFORE",
            "source_state_after_evidence_ref": "EXEC_LOCAL_STATE_AFTER",
        },
        "artifact_evidence": None,
        "evidence_transport_receipt": None,
        "blocker_evidence_refs": [],
        "mutation_summary": {"mutation_performed": True, "cleanup_status": "NOT_REQUIRED", "residual_changed_paths": []},
        "unresolved_items": [],
        "return_digest": None,
    }
    lifecycle["result_binding_digest"] = runtime._route_result_binding_digest(result)
    lifecycle["validation_binding_digest"] = runtime._validation_binding_digest(result)
    lifecycle["transition_digest"] = runtime.execution_lifecycle_result_digest(lifecycle)
    result["return_digest"] = runtime.digest(runtime.strip_digest(result, "return_digest"))
    runtime.validate_codex_execution_return_structure(result, projection, bundle)
    return result, bundle


def detached_popen_args() -> dict:
    common = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if os.name == "nt":
        required = ("CREATE_NEW_PROCESS_GROUP", "DETACHED_PROCESS", "CREATE_BREAKAWAY_FROM_JOB")
        missing = [name for name in required if not hasattr(subprocess, name)]
        if missing:
            raise RuntimeError(f"Windows detached adapter unavailable: {missing}")
        common["creationflags"] = sum(getattr(subprocess, name) for name in required)
    else:
        common["start_new_session"] = True
    return common


def launch(job_path: Path) -> dict:
    job = _load_json(job_path)
    validate_job(job)
    if repository_snapshot(Path(job["repository"])) != job["expected_before"]:
        raise RuntimeError("sealed BEFORE no longer matches; launch rejected")
    workspace = Path(job["execution_workspace"])
    occupied = ("completed.json", "failed.json", "evidence.json", "supervisor-claim.json", "continuation-claim.json")
    if any((workspace / name).exists() for name in occupied):
        raise RuntimeError("execution workspace already contains Machine or continuation state")
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    argv = [
        sys.executable, "-B", str(Path(__file__).resolve()), "supervisor",
        "--job", str(job_path.resolve()), "--job-digest", job["job_digest"],
    ]
    subprocess.Popen(argv, cwd=Path(job["repository"]), env=env, **detached_popen_args())
    return {
        "launch": "ACCEPTED",
        "execution_id": job["execution_id"],
        "job_digest": job["job_digest"],
        "execution_workspace": job["execution_workspace"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    seal = subparsers.add_parser("seal")
    seal.add_argument("--projection", type=Path, required=True)
    seal.add_argument("--authorization-envelope", type=Path, required=True)
    seal.add_argument("--repository", type=Path, required=True)
    seal.add_argument("--workspace", type=Path, required=True)
    seal.add_argument("--execution-id", required=True)
    seal.add_argument("--approved-input-capture", type=Path, required=True)
    seal.add_argument("--mutation-before-capture", type=Path, required=True)
    seal.add_argument("--before-source", type=Path, required=True)
    seal.add_argument("--execution-event-id", required=True)
    seal.add_argument("--attempt-id", required=True)
    seal.add_argument("--contract-digest", required=True)
    seal.add_argument("--continuation-id", required=True)
    seal.add_argument("--codex-session-id")
    seal.add_argument("--codex-thread-id")
    seal.add_argument("--predecessor-turn-id", required=True)
    initial_parser = subparsers.add_parser("initial-launch")
    initial_parser.add_argument("--prompt-file", type=Path, required=True)
    initial_parser.add_argument("--repository", type=Path, required=True)
    initial_parser.add_argument("--workspace", type=Path, required=True)
    initial_parser.add_argument("--execution-event-id", required=True)
    initial_parser.add_argument("--attempt-id", required=True)
    launch_parser = subparsers.add_parser("launch")
    launch_parser.add_argument("--job", type=Path, required=True)
    worker_parser = subparsers.add_parser("worker")
    worker_parser.add_argument("--job", type=Path, required=True)
    worker_parser.add_argument("--job-digest", required=True)
    supervisor_parser = subparsers.add_parser("supervisor")
    supervisor_parser.add_argument("--job", type=Path, required=True)
    supervisor_parser.add_argument("--job-digest", required=True)
    ack_parser = subparsers.add_parser("ack")
    ack_parser.add_argument("--job", type=Path, required=True)
    ack_parser.add_argument("--terminal-artifact-digest", required=True)
    ack_parser.add_argument("--codex-session-id", required=True)
    ack_parser.add_argument("--codex-thread-id", required=True)
    consume_parser = subparsers.add_parser("consume")
    consume_parser.add_argument("--workspace", type=Path, required=True)
    consume_parser.add_argument("--projection-digest", required=True)
    consume_parser.add_argument("--job-digest", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.mode == "seal":
        job, job_path = seal_job(
            args.projection, args.authorization_envelope, args.repository,
            args.workspace, args.execution_id, args.approved_input_capture,
            args.mutation_before_capture, args.before_source,
            args.execution_event_id, args.attempt_id, args.contract_digest,
            args.continuation_id, args.codex_session_id, args.codex_thread_id,
            args.predecessor_turn_id,
        )
        print(json.dumps({"sealed": True, "job": str(job_path), "job_digest": job["job_digest"]}, sort_keys=True))
        return 0
    if args.mode == "launch":
        print(json.dumps(launch(args.job), sort_keys=True))
        return 0
    if args.mode == "initial-launch":
        print(json.dumps(initial_launch(
            args.prompt_file, args.repository, args.workspace,
            args.execution_event_id, args.attempt_id,
        ), sort_keys=True))
        return 0
    if args.mode == "consume":
        evidence = consume_completed_evidence(args.workspace, args.projection_digest, args.job_digest)
        print(json.dumps({"accepted": True, "mechanical_evidence_digest": evidence["mechanical_evidence_digest"]}, sort_keys=True))
        return 0
    if args.mode == "supervisor":
        return supervisor(args.job, args.job_digest)
    if args.mode == "ack":
        claim = acknowledge_continuation(
            args.job, args.terminal_artifact_digest, args.codex_session_id, args.codex_thread_id,
        )
        print(json.dumps({"acknowledged": True, "status": claim["status"]}, sort_keys=True))
        return 0
    return worker(args.job, args.job_digest)


if __name__ == "__main__":
    raise SystemExit(main())
