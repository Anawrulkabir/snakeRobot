"""Bilateral cable actuation, implementation A: joint-level compliance law (CLAUDE.md 5.2 A).

The paper's Eq. 3 (Wang et al. 2023, p. 12) gives the commanded left and right
cable lengths from the suggested angle alpha, the generalized compliance G,
the wave amplitude A and the slack rate l0. A cable can go slack but cannot
stretch, so the joint is free wherever both cables are slack:

    exact_l(zeta) <= L_l  and  exact_r(zeta) <= L_r
    =>  zeta_min = inverse_exact_r(L_r)  <=  zeta  <=  inverse_exact_l(L_l) = zeta_max

(docs/paper_notes.md 1.5, my derivation). Inside the range the joint is
passive. Past a boundary, a stiff one-sided restoring torque acts (the taut
cable pulling), capped at the servo's stall torque.

Pure functions (math only) so the same law can run on the ESP32. Angles are
in radians, lengths in metres.
"""

import math

from snake.cable_geometry import exact_length


def geometry(cfg):
    """(L_c, L_j, l0 in m/rad) from config. l0 scales with R = sqrt(L_c^2 + L_j^2)."""
    Lc, Lj = cfg["cable"]["half_spacing"], cfg["cable"]["joint_offset"]
    return Lc, Lj, cfg["cable"]["l0_per_R"] * math.hypot(Lc, Lj)


def commanded_lengths(alpha, G, A, Lc, Lj, l0):
    """Paper Eq. 3: commanded (L_l, L_r) for suggested angle alpha."""
    g = (2 * G - 1) * A
    if alpha <= -g:
        Ll = exact_length(alpha, Lc, Lj, "l")
    else:
        Ll = exact_length(-A * min(1, 2 * G - 1), Lc, Lj, "l") + l0 * (g + alpha)
    if alpha >= g:
        Lr = exact_length(alpha, Lc, Lj, "r")
    else:
        Lr = exact_length(A * min(1, 2 * G - 1), Lc, Lj, "r") + l0 * (g - alpha)
    return Ll, Lr


def inverse_exact(L, side, Lc, Lj, hard_limit):
    """Joint angle at which the given cable is exactly taut at length L.

    exact_l(z) = 2R cos(-z/2 + phi) increases with z on [-pi/2, pi/2], so a
    left cable of length L caps the angle from above; the right cable caps it
    from below. Returns +-hard_limit if the cable is long enough never to
    become taut inside the joint's mechanical range.
    """
    R, phi = math.hypot(Lc, Lj), math.atan2(Lc, Lj)
    if side == "l":
        if L >= exact_length(hard_limit, Lc, Lj, "l"):
            return hard_limit
        return 2 * (phi - math.acos(max(-1.0, min(1.0, L / (2 * R)))))
    if L >= exact_length(-hard_limit, Lc, Lj, "r"):
        return -hard_limit
    return 2 * (math.acos(max(-1.0, min(1.0, L / (2 * R)))) - phi)


def tight_spool_lengths(alpha, Lc, Lj):
    """Stiffest one-servo circular shared spool (g4_options.md, drive_reach run
    20261016T175804Z_162cbe0): L_l,r = S/2 +- k alpha with S = 4 L_j (both
    cables taut at alpha = 0) and k = |d exact / d alpha| at 0 = L_c."""
    return 2 * Lj + Lc * alpha, 2 * Lj - Lc * alpha


def free_range(alpha, G, A, Lc, Lj, l0, hard_limit=math.pi / 2, law="paper"):
    """(zeta_min, zeta_max): the joint angles where both cables are slack.
    law = 'paper' (Eq. 3 with G) or 'tight_spool' (G ignored)."""
    if law == "paper":
        Ll, Lr = commanded_lengths(alpha, G, A, Lc, Lj, l0)
    elif law == "tight_spool":
        Ll, Lr = tight_spool_lengths(alpha, Lc, Lj)
    else:
        raise ValueError(f"unknown law {law!r}")
    return inverse_exact(Lr, "r", Lc, Lj, hard_limit), inverse_exact(Ll, "l", Lc, Lj, hard_limit)


def implicit_damping(c, dt, inertia):
    """Damping coefficient for an explicitly applied damper that behaves like
    backward Euler: c / (1 + c dt / I). Plain explicit damping goes unstable
    once c dt / I > 2. That happened at dt = 1 ms (a 500 Hz oscillation,
    tests/test_actuation.py): the inertia a joint torque acts on, with every
    other joint free to move, is only ~1.3-1.9e-5 kg m^2, giving
    c dt / I = 2.6-3.9. Pass that effective inertia, 1 / (M^-1)_jj, not the
    mass-matrix diagonal. For c dt / I << 1 the result equals c."""
    return c / (1.0 + c * dt / inertia)


def boundary_torque(zeta, zeta_dot, zmin, zmax, k, c, cap):
    """One-sided restoring torque. Zero inside [zmin, zmax]. Past a boundary,
    spring k plus damping c, acting only on motion away from the range
    (cables pull, they cannot push). Magnitude capped at cap (servo stall)."""
    if zeta > zmax:
        tau = -k * (zeta - zmax) - c * max(zeta_dot, 0.0)
    elif zeta < zmin:
        tau = -k * (zeta - zmin) - c * min(zeta_dot, 0.0)
    else:
        return 0.0
    return max(-cap, min(cap, tau))


def passive_torque(zeta, alpha, coeff, model="quadratic_alpha"):
    """Passive restoring torque centred on the commanded angle alpha
    (Fahad 2026-10-17; Fig. 5A(iii) fit, scripts/stiffness_estimate.py).
    quadratic_alpha: -coeff (zeta - alpha)|zeta - alpha|  (coeff in N m/rad^2)
    linear_alpha:    -coeff (zeta - alpha)                (coeff in N m/rad)
    none:            0
    Not capped: it is not the servo. Why the measured force is centred on
    alpha is UNKNOWN; this treats it as elastic about the pose."""
    e = zeta - alpha
    if model == "quadratic_alpha":
        return -coeff * e * abs(e)
    if model == "linear_alpha":
        return -coeff * e
    if model == "none":
        return 0.0
    raise ValueError(f"unknown passive model {model!r}")


class ComplianceA:
    """Per-step controller: suggested angles -> free ranges -> joint torques."""

    def __init__(self, cfg, G, amplitude, law="paper"):
        self.Lc, self.Lj, self.l0 = geometry(cfg)
        self.G, self.A, self.law = G, amplitude, law
        s = cfg["servo"]
        self.k, self.c, self.cap = s["boundary_stiffness"], s["boundary_damping"], s["stall_torque"]
        self.hard = math.radians(cfg["joint"]["hard_limit_deg"])

    def ranges(self, alphas):
        return [free_range(a, self.G, self.A, self.Lc, self.Lj, self.l0, self.hard, self.law) for a in alphas]

    def torques(self, alphas, zetas, zeta_dots, dt=None, inertias=None):
        """Joint torques. With dt and the joints' effective inertias
        (1 / (M^-1)_jj, see effective_inertias), the boundary damping is
        applied in implicit form (see implicit_damping)."""
        cs = [self.c] * len(zetas) if dt is None else [implicit_damping(self.c, dt, I) for I in inertias]
        return [
            boundary_torque(z, zd, lo, hi, self.k, c, self.cap)
            for (lo, hi), z, zd, c in zip(self.ranges(alphas), zetas, zeta_dots, cs)
        ]


def effective_inertias(m, d, dofs):
    """1 / (M^-1)_jj for each dof: the inertia a torque on that joint acts on
    while every other dof is free. Uses MuJoCo's factorized mass matrix from
    the last forward pass."""
    import mujoco
    import numpy as np

    E = np.zeros((len(dofs), m.nv))
    E[np.arange(len(dofs)), dofs] = 1.0
    X = np.zeros_like(E)
    mujoco.mj_solveM(m, d, X, E)
    return 1.0 / X[np.arange(len(dofs)), dofs]
