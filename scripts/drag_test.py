"""Simulated wheel drag test (G3): forward vs sideways resistance of one wheeled segment.

Mirrors the paper's wheel force experiment in spirit (p. 55, "F_perp/F_par =
1.6/1"). One segment is dragged at constant speed along its axis, then
sideways, with its yaw held fixed. The mean force the rig needs over the
steady part of each drag is the resistance in that direction.

  python scripts/drag_test.py              # writes results/drag_test/<run_id>/summary.json
"""
import copy
import json
import math
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


def drag_force(cfg, direction):
    """Mean rig force (N) to drag one segment at SPEED along 'forward' or 'sideways'."""
    one = copy.deepcopy(cfg)
    one["body"]["n_segments"] = 1
    m = build_model(one, drag_rig=True)
    d = mujoco.MjData(m)
    ax = {"forward": m.actuator("drag_x").id, "sideways": m.actuator("drag_y").id}[direction]
    forces = []
    while d.time < T_END:
        d.ctrl[:] = 0
        if d.time > SETTLE:
            d.ctrl[ax] = SPEED
        mujoco.mj_step(m, d)
        if d.time > 1.0:
            forces.append(d.actuator_force[ax])
    return float(np.mean(np.abs(forces))), float(np.std(forces))


def run(cfg):
    f_fwd, s_fwd = drag_force(cfg, "forward")
    f_side, s_side = drag_force(cfg, "sideways")
    one_mass = cfg["mass"]["shell"] + cfg["mass"]["hardware"] + cfg["mass"]["head_electronics"]
    return {
        "speed_m_per_s": SPEED,
        "forward_force_N": f_fwd,
        "forward_force_std_N": s_fwd,
        "sideways_force_N": f_side,
        "sideways_force_std_N": s_side,
        "ratio_sideways_over_forward": (f_side / f_fwd) if f_fwd > 1e-6 else math.inf,
        "coulomb_reference_mu_m_g_N": cfg["ground"]["friction_sliding"] * one_mass * 9.81,
        "note": "one head segment (no servo) on its own wheel; yaw held by the rig",
    }


if __name__ == "__main__":
    cfg = cfgmod.load()
    summary = run(cfg)
    run_dir = new_run("drag_test")
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"saved {run_dir.relative_to(Path.cwd()) if run_dir.is_relative_to(Path.cwd()) else run_dir}")
