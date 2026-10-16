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
