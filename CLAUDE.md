# CLAUDE.md — Compliant bilateral-cable snake robot (simulation first)

## 0. Read this first: how to work with me

I am Fahad, a mechanical engineer. This is my project. You implement; I make the engineering decisions.

- At every **decision gate** (section 10), stop. Lay out 2–3 options with trade-offs in plain English and a recommendation, then wait for my answer. Do not pick for me and continue.
- Log every decision in `docs/decisions.md`: date, question, options, what I chose, and why. Draft the options; I write or confirm the "why".
- Explain *why* in physics terms, not just *what* the code does. I want to be able to defend every choice to a professor.
- Small steps. Each milestone ends with something runnable and a short note in `docs/progress.md`.
- No hardware, firmware or CAD work in this phase unless I ask (section 12).

## 1. Goal of this phase

Build a MuJoCo simulation of a planar, cable-driven snake robot whose body compliance can be tuned. Use it to answer three questions **before** any money is spent on parts:

1. Does the published effect reproduce in simulation? In a lattice of posts, the reference paper reports that an intermediate level of cable compliance gets through better than a fully stiff or fully loose body, under the same open-loop wave command.
2. What does the physical robot need? Joint torque, cable tension, speed and segment length, so I can choose servos and size parts.
3. Is my extension idea worth building? The idea is adaptive slack: loosen only when jammed, tighten to push. Prototype it in simulation and compare it fairly against every fixed compliance setting.

Simulation results are evidence about the model, not about a real robot. Every write-up must say this (section 9).

## 2. Reference work: read before designing anything

Primary source (open access on arXiv):
- T. Wang, C. Pierce, V. Kojouharov, B. Chong, K. Diaz, H. Lu, D. I. Goldman, "Mechanical Intelligence Simplifies Control in Terrestrial Limbless Locomotion," *Science Robotics*, 2023. doi:10.1126/scirobotics.adi2243. arXiv: https://arxiv.org/abs/2304.08652

Secondary source (same lab, same actuation idea, 3D sidewinding):
- V. Kojouharov, T. Wang, M. Fernandez, J. Maeng, D. I. Goldman, ICRA 2024. arXiv: https://arxiv.org/abs/2309.13532

Task: read the arXiv PDF(s) in full. Write `docs/paper_notes.md` containing:

- **Compliance definition.** The exact definition of the paper's compliance parameter (generalized compliance), with equations copied from the paper and page or figure numbers. Do not invent or "simplify" this definition. If it is unclear, say so and ask me.
- **Robot parameters.** Number of segments and joints, segment length, mass, wave parameters (amplitude, spatial frequency, temporal frequency), and how cable lengths are set from the target angle.
- **Ground and contact.** Ground contact conditions: surface, wheels or skids, friction, anything stated about anisotropy.
- **Lattice geometry.** Post diameter and spacing (density) values tested.
- **Metrics.** The metrics the paper reports (e.g. speed, success, jamming) and their headline trends, each with a figure reference.
- **Unknowns.** A list of parameters the paper does **not** give, marked `UNKNOWN`.

Label every item: `read-directly (page X)`, `abstract-only`, or `my-inference`.

If the methods or supplementary material are missing from arXiv, stop and tell me exactly which file you need (section 13). Do not guess the missing values.

## 3. Starting point

There is no existing model to reuse. Build from scratch in an empty repo.

1. **Check the environment first.** Set up a virtual environment and install pinned `mujoco` and the rest of the stack (section 8). Confirm on my machine that:
   - `import mujoco` works,
   - a tiny test model steps headless,
   - `mujoco.viewer` opens a window,
   - offscreen rendering to a video file works.

   Report the OS, Python version and MuJoCo version in `docs/progress.md`. If something fails (often OpenGL or offscreen rendering), stop and tell me the exact error and the options.
2. **Write the model plan and wait for approval (gate G1).** Write a one-page `docs/model_plan.md` covering:
   - segment geometry (box or capsule) and how mass and inertia are set,
   - the joint type and limits,
   - how planarity is enforced,
   - where the cable sites go,
   - which values come from the paper and which from my hardware assumptions (section 4).

   Then stop. Write no model code until I approve the plan.

If I later find my earlier snake experiment, I will add its path here. It was only a basic test, so do not wait for it.

## 4. Target hardware (the simulation must describe a robot I can build)

These are first estimates. Keep them all in `config/robot.yaml`, never hard-coded.

| Item | Value |
|---|---|
| Body | 7 rigid segments, 6 yaw joints, planar motion |
| Segment pitch | about 0.10 m; total length about 0.7 m |
| Segments | 3D-printed (paid print service, so the design must stay simple and identical across segments) |
| Actuation | one hobby servo per joint, micro metal-gear class (MG90S-like) |
| Servo specs | to be confirmed from the actual model I can buy in Bangladesh; assume about 0.2 N·m stall and about 0.1 s/60° until confirmed |
| Cable drive | servo turns a spool that pays out the left cable and takes up the right cable, or the reverse |
| Electronics | ESP32 and battery in the head segment |
| Mass | segment mass estimated from servo + print + fasteners; head heavier |
| Ground contact | **open** (gate G3) |

## 5. Technical approach

### 5.1 Model generation

- Generate MJCF from Python using parameters in YAML. One source of truth: no hand-edited XML duplicates.
- The model is planar: constrain to the plane, with yaw hinge joints between segments.
- Obstacles are vertical cylinders placed on a lattice, parameterized by diameter, spacing and pattern.

### 5.2 Bilateral cable actuation: two implementations, compared

**A. Joint-level compliance law (fast, build first).**
- Reproduce the paper's mapping from target angle and compliance parameter to the joint's allowed range.
- Inside the range where both cables are slack, the joint is free (passive).
- At the range boundary, a stiff one-sided restoring torque acts, capped at servo torque.

**B. Cable-level model (closer to hardware).**
- Each joint gets two spatial tendons, routed through sites on the left and right sides of adjacent segments.
- Each tendon is length-limited (one-sided: it can go slack, it cannot over-stretch).
- Each control step, update the tendon length limits from the servo/spool angle (`model.tendon_range` is writable at runtime; verify this against the MuJoCo docs and a test).
- Cable stretch is set through the constraint softness (`solref`/`solimp`). Document the chosen values and their physical meaning.
- Log cable tension from the constraint force.

**Comparison.** Show that A and B agree on a flat-ground and a single-post test before using B for experiments. If they disagree, report the gap. Do not tune it away silently.

### 5.3 Gait

Serpenoid open-loop wave:

θ_i(t) = A · sin(ω t − 2π k i / N)

- A: amplitude. ω: angular frequency. k: number of spatial waves along the body. i: joint index. N: number of joints.
- Start from the paper's values, scaled to my robot size.
- Write the gait module so the same function could later run on an ESP32: pure function of time and parameters, with no MuJoCo calls inside.

### 5.4 Ground contact and friction (gate G3)

Lateral undulation on flat ground needs friction anisotropy (sliding sideways must be harder than sliding forward) or obstacles to push against. Before choosing, confirm from the paper what their robot used. Options to present:

1. Passive wheels under each segment. This is easy to build physically and gives clear anisotropy.
2. Anisotropic contact friction in MuJoCo. Check the docs for how contact-pair friction and tangent directions work; this is easy to get subtly wrong.
3. Isotropic low-friction ground, where all thrust comes from posts. This matches the lattice-only case.

Whatever is chosen must be buildable, because the physical robot must match the simulation.

### 5.5 Metrics

All metrics are computed by one tested module:

- Forward displacement per gait cycle and average speed.
- Success: head crosses the finish line within time T.
- Jam: center-of-mass speed below a threshold for longer than a set duration. Thresholds go in config.
- Joint torque (or cable tension) time series: mean, 95th percentile and peak.
- Collision count with posts.

### 5.6 Trials and randomness

Each condition runs over many randomized trials: initial position offset, heading, and wave phase. Seeds are logged.

- Default: 50 trials per condition.
- Report the mean and a confidence interval, never a single run.
- Run headless and in parallel (multiprocessing).

## 6. Experiments, in order

| ID | Purpose | Pass condition |
|---|---|---|
| E0 | Sanity on flat ground, no posts, stiff body | Moves forward at a plausible speed; energy and penetration checks pass |
| E1 | Reproduce the trend: compliance sweep × post density | The paper's qualitative trend appears, or the mismatch is reported with likely causes |
| E2 | Hardware requirements from simulation: torque and cable tension distributions per joint at the best compliance setting | A servo requirement with margin, compared to the assumed servo spec |
| E3 | Extension: adaptive slack (jam detected → loosen; free → tighten), using only signals the real robot could measure (servo position error, or current if we add a sensor) | Compared against **every** fixed setting from E1 on the same seeds |
| E4 | Sensitivity: friction, segment mass, cable stiffness, servo torque limit | Which unknowns change the conclusions; this list decides what I must measure on the real robot |

## 7. Outputs

- `results/<experiment>/<run_id>/`: config snapshot, seeds, raw metrics (CSV/Parquet), git commit hash.
- Plots in matplotlib, styled plainly. The main figure is success rate vs. compliance for each post density, with error bars.
- Short videos of representative runs (stiff, best, loose), rendered offscreen (e.g. with `mediapy`).
- `docs/results_E*.md`: what was run, what was found, what it does **not** show.

## 8. Repo layout and stack

```
config/        robot.yaml, gait.yaml, arena.yaml, experiments/*.yaml
snake/         model_builder.py, actuation.py (A and B), gait.py, arena.py, metrics.py, sim.py
experiments/   run_sweep.py, analyze.py
tests/         pytest tests (section 9)
docs/          paper_notes.md, decisions.md, progress.md, results_E*.md
results/       (git-ignored except summaries)
```

- Stack: Python 3.11+, `mujoco` (official bindings), numpy, scipy, matplotlib, pyyaml, pandas, pytest, mediapy.
- Pin versions in `pyproject.toml` or `requirements.txt`. Use a virtual environment.
- Interactive inspection uses `mujoco.viewer`. Experiments are always headless.

## 9. Integrity rules (non-negotiable)

- **Every number traceable.** Every number in a doc, plot or README is copied from a named field of a saved run, with its run ID. No numbers from memory, and no rounding toward the paper's values.
- **Tests that can fail.** Each test must be shown to fail on a planted fault. For example, the jam detector must flag a robot pinned between posts and must not flag a free-moving one. A sign flip in the compliance law must break the A/B agreement test.
- **Physics checks.** Timestep convergence (results stable when the timestep is halved), no persistent interpenetration with posts, and the joint-limit or cable constraint never violated by more than a stated tolerance.
- **No novelty claims.** Never write that something is "first" or "novel". Before E3 is called an extension, search the Goldman lab's related papers for adaptive or feedback compliance. Report what you read and what you could not open.
- **Honest scope.** Every results doc states that these are simulation results with an approximate contact model, and lists which physics is missing: cable friction and stretch details, servo backlash and dynamics, print tolerances.
- **AI disclosure.** The README states that the code was written with Claude Code under my direction, and that the decisions log records my choices.

## 10. Decision gates (stop and ask me)

| Gate | Question |
|---|---|
| G1 | Environment works, and is `docs/model_plan.md` approved? |
| G2 | Does the paper's compliance definition, as you summarized it, match my understanding? |
| G3 | Ground contact model (5.4) |
| G4 | Segment length, joint count and wave parameters for my robot |
| G5 | A/B agreement acceptable, or fix first? |
| G6 | E1 result. If the trend does not appear, how do we diagnose it before going further? |
| G7 | Servo choice after E2 |
| G8 | Exact adaptive-slack rule for E3 |

## 11. Milestone order

1. Environment check (section 3) → read papers → `paper_notes.md` → `model_plan.md` → G1, G2.
2. Model builder + gait + flat ground → E0 → G3, G4.
3. Compliance implementation A + metrics + tests.
4. Arena + trial runner → E1 (with A) → G6.
5. Implementation B + agreement test → G5.
6. E2 → G7.
7. E3 → G8 → results.
8. E4 → list of what to measure on the real robot.

## 12. Out of scope for now

- Physical build, ESP32 firmware, CAD/STL files, OpenCV tracking pipeline.
- Reinforcement learning or other learned controllers. Only add one if a later result shows a fixed rule is clearly insufficient, and only after asking me.
- ROS.

## 13. Inputs only I can provide

1. The *Science Robotics* published version and its Supplementary Materials, if the arXiv version lacks methods detail. Tell me exactly which values are missing first; I will get the files or contact the authors.
2. The actual servo model and its spec listing from a local shop, before G7.
