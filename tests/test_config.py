"""Tests for snake/config.py."""

import pytest

from snake import config as cfgmod


def test_every_entry_tagged():
    for name in ("robot.yaml", "gait.yaml"):
        cfgmod.values(cfgmod.load_raw(name))  # raises if any entry lacks a valid tag


def test_untagged_entry_rejected():
    with pytest.raises(ValueError):
        cfgmod.values({"body": {"n_segments": 7}})
    with pytest.raises(ValueError):
        cfgmod.values({"body": {"n_segments": {"value": 7, "source": "memory"}}})


def test_placeholders_listed():
    raw = {"a": {"x": {"value": 1, "source": "placeholder"}, "y": {"value": 2, "source": "paper"}}}
    assert cfgmod.placeholders(raw) == ["a.x"]
