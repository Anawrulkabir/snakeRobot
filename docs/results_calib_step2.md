# Calibration step 2: combined setup, full G sweep (run `20261017T111457Z_cc9bd78`)

**Scope.** These are simulation results with an approximate contact model.
Missing physics: cable friction and stretch, servo backlash and speed limits,
print tolerances, and the cause of the α-centred passive force. The segment
masses are placeholders. **5 seeds per G: a screening run.** The step-1
selections behind this setup rest on single successes or noise-sized rate
differences (`decisions.md`, method limitation).

**What was run.** `config/experiments/calib_step2.yaml`, the step-1
selection combined:
- post friction 0.1;
- MG90S 0.2027 N·m;
- 3 s overload rule;
- amplitude ×0.85 (50.6°);
- passive ×4 (0.25956 N·m/rad²).

Medium density, G = 0 … 1.5 × seeds 1001–1005. 35 trials, **0 diverged**,
2.25 CPU-h. Sources: `summary.json`, `trials.jsonl` and `trials.parquet`
in the run folder.

## Pre-registered outcome: **inconclusive**

Successes S(G) out of 5 (`summary.json` `successes_by_G`), with the mean
full-horizon rate (reported only; it does not break ties):

| G | Successes | Rate mean (m/cycle) | Final CoM dx mean (m) | stuck / overload / timeout | Tracking rms (rad) |
|---|---|---|---|---|---|
| 0.0 | 5/5 | 0.1881 | 2.019 | 0 / 0 / 0 | 0.011 |
| 0.25 | 4/5 | 0.1777 | 1.598 | 0 / 0 / 1 | 0.112 |
| 0.5 | 1/5 | 0.0615 | 0.464 | 4 / 0 / 0 | 0.152 |
| 0.75 | 2/5 | 0.0736 | 0.857 | 3 / 0 / 0 | 0.176 |
| 1.0 | 5/5 | 0.1799 | 2.029 | 0 / 0 / 0 | 0.188 |
| 1.25 | 0/5 | 0.0184 | 0.735 | 0 / 0 / 5 | 0.341 |
| 1.5 | 0/5 | 0.0165 | 0.660 | 0 / 0 / 5 | 0.340 |

Applying the rule (`experiments/analyze_calib_step2.py`):
- mid = max(S(0.75), S(1.0)) = max(2, 5) = 5.
- **Mid-G wins?** It needs 5 ≥ S(0) + 2 = 7. **No:** G = 0 also succeeded 5/5.
- **Reversed?** It needs S(0) = 5 ≥ mid + 2 = 7, or S(1.5) = 0 ≥ 7. **No.**
- **→ inconclusive.** Per the rule: stop and report. The combined setup is
  **not** adopted as the calibrated setup for E1.

## Joint-stop contacts (Fahad's item 4)

- **Stop-contact rate per G: 0.000 at every G** (`stop_hit_cycle_fraction`
  and `stop_hit_step_fraction`, mean over 5 trials). No trial in this run
  touched a hard stop.
- So **trials with stop contacts cannot be compared with trials without:**
  all 35 trials fall in the "without" group (`stop_contact_split_all_G`).
- Context: in step 1, stop contacts reached 5–19% of cycles at G = 0.75 in
  the friction 0.1 and overload variants. The combination adds passive ×4 and
  amplitude ×0.85. Either could explain the difference; this run does not
  separate them.

## What the data say

1. **The success pattern is not monotonic in G:** 5, 4, 1, 2, 5, 0, 0
   for G = 0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5.
   - Both G = 0 and G = 1.0 got through every time.
   - G = 0.5 and 0.75 mostly got stuck early, after 11–13 cycles, with rates
     of 0.0001–0.0032 m/cycle in the stuck trials.
   - G = 1.25 and 1.5 never got stuck. They crept forward (0.66–0.74 m mean)
     until the 40-cycle timeout.
2. **This setup does not show the paper's qualitative trend** (intermediate
   best, both ends worse). It also does not show its reverse. With 5 seeds,
   one success is one trial.
3. **No overloads at any G.** With μ = 0.1 and the 3 s rule, the jam
   mechanism that ended the pilot (a post holding joint 2 or 3 at the servo
   cap, `results_E1_pilot.md`) no longer ends trials. The failure mode
   changes to stuck (G 0.5–0.75) and slow creep (G ≥ 1.25).
4. **G = 0 does best at friction 0.1, as in step 1** (now 5/5). This
   supports the logged open question that the compliance benefit may depend
   on body–post friction (`open_lists.md`). It is not evidence for it: 5 seeds,
   one setup.

## What this does not show

- That intermediate compliance helps or does not help: the outcome is
  inconclusive by the pre-registered rule.
- Why G = 0.5 and 0.75 get stuck while G = 1.0 does not. That has not been
  diagnosed, and no further tuning is done without Fahad's approval.
- Anything about a real robot.
