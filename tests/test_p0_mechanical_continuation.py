import copy
import base64
import hashlib
import importlib.util
import inspect
import inspect
import json
import os
import shlex
import socket
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TOOLS = str(ROOT / "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = load_module("p0_runner", ROOT / "tools" / "run_mechanical_continuation.py")
generator = load_module("p0_generator", ROOT / "tools" / "generate_mechanical_assets.py")


class MechanicalContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.repository = self.base / "repository"
        self.repository.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repository, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.repository, check=True)
        subprocess.run(["git", "config", "user.name", "P0 Test"], cwd=self.repository, check=True)
        (self.repository / "tracked.txt").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=self.repository, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=self.repository, check=True)

    def tearDown(self):
        self.temporary.cleanup()

    def capture(self, capture_id, kind, observation, subject_type, subject_id, *, command="capture", exit_code=0, stdout=b"", observed_object=None):
        if observed_object is None:
            observed_object = {"kind": "REPOSITORY_COMMIT", "object_id": "owner/repo", "digest": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repository, text=True).strip()}
        row = {
            "capture_id": capture_id, "tool": runner.TOOL, "capture_kind": kind,
            "command": command, "exit_code": exit_code,
            "stdout": stdout.decode("utf-8", "replace"), "stderr": "",
            "stdout_bytes_base64": base64.b64encode(stdout).decode("ascii"), "stderr_bytes_base64": "",
            "stdout_sha256": hashlib.sha256(stdout).hexdigest(), "stderr_sha256": hashlib.sha256(b"").hexdigest(),
            "observed_object": observed_object, "observation": observation,
            "subject_type": subject_type, "subject_id": subject_id,
        }
        row["capture_sha256"] = runner.digest_object(row, "capture_sha256")
        return row

    def state_capture(self, phase, seed):
        components = {
            "head_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repository, text=True).strip(),
            "index_diff_sha256": hashlib.sha256(f"index-{seed}".encode()).hexdigest(),
            "worktree_diff_sha256": hashlib.sha256(f"worktree-{seed}".encode()).hexdigest(),
            "tracked_source_set_sha256": hashlib.sha256(f"tracked-{seed}".encode()).hexdigest(),
            "untracked_manifest_sha256": hashlib.sha256(f"untracked-{seed}".encode()).hexdigest(),
            "declared_ignored_coverage_sha256": hashlib.sha256(b"ignored").hexdigest(),
        }
        observation = {"capture_phase": phase, **components, "declared_ignored_paths": [], "state_fingerprint_sha256": hashlib.sha256(runner.canonical_bytes(components)).hexdigest()}
        return self.capture(f"CAP_STATE_{phase}", "REPOSITORY_STATE", observation, "LOCAL_REPOSITORY_SOURCE_STATE", f"{components['head_commit']}:{phase}")

    def job(self, commands=None):
        if commands is None:
            commands = [{"check_id": "CHECK", "argv": [sys.executable, "-c", "print('ok')"], "cwd_scope": "SOURCE_ROOT"}]
        observed_object = {"kind": "REPOSITORY_COMMIT", "object_id": "owner/repo", "digest": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repository, text=True).strip()}
        before_capture = self.state_capture("BEFORE", "before")
        after_capture = self.state_capture("AFTER", "after")
        before_fp = before_capture["observation"]["state_fingerprint_sha256"]
        after_fp = after_capture["observation"]["state_fingerprint_sha256"]
        approved = self.capture("CAP_OBJECT", "REPOSITORY_COMMIT", {"repository_id": "owner/repo", "remote_url": "https://github.com/owner/repo.git", "commit_sha": observed_object["digest"], "role": "APPROVED_INPUT"}, "TECHNICAL_PREFLIGHT", "subject", observed_object=observed_object)
        patch = b"diff --git a/tracked.txt b/tracked.txt\n"
        diff = self.capture("CAP_DIFF", "REPOSITORY_DIFF", {"base_ref": before_fp, "head_ref": after_fp, "changed_paths": ["tracked.txt"], "diff_sha256": hashlib.sha256(patch).hexdigest()}, "LOCAL_REPOSITORY_RESULT", after_fp, stdout=patch, observed_object=observed_object)
        targeted_argv = runner.TARGETED_CHECK[1]
        targeted = self.capture("CAP_TARGETED", "TEST_COMMAND", {"argv": targeted_argv, "cwd_scope": "SOURCE_ROOT", "target_ref": after_fp}, "VALIDATION_CHECK", runner.TARGETED_CHECK[0], command=shlex.join(targeted_argv), observed_object=observed_object)
        job = {
            "artifact_type": runner.JOB_TYPE,
            "version": 1,
            "execution_id": "p0-test",
            "projection_digest": "1" * 64,
            "execution_authorization_envelope_digest": "2" * 64,
            "repository": str(self.repository.resolve()),
            "execution_workspace": str((self.base / "workspace").resolve()),
            "observed_object": observed_object,
            "expected_before": runner.repository_snapshot(self.repository),
            "formal_target_ref": after_fp,
            "turn_a_provenance": {
                "approved_input_capture": approved, "mutation_before_capture": before_capture,
                "mutation_after_capture": after_capture, "mutation_diff_capture": diff,
                "targeted_validation_capture": targeted, "allowed_changed_paths": ["tracked.txt"],
            },
            "commands": commands,
            "repository_publication_mode": "NONE",
            "execution_event_id": "p0-event",
            "attempt_id": "attempt-01",
            "continuation_binding": {
                "contract_digest": "3" * 64,
                "continuation_id": "continuation-01",
                "codex_session_id": "thread-01",
                "codex_thread_id": "thread-01",
                "predecessor_turn_id": "turn-01",
                "allowed_resume_mode": runner.ALLOWED_RESUME_MODE,
                "binding_mode": runner.LEGACY_EXPLICIT,
                "execution_material_sha256": "3" * 64,
                "codex_runtime_identity": None,
                "initial_process_binding": None,
            },
        }
        job["job_digest"] = runner.digest_object(job, "job_digest")
        return job

    def publish_completion(self, workspace, job, evidence):
        evidence_path = workspace / "evidence.json"
        evidence_path.write_bytes(runner.canonical_bytes(evidence))
        completion = runner._completion_artifact(job, evidence_path)
        (workspace / "completed.json").write_bytes(runner.canonical_bytes(completion))
        return completion

    def runtime_identity(self):
        executable = self.base / "codex-stub.exe"
        if not executable.exists():
            executable.write_bytes(b"bounded synthetic Codex executable")
        identity = {
            "resolved_codex_executable": str(executable.resolve()),
            "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
            "codex_version": "codex-stub 1.0",
            "state_root_identity": {
                "mode": "EXPLICIT_CODEX_HOME",
                "CODEX_HOME": str((self.base / "codex-home").resolve()),
                "effective_state_root": str((self.base / "codex-home").resolve()),
                "USERPROFILE": str(self.base.resolve()),
                "APPDATA": str((self.base / "appdata").resolve()),
                "LOCALAPPDATA": str((self.base / "localappdata").resolve()),
            },
        }
        identity["runtime_identity"] = runner.digest_object(identity, "runtime_identity")
        return identity

    def production_job(self, workspace=None, thread_id="12345678-1234-4234-8234-123456789abc"):
        job = self.job()
        workspace = (workspace or (self.base / "workspace")).resolve()
        identity = self.runtime_identity()
        job["execution_workspace"] = str(workspace)
        job["continuation_binding"].update({
            "codex_session_id": thread_id,
            "codex_thread_id": thread_id,
            "binding_mode": runner.CLI_OWNED_PRODUCTION,
            "codex_runtime_identity": identity,
            "initial_process_binding": {
                "initial_pid": 4242,
                "terminal_channel": {"host": "127.0.0.1", "port": 1, "nonce": "synthetic"},
            },
        })
        job["job_digest"] = runner.digest_object(job, "job_digest")
        return job

    def initial_terminal(self, job, *, exit_code=0, completed=True):
        binding = job["continuation_binding"]
        terminal = {
            "artifact_type": "P0_INITIAL_PROCESS_TERMINAL",
            "version": 1,
            "execution_event_id": job["execution_event_id"],
            "attempt_id": job["attempt_id"],
            "execution_material_sha256": binding["execution_material_sha256"],
            "source_root": str(Path(job["repository"]).resolve()),
            "lifecycle_workspace": str(Path(job["execution_workspace"]).resolve()),
            "initial_pid": binding["initial_process_binding"]["initial_pid"],
            "frozen_thread_id": binding["codex_thread_id"],
            "initial_exit_code": exit_code,
            "initial_process_terminal_at": 1.0,
            "initial_turn_completed_observed": completed,
            "codex_runtime_identity": binding["codex_runtime_identity"],
            **runner._runtime_artifact_fields(binding["codex_runtime_identity"]),
        }
        terminal["artifact_digest"] = runner._artifact_digest(terminal)
        return terminal

    def test_initial_launch_read_once_exact_bytes_routes_and_publication_order(self):
        workspace = self.base / "lifecycle"
        prompt = mock.Mock()
        prompt_bytes = b"exact execution material\x00\xff"
        prompt.read_bytes.return_value = prompt_bytes
        identity = self.runtime_identity()
        thread_id = "12345678-1234-4234-8234-123456789abc"
        binding_listener, binding_channel = runner._new_lifecycle_listener()
        terminal_listener, terminal_channel = runner._new_lifecycle_listener()
        responses = {}
        clients = []
        client_connections = {"binding": threading.Event(), "terminal": threading.Event()}

        class FakeProcess:
            pid = 31337
            stdout = [
                runner.canonical_bytes({"type": "thread.started", "thread_id": thread_id}) + b"\n",
                runner.canonical_bytes({"type": "turn.started"}) + b"\n",
                runner.canonical_bytes({"type": "item.completed", "item": {"type": "agent_message", "text": "done"}}) + b"\n",
                runner.canonical_bytes({"type": "turn.completed"}) + b"\n",
            ]

            def wait(inner_self):
                self.assertFalse((workspace / runner.INITIAL_TERMINAL_ARTIFACT).exists())
                return 0

        def receive(name, coordinate, request_type, artifact_name):
            with socket.create_connection((coordinate["host"], coordinate["port"])) as connection:
                client_connections[name].set()
                connection.sendall(runner.canonical_bytes(runner._channel_request(
                    coordinate, request_type, "event", "attempt",
                )) + b"\n")
                responses[name] = runner._recv_json_line(connection)
                self.assertTrue((workspace / artifact_name).is_file())

        def spawn(argv, repository, lifecycle, supplied, env):
            self.assertTrue((workspace / runner.INITIAL_LAUNCH_CLAIM_ARTIFACT).is_file())
            self.assertEqual(1, prompt.read_bytes.call_count)
            self.assertEqual(prompt_bytes, supplied)
            self.assertEqual(self.repository.resolve(), repository)
            self.assertEqual(identity["resolved_codex_executable"], argv[0])
            self.assertEqual(["exec", "--json"], argv[1:3])
            self.assertNotIn("--skip-git-repo-check", argv)
            self.assertNotIn("--ephemeral", argv)
            self.assertNotIn("JOYFLOW_CODEX_THREAD_ID", env)
            self.assertNotIn(thread_id, env.values())
            clients.extend([
                threading.Thread(target=receive, args=(
                    "binding", binding_channel, "WAIT_BINDING_READY", runner.SESSION_BINDING_ARTIFACT,
                )),
                threading.Thread(target=receive, args=(
                    "terminal", terminal_channel, "WAIT_INITIAL_PROCESS_TERMINAL", runner.INITIAL_TERMINAL_ARTIFACT,
                )),
            ])
            for client in clients:
                client.start()
            self.assertTrue(client_connections["binding"].wait(2))
            self.assertTrue(client_connections["terminal"].wait(2))
            return FakeProcess(), mock.Mock()

        with mock.patch.object(runner, "_codex_runtime_identity", return_value=identity), mock.patch.object(
            runner, "_new_lifecycle_listener", side_effect=[
                (binding_listener, binding_channel), (terminal_listener, terminal_channel),
            ],
        ), mock.patch.object(runner, "_spawn_initial_codex", side_effect=spawn) as spawn_mock:
            result = runner.initial_launch(prompt, self.repository, workspace, "event", "attempt")
        for client in clients:
            client.join(2)
            self.assertFalse(client.is_alive())
        binding = runner._load_json(workspace / runner.SESSION_BINDING_ARTIFACT)
        terminal = runner._load_json(workspace / runner.INITIAL_TERMINAL_ARTIFACT)
        self.assertEqual(hashlib.sha256(prompt_bytes).hexdigest(), result["execution_material_sha256"])
        self.assertEqual(thread_id, binding["codex_session_id"])
        self.assertEqual(thread_id, binding["codex_thread_id"])
        self.assertEqual(identity["resolved_codex_executable"], binding["resolved_codex_executable"])
        self.assertEqual(identity["runtime_identity"], terminal["runtime_identity"])
        self.assertEqual(binding["artifact_digest"], responses["binding"]["artifact_digest"])
        self.assertEqual(terminal["artifact_digest"], responses["terminal"]["artifact_digest"])
        self.assertTrue(terminal["initial_turn_completed_observed"])
        prompt.read_bytes.assert_called_once_with()
        spawn_mock.assert_called_once()

    def test_initial_launch_duplicate_and_invalid_workspace_never_spawn(self):
        workspace = self.base / "lifecycle"
        workspace.mkdir()
        runner._exclusive_json(workspace / runner.INITIAL_LAUNCH_CLAIM_ARTIFACT, {"owner": True})
        prompt = mock.Mock()
        with mock.patch.object(runner, "_spawn_initial_codex") as spawn:
            with self.assertRaisesRegex(RuntimeError, "STOP_DUPLICATE_INITIAL_LAUNCH"):
                runner.initial_launch(prompt, self.repository, workspace, "event", "attempt")
            prompt.read_bytes.assert_not_called()
            spawn.assert_not_called()
        with mock.patch.object(runner, "_spawn_initial_codex") as spawn:
            with self.assertRaisesRegex(ValueError, "outside SOURCE_ROOT"):
                runner.initial_launch(prompt, self.repository, self.repository / "inside", "event", "attempt")
            spawn.assert_not_called()

    def test_initial_launch_unready_terminal_route_prevents_spawn(self):
        workspace = self.base / "lifecycle"
        prompt = mock.Mock()
        prompt.read_bytes.return_value = b"material"
        listener, coordinate = runner._new_lifecycle_listener()
        with mock.patch.object(runner, "_codex_runtime_identity", return_value=self.runtime_identity()), mock.patch.object(
            runner, "_new_lifecycle_listener", side_effect=[(listener, coordinate), OSError("route unavailable")],
        ), mock.patch.object(runner, "_spawn_initial_codex") as spawn:
            with self.assertRaisesRegex(OSError, "route unavailable"):
                runner.initial_launch(prompt, self.repository, workspace, "event", "attempt")
            spawn.assert_not_called()
        self.assertTrue((workspace / runner.INITIAL_LAUNCH_CLAIM_ARTIFACT).is_file())

    def test_initial_launch_rejects_missing_malformed_conflicting_thread_and_initial_failure(self):
        valid = "12345678-1234-4234-8234-123456789abc"
        other = "87654321-4321-4321-8321-cba987654321"
        cases = [
            ("missing", [{"type": "turn.completed"}], 0, "authoritative thread"),
            ("malformed", [{"type": "thread.started", "thread_id": "not-a-uuid"}, {"type": "turn.completed"}], 0, "authoritative thread"),
            ("conflicting", [{"type": "thread.started", "thread_id": valid}, {"type": "thread.started", "thread_id": other}, {"type": "turn.completed"}], 0, "authoritative thread"),
            ("nonzero", [{"type": "thread.started", "thread_id": valid}, {"type": "turn.completed"}], 7, "process failed"),
            ("no-completion", [{"type": "thread.started", "thread_id": valid}], 0, "completion was not observed"),
        ]
        for name, events, exit_code, message in cases:
            with self.subTest(name=name):
                workspace = self.base / f"lifecycle-{name}"
                process = mock.Mock(pid=123, stdout=[runner.canonical_bytes(event) + b"\n" for event in events])
                process.wait.return_value = exit_code
                prompt = mock.Mock()
                prompt.read_bytes.return_value = b"material"
                with mock.patch.object(runner, "_codex_runtime_identity", return_value=self.runtime_identity()), mock.patch.object(
                    runner, "_spawn_initial_codex", return_value=(process, mock.Mock())
                ):
                    with self.assertRaisesRegex(RuntimeError, message):
                        runner.initial_launch(prompt, self.repository, workspace, "event", name)
                prompt.read_bytes.assert_called_once_with()
                self.assertTrue((workspace / runner.INITIAL_TERMINAL_ARTIFACT).is_file())
                process.wait.assert_called_once_with()

    def test_seal_identity_modes_are_fail_closed_and_authoritative(self):
        identity = self.runtime_identity()
        authoritative = "12345678-1234-4234-8234-123456789abc"
        production = {
            "codex_thread_id": authoritative,
            "codex_runtime_identity": identity,
            "initial_process_binding": {"initial_pid": 1, "terminal_channel": {"host": "127.0.0.1", "port": 1, "nonce": "n"}},
        }
        kwargs = dict(
            execution_event_id="event", attempt_id="attempt", contract_digest="3" * 64,
            repository=self.repository.resolve(), workspace=(self.base / "outside").resolve(),
        )
        with mock.patch.object(runner, "_production_session_binding", return_value=production):
            automatic = runner._resolve_seal_codex_binding(codex_session_id=None, codex_thread_id=None, **kwargs)
            compatible = runner._resolve_seal_codex_binding(
                codex_session_id=authoritative, codex_thread_id=authoritative, **kwargs,
            )
            self.assertEqual(authoritative, automatic["codex_thread_id"])
            self.assertEqual(runner.CLI_OWNED_PRODUCTION, automatic["binding_mode"])
            self.assertEqual(automatic, compatible)
            with self.assertRaisesRegex(ValueError, "partial"):
                runner._resolve_seal_codex_binding(codex_session_id=authoritative, codex_thread_id=None, **kwargs)
            with self.assertRaisesRegex(ValueError, "differs"):
                runner._resolve_seal_codex_binding(
                    codex_session_id="wrong", codex_thread_id="wrong", **kwargs,
                )
        with mock.patch.object(runner, "_production_session_binding", return_value=None):
            legacy = runner._resolve_seal_codex_binding(
                codex_session_id="legacy", codex_thread_id="legacy", **kwargs,
            )
        self.assertEqual(runner.LEGACY_EXPLICIT, legacy["binding_mode"])

    def test_initial_terminal_fast_path_event_validation_and_bounded_race(self):
        job = self.production_job()
        workspace = Path(job["execution_workspace"])
        workspace.mkdir()
        terminal = self.initial_terminal(job)
        (workspace / runner.INITIAL_TERMINAL_ARTIFACT).write_bytes(runner.canonical_bytes(terminal))
        self.assertTrue(runner._initial_terminal_fast_path(job))
        left, right = socket.socketpair()
        try:
            wrong = {
                "event_type": "INITIAL_PROCESS_TERMINAL_READY",
                "execution_event_id": job["execution_event_id"],
                "attempt_id": "wrong-attempt",
                "nonce": job["continuation_binding"]["initial_process_binding"]["terminal_channel"]["nonce"],
                "artifact_digest": terminal["artifact_digest"],
            }
            right.sendall(runner.canonical_bytes(wrong) + b"\n")
            with self.assertRaisesRegex(ValueError, "mismatch"):
                runner._consume_initial_terminal_wakeup(job, left)
        finally:
            left.close(); right.close()
        with mock.patch.object(runner, "_initial_terminal_fast_path", side_effect=[False, True]) as fast, mock.patch.object(
            runner, "_connect_initial_terminal_channel", side_effect=ConnectionRefusedError("publication race")
        ):
            runner._await_initial_process_terminal_gate(job)
        self.assertEqual(2, fast.call_count)
        gate_source = inspect.getsource(runner._await_initial_process_terminal_gate)
        worker_source = inspect.getsource(runner._wait_for_worker_events)
        self.assertNotIn("sleep(", gate_source)
        self.assertNotIn("initial_terminal", worker_source)

    def test_production_resume_uses_frozen_executable_state_and_single_exact_thread(self):
        job = self.production_job()
        binding = job["continuation_binding"]
        last_message = Path(job["execution_workspace"]) / "last.txt"
        argv = runner._continuation_argv(job, last_message)
        self.assertEqual(binding["codex_runtime_identity"]["resolved_codex_executable"], argv[0])
        self.assertEqual(binding["codex_thread_id"], argv[-2])
        self.assertNotIn("--last", argv)
        self.assertEqual(1, argv.count("resume"))
        version = subprocess.CompletedProcess([], 0, b"codex-stub 1.0\n", b"")
        with mock.patch.object(runner, "_run_bytes", return_value=version):
            env = runner._production_resume_environment(binding)
        state = binding["codex_runtime_identity"]["state_root_identity"]
        for key in ("CODEX_HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA"):
            self.assertEqual(state[key], env[key])

    def test_active_writer_exit_and_unknown_dispatch_never_redispatch(self):
        job = self.job(); workspace = Path(job["execution_workspace"]); workspace.mkdir()
        terminal = runner._failure_artifact(job, "TEST", 1, RuntimeError("x"))

        def active_writer(job_arg, payload_path, argv, events_path, stderr_path):
            events_path.write_bytes(b"")
            stderr_path.write_text("thread already has an active writer\n", encoding="utf-8")
            process = mock.Mock(pid=1234, returncode=1)
            process.wait.return_value = 1
            return process

        with mock.patch.object(runner, "_spawn_continuation", side_effect=active_writer) as spawn:
            self.assertEqual(runner.DISPATCH_UNKNOWN, runner.dispatch_continuation(job, terminal))
            with self.assertRaises(FileExistsError):
                runner.dispatch_continuation(job, terminal)
        self.assertEqual(1, spawn.call_count)

    def test_dispatch_confirmation_requires_turn_completed_and_exact_thread(self):
        job = self.job(); workspace = Path(job["execution_workspace"]); workspace.mkdir()
        terminal = runner._failure_artifact(job, "TEST", 1, RuntimeError("x"))

        def incomplete(job_arg, payload_path, argv, events_path, stderr_path):
            events_path.write_text("\n".join([
                json.dumps({"type": "thread.started", "thread_id": "thread-01"}),
                json.dumps({"type": "turn.started"}),
                json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "done"}}),
            ]) + "\n", encoding="utf-8")
            stderr_path.write_bytes(b"")
            (workspace / "continuation-last-message.txt").write_text("done", encoding="utf-8")
            process = mock.Mock(pid=1234, returncode=0)
            process.wait.return_value = 0
            return process

        with mock.patch.object(runner, "_spawn_continuation", side_effect=incomplete):
            self.assertEqual(runner.DISPATCH_UNKNOWN, runner.dispatch_continuation(job, terminal))
        claim = runner._load_json(workspace / "continuation-claim.json")
        self.assertFalse(claim["automatic_resume_turn_completed_observed"])

    def test_schema_elapsed_seconds_is_optional_nonnegative_and_digest_bound(self):
        schema = generator.evidence_bundle_schema({})
        capture = schema["properties"]["raw_captures"]["items"]
        self.assertNotIn("elapsed_seconds", capture["required"])
        self.assertEqual({"type": "number", "minimum": 0}, capture["properties"]["elapsed_seconds"])
        sample = self.job()
        evidence = runner.execute_job(sample)
        capture_value = evidence["raw_captures"][0]
        original = capture_value["capture_sha256"]
        changed = dict(capture_value, elapsed_seconds=capture_value["elapsed_seconds"] + 1)
        self.assertNotEqual(original, runner.digest_object(changed, "capture_sha256"))

    def test_snapshot_uses_raw_status_and_utf8_record_order(self):
        (self.repository / "tracked.txt").write_text("changed\n", encoding="utf-8")
        (self.repository / "z.txt").write_bytes(b"z")
        (self.repository / "A.txt").write_bytes(b"A")
        snapshot = runner.repository_snapshot(self.repository)
        self.assertEqual(1, snapshot["tracked_modified"])
        self.assertEqual(2, snapshot["untracked"])
        self.assertEqual(3, snapshot["total_candidate_paths"])
        self.assertEqual(snapshot["records"], sorted(snapshot["records"], key=lambda value: value.encode("utf-8")))
        self.assertTrue(any("| M|" in record for record in snapshot["records"]))
        self.assertTrue(any("|??|" in record for record in snapshot["records"]))

    def test_job_tamper_is_rejected(self):
        job = self.job()
        job["commands"][0]["argv"][-1] = "print('tampered')"
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            runner.validate_job(job)

    def test_missing_turn_a_mutation_provenance_is_rejected(self):
        job = self.job()
        del job["turn_a_provenance"]
        job["job_digest"] = runner.digest_object(job, "job_digest")
        with self.assertRaisesRegex(ValueError, "invalid mechanical job shape|missing Turn-A mutation provenance"):
            runner.validate_job(job)

    def test_completed_mutation_equal_formal_fingerprints_is_rejected(self):
        job = self.job()
        after = copy.deepcopy(job["turn_a_provenance"]["mutation_after_capture"])
        after["observation"] = copy.deepcopy(job["turn_a_provenance"]["mutation_before_capture"]["observation"])
        after["observation"]["capture_phase"] = "AFTER"
        after["capture_sha256"] = runner.digest_object(after, "capture_sha256")
        job["turn_a_provenance"]["mutation_after_capture"] = after
        job["formal_target_ref"] = after["observation"]["state_fingerprint_sha256"]
        job["job_digest"] = runner.digest_object(job, "job_digest")
        with self.assertRaisesRegex(ValueError, "BEFORE fingerprint equals formal AFTER"):
            runner.validate_job(job)

    def test_validation_target_must_equal_formal_after_fingerprint(self):
        job = self.job()
        targeted = job["turn_a_provenance"]["targeted_validation_capture"]
        targeted["observation"]["target_ref"] = "0" * 64
        targeted["capture_sha256"] = runner.digest_object(targeted, "capture_sha256")
        job["job_digest"] = runner.digest_object(job, "job_digest")
        with self.assertRaisesRegex(ValueError, "validation target_ref"):
            runner.validate_job(job)

    def test_mutation_provenance_change_after_seal_breaks_job_digest(self):
        job = self.job()
        job["turn_a_provenance"]["allowed_changed_paths"].append("other.txt")
        with self.assertRaisesRegex(ValueError, "job digest mismatch"):
            runner.validate_job(job)

    def test_expected_launch_digest_rejects_resealed_substitution(self):
        job = self.job()
        original = job["job_digest"]
        job["execution_id"] = "substituted"
        job["job_digest"] = runner.digest_object(job, "job_digest")
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            runner.validate_job(job, original)

    def test_before_mismatch_executes_no_commands(self):
        marker = self.repository / "must-not-exist"
        job = self.job([{"check_id": "CHECK", "argv": [sys.executable, "-c", f"open({str(marker)!r},'w').write('x')"], "cwd_scope": "SOURCE_ROOT"}])
        (self.repository / "drift.txt").write_text("drift", encoding="utf-8")
        evidence = runner.execute_job(job)
        self.assertEqual("BEFORE_MISMATCH", evidence["result"])
        self.assertEqual([], evidence["raw_captures"])
        self.assertFalse(marker.exists())

    def test_all_sealed_commands_run_and_failure_remains_truthful(self):
        commands = [
            {"check_id": "ONE", "argv": [sys.executable, "-c", "print('one')"], "cwd_scope": "SOURCE_ROOT"},
            {"check_id": "TWO", "argv": [sys.executable, "-c", "import sys; print('two', file=sys.stderr); sys.exit(7)"], "cwd_scope": "SOURCE_ROOT"},
            {"check_id": "THREE", "argv": [sys.executable, "-c", "print('three')"], "cwd_scope": "SOURCE_ROOT"},
        ]
        evidence = runner.execute_job(self.job(commands))
        self.assertEqual("FAILED", evidence["result"])
        self.assertEqual([0, 7, 0], [capture["exit_code"] for capture in evidence["raw_captures"]])
        self.assertIn("two", evidence["raw_captures"][1]["stderr"])
        self.assertTrue(all(capture["elapsed_seconds"] >= 0 for capture in evidence["raw_captures"]))

    def test_after_source_drift_invalidates_success(self):
        target = self.repository / "unexpected.txt"
        command = {"check_id": "DRIFT", "argv": [sys.executable, "-c", f"open({str(target)!r},'w').write('drift')"], "cwd_scope": "SOURCE_ROOT"}
        evidence = runner.execute_job(self.job([command]))
        self.assertEqual("INVALIDATED_BY_SOURCE_DRIFT", evidence["result"])
        self.assertTrue(evidence["source_drift"])

    def test_completed_intake_rejects_machine_candidate_substitution(self):
        job = self.job(commands=[{"check_id": check_id, "argv": argv, "cwd_scope": "SOURCE_ROOT"} for check_id, argv in runner.APPROVED_COMMANDS])
        workspace = Path(job["execution_workspace"])
        workspace.mkdir()
        (workspace / "job.json").write_bytes(runner.canonical_bytes(job))
        substituted = copy.deepcopy(job["expected_before"])
        substituted["canonical_snapshot"] = "0" * 64
        captures = []
        for ordinal, (check_id, argv) in enumerate(runner.APPROVED_COMMANDS, 1):
            capture = self.capture(f"CAP_MACHINE_{ordinal}", "TEST_COMMAND", {"argv": argv, "cwd_scope": "SOURCE_ROOT", "target_ref": job["formal_target_ref"]}, "VALIDATION_CHECK", check_id, command=shlex.join(argv), observed_object=job["observed_object"])
            capture["elapsed_seconds"] = 0.1
            capture["capture_sha256"] = runner.digest_object(capture, "capture_sha256")
            captures.append(capture)
        evidence = {"artifact_type": runner.EVIDENCE_TYPE, "version": 1, "execution_id": job["execution_id"], "projection_digest": job["projection_digest"], "execution_authorization_envelope_digest": job["execution_authorization_envelope_digest"], "job_digest": job["job_digest"], "observed_object": job["observed_object"], "before": substituted, "raw_captures": captures, "after": copy.deepcopy(substituted), "source_drift": False, "result": "PASSED", "execution_error": None}
        evidence["mechanical_evidence_digest"] = runner.digest_object(evidence, "mechanical_evidence_digest")
        self.publish_completion(workspace, job, evidence)
        with self.assertRaisesRegex(ValueError, "Machine candidate differs"):
            runner.consume_completed_evidence(workspace, job["projection_digest"], job["job_digest"])

    def test_machine_evidence_contains_no_return_or_authority_actions(self):
        evidence = runner.execute_job(self.job())
        serialized = json.dumps(evidence, sort_keys=True)
        for forbidden in ("codex_execution_return", "return_digest", '"commit"', '"push"', "pull_request", '"merge"', '"repair"'):
            self.assertNotIn(forbidden, serialized.lower())

    def test_valid_turn_a_and_machine_evidence_construct_current_runtime_formal_objects(self):
        from tests import build_fixture

        _, projection, _, _ = build_fixture.approved_capsule(scope="REPOSITORY_CHANGE", publication_mode="NONE")
        check = projection["validation"]["checks"][0]
        job = self.job([{"check_id": check["check_id"], "argv": check["argv"], "cwd_scope": check["cwd_scope"]}])
        expected = copy.deepcopy(projection["execution_object"]["physical_object"])
        job["repository"] = str(ROOT)
        job["projection_digest"] = projection["projection_digest"]
        job["observed_object"] = expected
        provenance = job["turn_a_provenance"]
        approved = provenance["approved_input_capture"]
        approved["observed_object"] = expected
        approved["observation"] = {"repository_id": expected["object_id"], "remote_url": "https://github.com/example/repo.git", "commit_sha": expected["digest"], "role": "APPROVED_INPUT"}
        approved["capture_sha256"] = runner.digest_object(approved, "capture_sha256")
        for phase_key, phase in (("mutation_before_capture", "BEFORE"), ("mutation_after_capture", "AFTER")):
            state = provenance[phase_key]
            state["observed_object"] = expected
            state["observation"]["head_commit"] = expected["digest"]
            components = {key: state["observation"][key] for key in ("head_commit", "index_diff_sha256", "worktree_diff_sha256", "tracked_source_set_sha256", "untracked_manifest_sha256", "declared_ignored_coverage_sha256")}
            state["observation"]["state_fingerprint_sha256"] = hashlib.sha256(runner.canonical_bytes(components)).hexdigest()
            state["capture_sha256"] = runner.digest_object(state, "capture_sha256")
        before_fp = provenance["mutation_before_capture"]["observation"]["state_fingerprint_sha256"]
        after_fp = provenance["mutation_after_capture"]["observation"]["state_fingerprint_sha256"]
        diff = provenance["mutation_diff_capture"]
        diff["observed_object"] = expected
        diff["subject_id"] = after_fp
        diff["observation"].update({"base_ref": before_fp, "head_ref": after_fp, "changed_paths": ["runtime/joyflow_dual_layer.py"]})
        diff["capture_sha256"] = runner.digest_object(diff, "capture_sha256")
        targeted = provenance["targeted_validation_capture"]
        targeted["observed_object"] = expected
        targeted["observation"]["target_ref"] = after_fp
        targeted["capture_sha256"] = runner.digest_object(targeted, "capture_sha256")
        provenance["allowed_changed_paths"] = ["runtime/**"]
        job["formal_target_ref"] = after_fp
        job["job_digest"] = runner.digest_object(job, "job_digest")
        machine_capture = self.capture("CAP_MACHINE_CHECK", "TEST_COMMAND", {"argv": check["argv"], "cwd_scope": check["cwd_scope"], "target_ref": after_fp}, "VALIDATION_CHECK", check["check_id"], command=check["command"], observed_object=expected)
        machine_capture["elapsed_seconds"] = 0.1
        machine_capture["capture_sha256"] = runner.digest_object(machine_capture, "capture_sha256")
        evidence = {"artifact_type": runner.EVIDENCE_TYPE, "version": 1, "execution_id": job["execution_id"], "projection_digest": job["projection_digest"], "execution_authorization_envelope_digest": job["execution_authorization_envelope_digest"], "job_digest": job["job_digest"], "observed_object": expected, "before": job["expected_before"], "raw_captures": [machine_capture], "after": job["expected_before"], "source_drift": False, "result": "PASSED", "execution_error": None}
        evidence["mechanical_evidence_digest"] = runner.digest_object(evidence, "mechanical_evidence_digest")
        result, bundle = runner.construct_formal_artifacts(projection, job, evidence)
        runtime = runner._load_runtime_module(ROOT)
        runtime.validate_codex_execution_return_structure(result, projection, bundle)
        self.assertEqual(bundle["evidence_bundle_digest"], runtime.digest(runtime.strip_digest(bundle, "evidence_bundle_digest")))
        self.assertEqual(result["return_digest"], runtime.digest(runtime.strip_digest(result, "return_digest")))

    def test_notification_failure_cannot_change_persisted_truth(self):
        with mock.patch.object(runner.subprocess, "run", side_effect=OSError("notification unavailable")):
            runner._notify_best_effort("PASSED", self.base / "evidence.json")

    def test_posix_adapter_is_one_shot_session_detachment(self):
        with mock.patch.object(runner.os, "name", "posix"):
            kwargs = runner.detached_popen_args()
        self.assertTrue(kwargs["start_new_session"])
        self.assertNotIn("creationflags", kwargs)

    @unittest.skipUnless(sys.platform == "win32", "Windows adapter assertion")
    def test_windows_adapter_uses_proven_detached_flags(self):
        kwargs = runner.detached_popen_args()
        expected = subprocess.CREATE_NEW_PROCESS_GROUP + subprocess.DETACHED_PROCESS + subprocess.CREATE_BREAKAWAY_FROM_JOB
        self.assertEqual(expected, kwargs["creationflags"])
        self.assertNotIn("start_new_session", kwargs)

    def test_launch_returns_accepted_without_wait_or_poll(self):
        job = self.job()
        workspace = Path(job["execution_workspace"])
        workspace.mkdir()
        path = workspace / "job.json"
        path.write_bytes(runner.canonical_bytes(job))
        process = mock.Mock()
        with mock.patch.object(runner, "repository_snapshot", return_value=job["expected_before"]), mock.patch.object(
            runner, "detached_popen_args", return_value={}
        ), mock.patch.object(runner.subprocess, "Popen", return_value=process) as popen:
            accepted = runner.launch(path)
        self.assertEqual("ACCEPTED", accepted["launch"])
        popen.assert_called_once()
        process.wait.assert_not_called()
        process.poll.assert_not_called()

    def test_completed_intake_rejects_missing_elapsed(self):
        job = self.job()
        workspace = Path(job["execution_workspace"])
        workspace.mkdir()
        (workspace / "job.json").write_bytes(runner.canonical_bytes(job))
        evidence = runner.execute_job(job)
        evidence["result"] = "PASSED"
        evidence["source_drift"] = False
        evidence["raw_captures"] = []
        evidence["mechanical_evidence_digest"] = runner.digest_object(evidence, "mechanical_evidence_digest")
        with self.assertRaisesRegex(ValueError, "lacks sealed captures"):
            self.publish_completion(workspace, job, evidence)

    def test_completed_intake_rejects_evidence_tamper(self):
        job = self.job()
        workspace = Path(job["execution_workspace"])
        workspace.mkdir()
        (workspace / "job.json").write_bytes(runner.canonical_bytes(job))
        evidence_path = workspace / "evidence.json"
        evidence_path.write_bytes(b"{}")
        completion = {
            "artifact_type": runner.COMPLETION_TYPE, "version": 1,
            "terminal_semantics": runner.RESULT_AVAILABLE,
            "execution_event_id": job["execution_event_id"], "attempt_id": job["attempt_id"],
            "execution_id": job["execution_id"], "job_digest": job["job_digest"],
            "projection_digest": job["projection_digest"], "result": "PASSED",
            "evidence_file": "evidence.json", "evidence_sha256": "0" * 64,
        }
        completion["terminal_artifact_digest"] = runner.digest_object(completion, "terminal_artifact_digest")
        (workspace / "completed.json").write_bytes(runner.canonical_bytes(completion))
        with self.assertRaisesRegex(ValueError, "bind Evidence bytes"):
            runner.consume_completed_evidence(workspace, job["projection_digest"], job["job_digest"])

    def test_worker_publishes_only_evidence_and_validation_failure_is_consumable(self):
        job = self.job([{"check_id": "FAIL", "argv": [sys.executable, "-c", "raise SystemExit(9)"], "cwd_scope": "SOURCE_ROOT"}])
        workspace = Path(job["execution_workspace"]); workspace.mkdir()
        job_path = workspace / "job.json"; job_path.write_bytes(runner.canonical_bytes(job))
        self.assertEqual(0, runner.worker(job_path, job["job_digest"]))
        self.assertEqual("FAILED", json.loads((workspace / "evidence.json").read_text())["result"])
        self.assertFalse((workspace / "completed.json").exists())
        self.assertFalse((workspace / "failed.json").exists())

    def test_supervisor_normal_result_publishes_completed_not_failed_once(self):
        job = self.job(); workspace = Path(job["execution_workspace"]); workspace.mkdir()
        job_path = workspace / "job.json"; job_path.write_bytes(runner.canonical_bytes(job))
        evidence = runner.execute_job(job)
        monitor = mock.Mock()
        def worker_once(*args, **kwargs):
            (workspace / "evidence.json").write_bytes(runner.canonical_bytes(evidence))
            return 0, monitor
        with mock.patch.object(runner, "_wait_for_worker_events", side_effect=worker_once) as wait, mock.patch.object(runner, "dispatch_continuation", return_value=runner.DISPATCH_UNKNOWN), mock.patch.object(runner, "_notify_best_effort"):
            self.assertEqual(0, runner.supervisor(job_path, job["job_digest"]))
        wait.assert_called_once_with(job, job_path)
        monitor.publish_terminal.assert_called_once_with(runner.RESULT_AVAILABLE)
        self.assertTrue((workspace / "completed.json").exists())
        self.assertFalse((workspace / "failed.json").exists())
        terminal = runner._load_json(workspace / "completed.json")
        self.assertEqual(runner.RESULT_AVAILABLE, terminal["terminal_semantics"])
        self.assertEqual(job["job_digest"], terminal["job_digest"])

    def test_supervisor_worker_without_evidence_publishes_failed_not_completed(self):
        job = self.job(); workspace = Path(job["execution_workspace"]); workspace.mkdir()
        job_path = workspace / "job.json"; job_path.write_bytes(runner.canonical_bytes(job))
        monitor = mock.Mock()
        with mock.patch.object(runner, "_wait_for_worker_events", return_value=(7, monitor)) as wait, mock.patch.object(runner, "dispatch_continuation", return_value=runner.DISPATCH_UNKNOWN), mock.patch.object(runner, "_notify_best_effort"):
            self.assertEqual(1, runner.supervisor(job_path, job["job_digest"]))
        wait.assert_called_once_with(job, job_path)
        monitor.publish_terminal.assert_called_once_with(runner.MACHINE_INFRASTRUCTURE_FAILED)
        self.assertTrue((workspace / "failed.json").exists())
        self.assertFalse((workspace / "completed.json").exists())
        self.assertEqual(runner.MACHINE_INFRASTRUCTURE_FAILED, runner._load_json(workspace / "failed.json")["terminal_semantics"])

    def test_invalid_initial_gate_preserves_machine_terminal_and_never_dispatches(self):
        job = self.production_job(); workspace = Path(job["execution_workspace"]); workspace.mkdir()
        job_path = workspace / "job.json"; job_path.write_bytes(runner.canonical_bytes(job))
        evidence = runner.execute_job(job)
        invalid = self.initial_terminal(job)
        invalid["attempt_id"] = "wrong-attempt"
        invalid["artifact_digest"] = runner._artifact_digest(invalid)
        (workspace / runner.INITIAL_TERMINAL_ARTIFACT).write_bytes(runner.canonical_bytes(invalid))
        monitor = mock.Mock()

        def worker_once(*args, **kwargs):
            (workspace / "evidence.json").write_bytes(runner.canonical_bytes(evidence))
            return 0, monitor

        with mock.patch.object(runner, "_wait_for_worker_events", side_effect=worker_once), mock.patch.object(
            runner, "dispatch_continuation"
        ) as dispatch, mock.patch.object(runner, "_notify_best_effort"):
            with self.assertRaisesRegex(ValueError, "initial process terminal attempt_id mismatch"):
                runner.supervisor(job_path, job["job_digest"])
        self.assertTrue((workspace / "completed.json").is_file())
        self.assertFalse((workspace / "failed.json").exists())
        self.assertFalse((workspace / "continuation-claim.json").exists())
        dispatch.assert_not_called()
        monitor.publish_terminal.assert_called_once_with(runner.RESULT_AVAILABLE)
        monitor.publish_continuation.assert_not_called()

    def test_unavailable_initial_gate_preserves_machine_terminal_and_never_dispatches(self):
        job = self.production_job(); workspace = Path(job["execution_workspace"]); workspace.mkdir()
        job_path = workspace / "job.json"; job_path.write_bytes(runner.canonical_bytes(job))
        evidence = runner.execute_job(job)
        monitor = mock.Mock()

        def worker_once(*args, **kwargs):
            (workspace / "evidence.json").write_bytes(runner.canonical_bytes(evidence))
            return 0, monitor

        with mock.patch.object(runner, "_wait_for_worker_events", side_effect=worker_once), mock.patch.object(
            runner, "_connect_initial_terminal_channel", side_effect=ConnectionRefusedError("unavailable")
        ) as connect, mock.patch.object(runner, "dispatch_continuation") as dispatch, mock.patch.object(
            runner, "_notify_best_effort"
        ):
            with self.assertRaisesRegex(RuntimeError, "gate is unavailable"):
                runner.supervisor(job_path, job["job_digest"])
        self.assertTrue((workspace / "completed.json").is_file())
        self.assertFalse((workspace / "continuation-claim.json").exists())
        connect.assert_called_once_with(job)
        dispatch.assert_not_called()

    def test_machine_terminal_is_persisted_before_blocked_gate_then_dispatches_once(self):
        job = self.production_job(); workspace = Path(job["execution_workspace"]); workspace.mkdir()
        job_path = workspace / "job.json"; job_path.write_bytes(runner.canonical_bytes(job))
        evidence = runner.execute_job(job)
        monitor = mock.Mock()
        gate_entered = threading.Event()
        release_gate = threading.Event()
        result = []

        def worker_once(*args, **kwargs):
            (workspace / "evidence.json").write_bytes(runner.canonical_bytes(evidence))
            return 0, monitor

        def blocked_gate(job_arg):
            gate_entered.set()
            if not release_gate.wait(5):
                raise RuntimeError("synthetic Gate-B release timeout")

        def run_supervisor():
            result.append(runner.supervisor(job_path, job["job_digest"]))

        with mock.patch.object(runner, "_wait_for_worker_events", side_effect=worker_once), mock.patch.object(
            runner, "_await_initial_process_terminal_gate", side_effect=blocked_gate
        ), mock.patch.object(runner, "dispatch_continuation", return_value=runner.DISPATCH_UNKNOWN) as dispatch, mock.patch.object(
            runner, "_notify_best_effort"
        ):
            supervisor_thread = threading.Thread(target=run_supervisor)
            supervisor_thread.start()
            self.assertTrue(gate_entered.wait(2))
            self.assertTrue((workspace / "completed.json").is_file())
            self.assertFalse((workspace / "continuation-claim.json").exists())
            dispatch.assert_not_called()
            release_gate.set()
            supervisor_thread.join(5)
            self.assertFalse(supervisor_thread.is_alive())
        self.assertEqual([0], result)
        dispatch.assert_called_once()

    def test_valid_production_gate_dispatches_once_for_success_and_existing_failure(self):
        for machine_result in ("success", "failure"):
            with self.subTest(machine_result=machine_result):
                workspace = self.base / f"workspace-{machine_result}"
                job = self.production_job(workspace=workspace); workspace.mkdir()
                job_path = workspace / "job.json"; job_path.write_bytes(runner.canonical_bytes(job))
                initial = self.initial_terminal(job)
                (workspace / runner.INITIAL_TERMINAL_ARTIFACT).write_bytes(runner.canonical_bytes(initial))
                monitor = mock.Mock()
                if machine_result == "success":
                    evidence = runner.execute_job(job)

                    def worker_once(*args, **kwargs):
                        (workspace / "evidence.json").write_bytes(runner.canonical_bytes(evidence))
                        return 0, monitor
                else:
                    def worker_once(*args, **kwargs):
                        return 7, monitor
                with mock.patch.object(runner, "_wait_for_worker_events", side_effect=worker_once), mock.patch.object(
                    runner, "dispatch_continuation", return_value=runner.DISPATCH_UNKNOWN
                ) as dispatch, mock.patch.object(runner, "_notify_best_effort"):
                    exit_code = runner.supervisor(job_path, job["job_digest"])
                dispatch.assert_called_once()
                dispatched_terminal = dispatch.call_args.args[1]
                if machine_result == "success":
                    self.assertEqual(0, exit_code)
                    self.assertEqual(runner.COMPLETION_TYPE, dispatched_terminal["artifact_type"])
                    self.assertTrue((workspace / "completed.json").is_file())
                else:
                    self.assertEqual(1, exit_code)
                    self.assertEqual(runner.FAILURE_TYPE, dispatched_terminal["artifact_type"])
                    self.assertTrue((workspace / "failed.json").is_file())

    def test_legacy_gate_remains_compatible_without_initial_terminal_primitives(self):
        job = self.job()
        with mock.patch.object(runner, "_initial_terminal_fast_path") as fast, mock.patch.object(
            runner, "_connect_initial_terminal_channel"
        ) as connect, mock.patch.object(runner, "_consume_initial_terminal_wakeup") as consume:
            runner._await_initial_process_terminal_gate(job)
        fast.assert_not_called(); connect.assert_not_called(); consume.assert_not_called()

    def test_terminal_rejects_wrong_job_attempt_and_event_bindings(self):
        job = self.job(); workspace = Path(job["execution_workspace"]); workspace.mkdir()
        evidence = runner.execute_job(job); path = workspace / "evidence.json"; path.write_bytes(runner.canonical_bytes(evidence))
        terminal = runner._completion_artifact(job, path)
        for key in ("job_digest", "attempt_id", "execution_event_id"):
            changed = dict(terminal); changed[key] = "wrong"; changed["terminal_artifact_digest"] = runner.digest_object(changed, "terminal_artifact_digest")
            with self.assertRaisesRegex(ValueError, "binding mismatch"):
                runner.validate_terminal_artifact(changed, job)

    def test_duplicate_continuation_claim_cannot_dispatch_twice(self):
        job = self.job(); workspace = Path(job["execution_workspace"]); workspace.mkdir()
        terminal = runner._failure_artifact(job, "TEST", 1, RuntimeError("x"))
        with mock.patch.object(runner, "_spawn_continuation", side_effect=OSError("uncertain spawn")) as spawn:
            self.assertEqual(runner.DISPATCH_UNKNOWN, runner.dispatch_continuation(job, terminal))
            with self.assertRaises(FileExistsError):
                runner.dispatch_continuation(job, terminal)
        spawn.assert_called_once()
        self.assertEqual(runner.DISPATCH_UNKNOWN, runner._load_json(workspace / "continuation-claim.json")["status"])

    def test_manual_ack_is_separate_and_does_not_rewrite_automatic_unknown(self):
        job = self.job(); workspace = Path(job["execution_workspace"]); workspace.mkdir()
        job_path = workspace / "job.json"; job_path.write_bytes(runner.canonical_bytes(job))
        terminal = runner._failure_artifact(job, "TEST", 1, RuntimeError("x"))
        (workspace / "failed.json").write_bytes(runner.canonical_bytes(terminal))
        with mock.patch.object(runner, "_spawn_continuation", side_effect=OSError("uncertain spawn")):
            runner.dispatch_continuation(job, terminal)
        with self.assertRaisesRegex(ValueError, "terminal binding"):
            runner.acknowledge_continuation(job_path, "0" * 64, "thread-01", "thread-01")
        with self.assertRaisesRegex(ValueError, "Codex identity"):
            runner.acknowledge_continuation(job_path, terminal["terminal_artifact_digest"], "wrong", "thread-01")
        manual = runner.acknowledge_continuation(
            job_path, terminal["terminal_artifact_digest"], "thread-01", "thread-01",
        )
        self.assertEqual(runner.MANUAL_ACKNOWLEDGED, manual["status"])
        self.assertEqual(runner.DISPATCH_UNKNOWN, manual["automatic_dispatch_status_at_ack"])
        self.assertEqual(runner.DISPATCH_UNKNOWN, runner._load_json(workspace / "continuation-claim.json")["status"])

    def test_exact_thread_jsonl_proof_confirms_automatic_dispatch(self):
        job = self.job(); workspace = Path(job["execution_workspace"]); workspace.mkdir()
        terminal = runner._failure_artifact(job, "TEST", 1, RuntimeError("x"))

        def completed_process(job_arg, payload_path, argv, events_path, stderr_path):
            self.assertEqual([
                "codex", "exec", "resume", "--json", "--output-last-message",
                str((workspace / "continuation-last-message.txt").resolve()), "thread-01", "-",
            ], argv)
            events_path.write_text("\n".join([
                json.dumps({"type": "thread.started", "thread_id": "thread-01"}),
                json.dumps({"type": "turn.started"}),
                json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "done"}}),
                json.dumps({"type": "turn.completed"}),
            ]) + "\n", encoding="utf-8")
            stderr_path.write_bytes(b"")
            (workspace / "continuation-last-message.txt").write_text("done", encoding="utf-8")
            process = mock.Mock(pid=1234, returncode=0)
            return process

        with mock.patch.object(runner, "_spawn_continuation", side_effect=completed_process) as spawn:
            self.assertEqual(runner.DISPATCH_CONFIRMED, runner.dispatch_continuation(job, terminal))
        claim = runner._load_json(workspace / "continuation-claim.json")
        self.assertEqual("thread-01", claim["reported_thread_id"])
        self.assertTrue(claim["same_thread_confirmed"])
        self.assertTrue(claim["automatic_resume_user_turn_observed"])
        self.assertTrue(claim["automatic_resume_assistant_turn_observed"])
        spawn.assert_called_once()

    def test_exit_zero_wrong_reported_thread_stops_without_confirmation(self):
        job = self.job(); workspace = Path(job["execution_workspace"]); workspace.mkdir()
        terminal = runner._failure_artifact(job, "TEST", 1, RuntimeError("x"))

        def wrong_thread(job_arg, payload_path, argv, events_path, stderr_path):
            events_path.write_text("\n".join([
                json.dumps({"type": "thread.started", "thread_id": "wrong-thread"}),
                json.dumps({"type": "turn.started"}),
                json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "done"}}),
            ]) + "\n", encoding="utf-8")
            stderr_path.write_bytes(b"")
            (workspace / "continuation-last-message.txt").write_text("done", encoding="utf-8")
            return mock.Mock(pid=1234, returncode=0)

        with mock.patch.object(runner, "_spawn_continuation", side_effect=wrong_thread) as spawn:
            self.assertEqual(runner.STOP_CONTINUATION_WRONG_THREAD, runner.dispatch_continuation(job, terminal))
        claim = runner._load_json(workspace / "continuation-claim.json")
        self.assertEqual(runner.DISPATCH_UNKNOWN, claim["status"])
        self.assertFalse(claim["same_thread_confirmed"])
        self.assertEqual(runner.STOP_CONTINUATION_WRONG_THREAD, claim["stop_reason"])
        spawn.assert_called_once()

    def test_spawn_without_durable_confirmation_stays_unknown_and_cannot_redispatch(self):
        job = self.job(); workspace = Path(job["execution_workspace"]); workspace.mkdir()
        terminal = runner._failure_artifact(job, "TEST", 1, RuntimeError("x"))
        process = mock.Mock(pid=1234, returncode=0)
        with mock.patch.object(runner, "_spawn_continuation", return_value=process) as spawn:
            self.assertEqual(runner.DISPATCH_UNKNOWN, runner.dispatch_continuation(job, terminal))
            with self.assertRaises(FileExistsError):
                runner.dispatch_continuation(job, terminal)
        self.assertEqual(1, spawn.call_count)
        claim = runner._load_json(workspace / "continuation-claim.json")
        self.assertEqual(runner.DISPATCH_UNKNOWN, claim["status"])
        self.assertIn("dispatch_error", claim)

    def test_continuation_rejects_heuristic_session_and_wrong_thread_is_digest_bound(self):
        job = self.job(); job["continuation_binding"]["codex_session_id"] = "--last"; job["job_digest"] = runner.digest_object(job, "job_digest")
        with self.assertRaisesRegex(ValueError, "heuristic"):
            runner.validate_job(job)
        job = self.job(); original = job["job_digest"]; job["continuation_binding"]["codex_thread_id"] = "other"
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            runner.validate_job(job, original)

    def test_contract_repair_requires_fresh_attempt_and_allowed_paths(self):
        job = self.job()
        digest = job["continuation_binding"]["contract_digest"]
        self.assertEqual("CONTINUE_SAME_EXECUTION_EVENT", runner.authorize_in_contract_repair(job, "attempt-02", ["tracked.txt"], digest))
        self.assertEqual("STOP_CONTRACT_BOUNDARY_REACHED", runner.authorize_in_contract_repair(job, job["attempt_id"], ["tracked.txt"], digest))
        self.assertEqual("STOP_CONTRACT_BOUNDARY_REACHED", runner.authorize_in_contract_repair(job, "attempt-02", ["outside.txt"], digest))
        self.assertEqual("STOP_CONTRACT_BOUNDARY_REACHED", runner.authorize_in_contract_repair(job, "attempt-02", ["tracked.txt"], "wrong"))

    def test_supervisor_invokes_exact_worker_and_never_constructs_return_or_retries(self):
        job = self.job(); workspace = Path(job["execution_workspace"]); workspace.mkdir()
        job_path = workspace / "job.json"; job_path.write_bytes(runner.canonical_bytes(job))
        evidence = runner.execute_job(job)
        monitor = mock.Mock()
        def worker_once(*args, **kwargs):
            (workspace / "evidence.json").write_bytes(runner.canonical_bytes(evidence))
            return 0, monitor
        with mock.patch.object(runner, "_wait_for_worker_events", side_effect=worker_once) as wait, mock.patch.object(runner, "construct_formal_artifacts") as construct, mock.patch.object(runner, "dispatch_continuation", return_value=runner.DISPATCH_UNKNOWN), mock.patch.object(runner, "_notify_best_effort"):
            runner.supervisor(job_path, job["job_digest"])
        self.assertEqual(1, wait.call_count); construct.assert_not_called()

    def test_worker_start_uses_exact_single_worker_argv_and_isolated_progress_env(self):
        job = self.job(); job_path = Path(job["execution_workspace"]) / "job.json"
        listener = mock.Mock(); listener.getsockname.return_value = ("127.0.0.1", 43210)
        process = mock.Mock(pid=2468)
        holders = []
        with mock.patch.object(runner, "_runner_liveness_binding", return_value=("bound-source", 120)), mock.patch.object(runner.subprocess, "Popen", return_value=process) as popen:
            self.assertIs(process, runner._start_worker(job, job_path, listener, holders))
        argv = popen.call_args.args[0]
        self.assertEqual([sys.executable, "-B", str(Path(runner.__file__).resolve()), "worker", "--job", str(job_path.resolve()), "--job-digest", job["job_digest"]], argv)
        env = popen.call_args.kwargs["env"]
        self.assertEqual("127.0.0.1", env["JOYFLOW_PROGRESS_HOST"])
        self.assertEqual("43210", env["JOYFLOW_PROGRESS_PORT"])
        self.assertEqual(1, len(holders))

    def test_launch_detaches_supervisor_not_worker(self):
        job = self.job(); workspace = Path(job["execution_workspace"]); workspace.mkdir()
        path = workspace / "job.json"; path.write_bytes(runner.canonical_bytes(job))
        with mock.patch.object(runner, "repository_snapshot", return_value=job["expected_before"]), mock.patch.object(runner, "detached_popen_args", return_value={}), mock.patch.object(runner.subprocess, "Popen") as popen:
            runner.launch(path)
        argv = popen.call_args.args[0]
        self.assertIn("supervisor", argv); self.assertNotIn("worker", argv)

    def progress_monitor(self):
        job = self.job(); workspace = Path(job["execution_workspace"]); workspace.mkdir()
        patcher = mock.patch.object(
            runner, "_runner_liveness_binding",
            return_value=("tools/run_test_suite.py:EXECUTION_UNIT_TIMEOUT_SECONDS", 120),
        )
        patcher.start(); self.addCleanup(patcher.stop)
        return job, workspace, runner.ProgressMonitor(job, 101, 202, clock=lambda: 0.0)

    def progress_event(self, job, event_type, **extra):
        return {
            "event_type": event_type,
            "execution_event_id": job["execution_event_id"],
            "attempt_id": job["attempt_id"],
            "job_digest": job["job_digest"],
            "command_index": runner.TEST_COMMAND_INDEX,
            "liveness_bound_source": "tools/run_test_suite.py:EXECUTION_UNIT_TIMEOUT_SECONDS",
            "liveness_bound_value": 120,
            **extra,
        }

    def test_initial_epoch_and_first_real_completion_transition(self):
        job, workspace, monitor = self.progress_monitor()
        started = self.progress_event(job, "test_command_started", test_total=2)
        self.assertTrue(monitor.accept(started, now=10.0))
        self.assertEqual(130.0, monitor.deadline)
        self.assertEqual(runner.ACTIVE_AWAITING_FIRST_PROGRESS, runner._load_json(workspace / runner.STATUS_ARTIFACT)["state"])
        pulse = self.progress_event(job, "test_completed", sequence=1, test_id="tests.x.C.test_a", test_index=1, test_total=2, completed_at="2026-09-09T00:00:00Z")
        self.assertTrue(monitor.accept(pulse, now=20.0))
        status = runner._load_json(workspace / runner.STATUS_ARTIFACT)
        self.assertEqual(runner.ACTIVE_PROGRESSING, status["state"])
        self.assertEqual(1, status["last_accepted_sequence"])
        self.assertEqual(140.0, monitor.deadline)
        self.assertEqual([pulse], [json.loads(line) for line in (workspace / runner.PROGRESS_ARTIFACT).read_text().splitlines()])

    def test_wrong_or_stale_progress_is_ignored_without_rearm(self):
        job, _, monitor = self.progress_monitor()
        self.assertTrue(monitor.accept(self.progress_event(job, "test_command_started", test_total=2), now=0.0))
        valid = self.progress_event(job, "test_completed", sequence=1, test_id="tests.x.C.test_a", test_index=1, test_total=2, completed_at="now")
        self.assertTrue(monitor.accept(valid, now=1.0)); deadline = monitor.deadline
        variants = []
        for key in ("attempt_id", "job_digest"):
            event = dict(valid); event["sequence"] = 2; event[key] = "wrong"; variants.append(event)
        wrong_command = dict(valid); wrong_command.update(sequence=2, command_index=5); variants.append(wrong_command)
        duplicate = dict(valid); variants.append(duplicate)
        for event in variants:
            self.assertFalse(monitor.accept(event, now=50.0))
            self.assertEqual(1, monitor.last_sequence)
            self.assertEqual(deadline, monitor.deadline)

    def test_initial_epoch_expires_once_and_is_nonterminal(self):
        job, workspace, monitor = self.progress_monitor()
        monitor.accept(self.progress_event(job, "test_command_started", test_total=2), now=0.0)
        worker = mock.Mock(); worker.poll.return_value = None
        self.assertTrue(monitor.expire(worker, now=120.0))
        self.assertFalse(monitor.expire(worker, now=1000.0))
        probes = (workspace / runner.PROBE_ARTIFACT).read_text().splitlines()
        self.assertEqual(1, len(probes))
        status = runner._load_json(workspace / runner.STATUS_ARTIFACT)
        self.assertEqual(runner.ACTIVE_NO_RECENT_PROGRESS, status["state"])
        self.assertFalse((workspace / "completed.json").exists())
        self.assertFalse((workspace / "failed.json").exists())

    def test_sequence_epoch_single_probe_and_higher_sequence_recovery(self):
        job, workspace, monitor = self.progress_monitor()
        monitor.accept(self.progress_event(job, "test_command_started", test_total=2), now=0.0)
        first = self.progress_event(job, "test_completed", sequence=1, test_id="tests.x.C.test_a", test_index=1, test_total=2, completed_at="one")
        second = self.progress_event(job, "test_completed", sequence=2, test_id="tests.x.C.test_b", test_index=2, test_total=2, completed_at="two")
        monitor.accept(first, now=1.0)
        worker = mock.Mock(); worker.poll.return_value = None
        self.assertTrue(monitor.expire(worker, now=121.0))
        self.assertFalse(monitor.expire(worker, now=500.0))
        self.assertTrue(monitor.accept(second, now=501.0))
        self.assertEqual(runner.ACTIVE_PROGRESSING, runner._load_json(workspace / runner.STATUS_ARTIFACT)["state"])
        self.assertTrue(monitor.expire(worker, now=621.0))
        self.assertEqual(2, len((workspace / runner.PROBE_ARTIFACT).read_text().splitlines()))

    def test_probe_is_read_only_and_cannot_create_terminal_or_dispatch(self):
        job, workspace, monitor = self.progress_monitor()
        monitor.accept(self.progress_event(job, "test_command_started", test_total=1), now=0.0)
        worker = mock.Mock(); worker.poll.return_value = None
        with mock.patch.object(runner, "dispatch_continuation") as dispatch, mock.patch.object(runner.subprocess, "run") as run, mock.patch.object(runner.subprocess, "Popen") as popen:
            self.assertTrue(monitor.expire(worker, now=120.0))
        dispatch.assert_not_called(); run.assert_not_called(); popen.assert_not_called()
        self.assertEqual(1, worker.poll.call_count)
        self.assertFalse((workspace / "completed.json").exists())
        self.assertFalse((workspace / "failed.json").exists())

    def test_command_capture_preserves_exact_stdout_and_stderr_bytes(self):
        stdout = b"formal-stdout\x00bytes\n"; stderr = b"formal-stderr\xffbytes\n"
        completed = subprocess.CompletedProcess([], 0, stdout=stdout, stderr=stderr)
        command = {"check_id": "CHECK", "argv": [sys.executable, "-c", "pass"], "cwd_scope": "SOURCE_ROOT"}
        observed_object = self.job()["observed_object"]
        with mock.patch.object(runner, "_run_bytes", return_value=completed):
            capture = runner._capture(command, self.repository, "target", observed_object, 1)
        self.assertEqual(stdout, base64.b64decode(capture["stdout_bytes_base64"]))
        self.assertEqual(stderr, base64.b64decode(capture["stderr_bytes_base64"]))
        self.assertEqual(hashlib.sha256(stdout).hexdigest(), capture["stdout_sha256"])
        self.assertEqual(hashlib.sha256(stderr).hexdigest(), capture["stderr_sha256"])

    def test_projection_seal_binds_exact_seven_commands_and_none_publication(self):
        envelope_path = self.base / "envelope.json"
        envelope_path.write_bytes(runner.canonical_bytes({"repository_publication_mode": "NONE"}))
        envelope_digest = hashlib.sha256(envelope_path.read_bytes()).hexdigest()
        current = runner.repository_snapshot(self.repository)
        projection = {
            "projection_digest": None,
            "execution_object": {"physical_object": {"kind": "REPOSITORY_COMMIT", "object_id": "owner/repo", "digest": current["HEAD"]}},
            "decision_boundary": {"repository_binding": {"repository_id": "owner/repo", "working_branch": current["branch"]}, "boundary_obligations": [{"kind": "ALLOW_PATH", "statement": "tracked.txt"}]},
            "task_object_lifecycle": {"authorization_envelope_digest": envelope_digest},
            "validation": {"checks": [
                {"check_id": check_id, "argv": argv, "cwd_scope": "SOURCE_ROOT"}
                for check_id, argv in runner.APPROVED_COMMANDS
            ]},
        }
        projection["projection_digest"] = runner.digest_object(projection, "projection_digest")
        projection_path = self.base / "projection.json"
        projection_path.write_bytes(runner.canonical_bytes(projection))
        sample = self.job()
        approved_path = self.base / "approved.json"
        before_path = self.base / "before.json"
        approved_path.write_bytes(runner.canonical_bytes(sample["turn_a_provenance"]["approved_input_capture"]))
        before_path.write_bytes(runner.canonical_bytes(sample["turn_a_provenance"]["mutation_before_capture"]))
        with mock.patch.object(runner, "_capture_repository_state", return_value=sample["turn_a_provenance"]["mutation_after_capture"]), mock.patch.object(
            runner, "_local_diff_capture", return_value=sample["turn_a_provenance"]["mutation_diff_capture"]
        ), mock.patch.object(runner, "_capture_current_test", return_value=sample["turn_a_provenance"]["targeted_validation_capture"]), mock.patch.object(
            runner, "verify_turn_a_diff", return_value=["tracked.txt"]
        ):
            job, _ = runner.seal_job(
                projection_path, envelope_path, self.repository, self.base / "outside", "sealed-test",
                approved_path, before_path, self.base,
                "event", "attempt", "3" * 64, "continuation", "thread", "thread", "turn",
            )
        self.assertEqual("NONE", job["repository_publication_mode"])
        self.assertEqual([list(item) for item in runner.APPROVED_COMMANDS], [[item["check_id"], item["argv"]] for item in job["commands"]])


if __name__ == "__main__":
    unittest.main()
