# Servo choice: fit, mass and torque cap (Fahad 2026-10-17)

**Scope.** Placeholder joint stiffness (0.02 N·m/rad); medium-lattice gait
(A = 59.5°, ξ = 0.58); 0.125 Hz; 6 cycles; seeds 1–3. Simulation with
placeholder masses and contact; mechanics check, not an E1 result.

**Servo data** (`config/servos.yaml`, Fahad's shop listings), at 6 V:
- **MG90S:** 13 g; stall interpolated between 1.8 kg·cm (4.8 V) and
  2.2 kg·cm (6.6 V), giving **0.2027 N·m**; 0.10 s/60°.
- **MG996R:** 55 g; 11 kg·cm at 6 V = **1.0787 N·m**; 0.19 s/60°;
  rotation possibly only ~120°.

## Fit and model mass: run `20261017T054131Z_6dfdcbe`

Segment interior: 46 mm diameter × 56 mm length (50 mm width and 60 mm case,
minus a 2 mm wall, which is a proposal). Servo bodies only: no spools, horns,
wiring or wheel mount.

| Servos per joint | Arrangement | Fits? | Needs width / case length | Body segment mass | Robot mass |
|---|---|---|---|---|---|
| MG90S × 1 | single | yes | 30.0 / 36.5 mm | 38.0 g | 303 g |
| MG90S × 2 | side by side | yes | 37.7 / 36.5 mm | 51.0 g | 381 g |
| MG996R × 1 | single | **marginal** (cross-section diagonal 45.2 mm in a 46 mm bore) | 49.2 / 46.9 mm | 80.0 g | 555 g |
| MG996R × 2 | side by side | **no** | 60.6 / 46.9 mm | 135.0 g | 885 g |

**What the mass changes in the model:**
- segment inertia;
- wheel load, and with it sliding and rolling friction (∝ mass);
- the torque needed to drag the tail sideways;
- post contact forces.

**Spool travel with a ~120° MG996R:** radius ≥ travel / (2π/3). For one fixed
G = 0.75 at A = 53.7° (54 mm of travel, `g4_options.md`), that is ≥ 25.8 mm.
The full G sweep on one spool would need ≥ 40 mm, which cannot fit a 50 mm
body.

## Torque cap with each servo's mass: run `20261017T055642Z_d86fd6e`

Two progress rates are reported:
- **pre-registered:** displacement ÷ cycles elapsed;
- **full-horizon:** for overload or stuck endings, displacement ÷ the full
  6 cycles. See the metric artefact below.

| Servo | Condition | G | rate (pre-reg.) | rate (full-horizon) | time any joint at cap | overload endings | cycles elapsed |
|---|---|---|---|---|---|---|---|
| MG90S × 1 | open | 0 / 0.75 / 1 | 0.1314 / 0.0852 / 0.0846 | same | 0 / 0.026 / 0.026 | 0 / 0 / 0 | 6 |
| MG90S × 1 | medium | 0 | 0.1051 | **0.0417** | 0.081 | **3/3** | 0.9, 3.7, 3.2 |
| MG90S × 1 | medium | 0.75 / 1 | 0.0137 / 0.0128 | same | 0.024 / 0.026 | 0 / 0 | 6 |
| MG90S × 2 | medium | 0 | 0.1278 | **0.0412** | 0.102 | **3/3** | 1.4, 1.8, 4.2 |
| MG90S × 2 | medium | 0.75 / 1 | 0.0177 / 0.0159 | same | 0.032 / 0.034 | 0 / 0 | 6 |
| MG996R × 1 | open | 0 / 0.75 / 1 | 0.1304 / 0.0955 / 0.0952 | same | 0 / 0.001 / 0.001 | 0 / 0 / 0 | 6 |
| MG996R × 1 | medium | 0 | 0.1774 | **0.0696** | 0.075 | **3/3** | 1.3, 2.6, 3.2 |
| MG996R × 1 | medium | 0.75 / 1 | 0.0315 / 0.0173 | same | 0.004 / 0.002 | 0 / 0 | 6 |
| MG996R × 2 (does not fit) | medium | 0 / 0.75 / 1 | 0.1997 / 0.0986 / 0.1292 | 0.0855 / 0.0542 / 0.1160 | 0.086 / 0.054 / 0.054 | 3 / 3 / 2 of 3 | — |

**G = 0 overload rate in the medium lattice: 3/3 for every servo option,**
including the MG996R. In the earlier cap-only check (old masses), 1.0 N·m
overloaded 1/3. The MG996R's extra mass raises the friction loads enough to
reach the higher cap anyway. Open floor: no overloads for any option.

## Metric artefact found: the pre-registered rate rewards early overload

Displacement ÷ cycles *elapsed* gives an overload-ended trial a high rate. In
`diag_torque_cap` (run `20261016T191531Z_387fad8`, `trials.json`):
- cap 0.2 N·m, G = 0, seed 1: overloaded after 0.90 cycles having moved
  0.114 m, so **rate 0.127 m/cycle**;
- seed 2 ran all 6 cycles and moved further (0.241 m), but its **rate is
  0.040**.

That artefact affects every comparison in which overloads differ between
conditions, which is exactly the G = 0 vs compliant comparison.

**Re-reading the torque-cap check with the full-horizon rate** (recomputed
from its `trials.json`), medium lattice, G = 0, caps 0.2 / 0.5 / 1.0 N·m:
**0.0334 / 0.0462 / 0.0953 m/cycle**.
- From 0.2 to 0.5 N·m that is **+38%**, which **crosses Fahad's 10%
  threshold**.
- With the pre-registered rate it was +8.5% (not crossed).
- G ≥ 0.75 rows are unchanged: those trials never ended early.

**So whether the servo choice "affects E1 outcomes" depends on the metric.**
On the pre-registered metric it did not cross the threshold; on the
full-horizon metric it does, for G = 0. Between the two candidate servos
(MG90S × 1 vs MG996R × 1, each with its own mass), the full-horizon rates in
the medium lattice differ by:
- G = 0: 0.0417 → 0.0696 (+67%);
- G = 0.75: 0.0137 → 0.0315 (+130%);
- G = 1: 0.0128 → 0.0173 (+35%).

These are 3 seeds at placeholder stiffness, not yet a ranking.

## Not modelled

- **Servo speed:** the medium gait's peak joint rate is A·2πf ≈ 0.82 rad/s,
  about 0.13 s per 60°. That is within both servos' ratings at the joint,
  but the spool ratio changes it at the servo shaft.
- Rotation range, backlash, and stall heating. The shop warns against
  continuous stall, which supports the 1 s overload rule.
