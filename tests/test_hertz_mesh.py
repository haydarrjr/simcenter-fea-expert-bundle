from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fixtures.generate_hertz_contact import hertz


class HertzMeshTests(unittest.TestCase):
    def test_both_bodies_refine_toward_the_contact_surface(self):
        with TemporaryDirectory() as directory:
            folder = Path(directory) / 'hertz'
            hertz(401, 4, 0.010, folder)
            axis = []
            with (folder / 'hertz.dat').open() as deck:
                for line in deck:
                    if line.startswith('GRID*') and float(line[40:56]) == float(line[56:72]) == 0:
                        axis.append(float(next(deck)[8:24]))

        lower_end = axis.index(0.0)
        lower, upper = axis[:lower_end + 1], axis[lower_end + 1:]
        self.assertEqual(len(lower), len(upper))
        self.assertEqual((lower[0], upper[-1]), (-0.010, 0.010))
        for lower_z, upper_z in zip(reversed(lower), upper):
            self.assertAlmostEqual(-lower_z, upper_z, places=11)
        self.assertLess(upper[1] - upper[0], upper[-1] - upper[-2])
