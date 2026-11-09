import sys, tempfile, unittest, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import package_bundle as pb


class BundleLayoutTests(unittest.TestCase):
    def test_canonical_main_has_six_subrecipes(self):
        main = pb.load_recipe((ROOT / pb.MAIN).read_text(encoding='utf-8'))
        self.assertEqual({s['name'] for s in main['sub_recipes']}, pb.EXPECTED_SUBRECIPES)
        for s in main['sub_recipes']:
            self.assertTrue(s['path'].startswith('./subrecipes/'))
            self.assertTrue((ROOT / 'recipes' / s['path']).is_file())

    def test_only_main_agent_at_recipes_root(self):
        self.assertEqual(sorted(p.name for p in (ROOT / 'recipes').glob('*.yaml')), ['fea-expert-agent.yaml'])

    def test_all_38_skills_under_top_level_skills_dir(self):
        skills = sorted(p.parent.name for p in (ROOT / 'skills').glob('*/SKILL.md'))
        self.assertEqual(len(skills), 38)
        self.assertFalse((ROOT / '.agents').exists())
        self.assertFalse((ROOT / 'overlay').exists())

    def test_built_archive_layout(self):
        with tempfile.TemporaryDirectory() as d:
            r = pb.package(d)
            with zipfile.ZipFile(r['archive']) as z:
                names = set(z.namelist())
                main = pb.load_recipe(z.read(pb.MAIN))
            self.assertEqual(pb.check_layout(names, main), [])
            for sub in pb.EXPECTED_SUBRECIPES:
                self.assertIn(f'recipes/subrecipes/{sub}.yaml', names)
            toml = (Path(d) / '.sim-ai-agents.toml').read_text(encoding='utf-8')
            self.assertIn('version = "%s"' % main['version'], toml)

    def test_flattened_layout_is_rejected(self):
        main = {'sub_recipes': []}
        names = {'recipes/fea-expert-agent.yaml', 'recipes/fea-verifier.yaml', 'skills/a/SKILL.md'}
        self.assertTrue(pb.check_layout(names, main))


if __name__ == '__main__':
    unittest.main()
