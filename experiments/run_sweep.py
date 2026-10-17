"""Resumable, parallel lattice sweep (CLAUDE.md 5.6). One JSON line per trial.

Every condition in the experiment file runs on the same seeds (paired design:
seed -> same start heading, lateral offset and wave phase for every law).
Trials already in trials.jsonl are skipped, so an interrupted run continues
where it stopped.

  python experiments/run_sweep.py config/experiments/E1_pilot.yaml            # new run
  python experiments/run_sweep.py config/experiments/E1_pilot.yaml --resume results/E1_pilot/<run_id>
  python experiments/run_sweep.py ... --workers 4
"""

import argparse
import json
import shutil
import sys
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from snake import config as cfgmod  # noqa: E402
from snake.runlog import jsonl_to_parquet, new_run  # noqa: E402
from snake.trial import run_lattice_trial  # noqa: E402


def key(variant, density, law, G, seed):
    base = f"{density}|{law}|{G}|{seed}"
    return base if variant is None else f"{variant}|{base}"


def jobs_for(ex):
    """Optional run.variants: {name: {dotted override: value}} (calibration sweeps).
    Overrides: robot.<group>.<key>, arena.<group>.<key>, metrics.<group>.<key>,
    and gait.amplitude_scale (multiplies the density's amplitude)."""
    seeds = range(ex["seed_start"], ex["seed_start"] + ex["n_trials"])
    variants = list(ex.get("variants", {None: {}}))
    return [
        (v, dn, law, G, s) for v in variants for dn in ex["densities"] for s in seeds for law, G in ex["conditions"]
    ]


def apply_overrides(overrides, cfg, arena, mc):
    amp_scale = 1.0
    tables = {"robot": cfg, "arena": arena, "metrics": mc}
    for path, value in overrides.items():
        # A number must stay a number: PyYAML reads "1.0e9" (no sign) as a string.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"override {path}: {value!r} is not a number")
        if path == "gait.amplitude_scale":
            amp_scale = value
            continue
        top, group, k = path.split(".")
        if k not in tables[top][group]:
            raise KeyError(f"override {path}: no such config entry")
        tables[top][group][k] = value
    return amp_scale


def job(args):
    run_dir, variant, density, law, G, seed = args
    # Configs come from the run's own snapshot, so a resumed run uses the same values.
    cdir = Path(run_dir) / "config"
    load = lambda n: cfgmod.values(cfgmod.yaml.safe_load(open(cdir / n)))  # noqa: E731
    cfg, arena, mc, ex = load("robot.yaml"), load("arena.yaml"), load("metrics.yaml"), load("experiment.yaml")["run"]
    A, xi = ex["gait_by_density"][density]
    if variant is not None:
        A *= apply_overrides(ex["variants"][variant], cfg, arena, mc)
    t0 = time.process_time()
    try:
        r = run_lattice_trial(
            cfg, arena, mc, density, A, xi, ex["temporal_freq_hz"], law, 0.0 if G is None else G, seed
        )
    except FloatingPointError as e:
        # Recorded, not retried: analyze.py reports it and drops the seed from paired comparisons.
        r = {
            "density": density,
            "law": law,
            "seed": seed,
            "outcome": "diverged",
            "error": str(e),
            "cycles_elapsed": float("nan"),
            "com_dx_per_cycle_full_horizon_m": float("nan"),
            "t_end_s": 0.0,
        }
    r["G"] = G
    r["variant"] = variant
    r["cpu_s"] = time.process_time() - t0
    r["key"] = key(variant, density, law, G, seed)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("experiment")
    ap.add_argument("--resume")
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args()
    exp_path = Path(a.experiment)
    if a.resume:
        run_dir = Path(a.resume)
    else:
        run_dir = new_run(exp_path.stem, meta={"experiment_file": str(exp_path)})
        shutil.copy(exp_path, run_dir / "config" / "experiment.yaml")
    ex = cfgmod.values(cfgmod.yaml.safe_load(open(run_dir / "config" / "experiment.yaml")))["run"]
    out = run_dir / "trials.jsonl"
    done = set()
    if out.exists():
        for line in out.read_text().splitlines():
            if line.strip():
                done.add(json.loads(line)["key"])
    todo = [(str(run_dir), *j) for j in jobs_for(ex) if key(*j) not in done]
    print(f"{run_dir}: {len(done)} done, {len(todo)} to run", flush=True)
    with Pool(a.workers) as pool, open(out, "a") as f:
        for i, r in enumerate(pool.imap_unordered(job, todo), 1):
            f.write(json.dumps(r) + "\n")
            f.flush()
            print(
                f"[{i}/{len(todo)}] {r['key']} {r['outcome']} {r['cycles_elapsed']:.1f} cyc "
                f"rate_fh={r['com_dx_per_cycle_full_horizon_m']:.4f} cpu={r['cpu_s']:.0f}s",
                flush=True,
            )
    print(f"saved {out}")
    print(f"saved {jsonl_to_parquet(out)}")


if __name__ == "__main__":
    main()
