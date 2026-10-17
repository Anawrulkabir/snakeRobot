# Compliant bilateral-cable snake robot — simulation

[![tests](https://github.com/Anawrulkabir/snakeRobot/actions/workflows/tests.yml/badge.svg)](https://github.com/Anawrulkabir/snakeRobot/actions/workflows/tests.yml)

A MuJoCo simulation of a planar, cable-driven snake robot with tunable body
compliance, built before any hardware is bought. The project brief, plan and
rules are in [`CLAUDE.md`](CLAUDE.md).

Status: Milestone 2 (model builder and gait done; ground contact at gate G3). See
[`docs/progress.md`](docs/progress.md).

## Setup

Dependencies are locked with [uv](https://docs.astral.sh/uv/): `pyproject.toml`
lists them, and `uv.lock` pins the exact set that produced the saved runs
(Python 3.13).

```bash
uv sync --frozen                   # creates .venv from uv.lock
uv run pre-commit install          # ruff lint + format on every commit
uv run python scripts/check_env.py # add --no-viewer on a machine without a display
```

Without uv: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
(`requirements.txt` is exported from the lock).

- **macOS:** the interactive viewer only runs under MuJoCo's launcher. Use
  `mjpython scripts/check_env.py` (and `mjpython` for any viewer script).
  Headless runs and experiments use plain `python`.
- **Video output** needs the `ffmpeg` program on your PATH (used by mediapy).
  On macOS: `brew install ffmpeg`.

## Quick use

```bash
uv run pytest                        # run the tests (CI runs these, plus ruff, on every push and PR)
uv run python scripts/check_reproduction.py results/E1_pilot/<run_id> --G 0 0.75 1.5 --seeds 1001 1002
                                     # re-run logged trials, compare every field exactly
mjpython scripts/view_model.py       # watch the gait (macOS; plain python elsewhere)
python scripts/view_model.py --video gait.mp4
```

## Results files

Each sweep writes `results/<experiment>/<run_id>/` with a config snapshot,
`trials.jsonl` (the raw log, one line per trial) and `trials.parquet` (the
same rows, typed and checked against the JSONL). Both are committed, along
with `summary*.json`. Top-view replays of logged trials:
`scripts/animate_trial.py` (GIFs in `media/`).

## AI disclosure

The code in this repository was written with Claude Code (an AI coding
assistant) under the direction of Fahad, who makes the engineering decisions.
[`docs/decisions.md`](docs/decisions.md) records each decision and his choice.
Simulation results are evidence about the model, not about a physical robot.
