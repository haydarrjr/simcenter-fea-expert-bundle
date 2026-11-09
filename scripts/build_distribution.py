"""Build the explicit portable source allowlist and AgentAI bundle archive."""
from pathlib import Path
import hashlib, json
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from ruamel.yaml import YAML
try:
    from .validate_distribution import ROOT, distribution_files, validate
except ImportError:
    from validate_distribution import ROOT, distribution_files, validate


def build(root=ROOT):
    result = validate(root)
    recipe = YAML(typ='safe').load((root / 'recipes/fea-expert-agent.yaml').read_text(encoding='utf-8'))
    ver = str(recipe.get('version', '0.1.2'))
    out = root / 'dist'
    out.mkdir(exist_ok=True)
    archive = out / f'simcenter-fea-expert-source-{ver}.zip'
    if archive.is_symlink() or out.is_symlink():
        raise ValueError('unsafe output path')
    with ZipFile(archive, 'w', compression=ZIP_DEFLATED) as z:
        for p in distribution_files(root):
            info = ZipInfo(p.relative_to(root).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            z.writestr(info, p.read_bytes())
    result.update(
        version=ver,
        archive=archive.name,
        sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        artifact='SOURCE_ARCHIVE_ONLY',
    )
    (out / 'source-manifest.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
