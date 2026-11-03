import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[1]))
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from scripts import bundle
from scripts import install_development as installer


class DevelopmentInstallChecks(unittest.TestCase):
    def exercise(self, old_version=None, fail_enable=False, fail_disable=False):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            work = root / 'work'
            target = root / 'productdata'
            target.mkdir()
            archive = work / 'development-bundle' / bundle.ARTIFACT_NAME
            archive.parent.mkdir(parents=True)
            archive.write_bytes(b'new')
            (root / bundle.SIDECAR_NAME).write_bytes(b'manifest')
            (archive.parent / bundle.SIDECAR_NAME).write_bytes(b'manifest')
            name = f'{bundle.BUNDLE_ID}-{bundle.BUNDLE_VERSION}'
            dest = target / (name + '.bundle')
            if old_version:
                dest.write_bytes(b'old')
            ids = [f'{bundle.BUNDLE_ID}-{old_version}'] if old_version else []
            versions = [{'id': i, 'version': old_version} for i in ids]
            before = {'productData': str(target), 'groups': [{'key': bundle.BUNDLE_ID, 'enabledVersionIds': ids, 'versions': versions}]}
            after = {'groups': [{'key': bundle.BUNDLE_ID, 'enabledVersionIds': [name]}]}
            calls = []
            def cli(_cli, *args):
                calls.append(args)
                if args[1] == 'list':
                    return SimpleNamespace(stdout=json.dumps(before if len(calls) == 1 else after))
                if args[1] == 'disable' and fail_disable:
                    raise RuntimeError('disable failure')
                if args[1] == 'enable' and fail_enable and args[-1] == bundle.BUNDLE_VERSION:
                    raise RuntimeError('enable failure')
                return SimpleNamespace(stdout='')
            with patch.object(bundle, 'ROOT', root), patch.object(bundle, 'WORK_DIR', work), patch.object(bundle, 'validate_source_lock'), patch.object(bundle, 'validate_manifest'), patch.object(bundle, 'validate_recipe_source'), patch.object(bundle, 'audit_archive', return_value={'archive_sha256': hashlib.sha256(b'new').hexdigest()}), patch.object(bundle, 'cli_call', side_effect=cli):
                if fail_enable or fail_disable:
                    with self.assertRaises(RuntimeError):
                        installer.install(Path('cli'))
                    if old_version:
                        self.assertEqual(dest.read_bytes(), b'old')
                    else:
                        self.assertFalse(dest.exists())
                else:
                    self.assertEqual(installer.install(Path('cli'))['result'], 'DEVELOPMENT_INSTALLED_NOT_RELEASE')
                    self.assertEqual(dest.read_bytes(), b'new')
            return calls

    def test_successful_install(self):
        self.exercise(old_version='0.0.9')

    def test_restores_previous_different_version(self):
        calls = self.exercise(old_version='0.0.9', fail_enable=True)
        self.assertEqual(calls[-1], ('bundle', 'enable', bundle.BUNDLE_ID, '--version', '0.0.9'))

    def test_new_failed_install_removes_new_payload(self):
        self.exercise(fail_enable=True)

    def test_failed_initial_disable_never_writes(self):
        calls = self.exercise(old_version='0.0.9', fail_disable=True)
        self.assertEqual(len(calls), 2)
