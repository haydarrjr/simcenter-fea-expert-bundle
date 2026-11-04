"""Capture approved installed official SC3D launcher/agent/skill bytes for local bundling."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archive', type=Path)
    ap.add_argument('--destination', type=Path, required=True)
    args = ap.parse_args()
    receipt_path = args.destination / 'source.json'
    if receipt_path.exists():
        raise SystemExit('Capture already exists; refuse to replace provenance')
    hashes = {}
    with zipfile.ZipFile(args.archive) as z:
        for n in z.namelist():
            p = PurePosixPath(n)
            if n.endswith('/'):
                continue
            if n.startswith('skills/'):
                if '..' in p.parts or p.is_absolute() or '\\' in n:
                    raise RuntimeError('Unsafe upstream archive entry')
                dst = args.destination.joinpath(*p.parts)
                dst.parent.mkdir(parents=True, exist_ok=True)
                data = z.read(n)
                dst.write_bytes(data)
                hashes[n] = hashlib.sha256(data).hexdigest()
    receipt = dict(source_bundle_id='simcenter-3d', source_version='1.0.0-canary.30', source_archive_name=args.archive.name,
                   source_archive_sha256=hashlib.sha256(args.archive.read_bytes()).hexdigest(), files=hashes,
                   redistribution_scope='LOCAL_CUSTOM_BUNDLE_ONLY; no public redistribution clearance established')
    receipt_path.write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(files=len(hashes),skills=sum(n.endswith('/SKILL.md') for n in hashes),recipes=sum(n.startswith('recipes/') for n in hashes),launchers=sum(n.startswith('mcps/') for n in hashes)),indent=2))


if __name__ == '__main__':
    main()
