# Final independent numerical QA assessment

The selected **integrated loads and static responses**, together with a **separate strip response under the calculated mean load**, pass the study's 5% change screen between the medium and fine grids. This supports their use as the primary numerical continuation of the article's equations. Large spray-driven startup excursions and detailed spray pressure maps do not pass that screen and should not support quantitative claims.

Twenty-five executable tests pass in the final recorded run: seventeen authored by the independent numerical QA reviewer and eight accompanying the droplet implementation. The log is `numerics_qa_test_log.txt`. The test suite checks the original uniform-pressure strip formula and mesh order, impermeability, pressure signs and reconstruction, conservative exchange, transport/diffusion operators, structural interfaces and the saved controls. Numerical verification is distinct from experimental validation; no curtain measurements were fitted.

## Accepted observables

All comparisons below use pressure averaged by trapezoidal integration over exactly 10–12 s and the same physical width probes. Percentages use the fine result as denominator. A change below 5% is a sensitivity screen, not a rigorous error bound.

| Observable, medium → fine | Spray | Heat | Both |
|---|---:|---:|---:|
| Mean curtain pressure change | 3.78% | 0.26% | 4.63% |
| Width-mean static bottom displacement change, baseline curtain | 1.28% | 0.95% | 1.36% |
| Largest static displacement at fixed probes, baseline curtain | 2.08% | 0.91% | 3.41% |
| Largest excursion after release under the constant computed mean load | 3.47% | 0.80% | 2.77% |

The baseline curtain has mass per area 0.20 kg/m² and additional hem mass 0.05 kg/m. The fine-grid mean-load release calculation gives largest excursions of **4.62 cm for spray, 3.33 cm for heat, and 7.77 cm for both** at the selected probes. No contact or slope-limit stop occurs in those runs.

This release calculation is a declared prescribed-load experiment: the mean pressure is held constant while the original strip equation evolves from rest. Its structural clock is separate from the airflow clock. It does not claim that a real shower's later pressure remains constant or that the computed airflow boundary follows the moving sheet.

The lighter, unweighted curtain provides a further static comparison without relying on startup traces stopped by the slope limit:

| Fine-grid response, mass per area 0.10 kg/m², no added hem mass | Spray | Heat | Both |
|---|---:|---:|---:|
| Width-mean bottom displacement | 5.20 cm | 3.78 cm | 8.95 cm |
| Largest displacement at fixed probes | 7.45 cm | 4.77 cm | 11.69 cm |
| Largest absolute probe slope | 0.072 | 0.032 | 0.088 |
| Medium-to-fine change in largest probe displacement | 1.99% | 1.24% | 4.64% |

The slopes are comfortably below the specified 0.3 limit. The maximum slope itself is not within a 5% change for every mechanism, so its detailed value should not be presented as equally resolved. The small-slope validity conclusion has substantial margin.

## Observables not accepted at the same accuracy

The peak excursion during the actual simulated startup changes **20.60% for spray and 22.12% for both** between medium and fine grids. Those exact peaks remain unsuitable as primary quantitative results. The heat-only startup peak changes 1.05%.

After interpolation to common curtain coordinates, the 10–12 s mean pressure maps differ in relative L2 norm by **13.31% for spray, 1.89% for heat and 11.10% for both**. Accordingly, convergence of the mean load or a selected displacement must not be generalized to every local pressure or curtain trajectory. The strip equation integrates the pressure distribution and can yield more stable response quantities than the local values.

A 24-to-48-ray comparison passes the 5% screen for the checked spray displacement quantities, but it was performed on the baseline grid. It does not establish joint grid-and-ray convergence for every parameter combination. The parameter screen supports qualitative persistence and conditional model behavior; individual local predictions require the corresponding numerical checks.

## Other numerical risks checked

Reducing the fluid step from 0.004 to 0.002 s changes the baseline startup peak by 0.032%. Using pressure samples every 0.024 s instead of 0.1 s changes that peak by 0.40%, while the final fluid fields are bitwise identical. These checks identify spatial representation, rather than the tested time/output intervals, as the main remaining source of startup sensitivity.

The fine spray run records a maximum conservative nonlinear parcel/gas coupling indicator of 0.0686, below the initial 0.5 cautionary screen. The fully integrated fine runs have maximum advective CFL values of 0.435, 0.116 and 0.423 for spray, heat and both. Fine heat/both calculations completed before the diagnostic-only coupling monitor was added, so they do not have a recorded maximum of that indicator. Their finite bounded temperatures, completed evolution and exchange budgets provide no evidence that another expensive full run is necessary solely for this issue. The indicator is not a stability theorem for the complete integrator.

Pressure differences and normal viscous-stress corrections were independently reconstructed from stored final fields and matched their saved arrays. The source uses paired droplet/gas momentum and sensible heat transfer; blocked faces retain zero normal velocity. A truncated output archive was detected, replaced and followed by an atomic-save correction. The completed control archives pass the independent consistency checks.

For the spray case, translating the fixed curtain plane inward by 5 or 10 cm changes the checked static response quantities modestly. This supports a limited geometry-sensitivity argument. It does not replace a calculation with an actually deforming sheet, and the combined heated case has not received this geometry check.

Detailed values and reproducible independent calculations are in `numerics_qa_results.md`, `numerics_qa_results.json` and `tests/qa_response_checks.py`. The article and the previously delivered package were not revised during this QA work.
