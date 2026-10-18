"""Tests for the pre-registered G6 classification (experiments/diag_stuck.py)."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "diag_stuck", Path(__file__).resolve().parent.parent / "experiments" / "diag_stuck.py"
)
ds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ds)


def crit(j1=False, j2=False, j3=False, a1=False, a2=False):
    return {"J1": j1, "J2": j2, "J3": j3, "A1": a1, "A2": a2}


@pytest.mark.parametrize(
    "r, a3, expected",
    [
        (crit(j1=True, j2=True), False, "real jamming"),
        (crit(j1=True, j2=True, j3=True, a1=True), False, "unclear"),  # jamming signs plus an artefact sign
        (crit(a1=True), False, "artefact"),
        (crit(j1=True), True, "artefact"),  # one jamming sign is allowed
        (crit(j1=True, j3=True), True, "unclear"),
        (crit(j2=True), False, "unclear"),  # one jamming sign alone is not enough
    ],
)
def test_classify(r, a3, expected):
    assert ds.classify(r, a3) == expected


def frame(t, left, right, tau=0.0):
    sides = [[False, False] for _ in range(7)]
    sides[2] = [left, right]
    return {
        "t": t,
        "tau": [0.0, tau, 0.0, 0.0, 0.0, 0.0],
        "post_side": sides,
        "q": [0.0] * 6,
        "zeta_ctrl": [0.0] * 6,
        "range": [[-1.0, 1.0]] * 6,
        "alpha": [0.0] * 6,
        "anchors": [[-0.1 * (i + 1), 0.0] for i in range(6)],
        "yaw": [0.0] * 7,
        "capsules": [[[-0.1 * i - 0.08, 0.0], [-0.1 * i - 0.02, 0.0]] for i in range(7)],
    }


REC = {"period_s": 8.0, "posts": [], "post_radius": 0.05, "capsule_radius": 0.025, "segment_pitch": 0.1}


def test_j1_needs_opposite_sides_at_once():
    both = [frame(t, True, True, tau=0.1) for t in range(10)]
    one = [frame(t, True, False, tau=0.1) for t in range(10)]
    row = {"G": 0.75, "seed": 1, "outcome": "stuck", "cycles_elapsed": 2.0}
    assert ds.metrics({**REC, "frames": both}, row, stuck=False)["J1"]
    assert not ds.metrics({**REC, "frames": one}, row, stuck=False)["J1"]


def test_j2_side_follows_push_side():
    # Joint 2 (0-based 1) has segments 1 and 2 as neighbours; tau > 0 pushes toward -y (right).
    row = {"G": 0.75, "seed": 1, "outcome": "stuck", "cycles_elapsed": 2.0}
    right = [frame(t, False, True, tau=0.1) for t in range(10)]
    left = [frame(t, True, False, tau=0.1) for t in range(10)]
    assert ds.metrics({**REC, "frames": right}, row, stuck=False)["J2"]
    assert not ds.metrics({**REC, "frames": left}, row, stuck=False)["J2"]


def test_j1_check_catches_any_side(monkeypatch):
    # Planted fault: counting a contact on either side as "wedged" must fail the J1 test.
    one = [frame(t, True, False, tau=0.1) for t in range(10)]
    row = {"G": 0.75, "seed": 1, "outcome": "stuck", "cycles_elapsed": 2.0}
    src = (
        Path(spec.origin)
        .read_text()
        .replace(
            "sides[:, :, 0].any(axis=1) & sides[:, :, 1].any(axis=1)",
            "sides[:, :, 0].any(axis=1) | sides[:, :, 1].any(axis=1)",
        )
    )
    bad = importlib.util.module_from_spec(spec)
    exec(compile(src, spec.origin, "exec"), bad.__dict__)
    assert bad.metrics({**REC, "frames": one}, row, stuck=False)["J1"]  # the faulty rule wrongly calls it wedged
    assert not ds.metrics({**REC, "frames": one}, row, stuck=False)["J1"]
