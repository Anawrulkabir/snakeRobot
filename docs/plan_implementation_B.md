# Plan: implementation B (cable-level model), not started

**Status:** a plan for Fahad's go-ahead (decisions.md, 2026-10-18). Nothing
here is built.
**Purpose (Fahad):** check whether the cable-level model reproduces the mid-G
behaviour (stall and curl). That tells us whether the curling, if real, comes
from implementation A's simplification of the compliance law.

## What A does now, and what B changes

| | Implementation A (now) | Implementation B (planned) |
|---|---|---|
| Cable | none in the dynamics. Eq. 3 is turned into a joint free range [ζ_min, ζ_max] analytically | two spatial tendons per joint, site to site (they already exist in the model and measure length) |
| Taut cable | one-sided joint torque past the boundary, k = 11.459 N·m/rad, implicit damping | tendon length limit: the cable can go slack but cannot exceed its commanded length L_cmd(t) from Eq. 3 |
| Cable stretch | folded into k | constraint softness of the limit (`solreflimit`), set in direct spring–damper form so the axial stiffness is explicit (N/m) |
| Servo cap | joint torque clipped at stall | cable tension capped: past the cap the spool slips (the length limit is let out) |
| Logged | joint torque | cable tension (constraint force) and joint torque |

## Steps

1. **Runtime limits (verify first).** Set `limited="true"` and
   `range="0 L"` on each cable. Each step, write `model.tendon_range` from
   Eq. 3's commanded lengths. CLAUDE.md asks to confirm that `tendon_range`
   is writable at runtime and takes effect immediately: a test that changes
   the range mid-run and checks the length is held at the new value.
2. **Stiffness mapping.** Choose the cable axial stiffness so that B's joint
   stiffness at the boundary matches A's:
   - k_joint ≈ k_cable · L_c², so k_cable = 11.459 / 0.02² ≈ 2.9 × 10⁴ N/m
     (by moment arm L_c; to confirm against the exact geometry, Eq. S1).
   - Damping chosen to match A's boundary damping.
   - The values and their physical meaning are documented (stretch per
     newton).
3. **Servo cap and slip.** Hardware: the spool holds the cable until
   tension × spool radius reaches stall, then it back-drives. Model: if the
   cable tension exceeds stall / r_spool, the length limit is raised to the
   current length (slip). It returns toward L_cmd once the tension drops.
   For the A/B comparison, r_spool = L_c, so the cap matches A's joint-torque
   cap. **This slip rule is a modelling choice with no paper value**; it goes
   to Fahad as a decision before the agreement test.
4. **Tension logging and overload.** Tension comes from `efc_force` of the
   tendon-limit constraints. "At the cap" means tension ≥ 0.99 × cap, so the
   overload rule carries over unchanged.
5. **A/B agreement tests (gate G5)**, with tolerances fixed before running:
   - **static:** an external torque pushes one joint past its boundary; B's
     restoring torque and boundary angle must match A's (boundary angle
     within 0.5°, stiffness within 10%);
   - **flat ground:** G = 0, 0.75, 1.5 × 5 seeds; progress per cycle within
     10%; same endings;
   - **single post:** CLAUDE.md 5.2; one post in the path, same comparison;
   - **planted fault:** swapping the left and right commanded lengths must
     break the agreement test.
   - **If A and B disagree, the gap is reported, not tuned away** (CLAUDE.md).
6. **The question Fahad asked:** re-run the H1 seeds (open floor and medium
   lattice, G = 0, 0.5, 0.75, 1.0) with B. Compare stall and curl with A,
   using the same H1 measures. The reading is pre-registered before the run.

## Effort estimate (rough)

| Step | Work | Compute |
|---|---|---|
| 1–4: builder flags, runtime limits, slip, tension logging, unit tests | about 1 working session | minutes |
| 5: agreement tests and the G5 report | about 1 session, more if A and B disagree | ~1 h (B may run slower than A: constraints instead of an explicit torque; measured in step 1) |
| 6: H1 seeds with B | half a session | ~2 h for 80 trials, if B's cost is similar to A's |

**About 2–3 sessions in total**, plus 3–4 h of compute.

**Main risks:**
- `tendon_range` may not behave as expected at runtime (step 1 checks this
  first, before anything else is built).
- Soft constraints can chatter at the 1 ms timestep. That needs a timestep
  convergence check, as in E0.
- The slip rule is new physics that A does not have, so some disagreement
  is expected near the cap.
- If B disagrees with A, untangling why is open-ended. That would be
  reported at G5 before any H1 rerun.

## Not in scope

- Cable friction over guides or pulleys.
- Servo speed limits and backlash: A does not have them either, and adding
  them to B alone would confound the comparison. They are on the E4 list.
