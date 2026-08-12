from __future__ import annotations
import pathlib, unittest
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
