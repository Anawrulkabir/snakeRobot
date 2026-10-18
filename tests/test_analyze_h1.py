"""Tests for the pre-registered H1 reading (experiments/analyze_h1.py)."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "analyze_h1", Path(__file__).resolve().parent.parent / "experiments" / "analyze_h1.py"
)
h1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h1)


def row(p, c):
    return {h1.PROG: p, h1.CURL: c}


def seed(mid_p, mid_c, ref_p=0.2, ref_c=0.01):
    return {0.0: row(ref_p, ref_c), 1.0: row(ref_p, -ref_c), 0.5: row(mid_p, mid_c), 0.75: row(mid_p, mid_c)}


def test_supported():
    by = {s: seed(0.05, 0.05) for s in range(7)} | {s: seed(0.2, 0.0) for s in range(7, 10)}
    assert h1.verdict(by)[0] == "H1 supported"


def test_rejected():
    by = {s: seed(0.19, 0.05) for s in range(8)} | {s: seed(0.05, 0.05) for s in range(8, 10)}
    assert h1.verdict(by)[0] == "H1 rejected"


def test_six_of_ten_is_unclear():
    by = {s: seed(0.05, 0.05) for s in range(6)} | {s: seed(0.12, 0.0) for s in range(6, 10)}
    assert h1.verdict(by)[0] == "unclear"


def test_slow_without_curl_is_not_curl_stall():
    # Progress collapses but the body does not bend more one way: not a curl-stall.
    assert not h1.curl_stall(seed(0.05, 0.015), 0.5)


def test_curl_check_catches_missing_abs(monkeypatch):
    # Planted fault: comparing signed curl instead of |curl| would miss a negative curl.
    s = seed(0.05, -0.05)
    assert h1.curl_stall(s, 0.5)
    src = Path(spec.origin).read_text().replace("c = t[G][PROG], abs(t[G][CURL])", "c = t[G][PROG], t[G][CURL]")
    bad = importlib.util.module_from_spec(spec)
    exec(compile(src, spec.origin, "exec"), bad.__dict__)
    assert not bad.curl_stall(s, 0.5)
