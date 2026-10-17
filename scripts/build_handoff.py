# ruff: noqa: E501  (this script writes prose: manifest rows and captions)
"""Build media/handoff/ and media/handoff.zip: footage, stills, data, docs and
configs for an explainer video made elsewhere (Fahad 2026-10-17).

Every clip and still is re-rendered from a saved run by scripts/render_trial_3d.py
or scripts/animate_trial.py. Both replay the trial and stop if the replay does
not match its log, so nothing is drawn from an unverified replay. MANIFEST.md
gets one row per file: what it shows, the run ID and commit, the data basis,
and a caption.

  MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa python scripts/build_handoff.py [--jobs 3]
Existing renders are kept (delete a file to re-render it). Excluded on purpose:
paper_figures/ (authors' files), raw trials.jsonl / trials.parquet, .venv,
and any file over 15 MB (listed in MANIFEST.md if it happens).
"""

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import zipfile
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from snake import config as cfgmod  # noqa: E402
from snake.model_builder import segment_masses  # noqa: E402

OUT = ROOT / "media" / "handoff"
ZIP = ROOT / "media" / "handoff.zip"
MAX_FILE = 15e6
REPO = "https://github.com/Anawrulkabir/snakeRobot"
PR = "https://github.com/Anawrulkabir/snakeRobot/pull/1"
BRANCH = "claude/keen-knuth-hdt1w4"

PILOT = "results/E1_pilot/20261017T062232Z_b5aac2a"
CAL1 = "results/calib_step1/20261017T075321Z_dc2fb6c"
CAL2 = "results/calib_step2/20261017T111457Z_cc9bd78"
OPEN = "results/media_open_floor/20261017T112843Z_29c5654"

SIM = "simulation output (model inputs include placeholders: body-post and ground friction, segment masses)"

R3D = ["scripts/render_trial_3d.py"]
R2D = ["scripts/animate_trial.py"]
HD = ["--size", "1920x1080"]


def media_specs():
    """(path, command, shows, run, basis, caption)."""
    s = []

    def add(path, cmd, shows, run, caption, basis=SIM):
        s.append((path, cmd, shows, run, basis, caption))

    pilot_trials = [
        (
            0.0,
            "jam",
            "the head wedges between posts and joints 2-3 hold at the servo cap until the 1 s overload rule ends the trial",
        ),
        (0.75, "", "the paper's best-reported compliance; the head still jams and the trial ends by overload"),
        (1.5, "stall", "the loosest body cannot follow its commanded wave and stalls in front of the posts"),
    ]
    for G, tag, what in pilot_trials:
        name = f"pilot_seed1001_G{G}{'_' + tag if tag else ''}"
        add(
            f"video/3d_overhead_{name}.mp4",
            R3D + [PILOT, "--seed", "1001", "--G", str(G), "--duration", "15"] + HD,
            f"3D overhead render, E1 pilot medium lattice, seed 1001, G = {G}: {what}.",
            PILOT,
            f"Pilot, G = {G}: {what.split(';')[0]}.",
        )
        add(
            f"video/2d_topview_{name}.mp4",
            R2D + [PILOT, "--seed", "1001", "--G", str(G), "--duration", "15", "--fps", "30"] + HD,
            f"2D top-view replay of the same trial (G = {G}) with the commanded shape overlaid and joints at the cap in red.",
            PILOT,
            f"Top view, G = {G}: blue is the body, orange the shape the controller asks for.",
        )
    add(
        "video/2d_montage_pilot_seed1001_6G.mp4",
        R2D + [PILOT, "--seed", "1001", "--montage", "0,0.5,0.75,1.0,1.25,1.5", "--duration", "20", "--fps", "30"] + HD,
        "Six pilot trials (seed 1001, G = 0, 0.5, 0.75, 1.0, 1.25, 1.5) side by side on one scale.",
        PILOT,
        "Same start, six compliance settings: none of them gets through the medium lattice.",
    )
    add(
        "video/3d_angled_open_floor_G0.75.mp4",
        R3D + [OPEN, "--seed", "1001", "--G", "0.75", "--camera", "angled", "--seconds", "48", "--duration", "16"] + HD,
        "Angled close view of the robot on open floor (G = 0.75): capsule segments, wheels and joint motion.",
        OPEN,
        "The robot model: seven segments on passive wheels, driven by a travelling wave.",
    )
    add(
        "video/3d_overhead_calib1_friction0.1_seed1001_G0_pass.mp4",
        R3D + [CAL1, "--seed", "1001", "--G", "0.0", "--variant", "friction_0.1", "--duration", "16"] + HD,
        "Calibration step 1, variant friction_0.1 (body-post friction 0.1 instead of 0.4), G = 0, seed 1001: the robot crosses the lattice.",
        CAL1,
        "Same start as the pilot jam, but with slippery posts (friction 0.1): the stiff body gets through.",
    )

    def still(path, cmd, shows, run, caption, basis=SIM):
        s.append((path, cmd, shows, run, basis, caption))

    still(
        "stills/model_top.png",
        R3D + [OPEN, "--seed", "1001", "--G", "0.75", "--still", "0", "--tight"] + HD,
        "Top view of the robot model at its start pose on open floor.",
        OPEN,
        "Seven 3D-printable segments, 0.10 m apart; the head carries the electronics.",
        "model geometry from config (values tagged paper / decision / placeholder in config/robot.yaml)",
    )
    still(
        "stills/model_angled.png",
        R3D + [OPEN, "--seed", "1001", "--G", "0.75", "--camera", "angled", "--still", "0"] + HD,
        "Angled view of the robot model at its start pose on open floor (segments and wheels).",
        OPEN,
        "One passive wheel under each segment makes sliding sideways harder than rolling forward.",
        "model geometry from config (values tagged paper / decision / placeholder in config/robot.yaml)",
    )
    still(
        "stills/arena_start_pose.png",
        R3D + [PILOT, "--seed", "1001", "--G", "0.75", "--still", "0", "--view=-1.0,2.1,-0.95,0.95"] + HD,
        "The medium-density hexagonal post lattice (d = 0.103 m, L/d = 2.8) with the robot at its start pose.",
        PILOT,
        "The test: cross 1.95 m of posts within 40 gait cycles.",
        "arena geometry digitized/derived from the paper's densities; start pose from the run's seed",
    )
    still(
        "stills/jam_G0_overload_3d.png",
        R3D + [PILOT, "--seed", "1001", "--G", "0.0", "--still", "end"] + HD,
        "Last frame of the pilot G = 0 trial: segments next to the overloaded joints 2 and 3 in red.",
        PILOT,
        "Jam: the servo pulls at full torque while a post holds the joint.",
    )
    still(
        "stills/jam_G0_overload_2d.png",
        R2D + [PILOT, "--seed", "1001", "--G", "0.0", "--still", "end"] + HD,
        "Same jam in the 2D view: red joints at the servo cap, the commanded shape (orange) far from the body.",
        PILOT,
        "Where the body is versus where the controller wants it.",
    )
    still(
        "stills/stall_G1.5_2d.png",
        R2D + [PILOT, "--seed", "1001", "--G", "1.5", "--still", "end"] + HD,
        "Last frame of the pilot G = 1.5 trial: the loose body has stopped, far from its commanded shape.",
        PILOT,
        "Stall: too loose to push.",
    )
    still(
        "stills/pass_calib1_friction0.1_G0.png",
        R3D + [CAL1, "--seed", "1001", "--G", "0.0", "--variant", "friction_0.1", "--still", "end"] + HD,
        "Last frame of the passing trial (friction_0.1, G = 0, seed 1001): the head has crossed the far edge.",
        CAL1,
        "With low post friction the stiff body passes.",
    )
    still(
        "stills/joint_closeup_cable_anchors.png",
        R3D + [OPEN, "--seed", "1001", "--G", "0.75", "--camera", "closeup", "--joint", "3", "--still", "0"] + HD,
        "Close-up of joint 3 with see-through segments: the left (red) and right (green) cable anchor points and the cables.",
        OPEN,
        "Each joint is bent by two cables, one on each side.",
        "model geometry from config (anchor offsets L_c = L_j = 20 mm, decision G4)",
    )
    return s


def run_spec(spec):
    path, cmd, *_ = spec
    out = OUT / path
    if out.exists():
        return path, "kept", ""
    env = dict(os.environ, MUJOCO_GL="osmesa", PYOPENGL_PLATFORM="osmesa")
    p = subprocess.run([sys.executable, *cmd, "--out", str(out)], cwd=ROOT, env=env, capture_output=True, text=True)
    ok = p.returncode == 0 and out.exists()
    log = (p.stdout + p.stderr).strip().splitlines()
    return path, "rendered" if ok else "FAILED", " | ".join(log[-3:])


def jl(run):
    return [json.loads(x) for x in (ROOT / run / "trials.jsonl").read_text().splitlines() if x.strip()]


def write_csv(path, rows, cols):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


TRIAL_COLS = ["seed", "law", "G", "outcome", "cycles_elapsed", "com_dx_per_cycle_full_horizon_m", "final_com_dx_m"]


def data_files():
    """(path, shows, run, basis, caption); writes the files."""
    d = OUT / "data"
    out = []

    def trials(name, run, extra=()):
        rows = [r for r in jl(run) if r["outcome"] != "diverged"]
        write_csv(d / name, rows, ["variant", *TRIAL_COLS] if extra else TRIAL_COLS)
        return len(rows)

    n = trials("pilot_trials.csv", PILOT)
    out.append(
        (
            "data/pilot_trials.csv",
            f"E1 pilot, one row per trial ({n}): seed, law, G, ending, cycles, full-horizon rate (m/cycle), CoM distance (m).",
            PILOT,
            SIM,
            "160 trials, 0 successes: the floor effect.",
        )
    )
    n = trials("calib_step1_trials.csv", CAL1, extra=True)
    out.append(
        (
            "data/calib_step1_trials.csv",
            f"Calibration step 1, one row per trial ({n}), with the variant name.",
            CAL1,
            SIM,
            "One assumption changed at a time.",
        )
    )
    cal2 = ROOT / CAL2 / "summary.json"
    if cal2.exists():
        n = trials("calib_step2_trials.csv", CAL2, extra=True)
        out.append(
            (
                "data/calib_step2_trials.csv",
                f"Calibration step 2 (combined setup), one row per trial ({n}).",
                CAL2,
                SIM,
                "The pre-registered combination across the full G sweep.",
            )
        )
        shutil.copy(cal2, d / "calib_step2_summary.json")
        out.append(
            (
                "data/calib_step2_summary.json",
                "Calibration step 2 summary: successes per G, the pre-registered outcome, joint-stop split.",
                CAL2,
                SIM,
                "Step 2 verdict.",
            )
        )

    tc = json.loads((ROOT / "results/diag_torque_cap/20261016T191531Z_387fad8/summary.json").read_text())
    rows = []
    for k, v in tc["cells"].items():
        dn, G, cap = k.split("|")
        rows.append(
            {
                "density": dn,
                "G": G.split("=")[1],
                "cap_Nm": cap.split("=")[1],
                "progress_rate_mean_m_per_cycle": v["progress_rate_mean"],
                "frac_time_any_joint_at_cap": v["frac_time_any_joint_at_cap_mean"],
                "overload_endings": v["overload_endings"],
                "outcomes": " ".join(v["outcomes"]),
                "stop_hit_cycle_fraction": v["stop_hit_cycle_fraction_mean"],
            }
        )
    write_csv(d / "torque_cap_check.csv", rows, list(rows[0]))
    out.append(
        (
            "data/torque_cap_check.csv",
            "Torque-cap check: progress rate and time at the cap for servo caps 0.2 / 0.5 / 1.0 N m (older model: elapsed-cycles rate, no alpha-centred passive element, 6-cycle trials).",
            "results/diag_torque_cap/20261016T191531Z_387fad8",
            SIM,
            "A stronger servo mainly helps the stiff body.",
        )
    )

    dt = json.loads((ROOT / "results/drag_test/20261016T165908Z_dfd51e6/summary.json").read_text())
    write_csv(d / "drag_test.csv", dt["rows"], list(dt["rows"][0]))
    out.append(
        (
            "data/drag_test.csv",
            "Wheel drag test: forward and sideways drag force per segment type; target sideways/forward ratio 1.6.",
            "results/drag_test/20261016T165908Z_dfd51e6",
            SIM + "; target ratio 1.6 from the paper",
            "Sideways drag is 1.6 times forward drag, as in the paper's robot.",
        )
    )

    e0 = json.loads((ROOT / "results/E0/20261016T170631Z_ef124ae/summary.json").read_text())
    rows = [
        {
            "temporal_freq_hz": f,
            **{
                k: (v["mean"] if isinstance(v, dict) and "mean" in v else v)
                for k, v in m.items()
                if not isinstance(v, list)
            },
        }
        for f, m in e0["per_frequency"].items()
    ]
    write_csv(d / "e0_frequency.csv", rows, list(rows[0]))
    out.append(
        (
            "data/e0_frequency.csv",
            "E0 flat ground, stiff body: displacement per cycle and other metrics at 0.125 / 0.25 / 0.5 Hz (early model: rigid-plane load, position servos).",
            "results/E0/20261016T170631Z_ef124ae",
            SIM,
            "On flat ground the robot moves; speed per cycle barely depends on frequency.",
        )
    )

    dl = json.loads((ROOT / "results/diag_load/20261016T174857Z_00f197e/summary.json").read_text())
    rows = []
    for variant, byf in dl["results"].items():
        for f, v in byf.items():
            fd = v["forward_disp_per_cycle_m"]
            rows.append(
                {
                    "variant": variant,
                    "temporal_freq_hz": f,
                    "n": v.get("n"),
                    "forward_disp_per_cycle_m": fd["mean"] if isinstance(fd, dict) else fd,
                    "ci95_half_m": fd.get("ci95_half") if isinstance(fd, dict) else None,
                    "wheel_airborne_fraction": v.get("wheel_airborne_fraction"),
                    "in_gait_ratio_p99": v.get("in_gait_ratio_p99"),
                }
            )
    write_csv(d / "load_model_diagnosis.csv", rows, list(rows[0]))
    out.append(
        (
            "data/load_model_diagnosis.csv",
            "Load-model diagnosis: rigid plane vs per-segment vertical slide vs roll/pitch springs (and contact softness), flat ground.",
            "results/diag_load/20261016T174857Z_00f197e",
            SIM,
            "How the wheels share the load changes the speed by ~40%.",
        )
    )

    shutil.copy(
        ROOT / "results/stiffness_estimate/20261017T061904Z_10317fe/summary.json", d / "stiffness_estimate.json"
    )
    out.append(
        (
            "data/stiffness_estimate.json",
            "Passive restoring element fitted to paper Fig. 5A(iii) and scaled to this robot (three scalings).",
            "results/stiffness_estimate/20261017T061904Z_10317fe",
            "digitized from paper (Fig. 5A), scaled with estimated masses",
            "The joint's passive spring, measured from the paper's figure.",
        )
    )
    return out


DOCS = [
    "CLAUDE.md",
    "docs/decisions.md",
    "docs/progress.md",
    "docs/open_lists.md",
    "docs/paper_notes.md",
    "docs/literature_search.md",
    "docs/stiffness_interpretation.md",
]


def copy_docs_configs(head):
    rows = []
    for src in DOCS + sorted(str(p.relative_to(ROOT)) for p in (ROOT / "docs").glob("results_*.md")):
        dst = OUT / "docs" / Path(src).name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / src, dst)
        rows.append(
            (
                f"docs/{Path(src).name}",
                f"Copy of {src}.",
                f"commit {head}",
                "documentation (numbers cite run IDs)",
                "Project record.",
            )
        )
    for src in sorted((ROOT / "config").glob("*.yaml")) + sorted((ROOT / "config" / "experiments").glob("*.yaml")):
        rel = src.relative_to(ROOT / "config")
        dst = OUT / "config" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
        rows.append(
            (
                f"config/{rel}",
                f"Copy of config/{rel}.",
                f"commit {head}",
                "config: each value tagged paper / hardware / decision / proposal / placeholder",
                "Model parameters.",
            )
        )
    return rows


def run_commit(run):
    if run.startswith("commit "):
        return "-", run.split()[1]
    rid = Path(run).name
    return rid, rid.split("_", 1)[1]


def summary_block():
    cfg = cfgmod.load()
    masses = segment_masses(cfg)
    pilot = json.loads((ROOT / PILOT / "summary.json").read_text())["by_density"]["medium"]
    c1 = json.loads((ROOT / CAL1 / "summary.json").read_text())
    lines = [
        "# Handoff: compliant cable-driven snake robot (simulation)",
        "",
        "**This package documents a simulation.** No hardware exists yet. All footage is MuJoCo, re-rendered from saved runs; each",
        "replay was checked against its log before rendering.",
        "",
        "## Robot (config/robot.yaml)",
        "",
        f"- {cfg['body']['n_segments']} rigid segments, {cfg['body']['n_segments'] - 1} yaw joints, pitch {cfg['body']['segment_pitch']} m (body {cfg['body']['n_segments'] * cfg['body']['segment_pitch']:.1f} m), planar.",
        f"- Segment mass {masses[1] + cfg['mass']['wheel']:.3f} kg (body), {masses[0] + cfg['mass']['wheel']:.3f} kg (head with ESP32 and battery), each including its wheel: placeholders until weighed.",
        f"- One MG90S servo per joint, stall {cfg['servo']['stall_torque']} N m at 6 V; bilateral cables, anchors {cfg['cable']['half_spacing'] * 1000:.0f} mm off-centre.",
        "- Passive wheel under each segment (sideways : forward drag = 1.6 : 1). Compliance set by the paper's generalized compliance G (0 = stiff, 1.5 = loose).",
        "- Gait: serpenoid travelling wave, 0.125 Hz; medium lattice amplitude 59.5 deg (x0.85 = 50.6 deg in calibration step 2), 0.58 spatial waves.",
        "",
        "## Current stage",
        "",
        "Calibration before experiment E1 (does intermediate compliance get through post lattices best?).",
        "",
        "## Key numbers (copied from saved runs)",
        "",
        f"- E1 pilot (run `{Path(PILOT).name}`): 0 / {sum(c['n'] for c in pilot['conditions'].values())} successes at every G; overload fraction {pilot['overload_fraction_all_conditions']:.3f}.",
        f"- Calibration step 1 (run `{Path(CAL1).name}`): post friction 0.1 gave G = 0 {c1['cells']['friction_0.1']['0.0']['successes']}/5 and G = 0.75 {c1['cells']['friction_0.1']['0.75']['successes']}/5 successes; baseline 0/5 at both.",
    ]
    cal2 = ROOT / CAL2 / "summary.json"
    if cal2.exists():
        c2 = json.loads(cal2.read_text())
        sbg = ", ".join(f"G = {g}: {n}/5" for g, n in c2["successes_by_G"].items())
        lines.append(
            f"- Calibration step 2 (run `{Path(CAL2).name}`): successes {sbg}. Pre-registered outcome: **{c2['outcome_rule']}**."
        )
    else:
        lines.append("- Calibration step 2: not finished when this package was built.")
    lines += [
        "- Passive element (run `20261017T061904Z_10317fe`): c_q = 0.3372 N m/rad^2 on the paper's robot, 0.06489 friction-scaled (digitized from Fig. 5A).",
        "",
        "## Data basis",
        "",
        "Nothing in this package is a physical measurement; no robot has been built. Labels below:",
        "**simulation output** (numbers measured in the simulation; the model's inputs include placeholders),",
        "**digitized from paper**, **config** (tagged per value), **documentation**.",
        "",
    ]
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args()
    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    specs = media_specs()
    with Pool(a.jobs) as pool:
        results = pool.map(run_spec, specs)
    for p, status, log in results:
        print(f"{status:8} {p}  {log if status == 'FAILED' else ''}")
    rows = []
    status = {p: st for p, st, _ in results}
    for path, _, shows, run, basis, caption in specs:
        if status[path] != "FAILED":
            rows.append((path, shows, run, basis, caption))
    rows += data_files()
    rows += copy_docs_configs(head)
    (OUT / "links.txt").write_text(f"repository: {REPO}\npull request: {PR}\nbranch: {BRANCH}\n")
    rows.append(
        (
            "links.txt",
            "Repository, pull request and branch.",
            f"commit {head}",
            "documentation",
            "Where the code lives.",
        )
    )
    skipped = []
    for p in sorted(OUT.rglob("*")):
        if p.is_file() and p.stat().st_size > MAX_FILE:
            skipped.append(f"{p.relative_to(OUT)} ({p.stat().st_size / 1e6:.1f} MB)")
            p.unlink()
    rows = [r for r in rows if (OUT / r[0]).exists()]
    lines = summary_block()
    lines += [
        "## Files",
        "",
        "| Path | What it shows | Run ID | Commit | Data basis | Video caption |",
        "|---|---|---|---|---|---|",
    ]
    for path, shows, run, basis, caption in rows:
        rid, commit = run_commit(run)
        lines.append(f"| `{path}` | {shows} | `{rid}` | `{commit}` | {basis} | {caption} |")
    failed = [f"{p}: {log}" for p, st, log in results if st == "FAILED"]
    lines += ["", "## Not produced", ""]
    lines += [f"- {x}" for x in failed + skipped] or ["- nothing"]
    lines += [
        "",
        "## Excluded on purpose",
        "",
        "- `paper_figures/` (the authors' files; not ours to redistribute) and the paper PDFs.",
        "- Raw `trials.jsonl` / `trials.parquet` (in the repository; the CSVs here are derived from them).",
        "- `.venv` and other environment files.",
        "",
        f"Built by `scripts/build_handoff.py` at commit `{head}`. Video: H.264, 1920x1080, 30 fps. Stills: PNG, 1920 px wide.",
    ]
    (OUT / "MANIFEST.md").write_text("\n".join(lines) + "\n")
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                z.write(p, Path("handoff") / p.relative_to(OUT))
    n = sum(1 for p in OUT.rglob("*") if p.is_file())
    print(f"{ZIP}: {ZIP.stat().st_size / 1e6:.1f} MB, {n} files; not produced: {len(failed) + len(skipped)}")


if __name__ == "__main__":
    main()
