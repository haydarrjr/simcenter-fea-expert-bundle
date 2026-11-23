"""Build the explicit portable source allowlist and AgentAI bundle archive."""
from pathlib import Path
import hashlib, json
from ruamel.yaml import YAML
try:
    from .package_identity import write_zip
    from .validate_distribution import ROOT, distribution_files, validate
except ImportError:
    from package_identity import write_zip
    from validate_distribution import ROOT, distribution_files, validate


def build(root=ROOT, out=None):
    result = validate(root)
    recipe = YAML(typ='safe').load((root / 'recipes/fea-expert-agent.yaml').read_text(encoding='utf-8'))
    ver = str(recipe['version'])
    out = Path(out) if out is not None else root / 'dist'
    out.mkdir(parents=True, exist_ok=True)
    archive = out / f'simcenter-fea-expert-source-{ver}.zip'
    if archive.is_symlink() or out.is_symlink():
        raise ValueError('unsafe output path')
    files = {p.relative_to(root).as_posix(): p.read_bytes() for p in distribution_files(root)}
    write_zip(archive, files)
    result.update(
        version=ver,
        archive=archive.name,
        sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        artifact='SOURCE_ARCHIVE_ONLY',
    )
    (out / 'source-manifest.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    return result


if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
