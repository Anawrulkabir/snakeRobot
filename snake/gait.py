"""Serpenoid travelling wave, paper Eq. 2 (Wang et al. 2023, p. 12).

    alpha_i(t) = A sin(2 pi xi i / N - 2 pi f t + phase)

A: amplitude (rad), xi: spatial frequency (waves per body), f: temporal
frequency (Hz), i = 1..N with i = 1 the joint nearest the head, N: number
of joints. The wave travels from head to tail (toward increasing i).

The index base and the head-to-tail direction are a working convention until
G4 (docs/paper_notes.md 1.1 and 6). Pure function of time and parameters,
standard library only, so the same code can be ported to the ESP32.
"""

import math


def serpenoid(t, amplitude, spatial_freq, temporal_freq, n_joints, phase=0.0):
    """Suggested joint angles (radians) for joints i = 1..n_joints at time t (s)."""
    return [
        amplitude * math.sin(2 * math.pi * spatial_freq * i / n_joints - 2 * math.pi * temporal_freq * t + phase)
        for i in range(1, n_joints + 1)
    ]
