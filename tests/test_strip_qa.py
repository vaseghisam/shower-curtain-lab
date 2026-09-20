"""Independent pressure-to-mechanics interface checks."""
import json
import unittest

import numpy as np

from curtainflow.mechanics import transient, equilibrium
from curtainflow.simulation import strip_response


class StripInterfaceIndependentQA(unittest.TestCase):
    def test_original_uniform_pressure_benchmark_and_mesh_order(self):
        # Direct article formula, independently evaluated rather than calling
        # the production exact_profile helper.
        H, sigma, pressure, gravity = 1.8, .2, .2, 9.81
        s, unweighted = equilibrium(pressure, n=128, H=H, sigma=sigma, hem=0.)
        np.testing.assert_allclose(unweighted, pressure*s/(sigma*gravity),
                                   rtol=0., atol=2e-14)
        self.assertAlmostEqual(unweighted[-1], .1834862385321101, 13)
        hem = .1
        exact_bottom = pressure/(sigma*gravity)*(H-hem/sigma*np.log1p(sigma*H/hem))
        self.assertAlmostEqual(exact_bottom, .1057055910552982, 13)
        errors = []
        for n in [64, 128, 256]:
            _, y = equilibrium(pressure, n=n, H=H, sigma=sigma, hem=hem)
            errors.append(abs(y[-1]-exact_bottom))
        self.assertLess(errors[-1], 5e-7)
        self.assertTrue(np.all(np.log2(np.array(errors[:-1])/errors[1:]) > 1.99))

    def test_saved_pressure_reaches_correct_strip_height_width_and_time(self):
        top, bottom = 2.1, .3
        t = np.linspace(0., 1., 21)
        z = np.linspace(bottom, top, 41)
        widths = np.array([.4, .8, 1.2])
        factors = np.array([1., 2., 3.])
        q = lambda s: .002+.003*s
        loads = np.minimum(t/.3, 1.)[:, None, None] * factors[None, :, None] * q(top-z)[None, None, :]
        data = {'trace': t[:, None], 'pressure_load': loads,
                'load_z': z, 'y': widths,
                'metadata': np.array(json.dumps({'top': top, 'bottom': bottom}))}
        result = strip_response(data, sigma=.2, hem=.1, damping=.05, n=32)
        self.assertEqual(len(result), 3)
        for factor, width, actual in zip(factors, widths, result):
            exact = transient(n=32, H=top-bottom, sigma=.2, hem=.1,
                              pressure=lambda s: factor*q(s), damping=.05,
                              ramp=.3, duration=1., frames=21)
            self.assertEqual(actual['reason'], 'end')
            self.assertAlmostEqual(actual['width_y_m'], width)
            np.testing.assert_allclose(actual['t'], exact['t'], atol=1e-14)
            np.testing.assert_allclose(actual['y'], exact['y'], rtol=2e-5, atol=2e-8)

    def test_first_contact_contains_actual_event_state(self):
        t = np.linspace(0., 2., 41)
        z = np.linspace(.3, 2.1, 41)
        loads = np.full((len(t), 1, len(z)), .2)
        data = {'trace': t[:, None], 'pressure_load': loads, 'load_z': z,
                'y': np.array([.8]),
                'metadata': np.array(json.dumps({'top': 2.1, 'bottom': .3}))}
        actual = strip_response(data, sigma=.2, hem=.1, damping=0., n=64)[0]
        self.assertEqual(actual['reason'], 'first_contact')
        self.assertAlmostEqual(actual['t'][-1], actual['event_time'], 13)
        self.assertAlmostEqual(float(actual['y'][-1].max()), .15, 10)


if __name__ == '__main__':
    unittest.main()
