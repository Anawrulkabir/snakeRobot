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
