"""Run folders: results/<experiment>/<run_id>/ with config snapshot and git state (CLAUDE.md 7)."""
import datetime
import json
import shutil
import subprocess
from pathlib import Path

from snake import config as cfgmod

ROOT = Path(__file__).resolve().parent.parent


def _git(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def new_run(experiment, meta=None):
    """Create the run folder, snapshot all configs and git state, return its Path."""
    commit = _git("rev-parse", "--short", "HEAD")
    dirty = bool(_git("status", "--porcelain", "--", ".", ":!results"))  # run outputs do not count
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{stamp}_{commit}{'-dirty' if dirty else ''}"
    run_dir = ROOT / "results" / experiment / run_id
    (run_dir / "config").mkdir(parents=True)
    for f in cfgmod.CONFIG_DIR.glob("*.yaml"):
        shutil.copy(f, run_dir / "config" / f.name)
    info = {
        "run_id": run_id,
        "experiment": experiment,
        "git_commit": commit,
        "git_dirty": dirty,
        "placeholders": cfgmod.placeholders(cfgmod.load_raw()),
        **(meta or {}),
    }
    (run_dir / "run_info.json").write_text(json.dumps(info, indent=2))
    return run_dir
