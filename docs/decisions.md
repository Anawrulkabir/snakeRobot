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
