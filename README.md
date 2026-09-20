# Why a Shower Curtain Attacks You

This repository accompanies the revised science article. It connects droplet drag and sensible heating to a computed air-pressure field, then applies that pressure to the same hanging-strip equation developed in the article. The study uses declared inputs and parameter variations; it is not fitted to experimental curtain measurements.

## Read and publish

- [Complete TK Markdown article](why-a-shower-curtain-attacks-you-tk.md)
- [Canonical manuscript](article/why-a-shower-curtain-attacks-you.md)
- [Editorial changes, including all 18 highlighted passages](docs/EDITORIAL_CHANGELOG.md)
- [Numerical results and their scope](RESULTS.md)

Import the complete `why-a-shower-curtain-attacks-you-tk.md` file into TK. It uses inline dollar-delimited math, one-line display equations, and numbered references. Its media links are relative to `assets/`. Local Markdown and asset checks were performed; a live TK import was not tested. If TK does not resolve local media automatically, attach the corresponding PNG or GIF from `assets/` at its caption. MP4 versions are included for video publication.

For GitHub, extract the ZIP and use this directory's contents as the repository root. Upload the source, article, data and media together so relative links remain valid. The ZIP is a delivery container and does not need to be committed. No repository has been created or published on your behalf.

## Publication media

Each static figure has PNG and SVG versions. Each animation has GIF and MP4 versions, with inspection images. The renderer and source records are in [PUBLICATION_VISUALS.md](docs/PUBLICATION_VISUALS.md).

| Number | Figure | Animation |
| --- | --- | --- |
| 1 | Modeled enclosure geometry | Single-droplet drag benchmark |
| 2 | Prescribed pressure and curtain equilibrium | Analytic rotating-core pressure |
| 3 | Computed pressure and strip response | Analytic thermal pressure columns |
| 4 | Curtain mass and hem-weight response | Saved three-dimensional airflow, shown in a section |
| 5 | One-at-a-time input variation | Strip release under the computed mean load |

The first three animations are explicit analytic or numerical demonstrations of stated equations. The airflow animation uses saved computed fields. The release animation integrates strip dynamics under the computed 10–12 s mean load held constant, on its own release clock. It does not show a curtain moving inside a simultaneously recalculated airflow.

## Model and numerical evidence

The baseline uses a three-dimensional incompressible air calculation with an impermeable, fixed curtain. Water parcels transfer drag and sensible heat to the air. The resulting pressure difference drives independent vertical curtain strips, with gravity, hem weight, inertia and damping. [MODEL.md](docs/MODEL.md) specifies the equations, boundaries, inputs and references; [DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) defines all arrays and reproduction stages.

The room has free tangential slip, insulated walls and sealed curtain ends, with openings above and below the curtain. The baseline excludes a bather, ventilation, evaporation, humidity transport, breakup, splash and wet-contact mechanics. Effective mixing is a declared closure. These choices define the conditional calculation.

Integrated pressure, static response and the separate mean-load release maximum pass the study's medium-to-fine 5% change screen. Raw startup spray peaks and detailed spray pressure maps do not. Parameter variations are screening calculations; a joint finest-grid/highest-parcel calculation was not performed. These limitations remain in [RESULTS.md](RESULTS.md) and [QA_REPORT.md](docs/QA_REPORT.md).

## Reproduce

Use Python 3.12 with the pinned Python packages, plus FFmpeg for video export. Run commands from this directory:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m curtainflow.reproduce --stage qa
python -m curtainflow.reproduce --stage figures
python -m curtainflow.export_article
python -m curtainflow.validate_publication --strict-assets --require-tk
```

On Windows, activate with `.venv\Scripts\activate`. Reproduction writes new files in this directory; preserve any edited results first. The delivered data can be inspected without rerunning the flow solver.

```bash
python -m curtainflow.reproduce --stage flow --cases grid_fine_spray grid_fine_heat grid_fine_both --workers 2
python -m curtainflow.reproduce --stage analysis
python -m curtainflow.reproduce --stage figures
python -m curtainflow.reproduce --stage qa
python -m curtainflow.bundle
```

Omit `--cases` to rerun all executed configurations. Fine cases previously took roughly 13–17 minutes each in the production environment; hardware and concurrency affect duration. Each flow archive has an executed configuration sidecar. Data loads with `numpy.load(path, allow_pickle=False)`. Parcel snapshots use NaN padding for unused entries.

The original review figures and animations are retained in `figures/` and `animations/`; their renderer remains in `curtainflow/render.py`. Publication media are in `assets/`. Historical phase-one audit files retain their original scope and are not new claims about publication review.

## Quality assurance

The package includes 25 numerical tests, independent saved-result calculations, physics and numerical reviews, and publication checks:

- [Numerical QA](docs/QA_REPORT.md)
- [Publication science review](docs/PUBLICATION_SCIENCE_QA.md)
- [Independent editorial review](docs/PUBLICATION_EDITORIAL_QA.md)
- [Publication package review](docs/PUBLICATION_PACKAGE_QA.md)
- [Editorial revision record](docs/EDITORIAL_CHANGELOG.md)

`FILES.sha256` identifies the delivered files. The bundle command checks archive integrity, images, local links, publication preflight and hashes before writing a ZIP, then checks the ZIP itself. The inventory identifies the shipped implementation and data; it does not certify that every run preceded later diagnostic-only changes to the source. No new full CFD runs were needed for the publication revision.
