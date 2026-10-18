# G6 diagnosis: stuck mid-G trials (run `20261018T063335Z_f5c3592`)

**Scope.** Simulation results with an approximate contact model; combined
step-2 setup (friction 0.1, 3 s overload rule, amplitude ×0.85, passive ×4).
Criteria pre-registered in `decisions.md` ("G6: diagnose the stuck mid-G
trials") **before** any diagnostic data; applied by
`experiments/diag_stuck.py`. 23 trials: the 7 stuck trials and 8 comparison
trials replayed from step-2 run `20261017T111457Z_cc9bd78` (each matched its
log exactly), plus 8 narrow-band trials at G = 0.6/0.7 (diagnostic only).

## Verdict (pre-registered rule): **unclear** → stop, no recommendation from the criteria

- All 7 stuck trials classify as **"artefact"**, via **A1** (stuck joint at
  its slack-range boundary with no post contact on its neighbours), with no
  jamming criterion met.
- But **A1 fails the discrimination check:** it is also met in **3 of the 8
  passing comparison trials** (allowed: ≤ 1). By the rule, a classification
  resting on a non-discriminating criterion does not count → **unclear**.

## Per trial (stall window = last 10 cycles; comparison = whole trial)

| Trial | Ending | Stuck joint | mean \|τ\| (N·m) | J1 | J2 | J3 | A1: at boundary / neighbour contact | A2 | A3 | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| G=0.5|1002 | stuck (13.5 cyc) | 3 | 0.038 | 0.00 | 0.00 | 0.43 | 0.83 / 0.00 ✔ | 0.00 | ✔ | artefact |
| G=0.5|1003 | stuck (11.6 cyc) | 3 | 0.038 | 0.00 | 0.00 | 0.42 | 0.83 / 0.00 ✔ | 0.00 | – | artefact |
| G=0.5|1004 | stuck (13.0 cyc) | 3 | 0.038 | 0.00 | 0.00 | 0.53 ✔ | 0.82 / 0.00 ✔ | 0.00 | – | artefact |
| G=0.5|1005 | stuck (11.1 cyc) | 3 | 0.038 | 0.00 | 0.00 | 0.42 | 0.83 / 0.00 ✔ | 0.00 | ✔ | artefact |
| G=0.75|1002 | stuck (12.2 cyc) | 3 | 0.033 | 0.00 | 0.00 | 0.61 ✔ | 0.77 / 0.00 ✔ | 0.00 | ✔ | artefact |
| G=0.75|1003 | stuck (11.5 cyc) | 3 | 0.033 | 0.00 | 0.00 | 0.44 | 0.77 / 0.00 ✔ | 0.00 | – | artefact |
| G=0.75|1005 | stuck (11.2 cyc) | 3 | 0.033 | 0.00 | 0.00 | 0.44 | 0.77 / 0.00 ✔ | 0.00 | ✔ | artefact |
| G=0.0|1002 (comparison) | success (6.0 cyc) | 3 | 0.069 | 0.30 | 0.00 | 0.75 ✔ | 1.00 / 0.26 | 0.00 | n/a | — |
| G=0.0|1003 (comparison) | success (10.5 cyc) | 3 | 0.064 | 0.16 | 0.01 | 0.48 | 1.00 / 0.14 | 0.00 | n/a | — |
| G=0.0|1004 (comparison) | success (29.6 cyc) | 3 | 0.053 | 0.00 | 0.00 | 0.10 | 1.00 / 0.01 ✔ | 0.00 | n/a | — |
| G=0.0|1005 (comparison) | success (7.6 cyc) | 3 | 0.066 | 0.24 | 0.00 | 0.69 ✔ | 1.00 / 0.20 | 0.00 | n/a | — |
| G=1.0|1002 (comparison) | success (7.5 cyc) | 3 | 0.033 | 0.33 | 0.00 | 0.74 ✔ | 0.74 / 0.19 | 0.00 | n/a | — |
| G=1.0|1003 (comparison) | success (9.4 cyc) | 3 | 0.032 | 0.27 | 0.00 | 0.64 ✔ | 0.75 / 0.16 | 0.00 | n/a | — |
| G=1.0|1004 (comparison) | success (35.8 cyc) | 3 | 0.030 | 0.00 | 0.00 | 0.13 | 0.73 / 0.01 ✔ | 0.00 | n/a | — |
| G=1.0|1005 (comparison) | success (39.6 cyc) | 3 | 0.030 | 0.00 | 0.00 | 0.17 | 0.73 / 0.01 ✔ | 0.00 | n/a | — |

✔ = criterion met at its pre-registered threshold. Fractions are shares of the window.

## Discrimination check (met in ≥ 5/7 stuck and ≤ 1/8 comparison)

| Criterion | Stuck met | Comparison met | Discriminates |
|---|---|---|---|
| J1 | 0/7 | 0/8 | no |
| J2 | 0/7 | 0/8 | no |
| J3 | 2/7 | 4/8 | no |
| A1 | 7/7 | 3/8 | no |
| A2 | 0/7 | 0/8 | no |
| A3 | 4/7 | n/a | n/a (cross-G by design) |

## Outcomes per seed and G (A3 and the narrow band)

| Seed | G = 0.0 | G = 0.25 | G = 0.5 | G = 0.6 | G = 0.7 | G = 0.75 | G = 1.0 | G = 1.25 | G = 1.5 |
|---|---|---|---|---|---|---|---|---|---|
| 1002 | success | timeout | stuck | stuck | stuck | stuck | success | timeout | timeout |
| 1003 | success | success | stuck | success | stuck | stuck | success | timeout | timeout |
| 1004 | success | success | stuck | success | success | success | success | timeout | timeout |
| 1005 | success | success | stuck | stuck | stuck | stuck | success | timeout | timeout |

G = 0.6 and 0.7 are fresh diagnostic runs; all other cells are step-2 outcomes.
A3 (Claude's reading: stall persists at 0.6 **and** 0.7, absent at 0 and 1.0)
holds for seeds 1002 and 1005, not for 1003 (passes at 0.6) or 1004 (passes at
0.6 and 0.7). Under either reading the band effect is seed-dependent.

## What the numbers say (facts, not a verdict)

1. **No jamming sign in any stuck trial.** J1 = J2 = 0.00 in all 7: no
   posts on both sides, no torque pushing a neighbour into a post. J3 (the
   commanded shape overlaps a post) is met in 2/7 stuck trials and in 4/8
   passing trials, so it does not separate them.
2. **The stuck joint is joint 3 in every trial, stuck and passing.** Its mean
   torque in the stall window is 0.033–0.038 N·m (16–19% of the 0.2027 N·m
   stall). The servo is not straining.
3. **"At the slack-range boundary" is common in passing trials too**
   (0.73–1.00 of the window). At G = 0 it is 1.00 by construction: the free
   range collapses to a single angle. **I could have seen that before running
   and did not write it into the criteria.** It is one reason A1 fails the
   discrimination check.
4. **The component that differs is neighbour post contact:** 0.00 in all 7
   stall windows, against 0.01–0.26 over the passing trials. The 3 passing
   trials that met A1 are the 3 slowest passes (29.6, 35.8, 39.6 cycles), with
   neighbour contact 0.01. This was not a pre-registered criterion on its own
   and is reported, not used.
5. **2D replay** (`media/calib_step2_seed1002_G0.75_stuck_vs_G1.0_pass.gif`,
   chosen in advance). From the same start, at about 7.5 cycles, the G = 0.75
   body is **in front of the first post column, curled into a hook, and not
   touching posts**. The G = 1.0 body has reached the far side. **Seen after
   the criteria were fixed;** it is a description and not part of the verdict.

## What this does not show

- Whether the stall is an artefact of the compliance law or real physics:
  the pre-registered criteria do not separate stuck from passing trials well
  enough to say.
- Anything about a real robot.

Per the rule: **stop and report.** Choosing option 2, option 3, or a new
pre-registered diagnostic is Fahad's decision.
