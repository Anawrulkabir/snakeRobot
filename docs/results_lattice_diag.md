# Lattice failure diagnosis (before any fix)

**Run `20261016T185419Z_91e48fc`** (`results/diag_lattice/.../summary.json`).
Script: `experiments/diag_lattice.py`.
- 6 cycles per trial, 0.125 Hz, seeds 1–3 per cell.
- Joint stiffness 0.02 N·m/rad, as in the failing smoke trial.
- G4 gaits: medium A = 59.5°, ξ = 0.58; open A = 53.7°, ξ = 0.82.

Simulation of a model with placeholders, approximate contact; **nothing has
been fixed yet.**

The failing smoke trial was seed 1, medium lattice, G = 0.75: after 40 cycles
the head was still at the lattice entry.

## (a) The same gait on open floor

| Gait | G | com_dx_per_cycle_m (seeds 1, 2, 3) | stop-hit cycle fraction |
|---|---|---|---|
| medium gait | 0 | −0.0183, 0.1271, 0.1347 | 0, 0, 0 |
| medium gait | 0.75 | −0.0030, 0.0844, 0.0885 | 0.86 (all) |
| medium gait | 1.0 | −0.0028, 0.0828, 0.0853 | 0.86 (all) |
| open gait | 0 | 0.0243, 0.0797, 0.1032 | 0 |
| open gait | 0.75 | 0.0182, 0.0519, 0.0643 | 0 |
| open gait | 1.0 | 0.0178, 0.0472, 0.0574 | 0 |

- The robot **does** move forward on open floor with the medium gait (seeds
  2 and 3).
- **Seed 1 goes backwards in world x at every G.** For example, its head goes
  from −0.045 to −0.155 m over 6 cycles at G = 0. The cause is in (b).
- With the medium gait (A = 59.5°), joints still reach the 90° stop in 86% of
  cycles at G ≥ 0.75, even with stiffness 0.02. With the open gait
  (A = 53.7°) and the same stiffness, they never do.

## (b) Initial overlap at t = 0 — **BUG FOUND**

50 seeds per density, t = 0 pose only.

| Density | trials starting in contact with a post | max initial penetration | furthest body point at t = 0 |
|---|---|---|---|
| sparse | 0/50 | 0 | x = 0.024 m |
| **medium** | **17/50** | **0.0886 m** | **x = 0.236 m** (inside the lattice) |
| **dense** | **5/50** | **0.0399 m** | x = 0.068 m |

**Cause.** The start pose sets the *head segment's* yaw to the ±15° heading
noise, and puts the head at x = −0.05 m. With these gaits, though, the head
segment's orientation differs strongly from the body's travel axis (tail to
head). At some wave phases the body curls forward of the head, into the
lattice. At others the whole body points well away from +x, which is seed 1's
backward travel in (a). The intended start was the *body axis* pointing
toward the lattice, with the whole body behind the lattice front.

## (c) G = 0, 0.75, 1 in the medium lattice

| G | com_dx_per_cycle_m (seeds 1, 2, 3) | outcome | stop-hit cycle fraction | collisions (6 cycles) | torque peak |
|---|---|---|---|---|---|
| 0 | 0.0049, 0.1111, 0.0377 | timeout, **overload**, timeout | 0 | 22, 13, 23 | 0.2 (cap) |
| 0.75 | −0.0021, 0.0207, 0.0130 | timeout ×3 | 0.86 | 29, 22, 23 | 0.2 |
| 1.0 | 0.0018, 0.0194, 0.0140 | timeout ×3 | 0.86 | 30, 26, 29 | 0.2 |

Even from good starts (seeds 2 and 3), compliant settings progress at only
0.013–0.021 m/cycle in the lattice, against 0.083–0.089 on open floor. Their
tail joints are on the stops in 86% of cycles. G = 0 got further in one seed,
but overloaded a servo.

## (d) Body–post friction and head geometry — **BUG FOUND**

- Setting post friction to 0 gave results **identical to the last digit** to
  post friction 0.3. **The configured post friction has no effect.** MuJoCo
  combines two geoms' friction by taking the larger value. The body capsules
  carry MuJoCo's default sliding friction of 1.0, so the effective body–post
  friction is **1.0**, whatever `arena.yaml` says. (My explanation fits the
  identical outputs, but the default value is from my knowledge of MuJoCo,
  not checked in the docs.)
- Head geometry: the head capsule is rounded at the front, as planned.
  Nothing points to the head shape yet, but (b) and this friction bug have
  to be fixed before it can be judged.

## (e) Does the wave fit the lattice gaps?

Pure geometry of the commanded shape (straight chain of joint pins, averaged
over the cycle).

| Density | lateral extent (peak-to-peak) mean / max | body wavelength (projected) | spacing | gap (spacing − post diameter) | wavelength / spacing (ours) | paper (p. 36) |
|---|---|---|---|---|---|---|
| sparse | 0.225 / 0.241 m | 0.588 m | 0.389 | 0.286 | **1.51** | ~2 |
| medium | 0.234 / 0.275 m | 0.589 m | 0.250 | 0.147 | 2.35 | ~2.2 |
| dense | 0.246 / 0.262 m | 0.384 m | 0.212 | 0.109 | 1.81 | ~1.8 |

- Medium and dense match the paper's wavelength-to-spacing ratio within 7%.
  **Sparse does not:** 1.51 vs ~2. The paper does not say whether its
  "wavelength displayed on the body" is projected or measured along the
  body, so part of this gap may be definitional (UNKNOWN).
- The body sweeps 0.22–0.28 m sideways, against gaps of 0.109–0.286 m. The
  body is 0.05 m wide, so it fits through any gap, but it has to weave across
  2–3 post columns per wave in medium and dense.

## Summary of causes (for the failing smoke trial and beyond)

1. **Start-pose bug (b).** Seed 1 started pointing away from the lattice.
   About 1 in 3 medium starts and 1 in 10 dense starts begin with the body
   inside posts.
2. **Post-friction bug (d).** Effective body–post μ = 1.0 instead of the
   configured value.
3. **Physics:** with these amplitudes and weak passive stiffness, the
   compliant tail joints still hit the stops and the servos sit at the
   torque cap, and lattice progress is slow. Whether that persists with the
   digitized stiffness is the open question.

## Proposed fixes (not applied; for Fahad's approval)

- **Start pose:** rotate the whole commanded shape so its tail-to-head axis
  points along +x (± the heading noise). Then translate it so its front-most
  point sits 5 cm before the lattice front. Add a test that fails on any
  initial post contact.
- **Post friction:** give the posts contact priority, so their configured μ
  is the one used. Add a test that body–post friction changes with the
  config.
- Re-run (a)–(c) after both fixes, before any pilot.

---

## Re-run after both fixes: run `20261016T190405Z_c61d84c` (mechanics check only)

Both fixes applied (commit before `c61d84c`): start pose aimed by the body
axis, and posts given contact priority with body–post μ = 0.4 (placeholder,
Fahad). **Joint stiffness is still the placeholder 0.02 N·m/rad, so the G
ranking below is not interpreted** (Fahad 2026-10-16).

**(b) Start pose fixed.** For sparse, medium and dense (50 seeds each):
- 0 starts in contact with a post;
- maximum initial penetration 0;
- the body's front-most point exactly at −0.05 m.

Tests: `tests/test_trial.py`. The planted old placement produces overlaps.

**(a) Open floor: the seeds now agree.**

| Gait, G | com_dx_per_cycle_m (seeds 1, 2, 3) | stop-hit cycle fraction | torque peak |
|---|---|---|---|
| medium gait, 0 | 0.1367, 0.1316, 0.1268 | 0 | 0.091 |
| medium gait, 0.75 | 0.0875, 0.0879, 0.0826 | 0.86 | **0.2 (cap)** |
| medium gait, 1.0 | 0.0837, 0.0859, 0.0815 | 0.86 | 0.2 |
| open gait, 0 | 0.1113, 0.1102, 0.1094 | 0 | 0.07 |
| open gait, 0.75 | 0.0668, 0.0668, 0.0669 | 0 | **0.2** |
| open gait, 1.0 | 0.0602, 0.0598, 0.0600 | 0 | 0.2 |

**(c) Medium lattice (μ_post = 0.4).**

| G | com_dx_per_cycle_m | outcome | collisions (6 cycles) | stop-hit cycle fraction |
|---|---|---|---|---|
| 0 | 0.1266, 0.0401, 0.0775 | **overload**, timeout, **overload** | 3, 21, 10 | 0 |
| 0.75 | 0.0008, 0.0213, 0.0205 | timeout ×3 | 41, 26, 35 | 0.86 |
| 1.0 | −0.0013, 0.0195, 0.0210 | timeout ×3 | 27, 18, 21 | 0.86 |

The G = 0 seed-1 overload ended within the first cycle. That row reports
`torque_peak_Nm` = 0.0 only because torques are logged from cycle 1 onwards.
**This is a reporting gap: torques must be logged from t = 0** (to fix).

**(d) Post friction now acts.**

| G | μ_post = 0 | μ_post = 0.4 |
|---|---|---|
| 0 | 0.1407, **0.3129**, 0.0839 | 0.1266, 0.0401, 0.0775 |
| 0.75 | 0.0041, 0.0233, 0.0208 | 0.0008, 0.0213, 0.0205 |

Tests: `tests/test_trial.py`. Removing the post priority makes μ = 0.05 and
0.8 give identical results.

**(e) Wavelength-to-spacing ratio, both definitions** (gait unchanged).

| Density | projected wavelength / spacing | arc-length (L/ξ) wavelength / spacing | paper (p. 36) |
|---|---|---|---|
| sparse | 1.51 | **2.25** | ~2 |
| medium | **2.35** | 4.83 | ~2.2 |
| dense | **1.81** | 3.24 | ~1.8 |

Neither definition matches all three densities. Projected wavelength matches
medium and dense; arc-length matches sparse best. The paper's definition
stays UNKNOWN. **No gait change** (Fahad).

## Mechanics observations (not interpretations of G)

- **The torque cap is reached** in every compliant setting, even on open
  floor (G ≥ 0.75, both gaits). In the lattice, two of three G = 0 trials
  ended in overload (≥ 1 s at the 0.2 N·m cap).
- With the medium-lattice gait (A = 59.5°), tail joints reach the 90° stops
  in 86% of cycles at G ≥ 0.75 under the placeholder stiffness. This is to be
  re-checked with the digitized stiffness.
