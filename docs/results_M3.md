# Milestone 3: implementation A, smoke test and joint-stop finding

**Scope.** These are simulation results with an approximate contact model.
Placeholders still apply: masses, friction, wheel size, and the free-ground
jam threshold. There are no posts yet. Missing physics: cable friction and
stretch, servo backlash and dynamics, print tolerances, and the sleeve's
stiffness (see below).

## What was built

- `snake/actuation.py`, implementation A:
  - the paper's Eq. 3 cable law;
  - the joint free range from the inverse of Eq. S1, in closed form;
  - a one-sided boundary torque (stiffness 11.459 N·m/rad, i.e. stall after
    1° of overshoot), capped at the 0.2 N·m stall.
- **Boundary damping in implicit form,** using each joint's effective inertia
  1/(M⁻¹)_jj. Applied explicitly it oscillated at 500 Hz at dt = 1 ms,
  because the effective inertias are only 1.3–1.9e-5 kg·m², giving
  c·dt/I = 2.6–3.9 against a stability limit of 2.
- **G4 item 3 confirmed: implementation A is independent of the anchor
  offsets.**
  - Free ranges are identical within 1e-12 when L_c and L_j are scaled ×0.5,
    ×0.75 or ×1.5, with l0 stored as l0/R.
  - A simulated trial with halved offsets matches the baseline within 1e-9 m.
  - To get there, the case length had to be split from the anchor offset. It
    had been coupling the capsule length and inertia to L_j.
- Metrics:
  - jam detection (displacement over the last cycle below threshold for N
    cycles);
  - finish-line crossing;
  - debounced collision count.

  Thresholds are in `config/metrics.yaml` (proposals, to confirm before E1).
- Joint-stop logging: per cycle, and per joint.
- 73 tests, each paired with a planted fault.

## Smoke test: run `20261016T181330Z_9fae347`

Flat ground, no posts, 0.125 Hz, 3 seeds (2000–2002), vertical-slide load
model, G4 gait (A = 53.7°, ξ = 0.82).

| G | forward_disp_per_cycle_m (mean) | jammed | stop_hit_cycle_fraction (max) | max deviation from suggested (°) | torque_peak_Nm |
|---|---|---|---|---|---|
| 0 | 0.1141 | 0/3 | 0.00 | 0.3 | 0.055 |
| 0.25 | 0.0523 | 0/3 | 1.00 | 47.1 | 0.200 |
| 0.5 | 0.0547 | 0/3 | 1.00 | 58.3 | 0.200 |
| 0.75 | 0.0577 | 0/3 | 1.00 | 65.3 | 0.200 |
| 1.0 | 0.0557 | 0/3 | 1.00 | 69.1 | 0.200 |
| 1.25 | 0.0089 | 2/3 | 1.00 | 95.9 | 0.200 |
| 1.5 | −0.0007 | 3/3 | 0.00 | 106.1 | 0.088 |

- Timestep check at G = 0.75 (dt 0.5 ms against 1 ms): +1.3%, +1.8%, +3.5%
  per seed.
- **G4 stop rule triggered.** Joints sit on the 90° stop in **100% of
  cycles** for 0.25 ≤ G ≤ 1.25, far above the ~5% threshold.

## Joint-stop diagnosis: run `20261016T181938Z_a84cc70`

Same setup, G = 0.25, 0.75 and 1.0. Passive joint stiffness is expressed as
its torque at 45°, as a share of the 0.2 N·m stall.

| Variant | G | disp/cycle (m) | cycles on stop | fraction of steps on stop, joints 1→6 | max deviation (°) | torque p95 / peak (N·m) |
|---|---|---|---|---|---|---|
| baseline (k = 0) | 0.25 | 0.0523 | 1.00 | 0, 0, 0, 0, 0.20, 0.16 | 47 | 0.044 / 0.200 |
| baseline | 0.75 | 0.0577 | 1.00 | 0, 0, 0, 0.06, 0.11, 0.01 | 65 | 0.038 / 0.200 |
| baseline | 1.0 | 0.0557 | 1.00 | 0, 0, 0, 0.04, 0.12, 0.01 | 69 | 0.037 / 0.200 |
| stiffness 2% | 0.75 | 0.0536 | 1.00 | 0, 0, 0, 0, 0.09, 0.01 | 65 | 0.041 / 0.200 |
| stiffness 10% | 0.25 | 0.0886 | 0.00 | all 0 | 22 | 0.060 / 0.109 |
| stiffness 10% | 0.75 | 0.0731 | 0.00 | all 0 | 49 | 0.056 / 0.186 |
| stiffness 10% | 1.0 | 0.0660 | 0.00 | all 0 | 52 | 0.055 / 0.182 |
| stiffness 25% | 0.25 | 0.1094 | 0.00 | all 0 | 3 | 0.092 / 0.119 |
| stiffness 25% | 0.75 | 0.1018 | 0.00 | all 0 | 22 | 0.093 / 0.132 |
| stiffness 25% | 1.0 | 0.0955 | 0.00 | all 0 | 27 | 0.092 / 0.129 |
| damping 0.005 only | 0.75 | 0.0568 | 1.00 | 0, 0, 0, 0.01, 0.21, 0.13 | 65 | 0.039 / 0.200 |

**What it shows:**

- **Only the tail joints (4–6) reach the stops.** Joint 5 is the worst.
- **The cause is Eq. 3 itself, combined with zero restoring stiffness.** Once
  the outer cable is in its lengthened branch, the free range often extends
  to the 90° stop. With nothing pulling the joint back toward straight,
  ground friction and inertia carry the light tail joints onto the stop. The
  boundary torque then saturates at stall, which is why the peak torque is
  0.200 N·m.
- **Damping does not help. A weak restoring stiffness does:**
  - 2% of stall at 45° changes nothing;
  - 10% removes every stop contact;
  - 25% also shrinks the effect of G sharply (G = 0.25 → 1.0 spans only
    0.1094 → 0.0955 m/cycle).
- The paper's robot had such a restoring element. Its mesh sleeve "provides
  weak passive elasticity, facilitating a weak but inherent 'potential' for
  the robophysical model to return to the straight posture" (p. 55). Its
  value is not given (`paper_notes.md` §6, UNKNOWN). Our model had it at 0.
- **Implication: the passive joint stiffness is not a detail.** It decides
  whether the tail collapses onto the stops, and how strongly the
  performance depends on G, which is the very trend E1 tests.

## What this does not show

- Anything about lattices: there are no posts yet.
- Absolute speeds: placeholders.
- Whether the tail collapse also happens on a real robot. That depends on its
  real joint friction and any sleeve.
