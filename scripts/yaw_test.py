"""Torsional-friction check (G3 follow-up): does the wheel's pivot friction resist turning?

One segment is yawed at a constant rate in two ways:
  pin:   about its front joint pin, as when its neighbour bends. The wheel
         also slides sideways.
  wheel: about the wheel's own contact point (pivot in place, no sliding).
         This is the worst case for torsional friction.
The torque needed is measured with the configured torsional friction and
with torsional friction set to zero. The difference is what torsional
friction adds.

  python scripts/yaw_test.py      # writes results/yaw_test/<run_id>/summary.json
"""

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import mujoco  # noqa: E402
import numpy as np  # noqa: E402

from drag_test import single_segment, segment_weight  # noqa: E402
from snake import config as cfgmod  # noqa: E402
from snake.model_builder import build_mjcf  # noqa: E402
from snake.runlog import new_run  # noqa: E402

YAW_RATE = 1.0  # rad/s, same order as the gait's peak joint rate
MEANINGFUL = 0.05  # torsional share of yaw torque above which it counts as meaningful


def yaw_torque(cfg, kind="body", pivot="pin"):
    one = single_segment(cfg, kind)
    xml = build_mjcf(one, drag_rig=True).replace(
        '<position name="hold_yaw" joint="root_yaw" kp="50" kv="5"', '<velocity name="hold_yaw" joint="root_yaw" kv="5"'
    )
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    ax = m.actuator("hold_yaw").id
    ax_x, ax_y = m.actuator("drag_x").id, m.actuator("drag_y").id
    half = cfg["body"]["segment_pitch"] / 2
    tau = []
    while d.time < 2.0:
        d.ctrl[:] = 0
        if d.time > 0.2:
            d.ctrl[ax] = YAW_RATE
            if pivot == "wheel":
                # Keep the wheel centre fixed: root velocity = -omega z x r_wheel,
                # with r_wheel = R(yaw) (-p/2, 0) from the root to the wheel.
                yaw = d.qpos[m.joint("root_yaw").qposadr[0]]
                a, b = -half * np.cos(yaw), -half * np.sin(yaw)
                d.ctrl[ax_x], d.ctrl[ax_y] = YAW_RATE * b, -YAW_RATE * a
        mujoco.mj_step(m, d)
        if d.time > 0.7:
            tau.append(abs(d.actuator_force[ax]))
    return float(np.mean(tau))


def run(cfg):
    out = {"yaw_rate_rad_per_s": YAW_RATE, "meaningful_threshold": MEANINGFUL, "rows": []}
    c0 = copy.deepcopy(cfg)
    c0["ground"]["torsional_friction"] = 0.0
    for kind in ("head", "body"):
        for pivot in ("pin", "wheel"):
            with_t = yaw_torque(cfg, kind, pivot)
            without_t = yaw_torque(c0, kind, pivot)
            out["rows"].append(
                {
                    "segment": kind,
                    "pivot": pivot,
                    "torsional_friction_m": cfg["ground"]["torsional_friction"],
                    "yaw_torque_Nm": with_t,
                    "yaw_torque_without_torsion_Nm": without_t,
                    "torsion_share": (with_t - without_t) / with_t if with_t > 0 else 0.0,
                    "torsion_model_prediction_Nm": cfg["ground"]["torsional_friction"] * segment_weight(cfg, kind),
                    "servo_stall_torque_Nm": cfg["servo"]["stall_torque"],
                }
            )
    out["meaningful"] = any(r["torsion_share"] > MEANINGFUL for r in out["rows"])
    return out


if __name__ == "__main__":
    summary = run(cfgmod.load())
    run_dir = new_run("yaw_test")
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"saved {run_dir}")
