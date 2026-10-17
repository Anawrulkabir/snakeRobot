"""Tests for the Parquet copy of trials.jsonl."""

import json

import pandas as pd
import pytest

from snake.runlog import jsonl_to_parquet

ROWS = [
    {
        "key": "a",
        "law": "paper",
        "G": 0.75,
        "seed": 1,
        "rate": 0.1234567890123,
        "outcome": "stuck",
        "per_joint": [0.1, 0.2, 0.3],
    },
    {
        "key": "b",
        "law": "tight_spool",
        "G": None,
        "seed": 1,
        "rate": -0.0004,
        "outcome": "overload",
        "per_joint": [0.0, 0.5, 1.0],
    },
    {
        "key": "c",
        "law": "paper",
        "G": 1.5,
        "seed": 2,
        "rate": 0.0,
        "outcome": "diverged",
        "error": "diverged at t=1.000",
    },
]


def test_parquet_matches_jsonl(tmp_path):
    p = tmp_path / "trials.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in ROWS) + "\n")
    df = pd.read_parquet(jsonl_to_parquet(p))
    assert list(df["key"]) == ["a", "b", "c"]
    assert df["rate"].tolist() == [r["rate"] for r in ROWS]  # exact floats
    assert df["G"].dtype == float and df["G"].isna().tolist() == [False, True, False]
    assert list(df["per_joint"][0]) == pytest.approx([0.1, 0.2, 0.3])
    assert df["error"].isna().tolist() == [True, True, False]


def test_parquet_check_catches_dropped_row(tmp_path, monkeypatch):
    # Planted fault: a converter that loses the last row must be caught by verify_parquet.
    p = tmp_path / "trials.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in ROWS) + "\n")
    real = pd.DataFrame.from_records
    monkeypatch.setattr(pd.DataFrame, "from_records", staticmethod(lambda rows: real(rows[:-1])))
    with pytest.raises(ValueError):
        jsonl_to_parquet(p)


def test_parquet_check_catches_changed_value(tmp_path, monkeypatch):
    # Planted fault: a converter that rounds floats must be caught.
    p = tmp_path / "trials.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in ROWS) + "\n")
    real = pd.DataFrame.from_records
    monkeypatch.setattr(pd.DataFrame, "from_records", staticmethod(lambda rows: real(rows).round(3)))
    with pytest.raises(ValueError):
        jsonl_to_parquet(p)
