"""Conservative staggered-grid operators for a closed box with a thin baffle.

The cell-centered pressure has shape ``(Nx, Ny, Nz)``.  ``u[d]`` has the same
shape but stores the velocity on each cell's positive d-face. The final face
in each direction is an impermeable outer wall; the missing negative wall
has the same prescribed value, zero. Although ``roll`` is used to index these
arrays, no scalar or mass flux crosses a periodic boundary.

The curtain is a grid-aligned, zero-thickness, impermeable x-baffle spanning
the full y width. It runs from ``bottom`` to ``top``; air can circulate around
its horizontal edges. All solid boundaries impose zero normal velocity and
free tangential slip. No curtain penalty force or imposed pressure is used.

The pressure projection exactly solves the masked discrete Poisson problem
to sparse-factorization precision. The y-independent geometry permits an
orthonormal cosine transform in y and separate sparse x-z solves. This
solver therefore does not support y-dependent bodies or finite-width gaps.

Momentum transport uses centered conservative fluxes and conserves discrete
kinetic energy for a divergence-free field. Scalar transport can use either
centered fluxes (the default) or limited MUSCL upwind fluxes (``scheme='tvd'``).
The centered scalar scheme is not positivity-preserving. The time integrator
must control stability, and scalar extrema must be checked by the caller.
Centered space differences are second order on smooth interior solutions;
this is not a statement of second-order convergence at sharp baffle edges.
"""

from __future__ import annotations

import numpy as np
from scipy.fft import dct, idct
from scipy.sparse import coo_matrix, eye
from scipy.sparse.linalg import splu


class Grid:
    """MAC grid with impermeable, free-slip walls and an optional x-baffle.

    ``curtain_x=None`` disables the internal baffle. All supplied baffle
    coordinates must coincide with mesh faces; silently snapping a physical
    boundary differently on different grids would spoil a refinement study.
    """

    def __init__(self, shape=(24, 32, 32), length=(1.8, 2.4, 2.4),
                 curtain_x=.9, bottom=.3, top=2.1):
        self.shape = tuple(int(n) for n in shape)
        self.length = tuple(float(v) for v in length)
        if len(self.shape) != 3 or len(self.length) != 3:
            raise ValueError("shape and length must have three entries")
        if any(n < 2 for n in self.shape) or any(v <= 0 for v in self.length):
            raise ValueError("grid lengths must be positive and sizes at least two")
        self.h = np.asarray(self.length) / np.asarray(self.shape)
        self.axes = [(np.arange(n) + .5) * h
                     for n, h in zip(self.shape, self.h)]
        self.xyz = np.meshgrid(*self.axes, indexing="ij")
        self.curtain_x = curtain_x
        self.bottom = float(bottom)
        self.top = float(top)
        self.mask_faces = np.ones((3,) + self.shape)
        for d in range(3):
            index = [slice(None)] * 4
            index[0] = d
            index[d + 1] = -1
            self.mask_faces[tuple(index)] = 0.
        self.curtain_face_index = None
        self.curtain_z_slice = slice(0, 0)
        self.curtain_mask_yz = np.zeros(self.shape[1:], dtype=bool)
        if curtain_x is not None:
            if not (0 < curtain_x < self.length[0]):
                raise ValueError("curtain_x must lie inside the box")
            if not (0 <= bottom < top <= self.length[2]):
                raise ValueError("invalid curtain vertical span")
            locations = (curtain_x / self.h[0], bottom / self.h[2],
                         top / self.h[2])
            if not all(np.isclose(v, round(v), rtol=0, atol=1e-9)
                       for v in locations):
                raise ValueError("baffle coordinates must coincide with mesh faces")
            ix, iz0, iz1 = (int(round(v)) for v in locations)
            if iz0 == 0 and iz1 == self.shape[2]:
                raise ValueError("full-height baffle disconnects the pressure domain")
            self.curtain_face_index = ix - 1
            self.curtain_z_slice = slice(iz0, iz1)
            self.curtain_mask_yz[:, iz0:iz1] = True
            self.mask_faces[0, ix - 1, :, iz0:iz1] = 0.
        self._make_pressure_solver()

    def _make_pressure_solver(self):
        """Factor the y cosine modes of minus the masked Laplacian."""
        nx, ny, nz = self.shape
        ids = np.arange(nx * nz).reshape(nx, nz)
        rows, cols, values = [], [], []
        for d2, d3 in ((0, 0), (1, 2)):
            source = [slice(None), slice(None)]
            target = [slice(None), slice(None)]
            source[d2] = slice(None, -1)
            target[d2] = slice(1, None)
            source, target = tuple(source), tuple(target)
            aperture = self.mask_faces[d3, :, 0, :][source]
            keep = aperture > 0
            a, b = ids[source][keep], ids[target][keep]
            coeff = aperture[keep] / self.h[d3] ** 2
            for r, c, v in ((a, a, coeff), (b, b, coeff),
                            (a, b, -coeff), (b, a, -coeff)):
                rows.extend(r)
                cols.extend(c)
                values.extend(v)
        a0 = coo_matrix((values, (rows, cols)),
                        shape=(nx * nz, nx * nz)).tocsc()
        self._poisson_factors = []
        eye2 = eye(nx * nz, format="csc")
        # The constant cosine mode is singular. Remove one pressure unknown;
        # compatibility supplies its equation, and a mean-zero gauge is set
        # after all modes have been transformed back to physical space.
        self._poisson_factors.append(splu(a0[1:, 1:].tocsc()))
        for j in range(1, ny):
            eigenvalue = 4 * np.sin(np.pi * j / (2 * ny)) ** 2 / self.h[1] ** 2
            self._poisson_factors.append(splu(a0 + eigenvalue * eye2))

    def centers(self, u):
        """Average positive and negative faces to cell centers."""
        u = np.asarray(u) * self.mask_faces
        return np.asarray([.5 * (u[d] + np.roll(u[d], 1, axis=d))
                           for d in range(3)])

    def faces(self, f):
        """Average cell-centered vector values to open positive faces."""
        return np.asarray([.5 * (f[d] + np.roll(f[d], -1, axis=d))
                           for d in range(3)]) * self.mask_faces

    def div(self, u):
        """Conservative cell divergence; closed faces contribute zero flux."""
        u = np.asarray(u) * self.mask_faces
        return sum((u[d] - np.roll(u[d], 1, axis=d)) / self.h[d]
                   for d in range(3))

    def grad(self, p):
        """Pressure gradient on open faces, zero on solid normals."""
        return np.asarray([(np.roll(p, -1, axis=d) - p) / self.h[d]
                           for d in range(3)]) * self.mask_faces

    def lap(self, a):
        """Scalar no-flux Laplacian, exactly ``div(grad(a))``."""
        return self.div(self.grad(a))

    def project(self, u, dt, rho):
        """Return divergence-free velocity and its pressure in pascals.

        The input is a provisional MAC velocity in m/s. ``dt`` is seconds
        and ``rho`` kg/m^3. The pressure has zero cell-volume mean. Projection
        changes velocity by ``-dt/rho * grad(p)`` on the open faces.
        """
        if dt <= 0 or rho <= 0:
            raise ValueError("projection dt and density must be positive")
        bounded = np.asarray(u, dtype=float) * self.mask_faces
        rhs = -rho / dt * self.div(bounded)
        rhs -= rhs.mean()
        modes = dct(rhs, type=2, axis=1, norm="ortho", workers=1)
        pmodes = np.empty_like(modes)
        mode0 = np.zeros(self.shape[0] * self.shape[2])
        mode0[1:] = self._poisson_factors[0].solve(modes[:, 0, :].ravel()[1:])
        pmodes[:, 0, :] = mode0.reshape(self.shape[0], self.shape[2])
        for j in range(1, self.shape[1]):
            pmodes[:, j, :] = self._poisson_factors[j].solve(
                modes[:, j, :].ravel()).reshape(self.shape[0], self.shape[2])
        p = idct(pmodes, type=2, axis=1, norm="ortho", workers=1)
        p -= p.mean()
        return bounded - dt / rho * self.grad(p), p

    def convection(self, u):
        """Centered conservative MAC approximation to div(u tensor u).

        Each momentum flux uses the product of velocity averages at a common
        dual-control-volume face. For discretely solenoidal u this conserves
        the volume-weighted sum of |u|^2/2 before time discretization.
        Closed-face velocities are identically zero throughout the operator.
        """
        u = np.asarray(u) * self.mask_faces
        out = np.zeros_like(u)
        for c in range(3):
            for d in range(3):
                transport = .5 * (u[d] + np.roll(u[d], -1, axis=c))
                value = .5 * (u[c] + np.roll(u[c], -1, axis=d))
                flux = transport * value
                out[c] += (flux - np.roll(flux, 1, axis=d)) / self.h[d]
        return out * self.mask_faces

    def scalar_transport(self, u, a, scheme="central"):
        """Conservative scalar flux divergence with no wall leakage.

        ``central`` uses arithmetic face averages. ``tvd`` uses piecewise
        linear MUSCL reconstruction with a monotonized-central (MC) limiter
        and an upwind flux. A slope is zero wherever either adjacent normal
        face is blocked, so reconstruction never samples through a wall.

        The limited reconstruction is second order in smooth monotone
        interior regions and locally first order at extrema and walls.
        ``tvd`` names the one-dimensional limiter; it is not a claim that
        arbitrary multidimensional/time-discrete updates are TVD. For an
        incompressible velocity, nonnegative scalar data, and forward Euler,
        ``dt * sum(outgoing face speeds / h) <= 1/2`` is a sufficient
        positivity condition for this reconstruction. Additional diffusion
        and sources require their own combined timestep restriction. Use an
        SSP integrator and inspect extrema in the actual calculation.
        """
        if scheme not in ("central", "tvd"):
            raise ValueError("scalar scheme must be 'central' or 'tvd'")
        u = np.asarray(u) * self.mask_faces
        a = np.asarray(a)
        out = np.zeros_like(a, dtype=float)
        for d in range(3):
            if scheme == "central":
                value = .5 * (a + np.roll(a, -1, axis=d))
            else:
                left_difference = a - np.roll(a, 1, axis=d)
                right_difference = np.roll(a, -1, axis=d) - a
                centered_difference = .5 * (left_difference + right_difference)
                magnitude = np.minimum(np.minimum(2 * np.abs(left_difference),
                                                   2 * np.abs(right_difference)),
                                       np.abs(centered_difference))
                same_sign = left_difference * right_difference > 0
                open_neighbors = self.mask_faces[d] * np.roll(
                    self.mask_faces[d], 1, axis=d)
                slope = np.sign(centered_difference) * magnitude * same_sign * open_neighbors
                left_state = a + .5 * slope
                right_state = np.roll(a - .5 * slope, -1, axis=d)
                value = np.where(u[d] >= 0, left_state, right_state)
            flux = u[d] * value
            out += (flux - np.roll(flux, 1, axis=d)) / self.h[d]
        return out

    def diffusion(self, u):
        """Free-slip vector Laplacian on the MAC dual control volumes.

        Normal velocities satisfy their prescribed zero value. Tangential
        diffusion has no wall-normal flux. At a baffle tip, a dual face that
        straddles a blocked and open primal face has half its area open. The
        resulting symmetric operator dissipates discrete kinetic energy.
        Multiply this result by the chosen kinematic viscosity externally.
        """
        u = np.asarray(u) * self.mask_faces
        out = np.zeros_like(u)
        for c in range(3):
            for d in range(3):
                if c == d:
                    aperture = 1.
                else:
                    aperture = .5 * (self.mask_faces[d]
                                     + np.roll(self.mask_faces[d], -1, axis=c))
                flux = aperture * (np.roll(u[c], -1, axis=d) - u[c]) / self.h[d]
                out[c] += (flux - np.roll(flux, 1, axis=d)) / self.h[d]
        return out * self.mask_faces
