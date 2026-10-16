"""Load-model diagnosis before E1 (Fahad, 2026-10-16). Writes results/diag_load/<run_id>/.

Step 1 (0.25 Hz): for rigid plane, roll/pitch springs and vertical slide:
  - mean normal force per wheel, head to tail;
  - mean and max axle tilt;
  - the drag ratio measured in place during the gait: the peak sideways
    friction coefficient |f_axle|/N over the peak forward one |f_roll|/N,
    over samples where the wheel carries real load. The drag test's 1.6 is
    the reference;
  - control: rigid vs slide with uniform segment masses (head = body
    segment), to separate mass distribution from the vertical freedom itself.
Step 2: vertical slide at 0.0625 and 0.125 Hz, with contact time constant
  0.02 s and 0.04 s: is displacement per cycle on a quasi-static plateau?

  python experiments/diag_load.py
"""
import copy
import json
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402

from snake import config as cfgmod  # noqa: E402
from snake import metrics  # noqa: E402
from snake.runlog import new_run  # noqa: E402
from snake.sim import run_trial  # noqa: E402

SEEDS = list(range(1000, 1005))
N_CYCLES, SKIP = 6, 1
LOADED = 0.25   # a sample counts as loaded if N > 25% of the wheel's mean share
VARIANTS = {
    "rigid": dict(vertical_compliance="none"),
    "rollpitch": dict(vertical_compliance="rollpitch", vertical_stiffness=2.0, vertical_damping=0.01),
    "slide": dict(vertical_compliance="slide", vertical_stiffness=380.0, vertical_damping=0.5),
}


def make_cfg(base, variant, uniform_mass=False, contact_timeconst=None):
    c = copy.deepcopy(base)
    c["body"].update(VARIANTS[variant])
    if uniform_mass:
        c["mass"]["head_electronics"] = c["mass"]["servos_per_joint"] * c["mass"]["servo"]
    if contact_timeconst is not None:
        c["ground"]["contact_timeconst"] = contact_timeconst
    return c


def worker(job):
    label, cfg, gait, freq, seed = job
    r = run_trial(cfg, gait, freq, N_CYCLES, seed, detail_after_cycles=SKIP)
    n = N_CYCLES - SKIP
    heading = metrics.mean_body_heading(r["t"], r["body_axis_xy"], freq, SKIP, n)
    fwd, _ = metrics.displacement_per_cycle(r["t"], r["com_xy"], freq, SKIP, n, heading)
    w = r["wheel_detail"]
    N = w["normal"]
    share = N.mean() if N.size else 0.0
    ok = N > LOADED * share
    mu_side = w["f_axle"][ok] / N[ok]
    mu_fwd = w["f_roll"][ok] / N[ok]
    return {
        "label": label, "freq_hz": freq, "seed": seed,
        "forward_disp_per_cycle_m": fwd,
        "wheel_airborne_fraction": r["wheel_airborne_fraction"],
        "normal_mean_per_wheel_N": N.mean(axis=0).tolist(),
        "tilt_mean_deg": float(w["tilt_deg"].mean()),
        "tilt_max_deg": float(w["tilt_deg"].max()),
        "mu_side_p99": float(np.percentile(mu_side, 99)),
        "mu_fwd_p99": float(np.percentile(mu_fwd, 99)),
        "mu_side_max": float(mu_side.max()),
        "mu_fwd_max": float(mu_fwd.max()),
    }


def agg(rows):
    out = {}
    for label in dict.fromkeys(r["label"] for r in rows):
        for f in sorted({r["freq_hz"] for r in rows if r["label"] == label}):
            sub = [r for r in rows if r["label"] == label and r["freq_hz"] == f]
            m, h = metrics.mean_ci95([r["forward_disp_per_cycle_m"] for r in sub])
            side99 = float(np.mean([r["mu_side_p99"] for r in sub]))
            fwd99 = float(np.mean([r["mu_fwd_p99"] for r in sub]))
            out.setdefault(label, {})[str(f)] = {
                "n": len(sub),
                "forward_disp_per_cycle_m": {"mean": m, "ci95_half": h},
                "wheel_airborne_fraction": float(np.mean([r["wheel_airborne_fraction"] for r in sub])),
                "normal_mean_per_wheel_N_head_to_tail": np.mean(
                    [r["normal_mean_per_wheel_N"] for r in sub], axis=0).tolist(),
                "tilt_mean_deg": float(np.mean([r["tilt_mean_deg"] for r in sub])),
                "tilt_max_deg": float(np.max([r["tilt_max_deg"] for r in sub])),
                "mu_side_p99": side99,
                "mu_fwd_p99": fwd99,
                "in_gait_ratio_p99": side99 / fwd99,
                "in_gait_ratio_max": float(np.mean([r["mu_side_max"] for r in sub])) /
                float(np.mean([r["mu_fwd_max"] for r in sub])),
            }
    return out


def main():
    base = cfgmod.load()
    # As run (20261016T174857Z_00f197e): stiff position servos; each variant
    # sets its own load model.
    base["servo"]["actuation"] = "position"
    gait = cfgmod.load("gait.yaml")["wave"]
    gait = dict(gait, amplitude_deg=46, spatial_freq=0.82)  # as run: paper open-environment values, before the G4 x7/6 scaling
    jobs = []
    for v in VARIANTS:                                             # step 1
        jobs += [(v, make_cfg(base, v), gait, 0.25, s) for s in SEEDS]
    for v in ("rigid", "slide"):                                   # step 1 control
        jobs += [(f"{v}_uniform_mass", make_cfg(base, v, uniform_mass=True), gait, 0.25, s) for s in SEEDS]
    for tc in (0.02, 0.04):                                        # step 2
        for f in (0.0625, 0.125):
            jobs += [(f"slide_tc{tc}", make_cfg(base, "slide", contact_timeconst=tc), gait, f, s)
                     for s in SEEDS]
    with Pool() as pool:
        rows = pool.map(worker, jobs)
    summary = {"results": agg(rows), "variants": VARIANTS, "seeds": SEEDS,
               "loaded_threshold_of_mean_share": LOADED,
               "drag_test_reference_ratio": base["ground"]["anisotropy_ratio"],
               "segment_weights_N_head_to_tail": None}
    from snake.model_builder import segment_masses
    m = base["mass"]
    summary["segment_weights_N_head_to_tail"] = [
        (sm + m["wheel"]) * 9.81 for sm in segment_masses(base)]
    run_dir = new_run("diag_load", {"seeds": SEEDS})
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    (run_dir / "trials.json").write_text(json.dumps(rows))
    for label, per in summary["results"].items():
        for f, v in per.items():
            print(f"{label:22s} {f:>6s} Hz  disp {v['forward_disp_per_cycle_m']['mean']:.4f}"
                  f"+-{v['forward_disp_per_cycle_m']['ci95_half']:.4f}  air {v['wheel_airborne_fraction']:.3f}"
                  f"  tilt {v['tilt_mean_deg']:.2f}/{v['tilt_max_deg']:.2f}  ratio p99 {v['in_gait_ratio_p99']:.3f}"
                  f" max {v['in_gait_ratio_max']:.3f}  N {np.round(v['normal_mean_per_wheel_N_head_to_tail'], 3)}")
    print("segment weights N:", np.round(summary["segment_weights_N_head_to_tail"], 3))
    print(f"saved {run_dir}")


if __name__ == "__main__":
    main()
