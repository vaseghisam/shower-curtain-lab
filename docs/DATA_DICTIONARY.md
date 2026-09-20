# Numerical data and reproduction

All units are SI except configuration `flow_lpm` (litres/minute), `diameter_mm` (millimetres), and angle fields (degrees). Load is positive inward. Open NPZ archives with `numpy.load(path, allow_pickle=False)`.

## Flow case archives

Each `CASE.npz` has `CASE_config.json` containing the executed input dataclass, plus `CASE.json` containing input and run diagnostics. The JSON `metadata` scalar inside the archive is authoritative for that archive.

| Array | Dimensions | Meaning |
| --- | --- | --- |
| `x`, `y`, `z` | Nx, Ny, Nz | Cell-centre coordinates; x is normal to curtain, y along it, z upward |
| `load_z` | Nz_curtain | Cell heights on the blocked curtain face |
| `trace` | Nt × 9 | Physical time, mean/min/max Δp, maximum air speed, maximum gas temperature rise, mean inside/outside rise, active parcel count; exact names in metadata |
| `pressure_load` | Nt × Ny × Nz_curtain | Outside-minus-inside reduced pressure at cells adjacent to the impermeable face, Pa |
| `viscous_load` | Same | Corresponding normal viscous-stress jump, Pa; kept separate |
| `pressure_yz`, `temperature_yz` | Nt × Ny × Nz | Reduced pressure and gas temperature rise on the x cell nearest 0.45 m |
| `velocity_yz` | Nt × 3 × Ny × Nz | Cell-centred Cartesian velocity on that slice, m/s |
| `pressure_xz` | Nt × Nx × Nz | Reduced pressure on the y cell nearest 0.60 m |
| `velocity_xz` | Nt × 3 × Nx × Nz | Cell-centred velocity on that slice |
| `parcels` | Nt × 200 × 3 | Representative actual water-parcel positions, with NaN padding; index identity is not persistent |
| `final_u` | 3 × Nx × Ny × Nz | Staggered velocity at each cell's positive face; masked faces are zero |
| `final_p`, `final_theta` | Nx × Ny × Nz | Final reduced pressure and gas temperature rise |

The cell nearest a nominal slice location varies slightly with resolution. Always use the coordinate arrays when labelling a slice. Reduced pressure uses a gauge; pressure differences are gauge independent. The absolute pressure colours inside the enclosure are not themselves the load across the curtain.

Field snapshots are float32 to limit archive size; the computation and trace diagnostics use float64. Stored timestamps govern the output cadence. In the cadence experiment a requested 0.025 s interval becomes 0.024 s because output is saved on integer time-step boundaries.

## Structural data

`structural_CASE.npz` is the one-way response to the saved time-varying startup load. The fields `t_i`, `s_i`, `y_i` contain physical startup time, distance down the strip and inward displacement for probe i. Probe widths, stop reasons and exact event times are stored separately. An early slope stop is a censored trajectory, not a peak from a completed 12-second response.

`static_CASE.npz` contains the static response to the calculated mean pressure over the final two seconds of that source case. Main runs use exactly 10–12 s. The `s` array runs down the strip; `y` is width × strip nodes. Width-averaged hem displacement uses all saved width cells, whereas independently reported fixed-probe maxima use nine specified physical widths.

`release_CASE.npz` is a separate six-second mechanics experiment. The full spatial mean pressure from 10–12 s is held constant while a flat strip is released from rest. `t_i` is now time since release, independent of the airflow clock. `static_s_i` and `static_y_i` are the equilibrium reference at the same width. Metadata identifies the source archive and SHA-256, averaging window, damping, and the maximum-excursion probe selected for display. No pressure scaling is used.

`results_summary.json`, `material_summary.json`, `release_summary.json` and `damping_summary.json` retain the numerical chart values. Mean pressure and static loads use a time integral. Secondary RMS and sign-fraction diagnostics in `results_summary.json` are sample averages. They are not used as time-integrated headline measures. Independent QA values are in `docs/numerics_qa_results.json`.

The short `fine_timestep_probe` case is a development stability check, not a 12-second comparison. Other flow configurations include the baseline controls, three-grid comparisons, source/time/output refinements, one-at-a-time physical inputs, and translated-plane geometry checks. `experiment_design.json` includes named planned configurations; `*_config.json` sidecars identify what actually ran. In particular, a planned case without an archive is not a result.

## Reproduction commands

From the repository root with requirements installed:

```bash
python -m curtainflow.reproduce --stage qa
python -m curtainflow.reproduce --stage analysis
python -m curtainflow.reproduce --stage figures
```

The analysis stage recomputes structures and summaries from existing flow arrays, including the retained numerical review charts. The figures stage generates the five publication figures and five publication animations in `assets/`. The earlier review renderer remains available as `python -m curtainflow.render`; its files in `figures/` and `animations/` document phase one. QA includes both executable tests and the independent saved-result calculations.

To rerun the expensive airflow calculations from their saved configurations:

```bash
python -m curtainflow.reproduce --stage flow --workers 2
```

Add `--cases grid_fine_spray grid_fine_heat grid_fine_both` to select those cases. Each fine 12-second run took about 13–17 minutes in the production environment while other work ran concurrently; timing depends on hardware. Full fields at every computational step are not retained, but the configured simulation, output slices, load history and final 3D fields are reproducible. Final-source updates after some runs added diagnostics and atomic saving without changing their evolution equations. Hashes identify delivered artifacts, not a claim that every byte was produced before those diagnostic-only edits.
