"""Locomotion metrics (CLAUDE.md 5.5). Pure numpy, no MuJoCo, so each can be unit-tested.

Jam detection, success and collision counts come with the arena (milestone 4).
"""

import numpy as np


def cycle_window(t, freq, skip_cycles, n_cycles):
    """Boolean mask of samples in cycles [skip_cycles, skip_cycles + n_cycles)."""
    period = 1.0 / freq
    return (t >= skip_cycles * period) & (t < (skip_cycles + n_cycles) * period + 1e-12)


def displacement_per_cycle(t, xy, freq, skip_cycles, n_cycles, heading):
    """CoM displacement per gait cycle over a whole number of cycles.

    Returns (forward, net): forward is along the initial heading (radians),
    net is the straight-line distance. Both are per cycle, in metres.
    Sampling at whole cycles removes the within-cycle lateral sway.
    """
    period = 1.0 / freq
    t0, t1 = skip_cycles * period, (skip_cycles + n_cycles) * period
    p0 = np.array([np.interp(t0, t, xy[:, k]) for k in range(2)])
    p1 = np.array([np.interp(t1, t, xy[:, k]) for k in range(2)])
    d = p1 - p0
    u = np.array([np.cos(heading), np.sin(heading)])
    return float(d @ u) / n_cycles, float(np.linalg.norm(d)) / n_cycles


def mean_body_heading(t, axis_xy, freq, skip_cycles, n_cycles):
    """Direction (radians) of the tail-to-head axis, averaged over whole cycles.

    The head's own yaw swings with the wave, so it is not the travel axis.
    """
    w = cycle_window(t, freq, skip_cycles, n_cycles)
    v = axis_xy[w].mean(axis=0)
    return float(np.arctan2(v[1], v[0]))


def heading_drift_per_cycle(t, xy, freq, skip_cycles, n_cycles):
    """Change in CoM travel direction per cycle (radians), from cycle-sampled positions.

    A non-integer number of waves on the body makes an open-loop serpenoid
    turn slowly; this reports how much.
    """
    period = 1.0 / freq
    pts = np.array(
        [[np.interp((skip_cycles + k) * period, t, xy[:, j]) for j in range(2)] for k in range(n_cycles + 1)]
    )
    steps = np.diff(pts, axis=0)
    ang = np.unwrap(np.arctan2(steps[:, 1], steps[:, 0]))
    if len(ang) < 2:
        return 0.0
    return float((ang[-1] - ang[0]) / (len(ang) - 1))


def summary_stats(x):
    """Mean, 95th percentile and peak of |x| (CLAUDE.md 5.5 torque statistics)."""
    a = np.abs(np.asarray(x, dtype=float))
    return {"mean": float(a.mean()), "p95": float(np.percentile(a, 95)), "peak": float(a.max())}


def mean_ci95(values):
    """Mean and 95% confidence half-width (Student t) across trials."""
    from scipy import stats

    v = np.asarray(values, dtype=float)
    n = len(v)
    if n < 2:
        return float(v.mean()), float("nan")
    half = stats.t.ppf(0.975, n - 1) * v.std(ddof=1) / np.sqrt(n)
    return float(v.mean()), float(half)


def displacement_over_last_cycle(t, xy, freq):
    """For each sample, the CoM's straight-line displacement over the preceding
    gait cycle (NaN during the first cycle). Comparing points one full cycle
    apart removes the within-cycle sway."""
    period = 1.0 / freq
    t_prev = t - period
    ok = t_prev >= t[0]
    out = np.full(len(t), np.nan)
    px = np.interp(t_prev[ok], t, xy[:, 0])
    py = np.interp(t_prev[ok], t, xy[:, 1])
    out[ok] = np.hypot(xy[ok, 0] - px, xy[ok, 1] - py)
    return out


def detect_jam(t, xy, freq, threshold, min_cycles):
    """(jammed, first_jam_time). Jammed once displacement over the last cycle
    stays below threshold for at least min_cycles cycles in a row."""
    d = displacement_over_last_cycle(t, xy, freq)
    need = min_cycles / freq
    start = None
    for ti, di in zip(t, d):
        if np.isfinite(di) and di < threshold:
            start = ti if start is None else start
            if ti - start >= need:
                return True, float(start)
        else:
            start = None
    return False, None


def first_crossing(t, head_xy, line_point, line_normal, T=None):
    """Time the head first reaches the finish line (signed distance >= 0 along
    line_normal from line_point), or None if not within T."""
    n = np.asarray(line_normal, float)
    n = n / np.linalg.norm(n)
    s = (head_xy - np.asarray(line_point, float)) @ n
    idx = np.nonzero(s >= 0)[0]
    if len(idx) == 0:
        return None
    tc = float(t[idx[0]])
    return tc if T is None or tc <= T else None


def count_collisions(t, in_contact, min_gap):
    """Number of contact onsets. in_contact: bool array (samples x pairs).
    A pair must be out of contact for at least min_gap seconds before a new
    contact counts as a new collision."""
    c = np.atleast_2d(np.asarray(in_contact, bool))
    if c.shape[0] != len(t):
        c = c.T
    total = 0
    for j in range(c.shape[1]):
        last_off_start, on = None, False
        for ti, ci in zip(t, c[:, j]):
            if ci and not on:
                # First contact of this pair, or back after a real gap.
                if last_off_start is None or ti - last_off_start >= min_gap:
                    total += 1
                on = True
            elif not ci and on:
                on, last_off_start = False, ti
    return total


def progress_rate_full_horizon(dx, outcome, cycles_elapsed, max_cycles):
    """E1 primary metric (Fahad 2026-10-17), m per cycle.

    success:                  dx / cycles_elapsed (the trial's own duration)
    stuck, overload, timeout: dx / max_cycles (a trial that stops early is
                              treated as stopped for the rest of the limit)
    dx is the CoM's forward (x) displacement from the start pose. A zero
    denominator gives 0.
    """
    den = cycles_elapsed if outcome == "success" else max_cycles
    return float(dx) / den if den > 0 else 0.0


def progress_rate_elapsed(dx, cycles_elapsed):
    """Secondary (the earlier pre-registered metric): dx / cycles elapsed,
    whatever the ending. Rewards a fast start followed by an early overload."""
    return float(dx) / cycles_elapsed if cycles_elapsed > 0 else 0.0
