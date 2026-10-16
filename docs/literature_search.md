# Literature searches (CLAUDE.md 9: report what was read and what could not be opened)

## 2026-10-16: Goldman lab 2023–2026, sleeve / passive stiffness (for E1b), and adaptive compliance (for E3)

**Tools.** OpenAlex (search_works, get_work) and web search. arxiv.org is
blocked in this environment, so **no full texts could be opened**; only the
abstracts served by OpenAlex.

**Queries:**
1. OpenAlex: `Goldman limbless robot bilateral cable compliance mechanical intelligence`, 2023–2026. 0 results.
2. OpenAlex: `"mechanical intelligence" (limbless OR snake OR sidewinding OR undulation) robot`, 2023–2026. 6 results.
3. OpenAlex full text: `Goldman (robophysical OR limbless OR undulatory) (compliance OR compliant OR passive OR stiffness OR elastic)`, 2023–2026. 245 results; top 25 screened by title.
4. Web: `Goldman lab cable-driven limbless robot sleeve stiffness passive elasticity generalized compliance 2024 2025`. One relevant hit: an APS March Meeting 2023 abstract, "Compliant cable-driven limbless robot for complex terrain navigation". Not opened; it describes the same robot as Wang et al.

**Goldman-lab works found (cable-driven or compliant limbless):**

| Work | What was read | Sleeve or passive-stiffness value? | Adaptive or feedback compliance? |
|---|---|---|---|
| Wang et al. 2023, *Sci. Robot.*, arXiv 2304.08652 | full text (uploaded) | "weak passive elasticity", **no value** (p. 55) | proposes real-time G selection and local G from sensing as future work (p. 33); tests wave reversal on head collision |
| Kojouharov et al. 2024 ICRA, arXiv 2309.13532 | full text (uploaded) | mesh skin; **no value** | no |
| **Wang et al. 2025 ICRA, "AquaMILR", arXiv 2407.01733** | **abstract only** | not in abstract | **yes: "a real-time body compliance tuning controller based on cable tension feedback"** that "improves the robot's robustness and overall speed in heterogeneous hydrodynamic environments" (aquatic, not terrestrial) |
| Fernandez et al. 2025 ICRA, "AquaMILR+", arXiv 2409.18383 | abstract only | not in abstract | not in abstract |
| Dortilus et al. 2026, "Morphing MILR", arXiv 2607.19714 | abstract only | not in abstract ("programmable passive compliance") | not in abstract |
| Wang et al. 2026, "Three-dimensional hydro-cluttered locomotion by an undulatory robot", arXiv 2606.06829 | abstract only | not in abstract | not in abstract |
| Chong et al. 2023 RSS, "Gait design for limbless obstacle aided locomotion using geometric mechanics" | title only | — | — |
| Conti 2024, *Nat. Rev. Electr. Eng.*, "Controlling limbless locomotors with mechanical intelligence" | title only (closed access) | — | — |

**Could not open:** every arXiv full text above, the APS abstract page, and
Conti 2024.

**Consequences:**
- **E1b (passive stiffness × G):** I found no Goldman-lab study of sleeve or
  passive-stiffness values in what I could read. Four full texts are unread,
  so I **cannot** say none exists. E1b must not be called an extension until
  those full texts are checked.
- **E3 (adaptive slack):** the AquaMILR abstract reports real-time compliance
  tuning from cable-tension feedback, in water. Together with Wang 2023's
  future-work suggestion (p. 33), E3 must be framed as testing a terrestrial,
  lattice version of an approach the same lab has already demonstrated in
  water. The AquaMILR full text is needed to compare its rule with Fahad's.

**To unblock:** Fahad uploads the PDFs of arXiv 2407.01733 (AquaMILR, most
important), 2607.19714, 2606.06829 and 2409.18383.

---

## 2026-10-16 (2): Fahad's four uploads and prior compliance work

### Fahad's uploads: NOT in this container yet

Fahad reported putting AquaMILR (2407.01733), AquaMILR+ (2409.18383), the
3-D hydro-cluttered paper (2606.06829) and Morphing MILR (2607.19714) in
`docs/papers/`. None of them is here: no `docs/papers/` in the cloud
checkout, nothing new on the remote branch, nothing in the upload folder.
**Not yet read in full.** The points below are Fahad's reading, recorded so
they can be checked against the full texts once they arrive.

| Paper | Fahad's reading (unverified by Claude) | Bearing |
|---|---|---|
| AquaMILR (ICRA 2025) | Eq. 4 is a torque-threshold G controller: G = 1 baseline, +0.2 steps when torque passes 30/50/70% of stall, 0.5 s hold | E3: an adaptive-compliance rule already exists (aquatic). Agrees with the abstract read earlier ("real-time body compliance tuning controller based on cable tension feedback") |
| AquaMILR, AquaMILR+, 3-D, Morphing MILR | none reports passive body or sleeve stiffness | E1b |
| 3-D hydro-cluttered (2026) | varies **obstacle** compliance (rigid vs flexible clutter), **not** the body's passive stiffness | E1b: a different variable, so not prior work on body stiffness |
| Morphing MILR (2026) | 70 cm, 6 modules, 0.25 kg per module, 70° joint limit | Reference point (paper_notes §8) |
| (one of the four) | l0 = 0.6 mm/deg (vs 0.73 in Wang 2023) | Reference point (paper_notes §8). Which paper is to be confirmed |

### Prior work Fahad listed: access via OpenAlex

| Work | Found | Access | What the abstract says (relevant parts) |
|---|---|---|---|
| Schiebel, Maisonneuve, Diaz, Rieser, Goldman, "Robophysical Modeling of Bilaterally Activated and Soft Limbless Locomotors", Living Machines 2020, LNCS, pp. 300–311, doi:10.1007/978-3-030-64313-3_29 | yes (W3116103679) | **closed; no abstract in OpenAlex** | — (keywords only: snake robot, limbless locomotion, traveling waves, obstacle crossing) |
| Fu & Li, "Robotic modelling of snake traversing large, smooth obstacles reveals stability benefits of body compliance", R. Soc. Open Sci. 7:191192 (2020), doi:10.1098/rsos.191192 | yes (W3008098823) | open (gold) | "Adding body compliance reduced the robot's roll instability by statistically improving surface contact, without reducing speed" (3-D step climbing, not a lattice) |
| Travers, Whitman, Schiebel, Goldman, Choset, "Shape-Based Compliance in Locomotion", RSS XII (2016), doi:10.15607/rss.2016.xii.020 | yes (W2410605974) | open (gold) | Shape functions linking low-level control to planners in "a compliant control framework that directly controls shape parameters"; robots "feel their way through unknown environments". **Active, feedback compliance** |
| Wang, Whitman, Travers, Choset, "Directional Compliance in Obstacle-Aided Navigation for Snake Robots", ACC 2020, pp. 2458–2463, doi:10.23919/acc45564.2020.9148021 | yes (W3009939932) | open (arXiv 2003.01774; arXiv blocked here) | Joint-force proprioception; "directional compliance which modulates the effective stiffness of the robot so that it conforms to the terrain in some directions and resists in others"; mode switching when "wedged or stuck"; planar peg array. **Feedback directional compliance in a peg array: directly relevant to E3** |
| Justus & Hatton, PRE 2024 | **not found** (keyword, full-text and semantic searches) | — | Needs a title or DOI |

Also surfaced (not on Fahad's list, not Goldman lab):
- Ha 2023, "Robotic Snake Locomotion Exploiting Body Compliance and Uniform Body Tensions", IEEE T-RO, doi:10.1109/tro.2023.3294919 (closed).
- Incekara et al. 2025, "Tendon-Driven Compliant Wheel-Less Snake Robot…", Adv. Intell. Syst., doi:10.1002/aisy.202501183 (open).

Both are possibly relevant to passive body compliance (E1b). Only their
titles were read.

### Consequences (pending full texts)
- **E3:** prior work now includes feedback compliance in a peg array (Wang
  et al. ACC 2020), shape-based compliant control (Travers et al. RSS 2016)
  and torque-threshold G control in water (AquaMILR). E3 is framed as a
  terrestrial-lattice test of compliance tuning, using signals a hobby servo
  can provide. **No novelty claim.**
- **E1b:** no study of passive body stiffness found yet among the Goldman-lab
  papers. Still conditional on reading the four full texts and the two
  papers above.
