"""Lagrangian water parcels with conservative drag and sensible-heat feedback.

Each numerical parcel represents ``mass`` kilograms of equal-diameter spherical
droplets, not one enlarged droplet. Their acceleration follows

    dv/dt = g - 3 rho_a C_D |v-u| (v-u) / (4 rho_w d),

with the Schiller--Naumann drag correlation and C_D=0.44 above Re=1000.
Temperature obeys dT_w/dt = 6 k_a Nu (T_a-T_w)/(rho_w c_pw d**2),
with Nu=2+0.6 Re**0.5 Pr**(1/3) (Ranz--Marshall). There is no evaporation,
breakup, collision, splash, radiation, or wall-film model. Gas velocity and
temperature are frozen during a parcel step; midpoint drag is second order
for that frozen velocity, whereas full gas--parcel splitting is first order.

The gas receives precisely the negative computed parcel drag impulse and
water sensible-energy change. Cloud-in-cell interpolation and deposition use
the same weights, normalized over open staggered faces (or fluid cells).
Gravity and momentum/energy carried into walls are accounted for separately.
Wall-hit steps are shortened to the first geometric intersection.
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class DropletConfig:
    flow_lpm: float = 8.0
    diameter_mm: float = 1.0
    speed: float = 1.0
    tilt_deg: float = 20.0
    cone_half_deg: float = 8.0
    head: tuple = (0.45, 0.35, 2.1)
    head_radius: float = 0.05
    rays: int = 12
    water_delta_T: float = 18.0
    momentum: bool = True
    heat: bool = True
    rho_air: float = 1.2
    nu_air: float = 1.5e-5
    rho_water: float = 1000.0
    cp_air: float = 1005.0
    cp_water: float = 4180.0
    k_air: float = 0.026
    Pr: float = 0.71
    g: float = 9.81
    curtain_x: float | None = 0.9
    curtain_bottom: float = 0.3
    curtain_top: float = 2.1
    constant_Cd: float | None = None


def drag_rate(slip, diameter, cfg):
    """Return a>=0 such that droplet drag acceleration is -a*(v-u)."""
    speed = np.linalg.norm(slip, axis=-1)
    diameter = np.asarray(diameter)
    Re = speed * diameter / cfg.nu_air
    if cfg.constant_Cd is not None:
        return 3 * cfg.rho_air * cfg.constant_Cd * speed / (4 * cfg.rho_water * diameter)
    stokes = 18 * cfg.rho_air * cfg.nu_air / (cfg.rho_water * diameter**2)
    low = stokes * (1 + 0.15 * Re**0.687)
    high = 3 * cfg.rho_air * 0.44 * speed / (4 * cfg.rho_water * diameter)
    return np.where(Re <= 1000, low, high)


def thermal_rate(slip, diameter, cfg):
    """Return inverse sensible-temperature relaxation time, in s**-1."""
    Re = np.linalg.norm(slip, axis=-1) * diameter / cfg.nu_air
    Nu = 2 + 0.6 * np.sqrt(Re) * cfg.Pr**(1 / 3)
    return 6 * cfg.k_air * Nu / (cfg.rho_water * cfg.cp_water * diameter**2)


def midpoint_motion(velocity, gas_velocity, diameter, duration, cfg):
    """Frozen-gas explicit midpoint step; return (v_new, dx, drag_dv).

    ``duration`` may have one entry per parcel, allowing a partial wall-hit
    step. ``drag_dv`` excludes gravity and defines the deposited gas impulse.
    """
    duration = np.broadcast_to(np.asarray(duration), (len(velocity),))
    gravity = np.array([0.0, 0.0, -cfg.g])
    slip = velocity - gas_velocity
    a0 = -drag_rate(slip, diameter, cfg)[:, None] * slip + gravity
    middle = velocity + 0.5 * duration[:, None] * a0
    slip_mid = middle - gas_velocity
    drag_dv = -duration[:, None] * drag_rate(slip_mid, diameter, cfg)[:, None] * slip_mid
    new_velocity = velocity + drag_dv + duration[:, None] * gravity
    return new_velocity, duration[:, None] * middle, drag_dv


def cic_weights(positions, shape, h, offset, open_mask, baffle=None):
    """Flattened indices and normalized 8-node weights; no periodic wrap.

    Cell centers use offset=(.5,.5,.5). Positive x faces use (1,.5,.5),
    likewise for y,z. An unavailable boundary node is removed before
    normalization. Return arrays of shape (8, n_parcels).
    """
    positions = np.asarray(positions)
    q = positions / np.asarray(h) - np.asarray(offset)
    lower = np.floor(q).astype(int)
    frac = q - lower
    indices, weights = [], []
    shape = np.asarray(shape, dtype=int)
    for code in range(8):
        corner = np.array([(code >> d) & 1 for d in range(3)])
        index = lower + corner
        valid = np.all((index >= 0) & (index < shape), axis=1)
        safe = np.clip(index, 0, shape - 1)
        flat = np.ravel_multi_index(safe.T, tuple(shape))
        weight = np.prod(np.where(corner, frac, 1 - frac), axis=1)
        weight *= valid * np.asarray(open_mask).ravel()[flat]
        if baffle is not None and baffle[0] is not None:
            bx, bz0, bz1 = baffle
            node = (safe + np.asarray(offset)) * np.asarray(h)
            crossing = (positions[:, 0] - bx) * (node[:, 0] - bx) < 0
            along = np.divide(bx - positions[:, 0], node[:, 0] - positions[:, 0],
                              out=np.zeros(len(positions)), where=crossing)
            z_cross = positions[:, 2] + along * (node[:, 2] - positions[:, 2])
            weight *= ~(crossing & (z_cross >= bz0) & (z_cross <= bz1))
        indices.append(flat)
        weights.append(weight)
    indices, weights = np.asarray(indices), np.asarray(weights)
    total = weights.sum(axis=0)
    if np.any(total <= 0):
        raise ValueError("Parcel has no open grid support; check inlet/wall geometry")
    return indices, weights / total[None, :]


def interpolate(field, stencil):
    index, weight = stencil
    return np.sum(np.asarray(field).ravel()[index] * weight, axis=0)


def deposit(values, stencil, shape):
    """Conservative adjoint of interpolation; returns integrated nodal values."""
    index, weight = stencil
    return np.bincount(index.ravel(), weights=(weight * values[None, :]).ravel(),
                       minlength=int(np.prod(shape))).reshape(shape)


def nozzle_rays(cfg):
    """Deterministic equal-mass disk/cone quadrature, independent of mesh."""
    i = np.arange(cfg.rays)
    radius = np.sqrt((i + 0.5) / cfg.rays)
    angle = i * np.pi * (3 - np.sqrt(5))
    tilt = np.deg2rad(cfg.tilt_deg)
    axis = np.array([0.0, np.sin(tilt), -np.cos(tilt)])
    e1 = np.array([1.0, 0.0, 0.0])
    e2 = np.cross(axis, e1)
    transverse = np.cos(angle)[:, None] * e1 + np.sin(angle)[:, None] * e2
    positions = np.asarray(cfg.head) + cfg.head_radius * radius[:, None] * transverse
    cone = radius * np.deg2rad(cfg.cone_half_deg)
    directions = np.cos(cone)[:, None] * axis + np.sin(cone)[:, None] * transverse
    return positions, cfg.speed * directions


class Cloud:
    """Continuous deterministic parcel injection and conservative feedback.

    Required grid attributes: shape, h, mask_faces with shape (3,*shape).
    Optional ``fluid`` or ``mask_cells`` is a boolean fluid-cell mask. If
    absent all scalar cells are assumed fluid. Public parcel temperatures
    are temperature differences from the same ambient reference as theta.
    """

    def __init__(self, grid, config=None, **kwargs):
        if config is None:
            self.cfg = DropletConfig(**kwargs)
        elif isinstance(config, dict):
            self.cfg = DropletConfig(**(config | kwargs))
        elif isinstance(config, DropletConfig) and not kwargs:
            self.cfg = config
        else:
            raise TypeError("Pass a DropletConfig, dictionary, or keyword parameters")
        cfg = self.cfg
        if cfg.flow_lpm < 0 or cfg.diameter_mm <= 0 or cfg.rays < 1 or cfg.speed < 0:
            raise ValueError("Invalid injection parameters")
        if cfg.rho_air <= 0 or cfg.rho_water <= 0 or cfg.nu_air <= 0:
            raise ValueError("Fluid density and viscosity must be positive")
        self.grid = grid
        # Collision and interpolation barriers must match the flow geometry.
        if hasattr(grid, "curtain_x"):
            cfg.curtain_x = grid.curtain_x
            cfg.curtain_bottom = grid.bottom
            cfg.curtain_top = grid.top
        self.baffle = (cfg.curtain_x, cfg.curtain_bottom, cfg.curtain_top)
        self.shape = tuple(grid.shape)
        self.h = np.asarray(grid.h, dtype=float)
        self.length = self.h * self.shape
        self.volume = float(np.prod(self.h))
        self.cell_mask = np.asarray(getattr(grid, "fluid", getattr(grid, "mask_cells", np.ones(self.shape))))
        self.positions = np.empty((0, 3))
        self.velocities = np.empty((0, 3))
        self.masses = np.empty(0)
        self.diameters = np.empty(0)
        self.temperatures = np.empty(0)
        self.injected_mass = 0.0
        self.exited_mass = 0.0
        self.injected_momentum = np.zeros(3)
        self.exited_momentum = np.zeros(3)
        self.curtain_impacted_mass = 0.0
        self.curtain_impacted_momentum = np.zeros(3)
        self.curtain_impacted_energy = 0.0
        self.gravity_impulse = np.zeros(3)
        self.gas_impulse = np.zeros(3)
        self.drag_impulse = np.zeros(3)
        self.injected_energy = 0.0
        self.exited_energy = 0.0
        self.gas_energy = 0.0
        self.water_heat_change = 0.0
        self.peak_coupling_dt_bound = 0.0
        self.peak_coupling_nonlinear_dt_bound = 0.0
        self.max_particle_drag_rate = 0.0
        self.max_gas_drag_rate = 0.0
        self.coupling_dt_bound = 0.0
        self.coupling_nonlinear_dt_bound = 0.0
        self._head_positions, self._head_velocities = nozzle_rays(cfg)
        if np.any(self._head_positions <= 0) or np.any(self._head_positions >= self.length):
            raise ValueError("Nozzle injection disk must be inside the fluid domain")

    def _inject(self, dt):
        cfg = self.cfg
        mass = cfg.flow_lpm * 1e-3 / 60 * cfg.rho_water * dt
        if mass == 0:
            return
        n = cfg.rays
        masses = np.full(n, mass / n)
        self.positions = np.concatenate((self.positions, self._head_positions))
        self.velocities = np.concatenate((self.velocities, self._head_velocities))
        self.masses = np.concatenate((self.masses, masses))
        self.diameters = np.concatenate((self.diameters, np.full(n, cfg.diameter_mm * 1e-3)))
        self.temperatures = np.concatenate((self.temperatures, np.full(n, cfg.water_delta_T)))
        self.injected_mass += mass
        self.injected_momentum += (masses[:, None] * self._head_velocities).sum(axis=0)
        self.injected_energy += mass * cfg.cp_water * cfg.water_delta_T

    def _collision_time(self, acceleration, dt):
        """First exact wall intersection of the midpoint quadratic path.

        For each coordinate the midpoint position is x+v*t+a_old*t**2/2.
        Solving that quadratic avoids the chord-intersection time error. It
        remains an approximation to the continuous drag trajectory, with the
        same accuracy as the parcel integrator.
        """
        n = len(self.positions)
        duration = np.full(n, dt)
        hit = np.zeros(n, dtype=bool)
        curtain_hit = np.zeros(n, dtype=bool)

        def roots(d, boundary):
            a = .5 * acceleration[:, d]
            b = self.velocities[:, d]
            c = self.positions[:, d] - boundary
            discriminant = b*b - 4*a*c
            quadratic = (np.abs(a) > 1e-14) & (discriminant >= 0)
            q = -.5 * (b + np.copysign(np.sqrt(np.maximum(discriminant, 0)), b))
            first = np.divide(q, a, out=np.full(n, np.inf), where=quadratic)
            second = np.divide(c, q, out=np.full(n, np.inf), where=quadratic & (q != 0))
            linear = (np.abs(a) <= 1e-14) & (b != 0)
            first[linear] = -c[linear] / b[linear]
            for result in (first, second):
                result[(result < 0) | (result > dt)] = np.inf
            return first, second

        for d in range(3):
            for boundary in (0.0, self.length[d]):
                first, second = roots(d, boundary)
                event = np.minimum(first, second)
                earlier = event <= duration
                duration[earlier] = event[earlier]
                hit |= earlier
        cfg = self.cfg
        if cfg.curtain_x is not None:
            for event in roots(0, cfg.curtain_x):
                finite = np.isfinite(event)
                safe_time = np.where(finite, event, 0)
                z = self.positions[:, 2] + self.velocities[:, 2]*safe_time + .5*acceleration[:, 2]*safe_time**2
                earlier = finite & (event <= duration) & (z >= cfg.curtain_bottom) & (z <= cfg.curtain_top)
                duration[earlier] = event[earlier]
                hit |= earlier
                curtain_hit |= earlier
        return duration, hit, curtain_hit

    def step(self, u, theta, dt, t=0.0):
        """Advance parcels; return gas force density, heat rate, diagnostics.

        ``momentum=False`` or ``heat=False`` suppresses that feedback and
        records the suppressed transfer, allowing explicit mechanism controls.
        Water trajectories and cooling still evolve in these diagnostic cases.
        """
        if dt <= 0:
            raise ValueError("dt must be positive")
        self._inject(dt)
        cfg = self.cfg
        n = len(self.positions)
        force = np.zeros((3,) + self.shape)
        heat = np.zeros(self.shape)
        if n == 0:
            return force, heat, self.diagnostics()
        stencils = []
        for d in range(3):
            offset = np.full(3, 0.5)
            offset[d] = 1.0
            stencils.append(cic_weights(self.positions, self.shape, self.h, offset, self.grid.mask_faces[d], self.baffle))
        thermal_stencil = cic_weights(self.positions, self.shape, self.h, np.full(3, .5), self.cell_mask, self.baffle)
        gas_velocity = np.column_stack([interpolate(u[d], stencils[d]) for d in range(3)])
        gas_temperature = interpolate(theta, thermal_stencil)
        slip = self.velocities - gas_velocity
        rate = drag_rate(slip, self.diameters, cfg)
        # Frozen linear-drag coupled stiffness screen. Interpolation weights
        # sum to one, so Jensen's inequality bounds the coupled exchange
        # eigenvalues by beta_max + gamma_max, where beta is particle drag
        # rate and gamma_i=sum_p(m_p*beta_p*w_ip)/(rho_a*V). The quadratic
        # drag Jacobian has at most twice its frozen-rate magnitude. These
        # numbers diagnose the source splitting; they do not prove stability
        # of the complete flow integrator. No acceptance threshold is imposed.
        self.max_particle_drag_rate = float(np.max(rate))
        self.max_gas_drag_rate = 0.0
        if cfg.momentum:
            represented_drag = self.masses * rate
            for stencil in stencils:
                gamma = deposit(represented_drag, stencil, self.shape) / (cfg.rho_air * self.volume)
                self.max_gas_drag_rate = max(self.max_gas_drag_rate, float(np.max(gamma)))
        self.coupling_dt_bound = dt * (self.max_particle_drag_rate + self.max_gas_drag_rate)
        self.coupling_nonlinear_dt_bound = 2 * self.coupling_dt_bound
        self.peak_coupling_dt_bound = max(self.peak_coupling_dt_bound, self.coupling_dt_bound)
        self.peak_coupling_nonlinear_dt_bound = max(self.peak_coupling_nonlinear_dt_bound, self.coupling_nonlinear_dt_bound)
        max_drag_step = float(np.max(rate * dt))
        if max_drag_step > .5:
            raise RuntimeError(f"Parcel drag step too large ({max_drag_step:.3g}); reduce dt")
        acceleration = -rate[:, None] * slip + np.array([0., 0., -cfg.g])
        actual_dt, hit, curtain_hit = self._collision_time(acceleration, dt)
        new_velocity, displacement, drag_dv = midpoint_motion(self.velocities, gas_velocity, self.diameters, actual_dt, cfg)
        # The exponential update is exact for the frozen heat-transfer rate.
        decay = np.exp(-thermal_rate(slip, self.diameters, cfg) * actual_dt)
        new_temperature = gas_temperature + (self.temperatures - gas_temperature) * decay
        water_impulse = self.masses[:, None] * drag_dv
        water_heat = self.masses * cfg.cp_water * (new_temperature - self.temperatures)
        gas_impulse = -water_impulse
        gas_heat = -water_heat
        if cfg.momentum:
            for d in range(3):
                force[d] = deposit(gas_impulse[:, d], stencils[d], self.shape) / (dt * self.volume)
            self.gas_impulse += gas_impulse.sum(axis=0)
        if cfg.heat:
            heat = deposit(gas_heat, thermal_stencil, self.shape) / (dt * self.volume * cfg.rho_air * cfg.cp_air)
            self.gas_energy += gas_heat.sum()
        self.drag_impulse += water_impulse.sum(axis=0)
        self.water_heat_change += water_heat.sum()
        self.gravity_impulse[2] -= cfg.g * np.dot(self.masses, actual_dt)
        self.positions += displacement
        self.velocities = new_velocity
        self.temperatures = new_temperature
        self.exited_mass += self.masses[hit].sum()
        self.exited_momentum += (self.masses[hit, None] * self.velocities[hit]).sum(axis=0)
        self.exited_energy += np.dot(self.masses[hit], self.temperatures[hit]) * cfg.cp_water
        self.curtain_impacted_mass += self.masses[curtain_hit].sum()
        self.curtain_impacted_momentum += (self.masses[curtain_hit, None] * self.velocities[curtain_hit]).sum(axis=0)
        self.curtain_impacted_energy += np.dot(self.masses[curtain_hit], self.temperatures[curtain_hit]) * cfg.cp_water
        if np.any(hit):
            for key in ("positions", "velocities", "masses", "diameters", "temperatures"):
                setattr(self, key, getattr(self, key)[~hit])
        diagnostic = self.diagnostics()
        diagnostic["max_drag_step"] = max_drag_step
        diagnostic["instantaneous_gas_force"] = gas_impulse.sum(axis=0).tolist() if cfg.momentum else [0., 0., 0.]
        diagnostic["instantaneous_gas_force"] = (np.asarray(diagnostic["instantaneous_gas_force"]) / dt).tolist()
        diagnostic["instantaneous_heat_watts"] = float(gas_heat.sum() / dt) if cfg.heat else 0.
        return force, heat, diagnostic

    def diagnostics(self):
        momentum = (self.masses[:, None] * self.velocities).sum(axis=0)
        energy = np.dot(self.masses, self.temperatures) * self.cfg.cp_water
        momentum_residual = momentum + self.exited_momentum - self.injected_momentum - self.gravity_impulse - self.drag_impulse
        heat_residual = energy + self.exited_energy - self.injected_energy - self.water_heat_change
        return {
            "parcels": int(len(self.masses)),
            "max_particle_drag_rate_s_inv": self.max_particle_drag_rate,
            "max_gas_drag_rate_s_inv": self.max_gas_drag_rate,
            "coupling_dt_bound": self.coupling_dt_bound,
            "coupling_nonlinear_dt_bound": self.coupling_nonlinear_dt_bound,
            "peak_coupling_dt_bound": self.peak_coupling_dt_bound,
            "peak_coupling_nonlinear_dt_bound": self.peak_coupling_nonlinear_dt_bound,
            "water_mass_present_kg": float(self.masses.sum()),
            "water_mass_injected_kg": self.injected_mass,
            "water_mass_exited_kg": self.exited_mass,
            "curtain_impacted_mass_kg": self.curtain_impacted_mass,
            "curtain_impacted_momentum_kg_m_s": self.curtain_impacted_momentum.tolist(),
            "curtain_impacted_sensible_energy_J": self.curtain_impacted_energy,
            "outer_wall_exited_mass_kg": self.exited_mass - self.curtain_impacted_mass,
            "mass_balance_error_kg": float(self.masses.sum() + self.exited_mass - self.injected_mass),
            "water_momentum_balance_error_kg_m_s": momentum_residual.tolist(),
            "water_heat_balance_error_J": float(heat_residual),
            "gas_drag_impulse_N_s": self.gas_impulse.tolist(),
            "water_drag_impulse_N_s": self.drag_impulse.tolist(),
            "suppressed_drag_impulse_N_s": (-self.drag_impulse - self.gas_impulse).tolist(),
            "gas_sensible_heat_J": float(self.gas_energy),
            "suppressed_sensible_heat_J": float(-self.water_heat_change - self.gas_energy),
        }
