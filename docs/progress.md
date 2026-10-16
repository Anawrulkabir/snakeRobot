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
