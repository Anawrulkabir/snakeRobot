"""H1 mechanism test: the pre-registered reading (docs/decisions.md, "H1 mechanism
test", 2026-10-18), applied to the open-floor runs. Lattice runs are tabulated only.

Per mid G in {0.5, 0.75} and seed s:
  curl-stall  progress(G) < 0.5 progress(0) and < 0.5 progress(1.0), and
              |curl(G)| >= 2 |curl(0)| and >= 2 |curl(1.0)|
  no-stall    |progress(G) - progress(ref)| <= 0.2 progress(ref) for ref = G 0 and G 1.0
Verdict: supported if curl-stall in >= 7/10 seeds at both mid G; rejected if
no-stall in >= 7/10 seeds at both mid G; otherwise unclear.

  python experiments/analyze_h1.py results/h1_mechanism/<run_id>
writes <run_dir>/summary.json
"""

import json
import sys
from pathlib import Path

PROG = "com_dx_per_cycle_full_horizon_m"
CURL = "curl_index_rad"
MID = (0.5, 0.75)
REFS = (0.0, 1.0)
NEED = 7


def curl_stall(t, G):
    """t: {G: row} for one seed on open floor."""
    p, c = t[G][PROG], abs(t[G][CURL])
    return all(p < 0.5 * t[r][PROG] for r in REFS) and all(c >= 2 * abs(t[r][CURL]) for r in REFS)


def no_stall(t, G):
    return all(abs(t[G][PROG] - t[r][PROG]) <= 0.2 * abs(t[r][PROG]) for r in REFS)


def verdict(by_seed):
    """by_seed: {seed: {G: row}} (open floor). Returns (verdict, counts)."""
    counts = {
        str(G): {
            "curl_stall": sum(curl_stall(t, G) for t in by_seed.values()),
            "no_stall": sum(no_stall(t, G) for t in by_seed.values()),
            "n_seeds": len(by_seed),
        }
        for G in MID
    }
    if all(counts[str(G)]["curl_stall"] >= NEED for G in MID):
        return "H1 supported", counts
    if all(counts[str(G)]["no_stall"] >= NEED for G in MID):
        return "H1 rejected", counts
    return "unclear", counts


def main():
    run_dir = Path(sys.argv[1])
    rows = [json.loads(x) for x in (run_dir / "trials.jsonl").read_text().splitlines() if x.strip()]
    diverged = [r["key"] for r in rows if r["outcome"] == "diverged"]
    ok = [r for r in rows if r["outcome"] != "diverged"]
    tables = {}
    for dn in ("open", "medium"):
        by = {}
        for r in ok:
            if r["density"] == dn:
                by.setdefault(r["seed"], {})[r["G"]] = r
        tables[dn] = by
    complete = {s: t for s, t in tables["open"].items() if all(G in t for G in (*MID, *REFS))}
    v, counts = verdict(complete)
    keep = (PROG, CURL, "body_axis_change_deg", "outcome", "cycles_elapsed", "final_com_dx_m", "tracking_rms_rad")
    out = {
        "run_id": run_dir.name,
        "n_rows": len(rows),
        "diverged": diverged,
        "open_seeds_complete": len(complete),
        "verdict": v,
        "counts": counts,
        "per_seed": {
            dn: {str(s): {str(G): {k: t[G][k] for k in keep} for G in sorted(t)} for s, t in sorted(by.items())}
            for dn, by in tables.items()
        },
        "per_seed_flags_open": {
            str(s): {str(G): {"curl_stall": curl_stall(t, G), "no_stall": no_stall(t, G)} for G in MID}
            for s, t in sorted(complete.items())
        },
    }
    (run_dir / "summary.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({k: out[k] for k in ("n_rows", "diverged", "open_seeds_complete", "verdict", "counts")}, indent=2))


if __name__ == "__main__":
    main()
