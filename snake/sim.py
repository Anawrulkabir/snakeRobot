"""Single headless trial runner (CLAUDE.md 5.6). Returns raw time series; metrics live in metrics.py."""
import copy
import math

import mujoco
import numpy as np

from snake.gait import serpenoid
from snake.model_builder import build_model

LOG_EVERY = 10  # log every 10th step (10 ms at dt = 1 ms)


def run_trial(cfg, gait, freq, n_cycles, seed, timestep=None, detail_after_cycles=None):
    """Run the stiff-servo serpenoid on flat ground.

    detail_after_cycles: if set, also log per-wheel contact detail after that
    many cycles: normal force, axle tilt, and friction split into the wheel's
    rolling and axle directions (key 'wheel_detail').

    gait: {'amplitude_deg', 'spatial_freq'}; freq in Hz overrides the gait file.
    Randomized per seed: initial heading (uniform 0..2pi), wave phase
    (uniform 0..2pi) and start position (uniform +-0.05 m).
    """
    c = copy.deepcopy(cfg)
    if timestep is not None:
        c["sim"]["timestep"] = timestep
    m = build_model(c)
    d = mujoco.MjData(m)
    rng = np.random.default_rng(seed)
    heading = float(rng.uniform(0, 2 * math.pi))
    phase = float(rng.uniform(0, 2 * math.pi))
    x0, y0 = rng.uniform(-0.05, 0.05, size=2)

    A = math.radians(gait["amplitude_deg"])
    xi = gait["spatial_freq"]
    nj = m.nu

    def command(t):
        return serpenoid(t, A, xi, freq, nj, phase)

    # Start in the commanded shape so the servos do not jump at t = 0.
    d.qpos[m.joint("root_x").qposadr[0]] = x0
    d.qpos[m.joint("root_y").qposadr[0]] = y0
    d.qpos[m.joint("root_yaw").qposadr[0]] = heading
    jq = [m.joint(f"j{i}").qposadr[0] for i in range(1, nj + 1)]
    d.qpos[jq] = command(0.0)
    mujoco.mj_forward(m, d)

    seg_ids = [m.body(f"seg{i}").id for i in range(c["body"]["n_segments"])]
    seg_mass = m.body_mass[seg_ids]
    wheel_geoms = {m.geom(f"wheel{i}_tyre").id for i in range(c["body"]["n_segments"])}
    floor = m.geom("floor").id
    nwheel = len(wheel_geoms)

    T = n_cycles / freq
    steps = int(round(T / m.opt.timestep))
    log_every = max(1, int(round(LOG_EVERY * 1e-3 / m.opt.timestep)))
    t_log, com, track_err, torque, axis = [], [], [], [], []
    head_id, tail_id = seg_ids[0], seg_ids[-1]
    max_penetration, airborne_steps, wheel_steps = 0.0, 0, 0
    wheel_index = {m.geom(f"wheel{i}_tyre").id: i for i in range(nwheel)}
    detail_t0 = None if detail_after_cycles is None else detail_after_cycles / freq
    det_N, det_tilt, det_fr, det_fa = [], [], [], []
    f6 = np.zeros(6)
    for k in range(steps):
        d.ctrl[:] = command(d.time)
        mujoco.mj_step(m, d)
        if not np.all(np.isfinite(d.qpos)):
            raise FloatingPointError(f"simulation diverged at t={d.time:.3f}")
        touching = set()
        for con in d.contact[: d.ncon]:
            max_penetration = max(max_penetration, -con.dist)
            if floor in (con.geom1, con.geom2):
                touching |= {con.geom1, con.geom2} & wheel_geoms
        airborne_steps += nwheel - len(touching)
        wheel_steps += nwheel
        if detail_t0 is not None and d.time >= detail_t0:
            N = np.zeros(nwheel)
            Fw = np.zeros((nwheel, 3))
            for ci, con in enumerate(d.contact[: d.ncon]):
                w = wheel_index.get(con.geom1, wheel_index.get(con.geom2))
                if w is None:
                    continue
                mujoco.mj_contactForce(m, d, ci, f6)
                N[w] += f6[0]
                Fw[w] += con.frame.reshape(3, 3).T @ np.r_[0.0, f6[1:3]]   # friction only, world frame
            axles = np.array([d.xmat[sid].reshape(3, 3)[:, 1] for sid in seg_ids])
            tilt = np.degrees(np.arcsin(np.clip(np.abs(axles[:, 2]), 0, 1)))
            a_h = axles[:, :2] / np.linalg.norm(axles[:, :2], axis=1, keepdims=True)
            r_h = np.c_[-a_h[:, 1], a_h[:, 0]]
            det_N.append(N)
            det_tilt.append(tilt)
            det_fa.append(np.abs(np.sum(Fw[:, :2] * a_h, axis=1)))
            det_fr.append(np.abs(np.sum(Fw[:, :2] * r_h, axis=1)))
        if k % log_every == 0:
            t_log.append(d.time)
            # Segment CoM (wheels are tiny and move with their segment).
            xyz = d.xipos[seg_ids]
            com.append((seg_mass @ xyz[:, :2]) / seg_mass.sum())
            # Body axis: tail joint pin -> head pin.
            axis.append(d.xpos[head_id][:2] - d.xpos[tail_id][:2])
            track_err.append(np.array(d.qpos[jq]) - np.array(d.ctrl))
            torque.append(d.actuator_force.copy())
    return {
        "seed": seed,
        "heading": heading,
        "phase": phase,
        "timestep": m.opt.timestep,
        "t": np.array(t_log),
        "com_xy": np.array(com),
        "body_axis_xy": np.array(axis),
        "tracking_error": np.array(track_err),
        "actuator_torque": np.array(torque),
        "max_penetration": max_penetration,
        "wheel_airborne_fraction": airborne_steps / wheel_steps,
        "wheel_detail": None if detail_t0 is None else {
            "normal": np.array(det_N), "tilt_deg": np.array(det_tilt),
            "f_roll": np.array(det_fr), "f_axle": np.array(det_fa)},
    }


def coast_energy_check(cfg, v0=0.2, seconds=1.0):
    """Passive check: straight body, servos off, pushed forward at v0.

    With only friction acting, total mechanical energy must never increase.
    Returns the largest step-to-step energy increase (J) and initial energy.
    """
    c = copy.deepcopy(cfg)
    m = build_model(c)
    m.opt.enableflags |= mujoco.mjtEnableBit.mjENBL_ENERGY
    m.actuator_gainprm[:, 0] = 0   # servos off
    m.actuator_biasprm[:, :] = 0
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    # Let it settle onto its wheels first, then push.
    for _ in range(500):
        mujoco.mj_step(m, d)
    d.qvel[m.joint("root_x").dofadr[0]] = v0
    for i in range(c["body"]["n_segments"]):
        d.qvel[m.joint(f"axle{i}").dofadr[0]] = v0 / c["ground"]["wheel_radius"]
    mujoco.mj_forward(m, d)
    e0 = d.energy.sum()
    prev, worst = e0, 0.0
    for _ in range(int(seconds / m.opt.timestep)):
        mujoco.mj_step(m, d)
        e = d.energy.sum()
        worst = max(worst, e - prev)
        prev = e
    return {"max_energy_increase_J": float(worst), "initial_energy_J": float(e0), "final_energy_J": float(prev)}
