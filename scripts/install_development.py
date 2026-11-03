"""Explicit local development install with backup; never publishes a release."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
try:
    from . import bundle
except ImportError:
    import bundle


def install(cli: Path) -> dict:
    archive = bundle.WORK_DIR / 'development-bundle' / bundle.ARTIFACT_NAME
    bundle.validate_source_lock(development=True)
    bundle.validate_manifest()
    bundle.validate_recipe_source()
    audit = bundle.audit_archive(archive)
    sidecar = archive.parent / bundle.SIDECAR_NAME
    if sidecar.read_bytes() != (bundle.ROOT / bundle.SIDECAR_NAME).read_bytes():
        raise RuntimeError('Development sidecar differs from source.')
    listing = json.loads(bundle.cli_call(cli, 'bundle', 'list', '--json').stdout)
    target = Path(listing['productData'])
    name = f'{bundle.BUNDLE_ID}-{bundle.BUNDLE_VERSION}'
    old_group = next((g for g in listing['groups'] if g['key'] == bundle.BUNDLE_ID), None)
    old_ids = old_group['enabledVersionIds'] if old_group else []
    old_versions = [v['version'] for v in old_group['versions'] if v['id'] in old_ids] if old_group else []
    if len(old_versions) != len(old_ids) or len(old_ids) > 1:
        raise RuntimeError('Cannot safely restore ambiguous enabled versions.')
    backup = bundle.WORK_DIR / 'install-backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup.mkdir(parents=True, exist_ok=False)
    destinations = [target / (name + suffix) for suffix in ('.bundle', '.toml')]
    existed = {p: p.exists() for p in destinations}
    for p in destinations:
        if existed[p]:
            shutil.copyfile(p, backup / p.name)
    (backup / 'before.json').write_text(json.dumps(listing, indent=2), encoding='utf-8')
    if (target / 'enabled-bundles.json').exists():
        shutil.copyfile(target / 'enabled-bundles.json', backup / 'enabled-bundles.json')
    # A failed disable must not trigger copying or removal of existing payloads.
    if old_ids:
        bundle.cli_call(cli, 'bundle', 'disable', bundle.BUNDLE_ID)
    try:
        shutil.copyfile(archive, destinations[0])
        shutil.copyfile(sidecar, destinations[1])
        bundle.cli_call(cli, 'bundle', 'enable', bundle.BUNDLE_ID, '--version', bundle.BUNDLE_VERSION)
        after = json.loads(bundle.cli_call(cli, 'bundle', 'list', '--json').stdout)
        group = next(g for g in after['groups'] if g['key'] == bundle.BUNDLE_ID)
        if group['enabledVersionIds'] != [name]:
            raise RuntimeError('Development bundle not exclusively enabled after install.')
        if hashlib.sha256(destinations[0].read_bytes()).hexdigest() != audit['archive_sha256']:
            raise RuntimeError('Installed archive bytes differ.')
    except Exception as original:
        errors = []
        try:
            bundle.cli_call(cli, 'bundle', 'disable', bundle.BUNDLE_ID)
        except Exception as exc:
            errors.append(f'disable: {exc}')
        for p in destinations:
            try:
                if existed[p]:
                    shutil.copyfile(backup / p.name, p)
                elif p.exists():
                    p.unlink()
            except Exception as exc:
                errors.append(f'restore {p.name}: {exc}')
        for version in old_versions:
            try:
                bundle.cli_call(cli, 'bundle', 'enable', bundle.BUNDLE_ID, '--version', version)
            except Exception as exc:
                errors.append(f're-enable {version}: {exc}')
        rollback = {'original_error': str(original), 'rollback_errors': errors, 'previous_enabled_ids': old_ids}
        (backup / 'rollback.json').write_text(json.dumps(rollback, indent=2), encoding='utf-8')
        if errors:
            raise RuntimeError(f'Install failed; rollback incomplete. See {backup}') from original
        raise
    receipt = {'result': 'DEVELOPMENT_INSTALLED_NOT_RELEASE', 'productdata': str(target), 'backup': str(backup), 'archive_sha256': audit['archive_sha256'], 'native_execution': 'NOT_RUN'}
    (backup / 'installation.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt


def main():
    cli = bundle.cli_path(None)
    if cli is None:
        raise SystemExit('Set SC_AGENTS_CLI to the installed CLI executable.')
    print(json.dumps(install(cli), indent=2))


if __name__ == '__main__':
    main()
