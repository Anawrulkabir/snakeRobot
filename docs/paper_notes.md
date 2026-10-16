# Paper notes

Sources read in full (PDFs uploaded by Fahad, 2026-10-16):

- **[W]** T. Wang, C. Pierce, V. Kojouharov, B. Chong, K. Diaz, H. Lu, D. I. Goldman,
  "Mechanical Intelligence Simplifies Control in Terrestrial Limbless Locomotion",
  arXiv:2304.08652**v3** (1 Feb 2024), 78 pages. This arXiv version includes the
  Materials and Methods (pp. 33–38) and the full Supplementary Materials
  (Supplementary Methods, Supplementary Discussion, Figs. S1–S12, pp. 51–78).
  The published *Science Robotics* version was **not** read.
- **[K]** V. Kojouharov, T. Wang, M. Fernandez, J. Maeng, D. I. Goldman,
  "Anisotropic body compliance facilitates robotic sidewinding in complex
  environments", arXiv:2309.13532**v1**, 6 pages.

Page numbers are the PDF page numbers. In [W] the supplement restarts its own
printed numbering at 1. I give the PDF page here, so "p. 57" means printed
supplement page 7.

Labels: `read-directly (p. X)` = copied from the paper; `abstract-only` = only
the abstract says it; `my-inference` = my reasoning, not stated by the authors.

Arithmetic check: `scripts/check_paper_arithmetic.py` recomputes the paper's
own derived numbers (L_c = L_j, l0, γ, the "fully passive" G) from the equations as I
transcribed them below. All of them match the values the paper states. This
confirms the transcription of Eqs. S1, S2, S3 and S5. It does not test Eq. 3
directly; Eq. 3 was checked visually against the rendered page 12.

---

## 1. Compliance definition (generalized compliance G)

### 1.1 The gait the cables follow: "suggested" angle, Eq. 2, `read-directly (p. 12)`

$$\alpha_i(t) = A\sin\!\left(2\pi\xi\frac{i}{N} - 2\pi\omega t\right)$$

"where A, ξ and ω is the amplitude, the spatial and temporal frequencies of the
wave, i is the joint index, and N is the total number of joints." α is called
the **suggested angle**: "the angle that would be realized absent all external
and internal forces apart from those applied by the cables".

Note (`my-inference`): ω here is a temporal *frequency* (cycles per unit time,
because it is multiplied by 2π), not an angular frequency. CLAUDE.md §5.3 writes
θ_i = A·sin(ωt − 2πki/N), with ω as angular frequency. That is the same travelling
wave with ξ ↔ k and 2πω_paper ↔ ω_CLAUDE, and an overall sign flip, which is a
half-period phase shift. Both waves travel toward increasing i. **G4 should fix
one convention.**

### 1.2 Exact cable lengths, Eq. S1 / S2, `read-directly (p. 57, geometry Fig. S4 p. 69)`

"Exact length" means the cable is shortened and straight, so it holds the joint
at α (p. 56–57):

$$\mathcal{L}^l(\alpha_i) = 2\sqrt{L_c^2+L_j^2}\,\cos\!\left[-\frac{\alpha_i}{2}+\tan^{-1}\!\left(\frac{L_c}{L_j}\right)\right],\qquad
\mathcal{L}^r(\alpha_i) = 2\sqrt{L_c^2+L_j^2}\,\cos\!\left[\frac{\alpha_i}{2}+\tan^{-1}\!\left(\frac{L_c}{L_j}\right)\right]$$

For their robot (Eq. S2):
𝓛^l(α) = 79.2 cos(−α/2 + π/4) mm, 𝓛^r(α) = 79.2 cos(α/2 + π/4) mm.

From Fig. S4, L_c is the half-width from the robot's centreline to the cable
anchor on the link face, and L_j is the joint-pin offset from each link face.

- `my-inference`: S2 matches S1 only if tan⁻¹(L_c/L_j) = π/4, i.e. L_c = L_j = 79.2/(2√2) = 28.0 mm.
  This agrees with the stated "joint (28 mm length)" (p. 54).
- `my-inference`: 𝓛^l increases with α. A positive α (bend to the right) needs a *longer* left cable.

### 1.3 Commanded cable lengths, Eq. 3: the definition of G, `read-directly (p. 12)`

$$L_i^l(\alpha_i)=\begin{cases}\mathcal{L}_i^l(\alpha_i) & \text{if } \alpha_i \le -(2G_i-1)A\\[2pt]
\mathcal{L}_i^l[-A\cdot\min(1,2G_i-1)] + l_0\cdot[(2G_i-1)A+\alpha_i] & \text{if } \alpha_i > -(2G_i-1)A\end{cases}$$

$$L_i^r(\alpha_i)=\begin{cases}\mathcal{L}_i^r(\alpha_i) & \text{if } \alpha_i \ge (2G_i-1)A\\[2pt]
\mathcal{L}_i^r[A\cdot\min(1,2G_i-1)] + l_0\cdot[(2G_i-1)A-\alpha_i] & \text{if } \alpha_i < (2G_i-1)A\end{cases}$$

Definitions in the paper's own words (pp. 12–13):

- "α_i is the suggested angle, A is the wave amplitude as in Eq. 2, 𝓛^l_i and 𝓛^r_i are the exact lengths of left and right cables to form α_i."
- "l_0 is a design parameter that determines how much a cable will be lengthened and is fixed throughout this work."
- "G_i is the generalized compliance for the i-th joint … in this work we kept the generalized compliance value to be the same throughout all joints, G_1 = ⋯ = G_N = G. The generalized compliance G ∈ [0, +∞) is a parameter that expands the range of possible angles that can occur for a given suggested angle by altering the lengths of the cables on alternate sides."
- "G is a dimensionless quantity that quantifies body compliance and not related to the robophysical model's geometry and characteristics of the environment."

[K] uses the same law with γ ≡ (2G−1)A_H and min(A, γ) in place of
A·min(1, 2G−1). For γ ≥ 0 the two are algebraically identical. The law is
applied only to the lateral joints; the vertical joints stay at G = 0
(`read-directly ([K] p. 3)`).

Value of l_0 (`read-directly (p. 57)`): "we set γl_0 to be a constant with a
magnitude of 100 throughout this work, yielding l_0 = 0.73 mm/degree", where
γ = 4096/(πD_pulley) = 137.2 mm⁻¹ (Eq. S3). [K] states l_0 = 41.8 mm/rad
(`read-directly ([K] p. 3)`), which is the same value. The pulley diameter is
9.5 mm (`read-directly (p. 54)`).

### 1.4 Representative states, `read-directly (pp. 13–16, Fig. 3 p. 15, Fig. S5 pp. 70–72)`

| G | State (paper's name) | What the paper says |
|---|---|---|
| 0 | bidirectionally non-compliant | Both cables at exact length; "joint angles can precisely track the suggested angles"; behaves as a conventional rigid robot (p. 13) |
| 0.5 | directionally compliant | The cable on the outside of the bend is lengthened by l_0·α, so the joint can bend *further* (ζ ≥ α for α > 0; ζ ≤ α for α < 0) but resists un-bending; ζ = 0 at α = 0 (pp. 13–14) |
| 0.75 | hybrid | "bidirectionally compliant when α ∈ (−0.5A, 0.5A), and … directionally compliant otherwise" (pp. 15–16) |
| 1 | bidirectionally compliant | Both cables lengthened, by l_0(A+α) and l_0(A−α); directionally compliant only at α = ±A (p. 14) |
| ≈1.75 | fully passive | "a consistent value of 1.75 is observed to correspond with full passivity throughout this work" (p. 16) |

ζ is the **emergent angle**: the joint angle that actually occurs (p. 13).

Fully passive value, Eq. S4/S5 (`read-directly (p. 59)`):
G_passive = 1 + (𝓛_max − 𝓛^r(A)) / (2 l_0 A). The paper gives 1.74, 1.73, 1.71
and 1.64 for A = 46°, 48°, 51° and 72°. **This value depends on geometry and gait**
(p. 58), even though the representative values G = 0, 0.5 and 1 do not.

### 1.5 From cable lengths to the joint's allowed range (`my-inference`, needed for implementation A)

The paper gives cable lengths. It does not give the allowed range of joint
angles as a formula; it shows that range only graphically (Fig. 3, 3rd
column; Fig. S5). A cable can go slack but cannot stretch (p. 54: "non-elastic
fishing lines"). So the emergent angle must satisfy

𝓛^l(ζ) ≤ L^l(α) and 𝓛^r(ζ) ≤ L^r(α).

Since 𝓛^l increases and 𝓛^r decreases with ζ, this gives

ζ_max = (𝓛^l)⁻¹(L^l(α)) and ζ_min = (𝓛^r)⁻¹(L^r(α)).

Inside [ζ_min, ζ_max] both cables are slack and the joint is free. At either
end, one cable is taut. **This is my derivation, and it is what I propose to
implement in actuation A. It is part of the G2 question.**

### 1.6 Something I am unsure about (for G2)

- **Eq. 3 for 0 < G < 0.5.** The paper only narrates G = 0, 0.5, 0.75, 1 and 1.75 in words. Taken literally, Eq. 3 makes 2G−1 negative for G = 0.25. The left cable is then exact only when α ≤ (1−2G)A = 0.5A, and above that it carries slack of 𝓛^l(0.5A) + l_0(α − 0.5A) − 𝓛^l(α). So the joint is directionally compliant only for |α| > 0.5A and stiff otherwise. That is consistent with "increasing G leads to more compliance", but it is my reading of the equation, not a sentence in the paper. G = 0.25 was tested (p. 37: G from 0 to 1.5 in steps of 0.25).
- The slack term uses a **linear** l_0·(…) while the exact lengths are **cosines**. So the angular width of the free range at a given G is not simply proportional to G; it depends on L_c, L_j and l_0 (`my-inference`). For a robot with different geometry, the same G can give a different free range. This matters when scaling to your robot (G4).
- **A constraint on l_0** (`my-inference`, checked by `scripts/check_paper_arithmetic.py`). Eq. 3 never commands a cable *shorter* than its exact length only if l_0 ≥ max|d𝓛/dα|. If it did command a shorter cable, the servo would fight the other cable. For their geometry, max|d𝓛/dα| = 39.6 mm/rad = 0.691 mm/deg (at |α| = 90°), and l_0 = 0.73 mm/deg sits just above it. The script finds the minimum commanded slack is ≥ 0 for every G and A tested. The paper does not state this reason for its choice of l_0. **For your robot, l_0 has to be re-derived from your L_c and L_j.**

---

## 2. Robot parameters

| Item | Value | Label |
|---|---|---|
| Joints | 7 bending joints, yaw axis "perpendicular to the ground surface" | read-directly (p. 10, p. 54) |
| Modules | "chain of linked identical modules", 7 joints, so 8 modules | count of 8 is my-inference; "identical modules" read-directly (p. 53) |
| Body length | 86 cm | read-directly (p. 10, p. 53) |
| Case (module) | 55 mm long, 68 mm diameter, PLA, Raise3D E2 printer; head case rounded | read-directly (pp. 53–54) |
| Joint link | 28 mm long, PLA, range −90° to +90° | read-directly (p. 54) |
| Cable geometry | L_c = L_j = 28.0 mm | my-inference from Eq. S2 (see 1.2) |
| Actuator | one Dynamixel 2XL430-W250-T per module: **two independently controlled axes**, one per cable; stall torque 1.4 N·m | read-directly (p. 53) |
| Pulley | 9.5 mm diameter, PLA | read-directly (p. 54) |
| Cable | non-elastic fishing line (Rikimura), tensile strength up to 180 lb | read-directly (p. 54) |
| Position control | 4096 positions/rev; P(L) = P_0 − γL (Eq. S3); "cable length was approximately proportional to the motor position" | read-directly (pp. 53, 57) |
| Skin | elastic polyester mesh sleeve, 1.75 in ID; "weak passive elasticity" toward straight; isotropic, adds no thrust | read-directly (p. 55) |
| Mass | **UNKNOWN** (no total or per-module mass found) | — |
| Supply | 11.1 V DC, tethered | read-directly (p. 54) |

**Wave parameters** (`read-directly (p. 36)`): "A = 46°, 48°, 51°, 72° and
ξ = 0.82, 0.80, 0.58, 1.02 for open, sparse, medium, and dense environments,
respectively." They were chosen so that the ratio of body wavelength to lattice
spacing matches the nematodes': "∼2 for the sparse environment, ∼2.2 for the
medium environment, and ∼1.8 for the dense environment" (pp. 35–36). The
authors add: "the choices of these parameters depend on the robophysical
model's dimensional specifications, such as module length and the maximum
range of joint bending" (p. 36).

The temporal frequency ω or gait period is **UNKNOWN**: I found no numeric
value in [W] or [K].

**How cable lengths are set** (`read-directly (pp. 12, 57)`): Eq. 3 gives L^l
and L^r from α, G, A and l_0. Eq. S3 converts each length to a motor position.

---

## 3. Ground and contact

- **Passive wheels.** LEGO wheel frames screwed to a printed base under each case. The rubber tyres were replaced with low-friction fiberglass tape to get **F⊥/F∥ = 1.6:1 drag anisotropy**, "verified with wheel force experiments" (`read-directly (p. 55; also p. 35)`). The 1.6:1 was chosen to match the nematodes' ~1.5:1.
- **Wheels were kept on in all lattice environments.** They are needed in open and sparse lattices. In denser lattices "the robophysical model can move forward effectively without wheels" (`read-directly (pp. 55–56)`).
- **Surface.** A level pegboard, 2.4 m × 1.2 m, with 6.35 mm holes on a 25.4 mm grid (`read-directly (p. 36)`). The flat-ground tests in Fig. S12A were on a "wood-surface flat ground" (`read-directly (p. 63)`).
- **Wheel friction.** The force is "speed independent" (Coulomb-like) (`read-directly (p. 35)`). Absolute friction coefficients μ∥ and μ⊥ are **UNKNOWN**; only their ratio is given.
- **Inertia.** Coasting number C ~ 10⁻³, i.e. friction-dominated and nearly inertia-free (`read-directly (pp. 11, 61–62)`).
- [K] (sidewinding): no wheels; flat ground with Coulomb friction μ ≈ 0.7 (`read-directly ([K] p. 4)`). This is not the planar lateral-undulation case.
- **Bearing on G3** (`my-inference`): the reference robot used option 1 of §5.4 (passive wheels, anisotropy 1.6:1). The ratio is mild; many wheeled snakes use much higher ratios.

## 4. Lattice geometry

- **Posts.** PVC pipe caps, **12.7 cm diameter, 10 cm tall**, bolted to the pegboard; rigid and immovable (`read-directly (p. 36; p. 16)`).
- **Density.** Given only as L/d = 0 (open), 1.8 (sparse), 2.8 (medium) and 3.3 (dense), where L is body length and d is pillar spacing (`read-directly (p. 8)` for nematodes). The robot lattices were "scaled-up" to match, and Fig. 4C plots the robot against the same L/d axis (`read-directly (p. 16, Fig. 4C p. 18)`).
- **Robot spacing in metres: UNKNOWN as stated.** With L = 0.86 m, the implied d is about 0.48, 0.31 and 0.26 m (`my-inference`). Pegboard holes are 25.4 mm apart, so the real spacings were probably rounded to that grid (`my-inference`).
- Whether d is centre-to-centre or the edge-to-edge gap is **UNKNOWN**.
- **Lattice pattern** (square, hexagonal or staggered) for the robot is **UNKNOWN**. The nematode arrays are "hexagonal" (p. 7). The Fig. S1B photo looks staggered (`my-inference`).
- Lattice extent and start position: three random initial positions, kept the same for every G (`read-directly (p. 37)`). The size of the lattice region is **UNKNOWN**.

## 5. Metrics and headline trends

| Metric | Definition | Label |
|---|---|---|
| Wave efficiency η | η = v_CoM / v_wave, with v_wave = fλ | read-directly (p. 34; p. 37 says the robot is the same as the nematodes) |
| Trial end | (1) robot exits the lattice, (2) stuck = "did not proceed for 10 consecutive gait cycles", or (3) any servo exceeds stall torque | read-directly (p. 37) |
| Repetitions | 3 trials per G per environment; G = 0 to 1.5 in steps of 0.25; error bars are SD | read-directly (p. 37, Fig. 4 caption) |
| Mechanical cost of transport | c_mt = W/(mgd); W from servo torque minus a no-load calibration, T = (τ − τ_0)/R_pulley | read-directly (pp. 62–63) |
| Head events | gliding vs buckling (phase pause > 0.5 s for the robot); buckling 33.6% of n ≈ 100 | read-directly (p. 23, p. 37) |
| [K] traverse probability | success = whole body crosses the obstacle line within 10 cycles; 5 initial conditions per set | read-directly ([K] p. 4) |

**Headline trends** (all `read-directly`, wording from the paper; I did not
read numbers off the bar charts):

- **Flat ground:** "η was inversely correlated to G" (p. 17, Fig. 4B). c_mt rises roughly in proportion to G (p. 63, Fig. S12A).
- **Lattices:** "low G (≤ 0.5) resulted in frequent jams and becoming irreversibly stuck. At high G (≥ 1.5), the model failed to generate sufficient self-propulsion. G = 0.75 emerges as an appropriate G value for locomotion in all heterogeneous environments, as local maxima of η display at G ≈ 0.75" (p. 17, Fig. 4B).
- **Medium lattice:** stuck at G = 0 and 0.25; best η and c_mt in 0.5 ≤ G ≤ 1. **Dense lattice:** effective range shifts to 0.75 ≤ G ≤ 1.25 (pp. 65–66, Fig. S12D–E).
- **η increases with obstacle density at G = 0.75**, approaching the nematodes' values (p. 17, Fig. 4C).
- **Mechanism:** at intermediate G, would-be jamming contacts deflect the body ("easy" axis), while thrust-producing contacts are resisted ("hard" axis) (pp. 20–22, Fig. 6).
- **Closed-loop reversals:** reversing the wave on a head collision improves η for 0 ≤ G ≤ 0.5 in the dense lattice (pp. 25–26, Fig. 7D).
- **[K]:** in sidewinding through a row of posts, G = 1 gave a higher traverse probability than G = 0 or 0.5 (`read-directly ([K] p. 4, Fig. 6C)`).

**Gap against CLAUDE.md §5.5** (`my-inference`): [W] does not report a "success
rate" for the lattice experiments; it reports η and stuck/exit outcomes. Our
main figure (success rate vs. G) is therefore a metric of our own. The
reproduction test in E1 should compare against the **η-vs-G trend**, and treat
success rate as an addition.

---

## 6. Unknowns (not given in [W] or [K])

| Parameter | Status | Why it matters |
|---|---|---|
| Gait temporal frequency ω / period | UNKNOWN | Sets speed, torque, and whether inertia matters |
| Total and per-module mass; head mass | UNKNOWN | Contact normal forces, friction thrust |
| Absolute wheel friction μ∥, μ⊥ (only the ratio 1.6:1 is given) | UNKNOWN | Thrust magnitude; E4 sensitivity |
| Post–body friction coefficient | UNKNOWN | Sliding along posts |
| Lattice spacing in metres for the robot (only L/d) | UNKNOWN | Arena geometry; I can derive it from L/d (§4) but that is inference |
| Centre-to-centre vs gap definition of d | UNKNOWN | Changes the effective density by about one post diameter |
| Lattice pattern for the robot (square, hex, staggered) | UNKNOWN | Arena geometry |
| Lattice extent, start pose distribution, finish criterion ("exited the lattice") | UNKNOWN | Success metric definition |
| Mesh-sleeve stiffness and damping | UNKNOWN (only "weak passive elasticity") | Passive joint stiffness inside the slack range |
| Cable stiffness (only "non-elastic", 180 lb strength) | UNKNOWN | solref/solimp in implementation B |
| Servo position-control gains, speed limit, behaviour at stall | UNKNOWN | Torque cap and dynamics in A and B |
| Joint indexing in Eq. 2 (i = 1..N or 0..N−1; is i = 1 at the head?) | UNKNOWN (Fig. 4A plots i = 1 to 7, H at top) | Phase of the wave; a convention for G4 |
| Joint friction and damping | UNKNOWN | Passive joint behaviour |
| Window over which robot η is averaged | UNKNOWN (nematodes: ≥ 3 cycles, p. 34) | Metric comparability |

I do **not** need the *Science Robotics* published version for the items above:
arXiv v3 already contains the full Supplementary Methods. The unknowns are
missing from the supplement too. Only the authors could fill them in (§13 item 1).

---

## 7. Notes relevant to later gates (`my-inference` unless marked)

1. **Hardware mismatch: needs a decision before G4.** CLAUDE.md §4 says "one hobby servo per joint … pays out the left cable and takes up the right cable". The paper's robot uses **two independently driven axes per joint** (one Dynamixel 2XL430 with two outputs; `read-directly (p. 53)`), "This feature enables the left and right cables to be adjusted to different lengths as needed".
   - With a single spool, one cable shortens by exactly as much as the other lengthens (if both spool radii are equal). Eq. 3 requires lengthening both cables at once for G > 0.5. A single spool cannot produce that, so **bidirectional compliance (G ≥ 0.5 in the paper's sense) cannot be produced with one servo per joint as described.**
   - At most it can give a fixed, built-in slack. The options will be laid out at the relevant gate.
2. **Prior art for E3.** [W] p. 33 (`read-directly`): "adding sensory capabilities could enable the robot to learn or select the 'optimal' G value in real-time … locally varying G based on local sensing feedback would enable the system to maximize the utility of surrounding environment". The authors propose adaptive G as **future work**. [W] also tests a closed-loop rule (wave reversal on a head collision, pp. 24–26). E3 must be described as testing an idea the authors suggested, not as a new idea. The broader Goldman-lab search required by §9 has not been done yet.
3. **Servo torque scale.** The reference robot's servo stalls at 1.4 N·m and drives 9.5 mm pulleys. The assumed MG90S-class servo stalls at about 0.2 N·m. E2 will quantify whether that is enough; nothing here answers it.

---

## 8. Comparison points from later Goldman-lab robots (added 2026-10-16)

**Source:** the 2024–2026 papers, read in full by Claude on 2026-10-16
(`literature_search.md`, part 3). Used only as reference points and bounds,
never as model inputs.

| Quantity | Wang 2023 (this paper) | Later robot | Note |
|---|---|---|---|
| l0 (slack rate) | 0.73 mm/deg (p. 57) | AquaMILR 0.73 mm/deg (p. 3); 3-D hydro-cluttered 0.6 mm/deg (Supp. Text, p. 42) | Ours: 0.5214 mm/deg (scaled by R, G4) |
| Body | 86 cm, 7 joints (p. 10) | Morphing MILR: 70 cm, 6 modules, 6.5 cm diameter (p. 2); AquaMILR: 66 cm, 5 joints (p. 2) | Ours: 70 cm, 7 segments, 6 joints |
| Module mass | UNKNOWN; estimated 149–218 g from components (`data/paper_segment_mass_estimate.yaml`) | Morphing MILR 0.25 kg per module (p. 2); AquaMILR+ 0.68 kg per module (p. 2, aquatic, heavier build) | Used only as **bounds** on the estimate (Fahad 2026-10-16) |
| Joint limit | ±90° (p. 54) | Morphing MILR: up to 70°, limited by self-collision (p. 2) | Ours: ±90° |
| Lattice | L/d only (p. 8) | AquaMILR: 9 cm posts, triangular grid, 25 cm spacing (p. 3) | Ours: hexagonal (proposal) |
