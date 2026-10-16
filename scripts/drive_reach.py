"""G4 analysis: which compliance laws can a one-servo shared-spool drive produce?

A shared spool pays out one cable exactly as it takes up the other, so the
commanded lengths obey L_l + L_r = S (set at assembly) and
L_l - L_r = 2 l0 alpha (spool radius l0 per radian of joint angle). For the
paper's Eq. 3, the commanded sum is constant over the cycle only for G >= 1,
where L_l,r = S/2 +- l0 alpha with S = 2 L^l(-A) + 2 l0 (2G - 1) A.

With a circular spool of effective radius k (cable length per radian of joint
angle), the commanded lengths are straight lines in alpha:
L_l,r = S/2 +- k alpha. The exact lengths are concave in alpha, so a straight
line can touch them at one angle only. A circular spool therefore never makes
a cable taut over a range of angles, which is what Eq. 3 does for G < 1.
Two cases are evaluated:
  spool_l0:    k = l0. The shortest valid S is exactly the paper's G = 1;
               larger S gives exactly G > 1.
  spool_tight: k = d(exact)/d(alpha) at 0, S = 4 L_j. The stiffest circular
               spool: both cables taut at alpha = 0 only, slack elsewhere.

Writes results/drive_reach/<run_id>/summary.json (pure geometry, no simulation).
  python scripts/drive_reach.py
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
from scipy.optimize import brentq  # noqa: E402

from snake.cable_geometry import exact_length  # noqa: E402
from snake.runlog import new_run  # noqa: E402


def paper_cmd(alpha, G, A, Lc, Lj, l0):
    """Eq. 3 commanded (L_l, L_r)."""
    g = (2 * G - 1) * A
    Ll = (exact_length(alpha, Lc, Lj, "l") if alpha <= -g
          else exact_length(-A * min(1, 2 * G - 1), Lc, Lj, "l") + l0 * (g + alpha))
    Lr = (exact_length(alpha, Lc, Lj, "r") if alpha >= g
          else exact_length(A * min(1, 2 * G - 1), Lc, Lj, "r") + l0 * (g - alpha))
    return Ll, Lr


def spool_cmd(alpha, Gs, A, Lc, Lj, l0):
    S = 2 * exact_length(-A, Lc, Lj, "l") + 2 * l0 * (2 * Gs - 1) * A
    return S / 2 + l0 * alpha, S / 2 - l0 * alpha


def free_range(Ll, Lr, Lc, Lj):
    """(zeta_min, zeta_max): angles where both cables are slack (paper_notes 1.5)."""
    lo, hi = -math.pi / 2, math.pi / 2
    f_l = lambda z: exact_length(z, Lc, Lj, "l") - Ll
    f_r = lambda z: exact_length(z, Lc, Lj, "r") - Lr
    zmax = hi if f_l(hi) <= 0 else brentq(f_l, lo, hi)
    zmin = lo if f_r(lo) <= 0 else brentq(f_r, lo, hi)
    return zmin, zmax


def line_cmd(alpha, S, k):
    return S / 2 + k * alpha, S / 2 - k * alpha


def min_slack(fn, A, Lc, Lj):
    """Smallest commanded-minus-exact length over the cycle (m); < 0 means over-stretch."""
    return min(min(fn(a)[0] - exact_length(a, Lc, Lj, "l"), fn(a)[1] - exact_length(a, Lc, Lj, "r"))
               for a in np.linspace(-A, A, 2001))


def ranges(fn, A, Lc, Lj):
    out = {}
    for tag, a in (("alpha0", 0.0), ("alphaHalfA", A / 2), ("alphaA", A)):
        zmin, zmax = free_range(*fn(a), Lc, Lj)
        out[tag] = {"suggested_deg": math.degrees(a), "free_deg": [math.degrees(zmin), math.degrees(zmax)]}
    return out


def analyse(A_deg, Lc, Lj, l0):
    A = math.radians(A_deg)
    out = {"A_deg": A_deg, "paper": [], "spool": {}}
    for G in (0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5):
        sums = [sum(paper_cmd(a, G, A, Lc, Lj, l0)) for a in np.linspace(-A, A, 801)]
        out["paper"].append({
            "G": G,
            "sum_variation_mm": (max(sums) - min(sums)) * 1e3,
            "reachable_by_circular_spool": bool((max(sums) - min(sums)) < 1e-9),
            "ranges": ranges(lambda a: paper_cmd(a, G, A, Lc, Lj, l0), A, Lc, Lj),
        })
    # Cable travel each cable's spool must provide (max - min commanded length).
    alphas = np.linspace(-A, A, 801)
    per_G = {}
    all_lengths = []
    for G in (0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5):
        L = [paper_cmd(a, G, A, Lc, Lj, l0)[0] for a in alphas]
        per_G[str(G)] = (max(L) - min(L)) * 1e3
        all_lengths += L
    out["two_servo_travel_mm_per_G"] = per_G
    out["two_servo_travel_mm_G0_to_1.5"] = (max(all_lengths) - min(all_lengths)) * 1e3
    out["one_spool_l0_travel_mm"] = 2 * l0 * A * 1e3
    out["fully_passive_G"] = 1 + (exact_length(math.pi / 2, Lc, Lj, "l") - exact_length(A, Lc, Lj, "r")) / (2 * l0 * A)
    S1 = 2 * exact_length(-A, Lc, Lj, "l") + 2 * l0 * A          # paper's G = 1 total length
    out["spool"]["spool_l0_at_G1_min_slack_mm"] = min_slack(lambda a: line_cmd(a, S1, l0), A, Lc, Lj) * 1e3
    out["spool"]["spool_l0_shorter_by_1mm_min_slack_mm"] = min_slack(
        lambda a: line_cmd(a, S1 - 1e-3, l0), A, Lc, Lj) * 1e3
    k0 = math.hypot(Lc, Lj) * math.sin(math.atan2(Lc, Lj))        # |dL/dalpha| at alpha = 0
    tight = lambda a: line_cmd(a, 4 * Lj, k0)
    out["spool"]["tight"] = {"k_mm_per_deg": k0 * 1e3 * math.pi / 180, "S_mm": 4 * Lj * 1e3,
                             "min_slack_mm": min_slack(tight, A, Lc, Lj) * 1e3,
                             "ranges": ranges(tight, A, Lc, Lj)}
    return out


def main():
    Lc = Lj = 0.020                       # proposed (G4)
    R = math.hypot(Lc, Lj)
    # Paper: l0 = 0.73 mm/deg with R = 39.6 mm. Scaling l0 with R keeps Eq. 3
    # identical in angle space, so a given G means the same free range as in
    # the paper (exact lengths and slack both scale with R).
    l0 = math.degrees(1) * 0.73e-3 * R / 0.0396   # m/rad
    res = {"Lc_m": Lc, "Lj_m": Lj, "l0_m_per_rad": l0, "l0_mm_per_deg": l0 * 1e3 * math.pi / 180,
           "max_length_rate_mm_per_deg": R * 1e3 * math.pi / 180,
           "cases": [analyse(A, Lc, Lj, l0) for A in (46 * 7 / 6, 72 * 7 / 6)]}
    run_dir = new_run("drive_reach")
    (run_dir / "summary.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=1))
    print(f"saved {run_dir}")


if __name__ == "__main__":
    main()
