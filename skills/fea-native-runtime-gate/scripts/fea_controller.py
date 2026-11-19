"""Local operation journal for an existing, authorized Siemens MCP session."""
import argparse
import ast
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


EFFECTS = {
    'designcenter': {
        'dcopen-execute-tool': {'CAE_MUTATION'},
        'read-model-data': {'PURE_READ'},
    },
    'simcenter3d': {
        'part-info-tool': {'PURE_READ'}, 'mesh-info-tool': {'PURE_READ'},
        'surface-mesh-generation-tool': {'CAE_MUTATION'},
        'solid-mesh-generation-tool': {'CAE_MUTATION'},
    },
    'batchpost': {'contour': {'FILE_MUTATION'}, 'graphi': {'FILE_MUTATION'}},
}
PENDING = {'DISPATCH_RESERVED', 'OBSERVATION_REQUIRED', 'UNKNOWN'}


def canonical(value):
    return json.dumps(value, sort_keys=True, allow_nan=False, ensure_ascii=False,
                      separators=(',', ':')).encode('utf-8', errors='strict')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def normalize_journal(source):
    source = source.removeprefix('\ufeff')
    tree = ast.parse(source)
    entries = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main']
    if (len(entries) != 1 or [arg.arg for arg in entries[0].args.args] != ['args']
            or entries[0].args.posonlyargs or entries[0].args.kwonlyargs
            or entries[0].args.vararg or entries[0].args.kwarg or entries[0].args.defaults):
        raise ValueError('live journal requires exactly one main(args) entry point')
    blocked = {'exec', 'eval', 'compile', 'open', '__import__', 'getattr', 'setattr', 'globals',
               'locals', 'Save', 'SaveAs', 'SaveAll', 'UndoToMark', 'Exit', 'Solve', 'Submit'}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [node.module] if not node.level else [None]
        else:
            modules = []
        if any(not module or (module not in {'math', 'collections', 'NXOpen'} and
               (not module.startswith('NXOpen.') or module.split('.')[:2] == ['NXOpen', 'UF']))
               for module in modules):
            raise ValueError('journal import is outside the prepared sandbox profile')
        if ((isinstance(node, ast.Name) and node.id in blocked) or
                (isinstance(node, ast.Attribute) and (node.attr in blocked or
                                                       node.attr.startswith('__')))):
            raise ValueError('journal uses an unsupported or separately qualified operation')
    return source


def save(path, value):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        temp = Path(temporary.name)
        try:
            temporary.write(canonical(value) + b'\n')
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary.close()
            os.replace(temp, path)
        finally:
            temporary.close()
            temp.unlink(missing_ok=True)


class Controller:
    """Persist admission, raw receipts and independent observations across restarts."""

    def __init__(self, directory):
        self.root = Path(directory).resolve(strict=True)
        self.state = self.root / 'controller-state.json'

    @contextmanager
    def edit(self):
        with (self.root / 'controller.lock').open('a+b') as lock:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            state = json.loads(self.state.read_bytes()) if self.state.exists() else {'operations': {}}
            yield state
            save(self.state, state)

    def prepare(self, operation, binding, authorization=None):
        name = operation['operation_id']
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,95}', name):
            raise ValueError('invalid operation id')
        profile, tool, effect = (operation[k] for k in ('profile', 'tool', 'effect'))
        if effect not in EFFECTS.get(profile, {}).get(tool, ()):
            raise ValueError('tool and effect need a qualified FEA route')
        target = operation['target']
        if (target != binding.get('target') or any(not target.get(k) for k in
                ('session', 'release', 'owner', 'model', 'revision')) or not binding.get('evidence_ref')):
            raise ValueError('current host/model evidence is required')
        if binding.get('profile') != profile or binding.get('schema', {}).get('name') != tool:
            raise ValueError('current profile and exact advertised tool are required')
        schema = binding['schema']['inputSchema']
        if schema.get('type') != 'object':
            raise ValueError('unsupported advertised tool schema')
        arguments = dict(operation['arguments'])
        props = schema.get('properties', {})
        if not set(schema.get('required', ())) <= arguments.keys() <= props.keys():
            raise ValueError('payload keys differ from the current tool schema')
        for key, value in arguments.items():
            expected = {'string': str, 'integer': int, 'number': (float, int),
                        'boolean': bool, 'object': dict, 'array': list}.get(props[key].get('type'))
            if expected and (not isinstance(value, expected) or type(value) is bool and expected is not bool):
                raise ValueError(f'payload type differs from the current schema: {key}')
        if tool == 'dcopen-execute-tool':
            if arguments.keys() != {'python_code'}:
                raise ValueError('prepared live execute accepts only python_code')
            arguments['python_code'] = normalize_journal(arguments['python_code'])
        request = {**operation, 'arguments': arguments}
        request_digest = digest(request)
        if not operation.get('expected'):
            raise ValueError('an independent acceptance witness is required')
        if effect != 'PURE_READ':
            if (not authorization or authorization.get('operation_digest') != request_digest
                    or not authorization.get('evidence_ref')
                    or not operation.get('baseline') or operation['expected'] == operation['baseline']):
                raise ValueError('effectful calls require hash-bound authorization and distinct witnesses')
        with self.edit() as state:
            identity = {k: target[k] for k in ('session', 'release', 'owner', 'model')}
            if state.get('identity', identity) != identity:
                raise ValueError('controller is bound to another native target')
            state['identity'] = identity
            records = state['operations']
            if name in records or any(record['status'] in PENDING for record in records.values()):
                raise ValueError('duplicate operation or unreconciled native effect')
            if state.get('license_stop'):
                raise ValueError('native license failure is still unresolved')
            if any(records.get(dep, {}).get('status') != 'ACCEPTED' for dep in operation.get('depends_on', [])):
                raise ValueError('operation has an unaccepted dependency')
            records[name] = {'status': 'PREPARED', 'request': request, 'request_digest': request_digest,
                             'binding_digest': digest(binding), 'authorization': authorization,
                             'prepared_at': now()}
        return records[name]

    def reserve(self, name, binding, request_digest):
        with self.edit() as state:
            records = state['operations']
            record = records[name]
            if state.get('license_stop') or any(r['status'] in PENDING for r in records.values()):
                raise ValueError('native dispatch is fenced')
            if (record['status'] != 'PREPARED' or request_digest != record['request_digest'] or
                    digest(binding) != record['binding_digest'] or digest(record['request']) != request_digest):
                raise ValueError('prepared payload or binding changed')
            record.update(status='DISPATCH_RESERVED', reserved_at=now())
        return record['request']

    def record(self, name, raw=None, transport_error=None):
        with self.edit() as state:
            record = state['operations'][name]
            if record['status'] != 'DISPATCH_RESERVED':
                raise ValueError('operation has no pending reservation')
            serialized = canonical(raw).decode('utf-8').lower()
            license_stop = 'licensed number of users already reached' in serialized or 'nx_design_token' in serialized
            unknown = raw is None or transport_error or license_stop or not isinstance(raw, dict) or raw.get('isError')
            record.update(status='UNKNOWN' if unknown else 'OBSERVATION_REQUIRED',
                          raw_response=raw, raw_digest=digest(raw), transport_error=transport_error,
                          response_at=now())
            if license_stop:
                state['license_stop'] = name
        return record

    def observe(self, name, observation):
        with self.edit() as state:
            record = state['operations'][name]
            expected = record['request'].get('expected', {})
            baseline = record['request'].get('baseline', {})
            target = record['request']['target']
            if record['status'] not in PENDING:
                raise ValueError('operation is not awaiting observation')
            actual = observation['target']
            issued = datetime.fromisoformat(observation['observed_at'])
            if (any(actual.get(k) != target[k] for k in ('session', 'release', 'owner', 'model'))
                    or not actual.get('revision') or not observation.get('evidence_ref')
                    or observation['evidence_ref'] == record.get('raw_digest')
                    or issued <= datetime.fromisoformat(record['reserved_at'])
                    or issued > datetime.now(timezone.utc)):
                raise ValueError('fresh independent observation of this target is required')
            witnesses = observation['witnesses']
            def matches(contract):
                return bool(contract) and all(key in witnesses and witnesses[key] == value
                                              for key, value in contract.items())
            if matches(expected):
                status = 'ACCEPTED'
            elif matches(baseline):
                status = 'NOT_APPLIED'
            else:
                status = 'UNKNOWN'
            record.setdefault('observations', []).append(observation)
            record.update(status=status, observed_at=now())
        return record


async def execute_one(controller, operation, binding, invoke, readback, authorization=None):
    """Use the caller's existing tool binding, with no server or transport creation."""
    prepared = controller.prepare(operation, binding, authorization)
    name = operation['operation_id']
    request = controller.reserve(name, binding, prepared['request_digest'])
    try:
        raw = await invoke(request['profile'], request['tool'], request['arguments'])
    except BaseException as exc:
        controller.record(name, transport_error=str(exc))
        raise
    controller.record(name, raw)
    observation = await readback(request)
    return controller.observe(name, observation)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'reserve', 'record', 'observe'))
    parser.add_argument('workdir', type=Path)
    parser.add_argument('request', type=Path)
    args = parser.parse_args()
    controller = Controller(args.workdir)
    payload = json.loads(args.request.read_text(encoding='utf-8-sig'))
    print(json.dumps(getattr(controller, args.command)(**payload), indent=2, ensure_ascii=False))
