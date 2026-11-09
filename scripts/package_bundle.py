"""Package the Simcenter 3D FEA Expert Agent Workspace product bundle strictly from canonical sources.

Layout (must match the host loader):
  recipes/fea-expert-agent.yaml                main agent (YAML, has sub_recipes)
  recipes/subrecipes/<name>.yaml               every sub_recipes target, nothing else at recipes/ root
  skills/<skill>/...                           canonical 38 skills
  readme/README.md
Never copies an installed/extracted bundle. Usage:
  python scripts/package_bundle.py [--out dist/simcenter-fea-expert/<ver>]
"""
from pathlib import Path
import argparse, hashlib, json, zipfile
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
TOML = '''schema_version = "1"

[bundle]
id = "simcenter-fea-expert"
name = "Simcenter 3D FEA Expert"
version = "{v}"
description = "Route Simcenter 3D FEA requests through expert FEA skills and specialist subagents, reusing the host-managed Simcenter 3D, Designcenter Open and Product Support MCPs."
os = ["windows"]
homepage = "https://github.com/haydarrjr/simcenter-fea-expert-bundle"
tags = ["simcenter", "fea", "cae", "nastran"]

[dependencies]
products = ["Simcenter 3D 2612"]

[[contacts]]
role = "maintainer"
name = "FEA Expert Bundle Maintainers"
url = "https://github.com/haydarrjr/simcenter-fea-expert-bundle"

[[contributions]]
type = "recipes"
source = "recipes/"

[[contributions]]
type = "skills"
source = "skills/"

[[contributions]]
type = "readme"
source = "README.md"

[compat]
product = "Simcenter 3D 2612"
shell = "*"
'''


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
    files['readme/README.md'] = readme.read_bytes()
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


def package(out, root=ROOT):
    main, files = collect(root)
    v = str(main['version'])
    errs = check_layout(set(files), main)
    if errs:
        raise SystemExit('layout invalid: ' + '; '.join(errs))
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    zp = out / 'agents-artefact-windows.zip'
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in sorted(files):
            info = zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, files[n])
    (out / '.sim-ai-agents.toml').write_text(TOML.format(v=v), encoding='utf-8')
    with zipfile.ZipFile(zp) as z:
        errs = check_layout(set(z.namelist()), load_recipe(z.read(MAIN)))
    if errs:
        raise SystemExit('built archive invalid: ' + '; '.join(errs))
    return {'version': v, 'archive': str(zp), 'sha256': hashlib.sha256(zp.read_bytes()).hexdigest(), 'files': len(files)}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out')
    a = ap.parse_args()
    v = str(load_recipe((ROOT / MAIN).read_text(encoding='utf-8'))['version'])
    print(json.dumps(package(a.out or ROOT / 'dist/simcenter-fea-expert' / v), indent=2))
