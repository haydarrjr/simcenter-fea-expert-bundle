import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.harden_integration import transform, transform_recipe, START, POLICY
from scripts.hydrate_integrated_sc3d import hydrate
from scripts import bundle


class HardeningChecks(unittest.TestCase):
    def test_all_official_skills_receive_contract(self):
        receipt = json.loads((bundle.ROOT / bundle.CFG['integration_receipt']).read_text())
        names = [n for n in receipt['files'] if n.endswith('/SKILL.md')]
        self.assertEqual(len(names), 13)
        for name in names:
            raw = ('---\nname: ' + name.split('/')[1] + '\ndescription: test\n---\n# Original\n').encode()
            out = transform(name, raw)
            self.assertIn(START.encode(), out)
            self.assertTrue(out.startswith(raw.split(b'# Original')[0]))
            self.assertEqual(transform(name, out), out)
            self.assertIn(b'# Original', out)

    def test_corrects_import_and_gates_pagination(self):
        raw = b'---\nname: a\ndescription: test\n---\noptional `PAGE`; optional `CURSOR`\n```python\nif __name__ == "__main__":\n    import sys\n    main(sys.argv[1:])\n```\n'
        out = transform('skills/a/SKILL.md', raw)
        self.assertNotIn(b'    import sys', out)
        self.assertIn(b'    main(sys.argv[1:])', out)
        self.assertIn(b'optional `PAGE` only if advertised', out)
        self.assertIn(b'optional `CURSOR` only if advertised', out)

    def test_policy_covers_required_failure_modes(self):
        for needle in ['Product Support', 'current tool input schema', 'PARTIAL', 'no captured stdout',
                       'UNVERIFIED', 'uncomputed', 'project/solver/element-specific',
                       'independent native readback', 'never replay an uncertain mutation']:
            self.assertIn(needle, POLICY)

    def test_crlf_and_non_skill_bytes_preserved(self):
        raw = b'---\r\nname: a\r\ndescription: a\r\n---\r\nbody\r\n'
        out = transform('skills/a/SKILL.md', raw)
        self.assertNotIn(b'\n', out.replace(b'\r\n', b''))
        self.assertEqual(transform('mcps/a.bat', raw), raw)
        self.assertEqual(transform('skills/a/references/a.md', raw), raw)

    def test_recipe_policy_in_instructions_and_product_support_reachable(self):
        raw = b'version: "1"\ninstructions: |\n  legacy\nextensions:\n  - type: ref\n    name: Designcenter Open\n'
        out = transform_recipe('recipes/a.yaml', raw)
        self.assertEqual(transform_recipe('recipes/a.yaml', out), out)
        text = out.decode()
        self.assertLess(text.index('safety contract v1'), text.index('  legacy'))
        self.assertEqual(text.count('name: Product Support'), 1)
        self.assertIn('    name: Product Support', text.split('extensions:')[1])

    def test_packaging_calls_policy_transform(self):
        # Check the real payload route rather than merely testing the helper.
        with tempfile.TemporaryDirectory() as td:
            from unittest.mock import patch
            root = Path(td)
            source = root / 'integration/recipes/a.yaml'
            source.parent.mkdir(parents=True)
            source.write_bytes(b'instructions: |\n  legacy\nextensions:\n  - type: ref\n    name: Designcenter Open\n')
            with patch.object(bundle, 'ROOT', root), patch.object(bundle, 'CFG', {**bundle.CFG, 'integration_root': 'integration'}):
                self.assertIn(b'safety contract v1', bundle.payload_bytes('recipes/a.yaml', source))


class HydrationChecks(unittest.TestCase):
    def fixture(self, root, name='skills/a/SKILL.md'):
        archive = root / 'official.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr(name, b'approved')
        dest = root / 'capture'; dest.mkdir()
        receipt = {'source_archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                   'files': {name: hashlib.sha256(b'approved').hexdigest()}}
        (dest / 'source.json').write_text(json.dumps(receipt))
        return archive, dest

    def test_hydrate_is_pinned_idempotent_and_does_not_change_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            archive, dest = self.fixture(Path(td))
            before = (dest / 'source.json').read_bytes()
            self.assertEqual(hydrate(archive, dest), 1)
            self.assertEqual(hydrate(archive, dest), 1)
            self.assertEqual((dest / 'source.json').read_bytes(), before)
            (dest / 'skills/a/SKILL.md').write_bytes(b'user data')
            with self.assertRaisesRegex(RuntimeError, 'overwrite'):
                hydrate(archive, dest)

    def test_wrong_archive_and_unsafe_paths_fail(self):
        with tempfile.TemporaryDirectory() as td:
            archive, dest = self.fixture(Path(td), '../escape')
            with self.assertRaisesRegex(RuntimeError, 'Unsafe'):
                hydrate(archive, dest)
            archive.write_bytes(b'wrong')
            with self.assertRaisesRegex(RuntimeError, 'Archive SHA256'):
                hydrate(archive, dest)


if __name__ == '__main__':
    unittest.main()
