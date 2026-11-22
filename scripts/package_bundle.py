"""Package the Simcenter 3D FEA Expert Agent Workspace product bundle strictly from canonical sources.

Layout (must match the host loader):
  recipes/fea-expert-agent.yaml                main agent (YAML, has sub_recipes)
  recipes/subrecipes/<name>.yaml               every sub_recipes target, nothing else at recipes/ root
  skills/<skill>/...                           canonical 40 skills
  readme/README.md
Never copies an installed/extracted bundle. Usage:
  python scripts/package_bundle.py [--out dist/simcenter-fea-expert/<ver>]
"""
from pathlib import Path
import argparse, json, re, tomllib

try:
    from .package_identity import (BUNDLE_MANIFEST, PACKAGE_ID, add_manifest,
                                   content_digest, read_zip, sha, verify_files, write_zip)
    from .validate_distribution import distribution_files
except ImportError:
    from package_identity import (BUNDLE_MANIFEST, PACKAGE_ID, add_manifest,
                                  content_digest, read_zip, sha, verify_files, write_zip)
    from validate_distribution import distribution_files
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
MAIN = 'recipes/fea-expert-agent.yaml'
EXPECTED_SUBRECIPES = {
    'fea-model-inspector',
    'fea-journal-author',
    'fea-solver-diagnostics',
    'fea-results-post',
    'fea-verifier',
    'product-support-agent',
}
def load_recipe(raw):
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8')
    return YAML(typ='safe').load(raw)


def collect(root=ROOT):
    main = load_recipe((root / MAIN).read_text(encoding='utf-8'))
    files = {MAIN: (root / MAIN).read_bytes()}
    for sr in main.get('sub_recipes', []):
        rel = (Path('recipes') / sr['path']).as_posix().replace('/./', '/')
        files[rel] = (root / rel).read_bytes()
    for p in sorted((root / 'skills').rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc':
            files[p.relative_to(root).as_posix()] = p.read_bytes()
    readme = root / 'README.md'
    repository = json.loads((root / 'plugin.json').read_bytes())['repository'].rstrip('/')
    # Agent Workspace includes the README by itself. Route its repository links to GitHub.
    files['readme/README.md'] = re.sub(
        rb'(\]\()((?![a-zA-Z][a-zA-Z0-9+.-]*:|[/#])[^)\s]+)(\))',
        lambda match: match[1] + f'{repository}/blob/main/'.encode() + match[2] + match[3],
        readme.read_bytes(),
    )
    return main, files


def check_layout(names, main):
    """Return list of violations for a bundle namelist and its main recipe dict."""
    errs = []
    subs = main.get('sub_recipes') or []
    if {s.get('name') for s in subs} != EXPECTED_SUBRECIPES:
        errs.append('sub_recipes must be exactly %s' % sorted(EXPECTED_SUBRECIPES))
    for s in subs:
        rel = (Path('recipes') / s['path']).as_posix().replace('/./', '/')
        if not rel.startswith('recipes/subrecipes/'):
            errs.append('sub recipe outside recipes/subrecipes: ' + rel)
        if rel not in names:
            errs.append('missing sub recipe file: ' + rel)
    roots = [n for n in names if n.startswith('recipes/') and n.count('/') == 1]
    if roots != [MAIN]:
        errs.append('recipes/ root must hold only the main agent, found %s' % roots)
    if not any(n.startswith('skills/') and n.endswith('/SKILL.md') for n in names):
        errs.append('no skills')
    return errs


def source_digest(root):
    return content_digest({p.relative_to(root).as_posix(): p.read_bytes()
                           for p in distribution_files(root)})


def package(out, root=ROOT, *, candidate_digest=None):
    main, files = collect(root)
    version = str(main['version'])
    metadata = (root / '.sim-ai-agents.toml').read_bytes()
    spec = tomllib.loads(metadata.decode('utf-8'))['bundle']
    if spec['id'] != PACKAGE_ID or spec['version'] != version:
        raise ValueError('bundle metadata and recipe identity differ')
    for name, raw in files.items():
        if name.startswith('recipes/') and (str(load_recipe(raw)['version']) != version
                or load_recipe(raw)['bundle'] != f'{PACKAGE_ID}-{version}'):
            raise ValueError(f'recipe identity mismatch: {name}')
    if errors := check_layout(list(files), main):
        raise ValueError('layout invalid: ' + '; '.join(errors))
    files = add_manifest(files, BUNDLE_MANIFEST, version=version, channel='agentsai',
                         candidate_digest=candidate_digest or source_digest(root))
    out = Path(out)
    archive = out / 'agents-artefact-windows.zip'
    if archive.is_symlink() or out.is_symlink():
        raise ValueError('unsafe output path')
    write_zip(archive, files)
    manifest = verify_files(read_zip(archive), BUNDLE_MANIFEST, 'agentsai')
    (out / '.sim-ai-agents.toml').write_bytes(metadata)
    return {'version': version, 'archive': str(archive), 'sha256': sha(archive.read_bytes()),
            'files': len(files), 'content_digest': manifest['content_digest'],
            'candidate_source_digest': manifest['candidate_source_digest']}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out')
    a = ap.parse_args()
    v = str(load_recipe((ROOT / MAIN).read_text(encoding='utf-8'))['version'])
    print(json.dumps(package(a.out or ROOT / 'dist/simcenter-fea-expert' / v), indent=2))
