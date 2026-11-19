"""Verify that sandbox log evidence matches the request and real worker."""
import importlib.util
import json
from pathlib import Path
import unittest


script = Path(__file__).resolve().parents[1] / (
    'skills/designcenter-open-journal-authoring/scripts/verify_sandbox_syslog.py')
spec = importlib.util.spec_from_file_location('verify_sandbox_syslog', script)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class SandboxSyslogTests(unittest.TestCase):
    def test_exact_worker_and_witness(self):
        nonce = '1' * 32
        marker = f'FEA_SANDBOX_PASS:{nonce}'
        capture = {
            'request': {'name': 'dcopen-run-snippet-tool',
                        'arguments': {'nxopen_python_snippet': f'theSession.LogFile.WriteLine("{marker}")'}},
            'reply': {'result': {'isError': True, 'content': [
                {'type': 'text', 'text': json.dumps({
                    'toolExecutionStatus': 'ToolExecutionStatus::Completed',
                    'toolResponse': '**Exit Code:** 0\n\n*No output captured.*'})},
                {'type': 'text', 'text': 'EXECUTION_UNVERIFIED'},
            ]}},
        }
        log = (f'Process ID   :- 5812\n'
               f'Command line: C:\\App\\run_journal.exe -nx C:\\tmp\\DcOpenAgent\\job.py\n{marker}\n').encode()
        self.assertEqual(helper.verify(capture, log, 5812, nonce)['syslog_line'], 3)
        with self.assertRaisesRegex(ValueError, 'worker'):
            helper.verify(capture, log, 7084, nonce)
        with self.assertRaisesRegex(ValueError, 'once'):
            helper.verify(capture, log + (marker + '\n').encode(), 5812, nonce)
        capture['reply']['result']['content'][1]['text'] = 'EXECUTION_FAILED'
        with self.assertRaisesRegex(ValueError, 'normal exit'):
            helper.verify(capture, log, 5812, nonce)
