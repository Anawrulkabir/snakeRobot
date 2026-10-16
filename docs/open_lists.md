# Open lists: E4 sensitivity, hardware validation, E2 method

Items are added when a decision or result creates them. Each shows where it
came from.

## E4 sensitivity list (parameters whose effect on the conclusions must be tested)

| Parameter | Config key | Why it is on the list |
|---|---|---|
| Friction anisotropy ratio | `ground.anisotropy_ratio` | G3 follow-up (Fahad). The paper links performance mainly to drag anisotropy (p. 11) |
| Forward-resistance model (rolling friction vs axle friction) | `ground.axle_friction` | The wheel spins at ~53% of its rolling rate under the rolling-friction law (`results_E0.md`) |
| **Contact softness** | `ground.contact_timeconst` | Changed displacement per cycle by up to +13% at 0.5 Hz, and by ~15% at 0.0625–0.125 Hz (diagnosis runs `20261016T173615Z_5373862`, `20261016T174857Z_00f197e`). Added by Fahad 2026-10-16 |
| **Load distribution** | `body.vertical_compliance`, `body.vertical_stiffness`, `body.vertical_damping` | Rigid plane vs vertical slide changed displacement per cycle by about −44% (`results_E0.md`). Added by Fahad 2026-10-16 |
| **Compliance ranking vs contact softness** | `ground.contact_timeconst` 0.02 vs 0.04 s | E1 conclusions are rankings; check that the ranking survives the contact model (Fahad 2026-10-16) |
| **Passive joint stiffness (sleeve)** | `joint.stiffness` | 0 → 25% of stall at 45° moved disp/cycle at G = 0.75 from 0.0577 to 0.1018 m and removed tail joint-stop collapse (run `20261016T181938Z_a84cc70`); paper value UNKNOWN |
| Sliding friction μ | `ground.friction_sliding` | Placeholder, UNKNOWN (paper gives only the ratio) |
| Segment mass | `mass.*` | CLAUDE.md §6 E4 |
| Cable stiffness | (implementation B) | CLAUDE.md §6 E4 |
| Servo torque limit | `servo.stall_torque` | CLAUDE.md §6 E4 |

## Hardware validation list (measure on the real robot, compare with the model)

| Measurement | Compares with | Source |
|---|---|---|
| Weigh each part (servo, shell, wheel set, electronics) | `mass.*` placeholders | G3 (Fahad) |
| Drag test: pull a segment forward, then sideways, and record the force | `scripts/drag_test.py` ratio | G3 (Fahad) |
| **Per-wheel load** of the assembled robot (e.g. a kitchen scale under one wheel at a time) | load model: rigid plane vs vertical slide (`results_E0.md`) | Added by Fahad 2026-10-16 |
| **A restoring element (sleeve or elastic) is required.** Measure the joint restoring torque vs angle with the cables slack | `joint.stiffness`, `joint.damping` | Fahad 2026-10-16, after the milestone 3 joint-stop finding (`results_M3.md`) |
| Servo stall torque and speed of the model actually bought | `servo.*` | CLAUDE.md §13, before G7 |

## E2 method notes (to apply when E2 runs)

- **Run E2 at 0.0625 Hz**, where there is less chatter (Fahad 2026-10-16).
- **Low-pass filter the torques at the servo's bandwidth** before taking
  mean, p95 and peak. Contact chatter puts ~100 Hz content into the
  instantaneous forces (`results_E0.md`). The cut-off has to be justified
  from the servo's response, and the unfiltered values reported alongside.
  (Fahad 2026-10-16)
- **Confirm the peaks at a 0.5 ms timestep.** (Fahad 2026-10-16)

## E1 method notes

- 0.125 Hz. **Before the full sweep:** spot-check one density × one
  compliance at 0.0625 vs 0.125 Hz. If displacement per cycle or success rate
  differs by more than ~3%, stop and report (Fahad 2026-10-16).
- Report conclusions as rankings of compliance values, not absolute speeds
  (Fahad 2026-10-16).
- Conditions: the paper's G sweep (0–1.5) plus the tight-spool law, at
  every density (`g4_options.md` §4).
- Decision rule: 95% CI of the success-rate difference (best condition minus
  best one-spool condition); equivalence margin ±10 pp (`decisions.md` G4).
- Log joint-stop contacts; report if stops are hit in more than ~5% of
  cycles.
- Validation: a 7-joint paper-matched model at one density, full G sweep.
  Its G ranking must match the 6-joint model.

## E1b method notes (Fahad 2026-10-16)

- Passive stiffness × G at the medium and dense densities, with stiffness at
  0, 0.5×, 1× and 2× the paper estimate.
- Compute estimate before running: `compute_estimates.md` (26–39 h on
  4 cores, worst case).
- Must not be called an extension until the Goldman-lab full texts are
  checked (`literature_search.md`).

## After E1

- Feasibility of Fahad's single global tensioner (7 servos, G ≥ 1 adaptive):
  cable routing, friction, usefulness given E1.
- After E2: final cable offsets, spool radius and servo type, from measured
  cable tension.
