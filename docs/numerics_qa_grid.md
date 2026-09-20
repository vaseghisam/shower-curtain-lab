# Independent QA of the new MAC grid

Reviewed 15 September 2026. The reviewer inspected `curtainflow/grid.py` and authored `tests/test_grid_qa.py` independently of its implementation. All twelve independent grid tests passed locally. Three further driver/structural-interface tests passed, as described below. This is approval of the tested numerical operators and interfaces, not of unexamined physical parameter choices or final simulation results.

The new grid removes the old model's finite-slip sheet and penalized exterior walls. Curtain and wall normal velocities are exactly zero on their blocked MAC faces; the same face mask enters divergence, pressure gradient and the pressure Poisson operator. Thus a small divergence residual now accompanies an independently tested impermeability constraint. Both sides of the curtain share one pressure gauge because the top and lower gaps connect the fluid regions.

The pressure solver's cosine decomposition applies because the geometry is independent of the width coordinate. It therefore cannot represent a three-dimensional body or a curtain with finite side gaps without modifying that solver. The model must retain the documented full-width curtain and free-slip tangential wall conditions.

## Executed independent tests

| Test | Purpose | Result |
|---|---|---|
| Incompressibility and no penetration | A random provisional field becomes divergence-free; all curtain and exterior normal-face velocities vanish. | Pass |
| Orthogonal, idempotent projection | Projection removes gradient energy and a second projection does not change the velocity. | Pass |
| Divergence/gradient work identity | Pressure correction and the continuity equation use mutually consistent discrete operators. | Pass |
| Manufactured pressure jump | Reconstruct an arbitrary specified pressure field through the connected fluid graph; outside pressure 0.2 Pa higher gives positive inward load. | Pass |
| Hydrostatic column | A conservative vertical force is balanced by pressure with no spurious circulation or cross-curtain pressure difference at corresponding heights. | Pass |
| Zero state and uniform scalar | Rest remains rest; constant scalar transport vanishes for a divergence-free velocity. | Pass |
| Scalar conservation | Internal transport changes no net scalar amount in the closed domain. | Pass |
| Convective kinetic-energy identity | Centered conservative MAC convection conserves instantaneous discrete kinetic energy for a divergence-free field. | Pass |
| Diffusion symmetry and dissipation | Random velocity/scalar fields, including near the baffle tips, lose rather than gain energy through diffusion. | Pass |
| Free-slip eigenfunction | The vector Laplacian matches an independently derived discrete sine/cosine eigenvalue in a box without the baffle. | Pass |
| Limited scalar transport | The MUSCL/MC option conserves scalar amount, preserves a constant and does not create new extrema in the tested forward-Euler step at outgoing CFL 0.25. | Pass |
| Smooth limited transport | A strictly monotone manufactured scalar field gives spatial convergence order above 1.7 on three grids in the smooth interior. | Pass |

The manufactured pressure jump is a mathematical test only. It does not prescribe the pressure in the shower calculations. The eigenfunction check tests the smooth box operator; it does not establish an order of pressure convergence at the sharp curtain edges. The centered transport energy identity is semidiscrete; the chosen time integrator still needs stability and refinement checks. Scalar centered transport is not intrinsically positivity-preserving. The limited option improves that property but does not remove the combined transport/diffusion/source timestep restriction. Temperature extrema must be monitored in complete runs.

## Driver and structural interface

`tests/test_driver_qa.py` runs the actual simulation driver with only the droplet source mocked as an analytically prescribed conservative force. The two pressure corrections in SSPRK2 must combine as `0.5*pfirst + psecond`. The test verifies that the saved pressure equals the full force potential, that the manufactured cross-curtain pressure difference is 0.2 Pa, and that air remains at rest. It would fail if only the second pressure correction were reported. This source occurs only in the mathematical test, never in production simulation inputs.

`tests/test_strip_qa.py` checks a nonsymmetric spatial pressure profile applied to three width locations with a time-dependent ramp. The pressure-file interface reproduces direct integration of the strip equation with the same forcing. A separate first-contact test verifies that the saved endpoint is the actual event state and reaches exactly the specified 0.15 m plane. Both tests pass.

The reviewed structural continuation samples nine fixed physical width locations, from 0.15 m to 0.15 m inside the opposite wall. Pressure is interpolated across width to those positions, so grid refinement no longer shifts the probes. Any reported maximum concerns those sampled strips. A separate executed cadence study found less than 0.4% change in the baseline peak displacement between 0.024 s and 0.1 s pressure samples; details are in `numerics_qa_results.md`. No contact occurred in that comparison, so it does not establish contact-time accuracy in other cases. Pressure is extended from the nearest source cell center to the curtain endpoints; the consequences of that convention must diminish under spatial refinement before interpreting endpoint-dominated responses quantitatively.

The saved-output consistency test reconstructs the pressure difference and viscous normal-stress correction independently from the stored final fluid fields, verifies their area averages, and checks the control-case conservation records and impermeable faces. This test caught a truncated combined-control archive. The run was replaced, output saving was made atomic, and all four control archives subsequently passed. There are now sixteen tests authored by the independent numerical QA reviewer across the grid, driver, strip interface and saved-output files; all passed in the completed rerun.

Run the checks with `python -m unittest discover -s tests -p test_grid_qa.py -v` from the phase-1 directory.
