# Phase-one numerical study

This study addresses the quantitative continuation of the existing shower-curtain article. The article and its previously delivered package are unchanged. These are model predictions under declared conditions, without fitting to curtain measurements.

## Question and connected calculations

Can a plausible water spray, with and without sensible heating, establish an inward load and appreciable displacement in the hanging-strip model? Newton's droplet equation supplies the air force; the incompressible momentum equation supplies pressure; pressures at the two faces of an impermeable curtain supply the strip load. Vortex and hydrostatic examples remain analytic comparisons, not prescribed pressure distributions.

The original porous curtain approximation is replaced by an impermeable thin baffle. The room is a 1.8 × 2.4 × 2.4 m box, separated at x = 0.9 m by a curtain between z = 0.3 and 2.1 m. Its vertical ends meet the room walls; air exchanges through the upper and lower gaps. This is a deliberately simple enclosure, with no bather or ventilation. All physical dimensions remain constant in a grid study.

The airflow is first calculated with the curtain fixed. Applying the calculated load to a movable strip is a one-way continuation. It can estimate the initial tendency and a prescribed-load response. A large displacement is not automatically a self-consistent final position because the airflow calculation has not moved its boundary.

## Inputs and variation

Initial baseline: water flow 8 L/min; representative monodisperse diameter 1 mm; initial speed 1 m/s; head centered at (0.45,0.35,2.1) m; 0.05 m head radius; downward spray axis tilted 20 degrees toward +y; cone half angle 8 degrees; water 18 K warmer than 295.15 K ambient in heated cases. Sources and the distinction between observations, modeling precedents and scenario assumptions are recorded separately.

The four baseline comparisons keep geometry and water inputs fixed while enabling neither gas momentum nor gas heat exchange, momentum alone, heat alone, or both. Suppressing one exchange is a mechanism-isolation calculation, not a physically realizable independent shower.

Before inspecting outcomes, select one-at-a-time variations: flow 5 and 10 L/min; diameter 0.5 and 1.5 mm; launch speed 0.5 and 3 m/s; spray tilt 0 and 35 degrees; water temperature rises 13 and 19 K (35 and 41 Celsius at the chosen ambient); hem mass 0, 0.05 and 0.10 kg/m; curtain mass 0.10, 0.20 and 0.30 kg/m². Geometry changes will be separately identified. The study is a sensitivity screen, not a probability sample or an exhaustive Cartesian product of inputs.

An effective momentum diffusivity 0.003015 m²/s and thermal diffusivity 0.004307 m²/s initially represent unresolved air mixing. They are chosen model coefficients, not the molecular viscosity or measured shower turbulence. Halving and doubling the added mixing tests dependence on this closure. No change in mixing is made to force an inward answer.

## Numerical checks and reporting

The pressure solver must maintain exact zero velocity on blocked faces and small divergence in every fluid cell. The independent operator suite checks pressure sign, pressure reconstruction, work identities, convection energy, diffusion dissipation and scalar conservation. Parcel tests check gas/liquid momentum and sensible heat exchange, injection mass, and a drag benchmark. The hanging-strip solution is checked against the article's exact uniform-pressure formula.

Grid, time-step and parcel-number studies compare pressure-load profiles and the resulting displacement, with the same physical inputs and observation interval. A relative change below 5% is the intended screen for representative pressure/displacement quantities; near-zero observables need an absolute difference as well. This screen is not experimental validation or a confidence interval. Failed screens remain visible and prevent quantitative acceptance of the affected result.

Record both pressure load and the normal viscous-stress correction, rather than assuming their ratio. Record temperature extrema and total heat gain, which must follow the droplet sensible energy transfer. Structural integrations stop at first contact with the specified plane or a maximum slope of 0.3; they do not simulate wet adhesion or post-contact motion.

Only saved calculated fields will be animated. Every panel will identify the physical time, geometry and switches, and distinguish the fixed air boundary from the movable strip response. Representative cases are chosen after the comparison and QA; other outcomes remain in the results table.
