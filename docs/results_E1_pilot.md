# E1 pilot: medium lattice, 20 paired trials (run `20261017T062232Z_b5aac2a`)

**Scope.** These are simulation results with an approximate contact model.
Missing physics: cable friction and stretch, servo backlash and dynamics
(speed limits), print tolerances, and the cause of the passive α-centred force
(UNKNOWN; modelled as elastic). The body–post friction (0.4) and the
segment masses are placeholders.

**What was run.** `config/experiments/E1_pilot.yaml`: medium density
(L/d = 2.8); gait A = 59.5°, ξ = 0.58, 0.125 Hz; 40-cycle limit; 8 conditions
(paper G 0–1.5 and the tight spool) × seeds 1001–1020, paired (same start
pose and wave phase per seed). MG90S baseline (0.2027 N·m); passive element
quadratic about α, c_q = 0.06489 N·m/rad². Commit `b5aac2a`, clean.
160 trials, **0 diverged**. Sources: `summary.json`,
`summary_overload_diag.json` in the run folder.

## Headline: a floor effect

- **0 successes in 160 trials** (`success_frac_at_cycles` = 0 at 20, 30 and
  40 cycles for every condition).
- Crossing the lattice in 40 cycles needs ≥ 0.049 m/cycle (`metrics.yaml`).
  The highest single-trial full-horizon rate is 0.0127 m/cycle (G = 0.25,
  seed 1009). The highest condition mean of the final CoM displacement is
  0.320 m (G = 0), about 1.5 lattice rows.
- **Overload fraction over all conditions: 0.525** (84/160).
- Because every condition scores near zero, the conditions cannot be ranked
  in a way that means anything. **The equivalence trial count was not
  computed** (Fahad's rule: not while every G has a success rate below ~20%).

| Condition | Rate mean (m/cycle) | 95% CI | Success | stuck / overload / timeout | Final CoM dx mean (m) | Cycles mean | Stop-hit cycle fraction, pooled | Tracking rms (rad) |
|---|---|---|---|---|---|---|---|---|
| G=0.0 | 0.0080 | 0.0075–0.0085 | 0/20 | 0 / 20 / 0 | 0.320 | 3.3 | 0.000 | 0.046 |
| G=0.25 | 0.0073 | 0.0063–0.0083 | 0/20 | 0 / 17 / 3 | 0.292 | 15.8 | 0.957 | 0.169 |
| G=0.5 | 0.0037 | 0.0025–0.0049 | 0/20 | 9 / 6 / 5 | 0.147 | 21.5 | 0.973 | 0.225 |
| G=0.75 | 0.0049 | 0.0037–0.0062 | 0/20 | 10 / 10 / 0 | 0.198 | 7.7 | 0.000 | 0.264 |
| G=1.0 | 0.0054 | 0.0041–0.0068 | 0/20 | 7 / 13 / 0 | 0.218 | 6.1 | 0.000 | 0.281 |
| G=1.25 | 0.0057 | 0.0052–0.0061 | 0/20 | 20 / 0 / 0 | 0.226 | 25.1 | 0.000 | 0.510 |
| G=1.5 | 0.0004 | 0.0002–0.0007 | 0/20 | 20 / 0 / 0 | 0.018 | 11.4 | 0.000 | 0.545 |
| tight_spool | 0.0067 | 0.0058–0.0076 | 0/20 | 2 / 18 / 0 | 0.268 | 5.1 | 0.858 | 0.177 |

## 1. Joint-stop contacts (threshold: 5% of cycles)

- **Per cycle, pooled:** G = 0: 0.000; G = 0.25: 0.957; G = 0.5: 0.973;
  G = 0.75, 1.0, 1.25, 1.5: 0.000; tight spool: 0.858. **The prediction (below
  5%) fails** for G = 0.25, G = 0.5 and the tight spool.
- **Per time step it is small:** a mean `stop_hit_step_fraction` of 0.014
  (G = 0.25), 0.005 (G = 0.5) and 0.009 (tight spool). These are brief touches
  in most cycles, not sustained contact.
- **Which joints:** the rear joints 4–6. A scratch re-run of seed 1001 for
  4 cycles, with no early ending, gave a maximum |ζ| of 90.2–91.7° on joints
  4–6 and a time fraction on the stop of 0.0015–0.012 per joint. Joints 1–3
  never reached the stop. At G < 0.75 the slack side of the free range opens
  to the ±90° stop (Eq. 3 with A = 59.5°), so the rear joints overswing onto
  it. The passive element (0.040 N·m at 45° from α) does not stop that.
  (Scratch script, not a saved run; to be rerun as a logged diagnostic if
  needed.)
- G = 0.75 and 1.0 show 0 in the pilot partly because their trials end early
  (mean 7.7 and 6.1 cycles). The scratch run at G = 0.75 touched the stop on
  joint 6 (time fraction 0.0027).

## 2. Overload diagnosis (`summary_overload_diag.json`)

All 84 overloaded trials were re-run with diagnostic logging. **All 84
reproduced the logged trial exactly** (same ending, same final CoM
displacement and end time).

| Condition | Overloads | Overloading joint (count) | On hard stop | Torque into stop | Adjacent segment on a post (mean fraction of the 1 s window) | Mean distance outside free range |
|---|---|---|---|---|---|---|
| G=0.0 | 20 | j2: 18, j3: 2 | 0/20 | 0/20 | 1.000 | 22.0° |
| G=0.25 | 17 | j2: 15, j3: 2 | 0/17 | 0/17 | 0.999 | 29.1° |
| G=0.5 | 6 | j2: 5, j3: 1 | 0/6 | 0/6 | 1.000 | 29.3° |
| G=0.75 | 10 | j2: 7, j3: 3 | 0/10 | 0/10 | 0.998 | 30.6° |
| G=1.0 | 13 | j2: 12, j3: 1 | 0/13 | 0/13 | 1.000 | 27.7° |
| tight_spool | 18 | j2: 18 | 0/18 | 0/18 | 1.000 | 19.4° |

G = 1.25 and 1.5 had no overloads.

- **Not a hard-stop artefact.** No overloading joint was on its hard stop at
  any time during the overload window. The servo never pushed into a stop.
  In implementation A it cannot: the free range is clipped to ±90°, so the
  boundary torque always points back into the joint's range.
- **Mechanism:** a post holds joint 2 (between segments 1 and 2, behind the
  head) or joint 3 19–31° outside its free range for 1 s. The servo pulls
  back at the cap the whole time, and a segment beside that joint touches a
  post throughout the window. Both sides of the range occur (`n_mostly_past_lower_bound` /
  `upper_bound` in the summary). This is the head region jamming against the
  posts it meets first. The paper ends trials on the same condition (p. 37).
- At G = 0.75 and 1.0 it is the same mechanism with a larger excursion
  (27.7–30.6° outside the range vs 22.0° at G = 0).

## 3. Per-seed paired table (full-horizon rate, m/cycle; S success, J stuck, O overload, T timeout)

| seed | G=0.0 | G=0.25 | G=0.5 | G=0.75 | G=1.0 | G=1.25 | G=1.5 | tight_spool |
|---|---|---|---|---|---|---|---|---|
| 1001 | 0.0072 O | 0.0063 O | 0.0011 T | 0.0061 O | 0.0058 O | 0.0047 J | 0.0009 J | 0.0009 J |
| 1002 | 0.0082 O | 0.0026 T | 0.0028 T | 0.0020 J | 0.0084 O | 0.0059 J | -0.0008 J | 0.0023 J |
| 1003 | 0.0093 O | 0.0093 O | 0.0087 O | 0.0045 J | 0.0091 O | 0.0072 J | 0.0002 J | 0.0088 O |
| 1004 | 0.0081 O | 0.0077 O | 0.0025 J | 0.0092 O | 0.0092 O | 0.0060 J | 0.0005 J | 0.0075 O |
| 1005 | 0.0064 O | 0.0056 O | -0.0000 J | 0.0006 J | 0.0006 J | 0.0036 J | -0.0003 J | 0.0054 O |
| 1006 | 0.0083 O | 0.0072 O | 0.0070 O | 0.0095 O | 0.0069 O | 0.0058 J | 0.0011 J | 0.0073 O |
| 1007 | 0.0085 O | 0.0077 O | 0.0074 O | 0.0073 O | 0.0074 O | 0.0061 J | -0.0001 J | 0.0077 O |
| 1008 | 0.0093 O | 0.0078 O | 0.0024 J | 0.0022 J | 0.0020 J | 0.0064 J | 0.0002 J | 0.0079 O |
| 1009 | 0.0088 O | 0.0127 T | 0.0031 J | 0.0033 J | 0.0037 J | 0.0065 J | 0.0006 J | 0.0082 O |
| 1010 | 0.0073 O | 0.0065 O | 0.0008 J | 0.0015 J | 0.0060 O | 0.0048 J | 0.0010 J | 0.0063 O |
| 1011 | 0.0075 O | 0.0068 O | 0.0022 T | 0.0064 O | 0.0064 O | 0.0051 J | 0.0012 J | 0.0067 O |
| 1012 | 0.0092 O | 0.0083 O | 0.0030 T | 0.0028 J | 0.0082 O | 0.0068 J | 0.0005 J | 0.0085 O |
| 1013 | 0.0077 O | 0.0085 O | 0.0072 O | 0.0092 O | 0.0066 O | 0.0056 J | 0.0009 J | 0.0070 O |
| 1014 | 0.0078 O | 0.0074 O | 0.0019 T | 0.0068 O | 0.0017 J | 0.0055 J | 0.0008 J | 0.0071 O |
| 1015 | 0.0087 O | 0.0091 O | 0.0026 J | 0.0026 J | 0.0016 J | 0.0058 J | -0.0006 J | 0.0074 O |
| 1016 | 0.0066 O | 0.0058 O | 0.0013 J | 0.0058 O | 0.0056 O | 0.0042 J | 0.0007 J | 0.0059 O |
| 1017 | 0.0088 O | 0.0084 O | 0.0028 J | 0.0027 J | 0.0039 J | 0.0068 J | 0.0005 J | 0.0083 O |
| 1018 | 0.0054 O | 0.0055 O | 0.0070 O | 0.0053 O | 0.0010 J | 0.0040 J | 0.0004 J | 0.0055 O |
| 1019 | 0.0078 O | 0.0038 T | 0.0066 O | 0.0069 O | 0.0067 O | 0.0055 J | 0.0004 J | 0.0067 O |
| 1020 | 0.0091 O | 0.0088 O | 0.0031 J | 0.0043 J | 0.0083 O | 0.0069 J | 0.0005 J | 0.0085 O |

Diverged trials: none.

## 4. Overall overload fraction

**0.525** (84/160). By condition: G = 0 20/20, G = 0.25 17/20, tight spool
18/20, G = 1.0 13/20, G = 0.75 10/20, G = 0.5 6/20, G = 1.25 and 1.5 0/20.
Where trials do not overload, they get stuck: G = 1.25 and 1.5 are 20/20
stuck. At G = 1.5 the body barely follows the command (tracking rms 0.545 rad)
and moves 0.018 m on average.

**Plainly: under this setup no G gets through the medium lattice.** Stiff
settings overload within ~2–8 cycles, and loose settings get stuck. Overload
alone does not explain it: the conditions that never overload also fail.
Before E1, the setup needs a calibration (proposal below, **not run**).

## What this does not show

- Nothing about which G is best: with everything at the floor, the ranking is
  noise plus how early each trial stops. The secondary (elapsed) rate puts G = 0 first
  (0.1073 m/cycle) because those trials overload after ~3 cycles. That is the
  artefact the full-horizon metric was adopted to remove.
- Nothing about a real robot.

## Compute

160 trials took 3.88 CPU-h (`summary.json` `total_cpu_s`). The measured cost
is 0.911 CPU-s per simulated second. Wall time was about 1 h on 4 cores,
including one interruption and resume.

## Proposed calibration sweep (Fahad 2026-10-17). NOT RUN; for approval

**Goal:** find which assumption drives the universal failure, and check
that the setup gives the paper's qualitative result (mid-G best) under
paper-like conditions.

- **Conditions:** G = 0, 0.75, 1.5. Seeds 1001–1005, a subset of the pilot,
  so every variant is paired with the pilot baseline.
- **Baseline:** reused from the pilot rows. Those trials reproduce exactly:
  all 84 overload re-runs matched.
- **One change at a time** from the baseline:

| Variant | Change | Baseline value |
|---|---|---|
| friction_0.1 | `lattice.post_friction` 0.1 | 0.4 |
| friction_0.2 | `lattice.post_friction` 0.2 | 0.4 |
| servo_paper_eq | `servo.stall_torque` 0.2694 N·m = paper 1.4 N·m × friction-ratio factor 0.1924 (run `20261017T061904Z_10317fe`) | 0.2027 N·m |
| overload_3s | `overload.min_duration_s` 3.0 | 1.0 |
| overload_off | no overload ending (the cap still limits torque) | 1.0 s |
| amp_0.85 | amplitude 59.5° × 0.85 = 50.6° (ξ unchanged) | 59.5° |

**Compute:** 6 variants × 3 G × 5 seeds = **90 new trials**. Worst case,
every trial runs 40 cycles: 90 × 320 s × 0.911 CPU-s/s = 7.3 CPU-h, about
**1.8 h wall on 4 cores**. Variants that remove overload endings make trials
longer, so expect close to the worst case for those.

**Points for Fahad:**
1. **The paper-equivalent torque is only 33% above the MG90S** under friction
   scaling. If it changes little, that does not rule out torque. Option: add
   a 1.0 N·m bound level, which in the earlier cap check cut G = 0 overloads
   (run `20261016T191531Z_387fad8`).
2. **The listed variants target the overload failure. The loose settings
   fail differently:** G = 1.25 and 1.5 got stuck 20/20 with poor tracking
   (0.51–0.55 rad rms). Only post friction among the listed variants plausibly
   affects that. Option: add one passive-stiffness variant (c_q × 4, inside
   the E1b range) at the same 3 G.
3. **One-at-a-time may never reach success** if two assumptions fail
   together. Option: one combined "paper-like" variant chosen after seeing the
   single-variant results (a second, small step).
