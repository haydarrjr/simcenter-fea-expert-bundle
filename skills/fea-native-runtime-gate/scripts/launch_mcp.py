"""Local stdio adapter for installed Siemens MCP executables."""
import argparse
import itertools
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
from threading import Thread
import time
from uuid import uuid4


PROFILES = ('designcenter', 'simcenter3d', 'batchpost')
SANDBOX_TOOLS = {'dcopen-run-snippet-tool', 'dcopen-run-journal-tool'}
SANDBOX_FAILURE = re.compile(
    r'python execution error|sandboxing restriction|invalid journal code|traceback \(most recent call last\)'
    r'|toolExecutionStatus::Failed|journal execution failed|\b(?:NXException|AttributeError|TypeError|'
    r'NameError|SyntaxError|RuntimeError|ValueError|Exception):|\bstatus:[* ]*(?:failed|error)\b', re.I)
EXIT_CODE = re.compile(r'exit code:[* ]*(-?\d+)', re.I)


def guard_sandbox(message):
    result = message.get('result')
    if not isinstance(result, dict) or result.get('isError'):
        return message
    blocks = result.get('content', [])
    witness = '\n'.join(block.get('text', '') for block in blocks
                        if isinstance(block, dict) and block.get('type') == 'text')
    structured = result.get('structuredContent')
    if structured:
        witness += '\n' + json.dumps(structured, ensure_ascii=False)
    if SANDBOX_FAILURE.search(witness) or any(int(n) for n in EXIT_CODE.findall(witness)):
        reason = 'EXECUTION_FAILED: sandbox reported an execution error.'
    elif not witness.strip() or 'no output captured' in witness.lower():
        reason = 'EXECUTION_UNVERIFIED: sandbox did not provide observable output.'
    else:
        return message
    return {**message, 'result': {**result, 'isError': True,
                                  'content': [*blocks, {'type': 'text', 'text': reason}]}}


class InitialCatalog:
    """Hold an initial status-only catalog and refresh through the same child."""

    def __init__(self, seconds):
        self.seconds = seconds
        self.pending = {}
        self.held = {}
        self.bound = False
        self.refresh = None
        self.next_poll = 0.0
        self.ids = (f'fea-refresh-{uuid4()}-{index}' for index in itertools.count())

    def client(self, message, now):
        if not self.bound and message.get('method') == 'tools/list' and 'id' in message:
            params = message.get('params') or {}
            if not params.get('cursor'):
                self.pending[message['id']] = now + self.seconds

    def server(self, message, now):
        identifier = message.get('id')
        internal = identifier is not None and identifier == self.refresh
        if internal:
            self.refresh = None
        if message.get('method') == 'notifications/tools/list_changed':
            self.next_poll = now
        if not internal and identifier not in self.pending:
            return [message]
        tools = (message.get('result') or {}).get('tools')
        if isinstance(tools, list) and any(t.get('name') != 'dc_connection_status' for t in tools):
            self.bound = True
            ready = [{**message, 'id': key} for key in self.held]
            self.held.clear()
            if not internal:
                self.pending.pop(identifier, None)
                ready.append(message)
            return ready
        if internal:
            return []
        deadline = self.pending.pop(identifier)
        if not self.bound and isinstance(tools, list) and deadline > now:
            self.held[identifier] = (deadline, message)
            return []
        return [message]

    def tick(self, now):
        expired = []
        for identifier, (deadline, response) in list(self.held.items()):
            if deadline <= now:
                expired.append(response)
                del self.held[identifier]
        if self.held and self.refresh is None and now >= self.next_poll:
            self.refresh = next(self.ids)
            self.next_poll = now + 1.0
            return expired, {'id': self.refresh, 'jsonrpc': '2.0', 'method': 'tools/list'}
        return expired, None


def command(base, profile, tool_timeout, log_file=None, pipe_name=None):
    if profile not in PROFILES or not base.is_absolute():
        raise ValueError('choose a known profile and an absolute UGII_BASE_DIR')
    if profile == 'batchpost':
        argv = [str(base / 'NXBIN' / 'sc3d_batchpost_mcpconnector.exe')]
    else:
        argv = [str(base / 'UGII' / 'dcmcpserver' / 'DcMcpServer.exe'),
                '--server', profile, '--tool-timeout', str(tool_timeout)]
        if log_file:
            argv += ['--diagnostics', '--diagnostics-verbose', '--log-file-path', log_file]
    if pipe_name:
        argv += ['--mcp-pipe-name' if profile == 'batchpost' else '--pipe-name', pipe_name]
    if not Path(argv[0]).is_file():
        raise ValueError(f'installed Siemens executable not found: {argv[0]}')
    return argv


def discovery_compatibility_response(message, legacy_discovery):
    if message.get('method') != 'server/discover' or 'id' not in message:
        return None
    params = message.get('params') or {}
    meta = params.get('_meta') or {}
    client = meta.get('io.modelcontextprotocol/clientInfo') or {}
    if legacy_discovery or client.get('name') == 'vscode-agent-host':
        return {'jsonrpc': '2.0', 'id': message['id'], 'error': {
            'code': -32601, 'message': 'Method not found. This Siemens profile uses MCP initialize.'}}
    return None


def relay(argv, profile, wait, legacy_discovery=False):
    upstream = queue.Queue()
    child = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    catalog = InitialCatalog(wait)
    sandbox_requests = set()

    def pump(stream, origin):
        try:
            for line in iter(stream.readline, b''):
                upstream.put((origin, line))
        finally:
            upstream.put((origin, None))

    def send(stream, message):
        stream.write((json.dumps(message, ensure_ascii=True) + '\n').encode('utf-8'))
        stream.flush()

    Thread(target=pump, args=(sys.stdin.buffer, 'client'), daemon=True).start()
    Thread(target=pump, args=(child.stdout, 'server'), daemon=True).start()
    try:
        while True:
            try:
                origin, raw = upstream.get(timeout=0.25)
            except queue.Empty:
                origin, raw = None, None
            now = time.monotonic()
            if origin and raw is None:
                break
            if raw:
                try:
                    message = json.loads(raw)
                except ValueError:
                    print(f'{profile}: ignored a non-JSON line from {origin}', file=sys.stderr)
                    continue
                if origin == 'client':
                    response = (discovery_compatibility_response(message, legacy_discovery)
                                if profile != 'batchpost' else None)
                    if response is not None:
                        send(sys.stdout.buffer, response)
                        continue
                    if profile != 'batchpost':
                        catalog.client(message, now)
                    if (profile == 'designcenter' and message.get('method') == 'tools/call'
                            and message.get('params', {}).get('name') in SANDBOX_TOOLS
                            and 'id' in message):
                        sandbox_requests.add(message['id'])
                    send(child.stdin, message)
                else:
                    identifier = message.get('id')
                    if identifier in sandbox_requests:
                        sandbox_requests.remove(identifier)
                        message = guard_sandbox(message)
                    responses = catalog.server(message, now) if profile != 'batchpost' else [message]
                    for response in responses:
                        send(sys.stdout.buffer, response)
            for_waiting, refresh = catalog.tick(now)
            for response in for_waiting:
                send(sys.stdout.buffer, response)
            if refresh:
                send(child.stdin, refresh)
    except BrokenPipeError:
        pass
    finally:
        child.stdin.close()
        try:
            child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            child.terminate()
            child.wait(timeout=5)
    return child.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=PROFILES, default=os.getenv('MCP_SERVER', 'designcenter'))
    parser.add_argument('--ugii-base-dir', default=os.getenv('UGII_BASE_DIR'), required=False)
    parser.add_argument('--catalog-wait', type=float, default=75)
    parser.add_argument('--tool-timeout', type=int, default=180)
    parser.add_argument('--log-file')
    parser.add_argument('--pipe-name')
    parser.add_argument('--legacy-discovery', action='store_true',
                        help='Use standard MCP initialize for Siemens 2612 with the Copilot harness')
    args = parser.parse_args()
    if not args.ugii_base_dir or not 0 <= args.catalog_wait <= 180 or args.tool_timeout < 1:
        parser.error('explicit product location and valid timeouts are required')
    base = Path(args.ugii_base_dir)
    os.environ['UGII_BASE_DIR'] = str(base)
    os.environ.setdefault('DC_CONNECT_TIMEOUT', '10000')
    try:
        argv = command(base, args.profile, args.tool_timeout, args.log_file, args.pipe_name)
        return relay(argv, args.profile, args.catalog_wait,
                     legacy_discovery=args.legacy_discovery and args.profile != 'batchpost')
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
