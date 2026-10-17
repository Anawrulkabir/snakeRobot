"""Bit-for-bit reproduction check of logged sweep trials.

Re-runs selected rows of a run's trials.jsonl from the run's own config
snapshot and compares every logged field exactly (float equality, after the
JSON round trip), except cpu_s. Exits 1 on any difference.

  python scripts/check_reproduction.py results/E1_pilot/<run_id> \
  --G 0 0.75 1.5 --seeds 1001 1002 1003 1004 1005
"""
import argparse
import json
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("run_sweep", ROOT / "experiments" / "run_sweep.py")
run_sweep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_sweep)

IGNORE = {"cpu_s"}


def rerun(args):
    run_dir, row = args
    job = (run_dir, row.get("variant"), row["density"], row["law"], row["G"], row["seed"])
    new = json.loads(json.dumps(run_sweep.job(job)))     # same JSON round trip as the log
    diffs = [k for k in sorted(set(row) | set(new)) if k not in IGNORE and row.get(k) != new.get(k)]
    return row["key"], diffs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--G", type=float, nargs="*")
    ap.add_argument("--seeds", type=int, nargs="*")
    ap.add_argument("--variant")
    a = ap.parse_args()
    rows = [json.loads(x) for x in (Path(a.run_dir) / "trials.jsonl").read_text().splitlines() if x.strip()]
    sel = [r for r in rows
           if (a.G is None or (r["G"] is not None and r["G"] in a.G))
           and (a.seeds is None or r["seed"] in a.seeds)
           and r.get("variant") == a.variant and r["law"] == "paper"]
    with Pool() as pool:
        res = pool.map(rerun, [(a.run_dir, r) for r in sel])
    bad = [(k, d) for k, d in res if d]
    import mujoco, numpy  # noqa: E401, E402
    print(f"python {sys.version.split()[0]}, mujoco {mujoco.__version__}, numpy {numpy.__version__}")
    print(f"{len(res)} trials re-run, {len(res) - len(bad)} identical in every logged field (cpu_s excluded)")
    for k, d in bad:
        print(f"DIFFERENT {k}: {d}")
    sys.exit(1 if bad or not res else 0)


if __name__ == "__main__":
    main()
