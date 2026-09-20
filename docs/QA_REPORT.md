# Quality assurance for the phase-one study

**Disposition:** the study supports a conditional, centimetre-scale pressure-to-strip demonstration. Its specified integrated pressure, static displacement and mean-load release measures pass the medium-to-fine 5% change screen. The raw spray/combined startup maxima and detailed spray pressure maps do not pass and are excluded from the main quantitative argument. This is verification of the chosen calculation, not a fitted or experimentally validated shower prediction.

## Independent review

The physics QA agent reviewed the source evidence, droplet–air exchange, boundary conditions, pressure sign, strip mechanics and limits of one-way coupling. The numerical QA agent independently authored seventeen executable tests and evaluated saved results using direct continuum quadrature, separate from the production static finite-element calculation. Eight additional tests accompany the droplet implementation. The final recorded suite has **25 passing tests**; see `numerics_qa_test_log.txt`.

The independent review records are [physics_qa_model.md](physics_qa_model.md), [numerics_qa_final.md](numerics_qa_final.md), and [numerics_qa_results.md](numerics_qa_results.md). Initial audits are retained to show what changed during development. They are historical records, not statements that their identified faults remain in the final implementation.

## Equation and implementation checks

| Check | Evidence and result |
| --- | --- |
| Impermeable curtain and room walls | Exactly zero velocity on blocked faces in completed controls; no porous-curtain force law |
| Air incompressibility | Maximum recorded divergence below 5.4 × 10⁻¹⁴ s⁻¹ in the three fine runs |
| Pressure sign, gauge and force reconstruction | Independent manufactured-force test checks the full SSPRK pressure, including both projection corrections |
| Momentum transport | Discrete pressure/divergence adjoint identity and convection energy identity checked |
| Effective diffusion | Dissipation and masked free-slip boundary behavior checked |
| Gas temperature transport | Constant-field preservation, conservation, monotonicity and grid behavior checked with the limited scalar flux |
| Water mass | Fine-run cumulative imbalance below 1.5 × 10⁻¹⁴ kg for 1.6 kg injected |
| Water momentum | Gravity, transferred gas impulse, remaining parcel momentum and wall-exit momentum close below 2.3 × 10⁻¹³ N·s in fine runs |
| Sensible energy | Droplet ledger error below 8.0 × 10⁻⁹ J; gas heat-balance error below 3.0 × 10⁻¹¹ J in fine heated runs |
| Direct curtain impact | Zero represented water mass strikes the curtain in the selected fine controls |
| Drag and heat transfer | Drag correlation branches, representative mass, ballistic impact, sensible exchange and constant-drag trajectory benchmarks checked |
| Original strip equation | Uniform 0.20 Pa, H = 1.8 m, σ = 0.20 kg/m² gives 18.3486 cm without a hem weight and 10.5706 cm with 0.10 kg/m hem mass; weighted mesh convergence is second order |
| Structural events | Exact first-contact/slope-stop states are retained; no motion is extrapolated after termination |
| Saved arrays | Stored pressure differences and viscous normal-stress corrections independently reconstructed from final fields |

Conservation alone cannot establish pressure or displacement accuracy. It checks implementation consistency alongside, rather than in place of, the refinement comparisons.

## Refinement and model sensitivity

The grids are 24 × 32 × 32, 36 × 48 × 48 and 48 × 64 × 64 with unchanged physical geometry. The first two use a 0.004 s step; the fine grid uses 0.002 s. Nine structural probes remain at identical physical width positions between grids. Independent static quadrature and production finite elements agree to the displayed precision.

The accepted and failed medium-to-fine comparisons are tabulated in [RESULTS.md](../RESULTS.md). A 5% difference is a study screen, not a rigorous error estimate. The fine-grid/local-map failures remain relevant even where an integrated response passes.

- Halving the screening-grid fluid step changes the spray startup maximum by 0.032%.
- Saving pressure every 0.024 s rather than 0.10 s changes that maximum by 0.40%. The separate output-cadence run has bitwise identical final fluid fields, isolating the effect of sampling the load.
- Increasing nozzle quadrature from 24 to 48 parcels per injection step changes the checked spray displacement measures by less than 5% on the screening grid. The baseline 12-ray calculation has a larger source-sampling sensitivity; joint fine-grid/high-ray refinement is not established.
- The fine spray run's recorded conservative nonlinear source-coupling indicator peaks at 0.0686. Fine heat/both finished before this diagnostic-only monitor was added, so no recorded maximum is claimed for those runs. All three complete with bounded states; their largest advective CFL values are 0.435, 0.116 and 0.423.
- Including the recorded normal viscous-stress correction changes baseline coarse-grid static and dynamic response measures by less than 4%. The maps themselves can have a larger relative viscous correction.
- Varying effective air mixing, water properties and spray geometry leaves all sampled late mean loads inward. These parameter cases are screening calculations, not separately refined predictions.
- Translating the flat curtain by 5 and 10 cm checks spray-case distance sensitivity. It moves the rod too and does not represent an actually deformed sheet.
- Halving/doubling the assumed structural damping changes mean-load release peaks by approximately +4%/−7%. Static results do not depend on this coefficient.

## Authenticity of the visuals

Airflow and temperature frames are generated from saved numerical arrays. Their clock is physical simulation time. A two-dimensional slice of the three-dimensional velocity can show projected streamlines; these must not be called three-dimensional particle paths. Representative water-parcel snapshots do not preserve parcel identity between frames and are not joined into invented trajectories.

The curtain release animation integrates the article's strip dynamics under the computed 10–12 s mean spatial pressure held constant. Its independent clock is time since release. This experiment was explicitly introduced after the raw startup peaks failed their mesh check; it neither removes that failure nor claims to show actual subsequent bathroom evolution. No displaced curtain is inserted into the calculated airflow as if a moving-boundary solution had been performed.

Scientific charts retain units, pressure signs, actual geometry and source case identifiers. Root visual review checks legibility and correspondence with the reported quantities. The renderer writes assets atomically and validates PNG decoding, SVG parsing, every GIF frame and the full MP4 decode before replacement. Its `render_manifest.json` records source hashes and rendering metadata. Archive-level checks and per-file checksums are recorded at delivery.

## Development corrections retained in the record

The earlier porous boundary was replaced by an impermeable baffle before the main comparison. A missing contribution to full-step pressure was corrected and tested. An unstable first fine-grid trial was rejected; the time step was reduced with physical inputs unchanged. A truncated archive was detected, regenerated and followed by atomic numerical output. Structural sampling was changed from grid-relative indices to fixed physical positions before acceptance comparisons. Time averages were standardized to a trapezoidal integral over exactly 10–12 seconds.

These changes improve the numerical calculation without selecting an inward pressure target. See `development_notes.md` and the initial independent reviews for the sequence and details.
