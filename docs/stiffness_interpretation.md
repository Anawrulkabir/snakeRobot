# Fig. 5A interpretation, before the stiffness estimate (Fahad's item 3, 2026-10-17)

**Data:** `data/digitized/fig5a_*` (extracted from the vector figure
`fig5_v1.pdf`).
**Geometry:** paper L_c = L_j = 28 mm (Eq. S2), l0 = 0.73 mm/deg (p. 57).
**Force-to-torque:** τ = F·r, r = 0.060 m (p. 38). Assumption: the force is
tangential to the 60 mm circle.
**Status:** analysis only. The stiffness estimate has **not** been run.

## Q1: is the rise in panel (iii) (G = 1.5) from the sleeve, the cables, or both?

**Cables: no taut cable within ζ = −32…62°.** The paper does not say which
amplitude A the force tests used. Eq. 3 at α = 15°, G = 1.5 gives a free range
covering [−32°, 62°] for **every A ≥ 26.5°**. The paper's gaits use
A = 46–72°, and its force sweep reached α = ±75°, so the cables are slack over
the whole panel (iii) curve. Free ranges (lower, upper bound), by A:

| A | 15° | 20° | 25° | 30° | ≥ 40° |
|---|---|---|---|---|---|
| free range at α = 15° | (−6.7, 90) | (−17.0, 90) | (−28.6, 90) | (−42.4, 90) | (−90, 90) |

**Not a sleeve pulling toward straight.** A quadratic fit to (iii) gives:
- vertex at **15.23°**, minimum force 1.978 N;
- curvature 0.00349 N/deg², rms residual 0.135 N;
- a V-shape fits worse (rms 0.383 N);
- F(ζ = 0) = 2.45 N.

A spring toward straight would have its minimum at 0°. This one has its
minimum at the commanded (and starting) angle. The authors' heatmaps (Fig. S9B)
show the same: the low-force band follows the diagonal ζ ≈ α for every α
(read by eye from the rendered `figSI_ForceCharacterization`).

**What the rise is (my inference, not stated by the paper):** passive
resistance **centred on the starting pose**. Each test began at the commanded
angle and pushed away from it in one direction (p. 38). Two mechanisms fit:
1. elastic resistance about the pose the joint and sleeve were set to;
2. path-dependent friction (mesh fabric sliding, cable drag in the guides),
   which grows with travel from wherever motion began.

**Only loading curves were published, so the two cannot be told apart from
these data.** They act differently in a gait: (1) is a spring that follows
the commanded angle; (2) dissipates energy, with no preferred angle.

**Panel (ii) cross-check.** The right branch of (ii) (G = 0.75) lies within
**0.3 N** of (iii) all the way to 62° (e.g. 45°: 3.61 vs 3.33 N; 55°: 4.74
vs 4.70 N). Its local slope rises smoothly (0.033 → 0.171 N/deg). But Eq. 3
puts the right cable boundary at 39–49° for any A in 15–90°. **The predicted
cable boundary is not visible in the data.** Either the test conditions
differed from Eq. 3 as published (other A, l0 or cable state), or the boundary
is masked. Unresolved. The left branch of (ii) (0.50 N/deg, 15° → 7°) is much
stiffer than (iii), consistent with a taut cable on that side
(directional compliance).

**Answer:** the rise in (iii) is **not from the cables**. It is passive
resistance centred on the starting pose. Whether that resistance is a
sleeve-like spring about the pose or friction is **undetermined** from the
published data.

## Q2: how does the paper define f_s?

**It doesn't.** "f_s" appears only as a colour-bar label in Fig. 5B and
Fig. S9B: "2 (f_s)" at the bottom and "6 (F_max)" at the top. F_max is
defined in the text: "until the force reaches a maximum value, set as 6 N"
(p. 38). f_s is not defined anywhere in the main text or the Supplementary Methods
(searched the extracted text of arXiv v3). The extracted text of all 22
authors' figure files has no definition either: the label survives only as
"2 ( )", and no "threshold" appears.

The data support Fahad's reading that 2 N is a threshold, not a spring force:
- every panel starts at **2.02 N at zero deflection** (the black dot),
  including (iii), where both cables are slack. A spring gives zero force at
  zero deflection;
- the heatmaps' colour scale is clipped to 2–6 N.

What the threshold *is* cannot be told:
- it could be a recording or contact threshold, carrying no physics;
- or real static friction, which would be a breakaway torque of
  2 N × 0.06 m = **0.12 N·m**.

That matters for us: 0.12 N·m is 60% of the MG90S stall. **Proposal:** fit
stiffness to F − 2.02 N, and keep the offset as a separate, flagged question
(joint dry friction, on the E4 list), not as a spring.

## Q3: panel (i) (G = 0) against our cable-boundary stiffness

| | slope | as joint stiffness (× 0.06 m) |
|---|---|---|
| (i), within ±0.5° of α | 2.94 / 2.87 N/deg (left / right) | **10.1 / 9.9 N·m/rad** |
| (i), whole branch (±2°, to 6 N) | 1.92 / 1.98 N/deg | 6.6 / 6.8 N·m/rad |
| Ours: `servo.boundary_stiffness` | — | **11.459 N·m/rad** |

- Fahad's "about 2 N/deg" matches the whole-branch slope. Near α the slope is
  steeper, about 2.9 N/deg: the curves are concave.
- **Our boundary stiffness is within ~15% of the paper's near-α value, and
  1.7× its whole-branch value**, in absolute N·m/rad. That agreement is a
  coincidence: ours was chosen as "stall at 1° overshoot".
- In the paper, the boundary carried 6 N × 0.06 m = 0.36 N·m (2° overshoot)
  without reaching the 1.4 N·m stall. **Ours saturates at 0.2 N·m after 1°.**
  So the stiffness magnitudes agree, but the cap is about 7× lower.
- Caveat: the measured slope includes every compliance in the test chain:
  cable stretch, pulley, servo position loop, joint play, the fixture and the
  robot arm.

## What this means for the stiffness estimate (decisions for Fahad)

1. **Where the passive element is centred.** Our `joint.stiffness` is a
   spring toward **straight** (MuJoCo springref = 0). The data show
   resistance centred on the **commanded or starting angle**. Options:
   - (a) a spring about the commanded angle α(t) inside the free range;
   - (b) dry plus quadratic friction about the current position;
   - (c) keep the spring toward straight, flagged as contradicted by Fig. 5A.

   The data cannot separate (a) from (b).
2. **Shape.** Quadratic, not linear. Options: fit a linear secant stiffness
   over the gait's typical deflection range, or implement the quadratic law.
3. **The 2 N offset:** threshold (ignore) or static friction (0.12 N·m
   breakaway, on the E4 list).
4. **Scaling to our robot:** as decided (friction ratio primary). The paper's
   magnitude: at 30° from the vertex, ΔF = 3.1 N, i.e. **≈ 0.19 N·m** on
   their 1.4 N·m robot.
