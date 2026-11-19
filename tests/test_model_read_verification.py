"""Regression tests for schema, pagination and target evidence."""
import importlib.util
import json
from pathlib import Path
import unittest


path = Path(__file__).resolve().parents[1] / 'skills/designcenter-open-model-data-read/scripts/verify_read.py'
spec = importlib.util.spec_from_file_location('verify_read', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def capture(name, arguments, response):
    return {'request': {'name': name, 'arguments': arguments}, 'reply': {'result': {'content': [
        {'type': 'text', 'text': json.dumps({'toolExecutionStatus': 'ToolExecutionStatus::Completed',
                                             'toolResponse': response})}]}}}


class ModelReadTests(unittest.TestCase):
    def test_bind_identity_and_reject_invalid_continuation(self):
        entity = {'name': 'PartInfo', 'scalar_properties': ['filePath', 'isWorkPart']}
        domain = lambda item: {'name': 'modeling', 'entities': [item]}
        schema = capture('explore-model-structure', {'application': ['modeling']},
                         {'domain': [domain({**entity, 'scalar_properties': [
                             {'name': key} for key in entity['scalar_properties']]})]})
        args = {'schemaForExtraction': json.dumps({'domain': [domain(entity)]})}
        response = {'DesigncenterVersion': '2612', 'currentApplication': 'APP', 'partUnits': 'mm',
                    'data': {'PartInfo': [{'filePath': 'D:/copy.sim', 'isWorkPart': True}]}}

        def page(**updates):
            return capture('read-model-data', args, {**response, **updates})

        self.assertEqual(module.verify_read([schema], [page()], expected_part='d:/COPY.sim')['status'],
                         'VERIFIED')
        self.assertEqual(module.verify_read([schema], [page(hasMoreData=True)])['status'], 'PARTIAL')
        with self.assertRaisesRegex(ValueError, 'different active part'):
            module.verify_read([schema], [page()], expected_part='D:/other.sim')
        with self.assertRaisesRegex(ValueError, 'terminal'):
            module.verify_read([schema], [page(), page()])
        with self.assertRaisesRegex(ValueError, 'failed'):
            module.verify_read([schema], [page(error='No active part')])
