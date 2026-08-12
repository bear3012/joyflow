from __future__ import annotations
import pathlib, sys, unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import validate_package as vp

class PR2XDocumentIdentityTests(unittest.TestCase):
    def test_instruction_review_target_template_is_not_active_review_target(self):
        identity=vp.current_candidate_identity(ROOT)
        result=vp.verify_current_candidate_documents(ROOT,identity)
        self.assertEqual(result['status'],'PASS',result)
        self.assertEqual(result['active_authoritative_review_targets'],[])


    def test_current_development_instruction_is_external_active_binding(self):
        import json
        lineage=json.loads((ROOT/'PHASE2_STAGE_LINEAGE.json').read_text(encoding='utf-8'))
        binding=lineage['project_instruction_change_status']
        self.assertEqual(binding['change'],'USER_CONFIRMED_ACTIVE_COMPACT_V2_DEVELOPMENT_INSTRUCTION')
        self.assertEqual(binding['active_instruction']['confirmed_source_sha256'],'126b6e73df483e8d6bc81d6c18d41f8068844b46d529425ddac0b3fe54f6dff8')
        self.assertEqual(binding['active_instruction']['physical_surface'],'WEB_BRAIN_PROJECT_INSTRUCTION_EXTERNAL_TO_RUNTIME_PACKAGE')
        self.assertFalse(binding['development_instruction_duplicated_into_runtime_package'])
        self.assertFalse((ROOT/'JOYFLOW_PROJECT_INSTRUCTION_REPLACEMENT_CANDIDATE_ARCHITECTURE_CONVERGENCE.md').exists())

    def test_readme_is_phase2_candidate_identity(self):
        text=(ROOT/'README.md').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('# Joyflow Phase 2 Architecture Convergence & Closure Repair Candidate'))

if __name__=='__main__': unittest.main()
