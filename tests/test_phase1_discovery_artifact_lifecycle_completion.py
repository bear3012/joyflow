from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))

from runtime import joyflow_dual_layer as c
import build_fixture as f
import test_phase1_source_replay_grounding as replay
import test_phase1_evidence_content_binding as evidence_binding
from tests.platform_capabilities import probe_symlink_capability


class DiscoveryArtifactLifecycleCompletionTests(unittest.TestCase):
    def setUp(self):
        self.h = replay.SourceReplayGrounding()
        self.eb = evidence_binding.EvidenceContentBinding()

    def _refresh_bundle_and_return(self, bundle, ret):
        self.h.refresh_bundle(bundle)
        ret['evidence_bundle_digest'] = bundle['evidence_bundle_digest']
        ret['return_digest'] = c.digest(c.strip_digest(ret, 'return_digest'))

    def _actualize_local_execution_state(self, state, repo, base):
        state = copy.deepcopy(state)
        state['task_anchor']['repository_anchor']['baseline_commit'] = base
        state['active_fibers']['decision_boundary']['payload']['repository_binding']['expected_base_commit'] = base
        repo_payload = state['active_fibers']['repository_evidence']['payload']
        repo_payload['baseline_commit'] = base
        pd = repo_payload['path_discovery']
        pd['github_ref'] = f'github:example/repo@{base}'
        pd['final_path_decision']['baseline_commit'] = base
        for row in pd['github_path_evidence']:
            row['object_ref'] = f'github:example/repo@{base}'
            row['observed_commit_or_head'] = base
            row['scope']['raw_object_sha256'] = hashlib.sha256(c.canonical_bytes(c._github_source_capture_payload(row, repo))).hexdigest()
            row['scope']['scope_digest'] = c.digest(c._github_scope_payload(row))
            row['evidence_digest'] = c.digest(c.strip_digest(row, 'evidence_digest'))
            source = next(x for x in state['evidence_registry'] if x['evidence_id'] == row['raw_evidence_ref'].split(':')[-1]) if False else None
        # The standard fixture uses E_GITHUB_PATHS for the typed path evidence.
        typed = pd['github_path_evidence'][0]
        source = next(x for x in state['evidence_registry'] if x['evidence_id'] == 'E_GITHUB_PATHS')
        source.update({
            'ref': typed['raw_evidence_ref'],
            'raw_output_ref': typed['raw_evidence_ref'],
            'raw_output_sha256': typed['scope']['raw_object_sha256'],
            'subject_id': typed['object_ref'],
            'claim': c._github_scope_claim(typed),
        })
        source['claim_digest'] = c.digest(source['claim'])
        pd['final_path_decision']['decision_digest'] = c.digest(c.strip_digest(pd['final_path_decision'], 'decision_digest'))
        return f.refresh(state)

    def _approve_local_execution(self, state, discovery_projection, discovery_return):
        current = c.prepare_capsule_structural_fixture(
            state,
            path_discovery_projection=discovery_projection,
            path_discovery_return=discovery_return,
        )
        if current['task_progress']['stage'] in {'INTENT_DISCUSSION', 'REPOSITORY_DISCOVERY'}:
            current = f.advance(current, 'DECISION_CLOSURE')
        if current['task_progress']['stage'] != 'USER_APPROVAL':
            current = f.advance(current, 'USER_APPROVAL')
        projection, _, binding = c.draft_handoff(current)
        current = copy.deepcopy(current)
        current['approval_record'] = {
            'status': 'APPROVED_FINAL',
            'owner': 'WEB_BRAIN',
            'scope': c.expected_approval_scope(current),
            'basis': 'CURRENT_EXPLICIT_USER_DECISION',
            'decision_ref': 'conversation:test-local-discovery-execution-approval',
            'binding': binding,
        }
        current['derived_gates'] = c.compute_gate_snapshot(current)
        c.validate_capsule(current)
        return current, projection

    def test_local_discovery_source_object_transitions_into_execution_projection(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base, _ = self.h.repo(td, second_commit=False)
            discovery_projection, discovery_return = self.h.actualize_discovery(repo, base)
            state = self.eb.local_state(discovery_projection, discovery_return)
            state = self._actualize_local_execution_state(state, repo, base)
            _, execution_projection = self._approve_local_execution(state, discovery_projection, discovery_return)
            source = execution_projection['task_object_lifecycle']['discovery_object']['discovery_source_object']
            self.assertEqual(source['discovery_projection_digest'], discovery_projection['projection_digest'])
            self.assertEqual(source['path_discovery_return_digest'], discovery_return['return_digest'])
            self.assertEqual(source['selected_item_ids']['path_ids'], ['LOCAL_PATH_RUNTIME'])
            c.validate_execution_projection_sources(
                execution_projection,
                repository=repo,
                path_discovery_projection=discovery_projection,
                path_discovery_return=discovery_return,
            )

    def test_local_discovery_source_object_rejects_other_projection(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base, _ = self.h.repo(td, second_commit=False)
            discovery_projection, discovery_return = self.h.actualize_discovery(repo, base)
            state = self._actualize_local_execution_state(self.eb.local_state(discovery_projection, discovery_return), repo, base)
            _, execution_projection = self._approve_local_execution(state, discovery_projection, discovery_return)
            other = copy.deepcopy(discovery_projection)
            other['projection_digest'] = 'f' * 64
            with self.assertRaises(c.JoyflowError):
                c.validate_execution_projection_sources(
                    execution_projection,
                    repository=repo,
                    path_discovery_projection=other,
                    path_discovery_return=discovery_return,
                )

    def test_local_discovery_source_object_rejects_unselected_item_substitution(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base, _ = self.h.repo(td, second_commit=False)
            discovery_projection, discovery_return = self.h.actualize_discovery(repo, base)
            state = self._actualize_local_execution_state(self.eb.local_state(discovery_projection, discovery_return), repo, base)
            _, execution_projection = self._approve_local_execution(state, discovery_projection, discovery_return)
            source = execution_projection['task_object_lifecycle']['discovery_object']['discovery_source_object']
            source['selected_item_ids'] = ['LOCAL_CANDIDATE_TEST']
            source['source_digest'] = c.digest(c.strip_digest(source, 'source_digest'))
            execution_projection['task_object_lifecycle']['discovery_object']['discovery_digest'] = c.digest(
                c.strip_digest(execution_projection['task_object_lifecycle']['discovery_object'], 'discovery_digest')
            )
            execution_projection['task_object_lifecycle']['lifecycle_digest'] = c.digest(
                c.strip_digest(execution_projection['task_object_lifecycle'], 'lifecycle_digest')
            )
            execution_projection['projection_digest'] = c.digest(c.projection_payload(execution_projection))
            with self.assertRaises(c.JoyflowError):
                c.validate_execution_projection_sources(
                    execution_projection,
                    repository=repo,
                    path_discovery_projection=discovery_projection,
                    path_discovery_return=discovery_return,
                )

    def test_exact_ignored_symlink_is_captured_without_following_target(self):
        capability = probe_symlink_capability()
        if not capability['supported']:
            print('PLATFORM_CAPABILITY_NA ' + repr(capability))
            return
        with tempfile.TemporaryDirectory() as td:
            repo, _, _ = self.h.repo(td, second_commit=False)
            (repo / '.gitignore').write_text('current.cfg\ntarget.cfg\n', encoding='utf-8')
            subprocess.run(['git', '-C', str(repo), 'add', '.gitignore'], check=True)
            subprocess.run(['git', '-C', str(repo), 'commit', '-m', 'ignore local config'], check=True, capture_output=True)
            (repo / 'target.cfg').write_text('SECRET-TARGET-CONTENT\n', encoding='utf-8')
            (repo / 'current.cfg').symlink_to('target.cfg')
            coverage = {
                'mode': 'DECLARED_EXECUTION_RELEVANT_ONLY',
                'exact_files': [],
                'exact_symlinks': ['current.cfg'],
                'recursive_directories': [],
                'coverage_status': 'COMPLETE_FOR_DECLARED_EXECUTION_RELEVANT_PATHS',
                'full_local_filesystem_unchanged_claim': False,
            }
            rows = json.loads(c._declared_ignored_manifest(repo, coverage))
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row['kind'], 'SYMLINK')
            self.assertEqual(row['path'], 'current.cfg')
            self.assertEqual(row['link_target'], 'target.cfg')
            self.assertFalse(row['target_followed'])
            self.assertNotIn('SECRET-TARGET-CONTENT', json.dumps(row))

    def test_recursive_ignored_exclusion_prunes_descendants(self):
        with tempfile.TemporaryDirectory() as td:
            repo, _, _ = self.h.repo(td, second_commit=False)
            (repo / '.gitignore').write_text('local/\n', encoding='utf-8')
            subprocess.run(['git', '-C', str(repo), 'add', '.gitignore'], check=True)
            subprocess.run(['git', '-C', str(repo), 'commit', '-m', 'ignore local tree'], check=True, capture_output=True)
            (repo / 'local' / 'allowed').mkdir(parents=True)
            (repo / 'local' / 'secret').mkdir(parents=True)
            (repo / 'local' / 'allowed' / 'visible.cfg').write_text('VISIBLE\n', encoding='utf-8')
            (repo / 'local' / 'secret' / 'token.txt').write_text('SENTINEL-DO-NOT-READ\n', encoding='utf-8')
            coverage = {
                'mode': 'DECLARED_EXECUTION_RELEVANT_ONLY',
                'exact_files': [],
                'exact_symlinks': [],
                'recursive_directories': [{'root': 'local', 'exclusions': ['secret']}],
                'coverage_status': 'COMPLETE_FOR_DECLARED_EXECUTION_RELEVANT_PATHS',
                'full_local_filesystem_unchanged_claim': False,
            }
            rows = json.loads(c._declared_ignored_manifest(repo, coverage))
            paths = [r['path'] for r in rows]
            self.assertIn('local/allowed/visible.cfg', paths)
            self.assertFalse(any(p == 'local/secret' or p.startswith('local/secret/') for p in paths))
            self.assertNotIn('SENTINEL-DO-NOT-READ', json.dumps(rows))

    def test_declared_ignored_file_can_be_a_direct_path_fact(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base, _ = self.h.repo(td, second_commit=False)
            (repo / '.gitignore').write_text('ignored.cfg\n', encoding='utf-8')
            subprocess.run(['git', '-C', str(repo), 'add', '.gitignore'], check=True)
            subprocess.run(['git', '-C', str(repo), 'commit', '-m', 'ignore runtime config'], check=True, capture_output=True)
            base = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
            (repo / 'ignored.cfg').write_text('LOCAL=1\n', encoding='utf-8')
            projection, ret = self.h.actualize_discovery(repo, base)
            ret['ignored_path_coverage'] = {
                'mode': 'DECLARED_EXECUTION_RELEVANT_ONLY',
                'exact_files': ['ignored.cfg'],
                'exact_symlinks': [],
                'recursive_directories': [],
                'coverage_status': 'COMPLETE_FOR_DECLARED_EXECUTION_RELEVANT_PATHS',
                'full_local_filesystem_unchanged_claim': False,
            }
            components = c._source_worktree_components(repo, ret['ignored_path_coverage'])
            for key, phase, eid in [('repository_state_before', 'BEFORE', 'DISC_STATE_BEFORE'), ('repository_state_after', 'AFTER', 'DISC_STATE_AFTER')]:
                row = ret[key]
                row.update(components)
                row['capture_phase'] = phase
                row['evidence_ref'] = eid
                row['state_fingerprint_sha256'] = c.digest(c._state_fingerprint_payload(row))
                row['capture_record_digest'] = c.digest(c._capture_record_payload(row))
            evs = {x['evidence_id']: x for x in ret['evidence_rows']}
            for key in ('repository_state_before', 'repository_state_after'):
                row = ret[key]
                evs[row['evidence_ref']]['claim'] = c._git_state_claim(row)
                evs[row['evidence_ref']]['claim_digest'] = c.digest(evs[row['evidence_ref']]['claim'])
            ret['confirmed_paths'][0]['path'] = 'ignored.cfg'
            ret['candidate_paths'] = []
            ret['dependency_edges'] = []
            ret['validation_entries'] = []
            ret['local_only_findings'] = []
            ev = evs['DISC_OBS_RUNTIME']
            ev['observed_path'] = 'ignored.cfg'
            ev['claim'] = c._path_observation_claim(ret['confirmed_paths'][0]['path_id'], 'ignored.cfg')
            ev['claim_digest'] = c.digest(ev['claim'])
            ret['return_digest'] = c.digest(c.strip_digest(ret, 'return_digest'))
            c.validate_path_discovery_return(ret, projection, repository=repo)

    def _approved_artifact_capsule(self, source, argv, *, extra_check=False):
        state = f.new_capsule('ARTIFACT_REPAIR', 'ARTIFACT_CHANGE')
        sha = hashlib.sha256(source.read_bytes()).hexdigest()
        state['task_anchor']['artifact_anchor'].update({'artifact_id': source.name, 'artifact_sha256': sha})
        validation = state['active_fibers']['validation']['payload']
        validation['checks'][0].update({'argv': copy.deepcopy(argv), 'command': c._canonical_argv(argv), 'cwd_scope': 'SOURCE_ROOT'})
        if extra_check:
            second = copy.deepcopy(validation['checks'][0])
            second['check_id'] = 'CHECK_SECOND_OUTPUT'
            validation['checks'].append(second)
            for item in c.semantic_items(state):
                for effect in item.get('effects', []):
                    if effect.get('effect_type') == 'VALIDATE':
                        effect.setdefault('check_ids', []).append('CHECK_SECOND_OUTPUT')
                        extra_check = False
                        break
                if extra_check is False:
                    break
        state = f.refresh(state)
        current = c.prepare_capsule_structural_fixture(state)
        if current['task_progress']['stage'] in {'INTENT_DISCUSSION', 'REPOSITORY_DISCOVERY'}:
            current = f.advance(current, 'DECISION_CLOSURE')
        if current['task_progress']['stage'] != 'USER_APPROVAL':
            current = f.advance(current, 'USER_APPROVAL')
        projection, _, binding = c.draft_handoff(current)
        current = copy.deepcopy(current)
        current['approval_record'] = {'status': 'APPROVED_FINAL', 'owner': 'WEB_BRAIN', 'scope': c.expected_approval_scope(current), 'basis': 'CURRENT_EXPLICIT_USER_DECISION', 'decision_ref': 'conversation:test-two-output-approval', 'binding': binding}
        current['derived_gates'] = c.compute_gate_snapshot(current)
        c.validate_capsule(current)
        return current, projection

    def _actual_two_output_artifact_return(self, td):
        td = pathlib.Path(td)
        source_root = td / 'source'; source_root.mkdir()
        output_root = td / 'outputs'; output_root.mkdir()
        source = source_root / 'source-artifact.zip'; source.write_bytes(b'approved source')
        primary = output_root / 'primary.zip'; primary.write_bytes(b'primary output')
        secondary = output_root / 'manifest.json'; secondary.write_text('{"ok":true}\n', encoding='utf-8')
        argv = [sys.executable, '-c', 'print("artifact validation pass")']
        approved, projection = self._approved_artifact_capsule(source, argv, extra_check=True)
        ret, bundle = f.codex_return(projection)
        source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        primary_sha = hashlib.sha256(primary.read_bytes()).hexdigest()
        secondary_sha = hashlib.sha256(secondary.read_bytes()).hexdigest()
        input_obj = {'object_type': 'ARTIFACT', 'source_mode': 'EXISTING_ARTIFACT', 'object_id': source.name, 'ref_or_sha256': source_sha}
        primary_obj = {'object_type': 'ARTIFACT', 'source_mode': 'NEW_ARTIFACT', 'object_id': primary.name, 'ref_or_sha256': primary_sha}
        secondary_obj = {'object_type': 'ARTIFACT', 'source_mode': 'NEW_ARTIFACT', 'object_id': secondary.name, 'ref_or_sha256': secondary_sha}
        proc = subprocess.run(argv, cwd=output_root, capture_output=True)
        for cap in bundle['raw_captures']:
            if cap['capture_kind'] == 'ARTIFACT_SHA256':
                is_output = cap['capture_id'] == 'CAP_EXEC_ARTIFACT'
                path = primary if is_output else source
                obj = primary_obj if is_output else input_obj
                cap.update({'command': f'sha256 {path}', 'exit_code': 0, 'stdout': '', 'stderr': '', 'observed_object': copy.deepcopy(obj), 'observation': {'artifact_id': path.name, 'artifact_path': str(path.resolve()), 'artifact_sha256': obj['ref_or_sha256'], 'bytes': path.stat().st_size}})
                if is_output:
                    cap['subject_type'] = 'ARTIFACT'; cap['subject_id'] = primary_sha
            elif cap['capture_kind'] == 'TEST_COMMAND':
                final = cap['subject_type'] == 'VALIDATION_CHECK'
                is_secondary = final and cap['subject_id'].endswith(':CHECK_SECOND_OUTPUT')
                obj = secondary_obj if is_secondary else (primary_obj if final else input_obj)
                cap.update({'command': c._canonical_argv(cap['observation']['argv']), 'exit_code': proc.returncode, 'stdout': proc.stdout.decode(), 'stderr': proc.stderr.decode(), 'observed_object': copy.deepcopy(obj), 'observation': {'argv': cap['observation']['argv'], 'cwd_scope': 'SOURCE_ROOT', 'target_ref': obj['ref_or_sha256']}})
        primary_row = ret['artifact_evidence']['outputs'][0]
        primary_row.update({'artifact_id': primary.name, 'artifact_digest': primary_sha, 'bytes': primary.stat().st_size, 'media_type': 'application/zip', 'role': 'PRIMARY'})
        secondary_test_ref = next(r['evidence_ref'] for r in ret['machine_results'] if r['check_id'] == 'CHECK_SECOND_OUTPUT')
        primary_row['validation_evidence_refs'] = [x for x in primary_row['validation_evidence_refs'] if x != secondary_test_ref]
        secondary_digest_cap = copy.deepcopy(next(x for x in bundle['raw_captures'] if x['capture_id'] == 'CAP_EXEC_ARTIFACT'))
        secondary_digest_cap.update({'capture_id': 'CAP_EXEC_ARTIFACT_SECONDARY', 'command': f'sha256 {secondary}', 'stdout': '', 'observed_object': copy.deepcopy(secondary_obj), 'observation': {'artifact_id': secondary.name, 'artifact_path': str(secondary.resolve()), 'artifact_sha256': secondary_sha, 'bytes': secondary.stat().st_size}, 'subject_id': secondary_sha})
        bundle['raw_captures'].append(secondary_digest_cap)
        secondary_ev = copy.deepcopy(next(x for x in bundle['evidence_rows'] if x['evidence_id'] == 'EXEC_ARTIFACT'))
        secondary_ev.update({'evidence_id': 'EXEC_ARTIFACT_SECONDARY', 'ref': secondary_digest_cap['capture_id'], 'raw_output_ref': secondary_digest_cap['capture_id'], 'subject_id': secondary_sha})
        bundle['evidence_rows'].append(secondary_ev)
        secondary_row = {'artifact_id': secondary.name, 'artifact_digest': secondary_sha, 'bytes': secondary.stat().st_size, 'media_type': 'application/json', 'role': 'MANIFEST', 'validation_evidence_refs': ['EXEC_ARTIFACT_SECONDARY', secondary_test_ref]}
        ret['artifact_evidence']['outputs'] = sorted([primary_row, secondary_row], key=lambda row: row['artifact_id'])
        ret['artifact_evidence']['output_set_digest'] = c._artifact_output_set_digest(ret['artifact_evidence']['outputs'])
        outputs = c._canonical_artifact_outputs(ret['artifact_evidence']['outputs'])
        refs = sorted({ref for row in ret['artifact_evidence']['outputs'] for ref in row['validation_evidence_refs']})
        coverage = sorted([{'artifact_id': row['artifact_id'], 'validation_evidence_refs': sorted(row['validation_evidence_refs'])} for row in ret['artifact_evidence']['outputs']], key=lambda r: r['artifact_id'])
        lr = ret['execution_lifecycle_result']
        lr['execution_result_object'] = {'result_type': 'ARTIFACT_OUTPUT_SET', 'outputs': outputs, 'output_set_digest': ret['artifact_evidence']['output_set_digest']}
        lr['final_validation_object'] = {'target_type': 'ARTIFACT_OUTPUT_SET', 'target_digest': ret['artifact_evidence']['output_set_digest'], 'validation_environment': 'EXACT_OUTPUT_FILES', 'machine_result_evidence_refs': sorted({x['evidence_ref'] for x in ret['machine_results']}), 'artifact_validation_evidence_refs': refs, 'output_validation_coverage': coverage, 'uncovered_output_ids': []}
        lr['transition_digest'] = c.execution_lifecycle_result_digest(lr)
        out_ev = next(x for x in bundle['evidence_rows'] if x['evidence_id'] == 'EXEC_ARTIFACT')
        out_ev['subject_id'] = primary_sha
        ret['technical_preflight']['expected_execution_object'] = copy.deepcopy(input_obj)
        ret['technical_preflight']['observed_execution_object'] = copy.deepcopy(input_obj)
        self._refresh_bundle_and_return(bundle, ret)
        return approved, source, [primary, secondary], projection, ret, bundle

    def test_artifact_complete_two_output_set_passes_return_and_review(self):
        with tempfile.TemporaryDirectory() as td:
            approved, source, outputs, projection, ret, bundle = self._actual_two_output_artifact_return(td)
            c.validate_codex_execution_return(ret, projection, bundle, artifact=source, artifact_outputs=outputs, artifact_output_root=outputs[0].parent)
            executing = f.advance(approved, 'CODEX_EXECUTION')
            fixture_review = f.brain_review_capsule(executing, projection, ret, bundle)
            review = c.prepare_artifact_review_capsule(fixture_review, executing, review_projection=projection, codex_return=ret, evidence_bundle=bundle, source_artifact=source, artifact_outputs=outputs, artifact_output_root=outputs[0].parent)
            target = review['active_fibers']['execution_review']['payload']['review_target']
            self.assertEqual([x['artifact_id'] for x in target['outputs']], sorted(p.name for p in outputs))

    def test_artifact_complete_output_set_rejects_missing_or_extra_output(self):
        with tempfile.TemporaryDirectory() as td:
            _, source, outputs, projection, ret, bundle = self._actual_two_output_artifact_return(td)
            with self.assertRaises(c.JoyflowError):
                c.validate_codex_execution_return(ret, projection, bundle, artifact=source, artifact_outputs=[outputs[0]], artifact_output_root=outputs[0].parent)
            extra = outputs[0].parent / 'extra.bin'; extra.write_bytes(b'extra')
            with self.assertRaises(c.JoyflowError):
                c.validate_codex_execution_return(ret, projection, bundle, artifact=source, artifact_outputs=outputs + [extra], artifact_output_root=outputs[0].parent)

    def _actual_new_artifact_return(self, td):
        td = pathlib.Path(td)
        source_root = td / 'source'; source_root.mkdir()
        output_root = td / 'outputs'; output_root.mkdir()
        material = source_root / 'spec.txt'; material.write_text('approved source material\n', encoding='utf-8')
        output = output_root / 'new-package.zip'; output.write_bytes(b'new artifact bytes')
        material_sha = hashlib.sha256(material.read_bytes()).hexdigest()
        output_sha = hashlib.sha256(output.read_bytes()).hexdigest()
        argv = [sys.executable, '-c', 'print("new artifact validation pass")']
        state = f.new_capsule('ARTIFACT_REPAIR', 'ARTIFACT_CHANGE')
        state['task_anchor']['artifact_anchor'].update({'source_mode': 'NEW_ARTIFACT', 'artifact_id': None, 'artifact_sha256': None, 'source_material_refs': ['E_COLD_REVIEW'], 'source_materials': [{'material_id': 'SPEC', 'material_digest': material_sha, 'source_ref': 'E_COLD_REVIEW'}]})
        check = state['active_fibers']['validation']['payload']['checks'][0]
        check.update({'argv': argv, 'command': c._canonical_argv(argv), 'cwd_scope': 'SOURCE_ROOT'})
        state = f.refresh(state)
        current = c.prepare_capsule_structural_fixture(state)
        if current['task_progress']['stage'] in {'INTENT_DISCUSSION', 'REPOSITORY_DISCOVERY'}:
            current = f.advance(current, 'DECISION_CLOSURE')
        if current['task_progress']['stage'] != 'USER_APPROVAL':
            current = f.advance(current, 'USER_APPROVAL')
        projection, _, binding = c.draft_handoff(current)
        current = copy.deepcopy(current)
        current['approval_record'] = {'status': 'APPROVED_FINAL', 'owner': 'WEB_BRAIN', 'scope': c.expected_approval_scope(current), 'basis': 'CURRENT_EXPLICIT_USER_DECISION', 'decision_ref': 'conversation:test-new-artifact-approval', 'binding': binding}
        current['derived_gates'] = c.compute_gate_snapshot(current)
        c.validate_capsule(current)
        ret, bundle = f.codex_return(projection)
        source_obj = c._return_object_shape(projection['execution_object'])
        output_obj = {'object_type': 'ARTIFACT', 'source_mode': 'NEW_ARTIFACT', 'object_id': output.name, 'ref_or_sha256': output_sha}
        proc = subprocess.run(argv, cwd=output_root, capture_output=True)
        for cap in bundle['raw_captures']:
            if cap['capture_kind'] == 'SOURCE_MATERIAL_SET':
                materials = projection['task_object_lifecycle']['approved_input_object']['source_materials']
                cap.update({'command': 'source-material-set', 'exit_code': 0, 'stdout': projection['execution_object']['expected_ref_or_sha256'] + '\n', 'stderr': '', 'observed_object': copy.deepcopy(source_obj), 'observation': {'materials': materials, 'source_material_set_digest': projection['execution_object']['expected_ref_or_sha256']}})
            elif cap['capture_kind'] == 'ARTIFACT_SHA256':
                cap.update({'command': f'sha256 {output}', 'exit_code': 0, 'stdout': '', 'stderr': '', 'observed_object': copy.deepcopy(output_obj), 'observation': {'artifact_id': output.name, 'artifact_path': str(output.resolve()), 'artifact_sha256': output_sha, 'bytes': output.stat().st_size}, 'subject_type': 'ARTIFACT', 'subject_id': output_sha})
            elif cap['capture_kind'] == 'TEST_COMMAND':
                final = cap['subject_type'] == 'VALIDATION_CHECK'
                obj = output_obj if final else source_obj
                cap.update({'command': c._canonical_argv(cap['observation']['argv']), 'exit_code': proc.returncode, 'stdout': proc.stdout.decode(), 'stderr': proc.stderr.decode(), 'observed_object': copy.deepcopy(obj), 'observation': {'argv': cap['observation']['argv'], 'cwd_scope': 'SOURCE_ROOT', 'target_ref': obj['ref_or_sha256']}})
        ret['technical_preflight']['expected_execution_object'] = copy.deepcopy(source_obj)
        ret['technical_preflight']['observed_execution_object'] = copy.deepcopy(source_obj)
        row = ret['artifact_evidence']['outputs'][0]
        row.update({'artifact_id': output.name, 'artifact_digest': output_sha, 'bytes': output.stat().st_size, 'media_type': 'application/zip', 'role': 'PRIMARY'})
        ret['artifact_evidence']['output_set_digest'] = c._artifact_output_set_digest(ret['artifact_evidence']['outputs'])
        refs = sorted(row['validation_evidence_refs'])
        lr = ret['execution_lifecycle_result']
        lr['execution_result_object'] = {'result_type': 'ARTIFACT_OUTPUT_SET', 'outputs': c._canonical_artifact_outputs(ret['artifact_evidence']['outputs']), 'output_set_digest': ret['artifact_evidence']['output_set_digest']}
        lr['final_validation_object'] = {'target_type': 'ARTIFACT_OUTPUT_SET', 'target_digest': ret['artifact_evidence']['output_set_digest'], 'validation_environment': 'EXACT_OUTPUT_FILES', 'machine_result_evidence_refs': sorted({x['evidence_ref'] for x in ret['machine_results']}), 'artifact_validation_evidence_refs': refs, 'output_validation_coverage': [{'artifact_id': output.name, 'validation_evidence_refs': refs}], 'uncovered_output_ids': []}
        lr['transition_digest'] = c.execution_lifecycle_result_digest(lr)
        next(x for x in bundle['evidence_rows'] if x['evidence_id'] == 'EXEC_ARTIFACT')['subject_id'] = output_sha
        self._refresh_bundle_and_return(bundle, ret)
        return current, {'SPEC': material}, output, projection, ret, bundle

    def test_new_artifact_source_material_set_closes_formal_review(self):
        with tempfile.TemporaryDirectory() as td:
            approved, materials, output, projection, ret, bundle = self._actual_new_artifact_return(td)
            c.validate_codex_execution_return(ret, projection, bundle, source_materials=materials, artifact_outputs=[output],artifact_output_root=output.parent)
            executing = f.advance(approved, 'CODEX_EXECUTION')
            fixture_review = f.brain_review_capsule(executing, projection, ret, bundle)
            review = c.prepare_artifact_review_capsule(fixture_review, executing, review_projection=projection, codex_return=ret, evidence_bundle=bundle, source_materials=materials, artifact_outputs=[output],artifact_output_root=output.parent)
            target = review['active_fibers']['execution_review']['payload']['review_target']
            self.assertEqual(target['target_type'], 'ARTIFACT_OUTPUT_SET')
            self.assertEqual(target['outputs'][0]['artifact_id'], output.name)

    def test_new_artifact_source_material_digest_mismatch_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            _, materials, output, projection, ret, bundle = self._actual_new_artifact_return(td)
            materials['SPEC'].write_text('changed source material\n', encoding='utf-8')
            with self.assertRaises(c.JoyflowError):
                c.validate_codex_execution_return(ret, projection, bundle, source_materials=materials, artifact_outputs=[output],artifact_output_root=output.parent)

    def test_new_artifact_cli_carries_source_material_set_and_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            approved, materials, output, projection, ret, bundle = self._actual_new_artifact_return(td)
            executing = f.advance(approved, 'CODEX_EXECUTION')
            fixture_review = f.brain_review_capsule(executing, projection, ret, bundle)
            paths = {name: pathlib.Path(td) / name for name in ('input.json', 'previous.json', 'projection.json', 'return.json', 'bundle.json', 'review.json')}
            for name, obj in [('input.json', fixture_review), ('previous.json', executing), ('projection.json', projection), ('return.json', ret), ('bundle.json', bundle)]:
                paths[name].write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
            proc = subprocess.run([
                sys.executable, str(ROOT / 'runtime/joyflow_dual_layer.py'),
                'seal-artifact-review', str(paths['input.json']), str(paths['review.json']),
                '--previous', str(paths['previous.json']),
                '--projection', str(paths['projection.json']),
                '--codex-return', str(paths['return.json']),
                '--evidence-bundle', str(paths['bundle.json']),
                '--source-material', f'SPEC={materials["SPEC"]}',
                '--artifact-output', str(output),
                '--artifact-output-root', str(output.parent),
            ], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            review = json.loads(paths['review.json'].read_text(encoding='utf-8'))
            self.assertEqual(review['active_fibers']['execution_review']['payload']['review_target']['outputs'][0]['artifact_id'], output.name)

    def test_local_discovery_cli_requires_original_discovery_source(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base, _ = self.h.repo(td, second_commit=False)
            discovery_projection, discovery_return = self.h.actualize_discovery(repo, base)
            state = self._actualize_local_execution_state(self.eb.local_state(discovery_projection, discovery_return), repo, base)
            _, execution_projection = self._approve_local_execution(state, discovery_projection, discovery_return)
            paths = {name: pathlib.Path(td) / name for name in ('execution.json', 'discovery-projection.json', 'discovery-return.json')}
            for name, obj in [('execution.json', execution_projection), ('discovery-projection.json', discovery_projection), ('discovery-return.json', discovery_return)]:
                paths[name].write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
            proc = subprocess.run([
                sys.executable, str(ROOT / 'runtime/joyflow_dual_layer.py'),
                'verify-execution-projection', str(paths['execution.json']),
                '--repository', str(repo),
                '--path-discovery-projection', str(paths['discovery-projection.json']),
                '--path-discovery-return', str(paths['discovery-return.json']),
            ], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            proc_missing = subprocess.run([
                sys.executable, str(ROOT / 'runtime/joyflow_dual_layer.py'),
                'verify-execution-projection', str(paths['execution.json']),
                '--repository', str(repo),
                '--path-discovery-return', str(paths['discovery-return.json']),
            ], capture_output=True, text=True)
            self.assertEqual(proc_missing.returncode, 2)


if __name__ == '__main__':
    unittest.main()
