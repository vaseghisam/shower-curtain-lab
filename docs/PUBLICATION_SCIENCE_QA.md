# Publication scientific and citation audit

Reconstructed audit: 17 September 2026. This record restores the independent review after the workspace was reconstructed. Primary-source inspection was performed on 15 September and is retained in the conversation record. Restored code, model documentation, saved metadata and numerical summaries were checked again on 17 September. No CFD calculations were rerun.

## Status and scope

The restored implementation supplies the intended sequence: droplet drag and sensible heat exchange drive three-dimensional air motion; the pressure calculation enforces incompressibility and the declared boundaries; the resulting spatial pressure difference loads the same gravitationally tensioned strip equation developed analytically in the article. The accepted observables support a conditional demonstration of centimetre-scale inward motion. They do not establish experimental accuracy or the motion of a curtain around a bather.

The reconstructed manuscript has been read in full, the requested clarifications have been checked, and the final text passes this independent scientific and citation review within the stated scope. Its final SHA is recorded below. Numerical verification remains distinct from experimental validation.

## Restored implementation and evidence

Reviewed `RESULTS.md`, `docs/MODEL.md`, `docs/numerics_qa_final.md`, `docs/numerics_qa_results.json`, the fine-run JSON metadata, `data/results_summary.json`, `data/release_summary.json`, and the relevant portions of `curtainflow/droplets.py`, `simulation.py`, `averaging.py` and `release.py`.

| Link in the argument | Implementation and interpretation |
| --- | --- |
| Droplets to air momentum | Physical droplets use local slip velocity, molecular air viscosity and Schiller–Naumann drag. Parcels represent water mass; they are not enlarged physical drops. The gas receives the negative computed droplet drag impulse. |
| Droplets to air temperature | Ranz–Marshall sensible heat transfer cools the droplets and heats the gas. Incoming water is 40°C and initial air 22°C. The gas is not assigned an 18 K temperature rise. |
| Air motion to pressure | All three velocity components evolve in three dimensions. Projection computes reduced pressure with a shared gauge across the connected air domain. No desired pressure difference or sign is prescribed. |
| Pressure to mechanics | The inward load is outside-minus-inside pressure at corresponding heights. Its spatial dependence is retained and applied to the article’s tension law, T(s) = g[σ(H−s)+mh]. |
| Mean-load equilibrium | Pressure is averaged by trapezoidal integration over exactly 10–12 s, a selected transient interval. Static equilibrium under that mean load is not a claim that the airflow reached steady state. |
| Mean-load release | An initially held flat strip is released from rest under the computed mean spatial load, which is then held constant. Its six-second structural clock differs from the airflow’s twelve-second startup clock. |
| Geometry | Airflow uses a fixed, flat, impermeable curtain, sealed vertical ends, and 0.30 m gaps above and below. The room is 1.8 × 2.4 × 2.4 m. Outer walls are free-slip and insulating. |
| Limits | There is no bather, external ventilation, evaporation, humidity transport, latent heat, wet adhesion, moving air boundary, transverse strip coupling or resolved folding. |
| Computational controls | Momentum-only suppresses gas heat input; the initially uniform gas temperature then stays unchanged and thermal buoyancy is absent. Heat-only suppresses gas momentum feedback. These are equation-level controls, not separate physically realizable showers. |

All three restored fine-run metadata files specify 48 × 64 × 64 cells, 12 parcels per injection step, νeff = 0.003015 m²/s and αeff = 0.004307 m²/s. Each records zero normal boundary leakage and zero droplet mass impacting the curtain. The effective mixing coefficients are scenario assumptions, not molecular properties or a calibrated turbulence closure.

Droplet buoyancy is omitted from the particle equation. Its magnitude relative to droplet weight is ρair/ρwater = 1.2/1000 = 0.0012 for the stated properties, so this omission does not alter the intended accuracy of the demonstration.

## Numerical statements checked

The baseline curtain has σ = 0.20 kg/m² and an added hem mass mh = 0.05 kg per metre of width. The following quantities agree with the restored numerical summaries after rounding.

| Fine-grid quantity | Spray momentum | Sensible heating | Both |
| --- | ---: | ---: | ---: |
| Mean inward pressure, Pa | 0.0270 | 0.0188 | 0.0444 |
| Width-mean static hem displacement, cm | 1.82 | 1.33 | 3.21 |
| Largest static displacement at nine fixed probes, cm | 2.39 | 1.67 | 3.97 |
| Largest mean-load release excursion at those probes, cm | 4.62 | 3.33 | 7.77 |
| Width-mean static hem displacement, σ = 0.10 kg/m² and no hem, cm | 5.20 | 3.78 | 8.95 |
| Largest static displacement of that light curtain at fixed probes, cm | 7.45 | 4.77 | 11.69 |

The full-width discrete maximum and the maximum among nine fixed probes differ slightly. The article must identify the sampled maximum when reporting the values above. The light-sheet slopes remain below the declared small-slope limit with margin; that fact does not make the detailed maximum-slope values equally converged.

| Medium-to-fine relative change, using the finer value as denominator | Spray | Heating | Both |
| --- | ---: | ---: | ---: |
| Mean pressure | 3.78% | 0.26% | 4.63% |
| Mean static hem displacement | 1.28% | 0.95% | 1.36% |
| Largest static displacement at fixed probes | 2.08% | 0.91% | 3.41% |
| Largest mean-load release excursion | 3.47% | 0.80% | 2.77% |
| Largest raw startup excursion | 20.60% | 1.05% | 22.12% |
| Full mean-pressure map, relative L² difference | 13.31% | 1.89% | 11.10% |

The first four measures pass a 5% sensitivity screen. The full spray pressure maps and raw spray-driven startup peaks do not. Passing the selected comparison is neither a rigorous numerical error bound nor 5% physical accuracy.

The grid comparisons hold the nozzle sampling at 12 parcels per injection step. A separate 12→24→48 study was performed on the screening grid. Its last comparison passes for selected displacement measures, but the 12→24 mean static response changes about 5.6%. No joint finest-grid/highest-parcel study has been completed. One-at-a-time parameter-screen cases were not individually mesh-refined. These limits must remain explicit.

The mean-load release is a separate experiment. Averaging the input does not repair the failed mesh comparison for raw startup peaks. The article can report the accepted release observables only with their held-load definition and independent clock.

The additional normal-viscous-stress calculation on the screening grid changes mean static response by approximately 2–4%. It supports the pressure-led approximation for these response measures at that resolution. Geometry translation checks are spray-only and move the entire flat curtain and rod; they do not establish the deformed geometry or the combined heated case.

## Independent arithmetic and equations

The governing derivations checked are: positive inward pressure sign; circular-flow radial balance; solid-body core pressure integral; two-column hydrostatic pressure difference about a neutral level; gravitational tension; static strip load integral; weighted uniform-load formula and zero-hem limit; contact ratio; dynamic strip and inertial hem boundary equations.

| Analytic example | Recomputed value | Accepted article rounding |
| --- | ---: | ---: |
| Unweighted displacement, Δp = 0.20 Pa, H = 1.8 m, σ = 0.20 kg/m² | 0.183486 m | 18 cm |
| Same example with mh = 0.10 kg/m | 0.105706 m | 11 cm |
| Unweighted slope | 0.101937 | 0.102 |
| Slope angle | 5.820° | Roughly six degrees |
| Weighted contact ratio, clearance 0.15 m | 0.704704 | 0.70 |
| Dynamic-pressure scale, ρ = 1.2 kg/m³, U = 0.6 m/s | 0.216 Pa | 0.22 Pa |
| Thermal scale, ΔTair = 5 K, T₀ = 295 K, one metre below neutral level | 0.199525 Pa | 0.20 Pa |
| Richardson number for those temperature/speed scales and L = 1 m | 0.461864 | 0.46 |

These analytic chosen-load examples must remain separate from the computed shower loads. In particular, the simulation does not impose or reproduce a selected 0.20 Pa pressure.

## Primary references and claim support

The following source inspection is retained from the independent audit of 15 September 2026. This reconstruction does not claim to have retrieved the same pages again. Stable scientific content and source identities have been checked against the retained audit; no changed claim requires new external research.

| Article reference | Primary source | Supported claim and restriction |
| --- | --- | --- |
| 1 | NASA Glenn, [Drag Equation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/drag-equation/). | Standard drag magnitude and coefficient dependence. Vector direction and equal-and-opposite gas force are applications of mechanics. This is not a shower input dataset. |
| 2 | S. Ghosh and J. C. R. Hunt (1994), “Induced air velocity within droplet driven sprays,” *Proceedings of the Royal Society of London A* 444(1920), 105–127, [DOI](https://doi.org/10.1098/rspa.1994.0007). | Supports induced air flow from droplet-driven sprays and comparison with measurements. Publisher metadata and indexed primary text were verified, including the measurement comparison; direct full-text access failed. No quantitative shower benchmark is claimed. |
| 3 | NASA Glenn, [Bernoulli’s Equation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/bernoullis-equation/). | Supports the assumptions, streamline restriction, different streamline constants and dynamic-pressure scale. It does not justify inferring across-curtain pressure from two arbitrary air speeds. |
| 4 | David Schmidt (2001), [Why Does the Shower Curtain Move Toward the Water?](https://www.scientificamerican.com/article/why-does-the-shower-curta/), *Scientific American*, 11 July. | First-person description of a spray-driven low-pressure vortex. Axis explicitly perpendicular to the curtain; circulation parallel to it. Computational mechanism evidence, not experimental curtain validation. |
| 5 | Improbable Research, [Past Ig Winners, 2001 Physics](https://improbable.com/ig/winners/#ig2001). | Confirms Schmidt’s 2001 award and the citation’s “partial solution” wording. Use the current winners URL. |
| 6 | Jorge Lindley (2015), [MA3D1 Fluid Dynamics Support Class 2 — Conservation and Circulation](https://warwick.ac.uk/fac/sci/masdoc/people/studentpages/students2012/lindley/fluid_dynamics/fluidssupport2_2015.pdf), University of Warwick, 23 January. | A standard Rankine-vortex exercise. Does not explicitly print the manuscript’s pressure formula, which the article derives directly. Its Ω denotes vorticity, whereas the article’s Ω denotes angular speed; do not conflate them. |
| 7 | John H. Klote (1989), [Considerations of Stack Effect in Building Fires](https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nistir89-4035.pdf), NISTIR 89-4035, issued May 1989, §§2.1 and 3. Supplement: NIST (2022), [Building Airflow Physics](https://www.nist.gov/video/building-airflow-physics). | Supports the pressure relation about a neutral plane and dependence on opening geometry. For the article’s sign: Δp = g(ρout−ρin)(zn−z). Neither source determines a shower’s neutral height. |
| 8 | MIT Non-Newtonian Fluid Dynamics Group, [Definition of Surface Tension](https://web.mit.edu/nnf/education/wettability/definition.html), capillary adhesion section. | Supports attraction between appropriately wetted surfaces joined by a liquid bridge. It does not quantify curtain–skin adhesion or show that every liquid bridge attracts. |
| 9 | RWTH Aachen, [Heat Equation, §11.2 Boussinesq Approximation](https://rwth-mbd.pages.git.nrw/courses/cmm/content/script/chapters/heatequation.html). | Supports small density changes retained in thermal buoyancy and reference density elsewhere. Upward z gives positive buoyancy for warm air after reference hydrostatic subtraction. |
| 10 | OpenFOAM Foundation, [SchillerNaumann.C, version 13](https://cpp.openfoam.org/v13/SchillerNaumann_8C_source.html). | Verifies CdRe = 24(1 + 0.15Re^0.687) at low Re and 0.44Re above the switch. Project code uses the lower branch at exactly Re = 1000; OpenFOAM uses the upper branch there. This isolated endpoint convention does not invalidate the general correlation citation. |
| 11 | OpenFOAM Foundation, [RanzMarshall.C, parcel heat transfer, version 12](https://cpp.openfoam.org/v12/src_2lagrangian_2parcel_2submodels_2Thermodynamic_2HeatTransferModel_2RanzMarshall_2RanzMarshall_8C_source.html). | Verifies Nu = 2 + 0.6√Re Pr^(1/3). The project applies it to sensible convection and does not model evaporation or latent heat. |
| 12 | U.S. EPA, [Showerheads — WaterSense](https://www.epa.gov/watersense/showerheads). | Standard 2.5 US gal/min and WaterSense maximum 2.0 US gal/min, approximately 9.46 and 7.57 L/min. Context for an 8 L/min scenario, not a universal shower specification. |
| 13 | D. Zhang, L.-T. Wong, W.-K. Lam and K.-W. Mui (2025), [Measuring Dynamic Thermal Sensation in a Residential Bathroom for Water-Efficient Showering](https://ira.lib.polyu.edu.hk/bitstream/10397/116396/1/Zhang_Measuring_Dynamic_Thermal.pdf), Symposium CIB W062. | Table 1 supplies experimental water settings of 8/10 L/min and 35/38/41°C. Does not supply a jointly measured droplet, airflow, pressure and curtain specification for the project. |
| 14 | U.S. EPA, [Inhalation Exposure to Tap Water Through Showering: Literature and Model Review, Appendix C](https://archive.epa.gov/epawaste/hazard/web/pdf/appendc.pdf), printed p. C-3. | The approximately 1 mm diameter was selected by benzene-emission calibration. It is a modeling precedent, not a directly measured drop distribution. No such fit was performed in the project. |
| 15 | NPARC Alliance/NASA Glenn, [Tutorial on CFD Verification and Validation](https://www.grc.nasa.gov/WWW/wind/valid/tutorial/tutorial.html) and [Examining Spatial Convergence](https://www.grc.nasa.gov/WWW/wind/valid/tutorial/spatconv.html). | Supports the distinction between verification and validation. Relative two-grid change alone is not an error estimate. This reference must not be used as evidence for the package’s own reported tests or numerical results. |

## Reconstructed manuscript review and final sign-off

Reviewed file: `article/why-a-shower-curtain-attacks-you.md`.

Final reviewed SHA-256: `3aea75958b97c61a3bc9437fc171ad6f901427e65bd3590a485c21662e66a197`.

The complete article was read on 17 September 2026. The force signs, dimensions, analytic derivations, benchmark arithmetic and computed tables agree with the restored implementation and results. In particular, the article preserves the distinction between prescribed analytic loads and computed spatial pressures, between mean-load equilibrium and actual startup motion, and between the airflow and release clocks.

Four requested clarifications were applied and checked:

1. The droplet Reynolds-number paragraph now identifies νa as the molecular **kinematic** viscosity of air, consistent with units m²/s.
2. The Prandtl number is defined as the ratio of molecular momentum diffusivity to thermal diffusivity.
3. The reported sub-5% changes are explicitly identified as a sensitivity screen, not a numerical or physical error bound.
4. The EPA one-millimetre precedent is explicitly identified as having been selected by calibration against benzene emissions. The present study fits no curtain observations.

The drag relation is stated for positive Reynolds number through Re = 1000, with the finite zero-slip limit discussed separately. This agrees with the project’s branch convention. The Ranz–Marshall formula, source units, droplet mass and effective mixing coefficients are correct.

All 15 references are cited and their first appearances run from 1 through 15. All 15 bibliography entries match the retained source audit. Figure captions run from 1 through 5 and animation captions from 1 through 5, each in order of appearance. The current Ig Nobel URL and the NISTIR stack-effect source are present. Reference 15 supports the verification/validation distinction rather than acting as evidence for this package’s numerical outputs.

The text identifies the fixed air boundary, absence of a bather and wet-contact calculation, sensible-only heating, 10–12 s transient averaging window, retained spatial load, and separate six-second release experiment. The conditional light-curtain reach is tied to the unchanged computed load and nine fixed probes. Parameter cases are identified as screening-grid calculations without individual mesh refinement. The grid comparisons retain 12 parcels per injection step; separate parcel refinement and the absent joint finest-grid/highest-parcel run are disclosed. The less-stable full pressure maps and raw startup peaks are excluded from the article’s quantitative evidence.

No substantive scientific issue remains within that scope. No further external research, tests or CFD reruns were needed for this reconstruction review. This sign-off applies to the manuscript hash above and does not substitute for visual rendering QA or experimental validation.
