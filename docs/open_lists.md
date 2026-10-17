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
| **Passive joint stiffness (sleeve)** | `joint.stiffness` (superseded) → `joint.passive_coeff` | 0 → 25% of stall at 45° moved disp/cycle at G = 0.75 from 0.0577 to 0.1018 m and removed tail joint-stop collapse (run `20261016T181938Z_a84cc70`). Now α-centred quadratic, swept in E1b |
| **Passive element (a): friction about the current position** instead of the α-centred spring | not implemented yet | Fahad 2026-10-17: Fig. 5A cannot tell a pose-centred spring from path-dependent friction |
| **Passive element (c): linear law** | `joint.passive_model = linear_alpha`, k_lin 0.03951 N·m/rad friction-scaled | Fahad 2026-10-17 (run `20261017T061904Z_10317fe`) |
| **Body–post friction** | `arena.yaml` lattice.post_friction | Placeholder 0.4; the paper gives none (Fahad 2026-10-16). It does change outcomes (μ 0 vs 0.4: 0.313 vs 0.040 m/cycle in one G = 0 trial, run `20261016T190405Z_c61d84c`) |
| Static vs kinetic body–post friction | `arena.yaml` lattice.post_friction | The tilt test gives static μ at slip onset; the model uses one Coulomb μ |
| Sliding friction μ | `ground.friction_sliding` | Placeholder, UNKNOWN (paper gives only the ratio) |
| Segment mass | `mass.*` | CLAUDE.md §6 E4 |
| Cable stiffness | (implementation B) | CLAUDE.md §6 E4 |
| Servo torque limit | `servo.stall_torque` | CLAUDE.md §6 E4 |
| **Passive element (b): joint breakaway (dry) friction** | `joint.frictionloss` | Fig. 5A starts at 2.02 N at zero deflection in every panel. If that is static friction: 0.1212 N·m on the paper's robot, 0.0233 N·m friction-scaled (run `20261017T061904Z_10317fe`) |

## Hardware validation list (measure on the real robot, compare with the model)

| Measurement | Compares with | Source |
|---|---|---|
| Weigh each part (servo, shell, wheel set, electronics) | `mass.*` placeholders | G3 (Fahad) |
| Drag test: pull a segment forward, then sideways, and record the force | `scripts/drag_test.py` ratio | G3 (Fahad) |
| **Per-wheel load** of the assembled robot (e.g. a kitchen scale under one wheel at a time) | load model: rigid plane vs vertical slide (`results_E0.md`) | Added by Fahad 2026-10-16 |
| **Servo torque sufficiency (MG90S baseline, 0.2027 N·m at 6 V): the 0.2 N·m assumed stall is reached in the lattice and on open floor in simulation.** Confirm the real servo's stall torque, and consider a higher-torque servo (G7) | `servo.stall_torque` | Fahad 2026-10-16 (hardware risk) |
| **A restoring element (sleeve or elastic) is required.** Measure the joint restoring torque vs angle with the cables slack | `joint.stiffness`, `joint.damping` | Fahad 2026-10-16, after the milestone 3 joint-stop finding (`results_M3.md`) |
| **Servo power supply:** about 800 mA peak per servo, so 5–10 A total for 6–12 servos. Size the battery, regulator and wiring for that (Fahad 2026-10-17). The shop warns against continuous stall, which supports the 1 s overload rule in `metrics.yaml` | power electronics | Fahad 2026-10-17 |
| Servo stall torque and speed of the model actually bought | `servo.*` | CLAUDE.md §13, before G7 |

## E2 method notes (to apply when E2 runs)

- **Run E2 at 0.0625 Hz**, where there is less chatter (Fahad 2026-10-16).
- **Low-pass filter the torques at the servo's bandwidth** before taking
  mean, p95 and peak. Contact chatter puts ~100 Hz content into the
  instantaneous forces (`results_E0.md`). The cut-off has to be justified
  from the servo's response, and the unfiltered values reported alongside.
  (Fahad 2026-10-16)
- **Confirm the peaks at a 0.5 ms timestep.** (Fahad 2026-10-16)
- **Torque sufficiency is a hardware risk (Fahad 2026-10-16).** The servos hit
  the 0.2 N·m cap in every compliant setting, even on open floor, and G = 0
  trials overloaded in the medium lattice (run `20261016T190405Z_c61d84c`).
  E2 must state how often and for how long each joint sits at the cap, not
  only peaks.
- Torque-cap sensitivity (run `20261016T191531Z_387fad8`): 0.2 → 0.5 N·m
  changes the progress rate by ≤ 10% in every cell (not triggered). But
  0.2 → 1.0 N·m changes G = 0 in the lattice by +59% through fewer overload
  endings. **The rigid-vs-compliant gap in E1 depends on the servo class
  between ~0.2 and ~1 N·m.**
- Log torques from t = 0. They are currently logged from cycle 1, so a trial
  that overloads in its first cycle reports a peak of 0.

## E1 method notes

- 0.125 Hz. **Before the full sweep:** spot-check one density × one
  compliance at 0.0625 vs 0.125 Hz. If displacement per cycle or success rate
  differs by more than ~3%, stop and report (Fahad 2026-10-16).
- Report conclusions as rankings of compliance values, not absolute speeds
  (Fahad 2026-10-16).
- Conditions: the paper's G sweep (0–1.5) plus the tight-spool law, at
  every density (`g4_options.md` §4).
- **Paired design** (same seeds and poses across G).
  - Primary metric: **full-horizon progress rate** (Fahad 2026-10-17): dx ÷
    cycles elapsed for success; dx ÷ max_cycles for stuck, overload and
    timeout. The old rate (dx ÷ cycles elapsed) is secondary.
  - Equivalence: the paired-difference 95% CI lies within ±15% of the best
    condition's mean rate.
  - Secondary: success at 20/30/40 cycles, and survival curves vs distance
    (`decisions.md`, 2026-10-16). Supersedes the G4 success-rate rule.
- Pilot: 20 paired trials, medium density (`config/experiments/E1_pilot.yaml`,
  seeds 1001–1020, kept apart from the E1 seeds). Then compute the trial count for
  the CI to fit the margin, and the compute estimate, **before** E1.
- Log joint-stop contacts; report if stops are hit in more than ~5% of
  cycles.
- Validation: a 7-joint paper-matched model at one density, full G sweep.
  Its G ranking must match the 6-joint model.

## E1b method notes (Fahad 2026-10-16)

- Passive stiffness × G at the medium and dense densities. Levels: 0, ¼, ½,
  1, 2, 4, 8 × the friction-scaled c_q (run `20261017T061904Z_10317fe`; the
  stall scaling is 0.75× and the absolute 5.2× the friction-scaled value).
  Fahad 2026-10-16 asked for the pilot first: dense only, 20 trials per cell.
- Compute estimate before running: `compute_estimates.md` (26–39 h on
  4 cores, worst case).
- Must not be called an extension until the Goldman-lab full texts are
  checked (`literature_search.md`).

## Open questions (not claims)

- **Compliance benefit vs body–post friction** (Fahad 2026-10-17). In step 1 at
  μ = 0.1, G = 0 succeeded 4/5 against 1/5 at G = 0.75 (run `20261017T075321Z_dc2fb6c`).
  Candidate for a G × friction experiment.

## After E1

- Feasibility of Fahad's single global tensioner (7 servos, G ≥ 1 adaptive):
  cable routing, friction, usefulness given E1.
- After E2: final cable offsets, spool radius and servo type, from measured
  cable tension.
