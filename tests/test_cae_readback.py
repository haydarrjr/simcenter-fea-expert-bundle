"""Exercise CAE scope and field-error handling without a licensed host."""
from pathlib import Path
import runpy
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


JOURNAL = (Path(__file__).resolve().parents[1] /
           'skills/designcenter-open-journal-authoring/scripts/read_cae_2612.py')


class Part:
    FullPath = 'synthetic'
    Tag = 1
    PartUnits = 'Millimeters'
    IsModified = False


class SimPart(Part):
    pass


class BaseFemPart(Part):
    FullPathForAssociatedCadPart = 'cad.prt'


class AssyFemPart(BaseFemPart):
    pass


def read(work):
    nxopen = ModuleType('NXOpen')
    cae = ModuleType('NXOpen.CAE')
    cae.SimPart, cae.BaseFemPart, cae.AssyFemPart = SimPart, BaseFemPart, AssyFemPart
    nxopen.CAE = cae
    session = SimpleNamespace(Parts=SimpleNamespace(BaseWork=work, BaseDisplay=work))
    nxopen.Session = SimpleNamespace(GetSession=lambda: session)
    with patch.dict(sys.modules, {'NXOpen': nxopen, 'NXOpen.CAE': cae}):
        return runpy.run_path(str(JOURNAL))['main'](None)


class CaeReadbackTests(unittest.TestCase):
    def test_solution_bc_and_step_bc_have_distinct_scope(self):
        fem = AssyFemPart()
        fem.BaseFEModel = SimpleNamespace(
            MeshManager=SimpleNamespace(GetMeshCollectors=lambda: []),
            GetChildren=lambda: [SimpleNamespace(JournalIdentifier='component', Tag=2)],
        )
        load = SimpleNamespace(Name='traction', Tag=3, DescriptorName='pressure')
        step = SimpleNamespace(Name='service', Tag=4, GetBcs=lambda: [load])
        solution = SimpleNamespace(Name='static', Tag=5, SolutionType='SOL101', SolverType='NASTRAN',
                                   StepCount=1, GetStepByIndex=lambda index: step,
                                   GetBcs=lambda: [], ResultReferenceCount=0)
        sim = SimPart()
        sim.FemPart = fem
        sim.Simulation = SimpleNamespace(Solutions=[solution], ActiveSolution=solution)
        result = read(sim)
        self.assertEqual(result['part_kind'], 'SIM')
        self.assertEqual(result['active_solution_tag'], '5')
        self.assertEqual(result['solutions'][0]['bcs'], [])
        self.assertEqual(result['solutions'][0]['steps'][0]['bcs'], [('traction', '3', 'pressure')])
        self.assertEqual(result['root_mesh_collectors'], [])
        self.assertEqual(result['assembly_children'], [{'identifier': 'component', 'tag': '2'}])
        self.assertEqual(result['field_errors'], {})

        del solution.GetBcs
        partial = read(sim)['solutions'][0]
        self.assertNotIn('bcs', partial)
        self.assertIn('bcs', partial['field_errors'])
        self.assertEqual(partial['steps'][0]['bcs'], [('traction', '3', 'pressure')])

    def test_unreadable_mesh_is_not_an_empty_mesh(self):
        fem = BaseFemPart()
        fem.BaseFEModel = SimpleNamespace()
        result = read(fem)
        self.assertEqual(result['part_kind'], 'FEM')
        self.assertNotIn('root_mesh_collectors', result)
        self.assertIn('root_mesh_collectors', result['field_errors'])
        self.assertEqual(result['associated_cad_path'], 'cad.prt')

    def test_cad_part_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'SIM, FEM or assembly FEM'):
            read(Part())
