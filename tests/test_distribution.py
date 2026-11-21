"""Distribution checks authenticate source structure and AgentAI bundle readiness."""
import json, tempfile, unittest
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile
from ruamel.yaml import YAML
from scripts.validate_distribution import (CODEX_MARKETPLACE, ROOT, validate, distribution_files,
                                           EXPECTED_SUBRECIPES, missing_recipe_skills)
from scripts.build_distribution import build


class DistributionTests(unittest.TestCase):
    def test_meaningful_source_contract(self):
        result = validate()
        self.assertGreater(result['checked_criterion_count'], 0)
        self.assertEqual(result['skills'], 39)
        self.assertEqual(result['subrecipes'], 6)
        self.assertEqual(result['runtime'], 'NOT_RUN')

    def test_recipe_portable_no_local_server(self):
        recipe = YAML(typ='safe').load((ROOT / 'recipes/fea-expert-agent.yaml').read_text(encoding='utf-8'))
        self.assertEqual(
            {e['name'] for e in recipe['extensions'] if e['type'] == 'ref'},
            {'Simcenter 3D', 'Designcenter Open', 'Product Support', 'Simcenter Nastran MCP', 'Batch Post'},
        )
        self.assertNotIn('cmd', json.dumps(recipe['extensions']))
        self.assertEqual(
            [s['name'] for s in recipe['sub_recipes']],
            EXPECTED_SUBRECIPES,
        )
        self.assertEqual([p.name for p in (ROOT / 'recipes').glob('*.yaml')], ['fea-expert-agent.yaml'])

    def test_archive_exact_allowlist_and_determinism(self):
        a = build()
        b = build()
        self.assertEqual(a['sha256'], b['sha256'])
        with ZipFile(ROOT / 'dist' / a['archive']) as archive:
            self.assertTrue(all(info.create_system == 3 for info in archive.infolist()))
            self.assertEqual(set(archive.namelist()), {p.relative_to(ROOT).as_posix() for p in distribution_files()})
            for name in archive.namelist():
                self.assertNotIn('.work/', name)
                self.assertNotIn('__pycache__', name)
                if name.startswith('.agents/'):
                    self.assertEqual(name, CODEX_MARKETPLACE)
                self.assertNotIn('overlay/', name)
                self.assertFalse(name.lower().endswith(('.prt', '.step', '.log', '.zip', '.bundle')))

    def test_missing_skills_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, '39 canonical skills'):
                validate(Path(d))

    def test_recipe_missing_canonical_skill_reference(self):
        instructions = ('Load `simcenter-nastran` then `nastran-sol401-basic-checks`. '
                        'Delegate to `fea-solver-diagnostics` using `load_skill`.')
        self.assertEqual(missing_recipe_skills(instructions, {'simcenter-nastran'}),
                         {'nastran-sol401-basic-checks'})

    def test_batchpost_examples_use_their_qualified_reader_wrappers(self):
        references = ROOT / 'skills/batchpost-actions/references'
        for reference, version, section in (
            ('post-template', 'NX8.5', './PostView/DeformationOptions'),
            ('result-variable', 'NX2612', './PostView/ResultOptions'),
        ):
            with self.subTest(reference=reference):
                text = (references / f'{reference}.md').read_text(encoding='utf-8')
                xml = text.split('```xml\n', 1)[1].split('```', 1)[0]
                root = ElementTree.fromstring(xml)
                self.assertEqual(root.tag, 'NXPostProcessingTemplate')
                self.assertEqual(root.attrib['Version'], version)
                self.assertIsNotNone(root.find(section))


if __name__ == '__main__':
    unittest.main()
