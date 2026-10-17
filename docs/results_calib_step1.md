# Calibration step 1: one assumption at a time (run `20261017T075321Z_dc2fb6c`)

**Scope.** These are simulation results with an approximate contact model.
Missing physics: cable friction and stretch, servo backlash and speed
limits, print tolerances, and the cause of the α-centred passive force. The
segment masses are placeholders. With **5 seeds per cell**, this is a
screening run: one success is one trial.

**What was run.** `config/experiments/calib_step1.yaml`: medium density,
G = 0, 0.75, 1.5 × seeds 1001–1005. There are 9 variants, the baseline plus
one change each, chosen and marked plausible or not **before** the run
(`decisions.md`, "Calibration before E1"). 135 trials, **0 diverged**,
2.64 CPU-h. The run stopped once on a config typo (`progress.md`) and was
resumed; no trial of the affected variant had been written.
Sources: `summary.json` and `trials.jsonl` in the run folder.

**Baseline reproduces the pilot exactly:** 15/15 rows identical
(`baseline_reproduces_pilot.mismatches` = []).

## Results

| Variant | G | Successes | Rate mean (m/cycle) | Final CoM dx mean (m) | stuck / overload / timeout | Tracking rms (rad) |
|---|---|---|---|---|---|---|
| baseline | 0.0 | 0/5 | 0.0078 | 0.313 | 0 / 5 / 0 | 0.046 |
| baseline | 0.75 | 0/5 | 0.0045 | 0.179 | 3 / 2 / 0 | 0.265 |
| baseline | 1.5 | 0/5 | 0.0001 | 0.004 | 5 / 0 / 0 | 0.546 |
| amp_0.85 | 0.0 | 2/5 | 0.0328 | 0.991 | 0 / 3 / 0 | 0.021 |
| amp_0.85 | 0.75 | 0/5 | 0.0063 | 0.250 | 1 / 4 / 0 | 0.256 |
| amp_0.85 | 1.5 | 0/5 | -0.0004 | -0.014 | 5 / 0 / 0 | 0.507 |
| friction_0.1 | 0.0 | 4/5 | 0.2162 | 1.682 | 0 / 1 / 0 | 0.021 |
| friction_0.1 | 0.75 | 1/5 | 0.0619 | 0.503 | 3 / 1 / 0 | 0.262 |
| friction_0.1 | 1.5 | 0/5 | 0.0001 | 0.004 | 5 / 0 / 0 | 0.546 |
| friction_0.2 | 0.0 | 0/5 | 0.0121 | 0.484 | 0 / 5 / 0 | 0.021 |
| friction_0.2 | 0.75 | 0/5 | 0.0041 | 0.164 | 4 / 1 / 0 | 0.266 |
| friction_0.2 | 1.5 | 0/5 | 0.0002 | 0.006 | 5 / 0 / 0 | 0.546 |
| overload_3s | 0.0 | 0/5 | 0.0079 | 0.315 | 0 / 5 / 0 | 0.204 |
| overload_3s | 0.75 | 1/5 | 0.0592 | 0.718 | 3 / 1 / 0 | 0.276 |
| overload_3s | 1.5 | 0/5 | 0.0001 | 0.004 | 5 / 0 / 0 | 0.546 |
| overload_off | 0.0 | 4/5 | 0.1302 | 1.389 | 0 / 0 / 1 | 0.283 |
| overload_off | 0.75 | 2/5 | 0.0985 | 0.854 | 3 / 0 / 0 | 0.275 |
| overload_off | 1.5 | 0/5 | 0.0001 | 0.004 | 5 / 0 / 0 | 0.546 |
| passive_x4 | 0.0 | 0/5 | 0.0076 | 0.306 | 0 / 5 / 0 | 0.043 |
| passive_x4 | 0.75 | 1/5 | 0.0219 | 0.677 | 0 / 4 / 0 | 0.180 |
| passive_x4 | 1.5 | 0/5 | 0.0196 | 0.786 | 2 / 0 / 3 | 0.396 |
| servo_bound_1.0 | 0.0 | 1/5 | 0.0677 | 0.715 | 0 / 4 / 0 | 0.059 |
| servo_bound_1.0 | 0.75 | 0/5 | 0.0044 | 0.177 | 3 / 2 / 0 | 0.265 |
| servo_bound_1.0 | 1.5 | 0/5 | 0.0001 | 0.004 | 5 / 0 / 0 | 0.546 |
| servo_paper_eq | 0.0 | 0/5 | 0.0078 | 0.311 | 0 / 5 / 0 | 0.044 |
| servo_paper_eq | 0.75 | 0/5 | 0.0044 | 0.175 | 3 / 2 / 0 | 0.265 |
| servo_paper_eq | 1.5 | 0/5 | 0.0001 | 0.004 | 5 / 0 / 0 | 0.546 |

## Pre-registered selection for step 2 (automated, `experiments/analyze_calibration.py`)

| Assumption | Chosen | Basis at G = 0.75 (eligible levels only) |
|---|---|---|
| Post friction | **0.1** | 1/5 successes (0.2: 0/5; 0.4: 0/5) |
| Servo torque | **0.2027 N·m (baseline, MG90S)** | no successes; rate 0.0045 vs 0.0044 (paper-eq). The 1.0 N·m bound is not eligible (it had 0/5 here anyway) |
| Overload rule | **3 s** | 1/5 successes. "Off" (2/5) is not eligible |
| Amplitude | **×0.85 (50.6°)** | no successes; rate 0.0063 vs 0.0045 |
| Passive coefficient | **×4 (0.25956 N·m/rad²)** | 1/5 successes |

## What the data say (before step 2)

1. **Post friction is the strongest single lever.** μ = 0.1 took G = 0
   from 0/5 to 4/5 successes, G = 0.75 from 0/5 to 1/5, and G = 1.5 not at
   all. μ = 0.2 gave no successes.
2. **Removing the overload ending changes the most,** but it is not
   eligible: G = 0 4/5, G = 0.75 2/5. Many baseline trials end by overload
   while the body could still get through. The 3 s rule gives part of that
   (G = 0.75 1/5; G = 0 still 0/5).
3. **Torque barely matters below the bound.** The paper-equivalent
   0.2694 N·m changed nothing measurable. The 1.0 N·m bound gave G = 0 1/5.
4. **Passive ×4 is the only lever that moves G = 1.5:** 0.004 → 0.786 m mean
   final displacement, with tracking 0.546 → 0.396 rad. It turns the loose
   body's stall into slow progress (3/5 timeouts), with no successes.
5. **The changes that help most help G = 0 more than G = 0.75**
   (friction 0.1: 4/5 vs 1/5; overload off: 4/5 vs 2/5; amplitude ×0.85:
   2/5 vs 0/5). Passive ×4 is the exception (G = 0: 0/5, G = 0.75: 1/5).
   **This is a warning for step 2:** the combined setup may show the
   *stiffest* body doing best. That is the opposite of the paper's trend. If
   so, the pre-registered rule stops there.
6. Each selection rests on **one success or a small rate difference.** The
   amplitude choice rests on 0.0063 vs 0.0045 m/cycle with no successes. With
   5 seeds this is noise-sized. The rule was fixed in advance and is applied
   as written.
7. Joint-stop contacts reach 5–19% of cycles at G = 0.75 in the variants
   that let trials run longer (friction 0.1, overload 3 s / off). That is
   above the 5% reporting threshold.

## What this does not show

- That any setting reproduces the paper. Step 1 changes one assumption
  at a time; step 2 tests the combination.
- That μ = 0.1 or the 3 s overload rule describe the real robot. They are
  plausible-range choices, to be checked (tilt test; servo stall tolerance).
- Anything about a real robot.

**Step 2 has not been run** (waiting for Fahad).
