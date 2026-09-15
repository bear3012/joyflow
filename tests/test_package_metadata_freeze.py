from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / 'tools' / 'freeze_package_metadata.py'
spec = importlib.util.spec_from_file_location('freeze_package_metadata', MODULE_PATH)
assert spec and spec.loader
freeze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(freeze)


class PackageMetadataFreezeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        subprocess.run(['git','init','-q'], cwd=self.root, check=True)
        subprocess.run(['git','config','user.name','test'], cwd=self.root, check=True)
        subprocess.run(['git','config','user.email','test@example.invalid'], cwd=self.root, check=True)
        (self.root/'tools').mkdir()
        shutil.copy2(MODULE_PATH, self.root/'tools/freeze_package_metadata.py')
        (self.root/'PHASE2_STAGE_LINEAGE.json').write_text(json.dumps({
            'artifact_type':'PHASE2_STAGE_LINEAGE',
            'stage_id':'TEST_STAGE',
            'package_name':'TEST_PACKAGE',
            'status':'CANDIDATE_NOT_BASELINE',
            'parent_package':{'name':'parent.zip','bytes':1,'sha256':'00','review_target_source_filename':'parent.zip'},
        })+'\n', encoding='utf-8')
        (self.root/'payload.txt').write_text('hello\n', encoding='utf-8')
        for name, content in {
            'PACKAGE_MANIFEST.json':'{}\n',
            'VALIDATION_REPORT.json':'{}\n',
            'SHA256SUMS.txt':'x  payload.txt\n',
        }.items():
            (self.root/name).write_text(content, encoding='utf-8')
        subprocess.run(['git','add','.'], cwd=self.root, check=True)
        subprocess.run(['git','commit','-qm','source'], cwd=self.root, check=True)
        self.source = subprocess.check_output(['git','rev-parse','HEAD'], cwd=self.root, text=True).strip()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _install_metadata_commit(self) -> None:
        outputs = freeze.build_outputs(self.root, self.source)
        freeze.write_outputs(outputs, self.root)
        subprocess.run(['git','add',*freeze.METADATA_FILES], cwd=self.root, check=True)
        subprocess.run(['git','commit','-qm','metadata'], cwd=self.root, check=True)

    def test_freeze_is_deterministic_and_excludes_metadata_from_manifest_payload(self) -> None:
        first = freeze.build_outputs(self.root, self.source)
        second = freeze.build_outputs(self.root, self.source)
        self.assertEqual(first, second)
        manifest = json.loads(first['PACKAGE_MANIFEST.json'])
        paths = [row['path'] for row in manifest['payload_files']]
        self.assertNotIn('PACKAGE_MANIFEST.json', paths)
        self.assertNotIn('SHA256SUMS.txt', paths)
        self.assertNotIn('VALIDATION_REPORT.json', paths)
        self.assertIn('payload.txt', paths)
        self.assertIn('tools/freeze_package_metadata.py', paths)
        report = json.loads(first['VALIDATION_REPORT.json'])
        self.assertEqual(report['current_source_object'], self.source)
        self.assertEqual(report['package_currentness_freeze']['metadata_authority'], 'NONE_GENERATOR_IS_MECHANISM_ONLY')

    def test_check_accepts_metadata_only_successor_commit(self) -> None:
        self._install_metadata_commit()
        freeze.check_existing(self.root)

    def test_check_rejects_nonmetadata_source_drift(self) -> None:
        self._install_metadata_commit()
        (self.root/'payload.txt').write_text('changed\n', encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, 'non-metadata payload differs'):
            freeze.check_existing(self.root)

    def test_untracked_files_do_not_enter_package_identity(self) -> None:
        (self.root/'scratch.tmp').write_text('untracked\n', encoding='utf-8')
        outputs = freeze.build_outputs(self.root, self.source)
        manifest = json.loads(outputs['PACKAGE_MANIFEST.json'])
        self.assertNotIn('scratch.tmp', [row['path'] for row in manifest['payload_files']])


if __name__ == '__main__':
    unittest.main()
