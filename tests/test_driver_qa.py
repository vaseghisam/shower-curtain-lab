"""Independent full-driver pressure test using a manufactured conservative force.

The mock is deliberately limited to the parcel source. The production driver,
two stage pressure projections, pressure output and sampling all run unchanged.
This is a numerical test, never an input to the shower figures.
"""
import unittest
from unittest.mock import patch

import numpy as np


class DriverIndependentQA(unittest.TestCase):
    def test_two_stage_pressure_has_full_force_not_half(self):
        from curtainflow.simulation import Config, run

        class ConservativeSource:
            def __init__(self, grid, **kwargs):
                self.grid = grid
                self.positions = np.empty((0, 3))
                x, y, z = grid.xyz
                self.p = .2*(x > .9) + .05*np.cos(np.pi*y/2.4)
                self.p -= self.p.mean()

            def step(self, u, theta, dt, t):
                # Force density = grad(p); acceleration = grad(p) / rho.
                return self.grid.grad(self.p), np.zeros(self.grid.shape), {}

        cfg = Config(shape=(12, 16, 16), duration=.012,
                     output_interval=.004, dt=.004, heat=False)
        with patch('curtainflow.simulation.Cloud', ConservativeSource):
            result = run(cfg, quiet=True)
        x, y, z = np.meshgrid(result['x'], result['y'], result['z'], indexing='ij')
        expected = .2*(x > .9) + .05*np.cos(np.pi*y/2.4)
        expected -= expected.mean()
        np.testing.assert_allclose(result['final_p'], expected, rtol=0., atol=2e-8)
        self.assertLess(float(np.max(np.abs(result['final_u']))), 2e-12)
        np.testing.assert_allclose(result['pressure_load'][1:], .2, rtol=0., atol=2e-8)


if __name__ == '__main__':
    unittest.main()
