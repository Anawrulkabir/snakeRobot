"""Load the tagged YAML configs ({value, source, note} entries)."""

from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
SOURCES = {"hardware", "paper", "decision", "proposal", "placeholder"}


def load_raw(name="robot.yaml"):
    with open(CONFIG_DIR / name) as f:
        return yaml.safe_load(f)


def values(raw):
    """Strip tags: {'body': {'n_segments': {'value': 7, ...}}} -> {'body': {'n_segments': 7}}."""
    out = {}
    for group, entries in raw.items():
        out[group] = {}
        for key, entry in entries.items():
            if not isinstance(entry, dict) or "value" not in entry or "source" not in entry:
                raise ValueError(f"{group}.{key}: every entry needs 'value' and 'source'")
            if entry["source"] not in SOURCES:
                raise ValueError(f"{group}.{key}: unknown source {entry['source']!r}")
            out[group][key] = entry["value"]
    return out


def placeholders(raw):
    """Dotted names of every entry still tagged 'placeholder'."""
    return [
        f"{group}.{key}"
        for group, entries in raw.items()
        for key, entry in entries.items()
        if entry["source"] == "placeholder"
    ]


def load(name="robot.yaml"):
    return values(load_raw(name))
