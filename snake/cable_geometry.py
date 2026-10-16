"""Exact cable lengths, paper Eq. S1 (Wang et al. 2023, p. 57; docs/paper_notes.md 1.2).

The "exact" length is the length of a taut, straight cable that holds the
joint at angle alpha. Pure math so it can be reused on the ESP32 side.
Angles are in radians and lengths in metres.
"""
import math


def exact_length(alpha, half_spacing, joint_offset, side):
    """Exact length of the left ('l') or right ('r') cable at joint angle alpha.

    L^l = 2 sqrt(Lc^2 + Lj^2) cos(-alpha/2 + atan(Lc/Lj))
    L^r = 2 sqrt(Lc^2 + Lj^2) cos(+alpha/2 + atan(Lc/Lj))
    """
    sign = {"l": -1.0, "r": 1.0}[side]
    R = math.hypot(half_spacing, joint_offset)
    return 2 * R * math.cos(sign * alpha / 2 + math.atan2(half_spacing, joint_offset))


def max_length_rate(half_spacing, joint_offset):
    """max |d exact_length / d alpha| over all alpha, in m/rad. Equals sqrt(Lc^2 + Lj^2).

    Eq. 3 never commands a cable shorter than exact only if l0 >= this
    (docs/paper_notes.md 1.6, my derivation).
    """
    return math.hypot(half_spacing, joint_offset)
