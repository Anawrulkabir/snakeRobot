"""Overload diagnosis for a sweep run (Fahad 2026-10-17, after the E1 pilot).

Re-runs every trial that ended by overload, from the run's own config
snapshot, with run_lattice_trial(diag=True). Each re-run must reproduce the
logged trial exactly (final CoM displacement and end time); a mismatch is
reported and the row is not used. For the overloading joint over the 1 s
overload window it records: whether that joint was on its hard stop, whether
the servo torque pushed into the stop, whether its adjacent segments touched
a post, and which side of the free range it was on.

  python experiments/diag_pilot_overloads.py results/E1_pilot/<run_id>
writes <run_dir>/summary_overload_diag.json
"""

import json
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from snake import config as cfgmod  # noqa: E402
from snake.trial import run_lattice_trial  # noqa: E402


def job(args):
    run_dir, row = args
    cdir = Path(run_dir) / "config"
    load = lambda n: cfgmod.values(cfgmod.yaml.safe_load(open(cdir / n)))  # noqa: E731
    cfg, arena, mc, ex = load("robot.yaml"), load("arena.yaml"), load("metrics.yaml"), load("experiment.yaml")["run"]
    A, xi = ex["gait_by_density"][row["density"]]
    G = row["G"]
    r = run_lattice_trial(
        cfg,
        arena,
        mc,
        row["density"],
        A,
        xi,
        ex["temporal_freq_hz"],
        row["law"],
        0.0 if G is None else G,
        row["seed"],
        diag=True,
    )
    same = (
        r["outcome"] == row["outcome"]
        and r["final_com_dx_m"] == row["final_com_dx_m"]
        and r["t_end_s"] == row["t_end_s"]
    )
    return {
        "key": row["key"],
        "law": row["law"],
        "G": G,
        "seed": row["seed"],
        "reproduced_exactly": same,
        **(r["overload_diag"] or {}),
    }


def main():
    run_dir = Path(sys.argv[1])
    rows = [json.loads(x) for x in (run_dir / "trials.jsonl").read_text().splitlines() if x.strip()]
    ov = [r for r in rows if r["outcome"] == "overload"]
    with Pool() as pool:
        res = pool.map(job, [(str(run_dir), r) for r in ov])
    ok = [r for r in res if r["reproduced_exactly"]]
    by = {}
    for r in ok:
        by.setdefault("tight_spool" if r["law"] == "tight_spool" else f"G={r['G']}", []).append(r)
    agg = {}
    for k, v in by.items():
        agg[k] = {
            "n_overloads": len(v),
            "joint_counts": {str(j): sum(r["joint"] == j for r in v) for j in range(1, 7)},
            "n_with_joint_on_stop_any_time": sum(r["frac_on_hard_stop"] > 0 for r in v),
            "n_with_torque_into_stop_any_time": sum(r["frac_torque_into_stop"] > 0 for r in v),
            "mean_frac_on_hard_stop": float(np.mean([r["frac_on_hard_stop"] for r in v])),
            "mean_frac_adjacent_segment_on_post": float(np.mean([r["frac_adjacent_segment_on_post"] for r in v])),
            "mean_frac_any_segment_on_post": float(np.mean([r["frac_any_segment_on_post"] for r in v])),
            "n_mostly_past_lower_bound": sum(r["frac_past_lower_bound"] > 0.5 for r in v),
            "n_mostly_past_upper_bound": sum(r["frac_past_upper_bound"] > 0.5 for r in v),
            "mean_overshoot_deg": float(np.mean([r["overshoot_deg_mean"] for r in v])),
        }
    out = {
        "run_id": run_dir.name,
        "n_overloads": len(ov),
        "n_reproduced_exactly": len(ok),
        "not_reproduced": [r["key"] for r in res if not r["reproduced_exactly"]],
        "by_condition": agg,
        "trials": res,
    }
    (run_dir / "summary_overload_diag.json").write_text(json.dumps(out, indent=2))
    print(
        json.dumps(
            {k: out[k] for k in ("n_overloads", "n_reproduced_exactly", "not_reproduced", "by_condition")}, indent=2
        )
    )


if __name__ == "__main__":
    main()
