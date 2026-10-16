"""E0: flat ground, no posts, stiff body (CLAUDE.md 6).

Runs every frequency in config/experiments/E0.yaml over the same seeds, plus
a timestep-convergence run and a passive energy check. Writes
results/E0/<run_id>/trials.csv and summary.json.

Every value in config/robot.yaml tagged 'placeholder' is still a placeholder,
so speeds are provisional (see run_info.json).

  python experiments/run_e0.py
"""
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from snake import config as cfgmod  # noqa: E402
from snake import metrics  # noqa: E402
from snake.runlog import new_run  # noqa: E402
from snake.sim import coast_energy_check, run_trial  # noqa: E402


def trial(args):
    cfg, gait, freq, seed, n_cycles, skip, timestep = args
    r = run_trial(cfg, gait, freq, n_cycles, seed, timestep)
    n_meas = n_cycles - skip
    body_heading = metrics.mean_body_heading(r["t"], r["body_axis_xy"], freq, skip, n_meas)
    fwd, net = metrics.displacement_per_cycle(r["t"], r["com_xy"], freq, skip, n_meas, body_heading)
    w = metrics.cycle_window(r["t"], freq, skip, n_meas)
    tq = metrics.summary_stats(r["actuator_torque"][w])
    L = cfg["body"]["n_segments"] * cfg["body"]["segment_pitch"]
    wavelength = L / gait["spatial_freq"]     # body arc length per wave
    mu = cfg["ground"]["friction_sliding"]
    speed = net * freq
    return {
        "freq_hz": freq,
        "seed": seed,
        "timestep_s": r["timestep"],
        "initial_heading_rad": r["heading"],
        "wave_phase_rad": r["phase"],
        "forward_disp_per_cycle_m": fwd,
        "net_disp_per_cycle_m": net,
        "forward_disp_per_cycle_body_lengths": fwd / L,
        "speed_m_per_s": speed,
        # Paper p. 34: eta = v_CoM / v_wave, v_wave = f * wavelength.
        "wave_efficiency_eta": fwd * freq / (freq * wavelength),
        # Paper p. 62: C = v0 / (mu g tau_cycle).
        "coasting_number": speed / (mu * 9.81 * (1 / freq)),
        "heading_drift_rad_per_cycle": metrics.heading_drift_per_cycle(r["t"], r["com_xy"], freq, skip, n_meas),
        "max_tracking_error_deg": float(np.degrees(np.abs(r["tracking_error"][w]).max())),
        "torque_mean_Nm": tq["mean"],
        "torque_p95_Nm": tq["p95"],
        "torque_peak_Nm": tq["peak"],
        "max_penetration_m": r["max_penetration"],
        "wheel_airborne_fraction": r["wheel_airborne_fraction"],
    }


def main():
    cfg = cfgmod.load()
    gait = cfgmod.load("gait.yaml")["wave"]
    e0 = cfgmod.load("experiments/E0.yaml")
    run, chk = e0["run"], e0["checks"]
    seeds = [run["base_seed"] + k for k in range(run["trials_per_frequency"])]

    jobs = [(cfg, gait, f, s, run["n_cycles"], run["skip_cycles"], None)
            for f in run["frequencies_hz"] for s in seeds]
    jobs += [(cfg, gait, run["convergence_frequency_hz"], s, run["n_cycles"], run["skip_cycles"],
              run["convergence_timestep"]) for s in seeds[: run["convergence_trials"]]]
    with Pool() as pool:
        rows = pool.map(trial, jobs)
    df = pd.DataFrame(rows)
    main_dt = cfg["sim"]["timestep"]

    per_freq = {}
    for f in run["frequencies_hz"]:
        sub = df[(df.freq_hz == f) & np.isclose(df.timestep_s, main_dt)]
        stat = {}
        for col in ("forward_disp_per_cycle_m", "net_disp_per_cycle_m", "forward_disp_per_cycle_body_lengths",
                    "speed_m_per_s", "wave_efficiency_eta", "coasting_number",
                    "heading_drift_rad_per_cycle", "max_tracking_error_deg", "torque_peak_Nm",
                    "torque_p95_Nm", "wheel_airborne_fraction"):
            m, h = metrics.mean_ci95(sub[col])
            stat[col] = {"mean": m, "ci95_half": h}
        stat["n_trials"] = int(len(sub))
        stat["all_moved_forward"] = bool((sub.forward_disp_per_cycle_m > 0).all())
        per_freq[str(f)] = stat

    disp = {f: per_freq[str(f)]["forward_disp_per_cycle_m"]["mean"] for f in run["frequencies_hz"]}
    mean_disp = float(np.mean(list(disp.values())))
    quasi_dev = {str(f): v / mean_disp - 1 for f, v in disp.items()}

    fc = run["convergence_frequency_hz"]
    a = df[(df.freq_hz == fc) & np.isclose(df.timestep_s, main_dt)].set_index("seed")
    b = df[(df.freq_hz == fc) & np.isclose(df.timestep_s, run["convergence_timestep"])].set_index("seed")
    common = b.index
    conv_rel = (b.loc[common, "forward_disp_per_cycle_m"] / a.loc[common, "forward_disp_per_cycle_m"] - 1)

    energy = coast_energy_check(cfg)
    rel_energy = energy["max_energy_increase_J"] / energy["initial_energy_J"]

    checks = {
        "moves_forward_all_trials": all(per_freq[k]["all_moved_forward"] for k in per_freq),
        "max_penetration_m": float(df.max_penetration_m.max()),
        "penetration_ok": bool(df.max_penetration_m.max() <= chk["max_penetration_m"]),
        "energy": energy,
        "relative_energy_increase": rel_energy,
        "energy_ok": bool(rel_energy <= chk["max_relative_energy_increase"]),
        "timestep_convergence_rel_per_seed": {int(k): float(v) for k, v in conv_rel.items()},
        "timestep_convergence_max_abs_rel": float(np.abs(conv_rel).max()),
        "timestep_ok": bool(np.abs(conv_rel).max() <= chk["timestep_tolerance_rel"]),
        "quasi_static_deviation_rel": quasi_dev,
        "quasi_static": bool(max(abs(v) for v in quasi_dev.values()) <= chk["quasi_static_tolerance_rel"]),
    }
    summary = {"per_frequency": per_freq, "checks": checks,
               "gait": gait, "seeds": seeds, "thresholds": chk}

    run_dir = new_run("E0", {"seeds": seeds})
    df.to_csv(run_dir / "trials.csv", index=False)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(checks, indent=2))
    for f in run["frequencies_hz"]:
        s = per_freq[str(f)]
        print(f"{f} Hz: forward/cycle {s['forward_disp_per_cycle_m']['mean']:.4f} "
              f"+- {s['forward_disp_per_cycle_m']['ci95_half']:.4f} m, "
              f"track err {s['max_tracking_error_deg']['mean']:.2f} deg, "
              f"airborne {s['wheel_airborne_fraction']['mean']:.3f}")
    print(f"saved {run_dir}")


if __name__ == "__main__":
    main()
