"""Install, attest or roll back the Codex or VS Code project channel."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

try:
    from .package_identity import (PACKAGE_ID, atomic_write, file_hashes, json_bytes, project_path,
                                   read_json, read_zip, sha, verify_files)
    from .package_release import PROJECTS
except ImportError:
    from package_identity import (PACKAGE_ID, atomic_write, file_hashes, json_bytes, project_path,
                                  read_json, read_zip, sha, verify_files)
    from package_release import PROJECTS


RECEIPTS = {'codex': '.agents/fea-expert-install-receipt.json',
            'copilot': '.vscode/fea-expert-install-receipt.json'}
START = b'<!-- simcenter-fea-expert:start -->'
END = b'<!-- simcenter-fea-expert:end -->'
BLOCK = re.compile(re.escape(START) + b'.*?' + re.escape(END), re.S)


def allowed(name, channel):
    if channel == 'codex':
        return name in ('AGENTS.md', '.agents/fea-workflow.md', PROJECTS[channel][0],
                        RECEIPTS[channel]) or name.startswith('.agents/skills/')
    return name in ('.github/fea-workflow.md', '.github/copilot-instructions.md',
                    '.github/agents/simcenter-fea-expert.agent.md',
                    PROJECTS[channel][0], RECEIPTS[channel]) or name.startswith('.github/skills/')


def project_bytes(project, name):
    path = project_path(project, name)
    return path.read_bytes() if path.exists() else None


def merge_instructions(existing, generated):
    text = existing or b''
    text.decode('utf-8-sig')
    if text.count(START) != text.count(END) or text.count(START) > 1:
        raise ValueError('ambiguous FEA instruction markers in AGENTS.md')
    if START in text:
        if not BLOCK.search(text):
            raise ValueError('invalid order of FEA instruction markers')
        return BLOCK.sub(lambda _: generated.strip(), text, count=1)
    return text + (b'\n\n' if text and not text.endswith(b'\n\n') else b'') + generated


def attest(project, channel):
    project = Path(project).resolve(strict=True)
    receipt_name = RECEIPTS[channel]
    receipt = read_json(project_path(project, receipt_name).read_bytes())
    manifest_name = PROJECTS[channel][0]
    if (receipt.get('package_id') != PACKAGE_ID or receipt.get('channel') != channel
            or receipt.get('project') != str(project) or manifest_name not in receipt['installed_files']):
        raise ValueError('receipt belongs to a different project or channel')
    installed = {}
    for name, digest in receipt['installed_files'].items():
        if name == receipt_name or not allowed(name, channel):
            raise ValueError(f'out-of-scope receipt path: {name}')
        raw = project_path(project, name).read_bytes()
        if name == 'AGENTS.md':
            match = BLOCK.search(raw)
            if not match or raw.count(START) != 1 or raw.count(END) != 1:
                raise ValueError('FEA instruction block is missing or ambiguous')
            raw = match.group() + b'\n'
        if sha(raw) != digest:
            raise ValueError(f'installed resource changed: {name}')
        installed[name] = raw
    manifest = verify_files(installed, manifest_name, channel)
    if any(receipt[k] != manifest[k] for k in ('version', 'content_digest', 'candidate_source_digest')):
        raise ValueError('installation receipt and installed package differ')
    return receipt


def restore(project, originals):
    for name, raw in originals.items():
        target = project_path(project, name)
        if raw is None:
            target.unlink(missing_ok=True)
        else:
            atomic_write(target, raw)


def install(project, archive, backup, channel):
    project = Path(project).resolve(strict=True)
    archive = Path(archive).resolve(strict=True)
    backup = Path(backup).resolve()
    if backup.exists() or backup.is_relative_to(project):
        raise ValueError('select a new backup path outside the project')
    manifest_name = PROJECTS[channel][0]
    receipt_name = RECEIPTS[channel]
    files = read_zip(archive)
    manifest = verify_files(files, manifest_name, channel)
    if receipt_name in files or any(not allowed(name, channel) for name in files):
        raise ValueError('unexpected project channel member')
    opposite = 'copilot' if channel == 'codex' else 'codex'
    if project_bytes(project, RECEIPTS[opposite]) is not None:
        raise ValueError('use a separate project for the other FEA channel to avoid duplicate skills')
    current_receipt = project_bytes(project, receipt_name)
    owned = set(attest(project, channel)['installed_files']) if current_receipt else set()
    originals = {name: project_bytes(project, name) for name in sorted(set(files) | owned | {receipt_name})}
    for name, raw in originals.items():
        if raw is not None and name not in owned | {'AGENTS.md', receipt_name}:
            raise ValueError(f'workspace file is not owned by FEA Expert: {name}')
    if not current_receipt and b'simcenter-fea-expert:start' in (originals.get('AGENTS.md') or b''):
        raise ValueError('existing FEA instruction block lacks its installation receipt')
    receipt = {k: manifest[k] for k in ('package_id', 'version', 'channel',
                                        'candidate_source_digest', 'content_digest')}
    receipt.update(status='FILES_VERIFIED', project=str(project), backup=str(backup),
                   installed_files=file_hashes(files), archive_sha256=sha(archive.read_bytes()),
                   skill_count=sum(n.endswith('/SKILL.md') for n in files),
                   observed_at=datetime.now(timezone.utc).isoformat(),
                   host_loaded_identity='UNVERIFIED', native_execution='NOT_RUN')
    updates = dict(files)
    if 'AGENTS.md' in files:
        updates['AGENTS.md'] = merge_instructions(originals['AGENTS.md'], files['AGENTS.md'])
    updates[receipt_name] = json_bytes(receipt)
    updates.update({name: None for name in owned - files.keys()})
    backup.mkdir(parents=True)
    before = {name: sha(raw) if raw is not None else None for name, raw in originals.items()}
    after = {name: sha(raw) if raw is not None else None for name, raw in updates.items()}
    for name, raw in originals.items():
        if raw is not None:
            atomic_write(backup / 'original' / name, raw)
    atomic_write(backup / 'transaction.json', json_bytes({
        'project': str(project), 'channel': channel, 'before': before, 'after': after,
    }))
    applied = {}
    try:
        for name, raw in updates.items():
            if project_bytes(project, name) != originals[name]:
                raise ValueError(f'workspace changed during install: {name}')
            restore(project, {name: raw})
            applied[name] = originals[name]
        confirmed = attest(project, channel)
        atomic_write(backup / 'receipt.json', json_bytes(confirmed))
    except BaseException:
        restore(project, dict(reversed(list(applied.items()))))
        raise
    return confirmed


def rollback(project, backup, channel):
    project = Path(project).resolve(strict=True)
    backup = Path(backup).resolve(strict=True)
    plan = read_json(project_path(backup, 'transaction.json').read_bytes())
    if (plan['project'] != str(project) or plan['channel'] != channel
            or set(plan['before']) != set(plan['after'])
            or any(not allowed(name, channel) for name in plan['before'])):
        raise ValueError('rollback scope does not match this project/channel')
    originals = {}
    current = {}
    for name, digest in plan['before'].items():
        base = project_path(backup, 'original/' + name)
        originals[name] = base.read_bytes() if digest is not None else None
        current[name] = project_bytes(project, name)
        for raw, expected in ((originals[name], digest), (current[name], plan['after'][name])):
            if (sha(raw) if raw is not None else None) != expected:
                raise ValueError(f'rollback bytes changed: {name}')
    applied = {}
    try:
        for name, raw in originals.items():
            restore(project, {name: raw})
            applied[name] = current[name]
    except BaseException:
        restore(project, dict(reversed(list(applied.items()))))
        raise
    return {'status': 'ROLLED_BACK', 'project': str(project), 'channel': channel}


def main(channel=None):
    parser = argparse.ArgumentParser(description=__doc__)
    if channel is None:
        parser.add_argument('--channel', choices=PROJECTS, required=True)
    parser.add_argument('--project', type=Path, required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--archive', type=Path)
    modes.add_argument('--verify', action='store_true')
    modes.add_argument('--rollback', action='store_true')
    parser.add_argument('--backup', type=Path)
    args = parser.parse_args()
    channel = channel or args.channel
    if not args.verify and not args.backup:
        parser.error('--backup is required to install or roll back')
    if args.verify:
        result = attest(args.project, channel)
    elif args.rollback:
        result = rollback(args.project, args.backup, channel)
    else:
        result = install(args.project, args.archive, args.backup, channel)
    print(json.dumps({key: value for key, value in result.items() if key != 'installed_files'}, indent=2))


if __name__ == '__main__':
    main()
