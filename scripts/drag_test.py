"""Simulated wheel drag test (G3): forward vs sideways resistance of one wheeled segment.

Mirrors the paper's wheel force experiment in spirit (p. 55, "F_perp/F_par =
1.6/1"). One segment is dragged at constant speed along its axis, then
sideways, with its yaw held fixed. The mean force the rig needs over the
steady part of each drag is the resistance in that direction.

  python scripts/drag_test.py              # writes results/drag_test/<run_id>/summary.json
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mujoco  # noqa: E402
import numpy as np  # noqa: E402

from snake import config as cfgmod  # noqa: E402
from snake.model_builder import build_model  # noqa: E402
from snake.runlog import new_run  # noqa: E402

SPEED = 0.05        # m/s, slow compared with the body length per second
SETTLE, T_END = 0.5, 3.0   # s; average force over [1.0, T_END]
RATIO_TOL = 0.02           # stated tolerance on the sideways/forward ratio


def single_segment(cfg, kind):
    """Config for a one-segment model with the mass of a 'head' or a 'body' segment."""
    one = copy.deepcopy(cfg)
    one["body"]["n_segments"] = 1
    if kind == "body":
        m = one["mass"]
        m["head_electronics"] = m["servos_per_joint"] * m["servo"]
    return one


def segment_weight(cfg, kind):
    m = single_segment(cfg, kind)["mass"]
    return (m["shell"] + m["hardware"] + m["head_electronics"]) * 9.81


def drag_force(cfg, direction, kind="head", speed=None):
    """Mean |rig force| (N) and its SD to drag one segment along 'forward' or 'sideways'."""
    speed = SPEED if speed is None else speed
    one = single_segment(cfg, kind)
    m = build_model(one, drag_rig=True)
    d = mujoco.MjData(m)
    ax = {"forward": m.actuator("drag_x").id, "sideways": m.actuator("drag_y").id}[direction]
    forces = []
    while d.time < T_END:
        d.ctrl[:] = 0
        if d.time > SETTLE:
            d.ctrl[ax] = speed
        mujoco.mj_step(m, d)
        if d.time > 1.0:
            forces.append(d.actuator_force[ax])
    return float(np.mean(np.abs(forces))), float(np.std(forces))


def run(cfg, speeds=(0.01, SPEED)):
    """Drag a head-type and a body-type segment at each speed."""
    rows = []
    for kind in ("head", "body"):
        for v in speeds:
            f_fwd, s_fwd = drag_force(cfg, "forward", kind, v)
            f_side, s_side = drag_force(cfg, "sideways", kind, v)
            rows.append({
                "segment": kind,
                "speed_m_per_s": v,
                "weight_N": segment_weight(cfg, kind),
                "forward_force_N": f_fwd,
                "forward_force_std_N": s_fwd,
                "sideways_force_N": f_side,
                "sideways_force_std_N": s_side,
                "ratio_sideways_over_forward": (f_side / f_fwd) if f_fwd > 1e-9 else None,
                "coulomb_reference_mu_W_N": cfg["ground"]["friction_sliding"] * segment_weight(cfg, kind),
            })
    return {
        "target_ratio": cfg["ground"]["anisotropy_ratio"],
        "tolerance_rel": RATIO_TOL,
        "all_within_tolerance": all(
            r["ratio_sideways_over_forward"] is not None
            and abs(r["ratio_sideways_over_forward"] / cfg["ground"]["anisotropy_ratio"] - 1) <= RATIO_TOL
            for r in rows),
        "rows": rows,
        "note": "one segment on its own wheel, yaw held by the rig; 'body' segments carry servos, the head carries electronics",
    }


if __name__ == "__main__":
    cfg = cfgmod.load()
    summary = run(cfg)
    run_dir = new_run("drag_test")
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"saved {run_dir.relative_to(Path.cwd()) if run_dir.is_relative_to(Path.cwd()) else run_dir}")
