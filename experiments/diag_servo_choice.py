"""Servo choice check at placeholder stiffness (Fahad 2026-10-17).

MG90S and MG996R (config/servos.yaml, 6 V), each with 1 and 2 servos per
joint. The cap (stall torque at 6 V) and the segment mass change together.
- With 2 servos per joint (one per cable), each cable is pulled by one servo,
  so the joint torque cap is unchanged; only the mass changes.
- The cap is applied as joint torque, i.e. it assumes spool radius = cable
  moment arm.
Same protocol as diag_torque_cap: open floor (medium-lattice gait) and medium
lattice, G = 0, 0.75 and 1, 3 seeds, 6 cycles.
Not modelled: servo speed limits (0.10 / 0.19 s per 60 deg; the gait needs at
most ~0.8 rad/s, i.e. ~0.16 s/60 deg at the peak), rotation range, backlash.
  python experiments/diag_servo_choice.py   # writes results/diag_servo_choice/<run_id>/
"""

import copy
import json
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
import yaml  # noqa: E402

from snake import config as cfgmod  # noqa: E402
from snake.runlog import new_run  # noqa: E402
from snake.trial import run_lattice_trial  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STIFFNESS = 0.02
GS = (0.0, 0.75, 1.0)
SEEDS = (1, 2, 3)
N_CYCLES = 6
GAIT = (59.5, 0.58)
KGCM = 0.0980665


def servo_specs():
    s = yaml.safe_load(open(ROOT / "config" / "servos.yaml"))
    mg90 = s["MG90S"]
    t90 = mg90["stall_kgcm_at_4p8V"]["value"] + (6 - 4.8) / (6.6 - 4.8) * (
        mg90["stall_kgcm_at_6p6V"]["value"] - mg90["stall_kgcm_at_4p8V"]["value"]
    )
    return {
        "MG90S": (t90 * KGCM, mg90["mass_kg"]["value"]),
        "MG996R": (s["MG996R"]["stall_kgcm_at_6V"]["value"] * KGCM, s["MG996R"]["mass_kg"]["value"]),
    }


def job(args):
    name, n_per_joint, density, G, seed = args
    cap, mass = servo_specs()[name]
    cfg = cfgmod.load()
    cfg["joint"]["stiffness"] = STIFFNESS
    cfg["joint"]["passive_model"] = "none"  # as run (before the alpha-centred element, 2026-10-17)
    cfg["servo"]["stall_torque"] = cap
    cfg["mass"]["servo"] = mass
    cfg["mass"]["servos_per_joint"] = n_per_joint
    mc = copy.deepcopy(cfgmod.load("metrics.yaml"))
    mc["success"]["max_cycles"] = N_CYCLES
    r = run_lattice_trial(cfg, cfgmod.load("arena.yaml"), mc, density, *GAIT, 0.125, "paper", G, seed)
    return {
        "servo": f"{name}_x{n_per_joint}",
        "cap_Nm": cap,
        "density": density,
        "G": G,
        "seed": seed,
        "progress_rate_m_per_cycle": r["com_dx_per_cycle_m"],
        "progress_rate_full_horizon_m_per_cycle": r["com_dx_per_cycle_full_horizon_m"],
        "cycles_elapsed": r["cycles_elapsed"],
        "frac_time_any_joint_at_cap": r["frac_time_any_joint_at_cap"],
        "outcome": r["outcome"],
        "torque_peak_Nm": r["torque_peak_Nm"],
    }


def main():
    jobs = [
        (nm, n, dn, G, s)
        for nm in ("MG90S", "MG996R")
        for n in (1, 2)
        for dn in ("open", "medium")
        for G in GS
        for s in SEEDS
    ]
    with Pool() as pool:
        rows = pool.map(job, jobs)
    cells = {}
    for r in rows:
        k = f"{r['servo']}|{r['density']}|G={r['G']}"
        cells.setdefault(k, []).append(r)
    summary = {
        "specs_6V": {k: {"stall_Nm": v[0], "mass_kg": v[1]} for k, v in servo_specs().items()},
        "cells": {
            k: {
                "progress_rate_mean": float(np.mean([r["progress_rate_m_per_cycle"] for r in v])),
                "progress_rate_per_seed": [r["progress_rate_m_per_cycle"] for r in v],
                "full_horizon_rate_mean": float(np.mean([r["progress_rate_full_horizon_m_per_cycle"] for r in v])),
                "full_horizon_rate_per_seed": [r["progress_rate_full_horizon_m_per_cycle"] for r in v],
                "cycles_elapsed": [r["cycles_elapsed"] for r in v],
                "frac_time_any_joint_at_cap_mean": float(np.mean([r["frac_time_any_joint_at_cap"] for r in v])),
                "overload_endings": sum(r["outcome"] == "overload" for r in v),
                "outcomes": [r["outcome"] for r in v],
            }
            for k, v in cells.items()
        },
        "stiffness_Nm_per_rad": STIFFNESS,
        "gait": GAIT,
        "seeds": SEEDS,
        "n_cycles": N_CYCLES,
    }
    run_dir = new_run("diag_servo_choice", {"seeds": list(SEEDS)})
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    (run_dir / "trials.json").write_text(json.dumps(rows, indent=1))
    for k, v in summary["cells"].items():
        print(
            f"{k:28s} rate {v['progress_rate_mean']:+.4f}  full-horizon {v['full_horizon_rate_mean']:+.4f}  "
            f"at-cap {v['frac_time_any_joint_at_cap_mean']:.3f}  overloads {v['overload_endings']}/3  "
            f"cycles {[round(c, 1) for c in v['cycles_elapsed']]}"
        )
    print(f"saved {run_dir}")


if __name__ == "__main__":
    main()
