# Figure digitizing request (for Fahad, WebPlotDigitizer)

Purpose: estimate the paper's passive restoring stiffness (mesh sleeve plus
joint friction) for E1. Source PDF: arXiv 2304.08652v3.

## Required: Fig. 5A(iii) — PDF page 20, top-right panel ("G = 1.5, α = 15°")

**Why this panel.** With the paper's geometry (L_c = L_j = 28 mm,
l0 = 0.73 mm/deg), the free range at α = 15°, G = 1.5 is the full ±90° for
every amplitude the paper used (46°, 48°, 51°, 72°). So **both cables are
slack over the whole curve**, and the force is the passive restoring force
alone. This holds even though the paper does not say which amplitude A it
used in the force tests (checked with `snake.actuation.free_range`).

- Plot type: 2D (X-Y) Plot.
- X axis calibration: **ζ (°)**. Use the tick labels **−45** (left end) and
  **75** (right end).
- Y axis calibration: **F (N)**. Use the tick labels **2** (bottom) and
  **6** (top).
- **Check point:** the black dot should read about (15°, 2 N).
- **Digitize both curves, as separate datasets:**
  1. the **blue solid** curve;
  2. the **black dashed** curve.

  The caption does not say which is measured and which is a fit, so keep
  them apart.
- Cover both branches: left of the dot down to −45°, right of it up to 75°.
  About 25+ points per branch, denser near the dot, where the slope is
  smallest and matters most.

## Recommended: Fig. 5A(ii) — same page, middle panel ("G = 0.75, α = 15°")

Cross-check. Here the free range at α = 15° is only about [12°, 39–45°],
depending on the unknown A. The right branch from 15° to about 39° should
show the same passive restoring force as panel (iii); beyond that a cable
becomes taut.
- X: **0** and **75**. Y: **2** and **6**.
- Both curves (green solid, black dashed), as separate datasets.

## Optional: Fig. 5A(i) — same page, left panel ("G = 0, α = 15°")

Cables taut on both sides, so the slope gives the cable-plus-servo boundary
stiffness, which our `servo.boundary_stiffness` stands in for.
- X: **0** and **30**. Y: **2** and **6**.
- Both lines (red and black), as separate datasets.

## Not needed for the stiffness: Fig. 5B and Fig. S9 heatmaps

These encode force as colour, which WebPlotDigitizer does not read reliably.
They would only serve as a later check on the free-range boundaries.

## Format

One CSV per curve, two columns `zeta_deg,F_N`, named for example
`fig5A_iii_blue_solid.csv` and `fig5A_iii_black_dashed.csv`. Put them in
`data/digitized/`.

## Planned method (to be applied once the CSVs exist)

1. **Torque from force:** τ = F·r with r = 0.060 m. The pushing stick moved
   on a 60 mm circle centred on the joint axis, pushing at mid-module
   (p. 38). Assumption: the measured force is tangential to that circle.
2. **Fit, per branch,** τ(ζ) = τ₀ + k_p·|ζ − ζ_ref| (plus a quadratic term if
   the residuals are curved).
   - τ₀ captures the **2 N floor**: the colour bar labels it "f_s", which
     the paper never defines (preload, static friction, or the bottom of the
     plotted range).
   - k_p is the passive stiffness.
3. **Rest angle.** If the two branches are symmetric about ζ = α = 15°, the
   restoring element acts about the commanded pose (friction-like). If they
   are symmetric about ζ = 0, it acts about straight (sleeve-like). Our
   `joint.stiffness` assumes about straight; the data decide whether that
   holds.
4. **Scaling to this robot is a decision for Fahad.** The paper's servo
   stalls at 1.4 N·m and ours at 0.2 N·m; the robot's mass is UNKNOWN.
   - (a) use the paper's absolute N·m/rad (same sleeve, smaller robot);
   - (b) keep the same ratio of restoring torque to stall torque.

   The two differ by a factor of 7 (1.4/0.2). Scaling by weight or length is
   impossible without the paper's mass.
5. Every output value is labelled **approximate (digitized from figure)**.
