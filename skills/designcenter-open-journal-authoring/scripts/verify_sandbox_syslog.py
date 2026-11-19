"""Verify a sandbox test using its own Siemens run_journal system log."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re


TOOLS = {'dcopen-run-snippet-tool': 'nxopen_python_snippet',
         'dcopen-run-journal-tool': 'python_code'}


def verify(capture, log, worker_pid, nonce):
    """Correlate one observed worker and one test-only result marker."""
    if not re.fullmatch('[0-9a-f]{32}', nonce):
        raise ValueError('use a fresh 128-bit lowercase hexadecimal nonce')
    request = capture['request']
    field = TOOLS.get(request['name'])
    marker = f'FEA_SANDBOX_PASS:{nonce}'
    if field is None or request['arguments'][field].count(marker) != 1:
        raise ValueError('the MCP request must contain exactly one test marker')
    result = capture['reply'].get('result', {})
    blocks = [entry['text'] for entry in result.get('content', []) if entry.get('type') == 'text']
    if not blocks:
        raise ValueError('missing native tool response')
    response = json.loads(blocks[0])
    output = response.get('toolResponse')
    if (response.get('toolExecutionStatus') != 'ToolExecutionStatus::Completed'
            or not isinstance(output, str) or 'No output captured' not in output
            or not re.search(r'(?mi)^\*\*Exit Code:\*\*\s*0\s*$', output)
            or any('EXECUTION_FAILED' in block for block in blocks[1:])):
        raise ValueError('the Siemens worker did not report a normal exit with empty output')
    lines = log.decode('cp1252', errors='replace').splitlines()
    pids = [int(m[1]) for line in lines if (m := re.fullmatch(r'Process ID\s*:-\s*(\d+)', line))]
    if pids != [worker_pid] or not any(
            line.startswith('Command line: ') and re.search(
                r'\brun_journal\.exe[" ]+.*[\\/]DcOpenAgent[\\/]', line, re.I)
            for line in lines):
        raise ValueError('system log does not match the observed official sandbox worker')
    witnesses = [index for index, line in enumerate(lines, 1) if line.strip() == marker]
    if len(witnesses) != 1:
        raise ValueError('the exact sandbox test marker was not observed once')
    return {'status': 'SYSLOG_WITNESS_VERIFIED', 'mcp_output': 'EMPTY', 'tool': request['name'],
            'worker_pid': worker_pid, 'marker': marker, 'syslog_line': witnesses[0],
            'syslog_sha256': sha256(log).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path, help='JSON with original request and reply')
    parser.add_argument('syslog', type=Path, help='System log from the exact observed worker')
    parser.add_argument('--pid', required=True, type=int)
    parser.add_argument('--nonce', required=True)
    args = parser.parse_args()
    witness = verify(json.loads(args.capture.read_text(encoding='utf-8-sig')),
                     args.syslog.read_bytes(), args.pid, args.nonce)
    print(json.dumps(witness, indent=2))
