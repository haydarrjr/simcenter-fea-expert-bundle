"""Stage and verify a built Agent Workspace distribution through the selected CLI."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import tomllib
from ruamel.yaml import YAML

try:
    from .package_identity import (BUNDLE_MANIFEST, PACKAGE_ID, atomic_write, json_bytes,
                                   project_path, read_json, read_zip, sha, verify_files)
except ImportError:
    from package_identity import (BUNDLE_MANIFEST, PACKAGE_ID, atomic_write, json_bytes,
                                  project_path, read_json, read_zip, sha, verify_files)


def enabled_versions(catalog):
    return {group['key']: group['enabledVersionIds'] for group in catalog['groups']
            if group['enabledVersionIds']}


def on_demand_pointer(name, observed, archived, version_id):
    if name == BUNDLE_MANIFEST or (name.startswith('skills/') and '/references/' in name):
        return observed == b''
    yaml = YAML(typ='safe')
    if name.startswith('recipes/') and name.endswith('.yaml'):
        keys = ('bundle', 'version', 'title', 'description')
        source = yaml.load(archived.decode('utf-8'))
        return yaml.load(observed.decode('utf-8')) == {key: source[key] for key in keys}
    if name.startswith('skills/') and name.endswith('/SKILL.md'):
        text = observed.decode('utf-8')
        if not text.startswith(('---\n', '---\r\n')) or text.count('---') < 2:
            return False
        _, frontmatter, body = text.split('---', 2)
        source = yaml.load(archived.decode('utf-8').split('---', 2)[1])
        return (body.strip() == '<!-- Content loaded from bundle on demand -->'
                and yaml.load(frontmatter) == {'name': source['name'], 'description': source['description'],
                                               'bundle': version_id})
    return False


def attest_installed(product_data, version_id, files):
    root = project_path(product_data, version_id)
    expected = {name for name in files if not name.startswith('readme/')}
    actual = {path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_file()}
    extras = actual - expected
    if extras:
        if extras != {'mcps.json'} or read_json(project_path(root, 'mcps.json').read_bytes()) != {
                'mcpFolders': [], 'configs': []}:
            raise ValueError(f'unexpected materialized resources: {sorted(extras)}')
    if not expected <= actual:
        raise ValueError(f'missing materialized resources: {sorted(expected - actual)}')
    pointers = 0
    for name in sorted(expected):
        observed = project_path(root, name).read_bytes()
        if observed == files[name]:
            continue
        if not on_demand_pointer(name, observed, files[name], version_id):
            raise ValueError(f'materialized resource differs: {name}')
        pointers += 1
    return expected, pointers


def install(cli, product_data, archive, metadata, receipts):
    cli = Path(cli).resolve(strict=True)
    product_data = Path(product_data).resolve(strict=True)
    archive = Path(archive).resolve(strict=True)
    receipts = Path(receipts).resolve()
    metadata = Path(metadata).read_bytes()
    spec = tomllib.loads(metadata.decode('utf-8'))['bundle']
    files = read_zip(archive)
    identity = verify_files(files, BUNDLE_MANIFEST, 'agentsai')
    version = identity['version']
    if spec['id'] != PACKAGE_ID or spec['version'] != version:
        raise ValueError('sidecar and archive identity differ')
    version_id = f'{PACKAGE_ID}-{version}'
    archive_name = f'{version_id}.bundle'
    sidecar_name = f'{version_id}.toml'
    targets = {archive_name: archive.read_bytes(), sidecar_name: metadata}
    if any(project_path(product_data, name).exists() for name in [*targets, version_id]):
        raise FileExistsError('candidate version already exists in productdata')
    if any(not name.startswith(('recipes/', 'skills/', 'readme/')) for name in files):
        raise ValueError('unexpected bundle resource')
    env = {**os.environ, 'SC_AGENTS_PRODUCT_DATA': str(product_data)}

    def call(*args):
        result = subprocess.run([str(cli), 'bundle', *args], cwd=product_data, env=env, check=True,
                                capture_output=True, text=True, encoding='utf-8', timeout=60)
        return result.stdout

    def catalog():
        result = json.loads(call('list', '--json'))
        if Path(result['productData']).resolve() != product_data:
            raise ValueError('the CLI selected a different productdata')
        return result

    before = catalog()
    previous = enabled_versions(before)
    active = previous.get(PACKAGE_ID, [])
    if len(active) > 1 or any(not entry.startswith(PACKAGE_ID + '-') for entry in active):
        raise ValueError('ambiguous previous FEA activation')
    receipts.mkdir(parents=True)
    atomic_write(receipts / 'before.json', json_bytes(before))
    enabled = project_path(product_data, 'enabled-bundles.json')
    if enabled.is_file():
        atomic_write(receipts / 'enabled-bundles.before.json', enabled.read_bytes())
    for name, raw in targets.items():
        target = project_path(product_data, name)
        with target.open('xb') as stream:
            stream.write(raw)
        if target.read_bytes() != raw:
            raise ValueError(f'product staging readback differs: {name}')
    try:
        call('enable', PACKAGE_ID, '--version', version)
        after = catalog()
        atomic_write(receipts / 'after.json', json_bytes(after))
        if enabled_versions(after) != {**previous, PACKAGE_ID: [version_id]}:
            raise ValueError('CLI activation differs from requested version or changed other bundles')
        staged = read_zip(project_path(product_data, archive_name))
        if staged != files:
            raise ValueError('the enabled adjacent bundle differs from the verified candidate')
        observed, pointers = attest_installed(product_data, version_id, staged)
    except BaseException as exc:
        failure = {'status': 'FAILED', 'error': str(exc), 'staged_paths': list(targets)}
        try:
            actual = enabled_versions(catalog())
            if {k: v for k, v in actual.items() if k != PACKAGE_ID} != {
                    k: v for k, v in previous.items() if k != PACKAGE_ID}:
                raise ValueError('another bundle changed during activation')
            if actual.get(PACKAGE_ID, []) != active:
                if actual.get(PACKAGE_ID) != [version_id]:
                    raise ValueError('FEA activation changed outside this installation')
                if active:
                    call('enable', PACKAGE_ID, '--version', active[0].removeprefix(PACKAGE_ID + '-'))
                else:
                    call('disable', PACKAGE_ID)
            failure['rollback'] = 'VERIFIED' if enabled_versions(catalog()) == previous else 'UNVERIFIED'
        except (ValueError, OSError, subprocess.SubprocessError) as restore_error:
            failure.update(rollback='UNVERIFIED', rollback_error=str(restore_error))
        atomic_write(receipts / 'failure.json', json_bytes(failure))
        raise
    receipt = {'status': 'INSTALLED_VERIFIED', 'package_id': PACKAGE_ID, 'version': version,
               'candidate_source_digest': identity['candidate_source_digest'],
               'content_digest': identity['content_digest'], 'archive_sha256': sha(targets[archive_name]),
               'observed_at': datetime.now(timezone.utc).isoformat(), 'product_data': str(product_data),
               'verified_resources': len(observed), 'on_demand_pointers': pointers,
               'resource_storage': 'BUNDLE_ON_DEMAND' if pointers else 'EXTRACTED',
               'enabled_version_ids': [version_id],
               'skill_count': sum(name.endswith('/SKILL.md') for name in observed),
               'host_loaded_identity': 'UNVERIFIED', 'native_execution': 'NOT_RUN'}
    atomic_write(receipts / 'receipt.json', json_bytes(receipt))
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('cli', 'product-data', 'archive', 'metadata', 'receipt-directory'):
        parser.add_argument('--' + flag, required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(install(args.cli, args.product_data, args.archive, args.metadata,
                             args.receipt_directory), indent=2))
