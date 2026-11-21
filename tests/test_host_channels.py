"""Regression tests for candidate parity, managed installs and MCP admission."""
from datetime import datetime, timezone
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from time import monotonic
from types import SimpleNamespace
from unittest.mock import patch

from scripts.install_project import attest, install, rollback
from scripts.install_bundle import on_demand_pointer
from scripts.package_identity import BUNDLE_MANIFEST, check_paths, read_zip, verify_files
from scripts.package_release import PROJECTS, ROOT, build
from scripts.render_mcp_config import audit, profiles, render


def runtime(name, skill='fea-native-runtime-gate'):
    path = ROOT / 'skills' / skill / 'scripts' / f'{name}.py'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


launcher = runtime('launch_mcp')
batchpost_launcher = runtime('batchpost_mcp')
controller = runtime('fea_controller')
with patch.dict(sys.modules, {'fea_controller': controller}):
    official_adapter = runtime('official_mcp_adapter')


class OfficialAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_chain_builds_only_after_independent_acceptance(self):
        class Session:
            async def call_tool(self, tool, *, arguments):
                events.append(('call', tool, arguments))
                return {'content': [{'type': 'text', 'text': json.dumps({
                    'toolExecutionStatus': 'ToolExecutionStatus::Completed'})}]}

        target = dict(session='pid', release='2612', model='model.sim', owner='model.fem', revision='r')
        catalog = [{'name': 'read-model-data', 'inputSchema': {
            'type': 'object', 'properties': {'schemaForExtraction': {'type': 'string'}},
            'required': ['schemaForExtraction']}}]
        events = []
        adapter = official_adapter.OfficialMcpAdapter(Session(), 'designcenter', catalog, target, 'identity')

        def builder(name, expected, dependency):
            async def build(previous):
                events.append(('build', name))
                self.assertEqual(previous['status'] if previous else None, 'ACCEPTED' if dependency else None)
                return dict(operation_id=name, profile='designcenter', tool='read-model-data',
                            target=target, effect='PURE_READ', expected={'count': expected},
                            depends_on=[dependency] if dependency else [],
                            arguments={'schemaForExtraction': '{}'}), 'fresh identity', None
            return build

        async def readback(request):
            events.append(('readback', request['operation_id']))
            return dict(target=target, observed_at=controller.now(), evidence_ref='new result',
                        witnesses={'count': 1})

        with tempfile.TemporaryDirectory() as folder:
            receipts = await adapter.execute_chain(controller.Controller(folder), [
                builder('first', 1, None), builder('second', 2, 'first'),
                builder('third', 1, 'second')], readback)
        self.assertEqual([r['status'] for r in receipts], ['ACCEPTED', 'UNKNOWN'])
        self.assertEqual([e[0] for e in events], ['build', 'call', 'readback', 'build', 'call', 'readback'])

    def test_vendor_error_inside_successful_transport(self):
        self.assertTrue(controller.response_failed({'isError': False, 'content': [{
            'type': 'text', 'text': json.dumps({
                'toolExecutionStatus': 'ToolExecutionStatus::Completed',
                'toolResponse': {'error': 'No active part'}})}]}))


class ProjectChannels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.out = cls.root / 'candidate'
        cls.identity = build(cls.out)
        cls.other_out = cls.root / 'other-candidate'
        build(cls.other_out)

    def test_shared_candidate_and_canonical_skill_bytes(self):
        self.assertEqual((self.out / 'SHA256SUMS.txt').read_bytes(),
                         (self.other_out / 'SHA256SUMS.txt').read_bytes())
        bundle = read_zip(self.out / 'agents-artefact-windows.zip')
        common = verify_files(bundle, BUNDLE_MANIFEST, 'agentsai')['candidate_source_digest']
        for channel, (manifest, filename) in {
            **PROJECTS, 'portable': ('fea-expert-package.json', 'simcenter-fea-expert-plugin.zip')
        }.items():
            with self.subTest(channel=channel):
                path = self.out / filename
                self.assertEqual(path.read_bytes(), (self.other_out / filename).read_bytes())
                files = read_zip(path)
                self.assertEqual(verify_files(files, manifest, channel)['candidate_source_digest'], common)
                prefix = manifest.rsplit('/', 1)[0] + '/' if '/' in manifest else ''
                self.assertNotIn(prefix + BUNDLE_MANIFEST, files)
                for name, raw in bundle.items():
                    if name.startswith('skills/') and name != BUNDLE_MANIFEST:
                        self.assertEqual(files[prefix + name], raw)
                if channel == 'portable':
                    self.assertIn('com.github.copilot/agents/simcenter-fea-expert.agent.md', files)
                    self.assertNotIn('mcp.json', files)

    def test_packaged_fea_workflow_does_not_route_to_removed_engines(self):
        bundle = read_zip(self.out / 'agents-artefact-windows.zip')
        for name, raw in bundle.items():
            if name.startswith('skills/') and name.endswith('.md'):
                self.assertNotRegex(
                    raw.decode('utf-8').lower(),
                    r'\b(?:fea_capabilities|fea_get_example|fea_inspect_artifact|fea_agent|pynastran|'
                    r'calculix|opensees|scikit-fem|gmsh|pylife)\b',
                    name,
                )
        for _, filename in PROJECTS.values():
            files = read_zip(self.out / filename)
            root = next(name.split('/')[0] for name in files if name.endswith('/fea-workflow.md'))
            workflow = files[f'{root}/fea-workflow.md'].decode('utf-8')
            self.assertIn('globally configured official Siemens MCPs', workflow)
            self.assertIn(f'{root}/skills/fea-dynamics/references/sol103-free-free.md', files)

    def test_codex_update_and_rollback_preserve_existing_instructions(self):
        project = self.root / 'codex'
        project.mkdir()
        path = project / 'AGENTS.md'
        path.write_bytes(b'# User instructions\r\n')
        archive = self.out / PROJECTS['codex'][1]
        install(project, archive, self.root / 'backup-one', 'codex')
        before = path.read_bytes()
        install(project, archive, self.root / 'backup-two', 'codex')
        self.assertEqual(attest(project, 'codex')['skill_count'], 39)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(before.count(b'simcenter-fea-expert:start'), 1)
        rollback(project, self.root / 'backup-two', 'codex')
        rollback(project, self.root / 'backup-one', 'codex')
        self.assertEqual(path.read_bytes(), b'# User instructions\r\n')
        self.assertFalse((project / '.agents/fea-expert-package.json').exists())

    def test_copilot_preserves_workspace_config_and_rejects_tamper(self):
        project = self.root / 'copilot'
        (project / '.vscode').mkdir(parents=True)
        (project / '.github/workflows').mkdir(parents=True)
        mcp = project / '.vscode/mcp.json'
        mcp.write_bytes(b'{ /* existing */ "servers": {} }')
        timestamp = mcp.stat().st_mtime_ns
        unrelated = project / '.github/workflows/user.yml'
        unrelated.write_text('name: existing', encoding='utf-8')
        backup = self.root / 'copilot-backup'
        install(project, self.out / PROJECTS['copilot'][1], backup, 'copilot')
        self.assertEqual(mcp.stat().st_mtime_ns, timestamp)
        self.assertEqual(unrelated.read_text(), 'name: existing')
        (project / '.github/fea-workflow.md').write_text('changed', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'installed resource changed'):
            attest(project, 'copilot')
        with self.assertRaisesRegex(ValueError, 'rollback bytes changed'):
            rollback(project, backup, 'copilot')

    def test_local_mcp_configs_have_two_explicit_read_profiles(self):
        project = self.root / 'render-codex'
        project.mkdir()
        install(project, self.out / PROJECTS['codex'][1], self.root / 'render-backup', 'codex')
        product = self.root / 'Siemens Product'
        executable = product / 'UGII/dcmcpserver/DcMcpServer.exe'
        executable.parent.mkdir(parents=True)
        executable.touch()
        generated = profiles(project, product)
        decoded = tomllib.loads(render(generated, 'codex'))['mcp_servers']
        self.assertEqual(decoded, generated)
        for name, server in decoded.items():
            self.assertIn(name, server['args'])
            self.assertIn('dc_connection_status', server['enabled_tools'])
        self.assertNotIn('dcopen-execute-tool', decoded['designcenter']['enabled_tools'])
        self.assertNotIn('surface-mesh-generation-tool', decoded['simcenter3d']['enabled_tools'])
        self.assertIn('--legacy-discovery', decoded['simcenter3d']['args'])
        self.assertNotIn('--legacy-discovery', decoded['designcenter']['args'])
        binaries = product / 'NXBIN'
        binaries.mkdir()
        (binaries / 'sc3d_batchpost_mcpconnector.exe').touch()
        with self.assertRaisesRegex(ValueError, 'worker and connector'):
            profiles(project, product, batchpost=True)
        (binaries / 'sc3d_batchpost.exe').touch()
        batchpost = profiles(project, product, batchpost=True)['batchpost']
        self.assertEqual(Path(batchpost['args'][2]).name, 'batchpost_mcp.py')
        self.assertIn('open', batchpost['enabled_tools'])
        self.assertEqual(batchpost['env_vars'], ['SALT_LICENSE_SERVER', 'SALT_LICENSE_TYPE',
                                                 'SPLM_LICENSE_SERVER'])
        self.assertNotIn('env', batchpost)

    def test_unsafe_paths_are_rejected(self):
        for paths in (['../escape'], ['CON.md'], ['x/a', 'x/A'], ['a', 'A/b'], ['a/b:stream']):
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                check_paths(paths)

    def test_config_audit_reads_jsonc_and_reports_duplicate_profiles(self):
        cfg = self.root / 'native-mcp.json'
        cfg.write_text('{"mcpServers":{"foo":{"args":["--profile","designcenter"]}}}', encoding='utf-8')
        editor = self.root / 'mcp.json'
        editor.write_text('{"servers": { /* existing */ "designcenter": {}, }, }', encoding='utf-8')
        before = editor.read_bytes()
        result = audit([cfg, editor])
        self.assertEqual(result['multiple_definitions'], ['designcenter'])
        self.assertEqual(editor.read_bytes(), before)

    def test_vendor_pointer_replaces_data_only_and_binds_exact_bundle(self):
        name = 'skills/demo/SKILL.md'
        original = b'---\nname: demo\ndescription: Tool description\n---\nBody'
        pointer = b'---\nname: demo\ndescription: Tool description\nbundle: candidate\n---\n<!-- Content loaded from bundle on demand -->\n'
        self.assertTrue(on_demand_pointer(name, pointer, original, 'candidate'))
        self.assertFalse(on_demand_pointer(name, pointer, original, 'different-candidate'))
        self.assertFalse(on_demand_pointer('skills/demo/scripts/controller.py', b'', b'code', 'candidate'))


class CatalogAndSandbox(unittest.TestCase):
    def test_copilot_negotiation_uses_initialize_only_when_configured(self):
        discover = {'jsonrpc': '2.0', 'id': 0, 'method': 'server/discover'}
        self.assertIsNone(launcher.discovery_compatibility_response(discover, False))
        response = launcher.discovery_compatibility_response(discover, True)
        self.assertEqual(response['id'], 0)
        self.assertEqual(response['error']['code'], -32601)
        vscode = {**discover, 'params': {'_meta': {
            'io.modelcontextprotocol/clientInfo': {'name': 'vscode-agent-host'}}}}
        self.assertEqual(launcher.discovery_compatibility_response(vscode, False), response)
        for method in ('initialize', 'notifications/initialized', 'tools/list', 'tools/call'):
            self.assertIsNone(launcher.discovery_compatibility_response(
                {'jsonrpc': '2.0', 'id': 1, 'method': method}, True))
    def test_batchpost_requires_its_announced_pipe(self):
        worker = SimpleNamespace(stdout=io.BytesIO(
            b'sc3d_batchpost_example\nMCP ready to connect on pipe:\nsc3d_batchpost_actual\n'))
        with patch.object(batchpost_launcher, 'message'):
            batchpost_launcher.await_pipe(worker, 'sc3d_batchpost_actual', 1, monotonic())
            worker.stdout.seek(0)
            with self.assertRaisesRegex(RuntimeError, 'before announcing pipe readiness'):
                batchpost_launcher.await_pipe(worker, 'sc3d_batchpost_example', 1, monotonic())
    def test_status_only_refresh_preserves_schema_and_original_request_id(self):
        gate = launcher.InitialCatalog(5)
        gate.client({'id': 1, 'method': 'tools/list'}, 10)
        status = {'id': 1, 'result': {'tools': [{'name': 'dc_connection_status'}]}}
        self.assertEqual(gate.server(status, 10), [])
        _, internal = gate.tick(10)
        self.assertEqual(gate.tick(10), ([], None))
        domain = {'name': 'part-info-tool', 'inputSchema': {'type': 'object'}}
        response = {'id': internal['id'], 'result': {'tools': [domain]}}
        self.assertEqual(gate.server(response, 11), [{'id': 1, 'result': {'tools': [domain]}}])

    def test_startup_timeout_returns_original_connected_status_capability(self):
        gate = launcher.InitialCatalog(2)
        gate.client({'id': 1, 'method': 'tools/list'}, 10)
        status = {'id': 1, 'result': {'tools': [{'name': 'dc_connection_status'}]}}
        self.assertEqual(gate.server(status, 10), [])
        self.assertEqual(gate.tick(13), ([status], None))

    def test_sandbox_error_and_empty_stdout_remain_distinct(self):
        for text, reason in (('Exit code: 1', 'EXECUTION_FAILED'),
                             ('No output captured', 'EXECUTION_UNVERIFIED')):
            with self.subTest(text=text):
                envelope = {'result': {'content': [{'type': 'text', 'text': text}]}}
                guarded = launcher.guard_sandbox(envelope)
                self.assertTrue(guarded['result']['isError'])
                self.assertEqual(guarded['result']['content'][0]['text'], text)
                self.assertIn(reason, guarded['result']['content'][1]['text'])
                self.assertNotIn('isError', envelope['result'])


class ControllerTests(unittest.TestCase):
    def test_unknown_blocks_dependency_across_restart_until_fresh_readback(self):
        with tempfile.TemporaryDirectory() as folder:
            target = {'session': 'native', 'release': '2612', 'owner': 'fem',
                      'model': 'work-copy.fem', 'revision': 'r1'}
            operation = {'operation_id': 'mesh1', 'profile': 'simcenter3d',
                         'tool': 'surface-mesh-generation-tool', 'effect': 'CAE_MUTATION',
                         'target': target, 'arguments': {}, 'expected': {'count': 1},
                         'baseline': {'count': 0}}
            binding = {'profile': operation['profile'], 'target': target, 'evidence_ref': 'status.json',
                       'schema': {'name': operation['tool'], 'inputSchema': {'type': 'object'}}}
            authorization = {'operation_digest': controller.digest(operation), 'evidence_ref': 'intent.json'}
            run = controller.Controller(folder)
            prepared = run.prepare(operation, binding, authorization)
            run.reserve('mesh1', binding, prepared['request_digest'])
            self.assertEqual(run.record('mesh1', transport_error='timeout')['status'], 'UNKNOWN')
            reopened = controller.Controller(folder)
            next_operation = {**operation, 'operation_id': 'mesh2', 'depends_on': ['mesh1']}
            next_auth = {**authorization, 'operation_digest': controller.digest(next_operation)}
            with self.assertRaisesRegex(ValueError, 'unreconciled'):
                reopened.prepare(next_operation, binding, next_auth)
            observation = {'target': target, 'observed_at': datetime.now(timezone.utc).isoformat(),
                           'evidence_ref': 'independent-native-probe.json', 'witnesses': {'count': 1}}
            self.assertEqual(reopened.observe('mesh1', observation)['status'], 'ACCEPTED')
            self.assertEqual(reopened.prepare(next_operation, binding, next_auth)['status'], 'PREPARED')
            stored = json.loads((Path(folder) / 'controller-state.json').read_bytes())
            self.assertEqual(stored['operations']['mesh1']['transport_error'], 'timeout')

    def test_journal_checks_no_save_or_unqualified_import(self):
        self.assertEqual(controller.normalize_journal('\ufeffdef main(args):\n    return {}\n'),
                         'def main(args):\n    return {}\n')
        for code in ('import os\ndef main(args): pass', 'def main(args): wp.Save()',
                     'def main(path): return path'):
            with self.subTest(code=code), self.assertRaises(ValueError):
                controller.normalize_journal(code)

    def test_exact_export_template_and_late_artifact_reconciliation(self):
        target = {'session': 'native', 'release': '2612.1700', 'owner': 'sim',
                  'model': r'C:\work\model.sim', 'revision': 'r1'}
        tool = 'dcopen-execute-tool'
        binding = {'target': target, 'profile': 'designcenter', 'fem': r'C:\work\model.fem',
                   'solution_tag': '23', 'evidence_ref': 'native.json',
                   'schema': {'name': tool, 'inputSchema': {'type': 'object',
                              'properties': {'python_code': {'type': 'string'}}}}}
        code = controller.export_journal(target, binding['fem'], binding['solution_tag'])
        before = {'deck_path': r'C:\work\model-modes.dat', 'deck_present': False,
                  'original_solution_signature': 'original-static-id'}
        after = {**before, 'deck_present': True, 'export_finished': True, 'deck_qualified': True}
        operation = {'operation_id': 'deck', 'profile': 'designcenter', 'tool': tool,
                     'effect': 'DECK_EXPORT', 'target': target, 'arguments': {'python_code': code},
                     'baseline': before, 'expected': after}

        def prepare(run, request):
            return run.prepare(request, binding, {'operation_digest': controller.digest(request),
                                                   'evidence_ref': 'intent.json'})

        with tempfile.TemporaryDirectory() as folder:
            run = controller.Controller(folder)
            for invalid in (
                {**operation, 'arguments': {'python_code': code.replace('WriteSolverInputFile', 'Solve')}},
                {**operation, 'effect': 'CAE_MUTATION'},
                {**operation, 'expected': {**after, 'deck_path': r'C:\original\result.dat'}},
            ):
                with self.assertRaises(ValueError):
                    prepare(run, invalid)
            prepared = prepare(run, operation)
            run.reserve('deck', binding, prepared['request_digest'])
            self.assertEqual(run.record('deck', transport_error='timeout')['status'], 'UNKNOWN')

            def observe(witnesses):
                return run.observe('deck', {'target': target, 'witnesses': witnesses,
                                            'observed_at': datetime.now(timezone.utc).isoformat(),
                                            'evidence_ref': 'independent.json'})['status']

            self.assertEqual(observe(before), 'UNKNOWN')
            self.assertEqual(observe(after), 'ACCEPTED')


class ReportEvidenceTests(unittest.TestCase):
    def test_modal_file_cannot_silently_contain_extra_states(self):
        verifier = runtime('verify_modal_csv', 'batchpost-actions')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'modes.csv'
            path.write_text(',"Load Case 1 - Mode 7, 120.5Hz"\n', encoding='utf-8')
            self.assertEqual(verifier.verify([path], ['Load Case 1:Mode 7']), ['Load Case 1:Mode 7'])
            with path.open('a', encoding='utf-8') as stream:
                stream.write(',"Load Case 1 - Mode 8, 151.2Hz"\n')
            with self.assertRaisesRegex(ValueError, 'extra'):
                verifier.verify([path], ['Load Case 1:Mode 7'])

    def test_pdf_preflight_rejects_traced_glyph_clipping(self):
        preflight = runtime('check_pdf', 'fea-results-interpretation')

        class Document(list):
            needs_pass = False

        page = SimpleNamespace(get_text=lambda: 'Searchable heading', rect=(0, 0, 200, 300),
                               derotation_matrix=1,
                               get_bboxlog=lambda: [('fill-text', (0, 0, 201.5, 10))])
        with self.assertRaisesRegex(ValueError, 'extends beyond page'):
            preflight.check(Document([page]), ['Searchable heading'], 0)
