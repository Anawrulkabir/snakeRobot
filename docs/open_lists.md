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
| Servo stall torque and speed of the model actually bought | `servo.*` | CLAUDE.md §13, before G7 |

## E2 method notes (to apply when E2 runs)

- **Low-pass filter the torques at the servo's bandwidth** before taking
  mean, p95 and peak. Contact chatter puts ~100 Hz content into the
  instantaneous forces (`results_E0.md`). The cut-off has to be justified
  from the servo's response, and the unfiltered values reported alongside.
  (Fahad 2026-10-16)
- **Confirm the peaks at a 0.5 ms timestep.** (Fahad 2026-10-16)
