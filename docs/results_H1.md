# H1 mechanism test: is the mid-G stall a propulsion failure? (run `20261018T071302Z_d73fb14`)

**Scope.** Simulation results with an approximate contact model; combined
step-2 setup (friction 0.1, 3 s overload rule, amplitude ×0.85, passive ×4).
Fresh seeds 1006–1015 × G = 0, 0.5, 0.75, 1.0 × {open floor, medium
lattice}, with the same (medium) gait on both. 80 trials, **0 diverged**. The
rule was pre-registered in `decisions.md` before the run and is applied by
`experiments/analyze_h1.py`. Sources: `summary.json`, `trials.jsonl`,
`trials.parquet`.

## Verdict (pre-registered rule, open floor): **H1 rejected**

| Mid G | "curl-stall" seeds | "no-stall" seeds (within 20% of G = 0 and 1.0) |
|---|---|---|
| 0.5 | 0/10 | **10/10** |
| 0.75 | 0/10 | **10/10** |

By the rule, the mid-G stall **needs the posts**. On open floor, the mid-G
body moves forward at nearly the same rate as G = 0 and G = 1.0.

## Open floor, per seed

Progress p is the full-horizon rate (m/cycle); curl c is in rad; heading
change h is in degrees.

| Seed | G = 0 | G = 0.5 | G = 0.75 | G = 1.0 |
|---|---|---|---|---|
| 1006 | success, p 0.1514, c +0.0000, h +7 | success, p 0.1398, c -0.0003, h +5 | success, p 0.1499, c -0.0003, h +3 | success, p 0.1459, c -0.0028, h +3 |
| 1007 | success, p 0.1492, c +0.0001, h +9 | success, p 0.1367, c +0.0008, h +0 | success, p 0.1460, c -0.0005, h +1 | success, p 0.1415, c +0.0006, h +4 |
| 1008 | success, p 0.1494, c +0.0001, h +6 | success, p 0.1377, c +0.0009, h -0 | success, p 0.1473, c +0.0011, h -3 | success, p 0.1434, c +0.0001, h +3 |
| 1009 | success, p 0.1461, c +0.0000, h +5 | success, p 0.1348, c +0.0003, h -2 | success, p 0.1447, c +0.0003, h -0 | success, p 0.1416, c -0.0024, h +1 |
| 1010 | success, p 0.1477, c +0.0000, h +7 | success, p 0.1387, c -0.0003, h +7 | success, p 0.1486, c -0.0005, h +6 | success, p 0.1446, c -0.0034, h +6 |
| 1011 | success, p 0.1504, c +0.0000, h +8 | success, p 0.1396, c -0.0003, h +7 | success, p 0.1495, c -0.0004, h +6 | success, p 0.1455, c -0.0032, h +5 |
| 1012 | success, p 0.1503, c +0.0000, h +6 | success, p 0.1391, c +0.0005, h -1 | success, p 0.1491, c +0.0007, h -4 | success, p 0.1451, c -0.0004, h +2 |
| 1013 | success, p 0.1496, c -0.0000, h -8 | success, p 0.1396, c +0.0003, h -6 | success, p 0.1490, c +0.0005, h -3 | success, p 0.1456, c +0.0029, h -4 |
| 1014 | success, p 0.1504, c +0.0000, h +10 | success, p 0.1391, c -0.0005, h +6 | success, p 0.1494, c -0.0005, h +5 | success, p 0.1457, c -0.0029, h +4 |
| 1015 | success, p 0.1507, c +0.0000, h +7 | success, p 0.1399, c -0.0003, h +4 | success, p 0.1497, c -0.0004, h +3 | success, p 0.1461, c -0.0027, h +3 |

## Medium lattice, per seed (reported only; not part of the rule)

| Seed | G = 0 | G = 0.5 | G = 0.75 | G = 1.0 |
|---|---|---|---|---|
| 1006 | success, p 0.2816, c -0.0044, h +30 | success, p 0.3007, c -0.0059, h +25 | success, p 0.2020, c +0.0036, h -7 | success, p 0.1078, c -0.0020, h +28 |
| 1007 | success, p 0.3178, c -0.0002, h -9 | timeout, p -0.0358, c -0.0001, h -135 | success, p 0.2209, c +0.0075, h +1 | success, p 0.2937, c -0.0002, h +36 |
| 1008 | success, p 0.2775, c -0.0041, h +20 | success, p 0.1325, c +0.0028, h +3 | stuck, p 0.0030, c -0.0008, h -13 | success, p 0.2753, c +0.0040, h +40 |
| 1009 | success, p 0.2607, c -0.0040, h +40 | success, p 0.3181, c -0.0034, h +35 | success, p 0.3162, c -0.0045, h +39 | success, p 0.3194, c -0.0064, h +36 |
| 1010 | success, p 0.3001, c +0.0002, h +34 | success, p 0.2234, c +0.0038, h +3 | timeout, p -0.0614, c -0.0002, h -154 | success, p 0.3234, c +0.0014, h -11 |
| 1011 | success, p 0.3543, c +0.0002, h +28 | success, p 0.2783, c -0.0055, h +14 | success, p 0.3488, c -0.0067, h +31 | success, p 0.3525, c -0.0079, h +29 |
| 1012 | success, p 0.2837, c -0.0003, h +24 | stuck, p 0.0034, c -0.0003, h -28 | stuck, p 0.0036, c -0.0007, h -18 | success, p 0.2794, c +0.0060, h +36 |
| 1013 | success, p 0.2582, c +0.0044, h -13 | success, p 0.2788, c -0.0003, h +12 | timeout, p -0.0935, c -0.0032, h +162 | success, p 0.2793, c -0.0003, h +14 |
| 1014 | success, p 0.3023, c +0.0002, h +24 | success, p 0.2182, c +0.0013, h -19 | success, p 0.2768, c +0.0024, h -23 | success, p 0.3002, c -0.0063, h +25 |
| 1015 | success, p 0.2478, c -0.0039, h +30 | success, p 0.1983, c -0.0056, h +12 | success, p 0.2810, c -0.0000, h +32 | success, p 0.2204, c -0.0018, h +34 |

- G = 0.0: success 10/10, stuck 0, timeout 0, overload 0.
- G = 0.5: success 8/10, stuck 1, timeout 1, overload 0.
- G = 0.75: success 6/10, stuck 2, timeout 2, overload 0.
- G = 1.0: success 10/10, stuck 0, timeout 0, overload 0.

## Facts worth noting (not interpreted beyond the rule)

- **Open floor:**
  - Every trial succeeded (40/40).
  - Progress was 0.135–0.151 m/cycle across all G.
  - |curl index| ≤ 0.0034 rad (≤ 0.2°) in every open-floor trial.
- **Medium lattice, fresh seeds:**
  - G = 0 and G = 1.0 succeeded 10/10; G = 0.5 succeeded 8/10 and G = 0.75
    6/10.
  - The mid-G failures are stuck endings (seeds 1008, 1012) and timeouts with
    negative progress (seeds 1007, 1010, 1013). The timeouts show body-axis
    changes of −135° to +162°.
  - This is the same pattern as calibration step 2 (5, 4, 1, 2, 5 successes
    for G = 0 … 1.0), on different seeds.
- **Lattice progress was higher than open-floor progress** at the same G for
  most passing trials (about 0.2–0.35 vs about 0.14–0.15 m/cycle). With the
  same gait, the posts added forward speed.
- **Replay pair** (chosen in advance:
  `media/h1_open_seed1006_G0.75_vs_G1.0.gif`): open floor, seed 1006.
  G = 0.75 succeeded in 13.32 cycles and G = 1.0 in 13.80 cycles; both
  replays matched their logs.

## What this does not show

- Whether the in-lattice mid-G failures come from the compliance law's
  simplification or from real post interaction. That is the question for
  implementation B (Fahad, 2026-10-18).
- Anything about a real robot.
