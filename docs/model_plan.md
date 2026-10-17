# Model plan (for gate G1)

Status: **draft, waiting for Fahad's approval.** No model code is written until this is approved.

Source tags: **[P]** from the paper (`paper_notes.md`), **[H]** from Fahad's hardware assumptions (CLAUDE.md §4), **[C]** my proposal. All values go in `config/robot.yaml`, none in code. Units are SI internally, with angles in radians.

## 1. Body and segments

- 7 identical rigid segments with 6 yaw joints between them, at a pitch of 0.10 m, for a total length of about 0.70 m [H]. The paper's robot has 7 joints over 0.86 m [P]. It is not a template for size, only for the actuation law.
- **Collision shape: a capsule (cylinder with hemispherical ends) along the body axis [C].** Physics: a post contacting a capsule always meets a smooth convex surface, so the contact normal changes continuously as the body slides past. A box has corners, where the normal flips abruptly, so the body can snag on a post. That is the wedging the paper's mesh sleeve was added to prevent [P, p. 55]. The head capsule end is rounded anyway, matching the paper's rounded head case [P, p. 54]. The alternative is a box, which is closer to a simple printed part but snags at corners. Adjacent segments do not collide with each other.
- Proposed capsule radius: half the segment width [C]. The segment width is still **open** and is needed from Fahad, since the print sets it.
- **Mass and inertia are set explicitly, not from geometry density [C].** Each segment gets an `<inertial>` element with mass m_seg, centred at the segment's centre, and the inertia of a solid box of the printed part's outer size. Physics: the real segment's mass is concentrated in the servo, not spread uniformly through a printed shell. Setting mass explicitly keeps the mass that loads the ground (and so friction) equal to what we will weigh. At a coasting number of about 10⁻³ [P], inertia matters little, so an approximate inertia tensor is acceptable. E4 will test that.
- Masses are **not yet known**. m_seg = servo + print + fasteners. m_head = m_seg + ESP32 + battery [H]. **I need your estimates** (grams per segment, and extra grams for the head). I will not put in numbers from memory.

## 2. Joints

- A hinge about the vertical (z) axis at each segment junction [H].
- Hard mechanical limit ±90° [C, copying the paper's joint range, P p. 54]. This is the physical stop of the printed joint, not the compliance range.
- The compliance range (where both cables are slack) is imposed by the actuation layer, not by MJCF joint limits:
  - Implementation A: a one-sided restoring torque capped at the servo torque.
  - Implementation B: length-limited tendons.

  The 'cable' range always sits inside the ±90° stop.
- Passive joint stiffness and damping: default **0**. The paper's sleeve gave "weak passive elasticity" but no value [P, UNKNOWN]. It will be a config parameter, varied in E4.

## 3. Planarity

**Proposal: the head segment's root gets 3 slides (x, y, z) and 1 hinge (z); there is no roll or pitch freedom [C].** The yaw-only joints between segments then keep the whole chain level. Physics: the body can still fall under gravity and rest on its ground contacts. The normal force N therefore comes from weight, and friction (μN) is physical. The robot cannot tip over when a post pushes it sideways.

- Alternative 1: a free joint (6 DOF). This is most physical, but the body can roll over when a post contacts it near the top. The real robot's wheels and low centre of mass make rolling unlikely, and modelling it would add contact tuning we do not need yet.
- Alternative 2: x, y and yaw only, with no z slide. This has no real normal force, so ground friction would come from penetration artefacts. **Rejected.**

## 4. Ground contact points (details at G3)

Each segment gets small contact geoms under it (sphere "feet") at defined positions. Ground friction then acts at known points, as a wheel or skid would. Whether they behave as wheels (anisotropic) or skids (isotropic) is G3. The paper used passive wheels with a 1.6:1 anisotropy [P, p. 55].

## 5. Cable sites (for implementation B; A uses the same numbers analytically)

- I copy the paper's joint geometry (Fig. S4) [P]. The joint is a pin at distance **L_j** behind the rear face of segment i and **L_j** ahead of the front face of segment i+1. On each face, the left and right anchor sites sit at **±L_c** from the centreline.
- For a straight cable between the two anchors, the exact length is Eq. S1 [P]:

  𝓛^{l,r}(α) = 2√(L_c²+L_j²)·cos(∓α/2 + atan(L_c/L_j))

  With this geometry the simulation's tendon length equals this formula exactly. That gives a closed-form check for the tendon model.
- L_c and L_j for your robot are **open (G4)**. They follow from the segment width and joint design. They also fix l_0: the commanded cable must never be shorter than the exact length, which requires l_0 ≥ max|d𝓛/dα| = √(L_c²+L_j²) per radian. This is my derivation, checked against the paper's numbers in `scripts/check_paper_arithmetic.py`.
- Cable routing assumes two independently commanded cable lengths per joint, as in the paper. The one-servo-per-joint question (`paper_notes.md` §7.1) is unresolved and goes to G4. The model can represent either option; only the actuation layer changes.

## 6. Obstacles and numerics

- Posts are vertical cylinders on a lattice, with diameter, spacing and pattern in `arena.yaml` (§5.1). The arena is built at milestone 4.
- Timestep: start at 1 ms. Section 9 requires a convergence check at 0.5 ms.

## What I need from you to approve G1

1. Capsule body shape: yes or no.
2. Planar root of x/y/z slides + yaw hinge: yes or no.
3. Mass estimates: per segment, and the head's extra mass.
4. Segment width, or tell me to leave it as a parameter for now with a placeholder you choose.
