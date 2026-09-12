from __future__ import annotations
import io, json, os, pathlib, unittest
from unittest import mock
from tools import run_test_suite as r

class ModuleFirstRunnerTests(unittest.TestCase):
    def _path(self):
        return pathlib.Path('/tmp/test_fake.py')

    @mock.patch.object(r, 'discover_test_ids', return_value=['tests.test_fake.C.test_a','tests.test_fake.C.test_b'])
    @mock.patch.object(r, 'run_batches')
    @mock.patch.object(r, '_run_unittest', return_value=(0,2,'module-out',''))
    def test_module_success_skips_batch_fallback(self, _run, batches, _discover):
        result=r.run_module(self._path())
        self.assertEqual(result[1:3], (0,2)); batches.assert_not_called()

    @mock.patch.object(r, 'discover_test_ids', return_value=['tests.test_fake.C.test_a','tests.test_fake.C.test_b'])
    @mock.patch.object(r, 'run_batches', return_value=(0,2,'batch-out',''))
    @mock.patch.object(r, '_run_unittest', return_value=(1,2,'module-out','module-fail'))
    def test_module_failure_falls_back_but_remains_failed(self, _run, batches, _discover):
        result=r.run_module(self._path())
        self.assertNotEqual(result[1],0); batches.assert_called_once()

    @mock.patch.object(r, 'discover_test_ids', return_value=['tests.test_fake.C.test_a','tests.test_fake.C.test_b'])
    @mock.patch.object(r, 'run_batches')
    @mock.patch.object(r, 'run_methods', return_value=(0,2,'method-out',''))
    @mock.patch.object(r, '_run_unittest', return_value=(124,0,'','timeout'))
    def test_module_timeout_no_larger_than_batch_goes_directly_to_methods(self, _run, methods, batches, _discover):
        result=r.run_module(self._path())
        self.assertEqual(result[1:3], (0,2)); batches.assert_not_called()
        methods.assert_called_once_with('tests.test_fake', ['tests.test_fake.C.test_a','tests.test_fake.C.test_b'], 'MODULE_TIMEOUT_METHOD_FALLBACK')

    @mock.patch.object(r, 'discover_test_ids', return_value=['tests.test_fake.C.test_a','tests.test_fake.C.test_b'])
    @mock.patch.object(r, 'run_batches', return_value=(0,2,'batch-out',''))
    @mock.patch.object(r, '_run_unittest', return_value=(0,1,'module-out',''))
    def test_count_mismatch_requires_exact_batch_coverage(self, _run, batches, _discover):
        result=r.run_module(self._path())
        self.assertEqual(result[1:3], (0,2)); batches.assert_called_once()

class AdaptiveLargeModuleRunnerTests(unittest.TestCase):
    @mock.patch.object(r, 'discover_test_ids', return_value=[f'tests.test_fake.C.test_{i}' for i in range(13)])
    @mock.patch.object(r, 'run_batches', return_value=(0,13,'batch-out',''))
    @mock.patch.object(r, '_run_unittest')
    def test_large_module_uses_existing_batch_path_without_module_timeout_attempt(self, module_run, batches, _discover):
        result=r.run_module(pathlib.Path('/tmp/test_fake.py'))
        self.assertEqual(result[1:3], (0,13))
        batches.assert_called_once(); module_run.assert_not_called()

    @mock.patch.object(r, 'discover_test_ids', return_value=[f'tests.test_fake.C.test_{i}' for i in range(13)])
    @mock.patch.object(r, '_run_unittest')
    def test_large_module_batch_timeout_recovers_through_methods(self, unit_run, _discover):
        unit_run.side_effect=[(124,0,'','batch-timeout')]+[(0,1,'','') for _ in range(8)]+[(0,5,'','')]
        result=r.run_module(pathlib.Path('/tmp/test_fake.py'))
        self.assertEqual(result[1:3], (0,13))
        self.assertEqual(unit_run.call_count,10)
        self.assertEqual(unit_run.call_args_list[0].args[1], [f'tests.test_fake.C.test_{i}' for i in range(8)])
        self.assertEqual(unit_run.call_args_list[-1].args[1], [f'tests.test_fake.C.test_{i}' for i in range(8,13)])


class TerminalMethodFallbackTests(unittest.TestCase):
    def setUp(self):
        self.module='tests.test_fake'
        self.ids=['tests.test_fake.C.test_a','tests.test_fake.C.test_b']

    @mock.patch.object(r, '_run_unittest')
    def test_batch_timeout_methods_all_pass_recovers(self, unit_run):
        unit_run.side_effect=[(124,0,'batch-out','batch-timeout'),(0,1,'a-out',''),(0,1,'b-out','')]
        result=r.run_batch(self.module,1,self.ids)
        self.assertEqual(result[0:2],(0,2)); self.assertEqual(unit_run.call_count,3)
        self.assertIn('BATCH_TIMEOUT_METHOD_FALLBACK',result[3])

    @mock.patch.object(r, '_run_unittest')
    def test_batch_timeout_method_failure_remains_failed(self, unit_run):
        unit_run.side_effect=[(124,0,'','batch-timeout'),(0,1,'',''),(1,1,'','method-fail')]
        result=r.run_batch(self.module,1,self.ids)
        self.assertEqual(result[0:2],(1,2)); self.assertEqual(unit_run.call_count,3)
        self.assertIn(self.ids[1],result[3])

    @mock.patch.object(r, '_run_unittest', return_value=(124,0,'','method-timeout'))
    def test_individual_method_timeout_is_terminal(self, unit_run):
        result=r.run_methods(self.module,self.ids,'TEST_METHOD_FALLBACK')
        self.assertEqual(result[0:2],(124,0)); unit_run.assert_called_once()

    @mock.patch.object(r, '_run_unittest', return_value=(0,0,'',''))
    def test_method_count_mismatch_blocks(self, unit_run):
        result=r.run_methods(self.module,[self.ids[0]],'TEST_METHOD_FALLBACK')
        self.assertEqual(result[0:2],(2,0)); unit_run.assert_called_once()

    @mock.patch.object(r, '_run_unittest', return_value=(0,1,'',''))
    def test_batch_exact_count_mismatch_blocks(self, unit_run):
        result=r.run_batches(self.module,self.ids)
        self.assertEqual(result[0:2],(2,1)); unit_run.assert_called_once()


class ProgressPulseRunnerTests(unittest.TestCase):
    def test_actual_test_completion_emits_exactly_one_pulse_each(self):
        class ActualCases(unittest.TestCase):
            def test_one(self):
                self.assertTrue(True)
            def test_two(self):
                self.assertEqual(2, 1 + 1)
        stream = io.StringIO()
        with mock.patch.object(r, "emit_test_completed") as emit:
            result = unittest.TextTestRunner(
                stream=stream, verbosity=0, resultclass=r.ProgressTextTestResult,
            ).run(unittest.defaultTestLoader.loadTestsFromTestCase(ActualCases))
        self.assertTrue(result.wasSuccessful())
        self.assertEqual(2, emit.call_count)
        self.assertEqual(
            [test.id() for test in unittest.defaultTestLoader.loadTestsFromTestCase(ActualCases)],
            [call.args[0] for call in emit.call_args_list],
        )

    def test_emitted_events_have_real_index_total_and_monotonic_sequence(self):
        ids = ["tests.fake.C.test_one", "tests.fake.C.test_two"]
        binding = {
            "execution_event_id": "event", "attempt_id": "attempt", "job_digest": "a" * 64,
            "command_index": 6,
        }
        accepted = []
        def request(message):
            if message["event_type"] == "sequence_request":
                return {"accepted": True, "next_sequence": len(accepted) + 1}
            accepted.append(message)
            return {"accepted": True}
        env = {
            r.PROGRESS_BINDING_ENV: json.dumps(binding),
            r.PROGRESS_INDEX_MAP_ENV: json.dumps({ids[0]: 11, ids[1]: 12}),
            r.PROGRESS_TOTAL_ENV: "524",
        }
        with mock.patch.dict(os.environ, env, clear=False), mock.patch.object(r, "_progress_request", side_effect=request):
            r.emit_test_completed(ids[0]); r.emit_test_completed(ids[1])
        self.assertEqual([1, 2], [event["sequence"] for event in accepted])
        self.assertEqual([11, 12], [event["test_index"] for event in accepted])
        self.assertEqual([524, 524], [event["test_total"] for event in accepted])
        self.assertEqual(ids, [event["test_id"] for event in accepted])
        self.assertTrue(all(event["liveness_bound_value"] == r.EXECUTION_UNIT_TIMEOUT_SECONDS for event in accepted))

    def test_direct_runner_without_machine_context_does_not_open_control_channel(self):
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(r.socket, "create_connection") as connect:
            r.announce_test_command_started(3)
            r.emit_test_completed("tests.fake.C.test_one")
        connect.assert_not_called()

    def test_liveness_bound_has_one_authoritative_definition(self):
        self.assertEqual(120, r.EXECUTION_UNIT_TIMEOUT_SECONDS)
        self.assertEqual(r.EXECUTION_UNIT_TIMEOUT_SECONDS, r.MODULE_TIMEOUT_SECONDS)
        self.assertEqual(r.EXECUTION_UNIT_TIMEOUT_SECONDS, r.BATCH_TIMEOUT_SECONDS)
