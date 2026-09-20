"""Independent consistency checks on saved flow fields and diagnostics.

Numerical convergence is assessed separately: these tests cannot turn
under-resolved results into accepted physical predictions.
"""
import json
from pathlib import Path
import unittest

import numpy as np


class SavedResultsIndependentQA(unittest.TestCase):
    def test_control_outputs_pressure_stress_and_budgets(self):
        root = Path(__file__).resolve().parents[1]
        paths = sorted((root/'data').glob('control_*.npz'))
        if not paths:
            self.skipTest('No saved control results in this checkout')
        for path in paths:
            with self.subTest(case=path.stem), np.load(path) as data:
                meta = json.loads(str(data['metadata']))
                for key in ('final_p', 'final_u', 'final_theta', 'pressure_load', 'trace'):
                    self.assertTrue(np.isfinite(data[key]).all(), key)
                p, u = data['final_p'], data['final_u']
                hx = meta['length'][0]/meta['shape'][0]
                ix = round(meta['curtain_x']/hx)
                iz = np.flatnonzero((data['z'] > meta['bottom']) &
                                    (data['z'] < meta['top']))
                dp = p[ix][:, iz]-p[ix-1][:, iz]
                np.testing.assert_allclose(dp, data['pressure_load'][-1],
                                           rtol=0., atol=5e-8)
                if 'viscous_load' in data:
                    outside_grad = u[0, ix][:, iz]/hx
                    inside_grad = -u[0, ix-2][:, iz]/hx
                    correction = -2*meta['rho']*meta['nu']*(outside_grad-inside_grad)
                    np.testing.assert_allclose(correction, data['viscous_load'][-1],
                                               rtol=0., atol=5e-8)
                # Pressure samples are equally sized curtain-face areas.
                np.testing.assert_allclose(data['pressure_load'].mean(axis=(1, 2)),
                                           data['trace'][:, 1], rtol=0., atol=5e-8)
                self.assertEqual(meta['max_wall_leak_m_s'], 0.)
                self.assertLess(meta['max_divergence'], 1e-9)
                self.assertLess(abs(meta['max_water_mass_balance_error_kg']), 1e-10)
                self.assertLess(abs(meta['max_water_momentum_balance_error_N_s']), 1e-9)
                self.assertLess(abs(meta['max_water_energy_balance_error_J']), 1e-5)
                self.assertLess(abs(meta['air_heat_balance_error_J']), 1e-5)
                if not meta['heat']:
                    np.testing.assert_array_equal(data['final_theta'], 0.)
                if not meta['heat'] and not meta['momentum']:
                    np.testing.assert_array_equal(u, 0.)
                    np.testing.assert_array_equal(p, 0.)


if __name__ == '__main__':
    unittest.main()
