"""Render host-owned Siemens MCP configuration for review, without applying it."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tomllib


READ_TOOLS = {
    'designcenter': ['dc_connection_status', 'explore-model-structure', 'read-model-data',
                     'dcopen-list-namespaces', 'dcopen-list-classes', 'dcopen-class-info',
                     'dcopen-member-info', 'dcopen-pattern-lookup-tool',
                     'dcopen-keyword-search-tool', 'dcopen-semantic-search-tool'],
    'simcenter3d': ['dc_connection_status', 'part-info-tool', 'body-info-tool',
                    'material-info-tool', 'mesh-info-tool', 'mesh-quality-tool', 'boundary-condition-tool'],
}
ADDITIONAL_TOOLS = {
    'designcenter': ['dcopen-run-snippet-tool', 'dcopen-run-journal-tool', 'dcopen-execute-tool'],
    'simcenter3d': ['surface-mesh-generation-tool', 'solid-mesh-generation-tool',
                    'mesh-selection-visibility-tool', 'body-selection-visibility-tool'],
    'batchpost': ['open', 'list', 'contour', 'graphi', 'set', 'close'],
}


def profiles(project, product, *, host='codex', engineering=False, batchpost=False, logs=None):
    project = Path(project).resolve(strict=True)
    product = Path(product).resolve(strict=True)
    launcher = project / ('.agents' if host == 'codex' else '.github') / (
        'skills/fea-native-runtime-gate/scripts/launch_mcp.py')
    if not launcher.is_file() or not (product / 'UGII/dcmcpserver/DcMcpServer.exe').is_file():
        raise ValueError('install FEA project resources and select the Siemens product directory first')
    if batchpost and not all((product / 'NXBIN' / binary).is_file() for binary in (
            'sc3d_batchpost.exe', 'sc3d_batchpost_mcpconnector.exe')):
        raise ValueError('the selected Siemens product must have the BatchPost worker and connector')
    result = {}
    for name in [*READ_TOOLS, *(['batchpost'] if batchpost else [])]:
        if name == 'batchpost':
            argv = ['-B', '-u', str(launcher.with_name('batchpost_mcp.py')),
                    '--ugii-base-dir', str(product)]
        else:
            argv = ['-B', '-u', str(launcher), '--profile', name,
                    '--ugii-base-dir', str(product), '--tool-timeout', '40']
            if host == 'copilot':
                argv += ['--legacy-discovery', '--catalog-wait', '12']
        if logs is not None and name != 'batchpost':
            # This Siemens build writes a generated log filename inside this directory.
            argv += ['--log-file', str(Path(logs).resolve() / name)]
        tools = list(READ_TOOLS.get(name, []))
        if engineering or name == 'batchpost':
            tools.extend(ADDITIONAL_TOOLS[name])
        server = {'command': sys.executable, 'args': argv}
        if host == 'codex':
            server.update(enabled_tools=tools, startup_timeout_sec=95, tool_timeout_sec=240)
        else:
            server.update(type='stdio', tools=tools)
        result[name] = server
    return result


def toml_value(value):
    if isinstance(value, dict):
        return '{' + ', '.join(f'{json.dumps(key)} = {toml_value(item)}'
                               for key, item in value.items()) + '}'
    return json.dumps(value, ensure_ascii=False)


def render(servers, host):
    if host == 'copilot':
        return json.dumps({'mcpServers': servers}, ensure_ascii=False, indent=2)
    return '\n\n'.join(f'[mcp_servers.{name}]\n' + '\n'.join(
        f'{key} = {toml_value(value)}' for key, value in server.items())
        for name, server in servers.items())


def audit(paths):
    """Read selected scopes without printing credentials, commands or arguments."""
    report = {'scope': 'CONFIG_ONLY', 'files': [], 'profile_bindings': {}}
    for path in paths:
        path = Path(path).resolve(strict=True)
        raw = path.read_bytes()
        source = raw.decode('utf-8-sig')
        if path.suffix == '.toml':
            groups = {'mcp_servers': tomllib.loads(source).get('mcp_servers', {})}
        else:
            pattern = r'"(?:\\.|[^"\\])*"|//[^\r\n]*|/\*.*?\*/'
            clean = re.sub(pattern, lambda match: match[0] if match[0].startswith('"') else ' ',
                           source, flags=re.S)
            clean = re.sub(r'"(?:\\.|[^"\\])*"|,(?=\s*[}\]])',
                           lambda match: match[0] if match[0].startswith('"') else '', clean)
            document = json.loads(clean)
            groups = {key: document.get(key, {}) for key in ('mcpServers', 'servers')}
        item = {'file': str(path), 'sha256': hashlib.sha256(raw).hexdigest(),
                'mtime_ns': path.stat().st_mtime_ns, 'servers': []}
        for group, entries in groups.items():
            for name, entry in entries.items():
                argv = entry.get('args', [])
                env = entry.get('env', {})
                profile = env.get('MCP_SERVER')
                for flag in ('--profile', '--server'):
                    if flag in argv and argv.index(flag) + 1 < len(argv):
                        profile = argv[argv.index(flag) + 1]
                if profile not in {*READ_TOOLS, 'batchpost'}:
                    profile = name if name in {*READ_TOOLS, 'batchpost'} else None
                if profile is not None:
                    scope = {'namespace': name, 'kind': group, 'enabled': entry.get('enabled', True)}
                    item['servers'].append(scope)
                    if scope['enabled']:
                        report['profile_bindings'].setdefault(profile, []).append(
                            {'namespace': name, 'file': str(path)})
        report['files'].append(item)
    report['multiple_definitions'] = sorted(key for key, values in report['profile_bindings'].items()
                                            if len(values) > 1)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path)
    parser.add_argument('--product', type=Path)
    parser.add_argument('--audit', nargs='+', type=Path, metavar='CONFIG')
    parser.add_argument('--host', choices=('codex', 'copilot'), default='codex')
    parser.add_argument('--engineering', action='store_true', help='Include qualified action and sandbox candidates')
    parser.add_argument('--batchpost', action='store_true', help='Include separate BatchPost worker connector')
    args = parser.parse_args()
    if args.audit:
        print(json.dumps(audit(args.audit), ensure_ascii=False, indent=2))
    elif not args.project or not args.product:
        parser.error('--project and --product are required to render config')
    else:
        print(render(profiles(args.project, args.product, host=args.host,
                              engineering=args.engineering, batchpost=args.batchpost), args.host))
