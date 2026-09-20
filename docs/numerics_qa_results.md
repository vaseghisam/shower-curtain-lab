# Independent response and cadence QA

Static responses below use direct cumulative quadrature of the continuum hanging-strip equation under the pressure averaged over 10–12 s. The air boundary remains fixed. These are prescribed-load responses, not a computed final shape with two-way airflow feedback. Static width mean uses the full curtain-face quadrature; static and dynamic maxima concern nine fixed physical width probes.

| Case | Mean pressure (Pa) | Mean static bottom displacement (cm) | Largest static probe displacement (cm) | Largest dynamic probe displacement (cm) |
|---|---:|---:|---:|---:|
| control_spray | 0.030503 | 1.9211 | 2.7159 | 11.5961 |
| control_heat | 0.018941 | 1.3117 | 1.6427 | 1.6969 |
| control_both | 0.048652 | 3.2983 | 3.9359 | 10.9272 |
| grid_medium_spray | 0.027999 | 1.8432 | 2.4349 | 9.3024 |
| grid_fine_spray | 0.026980 | 1.8199 | 2.3852 | 7.7134 |
| grid_medium_heat | 0.018758 | 1.3155 | 1.6541 | 1.7061 |
| grid_fine_heat | 0.018807 | 1.3281 | 1.6693 | 1.7241 |
| grid_medium_both | 0.046495 | 3.2565 | 3.8382 | 8.8842 |
| grid_fine_both | 0.044436 | 3.2127 | 3.9735 | 7.2747 |
| time_half_spray | 0.030479 | 1.9208 | 2.7156 | 11.5924 |
| rays_double_spray | 0.032052 | 2.0346 | 2.8224 | 12.5469 |
| rays_quadruple_spray | 0.031883 | 2.0916 | 2.9642 | 12.2228 |
| qa_cadence_spray | 0.030502 | 1.9211 | 2.7159 | 11.6425 |

The grid, time-step and parcel comparisons use the same physical probe positions. Percentage differences below use the second case as denominator. They are sensitivity measures, not confidence intervals or an experimental validation.

| First → second | Static width mean change | Static probe maximum change | Dynamic peak change |
|---|---:|---:|---:|
| control_spray → grid_medium_spray | 4.228% | 11.543% | 24.657% |
| grid_medium_spray → grid_fine_spray | 1.282% | 2.081% | 20.601% |
| control_heat → grid_medium_heat | 0.289% | 0.689% | 0.538% |
| grid_medium_heat → grid_fine_heat | 0.949% | 0.911% | 1.048% |
| control_both → grid_medium_both | 1.285% | 2.547% | 22.996% |
| grid_medium_both → grid_fine_both | 1.363% | 3.406% | 22.124% |
| control_spray → time_half_spray | 0.016% | 0.010% | 0.032% |
| control_spray → rays_double_spray | 5.576% | 3.774% | 7.578% |
| rays_double_spray → rays_quadruple_spray | 2.729% | 4.784% | 2.652% |

## Saved-pressure cadence

A separate twelve-second run requested a 0.025 s output interval. With a 0.004 s fluid step, the production stride rounding gives an actual interval of 0.024 s. Its final velocity, pressure and temperature fields are bitwise identical to the baseline 0.1 s-output calculation. Only the pressure samples supplied to the structural continuation differ.

| Actual pressure sample interval | Dynamic probe peak (cm) | Change from 0.024 s output |
|---|---:|---:|
| 0.024 s | 11.64246 | 0.0000% |
| 0.048 s | 11.63420 | 0.0710% |
| 0.096 s | 11.60081 | 0.3578% |
| 0.100 s | 11.59612 | 0.3981% |

These cadence comparisons pass the study’s 5% screen for this baseline peak-displacement quantity. They do not establish contact-time accuracy for another case or resolve the separate mesh dependence. No first-contact event or slope-limit event occurred in these baseline cadence comparisons.

## Separate response under the computed mean load

This experiment holds the calculated 10–12 s mean pressure constant and releases an initially vertical strip from rest. The six-second structural clock begins at release. It does not claim that the subsequent bathroom pressure is constant or that the airflow boundary follows the sheet. It tests the original article’s mechanical equation with a load supplied by the airflow calculation.

| Pressure source | Largest release excursion at fixed probes | Contact or slope-limit stop |
|---|---:|---|
| grid_medium_spray | 4.77702 cm | No |
| grid_fine_spray | 4.61678 cm | No |
| grid_medium_heat | 3.30813 cm | No |
| grid_fine_heat | 3.33493 cm | No |
| grid_medium_both | 7.55383 cm | No |
| grid_fine_both | 7.76874 cm | No |

For spray, the maximum release excursion changes by 3.471% between the medium and fine pressure fields and passes the 5% screen. Individual probe excursions can differ more; this does not establish convergence of every local curtain trajectory.

For heat, the maximum release excursion changes by 0.804% between the medium and fine pressure fields and passes the 5% screen. Individual probe excursions can differ more; this does not establish convergence of every local curtain trajectory.

For both, the maximum release excursion changes by 2.766% between the medium and fine pressure fields and passes the 5% screen. Individual probe excursions can differ more; this does not establish convergence of every local curtain trajectory.

For spray, the mean pressure maps themselves differ by 13.31% in the stated interpolated L2 comparison, with a largest local difference of 0.03071 Pa. The complete local pressure map does not pass a 5% screen. The strip’s spatial integration can yield a more stable displacement observable than the local pressure values.

For heat, the mean pressure maps themselves differ by 1.89% in the stated interpolated L2 comparison, with a largest local difference of 0.00480 Pa. The complete local pressure map passes a 5% screen. The strip’s spatial integration can yield a more stable displacement observable than the local pressure values.

For both, the mean pressure maps themselves differ by 11.10% in the stated interpolated L2 comparison, with a largest local difference of 0.03002 Pa. The complete local pressure map does not pass a 5% screen. The strip’s spatial integration can yield a more stable displacement observable than the local pressure values.

## Light curtain without an added hem mass

The same computed mean pressures are applied to the static equation with mass per area 0.10 kg/m² and no added hem mass. The finite hem-slope limit is included explicitly. These responses use the fixed airflow geometry and are not inferred from startup trajectories stopped by the slope limit.

| Pressure source | Width-mean bottom displacement (cm) | Largest fixed-probe displacement (cm) | Largest absolute probe slope |
|---|---:|---:|---:|
| grid_medium_spray | 5.21980 | 7.29783 | 0.06279 |
| grid_fine_spray | 5.20361 | 7.44599 | 0.07175 |
| grid_medium_heat | 3.73007 | 4.71150 | 0.03009 |
| grid_fine_heat | 3.78041 | 4.77076 | 0.03185 |
| grid_medium_both | 9.02918 | 11.14416 | 0.08863 |
| grid_fine_both | 8.95345 | 11.68598 | 0.08767 |

For spray, medium-to-fine changes are 0.311% in width-mean bottom displacement, 1.990% in largest fixed-probe displacement and 12.487% in largest absolute probe slope.

For heat, medium-to-fine changes are 1.332% in width-mean bottom displacement, 1.242% in largest fixed-probe displacement and 5.508% in largest absolute probe slope.

For both, medium-to-fine changes are 0.846% in width-mean bottom displacement, 4.637% in largest fixed-probe displacement and 1.089% in largest absolute probe slope.

Reproduce this independent analysis with `python -m tests.qa_response_checks`. The calculation uses the data files currently present and records their names above; a missing fine-grid case is not treated as an accepted refinement. Input and source ranges are assessed in the separate physics review.
