# G4 — Cable drive, wave parameters and cable geometry (options for Fahad)

Status: **decided 2026-10-16** (see `decisions.md` G4). Section 4's rule
was replaced by Fahad's CI-of-difference rule with a ±10 pp margin.

Geometry analysis: `scripts/drive_reach.py`, run `20261016T175804Z_162cbe0`
(`results/drive_reach/.../summary.json`). That run is pure geometry from the
paper's Eqs. 3 and S1; there is no simulation in it. Every number below is
copied from it, or derived from it as stated.

Masses are the placeholders in `config/robot.yaml`. Prices are Fahad's earlier
estimate (12 servos ≈ BDT 3,600–4,800, so about BDT 300–400 each). Neither
has been checked.

---

## 1. Cable drive

### What a single shared spool can and cannot do

A shared spool pays out one cable exactly as it takes up the other. So the two
commanded lengths always sum to a constant S, fixed when the cables are
assembled. I checked the paper's Eq. 3 against that constraint (`drive_reach`,
`paper[*].reachable_by_circular_spool`):

| Paper's G | 0 | 0.25 | 0.5 | 0.75 | 1.0 | 1.25 | 1.5 |
|---|---|---|---|---|---|---|---|
| Commanded L_l + L_r constant over the cycle? (A = 53.7°) | no (36.1 mm travel) | no | no | no | **yes** | **yes** | **yes** |

- **G ≥ 1:** both cables stay in Eq. 3's lengthened branch over the whole
  cycle, so L_l,r = S/2 ± l0·α. That is exactly a circular spool with
  effective radius l0. One servo per joint reproduces G ≥ 1 **exactly**, and
  G is set by the assembled cable length S.
  - Shortening the cables below the G = 1 length over-stretches them at
    α = −A: 1 mm shorter gives −0.5 mm of slack, i.e. stretch
    (`spool_l0_shorter_by_1mm_min_slack_mm`). So G = 1 is the stiffest this
    spool can do.
- **G < 1:** Eq. 3 keeps one cable *taut over a range* of angles. A circular
  spool's lengths are straight lines in α, while the exact lengths are
  concave curves. A line can touch such a curve at only one angle, so this
  cannot be reproduced. That rules out the paper's best value, G = 0.75, with
  a circular spool.
- **The stiffest circular spool** (`spool.tight`: a smaller spool, both
  cables taut at α = 0) is a *different* law from any paper G:
  - stiff at α = 0;
  - free from 24.4° to 31.5° when commanded 26.8° (A/2);
  - free from 45.8° to 90° when commanded 53.7° (A).

  So it softens toward the extremes, roughly the reverse of the paper's
  G = 0.75.
- With one servo per joint, G is fixed by the hardware: the cable length and
  the spool shape. It cannot change while the robot runs. **E3 (adaptive
  slack) therefore needs two servos per joint**, or an extra actuator that
  sets the slack.

### Options

| | A. Two servos per joint (paper) | B. One servo, circular shared spool | C. One servo, printed cam spool |
|---|---|---|---|
| Servo count | 12 | 6 | 6 |
| Added mass | +6 × 13.5 g = **+81 g** (306 → 387 g, +26%) | 0 (current model) | 0 (+ cam print) |
| Servo cost (Fahad's estimate) | BDT 3,600–4,800 | BDT 1,800–2,400 | BDT 1,800–2,400 |
| G reachable | **any G ≥ 0, changed in software** | **G ≥ 1 exactly**, fixed by cable length (re-tension by hand to change). Or the "tight" spool law, which is not a paper G | **any single G**, fixed by the cam profile; reprint cams to change |
| E1 sweep possible on hardware | yes | only G ≥ 1 | one G per cam set |
| E3 adaptive slack possible | **yes** | no | no |
| Main risk | mass, cost, wiring | best G may be < 1 | cam design, cable friction on the profile (my inference; not analysed) |

My recommendation **depends on E1, and on whether E3 is a must-have.**

- If E3 is a must-have, A is the only option, whatever E1 shows.
- If E3 is optional, let E1 decide between A and B (see §4).

### Packaging constraint (affects A and B)

A 180° hobby servo can turn its spool only half a turn, so the spool radius
must be at least (cable travel)/π.

| Case (A = 53.7° open / 84.0° dense) | Cable travel | Spool radius on a 180° servo |
|---|---|---|
| A, one fixed G = 0.75 | 54.0 / 85.7 mm | 17.2 / 27.3 mm |
| A, whole sweep G 0–1.5 on one spool | 83.9 / 131.4 mm | 26.7 / 41.8 mm |
| B, circular spool | 56.0 / 87.6 mm | 17.8 / 27.9 mm |

The placeholder segment width is 50 mm (radius 25 mm), so the dense gait and
the full G sweep do not fit with 180° servos. Ways out:

- smaller L_c and L_j: travel scales with √(L_c² + L_j²), but cable tension
  rises;
- continuous or multi-turn servos, as the paper's Dynamixels were;
- a smaller amplitude.

This should be settled in the G4 cable geometry, not later.

---

## 2. Wave parameters scaled to 6 joints

**Rule (proposed).** Keep the paper's body *shape*: the same number of waves
on the body ξ, and the same curvature profile κ(s)·L. The paper shows that
for a jointed body, α ≈ κ·L/N (Eq. S11, p. 61). So keeping κ·L fixed means
scaling the joint amplitude by N_paper/N = 7/6. The ratio of wavelength to
post spacing is then preserved automatically, as long as the lattice is
scaled by body length (L/d unchanged, §3).

| Environment | Paper A (p. 36) | **Proposed A (×7/6)** | ξ (paper, unchanged) |
|---|---|---|---|
| open | 46° | **53.7°** | 0.82 |
| sparse | 48° | **56.0°** | 0.80 |
| medium | 51° | **59.5°** | 0.58 |
| dense | 72° | **84.0°** | 1.02 |

- **Alternative:** keep the paper's joint amplitudes unchanged. The body then
  bends less overall (7/6 less total curvature), and the wavelength-to-spacing
  match is lost.
- **Caveat:** the dense amplitude of 84.0° is close to the ±90° joint stop, so
  at high G the free range is clipped by the stop (`drive_reach` ranges).
  The packaging table above also shows the dense gait is the hardest to fit.
- The temporal frequency is 0.125 Hz for E1 (Fahad).

---

## 3. Cable geometry (proposed)

- **L_c = L_j = 20 mm.** This keeps the paper's 45° anchor geometry
  (L_c = L_j; paper 28 mm, `paper_notes` §1.2) and fits inside the 50 mm
  placeholder width (L_c ≤ 25 mm). R = √(L_c² + L_j²) = 28.3 mm.
- **l0 = 0.5214 mm/deg**: the paper's 0.73 mm/deg scaled by R/R_paper.
  - **Why (physics).** Exact lengths scale with R, and Eq. 3's slack scales
    with l0. With the same anchor angle and the same l0/R, Eq. 3 is identical
    in joint-angle space, so **G = 0.75 here allows the same free joint
    angles as G = 0.75 in the paper.** That keeps E1 comparable to the paper.
  - **Constraint check.** l0 must be at least the largest rate at which an
    exact length changes with angle, 0.4937 mm/deg, so that no cable is ever
    commanded shorter than exact. The same margin as the paper (×1.056) holds.
- Fully passive G for this geometry: **1.696** at A = 53.7°, **1.612** at
  A = 84.0° (paper: 1.74 and 1.64 for its own amplitudes).
- Open: the 50 mm width is still a placeholder. Smaller L_c and L_j would
  shrink the spools (§1, packaging) but raise cable tension, which E2 will
  quantify.

**Proposed lattice for E1** (milestone 4; listed here because the gait scaling
depends on it):

- spacing d = L/(L/d) with L = 0.70 m: sparse 0.389 m, medium 0.250 m, dense
  0.212 m;
- post diameter scaled from the paper's 12.7 cm by 0.70/0.86, giving 10.3 cm;
- whether d is centre-to-centre is UNKNOWN in the paper (`paper_notes` §4);
  I would use centre-to-centre.

---

## 4. Structuring E1 so it answers "6 or 12 servos" (proposed, pre-registered)

**Conditions** (in addition to Fahad's E1 settings: 0.125 Hz, vertical-slide
load model, 50 trials per cell):

- Paper G law (two-servo drive): G = 0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5,
  crossed with open, sparse, medium and dense.
- One extra law per density: the stiffest circular spool (`spool.tight`).
  G ≥ 1 needs no extra runs, since the one-spool drive reproduces those
  exactly.

**Decision rule, fixed now before any data (proposed):** for each lattice
density, let G* be the condition with the best success rate. Displacement per
cycle breaks ties.

- If some one-spool-reachable condition (G ≥ 1, or `spool.tight`) has a 95% CI
  overlapping G*'s, a 6-servo build can match the best fixed compliance in
  that density.
- If G* < 1 and is clearly better (CIs not overlapping) than every
  one-spool-reachable condition in the medium or dense lattice, matching the
  best fixed compliance needs option A, or a cam spool (C).
- **E3 is separate:** adaptive slack needs option A whatever this rule says.

Per Fahad, E1's conclusions are **relative** (the ranking of the compliance
laws), not absolute speeds.
