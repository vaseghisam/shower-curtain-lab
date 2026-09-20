# Development record

The pilot controls were run before exact quadratic wall-intersection timing was added. They were rerun for the final source; superseded pilot outputs are excluded from the review bundle. The selected results are the regenerated archives in `data/`.

The first fine-grid spray attempt at 48 × 64 × 64 cells and dt = 0.004 s stopped at 1.008 s when the CFL exceeded the declared 0.8 limit. A two-second probe at dt = 0.002 s remained stable (maximum CFL 0.435); the fine-grid study uses that smaller step. This is a numerical timestep correction, with no change to the physical source inputs.

One completed control output and a smoke PNG were found truncated during independent decoding. Data and visual output now use temporary files and atomic replacement; the affected control was recomputed and passed independent reconstruction. No damaged artifact is included in the release.

The structural sampler initially selected grid-index positions, which shifted under refinement. Production analysis now interpolates to nine fixed physical width locations. Structural outputs are regenerated from saved flow fields after this correction.

The 10–12 s load average was standardized from an arithmetic sample mean to a trapezoidal integral of the saved signal. Static summaries and charts were regenerated. The independently implemented averaging agrees with this definition.

Raw startup peak displacements failed the medium-to-fine screen for spray and combined forcing. Both QA reviewers accepted a separate release experiment under the computed mean spatial load, conditional on its own refinement comparison and distinct clock. This experiment passes the stated maximum-displacement screen; the failed startup and local-pressure-map comparisons remain disclosed.

The original article SHA-256 remains `e3fe24adad01689b6b5f64748864131187228e73d282ce1297b8009f5d427f17`; the previous ZIP remains `f7bb7d64874712760fa83fa0db2fc5bede7a50f96ad557ad35fdc02862b6a662`.
