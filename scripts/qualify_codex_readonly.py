"""Verify Model Inspection and Designcenter Open in one fresh Codex app-server thread."""
import argparse
from ast import literal_eval
from datetime import datetime, timezone
import json
import ntpath
import os
from pathlib import Path
import queue
import re
import subprocess
from threading import Thread
import tomllib

if __package__:
    from .install_project import attest
    from .package_identity import atomic_write, json_bytes
    from .render_mcp_config import profiles, toml_value
else:
    from install_project import attest
    from package_identity import atomic_write, json_bytes
    from render_mcp_config import profiles, toml_value


MATCH_FIELDS = ('name', 'filePath', 'isWorkPart', 'isDisplayPart', 'isModified')
CAE_PART_KEYS = ('path', 'isCurrentPart', 'isDisplayPart', 'isModified')
CAE_PART_SUFFIXES = {'.sim', '.fem', '.afm'}
NXOPEN_PART_ROLES = """import NXOpen

def main(args):
    parts = NXOpen.Session.GetSession().Parts
    work, display = parts.BaseWork, parts.BaseDisplay
    if not work or not display:
        raise ValueError("Expected loaded work and display parts")
    return {'parts': [
        {'filePath': part.FullPath, 'isWorkPart': part.Tag == work.Tag,
         'isDisplayPart': part.Tag == display.Tag, 'isModified': part.IsModified}
        for part in parts if part.Tag in (work.Tag, display.Tag)
    ]}
"""


class AppServer:
    def __init__(self, command, cwd, stderr):
        self.process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=stderr, text=True, encoding='utf-8', errors='strict')
        self.inbox = queue.Queue()
        self.identifier = 0
        Thread(target=self._read, daemon=True).start()

    def _read(self):
        try:
            for line in self.process.stdout:
                self.inbox.put(json.loads(line))
        finally:
            self.inbox.put(None)

    def send(self, message):
        self.process.stdin.write(json.dumps(message) + '\n')
        self.process.stdin.flush()

    def request(self, method, params, timeout=110):
        from time import monotonic
        self.identifier += 1
        self.send({'id': self.identifier, 'method': method, 'params': params})
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            try:
                response = self.inbox.get(timeout=max(0, deadline - monotonic()))
            except queue.Empty:
                break
            if response is None:
                raise RuntimeError('Codex app-server closed the transport')
            if response.get('id') == self.identifier:
                if 'error' in response:
                    raise RuntimeError(f'{method}: {response["error"]}')
                return response['result']
            if 'method' in response and 'id' in response:
                self.send({'id': response['id'], 'error': {'code': -32000,
                          'message': 'Unattended read-only qualification cannot approve server requests'}})
        raise TimeoutError(f'Codex app-server request exceeded waiting time: {method}')

    def close(self):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=5)
        finally:
            self.process.stdout.close()


def response_object(result):
    if result.get('isError'):
        raise ValueError('MCP returned isError')
    value = result.get('structuredContent')
    if not isinstance(value, dict):
        blocks = result['content']
        strings = [block['text'] for block in blocks if block['type'] == 'text']
        if len(strings) != 1:
            raise ValueError('expected one JSON result or structured content')
        value = json.loads(strings[0])
    if value.get('toolExecutionStatus') != 'ToolExecutionStatus::Completed':
        raise ValueError('native operation did not report completion')
    return value['toolResponse']


def find_rows(value, fields):
    if isinstance(value, list):
        return [row for item in value for row in find_rows(item, fields)]
    if isinstance(value, dict):
        if set(fields) <= value.keys():
            return [value]
        return [row for item in value.values() for row in find_rows(item, fields)]
    return []


def compare_targets(design, inspection):
    dkeys = ('filePath', 'isWorkPart', 'isDisplayPart', 'isModified')
    skeys = ('path', 'isCurrentPart', 'isDisplayPart', 'isModified')

    def current(rows, keys):
        selected = [r for r in rows if r[keys[1]] is True or r[keys[2]] is True]
        if not selected or any(not isinstance(r[keys[0]], str) or not ntpath.isabs(r[keys[0]])
                               or any(type(r[k]) is not bool for k in keys[1:]) for r in selected):
            raise ValueError('no usable absolute-path work/display identity')
        result = {ntpath.normcase(ntpath.normpath(r[keys[0]])): tuple(r[k] for k in keys[1:])
                  for r in selected}
        if len(result) != len(selected) or sum(roles[0] for roles in result.values()) != 1 or (
                sum(roles[1] for roles in result.values()) != 1):
            raise ValueError('ambiguous work/display identity')
        return result

    left = current(find_rows(design, dkeys), dkeys)
    right = current(find_rows(inspection, skeys), skeys)
    if left != right:
        raise ValueError('work/display path or dirty state differs across profiles')
    return left


def read_design_roles(call, inspection):
    active = [part for part in find_rows(inspection, CAE_PART_KEYS)
              if part['isCurrentPart'] or part['isDisplayPart']]
    if any(isinstance(part['path'], str) and ntpath.splitext(part['path'])[1].lower() in CAE_PART_SUFFIXES
           for part in active):
        result = response_object(call('designcenter', 'dcopen-execute-tool', {'python_code': NXOPEN_PART_ROLES}))
        return literal_eval(result['result']), 'nxopen_part_roles'
    schema = response_object(call('designcenter', 'explore-model-structure', {
        'application': ['modeling'], 'userQuery': 'Discover PartInfo for work and display part identity.'}))
    part_info = next(entity for domain in schema['domain'] if domain['name'] == 'modeling'
                     for entity in domain['entities'] if entity['name'] == 'PartInfo')
    if not set(MATCH_FIELDS) <= {field['name'] for field in part_info['scalar_properties']}:
        raise ValueError('current modeling schema does not contain the required PartInfo fields')
    extraction = {'domain': [{'name': 'modeling', 'entities': [
        {'name': 'PartInfo', 'scalar_properties': list(MATCH_FIELDS)}]}]}
    result = response_object(call('designcenter', 'read-model-data', {'schemaForExtraction': json.dumps(extraction)}))
    if result.get('hasMoreData'):
        raise ValueError('incomplete PartInfo evidence; additional pages are required')
    return result, 'modeling_part_info'


def trusted_backend_pid(folder):
    pids = set()
    for log in folder.glob('*.log'):
        pids.update(int(raw) for raw in re.findall(
            r'\[pipe-security\] Trust check passed for server PID (\d+)',
            log.read_text(encoding='utf-8', errors='replace')))
    if len(pids) != 1:
        raise ValueError(f'no unique trusted native server PID in {folder.name} logs')
    return pids.pop()


def qualify(project, product, out, codex):
    project = Path(project).resolve(strict=True)
    out = Path(out).resolve()
    receipt = attest(project, 'codex')
    servers = profiles(project, product, logs=out / 'vendor')
    # This harness dispatches only the fixed read-only NXOpen role query.
    servers['designcenter']['enabled_tools'].append('dcopen-execute-tool')
    names = tuple(servers)
    # Override enablement for this child only. Existing Codex and MCP config files stay intact.
    config = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')) / 'config.toml'
    if config.is_file():
        existing = tomllib.loads(config.read_text(encoding='utf-8-sig')).get('mcp_servers', {})
        servers.update({key: {'enabled': False} for key in existing if key not in names})
    out.mkdir(parents=True)
    evidence = {'status': 'INCOMPLETE', 'candidate_source_digest': receipt['candidate_source_digest'],
                'project_content_digest': receipt['content_digest'], 'profiles': {},
                'observed_at': datetime.now(timezone.utc).isoformat(),
                'model_mutation': 'NOT_RUN', 'solver': 'NOT_RUN'}
    try:
        with (out / 'codex.stderr.log').open('w', encoding='utf-8') as stderr:
            client = AppServer([codex, 'app-server', '-c', 'mcp_servers=' + toml_value(servers)],
                               project, stderr)
            try:
                evidence['codex'] = client.request('initialize', {
                    'clientInfo': {'name': 'simcenter-fea-qualification', 'version': '0.1.0'},
                    'capabilities': {'experimentalApi': True}})
                client.send({'method': 'initialized'})
                skills = client.request('skills/list', {'cwds': [str(project)], 'forceReload': True})
                root = project / '.agents/skills'
                found = {s['name'] for group in skills['data'] for s in group['skills']
                         if Path(s['path']).resolve().is_relative_to(root)}
                wanted = {n.split('/')[2] for n in receipt['installed_files'] if n.endswith('/SKILL.md')}
                evidence['skills'] = sorted(found)
                if found != wanted:
                    raise ValueError('Codex discovered a different FEA skill inventory')
                thread = client.request('thread/start', {
                    'cwd': str(project), 'ephemeral': True, 'approvalPolicy': 'never', 'sandbox': 'read-only'})
                thread_id = thread['thread']['id']
                evidence['thread_id'] = thread_id

                def call(name, tool, arguments):
                    state = evidence['profiles'][name]
                    schema = state['tools'][tool]['inputSchema']
                    if not set(schema.get('required', [])) <= arguments.keys() <= schema.get('properties', {}).keys():
                        raise ValueError(f'arguments differ from current schema for {name}/{tool}')
                    result = client.request('mcpServer/tool/call', {
                        'threadId': thread_id, 'server': name, 'tool': tool, 'arguments': arguments})
                    state.setdefault('calls', []).append({'tool': tool, 'arguments': arguments, 'response': result})
                    if result.get('isError'):
                        raise ValueError(f'{name}/{tool} returned isError')
                    return result

                for name in names:
                    catalog = client.request('mcpServerStatus/list', {
                        'threadId': thread_id, 'serverName': name, 'detail': 'toolsAndAuthOnly'})
                    state = next(server for server in catalog['data'] if server['name'] == name)
                    evidence['profiles'][name] = state
                    status = call(name, 'dc_connection_status', {})
                    if not any(block.get('text', '').startswith('Connected to ')
                               for block in status['content']):
                        raise ValueError(f'{name} did not report a connected application')

                inspection = response_object(call('simcenter3d', 'part-info-tool', {}))
                design, route = read_design_roles(call, inspection)
                evidence['designcenter_identity_route'] = route
                mesh = response_object(call('simcenter3d', 'mesh-info-tool', {}))
                inspection_after = response_object(call('simcenter3d', 'part-info-tool', {}))
                targets = compare_targets(design, inspection)
                if targets != compare_targets(design, inspection_after) or mesh.get('success') is not True:
                    raise ValueError('FE model probe failed or changed target during the read')
                evidence['target_state'] = targets
                evidence['mesh_collector_count'] = len(mesh['meshCollectors'])
            finally:
                client.close()
        pids = {name: trusted_backend_pid(out / 'vendor' / name) for name in names}
        if len(set(pids.values())) != 1:
            raise ValueError('the profiles are served by different native processes')
        evidence.update(status='READ_ONLY_VERIFIED', backend_pids=pids)
    except BaseException as exc:
        evidence['failure'] = str(exc)
        raise
    finally:
        atomic_write(out / 'evidence.json', json_bytes(evidence))
    return evidence


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--product', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--codex', default='codex')
    args = parser.parse_args()
    result = qualify(args.project, args.product, args.out, args.codex)
    print(json.dumps({key: result[key] for key in (
        'status', 'candidate_source_digest', 'backend_pids', 'target_state', 'mesh_collector_count')}, indent=2))
