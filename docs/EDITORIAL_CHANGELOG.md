# Editorial changes to the shower-curtain article

The revised manuscript incorporates the numerical study and all 18 highlighted passages in the supplied `Pasted text(1).txt`. The opening, physical progression, pressure sign, analytic vortex, thermal-column argument, and hanging-strip law remain. The previous reduced airflow model and its results have been replaced by the completed droplet-to-air calculations supplied with this package.

The [canonical article](../article/why-a-shower-curtain-attacks-you.md) and the [complete TK export](../why-a-shower-curtain-attacks-you-tk.md) have the same text, apart from punctuation normalization and asset paths. No copy-and-paste parts are required.

## The 18 highlighted passages

| No. | Marked concern in the supplied draft | Revision and location |
| --- | --- | --- |
| 1 | The paragraph beginning “However, the force balance includes more than pressure…” | In **The force acts across the curtain**, identifies tension as the resisting force, separates air pressure from viscous stress and direct water impact, and explains why the initial calculation ends before wet contact. |
| 2 | “The remaining question is how the pressure difference arises.” | Replaced by a transition that names the causal question: how falling water makes pressure on the two sides unequal, before calculating how the sheet yields. |
| 3 | Drainage “without requiring an equal volume of air to follow it.” | In **A spray also moves the air**, explicitly follows the two paths: water drains while the air can circulate above it or pass around the curtain. No disappearing air or volume-matching rule is implied. |
| 4 | Bernoulli's use depends on assumptions and comparison points. | In **Why ‘fast air means low pressure’ is insufficient**, defines a streamline and identifies what is compared along it. |
| 5 | Why faster air does not automatically determine pressure across the curtain. | The same section explains equal-height comparisons along one streamline, then explains why different currents may have different constants. |
| 6 | The meaning of the dynamic-pressure scale. | The 0.22 Pa example is related directly to the earlier 0.20 Pa illustrative load, with magnitude and sign of the actual cross-curtain difference left for the flow calculation. |
| 7 | “The actual difference requires the flow geometry and its boundary conditions.” | Replaced by concrete geometry effects: walls, openings, and spray position determine where air accelerates, turns, and returns; pressure must supply those forces. |
| 8 | Transition from speed to the vortex. | Introduces turning at constant speed as a motion that still needs a force, preparing the centripetal pressure balance in **The vortex inside the shower**. |
| 9 | Ambiguous “perspective parallel to curtain” caption. | Animation 2 specifies that the view looks along the vortex axis, normal to the curtain, while the circular paths lie parallel to the sheet. It remains an analytic example. |
| 10 | “Heating introduces another way to move the air.” | **What changes when the water is hot?** now traces warm droplets → warmer, lighter gas → rising air → exchange through lower and higher openings. |
| 11 | Why heating does not lower pressure everywhere. | Starting from equal pressure at the neutral level, the prose compares the pressure gradients of the two columns and explains inward loading below and outward loading above. |
| 12 | Why a cold shower is not a clean control. | Explains cooling and evaporation as remaining density influences, then specifies the computational control: suppress gas heat transfer and exclude evaporation. |
| 13 | “We can now connect pressure to displacement.” | **How far can a small pressure move the curtain?** now asks how strongly the hanging sheet resists the previously discussed loads. The transition leads directly to gravitational tension. |
| 14 | The small-slope approximation being “informative.” | The 0.102 slope is translated into an approximately six-degree tilt, explaining why a noticeable displacement along a long curtain can still involve a small angle. |
| 15 | Undefined “clearance.” | **When the curtain reaches you** defines clearance as the initial gap between curtain and body before introducing the flat test surface and contact ratio. |
| 16 | One equilibrium reaches contact while the other does not. | The unweighted and weighted static conclusions are stated explicitly, then distinguished from inertia-driven overshoot in the dynamic equation. |
| 17 | What the Reynolds and Richardson estimates imply. | **Joining the water, air, and curtain equations** explains the relative roles of inertia, molecular viscosity, and buoyancy at the chosen scales. The numbers remain illustrative, not computed characteristics of the enclosure. |
| 18 | Missing heading before the numerical setup. | Added **A specified shower to calculate**, followed by **From calculated pressure to inward motion**, **The same airflow, a lighter curtain**, and **How much depends on the chosen inputs?** |

## Integration of the completed calculations

The numerical section now uses explicit Lagrangian water parcels, Schiller–Naumann drag, Ranz–Marshall sensible heat exchange, incompressible Boussinesq airflow, and the original gravitational strip equation. Each equation's role and each new symbol are explained where introduced. The computational controls suppress selected gas exchanges; they are not presented as independently realizable shower devices.

The earlier 18 cm and 11 cm results retain their status as analytic examples under a chosen uniform pressure of 0.20 Pa. The final calculations supply spatially varying pressure instead. With the baseline curtain, the computed loads give width-averaged static hem displacements of 1.82 cm for spray, 1.33 cm for heating, and 3.21 cm for both. The article explains the differences through load magnitude, load position, and hem mass, without changing the earlier mechanical law.

Keeping the same pressure fields while varying the curtain shows why lighter sheets move farther. The light unweighted curtain has width-averaged reaches of 5.20, 3.78, and 8.95 cm; its largest sampled combined reach is 11.69 cm. The clearance discussion is conditional because the airflow contains no bather and the flat air boundary is held fixed.

The release animation solves the dynamic strip equation under the computed 10–12 s mean pressure. Its six-second clock is explicitly separate from the airflow's 0–12 s startup clock. No interpolated curtain poses, hidden pressure scaling, post-contact adhesion, or two-way moving-boundary solution is claimed.

The input study and the concise numerical-scope paragraph state which observables passed the declared grid screen, which detailed startup/map quantities remain unresolved, and which parameter cases were not separately refined. The full technical checks remain in the package's QA reports. The article presents a plausible-input study with no fitted curtain data; it does not claim experimental validation.

## Publication changes

- Replaced outdated remote Medium media links with ten numbered local assets: five figures and five animations.
- Kept analytic demonstrations, calculated airflow, static mechanics, and dynamic release distinct in captions.
- Removed editorial markers, temporary headings, obsolete source-model citations, and previous numerical results.
- Rebuilt the numbered references in order of first appearance, using direct primary-source links.
- Used `Y` for curtain displacement so it does not conflict with the room's `y` coordinate.
- Exported every display equation on one physical line and preserved complete references in the single TK Markdown file.

Independent review is recorded in [PUBLICATION_EDITORIAL_QA.md](PUBLICATION_EDITORIAL_QA.md) and [PUBLICATION_SCIENCE_QA.md](PUBLICATION_SCIENCE_QA.md). Machine preflight and archive checks are recorded separately.
