"""Deterministic package I/O and identity checks shared by all FEA channels."""
import hashlib
import json
import ntpath
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


PACKAGE_ID = 'simcenter-fea-expert'
BUNDLE_MANIFEST = 'skills/fea-native-runtime-gate/package-manifest.json'
DIGEST = re.compile(r'[0-9a-f]{64}')
VERSION = re.compile(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[a-zA-Z0-9.-]+)?')


def windows_reserved(part):
    check = getattr(ntpath, 'isreserved', None)
    return check(part) if check is not None else PureWindowsPath(part).is_reserved()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def read_json(raw):
    return json.loads(raw, object_pairs_hook=unique_object)


def check_paths(names):
    seen = set()
    for name in names:
        path = PurePosixPath(name)
        if (not name or path.as_posix() != name or path.is_absolute() or
                any(part in ('.', '..') or part.endswith((' ', '.')) or
                    windows_reserved(part) for part in path.parts) or
                re.search(r'[\\:*?"<>|\x00-\x1f]', name)):
            raise ValueError(f'unsafe package path: {name!r}')
        folded = name.casefold()
        if folded in seen:
            raise ValueError(f'duplicate or case-colliding path: {name}')
        seen.add(folded)
    for name in seen:
        if any(parent.as_posix() in seen for parent in PurePosixPath(name).parents):
            raise ValueError(f'file/directory collision: {name}')


def atomic_write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = tempfile.NamedTemporaryFile(dir=path.parent, delete=False)
    temp = Path(stream.name)
    try:
        with stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def write_zip(path, files):
    check_paths(files)
    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, 'w', ZIP_DEFLATED) as archive:
        for name, raw in sorted(files.items()):
            entry = ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (stat.S_IFREG | 0o644) << 16
            entry.compress_type = ZIP_DEFLATED
            archive.writestr(entry, raw)


def read_zip(path):
    with ZipFile(path) as archive:
        entries = archive.infolist()
        check_paths(entry.filename for entry in entries)
        if any(entry.is_dir() or stat.S_IFMT(entry.external_attr >> 16)
               not in (0, stat.S_IFREG) for entry in entries):
            raise ValueError('package members must be regular files')
        return {entry.filename: archive.read(entry) for entry in entries}


def file_hashes(files):
    return {name: sha(raw) for name, raw in sorted(files.items())}


def content_digest(files):
    return sha(json_bytes(file_hashes(files)))


def add_manifest(files, name, *, version, channel, candidate_digest):
    return {**files, name: json_bytes({
        'schema_version': 1, 'package_id': PACKAGE_ID, 'version': version,
        'channel': channel, 'candidate_source_digest': candidate_digest,
        'content_digest': content_digest(files), 'files': file_hashes(files),
    })}


def verify_files(files, manifest_name, channel, *, exact=True):
    manifest = read_json(files[manifest_name])
    if (manifest['schema_version'] != 1 or manifest['package_id'] != PACKAGE_ID or
            manifest['channel'] != channel or not VERSION.fullmatch(manifest['version']) or
            not DIGEST.fullmatch(manifest['candidate_source_digest'])):
        raise ValueError('unexpected FEA manifest identity')
    expected = manifest['files']
    check_paths(expected)
    if manifest_name in expected:
        raise ValueError('manifest includes itself')
    if exact and set(files) != set(expected) | {manifest_name}:
        raise ValueError('package inventory differs from manifest')
    if not expected.keys() <= files.keys():
        raise ValueError('package is missing manifest resources')
    managed = {name: files[name] for name in expected}
    actual = file_hashes(managed)
    if actual != expected or content_digest(managed) != manifest['content_digest']:
        raise ValueError('package bytes differ from manifest')
    return manifest


def project_path(root, name):
    """Reject symlinks/junctions and escaped parents before reading or writing."""
    check_paths([name])
    current = root
    for part in PurePosixPath(name).parts:
        current = current / part
        if (current.is_symlink() or getattr(current, 'is_junction', lambda: False)()
                or not current.resolve().is_relative_to(root)):
            raise ValueError(f'linked or escaping package destination: {current}')
    return current


def attest_tree(root, manifest_name, channel):
    root = Path(root).resolve(strict=True)
    raw = project_path(root, manifest_name).read_bytes()
    manifest = read_json(raw)
    files = {name: project_path(root, name).read_bytes() for name in manifest['files']}
    return verify_files({**files, manifest_name: raw}, manifest_name, channel)
