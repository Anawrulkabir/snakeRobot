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
