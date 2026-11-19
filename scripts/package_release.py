"""Build a candidate Agent Workspace, Codex, VS Code and source distribution."""
import argparse
import json
from pathlib import Path, PurePosixPath
import re
import tempfile

try:
    from . import build_distribution, package_bundle
    from .package_identity import (BUNDLE_MANIFEST, PACKAGE_ID,
                                   add_manifest, json_bytes, read_zip, sha, verify_files, write_zip)
except ImportError:
    import build_distribution
    import package_bundle
    from package_identity import (BUNDLE_MANIFEST, PACKAGE_ID,
                                  add_manifest, json_bytes, read_zip, sha, verify_files, write_zip)


ROOT = package_bundle.ROOT
PROJECTS = {
    'codex': ('.agents/fea-expert-package.json', 'codex-project-windows.zip'),
    'copilot': ('.github/fea-expert-package.json', 'vscode-copilot-windows.zip'),
}


def check_links(files):
    from posixpath import normpath
    for name, raw in files.items():
        if not name.endswith('.md'):
            continue
        text = re.sub(r'(?ms)^```.*?^```\s*', '', raw.decode('utf-8'))
        for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
            if link.startswith(('http:', 'https:', 'mailto:', '#')):
                continue
            destination = normpath(str(PurePosixPath(name).parent / link.split('#', 1)[0]))
            if destination not in files and not any(n.startswith(destination + '/') for n in files):
                raise ValueError(f'missing packaged link: {name} -> {link}')


def project_archive(bundle, channel, out, root=ROOT):
    payload = read_zip(bundle)
    identity = verify_files(payload, BUNDLE_MANIFEST, 'agentsai')
    skills = {name: raw for name, raw in payload.items()
              if name.startswith('skills/') and name != BUNDLE_MANIFEST}
    templates = root / 'integrations'
    workflow = (templates / 'fea-workflow.md').read_bytes()
    if channel == 'codex':
        files = {f'.agents/{name}': raw for name, raw in skills.items()}
        files['.agents/fea-workflow.md'] = workflow
        files['AGENTS.md'] = (templates / 'codex/project-instructions.md').read_bytes().strip() + b'\n'
    else:
        files = {f'.github/{name}': raw for name, raw in skills.items()}
        files['.github/fea-workflow.md'] = workflow
        files['.github/agents/simcenter-fea-expert.agent.md'] = (
            templates / 'vscode-copilot/simcenter-fea-expert.agent.md').read_bytes()
        files['.github/copilot-instructions.md'] = (
            templates / 'vscode-copilot/copilot-instructions.md').read_bytes()
    check_links(files)
    manifest, filename = PROJECTS[channel]
    files = add_manifest(files, manifest, version=identity['version'], channel=channel,
                         candidate_digest=identity['candidate_source_digest'])
    archive = out / filename
    write_zip(archive, files)
    verified = verify_files(read_zip(archive), manifest, channel)
    return {'archive': archive.name, 'sha256': sha(archive.read_bytes()),
            'content_digest': verified['content_digest'], 'files': len(files)}


def build(out=None, root=ROOT):
    candidate = package_bundle.source_digest(root)
    version = str(package_bundle.load_recipe((root / package_bundle.MAIN).read_bytes())['version'])
    out = Path(out) if out else root / 'dist' / PACKAGE_ID / f'{version}-candidate-{candidate[:12]}'
    if out.exists() or out.is_symlink():
        raise FileExistsError(f'candidate path already exists: {out}')
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.fea-stage-', dir=out.parent) as temp:
        stage = Path(temp) / 'candidate'
        bundle = package_bundle.package(stage, root, candidate_digest=candidate)
        archive = Path(bundle['archive'])
        bundle['archive'] = archive.name
        channels = {'agentsai': bundle}
        for channel in PROJECTS:
            channels[channel] = project_archive(archive, channel, stage, root)
        channels['source'] = build_distribution.build(root, stage)
        if package_bundle.source_digest(root) != candidate:
            raise ValueError('source changed during build')
        manifest = {'schema_version': 1, 'package_id': PACKAGE_ID, 'version': version,
                    'candidate_source_digest': candidate, 'qualification': 'SOURCE_ONLY',
                    'channels': channels}
        (stage / 'distribution-manifest.json').write_bytes(json_bytes(manifest))
        (stage / 'SHA256SUMS.txt').write_text(
            ''.join(f'{sha(path.read_bytes())}  {path.name}\n' for path in sorted(stage.iterdir())),
            encoding='ascii', newline='\n')
        stage.rename(out)
    return {**manifest, 'output_directory': str(out)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--candidate-digest', action='store_true')
    args = parser.parse_args()
    print(package_bundle.source_digest(ROOT) if args.candidate_digest else json.dumps(build(args.out), indent=2))
