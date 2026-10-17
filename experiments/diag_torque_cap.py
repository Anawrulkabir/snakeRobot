"""Torque-cap sensitivity at placeholder stiffness (Fahad 2026-10-16).

Servo cap 0.2, 0.5 and 1.0 N m; open floor (medium-lattice gait) and medium
lattice; G = 0, 0.75 and 1; 3 seeds; 6 cycles. Only the cap (servo stall
torque) changes: the boundary stiffness, which stands in for cable and servo
stiffness, is held at its configured value. Overload = held at >= 0.99 of
the cap for 1 s (config/metrics.yaml).
Decision rule (Fahad): if the progress rate changes by more than ~10% between
0.2 and 0.5 N m, the servo choice affects E1 and must be decided first.
  python experiments/diag_torque_cap.py   # writes results/diag_torque_cap/<run_id>/
"""
import copy
import json
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402

from snake import config as cfgmod  # noqa: E402
from snake.runlog import new_run  # noqa: E402
from snake.trial import run_lattice_trial  # noqa: E402

STIFFNESS = 0.02                # placeholder, same as the lattice diagnosis
CAPS = (0.2, 0.5, 1.0)
GS = (0.0, 0.75, 1.0)
SEEDS = (1, 2, 3)
N_CYCLES = 6
GAIT = (59.5, 0.58)             # medium-lattice gait (G4)
THRESH = 0.10


def job(args):
    density, cap, G, seed = args
    cfg = cfgmod.load()
    cfg["joint"]["stiffness"] = STIFFNESS
    cfg["joint"]["passive_model"] = "none"   # as run (before the alpha-centred element, 2026-10-17)
    cfg["servo"]["stall_torque"] = cap
    mc = copy.deepcopy(cfgmod.load("metrics.yaml"))
    mc["success"]["max_cycles"] = N_CYCLES
    r = run_lattice_trial(cfg, cfgmod.load("arena.yaml"), mc, density, *GAIT, 0.125, "paper", G, seed)
    return {"density": density, "cap": cap, "G": G, "seed": seed,
            "progress_rate_m_per_cycle": r["com_dx_per_cycle_m"],
            "frac_time_any_joint_at_cap": r["frac_time_any_joint_at_cap"],
            "frac_time_at_cap_per_joint": r["frac_time_at_cap_per_joint"],
            "outcome": r["outcome"], "cycles_elapsed": r["cycles_elapsed"],
            "stop_hit_cycle_fraction": r["stop_hit_cycle_fraction"],
            "torque_peak_Nm": r["torque_peak_Nm"], "torque_p95_Nm": r["torque_p95_Nm"]}


def main():
    jobs = [(dn, cap, G, s) for dn in ("open", "medium") for cap in CAPS for G in GS for s in SEEDS]
    with Pool() as pool:
        rows = pool.map(job, jobs)
    cells = {}
    for dn in ("open", "medium"):
        for G in GS:
            for cap in CAPS:
                sub = [r for r in rows if r["density"] == dn and r["G"] == G and r["cap"] == cap]
                cells[f"{dn}|G={G}|cap={cap}"] = {
                    "progress_rate_mean": float(np.mean([r["progress_rate_m_per_cycle"] for r in sub])),
                    "progress_rate_per_seed": [r["progress_rate_m_per_cycle"] for r in sub],
                    "frac_time_any_joint_at_cap_mean": float(np.mean([r["frac_time_any_joint_at_cap"] for r in sub])),
                    "overload_endings": sum(r["outcome"] == "overload" for r in sub),
                    "outcomes": [r["outcome"] for r in sub],
                    "stop_hit_cycle_fraction_mean": float(np.mean([r["stop_hit_cycle_fraction"] for r in sub])),
                }
    change = {}
    for dn in ("open", "medium"):
        for G in GS:
            a = cells[f"{dn}|G={G}|cap=0.2"]["progress_rate_mean"]
            b = cells[f"{dn}|G={G}|cap=0.5"]["progress_rate_mean"]
            change[f"{dn}|G={G}"] = (b - a) / abs(a) if abs(a) > 1e-9 else None
    trigger = any(v is None or abs(v) > THRESH for v in change.values())
    summary = {"cells": cells, "relative_change_0.2_to_0.5": change, "threshold": THRESH,
               "servo_choice_affects_E1": trigger, "stiffness_Nm_per_rad": STIFFNESS,
               "gait": GAIT, "seeds": SEEDS, "n_cycles": N_CYCLES}
    run_dir = new_run("diag_torque_cap", {"seeds": list(SEEDS)})
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    (run_dir / "trials.json").write_text(json.dumps(rows, indent=1))
    for k, v in cells.items():
        print(f"{k:28s} rate {v['progress_rate_mean']:+.4f}  at-cap {v['frac_time_any_joint_at_cap_mean']:.3f}  "
              f"overloads {v['overload_endings']}/3  stops {v['stop_hit_cycle_fraction_mean']:.2f}")
    print("relative change 0.2 -> 0.5:", {k: (None if v is None else round(v, 3)) for k, v in change.items()})
    print("servo choice affects E1:", trigger)
    print(f"saved {run_dir}")


if __name__ == "__main__":
    main()
