# Compliant bilateral-cable snake robot — simulation

A MuJoCo simulation of a planar, cable-driven snake robot with tunable body
compliance, built before any hardware is bought. The project brief, plan and
rules are in [`CLAUDE.md`](CLAUDE.md).

Status: Milestone 1 (environment check and paper reading). See
[`docs/progress.md`](docs/progress.md).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/check_env.py        # add --no-viewer on a machine without a display
```

- **macOS:** the interactive viewer only runs under MuJoCo's launcher. Use
  `mjpython scripts/check_env.py` (and `mjpython` for any viewer script).
  Headless runs and experiments use plain `python`.
- **Video output** needs the `ffmpeg` program on your PATH (used by mediapy).
  On macOS: `brew install ffmpeg`.

## AI disclosure

The code in this repository was written with Claude Code (an AI coding
assistant) under the direction of Fahad, who makes the engineering decisions.
[`docs/decisions.md`](docs/decisions.md) records each decision and his choice.
Simulation results are evidence about the model, not about a physical robot.
