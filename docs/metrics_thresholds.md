# Metric thresholds: physical justification (for Fahad's review before E1)

All values live in `config/metrics.yaml` and are **proposals** until Fahad
confirms them.

Reference quantities used below:
- body length L = 0.70 m;
- gait frequency f = 0.125 Hz, so one cycle = 8 s;
- servo stall torque 0.2 N·m;
- free-ground G = 0 displacement: 0.1141 m/cycle (smoke run
  `20261016T181330Z_9fae347`, same gait as E1, no posts);
- dense post spacing: 0.212 m;
- spatial frequency ξ = 0.82 waves per body.

| Threshold | Value | In body lengths, cycles or stall | Physical justification | Source of the value |
|---|---|---|---|---|
| Jam: displacement over the last cycle below | 0.01 m | 0.0143 L per cycle. **8.8%** of free-ground G = 0 progress | At this rate, passing one dense post spacing (0.212 m) takes 21 cycles, effectively stopped. It sits well below any robot making real progress, but above the residual drift of a robot wiggling in place (synthetic test: pinned body with 5 cm sway is flagged) | proposal |
| Jam: must persist for | 3 cycles | 24 s | In one cycle every joint goes through a full bend cycle. A stall lasting 3 full cycles is not a pause tied to one phase of the wave (e.g. a head collision; the paper's buckling events are brief phase pauses, p. 23). A 2-cycle stall is ignored (tested) | proposal |
| Trial ends if stuck for | 10 cycles | 80 s | Copied from the paper: "did not proceed for 10 consecutive gait cycles" (p. 37) | paper |
| Success: head crosses the lattice exit | 1.95 m | 2.79 L | The paper's 2.4 m pegboard scaled by 0.70/0.86. The paper's actual lattice extent is UNKNOWN, so this is my inference | proposal |
| Success: within | 40 cycles | 320 s | Requires ≥ 0.049 m/cycle (0.07 L per cycle), i.e. **43%** of free-ground G = 0 progress. A robot slower than that in the lattice is counted as not successful. That is a choice: lower it and slow runs pass, at higher compute cost | proposal |
| Collision: minimum gap between contacts | 0.05 s | 0.006 cycle | Contact chatter has a ~0.01 s period (~100 Hz, `results_E0.md`), so 0.05 s spans about 5 chatter periods. At free-ground speed (0.0143 m/s) the body moves 0.7 mm in 0.05 s, too little to leave a post and hit it again. So a re-contact this soon is the same collision (tested with a 3 ms flicker) | proposal |
| Overload: torque at ≥ this share of stall | 0.99 | 0.198 N·m | The paper ends a trial when a servo exceeds stall torque (p. 37). Our model caps torque at stall, so "pinned at the cap" is the analogue | proposal |
| Overload: sustained for | 1.0 s | 0.125 cycle | Excludes impact spikes, which last milliseconds. Short against the 8 s cycle, so a joint held at stall through a large part of a bend is flagged | proposal |

Not covered here: the E2 torque statistics (filtered at the servo bandwidth,
`open_lists.md`).
