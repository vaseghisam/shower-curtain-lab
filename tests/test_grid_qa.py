"""Independent numerical QA of the blocked-face MAC implementation.

These tests were authored separately from grid.py. Manufactured pressure fields
and discrete work identities test the operators without assuming a shower-flow
result or choosing parameters to produce inward movement.
"""
import unittest

import numpy as np

from curtainflow.grid import Grid


class GridIndependentQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grid = Grid((12, 16, 16), (1.8, 2.4, 2.4),
                        curtain_x=.9, bottom=.3, top=2.1)

    def random_projected(self, seed=1729):
        g = self.grid
        u = np.random.default_rng(seed).normal(size=(3,) + tuple(g.shape))
        return g.project(u, .002, 1.2)[0]

    def test_projection_is_incompressible_and_no_penetration(self):
        g = self.grid
        v = self.random_projected()
        self.assertLess(np.max(np.abs(g.div(v))), 2e-10)
        np.testing.assert_array_equal(v[g.mask_faces == 0], 0.)
        # Independent geometric face locations: exterior walls and curtain.
        self.assertEqual(float(np.max(np.abs(v[0, -1, :, :]))), 0.)
        self.assertEqual(float(np.max(np.abs(v[1, :, -1, :]))), 0.)
        self.assertEqual(float(np.max(np.abs(v[2, :, :, -1]))), 0.)
        curtain_face = 5  # (5 + 1) * 1.8 / 12 = 0.9 m
        z = (np.arange(16) + .5) * 2.4 / 16
        covered = (z > .3) & (z < 2.1)
        self.assertEqual(float(np.max(np.abs(v[0, curtain_face, :, covered]))), 0.)

    def test_pressure_projection_is_orthogonal_and_idempotent(self):
        g = self.grid
        rng = np.random.default_rng(1103)
        u = rng.normal(size=(3,) + tuple(g.shape)) * g.mask_faces
        v, _ = g.project(u, .002, 1.2)
        w, _ = g.project(v, .002, 1.2)
        np.testing.assert_allclose(w, v, rtol=0., atol=2e-11)
        self.assertLessEqual(float(np.sum(v*v)), float(np.sum(u*u)) + 1e-10)
        self.assertLess(abs(float(np.sum(v*(u-v)))), 2e-9)

    def test_divergence_gradient_discrete_work(self):
        g = self.grid
        rng = np.random.default_rng(42)
        u = rng.normal(size=(3,) + tuple(g.shape)) * g.mask_faces
        p = rng.normal(size=tuple(g.shape))
        lhs = float(np.sum(u * g.grad(p)))
        rhs = -float(np.sum(p * g.div(u)))
        self.assertAlmostEqual(lhs, rhs, delta=1e-9)

    def test_manufactured_pressure_jump_has_correct_sign(self):
        g = self.grid
        # Prescribed only for this mathematical operator test, not shower data.
        p = np.zeros(tuple(g.shape))
        p[6:, :, :] = .2
        p -= p.mean()
        v, recovered = g.project(.002 / 1.2 * g.grad(p), .002, 1.2)
        self.assertLess(float(np.max(np.abs(v))), 2e-12)
        np.testing.assert_allclose(recovered - recovered.mean(), p,
                                   rtol=0., atol=2e-10)
        # x increases outward; positive out-minus-in must mean inward loading.
        jump = recovered[6, :, 2:14] - recovered[5, :, 2:14]
        np.testing.assert_allclose(jump, .2, rtol=0., atol=2e-10)

    def test_hydrostatic_column_is_balanced_across_curtain(self):
        g = self.grid
        z = (np.arange(16) + .5) * 2.4 / 16
        p = np.broadcast_to(-1.2 * 9.81 * z, tuple(g.shape)).copy()
        p -= p.mean()
        v, recovered = g.project(.001 / 1.2 * g.grad(p), .001, 1.2)
        self.assertLess(float(np.max(np.abs(v))), 2e-12)
        np.testing.assert_allclose(recovered-recovered.mean(), p,
                                   rtol=0., atol=2e-9)
        np.testing.assert_allclose(recovered[6]-recovered[5], 0.,
                                   rtol=0., atol=2e-9)

    def test_zero_state_and_uniform_scalar(self):
        g = self.grid
        zero = np.zeros((3,) + tuple(g.shape))
        v, p = g.project(zero, .002, 1.2)
        np.testing.assert_array_equal(v, zero)
        np.testing.assert_array_equal(p, 0.)
        np.testing.assert_array_equal(g.convection(zero), zero)
        u = self.random_projected(19)
        constant = np.full(tuple(g.shape), 3.7)
        np.testing.assert_allclose(g.scalar_transport(u, constant), 0.,
                                   rtol=0., atol=1e-9)

    def test_scalar_transport_conserves_integral(self):
        g = self.grid
        u = self.random_projected(98)
        a = np.random.default_rng(63).normal(size=tuple(g.shape))
        rhs = g.scalar_transport(u, a)
        self.assertLess(abs(float(np.sum(rhs))), 2e-9)

    def test_centered_transport_kinetic_energy(self):
        g = self.grid
        u = self.random_projected(831)
        c = g.convection(u)
        power = float(np.sum(u*c))
        scale = max(1., float(np.sum(np.abs(u*c))))
        self.assertLess(abs(power)/scale, 2e-12,
                        f'Centered transport relative energy defect {power/scale}')

    def test_diffusion_is_symmetric_and_dissipative_at_baffle_tips(self):
        g = self.grid
        rng = np.random.default_rng(284)
        u = rng.normal(size=(3,) + tuple(g.shape)) * g.mask_faces
        v = rng.normal(size=(3,) + tuple(g.shape)) * g.mask_faces
        lu, lv = g.diffusion(u), g.diffusion(v)
        self.assertLess(float(np.sum(u*lu)), 0.)
        a, b = float(np.sum(u*lv)), float(np.sum(v*lu))
        self.assertAlmostEqual(a, b, delta=2e-10)
        np.testing.assert_array_equal(lu[g.mask_faces == 0], 0.)
        scalar = rng.normal(size=tuple(g.shape))
        self.assertLess(float(np.sum(scalar*g.lap(scalar))), 0.)
        self.assertLess(abs(float(g.lap(scalar).sum())), 2e-10)

    def test_free_slip_diffusion_matches_independent_eigenfunction(self):
        # In a box without a baffle, u_x = sin(kx*x) cos(ky*y) cos(kz*z)
        # has zero normal velocity at x walls and zero normal derivative at
        # the other walls. Check the actual staggered-grid eigenvalue.
        g = Grid((12, 16, 16), (1.8, 2.4, 2.4), curtain_x=None)
        x, y, z = np.meshgrid((np.arange(12)+1)*1.8/12,
                             (np.arange(16)+.5)*2.4/16,
                             (np.arange(16)+.5)*2.4/16,
                             indexing='ij')
        u = np.zeros((3,) + tuple(g.shape))
        u[0] = np.sin(np.pi*x/1.8)*np.cos(np.pi*y/2.4)*np.cos(np.pi*z/2.4)
        u *= g.mask_faces
        lam = -sum(4*np.sin(np.pi/(2*n))**2 / h**2
                   for n, h in zip(g.shape, g.h))
        np.testing.assert_allclose(g.diffusion(u), lam*u,
                                   rtol=0., atol=3e-12)

    def test_tvd_scalar_conserves_constant_mass_and_extrema(self):
        g = self.grid
        u = self.random_projected(1457)
        constant = np.full(tuple(g.shape), 2.3)
        np.testing.assert_allclose(g.scalar_transport(u, constant, scheme='tvd'),
                                   0., rtol=0., atol=1e-9)
        a = np.random.default_rng(492).uniform(.1, 1., tuple(g.shape))
        rhs = g.scalar_transport(u, a, scheme='tvd')
        self.assertLess(abs(float(rhs.sum())), 2e-9)
        outgoing = sum((np.maximum(u[d], 0.) +
                        np.maximum(-np.roll(u[d], 1, axis=d), 0.))/g.h[d]
                       for d in range(3))
        dt = .25/float(outgoing.max())
        updated = a-dt*rhs
        self.assertGreaterEqual(float(updated.min()), float(a.min())-1e-12)
        self.assertLessEqual(float(updated.max()), float(a.max())+1e-12)

    def test_tvd_smooth_interior_transport_second_order(self):
        errors = []
        # Constant interior transport and smooth strictly monotone data avoid
        # conflating limiter behaviour at extrema with smooth spatial order.
        for n in (8, 16, 32):
            g = Grid((n, n, n), (1.8, 2.4, 2.4), curtain_x=None)
            x, y, z = g.xyz
            a = np.exp(.4*x+.2*y+.3*z)
            u = np.empty((3,) + tuple(g.shape))
            u[0], u[1], u[2] = .2, .1, -.1
            u *= g.mask_faces
            calc = g.scalar_transport(u, a, scheme='tvd')
            exact = .07*a
            core = (slice(2, -2),)*3
            errors.append(float(np.sqrt(np.mean((calc[core]-exact[core])**2))))
        orders = np.log2(np.asarray(errors[:-1])/errors[1:])
        self.assertTrue(np.all(orders > 1.7), (errors, orders))


if __name__ == '__main__':
    unittest.main()
