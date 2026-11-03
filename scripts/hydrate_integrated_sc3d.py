"""Hydrate only receipt-pinned Siemens files from an authorized local bundle.

Does not change source.json, fetch anything, or grant redistribution permission.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile


def hydrate(archive: Path, destination: Path) -> int:
    receipt_path = destination / 'source.json'
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    if hashlib.sha256(archive.read_bytes()).hexdigest() != receipt['source_archive_sha256']:
        raise RuntimeError('Archive SHA256 differs from the approved source receipt')
    pending = []
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise RuntimeError('Duplicate archive entries')
        for name, digest in receipt['files'].items():
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
                raise RuntimeError('Unsafe receipt path')
            target = destination.joinpath(*path.parts)
            ancestors = [target, *target.parents]
            if any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()) for p in ancestors):
                raise RuntimeError('Refuse linked destination')
            data = z.read(name)
            if hashlib.sha256(data).hexdigest() != digest:
                raise RuntimeError('Payload SHA256 differs: ' + name)
            if target.exists() and target.read_bytes() != data:
                raise RuntimeError('Refuse to overwrite differing local payload: ' + name)
            pending.append((target, data))
    # Validate every source before writing any file; exclusive creation protects existing data.
    for target, data in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with target.open('xb') as out:
                out.write(data)
    return len(pending)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archive', type=Path)
    ap.add_argument('--destination', type=Path, default=Path('integration/simcenter-3d'))
    args = ap.parse_args()
    print(json.dumps({'hydrated_files': hydrate(args.archive, args.destination), 'redistribution': 'LOCAL_ONLY'}))


if __name__ == '__main__':
    main()
