"""Joint-stop diagnosis (milestone 3 smoke test found joints on the 90 deg stop in
100% of cycles for 0.25 <= G <= 1.25 on flat ground).

Which joints hit the stops, and does a weak passive restoring stiffness (the
paper's sleeve: 'weak passive elasticity', p. 55, value UNKNOWN) or passive
joint damping change that and the locomotion? Diagnostic only; nothing here
changes the config.

  python experiments/diag_stops.py   # writes results/diag_stops/<run_id>/
"""
import copy
import json
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402

from snake import config as cfgmod  # noqa: E402
from snake import metrics  # noqa: E402
from snake.runlog import new_run  # noqa: E402
from snake.sim import run_trial  # noqa: E402

G_VALUES = (0.25, 0.75, 1.0)
SEEDS = (2000, 2001, 2002)
N_CYCLES, SKIP = 6, 1
# Passive joint stiffness, expressed by its torque at 45 deg as a share of the
# 0.2 N m stall: k = share * 0.2 / (pi/4).
VARIANTS = {
    "baseline": {},
    "stiff_2pct": {"stiffness": 0.02 * 0.2 / (np.pi / 4)},
    "stiff_10pct": {"stiffness": 0.10 * 0.2 / (np.pi / 4)},
    "stiff_25pct": {"stiffness": 0.25 * 0.2 / (np.pi / 4)},
    "damping_0.005": {"damping": 0.005},
}


def job(args):
    name, cfg, gait, G, seed = args
    f = gait["temporal_freq"]
    r = run_trial(cfg, gait, f, N_CYCLES, seed, G=G)
    n = N_CYCLES - SKIP
    h = metrics.mean_body_heading(r["t"], r["body_axis_xy"], f, SKIP, n)
    fwd, _ = metrics.displacement_per_cycle(r["t"], r["com_xy"], f, SKIP, n, h)
    w = metrics.cycle_window(r["t"], f, SKIP, n)
    return {"variant": name, "G": G, "seed": seed, "forward_disp_per_cycle_m": fwd,
            "stop_hit_cycle_fraction": r["stop_hit_cycle_fraction"],
            "stop_step_fraction_per_joint": r["stop_step_fraction_per_joint"],
            "max_deviation_deg": float(np.degrees(np.abs(r["tracking_error"][w]).max())),
            "torque_peak_Nm": float(np.abs(r["actuator_torque"][w]).max()),
            "torque_p95_Nm": float(np.percentile(np.abs(r["actuator_torque"][w]), 95))}


def main():
    base = cfgmod.load()
    gait = cfgmod.load("gait.yaml")["wave"]
    jobs = []
    for name, j in VARIANTS.items():
        c = copy.deepcopy(base)
        c["joint"].update(j)
        jobs += [(name, c, gait, G, s) for G in G_VALUES for s in SEEDS]
    with Pool() as pool:
        rows = pool.map(job, jobs)
    out = {}
    for name in VARIANTS:
        for G in G_VALUES:
            sub = [r for r in rows if r["variant"] == name and r["G"] == G]
            out.setdefault(name, {})[str(G)] = {
                "forward_disp_per_cycle_m": float(np.mean([r["forward_disp_per_cycle_m"] for r in sub])),
                "stop_hit_cycle_fraction": float(np.mean([r["stop_hit_cycle_fraction"] for r in sub])),
                "stop_step_fraction_per_joint_head_to_tail": np.mean(
                    [r["stop_step_fraction_per_joint"] for r in sub], axis=0).tolist(),
                "max_deviation_deg": float(np.max([r["max_deviation_deg"] for r in sub])),
                "torque_peak_Nm": float(np.max([r["torque_peak_Nm"] for r in sub])),
                "torque_p95_Nm": float(np.mean([r["torque_p95_Nm"] for r in sub])),
            }
    summary = {"results": out, "variants": VARIANTS, "seeds": SEEDS, "G_values": G_VALUES}
    run_dir = new_run("diag_stops", {"seeds": list(SEEDS)})
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    for name, per in out.items():
        for G, v in per.items():
            print(f"{name:14s} G={G:4s} disp {v['forward_disp_per_cycle_m']:.4f}  stop cycles "
                  f"{v['stop_hit_cycle_fraction']:.2f}  per-joint {np.round(v['stop_step_fraction_per_joint_head_to_tail'], 2)}"
                  f"  dev {v['max_deviation_deg']:.0f}  p95 {v['torque_p95_Nm']:.3f} peak {v['torque_peak_Nm']:.3f}")
    print(f"saved {run_dir}")


if __name__ == "__main__":
    main()
