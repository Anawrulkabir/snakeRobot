"""Chatter diagnosis before E1 (Fahad, 2026-10-16). Writes results/diag_chatter/<run_id>/.

1. E0 gait at 0.125/0.25/0.5 Hz for: baseline, softer tyre contact, stiffer servos.
2. Vertical bounce frequency: estimate from the contact solref, from the static sag,
   from a tap test on the resting body, versus the chatter frequency seen in
   the gait (at two timesteps and two contact time constants).
3. Over-constraint test at 0.25 Hz: per-segment roll/pitch springs, or an
   independent vertical slide per segment.

Diagnostic only; nothing here changes the approved model.
  python experiments/diag_chatter.py
"""
import copy
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import mujoco  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from run_e0 import trial  # noqa: E402
from snake import config as cfgmod  # noqa: E402
from snake import metrics  # noqa: E402
from snake.gait import serpenoid  # noqa: E402
from snake.model_builder import build_model  # noqa: E402
from snake.runlog import new_run  # noqa: E402

FREQS = (0.125, 0.25, 0.5)
SEEDS = list(range(1000, 1005))      # first 5 E0 seeds
N_CYCLES, SKIP = 6, 1

SOFT_TIMECONST = 0.04                # s, 2x MuJoCo's default 0.02
STIFF_KP = 20.0                      # N m/rad, 10x the placeholder; torque cap unchanged
# Over-constraint variants. Stiffness chosen so the out-of-plane deflection is
# small: segment weight ~0.38 N acting over ~0.05 m gives ~0.019 N m, which a
# 2 N m/rad spring holds at ~0.5 deg. The slide spring sags ~1 mm under 0.38 N.
ROLLPITCH = dict(vertical_compliance="rollpitch", vertical_stiffness=2.0, vertical_damping=0.01)
SLIDE = dict(vertical_compliance="slide", vertical_stiffness=380.0, vertical_damping=0.5)


def variant(cfg, name):
    c = copy.deepcopy(cfg)
    if name == "soft_contact":
        c["ground"]["contact_timeconst"] = SOFT_TIMECONST
    elif name == "stiff_servo":
        c["servo"]["kp"] = STIFF_KP
    elif name == "rollpitch":
        c["body"].update(ROLLPITCH)
    elif name == "slide":
        c["body"].update(SLIDE)
    elif name != "baseline":
        raise ValueError(name)
    return c


def gait_z_spectrum(cfg, freq=0.25, seconds=8.0):
    """Dominant frequency of the head's vertical motion during the gait, sampled every step."""
    m = build_model(cfg)
    d = mujoco.MjData(m)
    g = dict(cfgmod.load("gait.yaml")["wave"], amplitude_deg=46, spatial_freq=0.82)  # as run
    A = math.radians(g["amplitude_deg"])
    jq = [m.joint(f"j{i}").qposadr[0] for i in range(1, m.nu + 1)]
    d.qpos[jq] = serpenoid(0.0, A, g["spatial_freq"], freq, m.nu)
    z = []
    while d.time < seconds:
        d.ctrl[:] = serpenoid(d.time, A, g["spatial_freq"], freq, m.nu)
        mujoco.mj_step(m, d)
        if d.time > 2.0:
            z.append(d.qpos[m.joint("root_z").qposadr[0]])
    z = np.array(z) - np.mean(z)
    spec = np.abs(np.fft.rfft(z))
    fr = np.fft.rfftfreq(len(z), m.opt.timestep)
    k = spec[1:].argmax() + 1
    return {"dominant_hz": float(fr[k]), "z_peak_to_peak_m": float(z.max() - z.min())}


def tap_test(cfg, v_tap=-0.005, seconds=0.3):
    """Rest the straight body on its wheels, servos holding, then give it a small
    downward velocity and record the vertical response every step."""
    m = build_model(cfg)
    d = mujoco.MjData(m)
    zq, zv = m.joint("root_z").qposadr[0], m.joint("root_z").dofadr[0]
    for _ in range(2000):
        mujoco.mj_step(m, d)
    z_rest = d.qpos[zq]
    d.qvel[zv] = v_tap
    z = []
    for _ in range(int(seconds / m.opt.timestep)):
        mujoco.mj_step(m, d)
        z.append(d.qpos[zq] - z_rest)
    z = np.array(z)
    # Count overshoots past rest after the first minimum: 0 means no ringing.
    i_min = int(z.argmin())
    after = z[i_min:]
    crossings = int(np.sum(np.diff(np.sign(after)) != 0))
    return {
        "static_sag_m": float(-z_rest),
        "tap_min_m": float(z.min()),
        "tap_max_after_min_m": float(after.max()),
        "time_to_min_s": i_min * m.opt.timestep,
        "zero_crossings_after_min": crossings,
    }


def bounce_analysis(cfg):
    """Part 2: compare candidate natural frequencies with the observed chatter frequency."""
    tc = cfg["ground"]["contact_timeconst"]
    # MuJoCo solref (timeconst, dampratio) with default solimp dmax = 0.95.
    # From my reading of the MuJoCo docs (NOT verified here, no doc access):
    # reference stiffness k = 1 / (dmax^2 tc^2 dampratio^2) per unit penetration,
    # as an acceleration, so independent of mass. omega = sqrt(k) = 1 / (dmax tc).
    dmax = 0.95
    f_solref = 1 / (dmax * tc) / (2 * math.pi)
    tap = tap_test(cfg)
    f_sag = math.sqrt(9.81 / tap["static_sag_m"]) / (2 * math.pi) if tap["static_sag_m"] > 0 else None
    obs = {
        "dt_1ms_tc_0.02": gait_z_spectrum(cfg),
    }
    c = copy.deepcopy(cfg)
    c["sim"]["timestep"] = 0.0005
    obs["dt_0.5ms_tc_0.02"] = gait_z_spectrum(c)
    c = copy.deepcopy(cfg)
    c["ground"]["contact_timeconst"] = SOFT_TIMECONST
    obs[f"dt_1ms_tc_{SOFT_TIMECONST}"] = gait_z_spectrum(c)
    return {
        "contact_timeconst_s": tc,
        "solref_formula_hz_unverified": f_solref,
        "sag_implied_hz": f_sag,
        "tap_test": tap,
        "observed_gait_chatter": obs,
    }


def summarize(df):
    out = {}
    for (name, f), sub in df.groupby(["variant", "freq_hz"]):
        out.setdefault(name, {})[str(f)] = {
            "n": int(len(sub)),
            "forward_disp_per_cycle_m": dict(zip(("mean", "ci95_half"),
                                                 metrics.mean_ci95(sub.forward_disp_per_cycle_m))),
            "wheel_airborne_fraction": dict(zip(("mean", "ci95_half"),
                                                metrics.mean_ci95(sub.wheel_airborne_fraction))),
            "max_tracking_error_deg": float(sub.max_tracking_error_deg.mean()),
            "torque_peak_Nm": float(sub.torque_peak_Nm.mean()),
            "torque_p95_Nm": float(sub.torque_p95_Nm.mean()),
        }
    return out


def main():
    cfg = cfgmod.load()
    # As run (20261016T173615Z_5373862): stiff position servos on the rigid plane.
    cfg["servo"]["actuation"] = "position"
    cfg["body"]["vertical_compliance"] = "none"
    gait = cfgmod.load("gait.yaml")["wave"]
    gait = dict(gait, amplitude_deg=46, spatial_freq=0.82)  # as run: paper open-environment values, before the G4 x7/6 scaling
    jobs, labels = [], []
    for name in ("baseline", "soft_contact", "stiff_servo"):
        for f in FREQS:
            for s in SEEDS:
                jobs.append((variant(cfg, name), gait, f, s, N_CYCLES, SKIP, None))
                labels.append(name)
    for name in ("rollpitch", "slide"):
        for s in SEEDS:
            jobs.append((variant(cfg, name), gait, 0.25, s, N_CYCLES, SKIP, None))
            labels.append(name)
    with Pool() as pool:
        rows = pool.map(trial, jobs)
    df = pd.DataFrame(rows)
    df.insert(0, "variant", labels)

    summary = {
        "part1_and_3": summarize(df),
        "part2_bounce": bounce_analysis(cfg),
        "settings": {"soft_contact_timeconst_s": SOFT_TIMECONST, "stiff_kp_Nm_per_rad": STIFF_KP,
                     "rollpitch": ROLLPITCH, "slide": SLIDE, "seeds": SEEDS, "freqs_hz": FREQS},
    }
    run_dir = new_run("diag_chatter", {"seeds": SEEDS})
    df.to_csv(run_dir / "trials.csv", index=False)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    for name, per in summary["part1_and_3"].items():
        for f, v in per.items():
            print(f"{name:13s} {f:>5s} Hz: disp/cycle {v['forward_disp_per_cycle_m']['mean']:.4f} "
                  f"+- {v['forward_disp_per_cycle_m']['ci95_half']:.4f}  airborne "
                  f"{v['wheel_airborne_fraction']['mean']:.3f}  track {v['max_tracking_error_deg']:.2f} deg  "
                  f"peak tq {v['torque_peak_Nm']:.4f}")
    print(json.dumps(summary["part2_bounce"], indent=2))
    print(f"saved {run_dir}")


if __name__ == "__main__":
    main()
