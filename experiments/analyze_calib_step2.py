"""Calibration step 2: the pre-registered outcome rule (docs/decisions.md,
"Calibration step 2", Fahad 2026-10-17), plus joint-stop reporting.

S(G) = successes out of 5. mid = max(S(0.75), S(1.0)).
  mid-G wins:   mid >= S(0) + 2 and mid >= S(1.5) + 2
  reversed:     S(0) >= mid + 2 or S(1.5) >= mid + 2
  otherwise:    inconclusive
The mean full-horizon rate is reported, never used to break ties.

  python experiments/analyze_calib_step2.py results/calib_step2/<run_id>
writes <run_dir>/summary.json
"""

import json
import sys
from pathlib import Path

import numpy as np

PRIMARY = "com_dx_per_cycle_full_horizon_m"
MARGIN = 2


def outcome(S):
    """S: {G: successes}. Returns 'mid-G wins', 'reversed' or 'inconclusive'."""
    mid = max(S[0.75], S[1.0])
    if mid >= S[0.0] + MARGIN and mid >= S[1.5] + MARGIN:
        return "mid-G wins"
    if S[0.0] >= mid + MARGIN or S[1.5] >= mid + MARGIN:
        return "reversed"
    return "inconclusive"


def stop_split(rows):
    """Trials with any joint-stop contact vs none: count, successes, mean rate, mean cycles."""
    out = {}
    for name, sel in (
        ("with_stop_contact", [r for r in rows if r["stop_hit_cycle_fraction"] > 0]),
        ("without_stop_contact", [r for r in rows if r["stop_hit_cycle_fraction"] == 0]),
    ):
        out[name] = {
            "n": len(sel),
            "successes": sum(r["outcome"] == "success" for r in sel),
            "rate_mean": float(np.mean([r[PRIMARY] for r in sel])) if sel else None,
            "cycles_mean": float(np.mean([r["cycles_elapsed"] for r in sel])) if sel else None,
            "outcomes": {o: sum(r["outcome"] == o for r in sel) for o in ("success", "stuck", "overload", "timeout")},
        }
    return out


def main():
    run_dir = Path(sys.argv[1])
    rows = [json.loads(x) for x in (run_dir / "trials.jsonl").read_text().splitlines() if x.strip()]
    ok = [r for r in rows if r["outcome"] != "diverged"]
    Gs = sorted({r["G"] for r in ok})
    per = {}
    for G in Gs:
        rs = [r for r in ok if r["G"] == G]
        per[str(G)] = {
            "n": len(rs),
            "successes": sum(r["outcome"] == "success" for r in rs),
            "outcomes": {o: sum(r["outcome"] == o for r in rs) for o in ("success", "stuck", "overload", "timeout")},
            "rate_mean": float(np.mean([r[PRIMARY] for r in rs])),
            "final_com_dx_mean_m": float(np.mean([r["final_com_dx_m"] for r in rs])),
            "cycles_mean": float(np.mean([r["cycles_elapsed"] for r in rs])),
            "tracking_rms_rad_mean": float(np.mean([r["tracking_rms_rad"] for r in rs])),
            "stop_hit_cycle_fraction_mean": float(np.mean([r["stop_hit_cycle_fraction"] for r in rs])),
            "stop_hit_step_fraction_mean": float(np.mean([r["stop_hit_step_fraction"] for r in rs])),
            "n_trials_with_stop_contact": sum(r["stop_hit_cycle_fraction"] > 0 for r in rs),
        }
    S = {G: per[str(G)]["successes"] for G in Gs}
    complete = all(per[str(G)]["n"] == 5 for G in (0.0, 0.75, 1.0, 1.5))
    s = {
        "run_id": run_dir.name,
        "n_rows": len(rows),
        "diverged": [r["key"] for r in rows if r["outcome"] == "diverged"],
        "total_cpu_s": float(sum(r["cpu_s"] for r in rows)),
        "per_G": per,
        "successes_by_G": {str(k): v for k, v in S.items()},
        "outcome_rule": outcome(S) if complete else "not evaluated: a deciding G has fewer than 5 valid trials",
        "stop_contact_split_all_G": stop_split(ok),
        "stop_contact_split_by_G": {str(G): stop_split([r for r in ok if r["G"] == G]) for G in Gs},
    }
    (run_dir / "summary.json").write_text(json.dumps(s, indent=2))
    print(json.dumps({k: s[k] for k in ("n_rows", "diverged", "successes_by_G", "outcome_rule")}, indent=2))


if __name__ == "__main__":
    main()
