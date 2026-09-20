# Publication package QA

Independent package review, 17 September 2026. **Publication preflight passed** after the article and visual exports were frozen. The audit checked 28 display equations, 15 references, all ten article media links, 69 publication file/source hashes, 16 retained review-visual source hashes, 15 PNG files, ten SVG files, all frames of five GIFs, and all five MP4 streams. The final bundle and inventory checks are recorded in `delivery_validation.json`; the detailed publication results are in `publication_preflight.json`.

## Numerical checks

The existing 25 numerical tests were rerun for this publication revision: all passed. They cover pressure projection and boundary conditions, discrete conservation, droplet drag and momentum/heat exchange, the analytic hanging-strip benchmark, pressure-to-strip coordinate mapping, and saved-result consistency. No new airflow simulation was needed for this revision.

The publication preflight independently integrates the saved fine-grid pressure over 10–12 seconds using an explicit trapezoidal sum. It verifies the saved summary values, release pressure arrays, release-source SHA-256 hashes, all nine probe peaks, and the selected maximum-displacement probe. It also compares the saved static response with a direct integral of the continuous hanging-strip equation on 8,193 points. That check is independent of the implementation's finite-element stiffness/load construction. The maximum hem difference is 7.6 micrometres; the small difference is consistent with quadrature in the saved 256-element discretization.

| Case | Area-mean pressure (Pa) | Width-mean static hem (cm) | Largest sampled mean-load release (cm) |
| --- | ---: | ---: | ---: |
| Spray | 0.02698009 | 1.819890 | 4.616781 |
| Heating | 0.01880657 | 1.328114 | 3.334930 |
| Spray + heating | 0.04443562 | 3.212729 | 7.768739 |

The chosen uniform-pressure analytic example independently evaluates to 0.18348624 m without a hem mass and 0.10570559 m with a 0.10 kg/m hem mass. These are chosen-load calculations, not outputs of the airflow calculation.

## Article and media checks

`python -m curtainflow.validate_publication --strict-assets --require-tk` checks single-physical-line display equations, balanced inline delimiters and braces, consecutive reference numbers, citation first appearance, five figure captions, five animation captions, ten local media links, absence of editorial markers, and exact agreement between the canonical article and its normalized TK export.

The same command checks the publication source/output hashes and the older review-visual source hashes. It independently decodes all publication PNG files and GIF frames, parses SVG files, and probes MP4 dimensions and frame counts. The renderer additionally fully decodes each MP4 with FFmpeg before atomic replacement and during its final verification. Its generation record includes the manifest hash and the code/style hashes, linking that completed verification to the shipped outputs.

`python -m curtainflow.validate_publication --strict-assets --require-tk --check-inventory` additionally compares every delivered file with `FILES.sha256` and checks inventory coverage. Run this read-only form after bundling; writing a new audit JSON after the inventory has been generated would deliberately invalidate its hash.

The bundle command performs numerical archive CRC checks, local Markdown-link checks, full PNG decoding, SVG parsing and a complete ZIP CRC check. `delivery_validation.json` records its counts. Code, tests, saved numerical inputs/results, figures, animations, reference documentation and QA records are included in the inventory.

## Limits of this review

These are code, saved-data, document and export-integrity checks. They do not establish experimental accuracy. The airflow computations were not rerun during article packaging; their numerical-convergence evidence and remaining limitations are retained in the phase-one QA records. In particular, passing integrity checks does not turn detailed startup pressure maps or the rejected raw startup peaks into mesh-independent predictions.

No actual TK import was performed. The Markdown has passed local syntax checks; if TK does not ingest relative media paths, attach the matching bundled PNG/GIF files from `assets/`. The package has not been uploaded to GitHub. The final file inventory attests the shipped code and artifacts, not the exact historical source revision used for every earlier run.
