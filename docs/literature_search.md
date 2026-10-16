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
