# Phase-one visual outputs

The primary airflow visuals use the three active mechanisms on the finest executed grid, 48 × 64 × 64 cells: `grid_fine_spray.npz`, `grid_fine_heat.npz`, and `grid_fine_both.npz`. The exact-rest exchange-off control is checked separately and is omitted from this three-panel comparison. The airflow boundary is fixed in every panel.

## Primary assets

| Basename | Content |
| --- | --- |
| `figure_01_geometry` | Physical enclosure dimensions and the actual saved fine-grid slice |
| `animation_01_fine_airflow` | Reduced pressure and instantaneous projected streamlines at physical airflow times 0–12 s |
| `animation_02_fine_curtain_pressure` | Full-curtain outside-minus-inside pressure maps at physical airflow times 0–12 s |
| `animation_03_fine_mean_load_release` | Separate release from rest under the computed 10–12 s mean pressure load, with the matching static reference |
| `animation_04_fine_air_temperature` | Air temperature rise and its corresponding buoyancy term at physical airflow times 0–12 s |

Static figures and animation posters are supplied as PNG and SVG under `figures/`. Animations are supplied as GIF and MP4 under `animations/`. Animation posters show their final rendered time.

The static-displacement results and their quantitative comparison are presented separately in the study charts. Local curtain-pressure maps are not fully grid-converged; the maps display the calculated fields on the named grid. Raw airflow-startup structural excursions are not part of this primary animation set.

## What the images represent

The saved y–z slice lies at **x = 0.46875 m**; the requested target was x = 0.45 m. This slice is parallel to the fixed curtain at x = 0.9 m. Streamlines are integrated within the saved instantaneous `(u_y, u_z)` field. They show the direction of its two-dimensional projection. They are neither particle trajectories nor three-dimensional streamlines, and their directional marks do not encode speed. The numerical velocity arrays are not altered. Per-panel speed readouts use the saved in-plane velocity.

Reduced pressure uses a common symmetric-log normalization, with a linear interval from −0.02 to +0.02 Pa and logarithmic scaling beyond it. Its limits include the full pressure range across all three mechanisms and all rendered times. Full-curtain pressure loads use a separate common linear scale. Air-temperature rise uses one common linear scale. Pixels represent saved cells without spatial smoothing. The temperature readout's `g β ΔT` is calculated from that same saved temperature field and the source configuration.

The airflow animations use all 121 saved snapshots, spaced 0.1 s apart, at 10 frames per second. The first and last clock values are 0 and 12 s. The final video frame remains visible for one frame interval.

## Separate mean-load release experiment

The release comparison reads `release_grid_fine_spray.npz`, `release_grid_fine_heat.npz`, and `release_grid_fine_both.npz`. Each archive supplies its dynamic response, static reference, pressure averaging window, source hash, and selected width probe. The source airflow hash is checked before rendering.

The release clock is **time since release under the computed 10–12 s mean load**. It is independent of the airflow clock. The pressure is held constant without rescaling. The displacement does not alter the airflow boundary or any displayed flow field.

Each mechanism uses its metadata-selected probe: the largest saved excursion among the same nine fixed sampled physical widths. The selected width remains fixed during the animation and is printed above its panel. The shape and static reference use that identical width. The accompanying history reports the largest inward displacement along this selected strip, `max(Y)`, in centimetres. It is not a width average. Its dashed line is the corresponding largest inward static displacement. Structural displacement is denoted by `Y` to distinguish it from air velocity.

Shape panels use equal horizontal and vertical metre scales. The default release animation draws every third saved 0.02 s state: 101 frames at 1/0.06 frames per second, covering release times 0–6 s. The history curve retains all saved samples up to the displayed time. The original response arrays and their extrema are preserved.

## Reproduction and verification

From the project root:

```bash
python -m curtainflow.render --only fine
python -m curtainflow.render --only release
```

`--data-dir` and `--output-dir` select alternate input and output roots. `--max-frames` chooses a constant stride through saved frames and adjusts playback rate to preserve physical time. A stride that does not divide the saved interval can omit the final state; the manifest records the exact chosen times.

All formats are first written in a private temporary directory on the same filesystem. PNGs pass checksum verification and full pixel decoding; GIFs decode every frame and match the requested frame count; SVGs parse as XML; MP4s pass a full ffmpeg decode and match the requested frame count. Completed files are flushed and atomically moved to their public filenames. The manifest is also updated atomically, with a file lock to protect simultaneous render completions.

`render_manifest.json` records the source-byte SHA-256 hashes, selected time samples, pressure and temperature scales, actual slice coordinates, release-probe choices, and interpretation of every output. Source hashes are captured from the exact bytes loaded before rendering.

## Final artifact audit

The 18 final visual files were re-opened after atomic publication and passed the complete decoding or parsing checks described above. All source hashes in the manifest match the current source archives. `docs/render_validation.json` records each delivered visual's byte size, SHA-256 hash, verification result, and expected animation frame count.

| Animation | GIF frames | MP4 frames | Sample spacing | Clock range |
| --- | ---: | ---: | ---: | --- |
| Fine-grid airflow | 121 | 121 | 0.10 s | Airflow 0–12 s |
| Fine-grid curtain pressure | 121 | 121 | 0.10 s | Airflow 0–12 s |
| Fine-grid mean-load release | 101 | 101 | 0.06 s | Release 0–6 s |
| Fine-grid air temperature | 121 | 121 | 0.10 s | Airflow 0–12 s |

The geometry and all four final posters were visually inspected. The release history uses `max(Y)` in centimetres, its shape uses metres at equal axis scales, and the pressure-map readouts sit below the axis labels.
