"""G6 diagnosis: real jamming vs compliance-law artefact in the stuck mid-G trials
of calibration step 2. The criteria and thresholds are pre-registered in
docs/decisions.md ("G6: diagnose the stuck mid-G trials", 2026-10-18); this
script applies them mechanically.

Trials (combined step-2 setup):
  stuck       the stuck trials at G = 0.5 and 0.75, replayed from the step-2 run
              (each replay must match its log exactly)
  comparison  the same seeds at G = 0 and 1.0, replayed from the step-2 run
  narrow      the same seeds at G = 0.6 and 0.7, fresh runs (diagnostic only)

  python experiments/diag_stuck.py results/calib_step2/<run_id>
writes results/diag_stuck/<run_id>/summary.json and trials.jsonl
"""

import argparse
import importlib.util
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402

from animate_trial import commanded_shape, replay  # noqa: E402
from snake import config as cfgmod  # noqa: E402
from snake.runlog import new_run  # noqa: E402
from snake.trial import push_side, run_lattice_trial  # noqa: E402

_spec = importlib.util.spec_from_file_location("run_sweep", ROOT / "experiments" / "run_sweep.py")
run_sweep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_sweep)

VARIANT = "combined"
STUCK_G = (0.5, 0.75)
COMPARE_G = (0.0, 1.0)
NARROW_G = (0.6, 0.7)
# Pre-registered thresholds (decisions.md).
FRAC = 0.5  # J1-J3, A1: share of the window
NEIGHBOUR_MAX = 0.10  # A1: neighbour post contact at most this share
A2_FRAC = 0.01
TAU_PUSH = 0.05  # N m, J2
BOUNDARY_TOL = math.radians(1.0)
INSIDE_TOL = 1e-6  # rad, A2 "strictly inside"
WINDOW_CYCLES = 10


def seg_dist(p, a, b):
    """Distance from point p to segment ab (2D)."""
    ab, ap = b - a, p - a
    t = np.clip(np.dot(ap, ab) / max(np.dot(ab, ab), 1e-12), 0.0, 1.0)
    return float(np.linalg.norm(ap - t * ab))


def metrics(rec, row, stuck):
    """Pre-registered criteria for one trial. Window: the last 10 cycles if the
    trial ended stuck, else the whole trial."""
    period = rec["period_s"]
    frames = rec["frames"]
    t_end = frames[-1]["t"]
    win = [f for f in frames if f["t"] >= t_end - WINDOW_CYCLES * period] if stuck else frames
    tau = np.array([f["tau"] for f in win])
    j = int(np.argmax(np.abs(tau).mean(axis=0)))  # 0-based: joint j+1, between seg j and seg j+1
    sides = np.array([f["post_side"] for f in win], dtype=bool)  # frames x segments x [left, right]
    neigh = sides[:, [j, j + 1], :]
    posts = np.array(rec["posts"])
    reach = rec["post_radius"] + rec["capsule_radius"]
    # J1: posts on opposite sides of the body at the same time
    j1 = float(np.mean(sides[:, :, 0].any(axis=1) & sides[:, :, 1].any(axis=1)))
    # J2: stuck joint torque >= 0.05 N m and a neighbour touches a post on the side the torque pushes toward
    hits = []
    for k, f in enumerate(win):
        t_j = f["tau"][j]
        s = push_side(t_j)
        idx = 0 if s > 0 else 1
        hits.append(abs(t_j) >= TAU_PUSH and s != 0 and bool(neigh[k, :, idx].any()))
    j2 = float(np.mean(hits))
    # J3: the commanded shape (hung from the actual head) overlaps a post
    over = []
    for f in win:
        c = commanded_shape(f, rec["segment_pitch"])
        near = posts[np.linalg.norm(posts - c[0], axis=1) < 1.0] if len(posts) else posts
        over.append(any(seg_dist(p, c[i], c[i + 1]) < reach for p in near for i in range(len(c) - 1)))
    j3 = float(np.mean(over))
    # A1: stuck joint at/past a slack-range boundary, neighbours (almost) free of posts
    z = np.array([f["q"][j] for f in win])
    lo = np.array([f["range"][j][0] for f in win])
    hi = np.array([f["range"][j][1] for f in win])
    at_bound = float(np.mean((z <= lo + BOUNDARY_TOL) | (z >= hi - BOUNDARY_TOL)))
    neigh_contact = float(np.mean(neigh.any(axis=(1, 2))))
    # A2: servo torque while strictly inside the slack range (paired with the angle the torque came from)
    zc = np.array([f["zeta_ctrl"][j] for f in win])
    inside = (zc > lo + INSIDE_TOL) & (zc < hi - INSIDE_TOL)
    a2 = float(np.mean(inside & (np.abs(tau[:, j]) > 1e-9)))
    return {
        "key": f"G={row['G']}|{row['seed']}",
        "G": row["G"],
        "seed": row["seed"],
        "outcome": row["outcome"],
        "cycles": row["cycles_elapsed"],
        "window_frames": len(win),
        "stuck_joint": j + 1,
        "stuck_joint_mean_abs_tau_Nm": float(np.abs(tau[:, j]).mean()),
        "J1_frac": j1,
        "J2_frac": j2,
        "J3_frac": j3,
        "A1_at_boundary_frac": at_bound,
        "A1_neighbour_contact_frac": neigh_contact,
        "A2_frac": a2,
        "J1": j1 >= FRAC,
        "J2": j2 >= FRAC,
        "J3": j3 >= FRAC,
        "A1": at_bound >= FRAC and neigh_contact <= NEIGHBOUR_MAX,
        "A2": a2 > A2_FRAC,
    }


def job(args):
    kind, run_dir, G, seed = args
    if kind in ("stuck", "comparison"):
        row, _, rec = replay(run_dir, seed, G, "paper", VARIANT)
    else:
        cdir = Path(run_dir) / "config"
        load = lambda n: cfgmod.values(cfgmod.yaml.safe_load(open(cdir / n)))  # noqa: E731
        cfg, arena, mc, ex = (
            load("robot.yaml"),
            load("arena.yaml"),
            load("metrics.yaml"),
            load("experiment.yaml")["run"],
        )
        A, xi = ex["gait_by_density"]["medium"]
        A *= run_sweep.apply_overrides(ex["variants"][VARIANT], cfg, arena, mc)
        rec = {}
        r = run_lattice_trial(cfg, arena, mc, "medium", A, xi, ex["temporal_freq_hz"], "paper", G, seed, record=rec)
        row = {"G": G, "seed": seed, "outcome": r["outcome"], "cycles_elapsed": r["cycles_elapsed"]}
    out = metrics(rec, row, stuck=row["outcome"] == "stuck")
    out["set"] = kind
    return out


def classify(r, a3):
    nj = sum(r[k] for k in ("J1", "J2", "J3"))
    art = r["A1"] or r["A2"] or a3
    if nj >= 2 and not art:
        return "real jamming"
    if art and nj <= 1:
        return "artefact"
    return "unclear"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step2_run")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    run = str(Path(a.step2_run))
    rows = [json.loads(x) for x in (Path(run) / "trials.jsonl").read_text().splitlines() if x.strip()]
    stuck = sorted((r["G"], r["seed"]) for r in rows if r["G"] in STUCK_G and r["outcome"] == "stuck")
    seeds = sorted({s for _, s in stuck})
    jobs = [("stuck", run, G, s) for G, s in stuck]
    jobs += [("comparison", run, G, s) for G in COMPARE_G for s in seeds]
    jobs += [("narrow", run, G, s) for G in NARROW_G for s in seeds]
    out_dir = new_run("diag_stuck", meta={"step2_run": Path(run).name, "n_jobs": len(jobs)})
    with Pool(a.jobs) as pool:
        res = pool.map(job, jobs)
    (out_dir / "trials.jsonl").write_text("".join(json.dumps(r) + "\n" for r in res))
    outcome = {(r["G"], r["seed"]): r["outcome"] for r in res}
    for r in rows:  # step-2 outcomes at the other G values, for A3 and the report
        outcome.setdefault((r["G"], r["seed"]), r["outcome"])
    st = [r for r in res if r["set"] == "stuck"]
    cmp_ = [r for r in res if r["set"] == "comparison"]
    for r in st:
        s = r["seed"]
        r["A3"] = (
            outcome.get((0.6, s)) == "stuck"
            and outcome.get((0.7, s)) == "stuck"
            and outcome.get((0.0, s)) != "stuck"
            and outcome.get((1.0, s)) != "stuck"
        )
        r["class"] = classify(r, r["A3"])
    disc = {}
    for c in ("J1", "J2", "J3", "A1", "A2"):
        n_st, n_cmp = sum(r[c] for r in st), sum(r[c] for r in cmp_)
        disc[c] = {"stuck_met": n_st, "comparison_met": n_cmp, "discriminates": n_st >= 5 and n_cmp <= 1}
    disc["A3"] = {"stuck_met": sum(r["A3"] for r in st), "comparison_met": None, "discriminates": None}
    counts = {k: sum(r["class"] == k for r in st) for k in ("artefact", "real jamming", "unclear")}

    def backed(cls, crits):
        # The criteria behind the class must pass the discrimination check (A3 is itself a cross-G comparison).
        used = {c for r in st if r["class"] == cls for c in crits if r[c]}
        return all(disc[c]["discriminates"] in (True, None) for c in used) and bool(used)

    if counts["artefact"] >= 5 and backed("artefact", ("A1", "A2", "A3")):
        verdict = "artefact"
    elif counts["real jamming"] >= 5 and backed("real jamming", ("J1", "J2", "J3")):
        verdict = "real jamming"
    else:
        verdict = "unclear"
    outcomes_by_seed = {
        str(s): {str(G): outcome.get((G, s)) for G in sorted({0.0, 0.25, 0.5, 0.6, 0.7, 0.75, 1.0, 1.25, 1.5})}
        for s in seeds
    }
    summary = {
        "run_id": out_dir.name,
        "step2_run": Path(run).name,
        "stuck_trials": [f"G={G}|{s}" for G, s in stuck],
        "per_stuck_trial": st,
        "comparison": cmp_,
        "narrow": [r for r in res if r["set"] == "narrow"],
        "outcomes_by_seed": outcomes_by_seed,
        "discrimination": disc,
        "class_counts": counts,
        "verdict": verdict,
        "recommendation": {"artefact": "option 3", "real jamming": "option 2", "unclear": "stop and report"}[verdict],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: summary[k] for k in ("run_id", "class_counts", "discrimination", "verdict")}, indent=2))


if __name__ == "__main__":
    main()
