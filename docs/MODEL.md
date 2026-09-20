# The model behind the phase-one calculations

This study asks whether stated, plausible shower inputs can produce inward air loading and centimetre-scale motion in the article's hanging-strip model. It computes water-to-air exchange, air motion, pressure, and a strip's response in that order. No curtain measurements are fitted, and no desired pressure or displacement is supplied to the airflow solver.

The simulations cover the first 12 seconds after the water starts in an initially still, isothermal enclosure. They are transient calculations. The selected inputs are individual plausible values, supported where possible by measurements or modeling precedents; they are not a jointly measured description of one shower. Numerical checks establish whether the implemented equations have been solved adequately for the reported quantities. They do not establish experimental accuracy.

## 1. Geometry, coordinates, and boundaries

The box measures 1.8 m in the x direction, 2.4 m in y, and 2.4 m vertically in z. The curtain is a zero-thickness, impermeable baffle at x = 0.90 m, extending from z = 0.30 m to z = 2.10 m and across the full y width. Its height is therefore H = 1.80 m. The shower occupies the side x < 0.90 m; positive curtain displacement points inward, toward decreasing x.

Air passes around the curtain's top and bottom through 0.30 m gaps. Its vertical ends meet the outer walls. Every solid boundary has zero normal air velocity and free tangential slip. The thermal boundary condition is insulating. The model contains no bather, exhaust fan, open bathroom door, wall-film heat transfer, or exchange with an external reservoir. A clearance plane used in structural calculations is a geometric comparison, not a body in the airflow.

Free slip removes unresolved wall boundary layers; insulation removes unspecified wall temperatures. These are declared boundary assumptions, not claims about actual bathroom walls. The geometry is invariant in y, which permits an efficient pressure solution while the velocity, pressure, temperature, and spray remain three-dimensional. The present solver cannot represent a y-dependent body or finite-width curtain-end openings.

## 2. Baseline inputs and their evidence

| Quantity | Baseline | Status and planned variation |
|---|---:|---|
| Water volume flow Q | 8 L/min | Scenario value near common shower rates. EPA gives 9.46 L/min for conventional 2.5 US gal/min heads and a 7.57 L/min WaterSense limit [1]. Published bathroom experiments used 8 and 10 L/min [2]. Screen 5 and 10 L/min. |
| Representative droplet diameter d | 1.0 mm | Monodisperse modeling assumption. An EPA shower-exposure model used 1 mm, selected through benzene-emission calibration [3]; this was not a direct droplet measurement. TOTO reports using 1.5 mm for a conventional-spray simulation and 0.3 mm for a mist simulation [4]. Screen 0.5 and 1.5 mm. |
| Launch speed | 1.0 m/s | Chosen near-head speed, followed by gravitational acceleration and drag. Experiments show head-dependent speeds and geometry [5]; their measured values are not a jointly compatible specification for this baseline. Screen 0.5 and 3.0 m/s. |
| Injection center | (0.45, 0.35, 2.10) m | Geometry assumption, unchanged during input sensitivity comparisons. |
| Injection radius | 0.05 m | Idealized disk of spray origins; individual nozzle jets and breakup are not resolved. |
| Spray axis | 20° from downward vertical, toward +y | Scenario geometry. Screen 0° and 35°. |
| Cone half angle | 8° | Idealized angular spread, not a measured distribution for a particular head. |
| Ambient temperature T₀ | 295.15 K = 22°C | Chosen initial temperature everywhere. |
| Incoming water temperature | 313.15 K = 40°C | Water is 18 K above the initial air. Published bathroom experiments used water at 35, 38, and 41°C [2]. Screen 35 and 41°C. |
| Air density ρ₀ | 1.2 kg/m³ | Constant reference property. |
| Molecular air viscosity νₐ | 1.5 × 10⁻⁵ m²/s | Used in droplet Reynolds numbers; distinct from the flow mixing coefficient. |
| Effective air viscosity ν_eff | 0.003015 m²/s | Chosen constant mixing closure: molecular value plus 0.003 m²/s. Halve and double the added term. |
| Effective thermal diffusivity α_eff | 0.004307 m²/s | Chosen constant heat-mixing closure, varied with momentum mixing. |
| Curtain mass per area σ | 0.20 kg/m² | Chosen mechanical input; screen 0.10 and 0.30 kg/m². |
| Hem mass per width m_h | 0.05 kg/m | Chosen mechanical input; also evaluate 0 and 0.10 kg/m. |
| Distributed damping c | 0.08 kg/(m² s) | Phenomenological structural damping, not measured for a commercial curtain. |

The choices intentionally preserve uncertainty about showerheads. No source supplies a universal droplet size, launch speed, airflow, or pressure difference. The evidence supports a set of scenarios to examine; it does not supply a fitted benchmark. The experiment definitions and case metadata are the authoritative record of which variations were actually run.

## 3. From falling water to air force

The article begins with the drag force exerted by a droplet on the air. For a spherical droplet with area A_d = πd²/4 and slip velocity **w** = **v** − **u**, this is

$$\mathbf F_{d\to a}=\frac12\rho_0 C_D A_d\lvert\mathbf w\rvert\mathbf w.$$

Dividing the equal and opposite force by the droplet mass ρ_wπd³/6 gives the actual equation integrated for its velocity:

$$\frac{d\mathbf x}{dt}=\mathbf v,\qquad
\frac{d\mathbf v}{dt}=-g\mathbf e_z-\frac{3\rho_0 C_D}{4\rho_wd}\lvert\mathbf w\rvert\mathbf w.$$

The droplet density is ρ_w = 1000 kg/m³. The diameter stays constant. The Schiller–Naumann drag relation supplies the drag coefficient [6]:

$$\mathrm{Re}_d=\frac{\lvert\mathbf w\rvert d}{\nu_a},$$

$$C_D=\frac{24}{\mathrm{Re}_d}\left(1+0.15\mathrm{Re}_d^{0.687}\right)
\quad\text{for }\mathrm{Re}_d\leq1000;\qquad C_D=0.44\quad\text{above }1000.$$

The code evaluates the low-speed acceleration in a form that remains finite when the slip vanishes. Crucially, the droplet Reynolds number uses molecular viscosity. The much larger effective mixing coefficient in the gas equation is not substituted into this correlation.

Each numerical parcel represents a known mass of equal-diameter physical droplets sharing a position and velocity. It is not one enlarged physical droplet. At every air time step Δt, the nozzle quadrature injects N_r parcels with individual represented mass

$$M_j=\frac{\rho_w Q\Delta t}{N_r}.$$

Their positions and directions deterministically cover the prescribed disk and cone. Baseline N_r = 12; the parcel refinement increases this number without changing the injected water mass. Gravity acts during flight, so a launch speed of 1 m/s is not the speed throughout the falling spray.

Gas velocity is interpolated to each parcel. Explicit midpoint integration gives its drag impulse, excluding gravity. The gas receives exactly the negative of that calculated drag impulse. Written for grid weights W_jk summing to one and cell volume V_k, the force-density contribution is

$$\mathbf f_{s,k}=-\frac{1}{V_k\Delta t}\sum_jW_{jk}\,\Delta\mathbf P_{j,\mathrm{drag}}.$$

The staggered velocity components have their own interpolation/deposition weights. Weights do not reach through the impermeable curtain and are normalized over available grid support. Interpolation and deposition use the same weights. Total exchange is therefore conserved to arithmetic precision, independently of whether the predicted airflow is inward or outward.

Droplets leave the calculation on hitting the box or baffle. Their outgoing momentum and sensible energy are recorded separately from gas exchange. Baffle impacts have a separate ledger; their impulse is not applied to the aerodynamic strip calculation. A case with appreciable direct curtain impact therefore requires separate interpretation. No splash, breakup, droplet collision, wall film, or liquid-volume displacement model is included. This is a dilute dispersed-spray approximation.

The scientific reason to include this coupling is established beyond showers: droplet-driven sprays can induce an air current through momentum exchange [7]. The resulting enclosure pressure still has to be solved; entrainment is not implemented as a prescribed low-pressure patch.

## 4. From warm water to gas temperature

The temperature difference in the input table is water temperature minus initial air temperature. The model never sets an 18 K interior-air temperature increase. It calculates sensible heat transferred during each droplet's finite residence time.

For a droplet with internally uniform temperature T_w, a convective heat-transfer coefficient h gives

$$m_dc_{pw}\frac{dT_w}{dt}=-h\pi d^2(T_w-T_a).$$

The Ranz–Marshall relation supplies h [8]:

$$\mathrm{Nu}=\frac{hd}{k_a}=2+0.6\mathrm{Re}_d^{1/2}\mathrm{Pr}^{1/3}.$$

With k_a = 0.026 W/(m K), Pr = 0.71, and c_pw = 4180 J/(kg K), substitution gives the equation used in the code:

$$\frac{dT_w}{dt}=-\frac{6k_a\mathrm{Nu}}{\rho_wc_{pw}d^2}(T_w-T_a).$$

For fixed local gas temperature and heat-transfer coefficient over a substep, the update is exponential. The gas receives the negative of the calculated parcel sensible-energy change. Its temperature source in cell k is

$$S_{T,k}=-\frac{1}{\rho_0c_{pa}V_k\Delta t}
\sum_jW_{jk}\,M_jc_{pw}\Delta T_{w,j},\qquad c_{pa}=1005\ \mathrm{J/(kg\,K)}.$$

There is no evaporation, humidity transport, latent heat, condensation, radiation, or post-impact water heating. The Ranz–Marshall formula is used only for sensible convection; citing its historical association with droplet evaporation does not mean that evaporation has been modeled. The closed, insulating gas domain makes its total sensible heat gain directly comparable with accumulated droplet-to-gas heat transfer.

## 5. The air equations and calculated pressure

The air model is the article's incompressible Boussinesq system, with explicitly chosen effective momentum and heat mixing:

$$\nabla\cdot\mathbf u=0,$$

$$\rho_0\left[\frac{\partial\mathbf u}{\partial t}+
(\mathbf u\cdot\nabla)\mathbf u\right]
=-\nabla\pi+\rho_0\nu_{\mathrm{eff}}\nabla^2\mathbf u
+\mathbf f_s+\rho_0g\beta\theta\mathbf e_z,$$

$$\frac{\partial\theta}{\partial t}+\mathbf u\cdot\nabla\theta
=\alpha_{\mathrm{eff}}\nabla^2\theta+S_T.$$

Here θ = T − T₀, β = 1/T₀, and π is pressure after subtracting the common reference hydrostatic column. Density changes are retained only in the thermal buoyancy term. The approximation requires temperature-related density changes to remain small relative to the reference density; extrema of βθ are a useful case diagnostic. Reference properties are held constant.

The effective coefficients smooth unresolved motion. This is neither a direct simulation at molecular viscosity nor a calibrated turbulence model. Halving and doubling the added mixing tests how strongly the outcomes depend on that assumption.

Pressure is found by projecting provisional staggered-grid velocities onto a discrete divergence-free field with blocked curtain and wall faces. One pressure gauge is shared across the connected air domain. There is no independently chosen inside pressure, outside pressure, Bernoulli constant, vortex-core pressure, or neutral height.

This connects the earlier analytic explanations without replacing them. Bernoulli's dynamic-pressure scale remains a scale, not a loading law. The vortex relation dπ/dr = ρ₀v_θ²/r explains radial pressure support in an ideal circulation, but no such vortex is imposed here. The article's hydrostatic two-column relation follows in a nearly hydrostatic thermal limit; the present openings and transient airflow determine the pressure distribution instead of prescribing a neutral pressure level. Schmidt's shower calculation is evidence that spray-driven circulation is a possible mechanism, rather than a target field copied into this calculation [9].

For reference, those limiting comparisons are

$$p_{\mathrm{dyn}}=\frac12\rho_0U^2,\qquad
\pi(a)-\pi(0)=\frac12\rho_0\Omega^2a^2$$

for a pressure scale and an ideal solid-body vortex core, and

$$\Delta p_b(z)=g(\rho_{\mathrm{out}}-\rho_{\mathrm{in}})(z_n-z)
\simeq\rho_0g\beta\Delta T_a(z_n-z)$$

for two approximately uniform-density hydrostatic columns whose pressures match at height z_n. In this last expression ΔT_a is an air-temperature difference. None of U, Ω, or z_n is selected to generate the simulated curtain load.

The article's regime estimates remain useful when constructed from stated scales:

$$\mathrm{Re}=\frac{UL}{\nu_a},\qquad
\mathrm{Ri}=\frac{g\beta\Delta T_a L}{U^2}.$$

Use a reported representative calculated air speed and air-temperature difference for these diagnostics, rather than equating water flow with gas speed or water temperature with air temperature. A physical Reynolds number based on ν_a and a numerical mixing ratio based on ν_eff describe different things; the larger mixing coefficient does not change the molecular Reynolds number of the physical scenario.

Because the momentum and temperature equations are coupled, their combined outcome need not equal the sum of two isolated pressure fields.

## 6. Force across the curtain

At corresponding heights on the two sides, the inward pressure load is

$$q_p(y,z,t)=\pi_{\mathrm{out}}-\pi_{\mathrm{in}}.$$

The subtracted reference hydrostatic pressures cancel at equal z. The solver evaluates the two cell pressures adjacent to the blocked face, with outside at larger x. Positive q_p pushes the curtain inward, toward decreasing x. The pressure force over the curtain is the article's area integral:

$$F_p(t)=\int_A q_p\,dA.$$

The modeled normal viscous-stress contribution, using the same effective viscosity as the momentum equation, is

$$q_\nu=2\rho_0\nu_{\mathrm{eff}}
\left[(\partial_xu_x)_{\mathrm{in}}-(\partial_xu_x)_{\mathrm{out}}\right],
\qquad q_{\mathrm{total}}=q_p+q_\nu.$$

The saved arrays `pressure_load` and `viscous_load` keep these contributions separate. The default `strip_response` applies `pressure_load`; setting `include_viscous=True` adds the recorded normal-stress correction. Both continuations are calculated for the baseline controls. Pressure-only structural results require the correction to be small for the reported observable, or a separately identified total-stress continuation. A spatial mean of pressure is insufficient when loading changes sign with height or differs along the width.

## 7. From computed load to a hanging strip

Let s = 2.10 m − z measure distance downward from the rod. Nine fixed physical width locations, from y = 0.15 to 2.25 m, receive linearly interpolated saved spatial and temporal pressure distributions. Keeping these physical locations fixed prevents sample position from changing during grid refinement. No uniform pressure is fitted to reproduce a desired excursion.

The article's gravitational tension per unit width is retained:

$$\mathcal T(s)=g[\sigma(H-s)+m_h].$$

Its small-slope dynamic equation is

$$\sigma\frac{\partial^2Y}{\partial t^2}
+c\frac{\partial Y}{\partial t}
=\frac{\partial}{\partial s}\left[\mathcal T(s)\frac{\partial Y}{\partial s}\right]+q(s,t).$$

The top satisfies Y(0,t) = 0. The hem's horizontal equation is

$$m_h\frac{\partial^2Y(H,t)}{\partial t^2}
=-\mathcal T(H)\frac{\partial Y(H,t)}{\partial s}.$$

The strip begins at rest. A finite-element discretization uses the exact linearly varying gravitational tension in each element, lumped distributed mass, and an added endpoint hem mass. Distributed damping is proportional to local strip length. Adjacent width strips have no transverse coupling, bending rigidity, wrinkle model, or shared tension redistribution.

The numerical equilibrium is checked against the article's analytic result for a uniform static pressure q₀:

$$Y(H)=\frac{q_0}{\sigma g}
\left[H-\frac{m_h}{\sigma}\ln\left(1+\frac{\sigma H}{m_h}\right)\right]
\quad (m_h>0).$$

For zero hem mass the continuous limit is Y(H) = q₀H/(σg). Thus the final simulation retains the same pressure-to-deflection mechanics that produced the article's illustrative 18 cm and 11 cm estimates. Those earlier estimates were uniform, static, chosen-load examples; a spatially varying transient load need not reproduce their numbers.

The dynamic integrator stops at the first computed crossing of a specified clearance plane, or when a maximum nodal slope reaches 0.3. These events mark limits of the calculation. They do not simulate contact with a body, capillary attachment, large rotations, or motion after touching. The static contact ratio Y(H)/d remains useful for a flat test plane, but it is not a general criterion for a moving, width-dependent curtain near a human body.

Two distinct load histories are retained. The raw startup continuation uses the saved 0–12 second pressure history. A separate release experiment first calculates the spatially resolved mean pressure

$$\bar q(y,s)=\frac{1}{2\ \mathrm{s}}\int_{10\ \mathrm{s}}^{12\ \mathrm{s}}q_p(y,s,t)\,dt,$$

using trapezoidal time integration, then holds that distribution constant while an initially straight strip is released from rest. Its six-second structural clock measures time since release under the computed mean load. It is distinct from the airflow startup clock. The load is not scaled, and the release problem uses the same dynamic equation and boundary conditions. Static responses use the same mean load. Numerical acceptance of selected mean-load observables does not repair the separate failed mesh comparison for spray-driven raw startup peaks; both comparisons remain in the QA record.

## 8. What one-way coupling establishes

The air boundary remains flat and fixed while its computed load drives the strip. The result therefore answers a precise conditional question: how does this gravitationally restrained strip respond to the load calculated in the stated enclosure? It also shows the initial direction of the aerodynamic tendency. It does not by itself compute the pressure after the strip changes the air passages.

For excursions approaching 0.10 m, a useful minimum geometry screen is to rerun the same flow with the entire flat baffle at x = 0.85 and 0.80 m on a mesh whose x spacing is 0.05 m, alongside x = 0.90 m. Water inputs, wall conditions, and observation time must remain fixed. This directly tests dependence on shower-to-curtain distance and compartment width. It moves the rod as well, so it is a translated-plane sensitivity, not the deformed shape of a top-supported curtain. A result that changes materially under these shifts must retain that geometry dependence in its interpretation.

A fully coupled final-position prediction would require a moving boundary with the supported curtain shape. That extension is unnecessary to make the present conditional demonstration authentic, provided figures and prose identify which boundary was used and avoid claiming that the final air and curtain shapes were solved together.

## 9. Controls and numerical evidence

Four controls enable neither gas exchange, momentum feedback alone, heat feedback alone, or both. Water still experiences drag and sensible cooling in the diagnostic controls; suppressed gas transfer is explicitly recorded. These are computational mechanism switches, not four independently realizable shower devices. The off case should leave the gas exactly at rest and its temperature unchanged.

The implementation uses a conservative MAC grid, centered momentum fluxes, a sparse pressure solve after a cosine transform in the y direction, and a limited upwind scalar flux. Air transport uses SSPRK2. Parcel motion uses a midpoint step with frozen local gas data; gas–parcel splitting is first order overall. A wall intersection is computed along the midpoint quadratic trajectory, and the particle substep ends at that intersection. Source refinement must therefore test the complete calculation rather than infer accuracy from the air integrator's order alone.

The baseline mesh is 24 × 32 × 32 with Δt = 0.004 s and saved fields every 0.10 s. Medium and fine meshes keep physical geometry fixed and aligned. Independent QA compares pressure profiles and structural observables under grid, time-step, parcel-number, and structural refinement. Near-zero quantities use absolute differences as well as relative changes. A small divergence or exact exchange ledger is necessary for consistency but cannot replace these observable-level comparisons.

Checks also cover pressure sign and gauge, blocked-face leakage, gas/liquid momentum exchange, mass and sensible-energy ledgers, scalar extrema, analytic strip equilibrium, and first-event behavior. Sensitivity to damping is needed if transient peaks or first-crossing times are emphasized. Figures must be generated from saved computed fields. Saved water-parcel point clouds are representative snapshots; their selected entries do not retain particle identity from frame to frame, so they must not be joined into apparent persistent trajectories.

## References and evidence status

1. U.S. EPA. [Showerheads — WaterSense](https://www.epa.gov/watersense/showerheads). Primary program specification for flow rates; not a droplet or pressure dataset.
2. Zhang, D., et al. (2025). [Measuring Dynamic Thermal Sensation in a Residential Bathroom for Water-Efficient Showering](https://ira.lib.polyu.edu.hk/bitstream/10397/116396/1/Zhang_Measuring_Dynamic_Thermal.pdf). CIB W062. Primary bathroom experiments; water-flow and water-temperature settings inspected in the full paper.
3. U.S. EPA. [Inhalation Exposure to Tap Water Through Showering: Literature and Model Review, Appendix C](https://archive.epa.gov/epawaste/hazard/web/pdf/appendc.pdf). Primary agency model review. Its 1 mm diameter is a modeling choice calibrated to benzene emissions, not a measured distribution used to fit this study.
4. TOTO (2025). [The Surprising Relationship Between the Fugaku Supercomputer and “Bathrooms” — Part 2](https://note.jp.toto.com/n/n7e7efebf8899?hl=en). First-party engineering account; stated simulated droplet diameters are modeling precedents.
5. Chan, W.-K., et al. (2017). [An Experimental Study of Shower Spray Properties and Shower Comfort](https://doi.org/10.2991/icsd-16.2017.79). [Full paper](https://www.atlantis-press.com/article/25871384.pdf). Primary experiments; near-head speed and spread vary between heads. No nozzle-diameter value is treated as a measured droplet diameter.
6. OpenFOAM Foundation. [Schiller–Naumann implementation](https://cpp.openfoam.org/v13/SchillerNaumann_8C_source.html). Official source inspected to verify the stated correlation and high-Reynolds-number branch; not experimental validation of this shower model.
7. Ghosh, S., and Hunt, J. C. R. (1994). [Induced air velocity within droplet driven sprays](https://doi.org/10.1098/rspa.1994.0007). Proceedings of the Royal Society A, 444, 105–127. Primary research on spray-induced air motion; no quantitative shower benchmark has been extracted here.
8. OpenFOAM Foundation. [Ranz–Marshall parcel heat-transfer implementation](https://cpp.openfoam.org/v12/src_2lagrangian_2parcel_2submodels_2Thermodynamic_2HeatTransferModel_2RanzMarshall_2RanzMarshall_8C_source.html). Official source inspected to verify Nu = 2 + 0.6√Re Pr^(1/3). The original relation is associated with Ranz and Marshall's 1952 work; this study verifies its implemented form against the official source.
9. Schmidt, D. (2001). [Why Does the Shower Curtain Move Toward the Water?](https://www.scientificamerican.com/article/why-does-the-shower-curta/). First-person account of the computational shower-curtain investigation, supporting a possible circulation mechanism.
