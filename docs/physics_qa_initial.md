# Independent physics QA of the proposed phase-one study

Review date: 15 September 2026. This report reviews the previously delivered equations and code and proposes a physically connected calculation. It does not certify results from the replacement solver, which had not been completed when this report was written. The original article and repository have not been edited.

## Scientific target

The target is a conditional demonstration: within an explicitly defined model, supported shower inputs and stated geometric assumptions can produce inward curtain motion. No fit to curtain measurements is needed. The calculation must retain the chain already introduced in the article:

1. Water droplets exchange momentum with the air through relative-velocity drag.
2. The air momentum and incompressibility equations determine velocity and pressure throughout the enclosure.
3. The pressure difference at corresponding positions on the two curtain faces drives the hanging-strip equation.
4. The computed shape determines displacement and possible first contact, subject to the mechanics approximation.

The analytic circular-vortex example and thermal-column calculation remain explanatory comparisons. Their pressure profiles must not be superimposed onto the computed flow. A rotating velocity field does not by itself establish a particular curtain pressure, and a heated enclosure need not have lower pressure at every height.

## What the previous implementation does

The signs in the previous coupling are internally consistent. Positive curtain displacement moves the surface in the negative x direction; the positive x force on air is consequently a positive inward force on the curtain. No simple sign reversal is justified by its outward spray result.

The more important issue is that the numerical curtain load is not the article's pressure difference. The old code uses a finite-slip velocity penalty, with sheet drag 12 kg/(m² s), spread over a Gaussian width of 0.08 m. The separately reported pressure difference samples points 0.16 m away on each side. This is a force-bearing permeable regularization, not a thin impermeable sheet. Its pressure and resistance parameters need their own sensitivity study; it also weakens the direct connection to the earlier pressure-loaded strip.

The spray is a prescribed downward acceleration, not a droplet ensemble. Hence changing its amplitude cannot be identified with a specified water flow rate. The constant mixing viscosity is about 200 times molecular air viscosity; it is a chosen closure. Six seconds of evolution does not establish stationary room circulation. Three-second grid comparisons do not certify later-time predictions.

The original geometry permits air around the hem and both curtain ends, with a very shallow rim. A downward jet can drive a floor return current and raise pressure at the lower curtain. This is a physically possible interpretation of the outward load, not a demonstrated diagnosis. The replacement model should distinguish this geometry effect from numerical error through controlled variations.

## Recommended replacement and its checks

Use a fixed, impermeable baffle on actual grid faces for the first airflow stage. Solve pressure with the same zero-flux constraints as the velocity projection. Extract pressure at its two faces using a common gauge. The total normal traction includes viscous normal stress where it is retained; if pressure alone drives the strip, state that approximation and evaluate whether the viscous correction is small.

Use Lagrangian droplets or a deterministic quadrature of trajectories. Specify a volumetric liquid flow Q and convert it to mass flow rho_w Q. Each trajectory carries a represented mass flux or a parcel multiplicity. Do not mistake a quadrature ray for one physical droplet, and do not count each time sample as newly injected water.

For a spherical droplet with diameter d,

$$m_d\dot{\mathbf v}_d=m_d\mathbf g-\frac12\rho_a C_D A_d|\mathbf v_d-\mathbf u|(\mathbf v_d-\mathbf u),\qquad \dot{\mathbf x}_d=\mathbf v_d.$$

The gas receives the opposite drag force, deposited conservatively. Gravity acting on the water must not be deposited independently into the air: only the drag transfers it. Droplets hitting a floor/body should leave the airborne population. Their remaining impact momentum belongs to that solid/water film, not to the gas. Direct droplet impact on the curtain should be excluded or explicitly counted as a different load.

A useful drag closure is the usual Schiller–Naumann spherical-particle expression, based on the **molecular** gas viscosity in the droplet Reynolds number:

$$\mathrm{Re}_d=\rho_a d|\mathbf v_d-\mathbf u|/\mu_a,\quad C_D=24(1+0.15\mathrm{Re}_d^{0.687})/\mathrm{Re}_d\;(\mathrm{Re}_d<1000),\quad C_D=0.44\;(\mathrm{Re}_d\ge1000).$$

The branch formula is independently visible in the [OpenFOAM Foundation implementation](https://cpp.openfoam.org/v13/SchillerNaumann_8C_source.html). This establishes the implemented correlation, not its empirical accuracy for arbitrary deforming droplets. Record Reynolds and Weber numbers along the supplied trajectories. Approximately spherical droplets are a stated closure; breakup, collisions and shape-dependent drag remain excluded unless implemented.

The mass represented by trajectories, air/particle momentum exchange, liquid exit momentum, and gas/solid pressure reactions should be recorded separately. If trajectories are solved in a frozen gas field and iterated, report that quasi-steady procedure and the iteration residual; do not label it time-resolved two-way particle tracking.

The baffle must have a defined top opening, lower passage and end conditions. A baseline with sealed ends is a legitimate geometry, but it is a geometry choice, not a universal shower. At least one end-gap variation is needed before generalizing. A large lower opening can change the pressure near the hem. Geometry changes should be specified before looking at the resulting deflection, then reported whether they help or reduce inward movement.

Finally, feed the computed spatial pressure into the existing hanging-strip model. Report whether a displayed curtain shape is a static response to a fixed-baffle load, a transient response to stored loads, or a simultaneously coupled result. For large predicted shifts, compare pressure after a geometric perturbation before claiming that fixed-baffle loading represents the deformed curtain.

## Parameter evidence

The table separates direct measurements, manufacturer modeling practice and proposed scenario values. The entries do not form a jointly measured shower: combining them creates an explicitly hypothetical configuration.

| Quantity | Evidence checked | Recommended use and limit |
|---|---|---|
| Liquid flow | EPA gives 2.5 US gpm for standard showerheads and at most 2.0 US gpm for WaterSense products, equivalent to 9.46 and 7.57 L/min. Zhang et al. directly tested 8 and 10 L/min. | 6, 8, 10 L/min is a useful study range. The 6 L/min endpoint is an efficiency scenario; 8 and 10 are directly represented in the cited experiment. |
| Near-head speed | Chan et al. table I reports 0.18–0.78 m/s at 20±5 mm below seven heads, at 1 bar. The indexed accepted manuscript of Estrada-Perez et al. reports speeds up to 5 m/s in its low-flow head and up to 3 m/s in its high-flow head. | A chosen 3 m/s case is consistent with the latter indexed evidence. Include slower inputs. These are local speeds for different heads, not interchangeable population averages. Full-text numerical verification of the Estrada-Perez manuscript remains unavailable in this review. |
| Droplet diameter | TOTO's engineering interview states model diameters of 1.5 mm for a conventional shower and 300 µm for a mist shower. | 0.5, 1.0, 1.5 mm can be declared representative spherical-droplet scenarios within these two technology scales. They are not a measured diameter distribution. A 0.3 mm case should be identified with fine mist and warrants evaporation sensitivity. |
| Full spray spread angle | Chan et al. table I gives 2°, 11°, 40°, 17°, 11°, 13°, 9°. | Full cone angles around 10–20° are supported examples; distinguish full cone angle, half angle and nozzle-axis tilt. A 20° axis tilt is a chosen installation angle, not the measured spread angle. |
| Water temperature | Zhang et al. tested 35, 38 and 41°C with both 8 and 10 L/min. | These are suitable hot-water inputs if a droplet heat-transfer model is used. They must not be substituted for gas temperature. |
| Room dimensions | Zhang et al. used 2.0×2.2×2.4 m, with a ventilation fan. | A meter-scale room of comparable size is supported. A closed room is a deliberate control; it does not reproduce their ventilated experiment. |
| Interior–exterior gas-temperature difference | No directly measured across-curtain difference was found in this review. Zhang et al. report a small initial room-air increase, then little temporal change. | Values such as 2, 5 and 8 K remain chosen warm-enclosure scenarios. Do not cite the water-temperature study as a measurement of these differences. Compute gas temperatures from a heat source, or explicitly initialize a warm enclosure. |
| Air mixing viscosity | No measurement or validated shower closure supports a constant 0.003 m²/s in the evidence reviewed. | Treat it as model uncertainty. Use multiple fixed mixing coefficients and show their effect. Do not call it air's molecular viscosity or claim DNS. |
| Curtain and hem mass | Earlier illustrative model uses sigma=0.20 kg/m² and hem mass0.10 kg/m. These are input choices, not curtain measurements. | Retain the baseline to preserve the article's connection, vary light/heavy cases, and label the assumed mass values. |

### Direct source records

**EPA.** [Showerheads](https://www.epa.gov/watersense/showerheads). Full page accessed. Supports flow-rate examples and distinction between conventional and WaterSense showerheads. It supplies no droplet distribution, velocity or curtain-force data.

**Chan, W.-K., Wong, L.-T., Zhou, Y., and Mui, K.-W. (2017).** [An Experimental Study of Shower Spray Properties and Shower Comfort](https://www.atlantis-press.com/article/25871384.pdf), DOI [10.2991/icsd-16.2017.79](https://doi.org/10.2991/icsd-16.2017.79). Full three-page PDF downloaded and table I inspected as a rendered page. It studies seven heads. Table I also gives head diameters45–150mm and nozzle diameters0.5–3mm; nozzle size is not droplet size. Its unusually low near-head velocities and larger impact forces should not be combined as if they constitute a verified momentum budget. No fitted correction has been invented.

**Estrada-Perez, C. E., Kinney, K. A., Maestre, J. P., Hassan, Y. A., and King, M. D. (2018).** [Droplet distribution and airborne bacteria in an experimental shower unit](https://doi.org/10.1016/j.watres.2017.11.039), Water Research130,47–57. The [publisher's accepted-manuscript entry](https://www.sciencedirect.com/science/article/am/pii/S0043135417309557) is indexed with the3/5m/s comparison, but a full-text fetch returned403. The abstract supports higher droplet velocities from the particular low-flow head. Respiratory aerosol measurements in this work must not be substituted for the mass-carrying millimeter spray.

**TOTO (31 January 2025).** [The Surprising Relationship Between the Fugaku Supercomputer and “Bathrooms”—TOTO's Unique Simulation Technology, Part2](https://note.jp.toto.com/n/n7e7efebf8899?hl=en). Full manufacturer engineering interview accessed. Its stated1.5mm/300µm diameters are useful disclosed model inputs; the page does not supply a statistical distribution of household shower droplets. No claims about the manufacturer's numerical accuracy are needed for this study.

**Zhang, D., Wong, L.-T., Lam, W.-K., and Mui, K.-W. (2025).** [Measuring Dynamic Thermal Sensation in a Residential Bathroom for Water-Efficient Showering](https://ira.lib.polyu.edu.hk/bitstream/10397/116396/1/Zhang_Measuring_Dynamic_Thermal.pdf), CIBW062 symposium, institutional accepted version. Full PDF accessed. Table1 supports the six combinations of water temperature35/38/41°C and flow8/10L/min. The experiment used18 people in the stated ventilated room. It does not measure pressure or curtain motion, nor establish a curtain-side thermal contrast.

**Schmidt, D. (2001).** [Why Does the Shower Curtain Move Toward the Water?](https://www.scientificamerican.com/article/why-does-the-shower-curta/). Full first-person account accessed. Reports a50,000-cell spray calculation spanning30s, including droplet breakup/deformation, and a vortex with axis perpendicular to the curtain. It supports mechanism plausibility, not a complete reproducible benchmark for our solver. Its reported force is weak and its curtain response depends on low curtain resistance.

**Ghosh, S., and Hunt, J. C. R. (1994).** [Induced air velocity within droplet driven sprays](https://doi.org/10.1098/rspa.1994.0007), Proceedings A444,105–127. Publisher bibliographic entry located; no full-text quantitative benchmark extracted in this review. This is the already-cited theoretical and experimental foundation for spray-induced air motion, not a supplied bathroom dataset.

## Thermal closure

A warm-enclosure initial condition is an acceptable controlled buoyancy experiment. Its simulation clock begins with already-warm air. If a warm region is maintained, quantify the heat source in watts and explain how it acts. A spatially imposed warm profile is not a prediction of shower warm-up.

The closer connection to water temperature uses sensible heat exchange for each droplet, with a standard sphere heat-transfer correlation. For example,

$$m_dc_w\dot T_d=-h_dA_{d,\mathrm{surface}}(T_d-T_a),\qquad h_d=k_a\mathrm{Nu}_d/d.$$

The gas receives the opposite thermal power. An established Ranz–Marshall closure uses Nu=2+0.6Re_d^(1/2)Pr^(1/3); the [OpenFOAM class documentation](https://api.openfoam.com/2606/classFoam_1_1RanzMarshall.html) was located through the official index, but its complete page was inaccessible. Use a verified implementation and state the empirical closure's range before adopting it.

The available sensible-heat budget is bounded by rho_w Q c_w(T_water,in−T_reference). Gas heating cannot exceed the water's loss of sensible enthalpy without another source. Surface area in heat transfer is pi d²; the projected area in drag is pi d²/4. These must not be confused.

Droplet sensible heat alone omits evaporation, latent cooling and humidity-related buoyancy. This can serve as a controlled model, but should be identified as such. Moisture is especially consequential for fine droplets. A model that includes heating without evaporation cannot claim to reconstruct the complete thermal field of an actual hot shower.

## Acceptance conditions for the first-phase result

The source values and scenario ranges should be recorded before publication-example selection. Show all mechanism controls with the same geometry and numerical method. Report pressure load by height as well as a mean; the strip's displacement depends on load position. Keep outward or near-zero outcomes in the parameter study.

Establish conservation of momentum exchange, numerical convergence of the relevant pressure/displacement metrics, and the validity range of the small-slope mechanics. A 0.15 m contact clearance can remain a specified test plane; it should not be drawn as the body geometry unless it actually matches that geometry. Air trajectories, droplets and curtain motion must all be derived from their identified calculated fields, with no rescaling of displacement to make the animation more dramatic.

For interpretation, distinguish a result that is stable under grid refinement from one that is insensitive to uncertain physical closure. Both matter, but they answer different questions. The replacement model can demonstrate a plausible mechanism without experimental fitting; it cannot establish that every shower, every curtain or every operating point behaves that way.
