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
