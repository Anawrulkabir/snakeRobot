# Decisions log

Format: date · question · options · choice · why (written or confirmed by Fahad).

---

## G2 — Compliance definition (2026-10-16)

**Question.** How should the simulation define generalized compliance G?

**Options** (drafted by Claude; details in `paper_notes.md` §1):
1. Use the paper's definition exactly: Eq. 3 sets the commanded left and right
   cable lengths from (α, G, A, l0). Each joint's allowed angle range follows
   from the cable geometry: the joint is free while both cables are slack
   (`paper_notes.md` §1.5, my derivation).
2. Redefine G as an angular slack (e.g. slack = G·A). Simpler, but it is no
   longer the paper's G, so E1 would not be a reproduction.
3. Option 1, plus a geometry-independent report of each G as the angular slack
   it produces.

**Choice.** Option 1 (Fahad).

**Why.** _Draft for Fahad to confirm or rewrite:_ the paper's G is defined
through cable lengths, so implementing it literally is what makes E1 a
reproduction. It also lets implementations A and B share the same Eq. 3, so
the A/B agreement test (G5) compares like with like.

**Consequences / still open.**
- For 0 < G < 0.5, Eq. 3 is applied literally (`paper_notes.md` §1.6). The
  paper never describes this range in words. Fahad has not yet separately
  confirmed this reading.
- l0 must be re-derived for this robot's cable geometry, so that
  l0 ≥ max|d𝓛/dα| (`paper_notes.md` §1.6). This is part of G4.

---

## Environment notes (not a gate)

- 2026-10-16: ffmpeg installed with Homebrew (`brew install ffmpeg`) on
  Fahad's Mac. It is not pinned in `requirements.txt`; the README lists it
  as a setup step.

---

## G1 — Environment and model plan (2026-10-16)

**Question.** Is the environment working, and is `docs/model_plan.md` approved?

**Environment.** Passed: all four checks on Fahad's Mac (run 3 in `progress.md`).

**Plan items decided by Fahad:**
1. Segment collision shape: **capsule** (option offered: box).
2. Planarity: **planar root**: x/y/z slides + yaw hinge on the head, yaw-only
   joints between segments (options offered: free joint; x/y/yaw without z).
3. Segment width: **kept as a parameter for now**; the value in
   `config/robot.yaml` is a placeholder.

**Why.** _Draft for Fahad to confirm or rewrite:_ a capsule gives smooth
contact normals against posts, so it doesn't snag on post edges. The planar
root keeps real gravity-loaded normal forces, so friction is physical, while
preventing roll-over that the wheeled robot should not show. The width waits
on the print design.

**Still open.** Mass estimates (per segment, head extra) are not provided yet.
Placeholders are used and flagged; no reported result may depend on them.

---

## G3 — Ground contact model (2026-10-16)

**Question.** How does the robot get forward/sideways friction anisotropy?

**Options** (drafted by Claude):
1. Real passive wheels in the simulation: one wheel per segment on a free axle.
2. Anisotropic contact friction on fixed feet (set a ratio directly).
3. Isotropic low friction; all thrust from posts.

**Choice.** Option 1, passive wheels (Fahad). Option 2 kept only as a knob for
the E4 sensitivity sweep, not for main runs. Option 3 rejected: the robot
cannot move on open ground, so E0 could not pass.

**Why.** _Text Fahad forwarded, marked for him to put into his own words:_
it matches the paper (wheels, 1.6:1, p. 55) and the robot he will build. The
sideways resistance comes from wheel physics, not a tuned number, and the
simulated drag ratio can later be compared with a drag test on the real
robot. Requested: a simulated drag test reporting the sideways/forward ratio
before E0 (`scripts/drag_test.py`).

**Masses** (Fahad, 2026-10-16; all placeholders until weighed):
servo 13.5 g, printed shell 20 g, wheel + axle + screws 5 g per segment,
head electronics +50 g. If G4 picks two servos per joint, add the second
servo's mass (`mass.servos_per_joint`).

**Modelling choices made while implementing (Claude, for Fahad to check):**
- Each joint's servo sits in the segment behind that joint, following the
  paper's cable routing (p. 53). So the head carries electronics, not a servo.
- Rolling resistance is modelled as dry axle friction (MuJoCo `frictionloss`).
  Its constraint time constant is set to 0.002 s instead of MuJoCo's default
  0.02 s. With the default, the friction behaved viscously at robot speeds
  (`tests/test_wheels.py`).

**Still open.** How much forward rolling resistance the wheels have
(`ground.axle_friction`, placeholder 0). With 0, forward resistance is zero,
so the anisotropy ratio is unbounded. See the G3 follow-up question in
`progress.md`.

---

## G3 follow-up — Rolling resistance and contact settings (2026-10-16)

**Question.** How much forward rolling resistance do the wheels have?

**Options** (drafted by Claude): (1) ideal wheels, zero rolling resistance;
(2) load-proportional rolling resistance giving 1.6:1 for every segment;
(3) constant axle friction (rejected: the ratio would depend on segment mass).

**Choice.** Option 2 (Fahad). **Why (Fahad):** rolling loss scales with wheel
load like sliding friction, so the forward/sideways ratio is independent of
segment mass. It matches the paper's 1.6:1 for E1, and E4 sweeps the ratio.

**Conditions Fahad set, and outcome:**
1. Drag test: each segment gets 1.6:1 within a stated tolerance (2%).
   **Met**, run `20261016T165908Z_dfd51e6`: ratios 1.592–1.600 for head and
   body segments at 0.01 and 0.05 m/s.
2. Torsional friction checked with a yaw test. **MuJoCo's default (0.005 m)
   was meaningful.** Pivoting a wheel in place, it made up 72% of the
   turning torque. Swinging about the joint pin it was only 1.6%, because
   sliding takes most of the shared friction limit.
   **Set to 0. Why (Claude, for Fahad to confirm):** the cylinder's two edge
   contacts already produce a pivot scrub of μ·N·half_width. A real tread's
   scrub is about half that (uniform-pressure line contact), so adding
   torsional friction would double-count it. After the change, the torsion
   share is 0 in yaw run `20261016T165916Z_bc3bd7f`.
3. The sideways force fluctuation is explained as **contact chatter**: not
   stick-slip (single μ, no static/kinetic difference, the wheel does not
   spin) and not timestep-only. The mechanism is still open; see `progress.md`.

**Implementation choices made on the way (Claude, for Fahad to check):**
- **Elliptic friction cone instead of MuJoCo's default pyramidal.** With the
  pyramidal cone, sideways drag at 0.01 m/s was 0.27 N against μ·W = 0.37 N,
  so not Coulomb.
- **Rolling coefficient μ_roll = μ·r/√(R² − 1), not μ·r/R.** The elliptic
  cone makes sliding force and rolling torque share one limit. The naive
  formula gives 1.89:1 instead of 1.6:1.
- **The tyre partly skids at that limit.** Spin is about 53% of the rolling
  rate, so the force law is right but the wheel's spin rate is not. This
  makes the model behave like anisotropic Coulomb friction acting at the
  wheel.

---

## Gait frequency for E0 (2026-10-16)

**Choice (Fahad).** 0.25 Hz, marked provisional. Also run 0.125 and 0.5 Hz
and report displacement per cycle for all three, to test whether locomotion
is quasi-static. Stop before E1 if it is not.
**Outcome:** see `results_E0.md`.

---

## Load model, provisional (2026-10-16)

**Question.** How is vertical load shared among the wheels? The rigid plane
of G1 gave a solver-chosen load split; see the load diagnosis in
`results_E0.md`.

**Options tested:** rigid plane (G1); roll/pitch springs at each joint;
independent spring-loaded vertical slide per segment.

**Choice (Fahad, provisional).** Independent vertical slide: each segment
carries about its own weight, with no tilt.

**Why (Fahad):** servo hinges have out-of-plane play, and floors aren't flat.
Final choice after step 1 of the load diagnosis.

Slide spring 380 N/m and damping 0.5 N·s/m are Claude's choices (about 1 mm
sag per segment), not measured. They are on the E4 list.

---

## Load model, final (2026-10-16)

**Choice (Fahad).** Independent vertical slide, confirmed.
**Why (Fahad):** the rigid plane is statically indeterminate, and its load
split is a solver artefact (load diagnosis, run `20261016T174857Z_00f197e`).

---

## E1 frequency and reporting (2026-10-16)

**Choice (Fahad).** 0.125 Hz, with conditions:
1. Before the full sweep, spot-check one lattice density × one compliance at
   0.0625 vs 0.125 Hz. If displacement per cycle or success rate differs by
   more than ~3%, stop and report.
2. E2 torque and tension statistics run at 0.0625 Hz, where there is less
   chatter.

**E1 reporting (Fahad):** conclusions are relative (the ranking of compliance
values), not absolute speed.
**E4 (Fahad):** check that the compliance ranking holds with contact softness
0.02 vs 0.04 s.

---

## G4 — Cable drive, wave parameters, cable geometry (2026-10-16)

Options in `docs/g4_options.md` (drive-reach run `20261016T175804Z_162cbe0`).

1. **Drive: deferred to E1 (Fahad).** The simulation keeps the general
   two-cable law (Eq. 3). Noted that E3 requires option A (two servos per
   joint).
   After E1, Fahad's idea is to be assessed for feasibility only: **a single
   global tensioner servo that changes all cable lengths together, to vary G
   within G ≥ 1 at runtime (7 servos total).** Questions: cable routing,
   friction, and whether adaptivity limited to G ≥ 1 is useful, given E1.
2. **Wave scaling ×7/6: approved (Fahad).** Amplitudes 53.7 / 56.0 / 59.5 /
   84.0° (open / sparse / medium / dense), ξ unchanged.
   - Log joint-stop contacts in every run. Report if stops are hit in more
     than ~5% of cycles.
   - Validation run: a 7-joint, paper-matched model at one density across the
     full G sweep. Check that its G ranking matches the 6-joint model.
3. **Cable geometry: L_c = L_j = 20 mm with scaled l0, for the simulation
   (Fahad).**
   - Confirm that implementation A's results are independent of the anchor
     offsets.
   - Final offsets, spool radius and servo type are decided after E2, from
     measured cable tension.
4. **Decision rule (Fahad, replaces the CI-overlap rule).**
   - Compute the 95% CI of the success-rate *difference*: the best condition
     minus the best one-spool-reachable condition (G ≥ 1, or the tight spool
     law).
   - **Equivalence margin: 10 percentage points.**
     - CI fully inside ±10 pp: 6 servos suffice.
     - CI fully outside ±10 pp: 12 needed.
     - Otherwise inconclusive: add trials.
   - Success rate is the primary measure, speed secondary.

---

## Passive joint stiffness for E1 (2026-10-16)

**Question.** The milestone 3 smoke test found the tail joints collapsing
onto the 90° stops with zero passive stiffness (`results_M3.md`). What
stiffness should E1 use?

**Options:** (1) estimate it from the paper's force-deformation data;
(2) make stiffness an E1 factor; (3) pick 10% of stall at 45°.

**Choice (Fahad).** Option 1, modified:
- Fahad digitizes Fig. 5A (and Fig. S9 if useful) with WebPlotDigitizer.
  Claude estimates the stiffness, states the method and assumptions, and
  labels it **approximate (digitized from figure)**. Request:
  `digitize_request.md`.
- The main E1 uses that stiffness.
- **New experiment E1b:** passive stiffness × G at the medium and dense
  densities, with stiffness at 0, 0.5×, 1× and 2× the estimate. Compute to be
  estimated before running (`compute_estimates.md`).
- Before calling E1b an extension, search Goldman-lab papers 2023–2026
  (`literature_search.md`).
- Hardware list: a restoring element (sleeve or elastic) is required; measure
  the joint restoring torque with the cables slack.
- Before E1, justify each metric threshold physically
  (`metrics_thresholds.md`).

---

## Stiffness scaling, E1b levels, reporting, run order, E3 framing (2026-10-16)

**Decisions (Fahad):**
1. **Paper segment mass:** estimate it from the listed components, labelled as
   an estimate (`data/paper_segment_mass_estimate.yaml`: 149–218 g). Use
   later robots' module masses (Morphing MILR 0.25 kg) only as bounds.
2. **Stiffness scaling:** report three scalings (absolute, fraction of stall,
   ratio of passive torque to friction torque μ·W_seg·lever arm). The
   **friction ratio is primary.**
   - Factors relative to the paper (`scripts/stiffness_estimate.py`):
     friction 0.164–0.240 (mid 0.195), stall 0.143, absolute 1.
   - **E1b levels:** 0, then ¼, ½, 1, 2, 4× the friction-scaled value,
     extended to **8×** because the absolute scaling lands at 5.13× the
     friction-scaled value.
3. **Thresholds approved.** Also: log the final distance of every trial;
   compute success post hoc at 20/30/40 cycles, and report whether the G
   ranking holds at each cutoff.
4. **Runner:** resumable (skips completed trials on restart) and runnable on
   Fahad's Mac.
   - Run order: E1 main → E1b pilot (dense only, 20 trials per cell) → full
     E1b only if the pilot shows stiffness changes the G ranking.
5. **E3:** reframed as a terrestrial-lattice test of compliance tuning, citing
   AquaMILR (and Wang et al. ACC 2020, Travers et al. RSS 2016), using signals
   hobby servos can provide (position error, or one current sensor). **No
   novelty claim. E3 is now lower priority than E1b.**

---

## E1 design revised before any E1 data (2026-10-16)

**Old design.**
- Primary: success rate.
- Decision rule (G4): 95% CI of the success-rate difference (best condition
  minus best one-spool condition), with a ±10 pp margin.
- 50 independent trials per condition.

**New design (Fahad).**
- **Paired:** identical seeds and initial poses for every G within a
  density. Analyse paired differences. (The trial code already derives
  heading, phase and offset from the seed alone, independent of G.)
- **Primary metric:** distance reached at the time limit. **Secondary:**
  success rate at 20/30/40 cycles.
- **Decision rule:** 95% CI of the paired difference in mean distance, best
  condition vs best one-spool condition. Margin **0.25 body lengths**
  (0.175 m).
- **Pilot:** 20 paired trials at the medium density. Then compute the trial
  count needed for the CI to be narrower than the margin, and report it with
  an updated compute estimate before E1 runs.

**Why it changed (Fahad):** no E1 data exists yet, so this is
pre-registration, not goalpost-moving. Pairing removes pose-to-pose variance
from the G comparison. Distance is a continuous measure: it carries more
information per trial than a pass/fail outcome.

**Notes from Claude, for Fahad to consider:**
- **Censoring.** If trials stop at the finish line (1.95 m), every successful
  trial's distance is capped there, which compresses differences between
  good conditions. Options:
  - make the lattice longer than any trial can travel in 40 cycles
    (≈ 4 m at open-floor speeds);
  - keep the finish line, and treat distance as censored.
- **Margin.** 0.25 L = 0.175 m is a little under one post-row pitch
  (medium 0.217 m, dense 0.184 m), so "within the margin" means "less than
  one lattice row apart". That seems a reasonable practical-equivalence
  scale. Whether it is achievable with feasible trial counts depends on the
  spread of distances, which the pilot will show.
- AquaMILR also used distance travelled, as start-to-end Euclidean distance
  with a survival curve (AquaMILR p. 4).

---

## Lattice bug fixes, body–post friction (2026-10-16)

**Fixes approved (Fahad):**
- The start pose aims the body axis and places the body's front-most point
  before the lattice.
- Posts get contact priority, so the configured friction is used.
- Tests with planted faults for both.

**Body–post friction (Fahad):** use the paper's value if given. It is not
(`paper_notes.md` §6), so **0.4** is used as a placeholder (PLA on PVC or
wood), and it is added to the E4 sweep.

---

## E1 primary metric changed again, before the pilot (2026-10-16)

**Previous (logged earlier the same day):** distance reached at the time
limit; equivalence = paired-difference CI within ±0.25 body lengths.

**New (Fahad, pre-registered before any pilot data):**
- **Primary:** mean **progress rate** = forward displacement ÷ cycles elapsed
  at trial end, whether the trial ends at the finish, by jam termination or
  at timeout.
- **Equivalence:** the 95% CI of the paired difference (best condition minus
  best one-spool condition) lies within **±15% of the best condition's mean
  rate.**
- **Secondary:** success rate at 20/30/40 cycles, and **survival curves**
  (fraction of trials still progressing vs distance), as in AquaMILR
  Fig. 4A (p. 4).

**Why (Fahad):** distance was censored at the finish line. A rate per elapsed
cycle is defined for every trial, however it ended.

---

## Fig. 5A data, figure files, servo candidates (2026-10-17)

- **Fig. 5A:** Fahad supplied vector-extracted curves (`data/digitized/`,
  exact, from `fig5_v1.pdf`). The authors' figure files are kept in
  `paper_figures/`, git-ignored, never committed (Fahad).
- **Body–post friction stays at 0.4** (placeholder) until Fahad's tilt test.
- **Baseline servo: MG90S** (RoboticsBD RBD-0217), at 6 V. **Alternative:
  MG996R.** Both are in `config/servos.yaml`.
- Fig. 5A interpretation reported **before** the stiffness estimate
  (`stiffness_interpretation.md`). Open decisions there: where the passive
  element is centred (straight vs commanded angle vs friction), its shape
  (quadratic), and the 2 N offset.
- **Open, for Fahad: the pre-registered progress rate (displacement ÷ cycles
  elapsed) rewards early overload** (`results_servo_choice.md`). A
  full-horizon variant (failures divided by the full time limit) is computed
  alongside it. Fahad decides which is primary before the pilot.

---

## Passive element, primary metric, servo (Fahad 2026-10-17, before any E1 or pilot data)

**1. Passive element model.**
- Question: where is the passive resistance centred, what shape, and what is f_s?
- Options (`stiffness_interpretation.md`): (a) spring about the commanded
  angle α; (b) friction about the current position; (c) spring toward
  straight. Shape linear or quadratic. f_s as threshold or dry friction.
- **Chosen:** (a), quadratic, F − f_s ∝ (ζ − α)² from Fig. 5A(iii), torque
  with the 60 mm lever; f_s is a recording threshold.
- **Why (Fahad):** the fit's vertex is at the commanded angle (15.23° vs
  15°) and the quadratic fits better than a V. The cause of the α-centred
  force is **unknown** (only loading curves were published).
- E4 gets (a) friction about the current position, (b) f_s as dry friction
  (0.12 N·m breakaway on the paper's robot, scaled), (c) the linear law.
- Coefficient: friction-ratio scaling (primary, decided 2026-10-16),
  0.06489 N·m/rad², run `20261017T061904Z_10317fe`.

**2. Panel (ii) no-kink discrepancy:** kept as an open question in
`stiffness_interpretation.md`. No action.

**3. Primary metric changed to the full-horizon progress rate.**
- **Why:** a flaw found in diagnostic runs, before any E1 or pilot data. The
  elapsed-cycles rate scored an early overload above a longer run
  (`results_servo_choice.md`; `diag_torque_cap`: a 0.9-cycle overload at
  0.127 m/cycle vs a full 6-cycle run at 0.040 m/cycle).
- **Definition** (`snake/metrics.py` `progress_rate_full_horizon`), with dx
  the CoM's forward (x) displacement from the start pose:

  | Ending | Rate |
  |---|---|
  | success (head tip crosses the far edge) | dx ÷ cycles elapsed |
  | stuck (10 cycles below the jam threshold) | dx ÷ max_cycles (40) |
  | overload (≥ 0.99 × stall for 1 s) | dx ÷ max_cycles |
  | timeout (40 cycles) | dx ÷ max_cycles |

- Test: a trial that reaches further never scores lower than one that stops
  earlier (`tests/test_metrics.py`). Planted fault: the old rate fails it.
- The old rate (dx ÷ cycles elapsed) is kept as a secondary metric
  (`com_dx_per_cycle_m`).
- Equivalence rule unchanged: the paired-difference 95% CI within ±15% of the
  best condition's mean rate.

**4. Servo: MG90S is the baseline; the MG996R is dropped.**
- **Why (Fahad):** the MG996R still overloads at G = 0, is 4× heavier, barely
  fits, and may turn only ~120°. The model should match the robot that will
  be built.
- Config: `servo.stall_torque` 0.2027 N·m (6 V), `mass.servo` 0.013 kg.
- 1 vs 2 MG90S per joint is decided after E1 (both fit).

**5. Test exit codes are checked on every commit** (after the masked failure
at `d86fd6e`).

---

## Calibration before E1, pre-registered (Fahad 2026-10-17, before step 1 is run)

**Why:** the E1 pilot (run `20261017T062232Z_b5aac2a`, `results_E1_pilot.md`)
had 0/160 successes at every G. That is a floor effect: the conditions cannot
be ranked. The equivalence trial count was not computed.

### Step 1: one assumption at a time (`config/experiments/calib_step1.yaml`)

G = 0, 0.75, 1.5 × seeds 1001–1005 (a subset of the pilot), medium density.
The baseline is rerun and must reproduce the pilot rows exactly.

| Assumption | Levels (baseline first) | Plausible a priori? (fixed now, before data) |
|---|---|---|
| Body–post friction | 0.4, 0.2, 0.1 | all three. 0.4 PLA on PVC/wood (placeholder); 0.2 and 0.1 smooth or low-friction posts, which an arena can be built with |
| Servo torque cap | 0.2027 (MG90S), 0.2694 (paper 1.4 N·m × friction factor 0.1924) N·m, **1.0 N·m** | 0.2027 and 0.2694 yes. **1.0 N·m: no.** It is a BOUND (Fahad), not a purchasable option |
| Overload rule | 1 s, 3 s, off | 1 s and 3 s yes. **Off: no.** A real servo cannot hold stall indefinitely (the shop warns against continuous stall; `open_lists.md`) |
| Gait amplitude | 59.5°, ×0.85 = 50.6° | both. The amplitude is a free gait choice |
| Passive coefficient | 0.06489, ×4 = 0.25956 N·m/rad² | both. ×4 lies inside the spread of the three scalings (absolute = 5.2×, run `20261017T061904Z_10317fe`) |

### Step 2 rule (pre-registered)

1. **Per assumption,** take the level that most increased success at
   **G = 0.75** in step 1, choosing only among levels marked plausible above
   (the baseline included):
   - if any plausible level had at least one success at G = 0.75: the level
     with the most successes, ties broken by the higher mean full-horizon
     rate;
   - if none had a success: the level with the highest mean full-horizon rate;
   - an exact tie with the baseline keeps the baseline.
2. **Combine** the chosen levels. Run G = 0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5
   × 5 seeds.
3. **If mid-G (0.75–1.0) beats both ends,** that combination is the
   calibrated setup for E1. Otherwise **stop and report: no further tuning
   without Fahad's approval.**
   - Operational reading, to confirm: "beats" means the better of G = 0.75
     and 1.0 has more successes than G = 0 and than G = 1.5, ties broken by
     mean full-horizon rate.
   - With 5 seeds this is a screening check, not a test.

The selection is automated in `experiments/analyze_calibration.py`, from
the table above, so the step-1 data cannot change which levels are eligible.

### Honesty note: E1 is conditional on calibration (Fahad 2026-10-17)

**E1 results are conditional on calibrated assumptions.** These were chosen
within their plausible ranges so that the setup reproduces the paper's
qualitative result. **Every E1 write-up must say this,** and list each
calibrated assumption with its range:

| Assumption | Plausible range considered |
|---|---|
| Body–post friction | 0.1–0.4 |
| Servo torque cap | 0.2027–0.2694 N·m |
| Overload duration | 1–3 s |
| Gait amplitude (medium) | 50.6–59.5° |
| Passive coefficient | 0.06489–0.25956 N·m/rad² |

Because the setup is tuned to show "mid-G best", E1 cannot be presented as an
independent reproduction of that trend. It can say whether the trend holds
across densities, seeds and the other G values once the setup has been
calibrated at one density. E4 then says how fragile it is.

### Raw data committed (Fahad 2026-10-17)

`trials.jsonl` is committed for the pilot and for every future sweep
(`.gitignore` exception).

---

## Calibration step 2: approved; outcome rule fixed before running (Fahad 2026-10-17)

**Approved:** step 2 as pre-registered. The combined setup is friction 0.1,
MG90S torque 0.2027 N·m, 3 s overload rule, amplitude ×0.85 (50.6°),
passive ×4 (0.25956 N·m/rad²). It runs at G = 0, 0.25, 0.5, 0.75, 1.0, 1.25,
1.5 × 5 seeds (1001–1005, the same as step 1), medium density.

**Outcome rule** (replaces the "operational reading" logged with the step-2
rule). S(G) is the number of successes out of 5. Let mid = max(S(0.75), S(1.0)).
- **Mid-G wins:** mid ≥ S(0) + 2 **and** mid ≥ S(1.5) + 2.
- **Reversed:** S(0) ≥ max(S(0.75), S(1.0)) + 2, **or**
  S(1.5) ≥ max(S(0.75), S(1.0)) + 2.
- **Otherwise inconclusive.**
- The mean full-horizon rate is reported alongside, **not used to break ties.**
- **Any outcome: stop and report.** Only "mid-G wins" makes the combined
  setup the calibrated setup for E1, and only after Fahad has seen the report.

**Also reported in step 2 (Fahad):** the joint-stop contact rate per G, and
whether trials with stop contacts end worse than trials without.

### Method limitation (Fahad 2026-10-17)

The step-1 selections rest on **5 seeds per cell**. Several rest on one
success (friction 0.1, overload 3 s and passive ×4 at G = 0.75: 1/5 each), or
on a rate difference of noise size (amplitude ×0.85: 0.0063 vs 0.0045 m/cycle,
no successes). The combined setup is therefore one plausible calibration, not
an optimised one. Any E1 write-up that uses it must say this.

### Open question, not a claim: does the compliance benefit depend on body–post friction?

In step 1 at post friction 0.1, G = 0 succeeded 4/5 against 1/5 at G = 0.75
(run `20261017T075321Z_dc2fb6c`). At friction 0.4 both were 0/5. One reading:
a low-friction lattice lets a stiff body slide past posts, and that removes
the advantage of compliance. Five seeds cannot show this. **Candidate for a
later G × friction experiment.** Logged in `open_lists.md`.
