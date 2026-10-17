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

---

## 2026-10-16 (3): the four Goldman-lab full texts, read

Fahad attached the PDFs to the chat; they are not committed (licensing).
Page numbers are PDF pages.

### AquaMILR: Wang, Mankame, Fernandez, Kojouharov, Goldman, ICRA 2025, arXiv 2407.01733v2

- **Robot.** 66 cm, 5 bending joints, Dynamixel 2XL430-W250-T, untethered
  (p. 2). Waterproofed in a "tube-shaped polyethylene plastic sleeve"; no
  stiffness given (p. 2).
- **Same Eq. 3 law, l0 = 0.73 mm/degree** (p. 3). Fully passive at G = 1.75
  (p. 3).
- **Lattice.** 9 cm PVC posts on a **triangular grid with 25 cm spacing**,
  2 m × 2 m (p. 3). Trials start at "a randomly selected position and
  orientation", and end when jammed or through. **Distance travelled is the
  Euclidean start-to-end distance**, and results are plotted as a
  **survival function vs distance travelled** (Fig. 4A, p. 4). This bears on
  Fahad's new primary metric.
- **Quasi-static.** "In the terradynamic regime, locomotion can be assumed
  quasi-static, making performance insensitive to undulation frequency"
  (p. 5). This is a claim about the lab's terrestrial robot, not a
  measurement.
- **Result.** Mid-range G is best in water: G = 1 traversed in all trials;
  G < 0.75 jammed, G > 1 lost propulsion (p. 4).
- **E3-relevant, Eq. 4 (p. 5):**
  G_i(τ) = 1 + 0.2σ(τ_i − 0.3T) + 0.2σ(τ_i − 0.5T) + 0.2σ(τ_i − 0.7T),
  with σ the unit step and T = 1.4 N·m stall. "Once an increase takes place,
  the increased G value will be maintained for 0.5 seconds or until the
  sensed torque drops below the thresholds" (p. 5). Decentralized (per
  joint), with torque estimated from the servo (p. 5). In a random lattice
  at 0.15 Hz: "a 100% successful traverse rate" (p. 5).
  **Fahad's reading: confirmed.**

### AquaMILR+: Fernandez, Wang, Tunnicliffe, Dortilus, Gunnarson, Dabiri, Goldman, ICRA 2025, arXiv 2409.18383v1

- 1 m body, 4 modules and 3 joints. "Single Module: 0.68 kg", "Full 4 Module
  Robot: 6.15 kg" (Table I, p. 2).
- Same Eq. 3 law; l0 is referred to [15] (Wang 2023), no value given (p. 4).
- **Passive inter-module element:** "8.9-cm-diameter PVC flex-duct
  ventilation tubing", 15 cm long, with "spring steel reinforcement", chosen
  for extensibility and constant volume (pp. 2–3). **No stiffness reported.**
- No compliance-tuning controller.

### Three-dimensional hydro-cluttered locomotion: Wang et al. 2026, arXiv 2606.06829v1

- **l0 = 0.6 mm/deg**: "This value provided sufficient slack to create
  measurable passive joint freedom while maintaining reliable cable
  engagement" (Supplementary Text, p. 42).
- **Obstacle compliance, not body stiffness.** It varies the *environment*:
  "open water, floating obstacles, elastic beams, deflecting rigid posts"
  and static rigid posts (pp. 13, 16). It reports "the stiffer the posts, the
  more stable the reaction forces they provide" (p. 15). The robot's own
  passive stiffness is **not** varied or reported. Body compliance is varied
  only through G (pp. 7–9). The modules have a "waterproof flexible
  connection" (p. 7); no stiffness given.
- **Inertia-induced rolling** as a jam-recovery mechanism (abstract, pp. 20–21):
  aquatic, not applicable to our planar robot.

### Morphing MILR: Dortilus, Wang, Tunnicliffe, Fernandez, Goldman, 2026, arXiv 2607.19714v1

- "70 cm Length", "6.5 cm Diameter", "Single Module: 0.25 kg", "Full
  6 Module Robot: 1.5 kg" (spec table, p. 2).
- Bending joint "up to 70 degrees, limited by module self collision" (p. 2).
- Same Eq. 3 law; l0 "derivation and parameter selection comes from [34]"
  (p. 3), no value given. "We only keep compliance active during obstacle…"
  (p. 3): compliance is used selectively.
- In an obstacle field, "the majority of successful runs occurred with G = 1",
  over 20 trials (p. 5).
- No passive body stiffness reported; no compliance-tuning controller.

### Checks against Fahad's points

| Fahad's point | Result |
|---|---|
| 1. AquaMILR Eq. 4: torque-threshold G controller, G = 1 baseline, +0.2 at 30/50/70% stall, 0.5 s hold | **Confirmed** (p. 5). The hold also ends early if the torque drops below the threshold |
| 2. None of the four reports passive body/sleeve stiffness | **Confirmed.** AquaMILR+ does have a passive inter-module element (spring-steel flex duct, pp. 2–3) and the 3-D paper a "flexible connection" (p. 7), but neither gives a value |
| 2. The 3-D paper varies obstacle compliance, not body passive stiffness | **Confirmed** (pp. 13–16) |
| 4. Morphing MILR: 70 cm, 6 modules, 0.25 kg/module, 70° limit | **Confirmed** (p. 2) |
| 4. l0 = 0.6 mm/deg | **Confirmed, but it is from the 3-D paper** (Supplementary Text, p. 42), not Morphing MILR. AquaMILR uses 0.73 (p. 3) |

### Updated consequences

- **E1b:** no Goldman-lab paper among these reports or varies passive body
  stiffness. Two passive inter-module elements exist without values. Fu & Li
  2020 (body compliance and roll stability), Ha 2023 and Incekara 2025 (not
  read beyond the title) remain to be checked. **E1b is not called an
  extension** until those are read.
- **E3:** AquaMILR Eq. 4 is a direct precedent: a per-joint torque-threshold
  G controller, in water. Also related: Wang et al. ACC 2020 (directional
  compliance from joint forces in a peg array) and Travers et al. RSS 2016.
  E3 is framed as a terrestrial-lattice test of compliance tuning with
  hobby-servo signals. **No novelty claim.**
- **Justus & Hatton,** "Optimal gaits for inertia-dominated swimmers with
  passive elastic joints", Phys. Rev. E 109, 034602 (2024), is reference [29]
  of AquaMILR (p. 7). Not yet located in OpenAlex; Fahad to supply it.
