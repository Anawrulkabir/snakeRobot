"""One lattice trial (CLAUDE.md 5.6; E1/E1b). Headless; returns a flat dict of results.

A trial ends at the first of:
  success   head tip crosses the far edge of the lattice (arena lattice.length_m)
  stuck     CoM displacement over the last cycle < jam threshold for
            trial.stuck_terminate_cycles cycles in a row (paper p. 37)
  overload  a joint torque held at >= overload fraction of stall for
            overload.min_duration_s (paper p. 37 analogue)
  timeout   success.max_cycles cycles
Success at shorter cutoffs is computed afterwards from t_success
(Fahad 2026-10-16: 20/30/40 cycles).
"""
import copy
import math

import mujoco
import numpy as np

from snake import arena as arena_mod
from snake.actuation import ComplianceA, effective_inertias
from snake.gait import serpenoid
from snake.model_builder import build_model

LOG_DT = 0.01
STOP_TOL = math.radians(0.25)


def body_front_x(m, d, c):
    """Largest x reached by any body capsule (its surface, not its centre)."""
    r = c["body"]["segment_width"] / 2
    front = -np.inf
    for i in range(c["body"]["n_segments"]):
        g = m.geom(f"seg{i}_body").id
        half = m.geom_size[g][1]
        zax = d.geom_xmat[g].reshape(3, 3)[:, 2]
        front = max(front, d.geom_xpos[g][0] + abs(zax[0]) * half + r)
    return float(front)


def place_body(m, d, c, angles, jq, heading, front_x, y0):
    """Start pose (fix for the lattice diagnosis start-pose bug).

    Joints take the commanded shape. The whole body is then rotated so its
    tail-to-head axis (tail pin to head pin) points along `heading`, and
    translated so its front-most surface point is at x = front_x, with the
    head pin at y = y0. Earlier the *head segment's* yaw was set to the
    heading, and the body could curl into the lattice or point away from it.
    """
    n = c["body"]["n_segments"]
    rx, ry, ryaw = (m.joint(nm).qposadr[0] for nm in ("root_x", "root_y", "root_yaw"))
    d.qpos[jq] = angles
    d.qpos[[rx, ry, ryaw]] = 0.0
    mujoco.mj_forward(m, d)
    head, tail = d.xpos[m.body("seg0").id][:2], d.xpos[m.body(f"seg{n - 1}").id][:2]
    axis_angle = math.atan2(*(head - tail)[::-1])
    d.qpos[ryaw] = heading - axis_angle
    mujoco.mj_forward(m, d)
    d.qpos[rx] += front_x - body_front_x(m, d, c)
    d.qpos[ry] = y0
    mujoco.mj_forward(m, d)


def run_lattice_trial(cfg, arena, mcfg, density, amplitude_deg, spatial_freq, freq, law, G, seed,
                      timestep=None):
    c = copy.deepcopy(cfg)
    if timestep is not None:
        c["sim"]["timestep"] = timestep
    if c["servo"]["actuation"] != "compliance_A":
        raise ValueError("lattice trials use servo.actuation = compliance_A")
    n = c["body"]["n_segments"]
    L = n * c["body"]["segment_pitch"]
    lat = arena["lattice"]
    posts = arena_mod.post_centres(arena, density, L)
    m = build_model(c, posts=posts if len(posts) else None, post_radius=lat["post_diameter_m"] / 2,
                    post_height=lat["post_height_m"], post_friction=lat["post_friction"])
    d = mujoco.MjData(m)

    # Randomized start (config/arena.yaml start).
    rng = np.random.default_rng(seed)
    st = arena["start"]
    heading = math.radians(rng.uniform(-st["heading_noise_deg"], st["heading_noise_deg"]))
    phase = float(rng.uniform(0, 2 * math.pi))
    sp = arena_mod.spacing(arena, density, L)
    y0 = float(rng.uniform(-sp / 2, sp / 2)) if sp is not None else float(rng.uniform(-0.05, 0.05))

    A = math.radians(amplitude_deg)
    nj = m.nu
    jq = np.array([m.joint(f"j{i}").qposadr[0] for i in range(1, nj + 1)])
    jv = np.array([m.joint(f"j{i}").dofadr[0] for i in range(1, nj + 1)])
    law_obj = ComplianceA(c, G, A, law=law)

    def command(t):
        return serpenoid(t, A, spatial_freq, freq, nj, phase)

    place_body(m, d, c, command(0.0), jq, heading, st["head_x_m"], y0)

    # Initial-state checks: no body may start touching or inside a post.
    init_contacts, init_pen = 0, 0.0
    post_geom_set = {m.geom(f"post{k}").id for k in range(len(posts))}
    for con in d.contact[: d.ncon]:
        if con.geom1 in post_geom_set or con.geom2 in post_geom_set:
            init_contacts += 1
            init_pen = max(init_pen, -con.dist)
    init_front_x = body_front_x(m, d, c)
    n_ = c["body"]["n_segments"]
    ax = d.xpos[m.body("seg0").id][:2] - d.xpos[m.body(f"seg{n_ - 1}").id][:2]
    init_axis_deg = math.degrees(math.atan2(ax[1], ax[0]))

    seg_ids = [m.body(f"seg{i}").id for i in range(n)]
    seg_mass = m.body_mass[seg_ids]
    tip = m.site("head_tip").id
    post_ids = {m.geom(f"post{k}").id: k for k in range(len(posts))}
    hard = math.radians(c["joint"]["hard_limit_deg"])
    stall = c["servo"]["stall_torque"]
    ov_frac, ov_dur = mcfg["overload"]["torque_fraction_of_stall"], mcfg["overload"]["min_duration_s"]
    jam_thr = mcfg["jam"]["disp_per_cycle_threshold_m"]
    jam_cyc = mcfg["jam"]["min_duration_cycles"]
    stuck_cyc = mcfg["trial"]["stuck_terminate_cycles"]
    gap = mcfg["collision"]["min_gap_s"]
    period = 1.0 / freq
    t_end = mcfg["success"]["max_cycles"] * period
    log_every = max(1, int(round(LOG_DT / m.opt.timestep)))
    finish = lat["length_m"]

    def com():
        xyz = d.xipos[seg_ids]
        return (seg_mass @ xyz[:, :2]) / seg_mass.sum()

    com0 = com()
    t_log, com_log = [d.time], [com0]
    post_on = np.zeros(len(posts), bool)
    post_off_t = np.full(len(posts), -np.inf)
    collisions = 0
    over_t = np.zeros(nj)
    max_over = 0.0
    stop_steps = 0
    stop_cycles = set()
    cap_steps = 0
    cap_steps_joint = np.zeros(nj)
    slow_since = None
    jam_t = None
    outcome, t_success = "timeout", None
    torques = []
    max_lat = 0.0
    head_x_cycles = [float(d.site_xpos[m.site("head_tip").id][0])]
    next_cycle = period

    k = 0
    while d.time < t_end:
        d.ctrl[:] = law_obj.torques(command(d.time), d.qpos[jq], d.qvel[jv], m.opt.timestep,
                                    effective_inertias(m, d, jv))
        mujoco.mj_step(m, d)
        k += 1
        if not np.all(np.isfinite(d.qpos)):
            raise FloatingPointError(f"diverged at t={d.time:.3f} (seed {seed})")
        # Collisions with posts (debounced onsets, metrics.count_collisions logic).
        if len(posts):
            now = np.zeros(len(posts), bool)
            for con in d.contact[: d.ncon]:
                p = post_ids.get(con.geom1, post_ids.get(con.geom2))
                if p is not None:
                    now[p] = True
            onset = now & ~post_on
            collisions += int(np.sum(onset & (d.time - post_off_t >= gap)))
            post_off_t[post_on & ~now] = d.time
            post_on = now
        # Joint stops.
        on_stop = np.abs(d.qpos[jq]) >= hard - STOP_TOL
        if on_stop.any():
            stop_steps += 1
            stop_cycles.add(int(d.time * freq))
        # Overload: torque held at the cap.
        at_cap = np.abs(d.actuator_force) >= ov_frac * stall
        cap_steps += bool(at_cap.any())
        cap_steps_joint += at_cap
        over_t = np.where(at_cap, over_t + m.opt.timestep, 0.0)
        max_over = max(max_over, float(over_t.max()))
        if over_t.max() >= ov_dur:
            outcome = "overload"
            break
        # Success: head tip past the far edge of the lattice.
        if d.site_xpos[tip][0] >= finish:
            outcome, t_success = "success", d.time
            break
        if d.time >= next_cycle:
            head_x_cycles.append(float(d.site_xpos[tip][0]))
            next_cycle += period
        if k % log_every == 0:
            cxy = com()
            t_log.append(d.time)
            com_log.append(cxy)
            max_lat = max(max_lat, abs(cxy[1]))
            torques.append(np.abs(d.actuator_force).copy())   # from t = 0 (diag run c61d84c)
            # Displacement over the last cycle -> jam flag and stuck termination.
            if d.time >= period:
                tt = np.array(t_log)
                cc = np.array(com_log)
                prev = np.array([np.interp(d.time - period, tt, cc[:, j]) for j in range(2)])
                disp = float(np.hypot(*(cxy - prev)))
                if disp < jam_thr:
                    slow_since = d.time if slow_since is None else slow_since
                    if jam_t is None and d.time - slow_since >= jam_cyc * period:
                        jam_t = slow_since
                    if d.time - slow_since >= stuck_cyc * period:
                        outcome = "stuck"
                        break
                else:
                    slow_since = None

    cxy = com()
    tq = np.array(torques) if torques else np.zeros((1, nj))
    cycles = d.time * freq
    return {
        "density": density, "law": law, "G": G, "seed": seed, "freq_hz": freq,
        "amplitude_deg": amplitude_deg, "spatial_freq": spatial_freq,
        "timestep_s": m.opt.timestep,
        "initial_heading_deg": math.degrees(heading), "initial_y_m": y0, "wave_phase_rad": phase,
        "outcome": outcome,
        "t_end_s": d.time, "cycles_elapsed": cycles,
        "t_success_s": t_success,
        "success_cycles": None if t_success is None else t_success * freq,
        "final_head_x_m": float(d.site_xpos[tip][0]),
        "final_com_dx_m": float(cxy[0] - com0[0]),
        "final_com_dy_m": float(cxy[1] - com0[1]),
        "com_dx_per_cycle_m": float(cxy[0] - com0[0]) / cycles if cycles > 0 else 0.0,
        # Full-horizon rate: a trial that stops early by overload or stuck is
        # treated as stopped for the rest of the time limit, so its
        # displacement is divided by max_cycles. Success keeps its own
        # duration. com_dx_per_cycle_m (the pre-registered metric) rewards a
        # fast start followed by an overload (diag_torque_cap: 0.9-cycle
        # overload 0.127 m/cycle vs full 6-cycle run 0.040 m/cycle).
        "com_dx_per_cycle_full_horizon_m": float(cxy[0] - com0[0]) / (
            cycles if outcome == "success" else mcfg["success"]["max_cycles"]),
        "max_lateral_com_m": float(max_lat),
        "jammed": jam_t is not None, "t_jam_s": jam_t,
        "collisions": collisions,
        "stop_hit_cycle_fraction": len(stop_cycles) / max(1, math.ceil(cycles)),
        "stop_hit_step_fraction": stop_steps / max(1, k),
        "max_time_at_cap_s": max_over,
        # Fraction of time any joint (and each joint) sits at >= overload
        # fraction of the torque cap (Fahad 2026-10-16, torque-cap check).
        "frac_time_any_joint_at_cap": cap_steps / max(1, k),
        "frac_time_at_cap_per_joint": (cap_steps_joint / max(1, k)).tolist(),
        "torque_mean_Nm": float(tq.mean()),
        "torque_p95_Nm": float(np.percentile(tq, 95)),
        "torque_peak_Nm": float(tq.max()),
        "n_posts": int(len(posts)),
        "head_x_per_cycle_m": head_x_cycles,
        "initial_post_contacts": init_contacts,
        "initial_max_penetration_m": init_pen,
        "initial_body_front_x_m": init_front_x,
        "initial_body_axis_deg": init_axis_deg,
    }
