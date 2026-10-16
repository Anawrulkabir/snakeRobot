"""Passive restoring stiffness from the paper's Fig. 5A, digitized by Fahad,
and its scaling to this robot. Writes results/stiffness_estimate/<run_id>/summary.json.

Method (docs/digitize_request.md):
  tau = F * r, with r = 0.060 m (pushing stick on a 60 mm circle about the
  joint axis, p. 38; force assumed tangential). Each branch of Fig. 5A(iii)
  (G = 1.5, alpha = 15 deg, both cables slack) is fitted with
  tau = tau0 + k |zeta - zeta_ref|. Branch slopes give the stiffness k_paper
  (N m/rad). The rest-angle test compares branch symmetry about zeta = alpha
  vs zeta = 0.

Scaling to this robot (Fahad 2026-10-16):
  absolute:  k = k_paper
  stall:     k = k_paper * stall_ours / stall_paper
  friction (primary): k = k_paper * (W_seg * lever)_ours / (W_seg * lever)_paper.
    The sliding friction coefficient mu is assumed equal for both robots and
    cancels. The paper's segment weight is an estimate
    (data/paper_segment_mass_estimate.yaml).
E1b levels: 0 and log-spaced multiples of the friction-scaled value,
extended until both other scalings fall inside the range.

All outputs are labelled APPROXIMATE (digitized from figure).
  python scripts/stiffness_estimate.py
"""
import glob
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

R_PUSH = 0.060          # m, p. 38
ALPHA = 15.0            # deg, Fig. 5A
STALL_PAPER = 1.4       # N m, p. 53
G = 9.81


def mass_estimate():
    d = yaml.safe_load(open(ROOT / "data" / "paper_segment_mass_estimate.yaml"))
    lo = sum(v["range_g"][0] for v in d["items"].values()) / 1000
    hi = sum(v["range_g"][1] for v in d["items"].values()) / 1000
    return lo, hi, d["module_pitch_m"]["value"]


def fit_branch(z_deg, F, zref):
    """Least squares tau = tau0 + k |zeta - zref| (zeta in rad). Returns k, tau0, rms."""
    x = np.abs(np.radians(z_deg - zref))
    tau = F * R_PUSH
    A = np.c_[np.ones_like(x), x]
    (tau0, k), *_ = np.linalg.lstsq(A, tau, rcond=None)
    rms = float(np.sqrt(np.mean((A @ [tau0, k] - tau) ** 2)))
    return float(k), float(tau0), rms


def scalings(k_paper, cfg):
    lo, hi, pitch_paper = mass_estimate()
    m_ours = segment_masses(cfg)[1] + cfg["mass"]["wheel"]          # a body segment
    lever_ours = cfg["body"]["segment_pitch"]
    out = {"paper_segment_mass_kg_range": [lo, hi], "ours_body_segment_mass_kg": m_ours}
    fr = [(m_ours * G * lever_ours) / (m * G * pitch_paper) for m in (hi, lo)]
    out["friction_factor_range"] = fr
    out["friction_factor_mid"] = (m_ours * lever_ours) / (0.5 * (lo + hi) * pitch_paper)
    out["stall_factor"] = cfg["servo"]["stall_torque"] / STALL_PAPER
    out["absolute_factor"] = 1.0
    if k_paper is not None:
        out["k_absolute_Nm_per_rad"] = k_paper
        out["k_stall_Nm_per_rad"] = k_paper * out["stall_factor"]
        out["k_friction_Nm_per_rad"] = k_paper * out["friction_factor_mid"]
        out["k_friction_range_Nm_per_rad"] = [k_paper * f for f in fr]
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


def main():
    cfg = cfgmod.load()
    files = sorted(glob.glob(str(ROOT / "data" / "digitized" / "*.csv")))
    fits = {}
    for f in files:
        d = np.loadtxt(f, delimiter=",", skiprows=1)
        z, F = d[:, 0], d[:, 1]
        name = Path(f).stem
        for side, mask in (("left", z < ALPHA), ("right", z > ALPHA)):
            if mask.sum() >= 3:
                fits[f"{name}:{side}"] = {
                    ref: dict(zip(("k_Nm_per_rad", "tau0_Nm", "rms_Nm"), fit_branch(z[mask], F[mask], zr)))
                    for ref, zr in (("about_alpha", ALPHA), ("about_zero", 0.0))}
    k_paper = None
    iii = [v["about_alpha"]["k_Nm_per_rad"] for k, v in fits.items() if "iii" in k]
    if iii:
        k_paper = float(np.median(iii))
    summary = {"label": "APPROXIMATE (digitized from figure)", "csv_files": [Path(f).name for f in files],
               "branch_fits": fits, "k_paper_Nm_per_rad": k_paper,
               "scaling": scalings(k_paper, cfg)}
    if not files:
        summary["note"] = "no CSVs found in data/digitized/: scaling factors only"
    run_dir = new_run("stiffness_estimate")
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"saved {run_dir}")


if __name__ == "__main__":
    main()
