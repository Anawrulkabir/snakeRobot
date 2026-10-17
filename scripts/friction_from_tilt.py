"""Body-post friction from Fahad's tilt test: mu = tan(slip angle).

  python scripts/friction_from_tilt.py   # reads data/measured/post_friction_tilt.csv
Writes results/friction_tilt/<run_id>/summary.json.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from snake.metrics import mean_ci95  # noqa: E402
from snake.runlog import new_run  # noqa: E402


def main():
    f = ROOT / "data" / "measured" / "post_friction_tilt.csv"
    d = np.genfromtxt(f, delimiter=",", names=True)
    ang = np.atleast_1d(d["angle_deg"])
    mu = np.tan(np.radians(ang))
    m, h = mean_ci95(mu)
    summary = {
        "n_trials": int(len(mu)),
        "angle_deg": ang.tolist(),
        "mu_per_trial": mu.tolist(),
        "mu_mean": m,
        "mu_sd": float(mu.std(ddof=1)) if len(mu) > 1 else None,
        "mu_ci95_half": h,
        "note": "static friction at slip onset (tilt test); the model uses one Coulomb mu",
    }
    run_dir = new_run("friction_tilt")
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"saved {run_dir}")


if __name__ == "__main__":
    main()
