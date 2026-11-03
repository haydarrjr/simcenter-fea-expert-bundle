"""Fail closed on tracked private/proprietary payload and credential literals.

Runs without submodules, product installation, network or secrets. This does not
establish redistribution clearance for any external input or qualify a host.
"""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import bundle


def check() -> dict:
    result = subprocess.run(['git', 'ls-files', '--stage', '-z'], cwd=ROOT, check=True, capture_output=True)
    count = 0
    for entry in result.stdout.split(b'\0'):
        if not entry:
            continue
        meta, raw_name = entry.split(b'\t', 1)
        mode = meta.split()[0].decode()
        name = raw_name.decode()
        if name.startswith('vendor/'):
            if mode != '160000':
                raise RuntimeError('Private vendor content tracked: ' + name)
            continue
        if name.startswith('integration/') and name != 'integration/simcenter-3d/source.json':
            raise RuntimeError('Proprietary integration payload tracked: ' + name)
        if name.startswith('.work/') or name.endswith(('.bundle', '.zip', '.exe', '.dll', '.log', '.env')):
            raise RuntimeError('Local/binary/secret payload tracked: ' + name)
        if mode != '100644' and mode != '100755':
            raise RuntimeError('Unexpected tracked mode: ' + name)
        # Inspect staged bytes, not a possibly sanitized worktree.
        data = subprocess.run(['git', 'show', ':' + name], cwd=ROOT, check=True, capture_output=True).stdout
        text = data.decode('utf-8')
        if bundle.CREDENTIAL_RE.search(text):
            raise RuntimeError('Credential literal tracked: ' + name)
        if ('license: Proprietary' + ' - Siemens') in text or ('Unpublished work.' + ' Copyright') in text:
            raise RuntimeError('Proprietary source text tracked: ' + name)
        count += 1
    bundle.validate_manifest()
    bundle.validate_recipe_source()
    return {'result': 'PASS', 'checked_public_files': count, 'evidence_class': 'SOURCE_TESTED',
            'full_bundle_build': 'NOT_RUN', 'native_execution': 'NOT_RUN', 'engineering_acceptance': 'NOT_RUN'}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
