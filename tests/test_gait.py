"""Tests for snake/gait.py (paper Eq. 2)."""

import ast
import math
from pathlib import Path

import pytest

from snake.gait import serpenoid

A, XI, F, N = math.radians(46), 0.82, 0.25, 6


def wave_direction(gait):
    """+1 if the wave travels toward increasing joint index (head to tail).

    A crest at joint i reaches joint i+1 later, so the phase lag between
    neighbours tells the direction. Estimate it from the time of each
    joint's first peak.
    """
    ts = [k * 1e-3 for k in range(int(1 / F / 1e-3))]
    peaks = []
    for j in range(N):
        series = [gait(t)[j] for t in ts]
        peaks.append(ts[series.index(max(series))])
    # Unwrap one period so that a small lag reads as small.
    lag = (peaks[1] - peaks[0]) % (1 / F)
    return 1 if lag < 0.5 / F else -1


def test_matches_eq2_values():
    t = 0.37
    got = serpenoid(t, A, XI, F, N)
    for i, a in enumerate(got, start=1):
        assert a == pytest.approx(A * math.sin(2 * math.pi * XI * i / N - 2 * math.pi * F * t))


def test_amplitude_bound():
    for k in range(400):
        assert all(abs(a) <= A + 1e-12 for a in serpenoid(k * 0.01, A, XI, F, N))


def test_travels_head_to_tail():
    assert wave_direction(lambda t: serpenoid(t, A, XI, F, N)) == 1


def test_direction_check_catches_reversed_wave():
    # Planted fault: flipping the sign of the time term reverses the wave.
    reversed_wave = lambda t: serpenoid(-t, A, XI, F, N)
    assert wave_direction(reversed_wave) == -1


def test_period():
    a0 = serpenoid(0.1, A, XI, F, N)
    a1 = serpenoid(0.1 + 1 / F, A, XI, F, N)
    assert a0 == pytest.approx(a1)


def test_no_mujoco_or_numpy_imports():
    # Must stay portable to the ESP32 (CLAUDE.md 5.3).
    src = Path(__file__).resolve().parent.parent / "snake" / "gait.py"
    imported = set()
    for node in ast.walk(ast.parse(src.read_text())):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module.split(".")[0])
    assert imported <= {"math"}
