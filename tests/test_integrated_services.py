"""Independent checks of the bundled official service capture and materialization inputs."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import bundle


class IntegrationChecks(unittest.TestCase):
    @unittest.skipUnless((bundle.ROOT / bundle.CFG["integration_root"] / "recipes").is_dir(), "authorized local Siemens payload not hydrated")
    def test_official_capture_counts_and_titles(self):
        files = bundle.integration_files()
        self.assertEqual(len(files), 23)
        self.assertEqual(sum(n.endswith('/SKILL.md') for n in files), 13)
        self.assertEqual(sum(n.startswith('mcps/') for n in files), 0)
        recipes = [p.read_text(encoding='utf-8') for n, p in files.items() if n.startswith('recipes/')]
        self.assertEqual(len(recipes), 4)
        for title in ['BatchPost Agent', 'Designcenter Open Journal Agent', 'Simcenter 3D Documentation Agent', 'Simcenter 3D Assistant']:
            self.assertTrue(any(f'title: "{title}"' in t for t in recipes), title)

    @unittest.skipUnless((bundle.ROOT / bundle.CFG["integration_root"] / "recipes").is_dir(), "authorized local Siemens payload not hydrated")
    def test_no_bundled_mcp_launchers(self):
        payload = bundle.archive_payload_map()
        self.assertEqual(bundle.CFG['integration_mcp_map'], {})
        self.assertEqual(bundle.CFG['manifest_mcp_names'], [])
        self.assertFalse(any(k.startswith('mcps/') for k in payload))
        self.assertFalse(any(p.suffix.lower() in ('.bat', '.exe', '.dll') for p in payload.values()))

    @unittest.skipUnless((bundle.ROOT / bundle.CFG["integration_root"] / "recipes").is_dir(), "authorized local Siemens payload not hydrated")
    def test_real_packaged_policy_and_provenance(self):
        files = bundle.integration_files()
        before = {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in files.items()}
        staged = bundle.collect_skills()
        evidence = bundle.integration_evidence()
        changed = 0
        for name, path in files.items():
            packaged = staged[name] if name.startswith('skills/') else bundle.payload_bytes(name, path)
            item = evidence['files'][name]
            self.assertEqual(item['source_sha256'], before[name])
            self.assertEqual(item['packaged_sha256'], hashlib.sha256(packaged).hexdigest())
            if name.endswith('/SKILL.md') or name.startswith('recipes/'):
                changed += 1
                self.assertNotEqual(item['source_sha256'], item['packaged_sha256'])
                self.assertIn(b'overrides conflicting legacy guidance', packaged)
            else:
                self.assertEqual(item['source_sha256'], item['packaged_sha256'])
        self.assertEqual(changed, 17)
        self.assertNotIn(b'    import sys', staged['skills/designcenter-open-journal-authoring/SKILL.md'])
        self.assertEqual(before, {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in files.items()})

    def test_tampered_missing_extra_capture_rejected(self):
        for mode in ['tamper', 'missing', 'extra']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as td:
                base = Path(td)
                item = base / 'integration/recipes/a.yaml'
                item.parent.mkdir(parents=True)
                item.write_bytes(b'original')
                receipt = base / 'integration/source.json'
                receipt.write_text(json.dumps({'files': {'recipes/a.yaml': hashlib.sha256(b'original').hexdigest()}}))
                if mode == 'tamper':
                    item.write_bytes(b'changed')
                elif mode == 'missing':
                    item.unlink()
                else:
                    (item.parent / 'extra.yaml').write_bytes(b'x')
                cfg = {**bundle.CFG, 'integration_root': 'integration', 'integration_receipt': 'integration/source.json'}
                with patch.object(bundle, 'ROOT', base), patch.object(bundle, 'CFG', cfg):
                    with self.assertRaises(RuntimeError):
                        bundle.integration_files()

    def test_manifest_declares_no_duplicate_mcps(self):
        m = bundle.validate_manifest()
        self.assertEqual(m.get('mcps', []), [])
        self.assertFalse(any(c.get('type') == 'mcps' for c in m.get('contributions', [])))


if __name__ == '__main__':
    unittest.main()
