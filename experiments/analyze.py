"""Paired analysis of a sweep run (E1 pilot and E1). Writes summary.json next to trials.jsonl.

Primary metric: full-horizon progress rate (metrics.progress_rate_full_horizon,
Fahad 2026-10-17). Per density:
  - per condition: mean and 95% CI (t) of the rate; outcome counts; success
    at the report cutoffs; mean of the secondary (elapsed) rate;
  - best condition = highest mean rate; best one-spool condition = highest
    mean among G >= 1 and the tight-spool law (g4_options.md);
  - paired differences (best minus each condition, same seeds): mean, SD,
    95% CI, and whether the CI lies within +-margin x best mean (equivalence);
  - trials needed so that the CI half-width t * SD / sqrt(n) fits inside
    the margin, for (a) a true difference equal to the observed mean
    difference and (b) a true difference of 0:
        n = smallest n with t_{0.975, n-1} * SD / sqrt(n) <= margin - |d|
    (no n exists when |d| >= margin).
  - survival vs distance: fraction of trials whose CoM got at least x
    forward, on a fixed grid.

  python experiments/analyze.py results/E1_pilot/<run_id> [--margin 0.15]
"""
import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
from scipy import stats  # noqa: E402

from snake import config as cfgmod  # noqa: E402

PRIMARY = "com_dx_per_cycle_full_horizon_m"
SECONDARY = "com_dx_per_cycle_m"
N_MAX = 100000


def cond_name(law, G):
    return "tight_spool" if law == "tight_spool" else f"G={G}"


def one_spool(law, G):
    return law == "tight_spool" or (G is not None and G >= 1.0)


def ci95(x):
    x = np.asarray(x, float)
    n = len(x)
    m = float(x.mean())
    if n < 2:
        return m, float("nan"), float("nan"), float("nan")
    sd = float(x.std(ddof=1))
    h = stats.t.ppf(0.975, n - 1) * sd / math.sqrt(n)
    return m, sd, m - h, m + h


def n_needed(sd, d, margin):
    room = margin - abs(d)
    if room <= 0 or not np.isfinite(sd):
        return None
    if sd == 0:
        return 2
    for n in range(2, N_MAX):
        if stats.t.ppf(0.975, n - 1) * sd / math.sqrt(n) <= room:
            return n
    return None


def analyze(rows, mcfg, margin):
    cutoffs = mcfg["report"]["success_cutoffs_cycles"]
    out = {}
    for dn in sorted({r["density"] for r in rows}):
        rs = [r for r in rows if r["density"] == dn]
        conds = sorted({(r["law"], r["G"]) for r in rs}, key=lambda c: (c[0] == "tight_spool", c[1] or 0))
        by = {c: {r["seed"]: r for r in rs if (r["law"], r["G"]) == c} for c in conds}
        seeds = sorted(set.intersection(*(set(v) for v in by.values())))
        per = {}
        for c in conds:
            x = [by[c][s][PRIMARY] for s in seeds]
            m, sd, lo, hi = ci95(x)
            oc = [by[c][s]["outcome"] for s in seeds]
            sc = [by[c][s]["success_cycles"] for s in seeds]
            per[cond_name(*c)] = {
                "law": c[0], "G": c[1], "one_spool": one_spool(*c), "n": len(seeds),
                "rate_mean": m, "rate_sd": sd, "rate_ci95": [lo, hi],
                "secondary_elapsed_rate_mean": float(np.mean([by[c][s][SECONDARY] for s in seeds])),
                "outcomes": {o: oc.count(o) for o in ("success", "stuck", "overload", "timeout")},
                "success_frac_at_cycles": {str(k): float(np.mean([v is not None and v <= k for v in sc]))
                                           for k in cutoffs},
                "final_com_dx_mean_m": float(np.mean([by[c][s]["final_com_dx_m"] for s in seeds])),
                "frac_time_any_joint_at_cap_mean": float(np.mean([by[c][s]["frac_time_any_joint_at_cap"]
                                                                  for s in seeds])),
                "stop_hit_cycle_fraction_mean": float(np.mean([by[c][s]["stop_hit_cycle_fraction"]
                                                               for s in seeds])),
                # Pooled: cycles with any joint-stop contact / all cycles run, over every trial.
                "stop_hit_cycle_fraction_pooled": float(
                    sum(by[c][s]["stop_hit_cycle_fraction"] * max(1, math.ceil(by[c][s]["cycles_elapsed"]))
                        for s in seeds) / sum(max(1, math.ceil(by[c][s]["cycles_elapsed"])) for s in seeds)),
                "tracking_rms_rad_mean": float(np.mean([by[c][s]["tracking_rms_rad"] for s in seeds])),
                "cpu_s_mean": float(np.mean([by[c][s]["cpu_s"] for s in seeds])),
                "cycles_elapsed_mean": float(np.mean([by[c][s]["cycles_elapsed"] for s in seeds])),
            }
        best = max(conds, key=lambda c: per[cond_name(*c)]["rate_mean"])
        spools = [c for c in conds if one_spool(*c)]
        best_spool = max(spools, key=lambda c: per[cond_name(*c)]["rate_mean"]) if spools else None
        best_mean = per[cond_name(*best)]["rate_mean"]
        M = margin * best_mean
        diffs = {}
        for c in conds:
            if c == best:
                continue
            d = [by[best][s][PRIMARY] - by[c][s][PRIMARY] for s in seeds]
            m, sd, lo, hi = ci95(d)
            diffs[cond_name(*c)] = {
                "mean": m, "sd": sd, "ci95": [lo, hi],
                "equivalent_within_margin": bool(lo >= -M and hi <= M),
                "n_needed_if_true_diff_as_observed": n_needed(sd, m, M),
                "n_needed_if_true_diff_zero": n_needed(sd, 0.0, M),
            }
        grid = np.round(np.arange(0.0, 2.01, 0.1), 2)
        surv = {cond_name(*c): [float(np.mean([by[c][s]["final_com_dx_m"] >= g for s in seeds])) for g in grid]
                for c in conds}
        table = {str(s): {cond_name(*c): {"rate": by[c][s][PRIMARY], "outcome": by[c][s]["outcome"],
                                          "cycles": by[c][s]["cycles_elapsed"]} for c in conds}
                 for s in seeds}
        out[dn] = {"seeds": seeds, "conditions": per, "per_seed": table,
                   "overload_fraction_all_conditions": float(np.mean([r["outcome"] == "overload" for r in rs])), "best": cond_name(*best),
                   "best_one_spool": cond_name(*best_spool) if best_spool else None,
                   "margin_frac": margin, "margin_m_per_cycle": M,
                   "paired_diff_best_minus": diffs,
                   "survival_grid_m": grid.tolist(), "survival_frac": surv}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--margin", type=float, default=0.15)
    a = ap.parse_args()
    run_dir = Path(a.run_dir)
    allrows = [json.loads(line) for line in (run_dir / "trials.jsonl").read_text().splitlines() if line.strip()]
    diverged = [r["key"] for r in allrows if r["outcome"] == "diverged"]
    rows = [r for r in allrows if r["outcome"] != "diverged"]   # their seeds drop out of the paired sets
    mcfg = cfgmod.values(cfgmod.yaml.safe_load(open(run_dir / "config" / "metrics.yaml")))
    s = {"run_id": run_dir.name, "n_rows": len(allrows), "diverged": diverged, "primary_metric": PRIMARY,
         "total_cpu_s": float(sum(r["cpu_s"] for r in allrows)),
         "total_sim_s": float(sum(r["t_end_s"] for r in allrows)),
         "by_density": analyze(rows, mcfg, a.margin)}
    s["cpu_s_per_sim_s"] = s["total_cpu_s"] / s["total_sim_s"]
    (run_dir / "summary.json").write_text(json.dumps(s, indent=2))
    print(json.dumps(s, indent=2))


if __name__ == "__main__":
    main()
