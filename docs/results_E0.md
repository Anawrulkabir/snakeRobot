# E0 results: flat ground, no posts, stiff body

**Run:** `20261016T170631Z_ef124ae`. Clean git tree at commit `ef124ae`.
Files: `results/E0/20261016T170631Z_ef124ae/summary.json` (committed);
`trials.csv` and `run_info.json` are local. Every number below is copied from
`summary.json` and rounded for reading only.

**Scope.** These are simulation results with an approximate soft-contact
model, about a model, not a robot. Most robot parameters are still
placeholders: segment width, ride height, all masses, friction coefficient,
wheel size, servo gain, cable geometry, and the gait frequency itself
(`run_info.json` → `placeholders`). Missing physics: cable friction and
stretch, servo backlash and speed limits, print tolerances, and the mesh
sleeve's stiffness. **Speeds are provisional.**

## Setup

- Body: stiff. Each joint has a torque-capped position servo (kp placeholder,
  0.2 N·m cap). This stands in for G = 0, not the paper's cable law.
- Gait: paper Eq. 2 with A = 46° and ξ = 0.82 (paper open-environment
  values, not yet scaled; G4).
- Ground: passive wheels with sideways/forward ratio 1.6:1, checked in drag
  test run `20261016T165908Z_dfd51e6`.
- Frequencies 0.125, 0.25 and 0.5 Hz. 10 trials each, seeds 1000–1009 (the
  same seeds at every frequency), with randomized heading, wave phase and
  start offset.
- 6 cycles per trial; the first is discarded; metrics over cycles 1–5.
- Displacement is measured along the mean tail-to-head body axis, sampled at
  whole cycles.

## Results (mean ± 95% CI half-width, n = 10)

**What the CI means.** The ±95% CI reflects *numerical repeatability* across
randomized heading, phase and start position on perfectly uniform flat
ground. It is **not** real-world uncertainty. It contains none of the
uncertainty in the placeholder parameters, the contact model, or
build-to-build variation, which are far larger (see the diagnosis below).

| f (Hz) | forward_disp_per_cycle_m | body lengths / cycle | wave_efficiency_eta | coasting_number | max_tracking_error_deg | torque_peak_Nm | wheel_airborne_fraction |
|---|---|---|---|---|---|---|---|
| 0.125 | 0.1716 ± 0.0001 | 0.2451 | 0.2010 | 0.00055 | 1.76 | 0.0624 | 0.129 |
| 0.25 | 0.1809 ± 0.0001 | 0.2584 | 0.2119 | 0.0023 | 2.01 | 0.0724 | 0.245 |
| 0.5 | 0.1964 ± 0.0002 | 0.2805 | 0.2300 | 0.0100 | 2.57 | 0.0939 | 0.407 |

- Heading drift per cycle: |mean| ≤ 0.0004 rad at every frequency.
- η follows the paper's definition (p. 34). The wavelength is taken as body
  length / ξ. The coasting number follows the paper's definition (p. 62).

## Checks (thresholds in `config/experiments/E0.yaml`, set before the run)

| Check | Result | Threshold | Pass |
|---|---|---|---|
| Moves forward in every trial | yes | — | ✔ |
| Max penetration | 8.96e-05 m | 1e-3 m | ✔ |
| Passive coast: largest step energy rise / initial energy | 5.5e-07 | 1e-6 | ✔ |
| Timestep convergence (0.25 Hz, dt 1 ms vs 0.5 ms, 5 seeds) | max 0.97% | 5% | ✔ |
| Quasi-static: displacement per cycle vs the mean across frequencies | −6.2%, −1.1%, +7.3% | ±10% | ✔ |

## Reading the quasi-static result (needs Fahad's judgment before E1)

The check passes the threshold I set before the run. **But the trend is
systematic, not noise.** Displacement per cycle rises steadily with
frequency, by 14% from 0.125 to 0.5 Hz, while the CIs are about ±0.0001 m.
Three candidate causes:

1. **Inertia.** Unlikely to dominate. The coasting number stays ≤ 0.01. The
   paper puts its robot at ~10⁻³ and treats ~10⁻² as still inertia-free
   (p. 11).
2. **Servo tracking.** The executed shape departs more from the commanded
   one at higher frequency (max error 1.76° → 2.57°).
3. **Contact chatter.** The fraction of time the wheels are off the floor
   rises from 0.129 to 0.407 with frequency (see below).

I have not separated these. A clean test would rerun the three frequencies
with chatter suppressed and with stiffer servos.

## Known model limitation: wheel spin

The tyre skids partly instead of rolling cleanly: its spin is about **53% of
the pure-rolling rate** (G3 follow-up, `decisions.md`). The forward/sideways
force law is the intended 1.6:1 Coulomb law; the wheel's spin is not physical.
**E4 will compare an alternative forward-resistance model** (for example
axle friction, `ground.axle_friction`) to check whether this matters.

## Known artefact: contact chatter

- The whole body bounces on its soft wheel contacts: all 7 wheels touch, or
  none. Peak-to-peak vertical motion is under 0.1 mm, at ~84 Hz.
- The total normal force averages the body weight (ratio 0.9996), but swings
  from 0 to 1.62× weight.
- It barely changes with timestep, solver tolerance, contact damping ratio,
  noslip iterations or wheel shape (cylinder or sphere). A softer contact time
  constant roughly halves it.
- Averages (displacement) converge with timestep. Instantaneous forces, and so
  torque peaks and p95, are suspect.
- Details: `progress.md`, G3 follow-up. **The mechanism is not yet
  identified.**

## What E0 does not show

- Anything about posts or compliance (E1).
- Whether these speeds hold on the real robot: masses, friction and
  frequency are placeholders.
- Torque statistics suitable for servo sizing. The chatter makes peaks
  unreliable, and the stiff servo is not the cable law.

---

## Chatter diagnosis before E1 (Fahad, 2026-10-16)

**Run `20261016T173615Z_5373862`** (`results/diag_chatter/.../summary.json`).
5 seeds (1000–1004) per cell, the same as E0's first five.
Script: `experiments/diag_chatter.py`. Diagnostic only; the approved model is
unchanged.

### 1. Softer contact and stiffer servos (mean over 5 seeds)

| Variant | f (Hz) | forward_disp_per_cycle_m | wheel_airborne_fraction | max_tracking_error_deg | torque_peak_Nm |
|---|---|---|---|---|---|
| baseline | 0.125 | 0.1716 | 0.129 | 1.76 | 0.0624 |
| baseline | 0.25 | 0.1808 | 0.245 | 2.02 | 0.0726 |
| baseline | 0.5 | 0.1964 | 0.407 | 2.56 | 0.0934 |
| soft contact (time const 0.04 s) | 0.125 | 0.1730 | 0.056 | 1.74 | 0.0617 |
| soft contact | 0.25 | 0.1901 | 0.128 | 1.98 | 0.0711 |
| soft contact | 0.5 | 0.2218 | 0.246 | 2.65 | 0.0970 |
| stiff servos (kp 20 N·m/rad) | 0.125 | 0.1642 | 0.136 | 0.28 | 0.1034 |
| stiff servos | 0.25 | 0.1782 | 0.255 | 0.20 | 0.0840 |
| stiff servos | 0.5 | 0.1940 | 0.426 | 0.39 | 0.1273 |

What this shows:

- **Servo tracking does not explain the frequency trend.** Stiffer servos cut
  the tracking error about tenfold, but displacement still rises with
  frequency (+18% from 0.125 to 0.5 Hz, against +14% at baseline).
- **The amount of chatter does not explain it either.** The softer contact
  halves the chatter at every frequency, yet the trend gets *stronger*:
  +28% from 0.125 to 0.5 Hz.
- **The contact model's softness changes the displacement itself:** by up to
  +13% at 0.5 Hz (0.2218 vs 0.1964 m/cycle).
- My inference, untested: the rate dependence comes from the soft contact's
  tangential compliance, which makes friction slightly rate-dependent at
  short timescales, rather than from inertia. Inertia stays unlikely, since
  the coasting number is ≤ 0.01.

### 2. Bounce frequency versus the observed chatter

| Estimate | Value |
|---|---|
| From solref, ω = 1/(d_max·τ), with τ = 0.02 s and d_max = 0.95. **My reading of the MuJoCo docs; not verified (no doc access here).** | 8.4 Hz |
| From static sag, √(g/δ)/2π, δ = 7.6e-05 m | 57.0 Hz |
| Tap test on the resting body (servos holding): overshoots past rest | **0**: critically damped, no ringing; minimum reached at 18 ms |
| Observed gait chatter, dt 1 ms | dominant 99.8 Hz, peak-to-peak 9.5e-05 m |
| Observed gait chatter, dt 0.5 ms | dominant 115.3 Hz, peak-to-peak 3.6e-05 m |
| Observed gait chatter, contact time constant 0.04 s | no chatter peak (dominant 0.5 Hz, the gait's own harmonic) |

- **Correction:** the 84 Hz I reported earlier came from a scratchpad probe
  over a different time window (4–8 s instead of 2–8 s). The spectrum is
  broad, so the exact peak location is not robust. Use the values above.
- **The chatter is not the contact's natural bounce.** The resting contact is
  critically damped and does not ring at all. Neither estimate (8.4 Hz,
  57 Hz) matches the ~100 Hz seen. The chatter's frequency and amplitude
  both shift when the timestep is halved. Together this points to a
  numerical, solver-level limit cycle when contacts carry friction, not to a
  physical resonance.
- The fraction of time airborne is nearly independent of timestep (E0
  probe), so the mechanism is still **not fully identified**.

### 3. Over-constraint test (0.25 Hz)

| Variant | forward_disp_per_cycle_m | wheel_airborne_fraction |
|---|---|---|
| baseline (rigid plane) | 0.1808 | 0.245 |
| roll/pitch springs at each joint (2 N·m/rad) | 0.0903 | 0.205 |
| independent vertical slide per segment (380 N/m) | 0.1010 | 0.210 |

- **Chatter does not disappear** when the wheels are no longer forced onto
  one rigid plane; it only drops slightly. So over-constraint is not its
  cause.
- **Displacement roughly halves.** How vertical load is shared among the
  wheels matters a great deal. My inference, untested: in the rigid-plane
  model every wheel sinks equally, so every wheel carries about the same
  load (the heavy head's weight is spread over all seven). With vertical
  freedom, each wheel carries closer to its own segment's weight. The real
  robot sits somewhere in between, depending on how stiff its joints are out
  of plane.
