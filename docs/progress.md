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
