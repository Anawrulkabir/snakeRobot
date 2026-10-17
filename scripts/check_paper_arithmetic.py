"""Recompute numbers quoted in Wang et al. 2023 (arXiv:2304.08652v3) from the
paper's own equations, to confirm the transcription in docs/paper_notes.md.

Pure arithmetic, no simulation. Every input below is copied from the paper
with its page number; the script prints the derived values next to the
values the paper states.
"""

import math

# Eq. S2 (p. 57): L^l(a) = 79.2 cos(-a/2 + pi/4) mm, L^r(a) = 79.2 cos(a/2 + pi/4) mm
K_MM = 79.2


def L_left(a_rad):
    return K_MM * math.cos(-a_rad / 2 + math.pi / 4)


def L_right(a_rad):
    return K_MM * math.cos(a_rad / 2 + math.pi / 4)


# Eq. S1 (p. 57) has the form 2*sqrt(Lc^2 + Lj^2) cos(+-a/2 + atan(Lc/Lj)).
# Matching S2 needs atan(Lc/Lj) = pi/4, so Lc = Lj, and 2*sqrt(2)*Lc = 79.2.
Lc = K_MM / (2 * math.sqrt(2))
print(f"Lc = Lj implied by Eq. S2: {Lc:.2f} mm   (p. 54 states joint length 28 mm)")

# p. 57: gamma = 4096 / (pi * D_pulley); D_pulley = 9.5 mm (p. 54); gamma*l0 = 100
gamma = 4096 / (math.pi * 9.5)
l0_mm_per_deg = 100 / gamma
print(f"gamma = {gamma:.1f} /mm   (paper: 137.2)")
print(f"l0 = {l0_mm_per_deg:.3f} mm/deg   (paper: 0.73 mm/degree, p. 57)")
print(f"l0 = {l0_mm_per_deg * 180 / math.pi:.1f} mm/rad   (Kojouharov et al.: 41.8 mm/rad, p. 3)")

# Eq. S5 (p. 59): G_passive = 1 + (L_max - L^r(A)) / (2 l0 A), with L_max = L^l(pi/2)
L_max = L_left(math.pi / 2)
paper_values = {46: 1.74, 48: 1.73, 51: 1.71, 72: 1.64}
for A_deg, stated in paper_values.items():
    Lr_A = L_right(math.radians(A_deg))
    G_p = 1 + (L_max - Lr_A) / (2 * 0.73 * A_deg)
    print(f"A = {A_deg} deg: fully passive G = {G_p:.3f}   (paper: {stated})")

# my-inference check: Eq. 3 never commands a cable shorter than its exact
# length (which would stall the servo) only if l0 >= max |dL/dalpha|.
# From Eq. S2, |dL/dalpha| = (79.2/2)|sin(+-a/2 + pi/4)|, largest at |a| = 90 deg.
max_slope_deg = (K_MM / 2) * math.pi / 180
print(f"max |dL/dalpha| = {max_slope_deg:.3f} mm/deg vs l0 = 0.73 mm/deg")
for A_deg in (46, 72):
    for G in (0.25, 0.5, 0.75, 1.0, 1.5):
        g = (2 * G - 1) * A_deg
        worst = min(
            L_left(math.radians(-A_deg * min(1, 2 * G - 1))) + 0.73 * (g + a / 10) - L_left(math.radians(a / 10))
            for a in range(-A_deg * 10, A_deg * 10 + 1)
            if a / 10 > -g
        )
        print(f"A = {A_deg} deg, G = {G}: min left-cable slack = {worst:.3f} mm")
