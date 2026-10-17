"""Milestone 3 smoke test: implementation A on flat ground (no posts).

Not E1: no lattice, only 3 seeds. It checks that implementation A runs
across the whole G sweep, that joint-stop logging and jam detection work in a
real trial, and that a mid-range G is stable when the timestep is halved.

  python experiments/smoke_compliance_a.py   # writes results/smoke_compliance_a/<run_id>/
"""

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

G_VALUES = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5)
SEEDS = (2000, 2001, 2002)
N_CYCLES, SKIP = 6, 1
STOP_WARN = 0.05  # Fahad (G4): report if stops are hit in > ~5% of cycles


def job(args):
    cfg, gait, G, seed, dt = args
    f = gait["temporal_freq"]
    r = run_trial(cfg, gait, f, N_CYCLES, seed, timestep=dt, G=G)
    n = N_CYCLES - SKIP
    h = metrics.mean_body_heading(r["t"], r["body_axis_xy"], f, SKIP, n)
    fwd, _ = metrics.displacement_per_cycle(r["t"], r["com_xy"], f, SKIP, n, h)
    mc = cfgmod.load("metrics.yaml")["jam"]
    jam, _ = metrics.detect_jam(r["t"], r["com_xy"], f, mc["disp_per_cycle_threshold_m"], mc["min_duration_cycles"])
    w = metrics.cycle_window(r["t"], f, SKIP, n)
    return {
        "G": G,
        "seed": seed,
        "timestep": r["timestep"],
        "forward_disp_per_cycle_m": fwd,
        "jammed": bool(jam),
        "stop_hit_cycle_fraction": r["stop_hit_cycle_fraction"],
        "max_deviation_from_suggested_deg": float(np.degrees(np.abs(r["tracking_error"][w]).max())),
        "torque_peak_Nm": float(np.abs(r["actuator_torque"][w]).max()),
        "wheel_airborne_fraction": r["wheel_airborne_fraction"],
    }


def main():
    cfg = cfgmod.load()
    gait = cfgmod.load("gait.yaml")["wave"]
    jobs = [(cfg, gait, G, s, None) for G in G_VALUES for s in SEEDS]
    jobs += [(cfg, gait, 0.75, s, 0.0005) for s in SEEDS]
    with Pool() as pool:
        rows = pool.map(job, jobs)
    summary = {
        "per_G": {},
        "timestep_check_G0.75": {},
        "seeds": SEEDS,
        "gait": gait,
        "stop_warning_threshold": STOP_WARN,
    }
    for G in G_VALUES:
        sub = [r for r in rows if r["G"] == G and r["timestep"] == cfg["sim"]["timestep"]]
        m, h = metrics.mean_ci95([r["forward_disp_per_cycle_m"] for r in sub])
        summary["per_G"][str(G)] = {
            "forward_disp_per_cycle_m": {"mean": m, "ci95_half": h},
            "jammed_trials": sum(r["jammed"] for r in sub),
            "stop_hit_cycle_fraction_max": max(r["stop_hit_cycle_fraction"] for r in sub),
            "stop_warning": max(r["stop_hit_cycle_fraction"] for r in sub) > STOP_WARN,
            "max_deviation_from_suggested_deg": max(r["max_deviation_from_suggested_deg"] for r in sub),
            "torque_peak_Nm": max(r["torque_peak_Nm"] for r in sub),
            "wheel_airborne_fraction": float(np.mean([r["wheel_airborne_fraction"] for r in sub])),
        }
    a = {
        r["seed"]: r["forward_disp_per_cycle_m"]
        for r in rows
        if r["G"] == 0.75 and r["timestep"] == cfg["sim"]["timestep"]
    }
    b = {r["seed"]: r["forward_disp_per_cycle_m"] for r in rows if r["G"] == 0.75 and r["timestep"] == 0.0005}
    summary["timestep_check_G0.75"] = {str(s): b[s] / a[s] - 1 for s in SEEDS}
    run_dir = new_run("smoke_compliance_a", {"seeds": list(SEEDS)})
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    (run_dir / "trials.json").write_text(json.dumps(rows, indent=1))
    for G, v in summary["per_G"].items():
        print(
            f"G={G:5s} disp/cycle {v['forward_disp_per_cycle_m']['mean']:.4f} +- "
            f"{v['forward_disp_per_cycle_m']['ci95_half']:.4f}  jammed {v['jammed_trials']}/3  "
            f"stops {v['stop_hit_cycle_fraction_max']:.2f}  dev {v['max_deviation_from_suggested_deg']:.1f} deg  "
            f"peak tq {v['torque_peak_Nm']:.3f}"
        )
    print("dt check G=0.75 (rel):", {k: round(v, 4) for k, v in summary["timestep_check_G0.75"].items()})
    print(f"saved {run_dir}")


if __name__ == "__main__":
    main()
