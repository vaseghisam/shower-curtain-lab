# Publication editorial review

**Outcome: pass.** The revised manuscript addresses all 18 FIRE passages in the uploaded draft. Its numerical sections continue the earlier physical and mechanical argument. No blocking editorial issue remains.

## Reviewed material and scope

- Manuscript: `article/why-a-shower-curtain-attacks-you.md`.
- Manuscript SHA-256 at review: `3aea75958b97c61a3bc9437fc171ad6f901427e65bd3590a485c21662e66a197`.
- Annotated input: the uploaded `Pasted text(1).txt`.
- Supporting context: `RESULTS.md`, used to check how the prose distinguishes the reported measures and experiments.

This was an independent editorial review under the scientific-writing and moderated-terms instructions. It covered the complete manuscript, rather than the flagged sentences alone. It did not rerun the simulations, verify external references, or inspect finished media; those have separate numerical, scientific, and production reviews.

## The 18 marked passages

| No. | Concern in the annotated draft | Resolution in the revised manuscript | Result |
| --- | --- | --- | --- |
| 1 | Pressure, viscous stresses, direct droplet impact, and support forces were introduced together without a clear order. | The pressure section begins with the rod and material resisting through tension, then states why the first model uses pressure as the sideways load and separates approach from impact and wet adhesion. | Pass |
| 2 | “The remaining question is how the pressure difference arises” did not explain the transition. | The transition asks how falling water makes the pressures unequal before calculating how the sheet yields. | Pass |
| 3 | Air not following water down the drain was difficult to visualize. | Air is described returning around the spray or through curtain openings while water collects and drains below it. The volume statement follows that physical picture. | Pass |
| 4 | Bernoulli's assumptions and the points being compared were too compressed. | A streamline is defined, and the pressure–speed–height comparison is explicitly made along the same streamline under the stated assumptions. | Pass |
| 5 | The limits of inferring pressure from speed needed explanation. | Two equal-height points on one streamline are contrasted with separate currents whose Bernoulli constants may differ. The curtain consequence follows directly. | Pass |
| 6 | The significance of the dynamic-pressure estimate was unclear. | The 0.22 Pa scale is compared with the earlier 0.20 Pa illustrative load, followed immediately by the limits on predicting the actual pressure magnitude and sign. | Pass |
| 7 | “Geometry and boundary conditions” remained abstract. | Walls, openings, and spray position are related to where air accelerates, turns, and returns. | Pass |
| 8 | The transition to vortices did not prepare the force argument. | Turning at constant speed is introduced as motion requiring a force before the centripetal pressure balance appears. | Pass |
| 9 | The vortex animation's viewing direction was ambiguous. | Its caption distinguishes looking along the axis, normal to the curtain, from circular paths lying parallel to the sheet. | Pass |
| 10 | “Heating introduces another way to move the air” announced rather than explained. | Heat transfer from warm droplets is followed through density decrease, rising air, lower replacement flow, and upper outflow. | Pass |
| 11 | The thermal pressure sign above and below the neutral level needed a causal explanation. | Different hydrostatic pressure gradients are traced from equal pressure at the neutral height to inward loading below and possible outward loading above. | Pass |
| 12 | The qualification about cold showers was abrupt. | Cooling and evaporation are connected to density changes, then the momentum-only computational control is explained by suppressing heat transfer and excluding evaporation. | Pass |
| 13 | The transition from airflow to displacement was generic. | The text connects relevant pressure differences to the sheet's resistance before introducing the hanging strip. | Pass |
| 14 | “Informative” did not specify why the small-slope approximation was useful. | The slope of 0.102 is translated into about six degrees, explaining how a long curtain can reach far with a small angular deflection. | Pass |
| 15 | “Clearance” appeared without an immediate plain-language definition. | It is defined as the initial gap between curtain and body before the contact ratio is introduced. | Pass |
| 16 | Crossing a contact boundary was abstract and could be confused with actual motion. | The predicted free equilibrium is compared with the test plane; the next paragraph explains overshoot before giving the dynamic equation. | Pass |
| 17 | The Reynolds and Richardson estimates needed a physical interpretation. | The relative roles of inertia, molecular viscosity, and buoyancy are explained, and the illustrative estimates are separated from computed characteristic values. | Pass |
| 18 | A heading was missing before the numerical setup. | “A specified shower to calculate” introduces geometry, input choices, parameter evidence, approximations, and the four controls. | Pass |

## Continuity of the numerical argument

The final sections retain the mechanism developed earlier. Droplet drag transfers momentum to the gas, sensible cooling transfers heat, and the calculated air pressure is used in the same gravitationally tensioned strip law. The manuscript states that neither a low-pressure patch, vortex strength, nor a neutral pressure level is supplied as an input.

The article reports the inward pressure and displacement results before its numerical qualifications. It then explains why the baseline displacements are smaller than the earlier 18 cm example: the computed load is smaller and nonuniform, and the baseline curtain has an added hem mass. The mechanical law remains unchanged.

The lighter-curtain comparison varies mass and hem weight under the retained load. It connects the reported reach to clearance while stating that the air calculation contains no body and does not update the pressure as the curtain moves. The release animation is introduced as a separate experiment under the computed mean pressure, with its own clock. It is not presented as the curtain's fully coupled shower-startup history.

The parameter study follows these examples and states what was varied. Sampled persistence of inward loading is not described as a probability distribution or a universal result. The numerical qualifications identify the measures used in the article and the unresolved measures, with detailed records placed in the companion package. They do not replace the article's explanatory conclusion.

## Wording and format checks

The opening retains the original scene and the distinction between airflow and sheet mechanics. Definitions precede the equations that require them. The closing paragraphs return to weight, restraint, air passages, and clearance without claiming experimental validation.

The manuscript contains no FIRE markers, obsolete HERE markers, missing-heading placeholders, or previous Medium-hosted media links. Its five figure captions and five animation captions are numbered in their own order of appearance. The mathematical source uses single-line display delimiters; final TK export validation is a separate production check.

The contextual wording review found no unresolved use of the registered broad terms. The molecular viscosity in the droplet Reynolds number is now identified as the molecular **kinematic** viscosity of air, and the Prandtl number is explained. The final science edits also distinguish a refinement screen from an error bound. These changes preserve the surrounding narrative.
