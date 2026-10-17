# Progress

## Milestone 1: environment check → paper notes → model plan (in progress)

### 2026-10-16: repository scaffold
- Added the directory layout from CLAUDE.md section 8, `requirements.txt`,
  `.gitignore`, `README.md` (with the AI disclosure), and `scripts/check_env.py`.
- **Not done:** the environment check itself. It must run on Fahad's machine
  (CLAUDE.md section 3). The version pins in `requirements.txt` have not been
  installed or tested anywhere yet.
- Reading the papers was blocked at first: this cloud environment cannot
  reach `arxiv.org`.

### 2026-10-16: paper notes
- Fahad uploaded arXiv:2304.08652v3 (78 pp., including the full supplement)
  and arXiv:2309.13532v1. Both were read in full.
- Wrote `docs/paper_notes.md`.
- Added `scripts/check_paper_arithmetic.py`. Run it with
  `python3 scripts/check_paper_arithmetic.py`; it needs only the standard
  library. It recomputes the paper's derived values (L_c = L_j = 28 mm,
  l0 = 0.73 mm/deg, the fully passive G for each amplitude) from the equations
  as transcribed, and they match the paper's stated values.
- Open for G2: the compliance definition summary in `paper_notes.md` §1.
- Raised for a later gate: the paper uses two independent cable drives per
  joint, while CLAUDE.md §4 assumes one servo per joint
  (`paper_notes.md` §7.1).
- Not yet written: `docs/model_plan.md`. It is next, after G2.

### 2026-10-16: G2 decided; model plan drafted
- G2: Fahad chose option 1 (the paper's Eq. 3 used exactly). Logged in
  `docs/decisions.md`; the "why" is a draft waiting for his confirmation.
- Wrote `docs/model_plan.md`. Gate G1 is open; no model code yet.

### Environment check results (Fahad's machine, 2026-10-16, run 1)
Output of `python scripts/check_env.py`, pasted by Fahad:
- OS: macOS-26.6.2-arm64-arm-64bit-Mach-O
- Python: 3.13.2
- MuJoCo: 3.2.6
- MUJOCO_GL: (unset)
- 1. import mujoco: PASS — mujoco 3.2.6
- 2. headless step: PASS — box fell from z=0.500 m to z=0.0499 m in 2 s sim time
- 3. viewer window: FAIL — RuntimeError: `launch_passive` requires that the Python script be run under `mjpython` on macOS
- 4. offscreen video: FAIL — RuntimeError: Program 'ffmpeg' is not found

Notes:
- The pinned `requirements.txt` installed without errors on this machine.
- Check 4 failed while writing the file, not while rendering. The traceback
  is raised inside `mediapy.write_video`, after `mujoco.Renderer` had
  produced every frame. So offscreen OpenGL rendering works on this Mac;
  only the video encoder is missing.
- Both failures are waiting on Fahad's choice of fix.

### Environment check results (Fahad's machine, 2026-10-16, run 2)
- OS / Python / MuJoCo: same as run 1 (macOS-26.6.2-arm64, 3.13.2, 3.2.6)
- 1. import mujoco: PASS — mujoco 3.2.6
- 2. headless step: PASS — box fell from z=0.500 m to z=0.0499 m in 2 s sim time
- 3. viewer window: FAIL — same error as run 1 (needs `mjpython` on macOS)
- 4. offscreen video: PASS — 30 frames -> env_check_output/tiny.mp4 (4413 bytes)

Notes:
- ffmpeg became available between runs 1 and 2. How it was installed is not
  yet recorded; it is not in `requirements.txt`.

### Environment check results (Fahad's machine, 2026-10-16, run 3): all pass
Command: `mjpython scripts/check_env.py`
- OS: macOS-26.6.2-arm64-arm-64bit-Mach-O
- Python: 3.13.2
- MuJoCo: 3.2.6
- MUJOCO_GL: (unset)
- 1. import mujoco: PASS — mujoco 3.2.6
- 2. headless step: PASS — box fell from z=0.500 m to z=0.0499 m in 2 s sim time
- 3. viewer window: PASS — passive viewer opened for 3 s
- 4. offscreen video: PASS — 30 frames -> env_check_output/tiny.mp4 (4413 bytes)

Environment check (CLAUDE.md §3 step 1) complete. On macOS, anything that
opens `mujoco.viewer.launch_passive` must be started with `mjpython`, not
`python`. Headless experiments use plain `python`.

## Milestone 2: model builder + gait + flat ground (in progress)

### 2026-10-16: model builder, gait, tests
- G1 decided (`docs/decisions.md`): capsule segments, planar root
  (x/y/z slides + yaw), segment width kept as a parameter.
- `config/robot.yaml` and `config/gait.yaml`: every value is tagged
  `hardware`, `paper`, `decision`, `proposal` or `placeholder`.
  `snake.config.placeholders()` lists the placeholders still in use.
- `snake/model_builder.py` generates the MJCF:
  - 7 capsule segments and 6 yaw hinges with a ±90° hard stop.
  - Explicit masses, and a sphere foot under each segment.
  - Cable anchor sites with the paper's Fig. S4 geometry, and 12 spatial
    tendons that only measure length for now.
  - A torque-capped position servo per joint, for the stiff body in E0.
- `snake/cable_geometry.py`: Eq. S1 exact cable lengths.
- `snake/gait.py`: Eq. 2 serpenoid. Pure function, imports only `math`.
- `scripts/view_model.py`: watch the gait (`mjpython` on macOS), or write an
  mp4 with `--video`.
- Tests: 21 pass (`python -m pytest`). Each check has a planted fault it must
  catch:
  - cable sign flip and misplaced anchor sites;
  - body sunk below the floor, with the builder guard disabled;
  - reversed wave direction;
  - untagged config entries.

  A further planted fault in the builder itself (hinge axis flipped to −z)
  made 3 tests fail. The builder was restored afterwards.
- One test was wrong at first. I had checked that the body touches the floor
  by looking for contacts, but body and floor are in contact groups that
  never collide, so that check could never fire. It is now a geometric
  clearance check.
- Smoke run: the gait runs for 8 s of simulated time without numerical blow-up. Its
  numbers are not reported because masses, friction, frequency and geometry
  are placeholders.
- The cloud sandbox has no OpenGL library, so videos must be rendered on
  Fahad's Mac.

**Next: G3 (ground contact).** E0 cannot pass before G3 is decided. On
isotropic flat ground, lateral undulation produces no net forward thrust.
Masses are also still needed.

### 2026-10-16: G3 wheels and the simulated drag test
- G3 decided: passive wheels (`docs/decisions.md`). Masses set from Fahad's
  estimates, all placeholders. Joint servos sit in the segment behind each
  joint. Total model mass is 0.306 kg.
- `scripts/drag_test.py` drags one wheeled segment at 0.05 m/s along its axis,
  then sideways. It saves `results/drag_test/<run_id>/` with a config snapshot,
  git state and `summary.json`; `snake/runlog.py` builds the folder.
- Run `20261016T165127Z_f707980`, with every ground parameter at its current
  placeholder (`axle_friction` = 0). Values from its `summary.json`:
  - `sideways_force_N` = 0.3677269380386845
    (`coulomb_reference_mu_m_g_N` = 0.36787500000000006)
  - `forward_force_N` = 0.0, so `ratio_sideways_over_forward` = Infinity.
    With zero axle friction nothing resists rolling.
  - `sideways_force_std_N` = 0.08385304409758303: the sideways drag force
    fluctuates. Not investigated yet.
- A test caught a modelling problem. MuJoCo's dry joint friction, at its
  default softness (time constant 0.02 s), acted like viscous drag below
  ~0.1 m/s. The axle friction now uses a 0.002 s time constant. A test checks
  that forward drag force equals τ/r, and a planted fault with the default
  time constant shows it fails.
- Tests: 26 pass.

**Open (G3 follow-up):** the forward rolling resistance of the wheels. E0
should not run until this is chosen.

### 2026-10-16: G3 follow-up (rolling resistance, torsion, chatter) and E0
- Rolling resistance: load-proportional, set for 1.6:1. Elliptic cone;
  μ_roll = μ·r/√(R² − 1). Drag run `20261016T165908Z_dfd51e6`: every row
  within the 2% tolerance (`all_within_tolerance` = true).
- Torsional friction: MuJoCo's default was meaningful (72% of the
  pivot-in-place torque), so it is now 0. Yaw run `20261016T165916Z_bc3bd7f`:
  `meaningful` = false. Reasons in `decisions.md`.
- **Sideways force fluctuation: contact chatter.** Diagnosis:
  - Drag rig at 0.05 m/s: the wheel has no contact in 11.7% of samples, and
    the force oscillates at ~59 Hz.
  - Vertical motion is 0.045 mm. It is absent at ≤ 0.02 m/s, and grows with
    drag speed and rig stiffness.
  - It shrinks as the timestep is halved (force SD 0.078 → 0.059 → 0.048 N).
  - It is unchanged by condim 3 vs 6 or by torsion.
  - Not stick-slip: MuJoCo has a single μ, and the wheel does not spin.
- **The same chatter appears during the gait:**
  - Whole-body bounce (0 or 7 wheels touching), < 0.1 mm at ~84 Hz.
  - Normal force averages the weight (0.9996) but swings from 0 to 1.62× weight.
  - It is nearly independent of timestep (airborne fraction 24.5 → 24.0 →
    23.8%).
  - No change from contact damping ratio, noslip, impratio, solver
    tolerance, or a sphere or locked wheel.
  - A softer contact time constant (0.04 s) halves it.
  - **The mechanism is not identified.** All of these numbers came from
    single diagnostic runs in the scratchpad; they are not saved runs.
- New code:
  - `snake/metrics.py` and `snake/sim.py`, with tests and planted faults;
  - `experiments/run_e0.py`, with thresholds in `config/experiments/E0.yaml`;
  - `snake/runlog.py` no longer marks a run dirty because of files in
    `results/`.

  41 tests pass.
- **E0 run `20261016T170631Z_ef124ae`:** all checks pass. Write-up in
  `docs/results_E0.md`. Displacement per cycle rises 14% from 0.125 to
  0.5 Hz: inside the ±10% quasi-static threshold, but systematic. It may come
  from servo tracking or chatter rather than inertia. **Waiting for Fahad
  before E1.**

### 2026-10-16: chatter diagnosis before E1
- Fahad confirmed torsional friction = 0. He will write the reasoning in
  `decisions.md`.
- Added to `results_E0.md`:
  - the CI reflects numerical repeatability, not real-world uncertainty;
  - wheel spin is ~53% of the rolling rate, and E4 will compare an
    alternative forward-resistance model.
- New config switches (defaults reproduce E0 exactly):
  `ground.contact_timeconst`, `body.vertical_compliance` / `_stiffness` /
  `_damping`.
- Diagnosis run `20261016T173615Z_5373862`; results in `results_E0.md`.
  Short version:
  - The displacement-vs-frequency trend is caused by neither servo tracking
    nor the amount of chatter.
  - The chatter is not a physical bounce: no ringing, about 100 Hz, shifts
    with the timestep.
  - Over-constraint does not cause it.
  - Contact softness and vertical load sharing both change displacement a
    lot: +13% and about −50%.
- **Stopped before choosing a fix, as Fahad asked.**

### 2026-10-16: load-model diagnosis and quasi-static plateau
- `snake/sim.py` can now log per-wheel contact detail: normal force, axle
  tilt, and friction split into rolling and axle directions.
- Run `20261016T174857Z_00f197e`:
  - **The halving comes from load distribution, not from anisotropy.** The
    in-gait ratio is 1.48–1.60 in every variant.
  - With the vertical slide, each wheel carries its own weight. The rigid
    plane produces a solver-chosen, uneven split.
  - Quasi-static plateau under the slide: 0.0625 vs 0.125 Hz agree within
    1.0% with the default contact, and 2.7% with the softer contact.
- Step 3: vertical slide set as the **provisional** default load model
  (`config/robot.yaml`, `decisions.md`).
- Steps 4–5: `docs/open_lists.md` created, holding the E4 sensitivity list,
  the hardware validation list and the E2 method notes.
- **Stopped to report (Fahad's instruction).** E1 frequency is proposed, not
  set.

### 2026-10-16: decisions logged; G4 options prepared
- Logged in `decisions.md`:
  - load model final (vertical slide);
  - E1 at 0.125 Hz, with the spot-check condition;
  - E2 at 0.0625 Hz;
  - E1 results reported as rankings;
  - E4 ranking-vs-contact check.
- `scripts/drive_reach.py`, run `20261016T175804Z_162cbe0`. A one-servo
  circular shared spool reproduces the paper's G ≥ 1 exactly, and no G < 1.
  The 180° hobby servo travel limit makes spools of 17–42 mm radius.
- `docs/g4_options.md`:
  - drive options A/B/C with servo count, added mass, cost and reachable G;
  - wave parameters scaled ×7/6;
  - cable geometry L_c = L_j = 20 mm, l0 = 0.5214 mm/deg;
  - proposed E1 structure with a pre-registered 6-vs-12 decision rule.
- **Waiting for G4.** Next after G4: milestone 3 (compliance implementation
  A + tests), then the arena and E1.

## Milestone 3: compliance implementation A + metrics + tests

### 2026-10-16
- G4 logged (`decisions.md`): drive deferred to E1; ×7/6 gait; 20/20 mm
  anchors with scaled l0; CI-of-difference decision rule with a ±10 pp
  margin. Fahad's global-tensioner idea is queued for after E1.
- Implementation A, metrics, stop logging and tests are done (73 tests).
  Details in `results_M3.md`.
- Anchor-offset independence confirmed: exact for the law, and within 1e-9 m
  in simulation, after splitting the case length from the anchor offset.
- Smoke run `20261016T181330Z_9fae347`: **the joint-stop rule triggered.**
  The tail joints sit on the 90° stop in 100% of cycles for
  0.25 ≤ G ≤ 1.25.
- Diagnosis run `20261016T181938Z_a84cc70`: the cause is zero passive
  restoring stiffness. The paper's sleeve provided one; its value is UNKNOWN.
  10% of stall at 45° removes the collapse, and 25% also suppresses the
  effect of G.
- The E0 and diagnosis scripts now pin their as-run settings (stiff servo,
  rigid plane, 46° gait). E0 still reproduces exactly.
- **Stopped for a decision on passive joint stiffness before E1.**

### 2026-10-16: passive stiffness plan, literature search, metric thresholds
- `digitize_request.md`: Fig. 5A(iii) is required. At G = 1.5, α = 15° both
  cables are slack over the whole curve, for every amplitude the paper used,
  so it measures the passive restoring force alone. Panels (ii) and (i) are
  optional cross-checks.
- `literature_search.md`: no sleeve or stiffness value found in the abstracts
  I could read; arXiv full texts could not be opened.
  **The AquaMILR (ICRA 2025) abstract reports real-time compliance tuning
  from cable-tension feedback, which bears directly on E3.**
- `metrics_thresholds.md`: every threshold justified in body lengths, cycles
  or stall fraction. Success and overload thresholds added to
  `config/metrics.yaml` as proposals.
- `compute_estimates.md`: E1 17–26 h, E1b 26–39 h, on 4 cores, worst case.
- **Stopped.** Waiting for the digitized CSVs and Fahad's review of the
  thresholds.

### 2026-10-16: four papers read; lattice diagnosis; E1 redesign logged
- AquaMILR, AquaMILR+, the 3-D hydro-cluttered paper and Morphing MILR read
  in full. Fahad's points checked with page references
  (`literature_search.md`, part 3).
  - AquaMILR Eq. 4 confirmed (p. 5).
  - l0 = 0.6 mm/deg is from the 3-D paper (Supp. p. 42), not Morphing MILR.
  - No paper reports passive body stiffness.
- Lattice diagnosis run `20261016T185419Z_91e48fc` (`results_lattice_diag.md`):
  - **start-pose bug** (body can start inside posts, or facing away);
  - **post-friction bug** (configured μ ignored; effective 1.0);
  - slow compliant progress in the medium lattice, with tail joints on the
    stops.

  **Not fixed:** waiting for Fahad.
- E1 redesign logged in `decisions.md`: paired design; distance primary;
  0.25 L margin; medium pilot. With notes on censoring at the finish line and
  on the margin.

### 2026-10-16: lattice bugs fixed; diagnosis re-run; metric pre-registered
- Start pose and post friction fixed, each with a test and a planted fault
  (`tests/test_trial.py`). Body–post μ = 0.4, placeholder.
- Re-run `20261016T190405Z_c61d84c` (`results_lattice_diag.md`): starts
  clean; post friction acts; seeds consistent.
  - Torque cap reached in all compliant settings.
  - Overloads at G = 0 in the medium lattice.
  - Mechanics check only: stiffness is still a placeholder.
- Torques are now logged from t = 0.
- E1 primary metric changed to progress rate, ±15% equivalence, survival
  curves (`decisions.md`). Torque sufficiency flagged as a hardware risk
  (`open_lists.md`).
- Waiting for the Fig. 5A CSVs. Then: stiffness estimate → medium pilot (20
  paired trials) → trial-count and compute estimate → E1.

### 2026-10-16: torque-cap sensitivity; friction-measurement intake
- Run `20261016T191531Z_387fad8` (`results_lattice_diag.md`): 0.2 → 0.5 N·m
  changes the progress rate by at most 9.9% (rule not triggered; that cell
  is noise-sized). 0.2 → 1.0 N·m raises G = 0 in the lattice by 59%, through
  fewer overload endings.
- `data/measured/README.md` and `scripts/friction_from_tilt.py` are ready
  for Fahad's tilt-test CSV (μ = tan θ, mean and 95% CI). It will replace
  the 0.4 placeholder.

### 2026-10-17: Fig. 5A data in; interpretation; servo options
- Vector-extracted Fig. 5A CSVs are in `data/digitized/`. The authors'
  figures are in `paper_figures/` (git-ignored, verified with
  `git check-ignore`).
- `stiffness_interpretation.md` (Fahad's item 3), before any estimate:
  - (iii) rise not from the cables (slack for any A ≥ 26.5°);
  - it is centred at the start angle (vertex 15.23°) and quadratic;
  - f_s is undefined in all paper text and figures;
  - panel (i) is ~10 N·m/rad near α, vs our 11.459.
- `results_servo_choice.md`:
  - fit: MG90S × 1 or × 2 fit; MG996R × 1 is marginal; MG996R × 2 does not
    fit;
  - G = 0 overloads 3/3 in the medium lattice for every option.
- **Metric artefact:** the pre-registered rate rewards early overload. A
  full-horizon rate was added; the choice of primary metric is open for
  Fahad.
- Process slip: commit `d86fd6e` went in with 3 failing tests (the pytest
  exit code was masked by a pipe). Fixed in the next commit; from now on
  tests run without a pipe, with the exit code checked.

### 2026-10-17: Fahad's decisions 1–5 implemented; stiffness estimate; pilot started
- **Passive element:** α-centred quadratic, τ_p = −c_q (ζ − α)|ζ − α|, outside
  the servo (`snake/actuation.py` `passive_torque`, applied in
  `snake/trial.py`). Tests: restoring sign, quadratic magnitude, a trial-level
  tracking test, each failing on a planted sign flip.
- **Stiffness estimate** (run `20261017T061904Z_10317fe`): c_q = 0.3372
  N·m/rad² on the paper's robot; 0.06489 N·m/rad² friction-scaled (primary,
  now in `config/robot.yaml`). Details in `stiffness_interpretation.md`.
- **Correction:** `stiffness_interpretation.md` first gave the quadratic
  "curvature" as 0.00349 N/deg². That is d²F/dζ², twice the coefficient, and
  the ΔF at 30° derived from it (3.1 N, 0.19 N·m) was 2× too large. Corrected
  to 1.3 N, 0.08 N·m (read from the data).
- **Primary metric:** full-horizon progress rate (`snake/metrics.py`), with a
  monotonicity test that the old rate fails.
- **Servo:** MG90S baseline (0.2027 N·m at 6 V, 13 g); MG996R dropped.
- **Integrity fix:** MuJoCo resets the state on its own when accelerations
  blow up (it writes `MUJOCO_LOG.TXT` and carries on). The trial loops now
  raise on that warning, not only on NaN. It appeared only in a planted-fault
  test; no earlier run in this container produced the log file.
- **Sweep runner:** `experiments/run_sweep.py` (resumable, paired seeds,
  config snapshot per run) and `experiments/analyze.py` (paired CIs, trial
  count for the ±15% margin). Pilot started: run `20261017T062232Z_b5aac2a`.

### 2026-10-17: E1 pilot done: floor effect (`results_E1_pilot.md`)
- Run `20261017T062232Z_b5aac2a`: 160 trials, 0 successes, 0 diverged, overload
  fraction 0.525. Stiff settings overload (a post holds joint 2 or 3 outside
  its range; never a hard-stop artefact; all 84 re-runs reproduced exactly).
  Loose settings get stuck.
- Equivalence trial count not computed (all G below 20% success). A
  calibration sweep is proposed and awaits Fahad.

### 2026-10-17: calibration step 1 crash and fix (run `20261017T075321Z_dc2fb6c`)
- The sweep stopped after 87/135 trials. `overload_off` had
  `min_duration_s: 1.0e9`, which PyYAML reads as the **string** "1.0e9"
  (without a sign in the exponent it is not a float), so its first trial
  raised a TypeError.
- No `overload_off` trial had been written. The value was corrected to
  `1.0e+9` in `config/experiments/calib_step1.yaml` **and** in the run's own
  snapshot (`config/experiment.yaml`, identical to the source after the fix),
  and the run was resumed. The 87 completed trials are unaffected: they do
  not read that variant.
- Guard added: an override that is not a number now raises at load time
  (`tests/test_sweep.py`, planted fault = the original string).

### 2026-10-17: calibration step 1 done; visualisation
- Run `20261017T075321Z_dc2fb6c` (`results_calib_step1.md`): 135 trials, 0
  diverged, baseline 15/15 identical to the pilot. Pre-registered selection:
  friction 0.1, MG90S torque, 3 s overload, amplitude ×0.85, passive ×4.
  The strongest levers favour G = 0 over G = 0.75. Step 2 waits for Fahad.
- `scripts/animate_trial.py` (2D GIF replay, checked against the log) and
  `scripts/render_trial_3d.py` (OSMesa installed in the cloud container with
  apt; EGL failed without a GPU). GIFs in `media/`.

### 2026-10-17: engineering infrastructure (no result changes)
- **uv lock:** `pyproject.toml` + `uv.lock` (58 packages). The
  result-affecting stack is pinned at the versions that produced every run.
  `requirements.txt` is now exported from the lock. In the locked
  environment (Python 3.13.16, mujoco 3.2.6, numpy 2.1.3), the pilot
  baseline re-ran **15/15 identical in every logged field**
  (`scripts/check_reproduction.py`), before and after the formatting and lint
  commits. A calibration variant (friction_0.1, 6 trials) was also identical.
- **ruff + pre-commit:** config in `pyproject.toml`; local hooks in
  `.pre-commit-config.yaml`.
  - The formatting-only commit (`5de6fb8`, 42 files) was verified with
    identical ASTs for every file.
  - Lint fixes are in a separate commit (`60925de`). They include a real
    bug: `scripts/view_model.py` raised UnboundLocalError (F823).
- **Parquet:** `trials.parquet` next to every `trials.jsonl`, verified
  against it after writing. Back-filled for the pilot and calibration
  step 1.
- **CI:** `.github/workflows/tests.yml` runs ruff (lint, format check) and
  pytest in the locked env on every push and PR. The first runs were green
  (runs 39027267243 push, 39027267930 PR). Badge in the README.
