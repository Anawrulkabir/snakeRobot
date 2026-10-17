"""Calibration step 1 analysis and the pre-registered step-2 selection
(docs/decisions.md, 2026-10-17, "Calibration before E1").

Per variant x G: successes, outcomes, mean full-horizon rate, mean final CoM
displacement, paired difference to the baseline. Then, per assumption, the
level chosen by the pre-registered rule at G = 0.75 among the levels marked
plausible a priori (PLAUSIBLE below, copied from decisions.md before step 1
ran). Also checks that the baseline rows reproduce the pilot exactly.

  python experiments/analyze_calibration.py results/calib_step1/<run_id> \
      --pilot results/E1_pilot/20261017T062232Z_b5aac2a
writes <run_dir>/summary.json
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PRIMARY = "com_dx_per_cycle_full_horizon_m"
SELECT_G = 0.75
# Assumption -> {variant: plausible a priori}. 'baseline' belongs to every group.
PLAUSIBLE = {
    "post_friction": {"baseline": True, "friction_0.2": True, "friction_0.1": True},
    "servo_torque": {"baseline": True, "servo_paper_eq": True, "servo_bound_1.0": False},
    "overload_rule": {"baseline": True, "overload_3s": True, "overload_off": False},
    "amplitude": {"baseline": True, "amp_0.85": True},
    "passive_coeff": {"baseline": True, "passive_x4": True},
}


def cell_stats(rows):
    return {
        "n": len(rows),
        "successes": sum(r["outcome"] == "success" for r in rows),
        "outcomes": {
            o: sum(r["outcome"] == o for r in rows) for o in ("success", "stuck", "overload", "timeout", "diverged")
        },
        "rate_mean": float(np.mean([r[PRIMARY] for r in rows])),
        "final_com_dx_mean_m": float(np.mean([r["final_com_dx_m"] for r in rows])),
        "cycles_mean": float(np.mean([r["cycles_elapsed"] for r in rows])),
        "tracking_rms_rad_mean": float(np.mean([r["tracking_rms_rad"] for r in rows])),
        "stop_hit_cycle_fraction_mean": float(np.mean([r["stop_hit_cycle_fraction"] for r in rows])),
    }


def select(group, cells):
    """Pre-registered rule. cells: {variant: cell_stats at G = 0.75}. Returns (variant, reason)."""
    cand = [v for v, ok in PLAUSIBLE[group].items() if ok and v in cells]
    if any(cells[v]["successes"] > 0 for v in cand):
        score = lambda v: (cells[v]["successes"], cells[v]["rate_mean"], v == "baseline")  # noqa: E731
        why = "most successes at G = 0.75, ties by mean full-horizon rate"
    else:
        score = lambda v: (cells[v]["rate_mean"], v == "baseline")  # noqa: E731
        why = "no plausible level succeeded at G = 0.75: highest mean full-horizon rate"
    return max(cand, key=score), why


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--pilot")
    a = ap.parse_args()
    run_dir = Path(a.run_dir)
    rows = [json.loads(x) for x in (run_dir / "trials.jsonl").read_text().splitlines() if x.strip()]
    ok = [r for r in rows if r["outcome"] != "diverged"]
    variants = sorted({r["variant"] for r in rows}, key=lambda v: (v != "baseline", v))
    Gs = sorted({r["G"] for r in rows})
    cells = {
        v: {str(G): cell_stats([r for r in ok if r["variant"] == v and r["G"] == G]) for G in Gs} for v in variants
    }
    base = {(r["G"], r["seed"]): r for r in ok if r["variant"] == "baseline"}
    paired = {}
    for v in variants:
        if v == "baseline":
            continue
        paired[v] = {}
        for G in Gs:
            d = [
                r[PRIMARY] - base[(G, r["seed"])][PRIMARY]
                for r in ok
                if r["variant"] == v and r["G"] == G and (G, r["seed"]) in base
            ]
            paired[v][str(G)] = {"mean_diff_vs_baseline": float(np.mean(d)) if d else None, "n": len(d)}
    sel = {}
    for g in PLAUSIBLE:
        v, why = select(g, {k: cells[k][str(SELECT_G)] for k in PLAUSIBLE[g] if k in cells})
        sel[g] = {"chosen": v, "reason": why}
    out = {
        "run_id": run_dir.name,
        "n_rows": len(rows),
        "diverged": [r["key"] for r in rows if r["outcome"] == "diverged"],
        "total_cpu_s": float(sum(r["cpu_s"] for r in rows)),
        "cells": cells,
        "paired_vs_baseline": paired,
        "plausible_a_priori": PLAUSIBLE,
        "step2_selection_at_G": SELECT_G,
        "step2_selection": sel,
    }
    if a.pilot:
        pilot = {
            (r["G"], r["seed"]): r
            for r in map(json.loads, (Path(a.pilot) / "trials.jsonl").read_text().splitlines())
            if r["law"] == "paper"
        }
        mism = [
            f"G={G}|{s}"
            for (G, s), r in base.items()
            if (G, s) not in pilot
            or (pilot[(G, s)]["final_com_dx_m"], pilot[(G, s)]["t_end_s"], pilot[(G, s)]["outcome"])
            != (r["final_com_dx_m"], r["t_end_s"], r["outcome"])
        ]
        out["baseline_reproduces_pilot"] = {"pilot_run": Path(a.pilot).name, "n_checked": len(base), "mismatches": mism}
    (run_dir / "summary.json").write_text(json.dumps(out, indent=2))
    print(
        json.dumps(
            {
                k: out[k]
                for k in ("n_rows", "diverged", "step2_selection") + (("baseline_reproduces_pilot",) if a.pilot else ())
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
