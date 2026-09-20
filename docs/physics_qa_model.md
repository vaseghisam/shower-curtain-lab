# Independent physics review of the replacement model

Reviewer: physics QA agent, separate from the solver implementation. Scope: `STUDY_PLAN.md`, `grid.py`, `droplets.py`, `simulation.py`, `mechanics.py`, and the four preliminary 12-second control outputs in `data/pilot`. This report reviews the equations and physical interpretation; the separate numerical QA reports govern refinement and numerical acceptance. The original article and original package were not edited.

## Assessment

The replacement preserves the article's causal chain: individual droplet drag supplies air momentum; a three-dimensional incompressible calculation establishes pressure; pressures adjacent to an impermeable curtain supply a hanging-strip load. Warm water supplies computed sensible heat, which then supplies buoyancy. Neither mechanism is implemented through a selected inward pressure field. This is an appropriate model for the user's requested conditional demonstration with plausible inputs and no experimental fit.

The model supports statements about computed loads and the response of the article's strip to those loads under the specified conditions. The fixed airflow boundary and one-way structural continuation must remain explicit. A static or dynamic displacement obtained from a fixed-boundary load is not automatically a self-consistent position of a curtain that has changed the flow passages.

## Equation and implementation audit

| Connection | Independent finding | Status |
|---|---|---|
| Spherical drag → droplet acceleration | Division by spherical droplet mass gives the implemented factor 3ρₐ/(4ρ_wd). Sign opposes slip; gravity is separate. Molecular viscosity is used in the droplet Reynolds number. | Consistent with stated model. |
| Droplet acceleration → gas forcing | Gas receives the negative of the computed parcel drag impulse, with normalized grid deposition. Parcel mass represents many same-diameter droplets and does not change their physical diameter. | Conserves intended exchange. |
| Water heat loss → gas heat | The spherical energy balance gives 6kₐNu/(ρ_wc_pwd²), matching the code. Frozen-coefficient exponential cooling and opposite gas heating are consistent. | Sensible heat only; no evaporation claim. |
| Air momentum → pressure | One pressure gauge is used in a connected, impermeable-baffle geometry. Blocked faces are exactly closed. No pressure jump is prescribed as an input. | Repairs the earlier porous-layer ambiguity. |
| Pressure sign → curtain direction | Outside-minus-inside pressure is positive for inward displacement toward decreasing x. | Consistent; no sign reversal to obtain a desired result. |
| Normal viscous load | The sign 2ρν_eff[(∂ₓuₓ)_in − (∂ₓuₓ)_out] follows from the normal stress on the two sides. | Diagnostic is implemented; it should be included in, or compared with, final structural loading. |
| Load → strip | The original gravitational tension, dynamic hem mass, and top support are retained. Saved spatial/time loading is applied to selected width strips. | Direct article connection; not a fitted uniform-pressure surrogate. |
| Strip model validity | Small slopes, no cross-width coupling, constant gravitational tension to leading order, and phenomenological damping. | Conditional response; slope and clearance events limit integration. |

The updated collision routine was inspected after the initial pilot runs. It now finds wall intersections along the midpoint quadratic trajectory, ending each parcel's step at that intersection. It also records curtain-impact mass, momentum, and sensible energy separately. These changes address earlier audit comments; the retained pilot data predate those additional diagnostics and must not be presented as the final source run.

## Parameter support

The chosen 8 L/min flow and 40°C water temperature are within the settings or rates documented by the primary sources in `MODEL.md`. A 1 mm representative diameter has an EPA modeling precedent, but that diameter was calibrated to benzene emissions in the cited exposure model. It is not a measured droplet distribution and was not fitted to curtain behavior here. TOTO's published simulated droplet sizes provide additional modeling precedents. The chosen launch speed, cone, head location, and enclosure geometry form a declared scenario rather than a jointly measured shower.

The launch speed is an initial condition. Droplets accelerate downward under gravity and exchange momentum with moving air, so their later speeds and the gas speed should not be compared with launch speed as if that value were a universal upper bound.

The effective momentum diffusivity is about 200 times the selected molecular viscosity. This is a constant unresolved-mixing assumption, not measured shower turbulence. The proposed half/double screen is necessary to show how the conditional result depends on this closure. The analogous thermal diffusivity is also a chosen closure. The thermal field must always be reported as calculated air temperature, not equated with water temperature.

## Preliminary control evidence

The archived pilot calculation left the gas exactly at rest in the off control. Its three forced cases gave positive spatially averaged pressure differences at 12 seconds, while individual curtain locations also had negative pressure differences. This supports retaining spatial loading rather than replacing it with a single mean force. These pilot signs are not substitutes for a final refinement study.

The pilot gas/liquid exchange ledgers closed to rounding-level differences; the combined run recorded approximately 12.29 kJ of sensible heat transferred to the gas and the same gas heat gain. Such balances check implementation consistency, not the accuracy of the heat-transfer closure in a real shower. Temperature extrema remained finite and nonnegative relative to the initial state. The largest pilot heat-only temperature rise was about 16.13 K, giving βθ ≈ 0.055: a modest, explicitly inspectable Boussinesq density change.

The saved modeled normal-viscous load was not negligible at every location. Its field norm divided by the pressure-load norm over all saved pilot frames was 8.66% for spray, 6.80% for heat, and 6.91% for both. At 12 seconds the respective ratios were 11.73%, 6.66%, and 7.24%. These are load-field diagnostics from preliminary data, not final uncertainty estimates. The relevant follow-up is to compare pressure-only and pressure-plus-viscous structural observables, because the strip weights the spatial load nonuniformly.

## QA matrix and remaining interpretation checks

The study plan's control, grid, time-step, parcel, and analytic-strip checks cover the main equation chain. The following additions or explicit reporting choices improve that plan without demanding experimental fitting:

1. **Apply or compare the full modeled normal stress.** Preserve separate pressure and viscous arrays, then compare resulting excursions. A small mean viscous force alone does not establish a small displacement effect.
2. **Expose direct water impact.** Report the new curtain-impact ledger for each case. A substantial impact count changes interpretation because the strip currently receives aerodynamic loading only.
3. **Screen damping when reporting transient peaks or times.** The coefficient is assumed, so a half/double comparison should accompany a quantitative claim about overshoot or a first-clearance event. Static equilibrium does not depend on damping.
4. **Check the saved loading cadence and structural resolution.** Air time-step convergence does not itself establish convergence of a strip driven by time-interpolated saved loads. Compare selected cases using a finer save interval and structural mesh if transient observables are emphasized.
5. **Describe finite observation time.** The 12-second results describe startup and the stated interval; they do not establish a long-time steady state in an insulated enclosure that continues to receive heat.
6. **Retain all screened outcomes.** Both positive and negative loads, sign changes with height, weak thermal motion, and closure sensitivity are legitimate conditional results. Varying plausible inputs is appropriate; selecting only a preferred sign without showing the screen is not.
7. **Keep animations faithful to stored fields.** Water-parcel snapshots are representative point clouds. The saved subset changes identity between frames, so connecting equal array positions into apparent trajectories would be false. A streamline is an instantaneous velocity-field diagnostic, not a material air path unless actually integrated through time.

## Fixed-boundary sensitivity

A moved-boundary calculation is not a prerequisite for stating the strip's response to the calculated fixed-boundary load. It becomes important when interpreting a large excursion as the actual final position or a physical contact prediction. The available solver permits a practical geometry screen without implementing fluid–structure coupling: at the 0.05 m x spacing, compare baffle positions x = 0.90, 0.85, and 0.80 m with other inputs fixed, initially for spray and combined forcing.

This is a uniformly translated plane, including its upper support. It tests distance and compartment-width dependence. It does not reproduce the deformed profile of a curtain whose rod stays fixed, and it cannot certify moving-curtain accuracy. If sign, pressure profile, or excursion changes materially, report the dependence and keep the prescribed-load interpretation. A stable result under these translations supports robustness to that particular geometry change, not a universal claim about all bathrooms.

The appropriate scientific claim is conditional: within the declared parameter range and model assumptions, the solved exchange and flow can produce the reported load, and the same hanging-strip mechanics introduced earlier produces the reported response. Experimental validation and full moving-boundary coupling would answer additional questions, but they are not required to make this specified numerical demonstration authentic.

## Addendum: release under a computed mean load

The production agent subsequently reported that medium-to-fine differences were small for the 10–12 second mean spray load and the corresponding static strip deflections, while the full-startup dynamic maximum still changed by approximately 20.6%. Those are different observables. Passing a mean-load or static check does not make the startup maximum numerically accepted.

A separate release-under-mean-load experiment is physically legitimate and remains close to the article's original mechanics. Define a spatially resolved load from the computed airflow:

$$\bar q(y,s)=\frac{1}{t_b-t_a}\int_{t_a}^{t_b}q(y,s,t)\,dt,
\qquad t_a=10\ \mathrm{s},\quad t_b=12\ \mathrm{s}.$$

Here q must be identified as pressure alone or total modeled normal stress; the selected definition must be consistent across cases. Apply this unscaled distribution as a constant load in the same strip equation, beginning with a straight, stationary strip. The animation then solves a new mechanical initial-value problem. Its clock measures time since release under the computed mean load. It does not resume the actual shower calculation at 12 seconds, and its motion is not the shower-startup prediction.

This is an appropriate conditional demonstration because the load amplitude, height dependence, and width dependence all come from the solved air calculation. No illustrative 0.2 Pa, pressure multiplier, prescribed inward path, or target excursion replaces the result. In the linear unconstrained static strip model, equilibrium is a linear function of loading; equilibrium under the average load also equals the average of the instantaneous equilibrium solutions. That identity does not imply that a dynamically moving curtain follows either equilibrium.

Recommended presentation and acceptance:

1. Use mean-load static displacement as the main numerical quantity once its own checks pass. The release animation can explain the mechanical response to that calculated load.
2. Run the release problem with both medium and fine mean spatial profiles before quoting its transient peak. Static tip convergence alone does not establish convergence of the excited modes. Also retain the structural resolution and assumed damping checks.
3. Show the 10–12 second averaging window explicitly. It is a selected transient interval, not an established steady state or a statistically converged turbulent mean. Compare another late interval if claiming the chosen window represents a persistent load; otherwise report it simply as the chosen interval.
4. Preserve the failed full-startup peak comparison and identify it as the reason for separating the better-resolved mean-load experiment. Averaging is a change in the question being answered, not a numerical repair of that failure.
5. Keep the actual air-transient animation and the mechanical-release animation on separate clocks and label their fixed-boundary relationship. A synchronized overlay would imply a coupled physical history unless this distinction were unmistakable.

Subject to these conditions, the mean-load release study is an authentic calculation from the article's equations and a useful phase-one result. It should not be advertised as recovering a converged large startup excursion or demonstrating contact in a real shower.

## Final scientific and editorial audit of RESULTS.md

The final results text was checked against `numerics_qa_results.md`, `numerics_qa_final.md`, `results_summary.json`, `material_summary.json`, `damping_summary.json`, and the fine-run metadata. The main tables correctly use the fixed physical probes for their stated maxima, rather than substituting maxima over every sampled width. The light-curtain width means and the 7.45, 4.77, and 11.69 cm probe maxima agree with the independent static calculation. The reported full-width slope bound below 0.14 is supported by the separate material-response summary; it is not presented as a finely converged local slope value.

The release peaks of 4.62, 3.33, and 7.77 cm refer to the separate constant-mean-load mechanical experiment, and both its initial condition and clock are explicitly distinguished from the 0–12 second airflow startup. The failed spray startup peaks and local pressure-map comparisons remain visible. The text also discloses the incomplete joint grid/parcel study and identifies the parameter sweep as a screening-grid sensitivity study. Consequently, passing selected mesh comparisons is not described as a universal error bound or experimental accuracy.

Three clarifications were added directly to RESULTS.md:

1. The main mechanics is pressure-only; on the screening grid, adding the modeled normal viscous stress increases width-mean static hem displacement by 2.0%, 3.5%, and 3.0% for spray, heat, and both. These percentages were independently recomputed from the stored summaries and are not claimed for the fine grid. The fine baseline droplet ledgers all record zero curtain impacts.
2. The light curtain's crossing of a hypothetical 10 cm clearance is explicitly conditional on the unchanged load and absence of a body or moving airflow boundary. It is not a computed body-contact event.
3. The translated-curtain geometry comparisons are identified as spray-only. Their scope is not extended to the combined heated case, whose larger light-curtain displacement remains a fixed-boundary result.

MODEL.md also now states the precise averaging equation and the separate release load history. No original article text or previous package was changed. The resulting phase-one interpretation is scientifically consistent with the requested plausibility demonstration: computed sources produce computed loads, and the article's existing mechanics produces the reported conditional response. Unresolved local and startup quantities remain outside that accepted argument.
