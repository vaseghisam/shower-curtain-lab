"""Independent conservation, analytic-drag, and interpolation checks."""
import unittest
from types import SimpleNamespace
import numpy as np
from curtainflow.droplets import (Cloud, DropletConfig, cic_weights, deposit,
                                 drag_rate, interpolate, midpoint_motion,
                                 thermal_rate)


def grid_fixture(baffle=True):
    shape = (18, 16, 24)
    length = (1.8, 1.6, 2.4)
    mask = np.ones((3,) + shape)
    for d in range(3):
        index = [slice(None)] * 4
        index[0], index[d + 1] = d, -1
        mask[tuple(index)] = 0
    if baffle:
        mask[0, 8, :, 3:21] = 0
    return SimpleNamespace(shape=shape, h=np.asarray(length) / shape,
                           length=length, mask_faces=mask,
                           curtain_x=.9 if baffle else None, bottom=.3, top=2.1)


class DropletTests(unittest.TestCase):
    def test_quadratic_drag_terminal_solution_and_order(self):
        # Independent closed-form downward speed from rest under constant Cd.
        cfg = DropletConfig(constant_Cd=.5)
        diameter = np.array([.001])
        coefficient = 3 * cfg.rho_air * .5 / (4 * cfg.rho_water * diameter[0])
        terminal = np.sqrt(cfg.g / coefficient)
        duration = .8
        exact = terminal * np.tanh(cfg.g * duration / terminal)
        errors = []
        for dt in (.01, .005, .0025):
            velocity = np.zeros((1, 3))
            for _ in range(round(duration / dt)):
                velocity, _, _ = midpoint_motion(velocity, np.zeros_like(velocity), diameter, dt, cfg)
            errors.append(abs(velocity[0, 2] + exact))
        self.assertLess(errors[-1], 2e-5)
        self.assertGreater(errors[0] / errors[1], 3.8)
        self.assertGreater(errors[1] / errors[2], 3.8)

    def test_stokes_limit_and_zero_slip(self):
        cfg = DropletConfig(g=0)
        d = np.array([.001])
        zero = np.zeros((1, 3))
        expected = 18 * cfg.rho_air * cfg.nu_air / (cfg.rho_water * d**2)
        np.testing.assert_allclose(drag_rate(zero, d, cfg), expected)
        v, dx, drag = midpoint_motion(zero, zero, d, .01, cfg)
        np.testing.assert_array_equal(v, zero)
        np.testing.assert_array_equal(dx, zero)
        np.testing.assert_array_equal(drag, zero)
        expected_thermal = 12 * cfg.k_air / (cfg.rho_water * cfg.cp_water * d**2)
        np.testing.assert_allclose(thermal_rate(zero, d, cfg), expected_thermal)

    def test_cic_adjoint_conservation_and_baffle_exclusion(self):
        grid = grid_fixture()
        rng = np.random.default_rng(123)
        p = np.array([[.89, .7, 1.1], [.91, .7, 1.1], [.89, .7, 2.3]])
        st = cic_weights(p, grid.shape, grid.h, [.5]*3, np.ones(grid.shape), (.9, .3, 2.1))
        values = rng.normal(size=3)
        field = rng.normal(size=grid.shape)
        spread = deposit(values, st, grid.shape)
        self.assertAlmostEqual(spread.sum(), values.sum(), places=14)
        self.assertAlmostEqual(np.sum(spread * field), np.dot(values, interpolate(field, st)), places=14)
        # Interior parcels cannot exchange heat across the zero-thickness sheet.
        ix = np.unravel_index(st[0], grid.shape)[0]
        self.assertTrue(np.all(st[1][:, 0][ix[:, 0] >= 9] == 0))
        self.assertTrue(np.all(st[1][:, 1][ix[:, 1] < 9] == 0))

    def test_step_action_reaction_mass_and_heat(self):
        grid = grid_fixture()
        cloud = Cloud(grid, rays=8)
        dt = .002
        u = np.zeros((3,) + grid.shape)
        theta = np.zeros(grid.shape)
        f, q, diag = cloud.step(u, theta, dt)
        volume = np.prod(grid.h)
        expected_mass = 8e-3 / 60 * 1000 * dt
        self.assertAlmostEqual(cloud.masses.sum(), expected_mass, places=15)
        np.testing.assert_allclose(f.sum(axis=(1,2,3))*volume*dt, -cloud.drag_impulse, atol=1e-16)
        self.assertAlmostEqual(q.sum()*volume*dt*1.2*1005, -cloud.water_heat_change, places=12)
        np.testing.assert_allclose(diag["water_momentum_balance_error_kg_m_s"], 0, atol=1e-16)
        self.assertLess(abs(diag["water_heat_balance_error_J"]), 1e-10)
        self.assertTrue(np.all(f[grid.mask_faces == 0] == 0))
        self.assertGreater(diag["instantaneous_heat_watts"], 0)

    def test_injection_wall_exit_and_global_budgets(self):
        grid = grid_fixture(baffle=False)
        cloud = Cloud(grid, head=(.45,.35,.12), speed=2., tilt_deg=0,
                      head_radius=.01, rays=4)
        u, theta = np.zeros((3,) + grid.shape), np.zeros(grid.shape)
        for i in range(50):
            _, _, diag = cloud.step(u, theta, .002, i*.002)
        self.assertGreater(cloud.exited_mass, 0)
        self.assertLess(abs(diag["mass_balance_error_kg"]), 1e-14)
        np.testing.assert_allclose(diag["water_momentum_balance_error_kg_m_s"], 0, atol=1e-14)
        self.assertLess(abs(diag["water_heat_balance_error_J"]), 1e-9)
        np.testing.assert_allclose(cloud.gas_impulse + cloud.drag_impulse, 0, atol=1e-14)
        self.assertAlmostEqual(cloud.gas_energy + cloud.water_heat_change, 0, places=12)

    def test_diagnostic_switches_are_explicit(self):
        grid = grid_fixture()
        cloud = Cloud(grid, momentum=False, heat=False)
        u, theta = np.zeros((3,) + grid.shape), np.zeros(grid.shape)
        f, q, diag = cloud.step(u, theta, .002)
        self.assertTrue(np.all(f == 0))
        self.assertTrue(np.all(q == 0))
        self.assertGreater(diag["suppressed_sensible_heat_J"], 0)
        self.assertGreater(np.linalg.norm(diag["suppressed_drag_impulse_N_s"]), 0)

    def test_quadratic_wall_time_and_curtain_impact_budget(self):
        grid = grid_fixture()
        cloud = Cloud(grid, flow_lpm=0, constant_Cd=0, g=0)
        cloud.positions = np.array([[.89, .7, 1.]])
        cloud.velocities = np.array([[2., 0., 0.]])
        cloud.diameters = np.array([.001])
        cloud.masses = np.array([.01])
        cloud.temperatures = np.array([0.])
        cloud.injected_mass = .01
        cloud.injected_momentum = np.array([.02, 0., 0.])
        _, _, diag = cloud.step(np.zeros((3,)+grid.shape), np.zeros(grid.shape), .01)
        self.assertEqual(len(cloud.masses), 0)
        self.assertAlmostEqual(diag["curtain_impacted_mass_kg"], .01)
        np.testing.assert_allclose(diag["curtain_impacted_momentum_kg_m_s"], [.02,0,0])
        self.assertAlmostEqual(diag["outer_wall_exited_mass_kg"], 0)
        # Independently known free-fall time from rest to the floor.
        cloud.positions = np.array([[.45, .7, .001]])
        cloud.velocities = np.zeros((1,3))
        time, hit, curtain = cloud._collision_time(np.array([[0.,0.,-9.81]]), .1)
        self.assertAlmostEqual(time[0], np.sqrt(.002/9.81), places=14)
        self.assertTrue(hit[0])
        self.assertFalse(curtain[0])

    def test_drag_stiffness_screen_counts_represented_gas_loading(self):
        grid = grid_fixture()
        cloud = Cloud(grid, rays=1, head_radius=0)
        dt = .002
        beta = drag_rate(cloud._head_velocities, np.array([.001]), cloud.cfg)[0]
        mass = cloud.cfg.flow_lpm * 1e-3 / 60 * cloud.cfg.rho_water * dt
        maximum_weight = 0.
        for d in range(3):
            offset = np.full(3, .5)
            offset[d] = 1.
            _, weights = cic_weights(cloud._head_positions, grid.shape, grid.h,
                                     offset, grid.mask_faces[d], cloud.baffle)
            maximum_weight = max(maximum_weight, np.max(weights))
        expected_gamma = mass * beta * maximum_weight / (cloud.cfg.rho_air * np.prod(grid.h))
        _, _, diag = cloud.step(np.zeros((3,)+grid.shape), np.zeros(grid.shape), dt)
        self.assertAlmostEqual(diag["max_gas_drag_rate_s_inv"], expected_gamma, places=14)
        self.assertAlmostEqual(diag["coupling_dt_bound"], dt*(beta+expected_gamma), places=14)
        self.assertAlmostEqual(diag["coupling_nonlinear_dt_bound"], 2*dt*(beta+expected_gamma), places=14)
        self.assertEqual(diag["coupling_dt_bound"], diag["peak_coupling_dt_bound"])


if __name__ == "__main__":
    unittest.main()
