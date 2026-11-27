"""Local operation journal for an existing, authorized Siemens MCP session."""
import argparse
import ast
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import stat
import tempfile
import time


EFFECTS = {
    'designcenter': {
        'dcopen-execute-tool': {'CAE_MUTATION', 'DECK_EXPORT'},
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


def strict_json_load(path, max_bytes):
    def unique(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise ValueError(f'duplicate JSON key: {key}')
            result[key] = value
        return result

    with Path(path).open('rb') as stream:
        data = stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError('JSON document exceeds the supported size')
    value = json.loads(data.decode('utf-8'), object_pairs_hook=unique)
    canonical(value)
    return value


def reject_alias(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        raise ValueError('controller file must not be an alias or reparse point')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def response_failed(raw):
    if not isinstance(raw, dict) or raw.get('isError') or 'error' in raw:
        return True
    payloads = [raw, raw.get('structuredContent')]
    if not isinstance(raw.get('content', []), list):
        return True
    for block in raw.get('content', []):
        if isinstance(block, dict) and block.get('type') == 'text':
            try:
                payloads.append(json.loads(block.get('text', '')))
            except ValueError:
                continue
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        status = payload.get('toolExecutionStatus')
        body = payload.get('toolResponse')
        if (status and status != 'ToolExecutionStatus::Completed'
                or isinstance(body, dict) and body.get('error')):
            return True
    return False


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


def export_journal(target, fem, solution_tag):
    """Render the only journal admitted as DECK_EXPORT (qualified 2612 build)."""
    sim = target['model']
    if (target['release'] != '2612.1700' or not isinstance(sim, str)
            or not isinstance(fem, str) or not PureWindowsPath(sim).is_absolute()
            or not PureWindowsPath(fem).is_absolute() or not sim.lower().endswith('.sim')
            or not fem.lower().endswith('.fem') or not isinstance(solution_tag, str)
            or not re.fullmatch(r'[1-9][0-9]*', solution_tag)):
        raise ValueError('export requires qualified build, exact SIM/FEM paths and solution tag')
    return f"""import NXOpen
import NXOpen.CAE

def main(args):
    parts = NXOpen.Session.GetSession().Parts
    work = parts.BaseWork
    if (not isinstance(work, NXOpen.CAE.SimPart) or work.FullPath.lower() != {sim.lower()!r}
            or not parts.BaseDisplay or parts.BaseDisplay.Tag != work.Tag
            or not work.FemPart or work.FemPart.FullPath.lower() != {fem.lower()!r}):
        raise RuntimeError('Work/display/FEM identity mismatch')
    for solution in work.Simulation.Solutions:
        if str(solution.Tag) == {solution_tag!r}:
            if solution.SolutionType != 'SEMODES 103':
                raise RuntimeError('Expected SEMODES 103')
            solution.Solve(NXOpen.CAE.SimSolution.SolveOption.WriteSolverInputFile,
                           NXOpen.CAE.SimSolution.SetupCheckOption.CompleteCheckAndOutputErrors)
            return str(solution.Tag)
    raise RuntimeError('Qualified solution tag not found')
"""


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

    def snapshot(self):
        path = self.state
        reject_alias(path)
        if not path.exists():
            return {'operations': {}}
        state = strict_json_load(path, max_bytes=64 * 1024 * 1024)
        if (type(state) is not dict or type(state.get('operations')) is not dict
                or set(state) - {'operations', 'identity', 'license_stop', 'runtime_v1'}):
            raise ValueError('unrecognized controller state')
        if any(type(record) is not dict or 'status' not in record for record in state['operations'].values()):
            raise ValueError('corrupt legacy controller state')
        return state

    @contextmanager
    def edit(self):
        path = self.root / 'controller.lock'
        reject_alias(path)
        with path.open('a+b') as lock:
            deadline = time.monotonic() + 5
            lock.seek(0)
            while True:
                try:
                    if os.name == 'nt':
                        import msvcrt
                        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError as exc:
                    if time.monotonic() >= deadline:
                        raise TimeoutError('controller ledger lock is busy') from exc
                    time.sleep(0.025)
            state = self.snapshot()
            yield state
            if len(canonical(state)) + 1 > 64 * 1024 * 1024:
                raise ValueError('controller ledger has reached its size limit')
            save(self.state, state)

    def transition(self, action, **payload):
        """Admit v1 operations using this controller's existing ledger and lock."""
        from fea_runtime import operations

        handlers = {'prepare': operations.prepare, 'reserve': operations.reserve,
                    'record': operations.record_response, 'observe': operations.observe,
                    'reconcile': operations.observe}
        if action == 'reconcile':
            payload['reconcile'] = True
        return handlers[action](self, **payload)

    @staticmethod
    def _legacy_writer(state):
        if state.get('runtime_v1', {}).get('operations'):
            raise ValueError('legacy dispatch is disabled after v1 admission in this root')

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
            if effect == 'DECK_EXPORT':
                before, after = (operation.get(k, {}) for k in ('baseline', 'expected'))
                deck = PureWindowsPath(after.get('deck_path', ''))
                if (arguments['python_code'] != export_journal(target, binding.get('fem'),
                                                               binding.get('solution_tag'))
                        or before.get('deck_path') != after.get('deck_path')
                        or deck.parent != PureWindowsPath(target['model']).parent
                        or deck.suffix.lower() not in {'.dat', '.bdf', '.nas'}
                        or before.get('deck_present') is not False
                        or after.get('deck_present') is not True
                        or after.get('export_finished') is not True
                        or after.get('deck_qualified') is not True
                        or not before.get('original_solution_signature')
                        or after.get('original_solution_signature') != before['original_solution_signature']):
                    raise ValueError('export requires the exact template and preflighted fresh target')
            else:
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
            self._legacy_writer(state)
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
            self._legacy_writer(state)
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
            unknown = transport_error or license_stop or response_failed(raw)
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
            elif matches(baseline) and (record['request']['effect'] != 'DECK_EXPORT'
                                        or witnesses.get('export_finished') is True):
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
