"""Distribution checks authenticate source structure and AgentAI bundle readiness."""
import json, tempfile, unittest
from pathlib import Path
from zipfile import ZipFile
from ruamel.yaml import YAML
from scripts.validate_distribution import ROOT, validate, distribution_files, EXPECTED_SUBRECIPES
from scripts.build_distribution import build


class DistributionTests(unittest.TestCase):
    def test_meaningful_source_contract(self):
        result = validate()
        self.assertGreater(result['checked_criterion_count'], 0)
        self.assertEqual(result['skills'], 38)
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
            self.assertEqual(set(archive.namelist()), {p.relative_to(ROOT).as_posix() for p in distribution_files()})
            for name in archive.namelist():
                self.assertNotIn('.work/', name)
                self.assertNotIn('__pycache__', name)
                self.assertNotIn('.agents/', name)
                self.assertNotIn('overlay/', name)
                self.assertFalse(name.lower().endswith(('.prt', '.step', '.log', '.zip', '.bundle')))

    def test_missing_skills_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, '38 canonical skills'):
                validate(Path(d))


if __name__ == '__main__':
    unittest.main()
