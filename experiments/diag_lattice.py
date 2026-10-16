"""Lattice failure diagnosis (Fahad 2026-10-16), steps (a)-(e). Report only, no fixes.

The first lattice smoke trial (medium, G = 0.75, A = 59.5 deg, xi = 0.58,
joint stiffness 0.02 N m/rad, 40 cycles) ended with the head still at the
lattice entry. This script tests, in order:
  (a) the same gait on open floor;
  (b) initial post overlap or penetration at t = 0 (geometry only, many seeds);
  (c) G = 0, 0.75, 1 in the medium lattice;
  (d) body-post friction (0, 0.3) and the head's first contacts;
  (e) whether the commanded wave fits the lattice gaps (pure geometry).
6 cycles per trial, 3 seeds per cell.
  python experiments/diag_lattice.py   # writes results/diag_lattice/<run_id>/
"""
import copy
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402

from snake import arena as arena_mod  # noqa: E402
from snake import config as cfgmod  # noqa: E402
from snake.gait import serpenoid  # noqa: E402
from snake.runlog import new_run  # noqa: E402
from snake.trial import run_lattice_trial  # noqa: E402

STIFFNESS = 0.02          # as in the failing smoke trial
SEEDS = (1, 2, 3)
N_CYCLES = 6
GAITS = {  # paper amplitude x 7/6, paper xi (G4)
    "open": (53.666667, 0.82), "sparse": (56.0, 0.80), "medium": (59.5, 0.58), "dense": (84.0, 1.02)}


def base():
    cfg = cfgmod.load()
    cfg["joint"]["stiffness"] = STIFFNESS
    mc = copy.deepcopy(cfgmod.load("metrics.yaml"))
    mc["success"]["max_cycles"] = N_CYCLES
    return cfg, cfgmod.load("arena.yaml"), mc


def job(args):
    label, density, gait_density, G, seed, post_mu = args
    cfg, arena, mc = base()
    if post_mu is not None:
        arena["lattice"]["post_friction"] = post_mu
    A, xi = GAITS[gait_density]
    r = run_lattice_trial(cfg, arena, mc, density, A, xi, 0.125, "paper", G, seed)
    r["label"] = label
    return r


def wave_geometry(cfg, A_deg, xi, n_phase=16):
    """Commanded body shape (straight-line chain of joint pins) over a cycle:
    lateral extent (peak to peak, perpendicular to the mean axis) and the
    body's projected length along it."""
    n = cfg["body"]["n_segments"]
    p = cfg["body"]["segment_pitch"]
    widths, lengths = [], []
    for k in range(n_phase):
        ang = serpenoid(k / n_phase / 0.125, math.radians(A_deg), xi, 0.125, n - 1)
        h, pts = 0.0, [np.zeros(2)]
        for i in range(n):
            if i > 0:
                h += ang[i - 1]
            pts.append(pts[-1] - p * np.array([math.cos(h), math.sin(h)]))
        pts = np.array(pts)
        axis = pts[0] - pts[-1]
        u = axis / np.linalg.norm(axis)
        nrm = np.array([-u[1], u[0]])
        lat = pts @ nrm
        widths.append(lat.max() - lat.min())
        lengths.append(np.linalg.norm(axis))
    return float(np.mean(widths)), float(np.max(widths)), float(np.mean(lengths))


def main():
    cfg, arena, mc = base()
    L = cfg["body"]["n_segments"] * cfg["body"]["segment_pitch"]
    jobs = []
    # (a) open floor with the medium gait (and the open gait for reference)
    for G in (0.0, 0.75, 1.0):
        jobs += [("a_open_mediumgait", "open", "medium", G, s, None) for s in SEEDS]
        jobs += [("a_open_opengait", "open", "open", G, s, None) for s in SEEDS]
    # (c) medium lattice
    for G in (0.0, 0.75, 1.0):
        jobs += [("c_medium", "medium", "medium", G, s, None) for s in SEEDS]
    # (d) frictionless posts
    for G in (0.0, 0.75):
        jobs += [("d_medium_postmu0", "medium", "medium", G, s, 0.0) for s in SEEDS]
    with Pool() as pool:
        rows = pool.map(job, jobs)

    # (b) initial overlap over many seeds, every density, all G irrelevant (t = 0 pose)
    init = {}
    for dn in ("sparse", "medium", "dense"):
        mc0 = copy.deepcopy(mc)
        mc0["success"]["max_cycles"] = 0
        stats = [run_lattice_trial(cfg, arena, mc0, dn, *GAITS[dn], 0.125, "paper", 0.75, s)
                 for s in range(50)]
        init[dn] = {"seeds": 50,
                    "trials_with_initial_post_contact": sum(r["initial_post_contacts"] > 0 for r in stats),
                    "max_initial_penetration_m": max(r["initial_max_penetration_m"] for r in stats),
                    "max_initial_body_front_x_m": max(r["initial_body_front_x_upper_bound_m"] for r in stats)}

    # (e) wave geometry vs lattice gaps
    geo = {}
    for dn, (A, xi) in GAITS.items():
        wmean, wmax, ax_len = wave_geometry(cfg, A, xi)
        d = arena_mod.spacing(arena, dn, L)
        geo[dn] = {"A_deg": A, "xi": xi, "lateral_extent_mean_m": wmean, "lateral_extent_max_m": wmax,
                   "axial_length_m": ax_len,
                   "body_wavelength_m": ax_len / xi if xi > 0 else None,
                   "spacing_m": d,
                   "gap_m": None if d is None else d - arena["lattice"]["post_diameter_m"],
                   "body_width_m": cfg["body"]["segment_width"],
                   "wavelength_over_spacing": None if d is None else (ax_len / xi) / d,
                   "paper_wavelength_over_spacing": {"sparse": 2.0, "medium": 2.2, "dense": 1.8}.get(dn)}

    cells = {}
    for r in rows:
        key = f"{r['label']}|G={r['G']}"
        cells.setdefault(key, []).append(r)
    summary_cells = {}
    for key, rs in cells.items():
        summary_cells[key] = {
            "com_dx_per_cycle_m": [round(r["com_dx_per_cycle_m"], 4) for r in rs],
            "head_x_per_cycle_m": [[round(x, 3) for x in r["head_x_per_cycle_m"]] for r in rs],
            "outcome": [r["outcome"] for r in rs],
            "stop_hit_cycle_fraction": [round(r["stop_hit_cycle_fraction"], 2) for r in rs],
            "collisions": [r["collisions"] for r in rs],
            "torque_peak_Nm": [round(r["torque_peak_Nm"], 3) for r in rs],
            "initial_post_contacts": [r["initial_post_contacts"] for r in rs],
        }
    summary = {"stiffness_Nm_per_rad": STIFFNESS, "n_cycles": N_CYCLES, "seeds": SEEDS,
               "cells": summary_cells, "b_initial_overlap": init, "e_wave_geometry": geo}
    run_dir = new_run("diag_lattice", {"seeds": list(SEEDS)})
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=1))
    print(f"saved {run_dir}")


if __name__ == "__main__":
    main()
