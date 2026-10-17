"""Passive restoring element from the paper's Fig. 5A(iii), and its scaling to
this robot. Writes results/stiffness_estimate/<run_id>/summary.json.

Model (Fahad 2026-10-17, docs/decisions.md): quadratic restoring force about
the commanded angle alpha,
    F - f_s = a (zeta - alpha)^2,
fitted to the measured curve of Fig. 5A(iii) (G = 1.5, alpha = 15 deg, both
cables slack: docs/stiffness_interpretation.md Q1). f_s = 2.02 N is the
force at zero deflection (the black dot, data/digitized/README.md) and is
treated as a recording threshold, so it is subtracted, not modelled.
Torque: tau = F r, r = 0.060 m (pushing stick on a 60 mm circle, p. 38;
force assumed tangential), so the joint law is
    tau_p = -c_q (zeta - alpha) |zeta - alpha|,  c_q = a r  [N m/rad^2].
Why the force is centred on alpha is UNKNOWN (only loading curves were
published; elastic about the pose vs path-dependent friction cannot be told
apart).

Also reported, for comparison and for the E4 alternatives:
  - the free three-parameter quadratic (vertex, minimum, curvature);
  - the one-parameter fit per branch (left / right of alpha);
  - E4 (c), linear approximation: tau - tau_s = k_lin |zeta - alpha|, least
    squares through the origin over the same data;
  - E4 (b), f_s as dry friction: breakaway f_s r.

Scaling to this robot (Fahad 2026-10-16):
  absolute:  factor 1
  stall:     stall_ours / stall_paper
  friction (primary): (W_seg * lever)_ours / (W_seg * lever)_paper. The
    sliding friction coefficient is assumed equal for both robots and
    cancels. The paper's segment weight is an estimate
    (data/paper_segment_mass_estimate.yaml).
E1b levels: 0 and log-spaced multiples of the friction-scaled value,
extended until both other scalings fall inside the range.

All outputs are labelled APPROXIMATE (digitized from figure).
  python scripts/stiffness_estimate.py
"""

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import yaml  # noqa: E402

from snake import config as cfgmod  # noqa: E402
from snake.model_builder import segment_masses  # noqa: E402
from snake.runlog import new_run  # noqa: E402

R_PUSH = 0.060  # m, p. 38
ALPHA = 15.0  # deg, Fig. 5A
F_S = 2.02  # N, zero-deflection force (black dot), data/digitized/README.md
STALL_PAPER = 1.4  # N m, p. 53
G = 9.81
PANEL = "fig5a_iii_data.csv"


def mass_estimate():
    d = yaml.safe_load(open(ROOT / "data" / "paper_segment_mass_estimate.yaml"))
    lo = sum(v["range_g"][0] for v in d["items"].values()) / 1000
    hi = sum(v["range_g"][1] for v in d["items"].values()) / 1000
    return lo, hi, d["module_pitch_m"]["value"]


def fit_quadratic_about(z_deg, F, zref=ALPHA, fs=F_S):
    """Least squares F - fs = a (zeta - zref)^2 (zeta in rad). Returns a [N/rad^2], rms [N]."""
    x2 = np.radians(z_deg - zref) ** 2
    y = F - fs
    a = float(x2 @ y / (x2 @ x2))
    return a, float(np.sqrt(np.mean((a * x2 - y) ** 2)))


def fit_linear_about(z_deg, F, zref=ALPHA, fs=F_S):
    """Least squares F - fs = b |zeta - zref| (zeta in rad). Returns b [N/rad], rms [N]."""
    x = np.abs(np.radians(z_deg - zref))
    y = F - fs
    b = float(x @ y / (x @ x))
    return b, float(np.sqrt(np.mean((b * x - y) ** 2)))


def fit_free_quadratic(z_deg, F):
    """F = c2 z^2 + c1 z + c0 (z in deg). Returns vertex [deg], minimum [N], curvature [N/deg^2], rms [N]."""
    c2, c1, c0 = np.polyfit(z_deg, F, 2)
    v = -c1 / (2 * c2)
    rms = float(np.sqrt(np.mean((np.polyval([c2, c1, c0], z_deg) - F) ** 2)))
    return float(v), float(c0 - c1**2 / (4 * c2)), float(c2), rms


def scalings(cfg):
    lo, hi, pitch_paper = mass_estimate()
    m_ours = segment_masses(cfg)[1] + cfg["mass"]["wheel"]  # a body segment
    lever_ours = cfg["body"]["segment_pitch"]
    out = {
        "paper_segment_mass_kg_range": [lo, hi],
        "ours_body_segment_mass_kg": m_ours,
        # Bound only (Fahad 2026-10-16): Morphing MILR module mass 0.25 kg.
        "bound_check_morphing_milr_module_kg": 0.25,
        "estimate_within_bound": hi <= 0.25,
    }
    out["friction_factor_range"] = [(m_ours * lever_ours) / (m * pitch_paper) for m in (hi, lo)]
    out["friction_factor_mid"] = (m_ours * lever_ours) / (0.5 * (lo + hi) * pitch_paper)
    out["stall_factor"] = cfg["servo"]["stall_torque"] / STALL_PAPER
    out["absolute_factor"] = 1.0
    # E1b multiples of the friction-scaled value: 1/4 .. 4, extended (x2 steps)
    # until the stall- and absolute-scaled values both fall inside.
    rel = [out["stall_factor"] / out["friction_factor_mid"], 1.0 / out["friction_factor_mid"]]
    mults = [0.25, 0.5, 1.0, 2.0, 4.0]
    while max(rel) > mults[-1]:
        mults.append(mults[-1] * 2)
    while min(rel) < mults[0]:
        mults.insert(0, mults[0] / 2)
    out["other_scalings_as_multiples_of_friction"] = {"stall": rel[0], "absolute": rel[1]}
    out["E1b_multiples_of_friction_scaled"] = [0.0] + mults
    return out


def scaled(value, sc):
    return {
        "absolute": value * sc["absolute_factor"],
        "stall": value * sc["stall_factor"],
        "friction_primary": value * sc["friction_factor_mid"],
        "friction_range": [value * f for f in sc["friction_factor_range"]],
    }


def main():
    cfg = cfgmod.load()
    d = np.loadtxt(ROOT / "data" / "digitized" / PANEL, delimiter=",", skiprows=1)
    z, F = d[:, 0], d[:, 1]
    a, rms = fit_quadratic_about(z, F)
    branches = {
        side: dict(zip(("a_N_per_rad2", "rms_N"), fit_quadratic_about(z[m], F[m])))
        for side, m in (("left", z < ALPHA), ("right", z > ALPHA))
    }
    b, rms_lin = fit_linear_about(z, F)
    v, fmin, curv, rms_free = fit_free_quadratic(z, F)
    sc = scalings(cfg)
    c_q = a * R_PUSH
    k_lin = b * R_PUSH
    tau_s = F_S * R_PUSH
    defl = math.radians(30)
    summary = {
        "label": "APPROXIMATE (digitized from figure)",
        "panel": PANEL,
        "n_points": int(len(z)),
        "zeta_range_deg": [float(z.min()), float(z.max())],
        "alpha_deg": ALPHA,
        "f_s_N": F_S,
        "lever_m": R_PUSH,
        "main_quadratic_about_alpha": {
            "a_N_per_rad2": a,
            "rms_N": rms,
            "c_q_paper_Nm_per_rad2": c_q,
            "branches": branches,
            "c_q_scaled_Nm_per_rad2": scaled(c_q, sc),
            "torque_at_30deg_paper_Nm": c_q * defl**2,
            "torque_at_30deg_scaled_Nm": scaled(c_q * defl**2, sc),
        },
        "free_quadratic": {"vertex_deg": v, "min_force_N": fmin, "curvature_N_per_deg2": curv, "rms_N": rms_free},
        "E4c_linear_about_alpha": {
            "b_N_per_rad": b,
            "rms_N": rms_lin,
            "k_lin_paper_Nm_per_rad": k_lin,
            "k_lin_scaled_Nm_per_rad": scaled(k_lin, sc),
        },
        "E4b_dry_friction": {"breakaway_paper_Nm": tau_s, "breakaway_scaled_Nm": scaled(tau_s, sc)},
        "scaling": sc,
        "ours_stall_Nm": cfg["servo"]["stall_torque"],
    }
    run_dir = new_run("stiffness_estimate")
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"saved {run_dir}")


if __name__ == "__main__":
    main()
