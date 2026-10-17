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
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
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


def jsonl_to_parquet(jsonl_path):
    """Write trials.parquet next to a trials.jsonl (Fahad 2026-10-17).

    The JSONL stays the raw log; the Parquet file is a typed, columnar copy
    for analysis. One row per line, same columns; list fields stay lists,
    missing fields are null. Returns the Parquet path.
    """
    import pandas as pd

    jsonl_path = Path(jsonl_path)
    rows = [json.loads(x) for x in jsonl_path.read_text().splitlines() if x.strip()]
    out = jsonl_path.with_suffix(".parquet")
    df = pd.DataFrame.from_records(rows)
    # G is null for the tight-spool law; keep it a float column, not object.
    if "G" in df:
        df["G"] = pd.to_numeric(df["G"])
    df.to_parquet(out, engine="pyarrow", index=False)
    verify_parquet(rows, out)
    return out


def verify_parquet(rows, parquet_path):
    """Raise if the Parquet file does not hold exactly the JSONL rows: same
    count and order, and every scalar field equal (floats exactly, None as null)."""
    import math

    import pandas as pd

    df = pd.read_parquet(parquet_path)
    if len(df) != len(rows):
        raise ValueError(f"{parquet_path}: {len(df)} rows, JSONL has {len(rows)}")
    for i, r in enumerate(rows):
        for k, v in r.items():
            if isinstance(v, (list, dict)):
                continue
            got = df.at[i, k]
            same = (v is None and pd.isna(got)) or (
                isinstance(v, float) and isinstance(got, float) and math.isnan(v) and math.isnan(got)
            )
            if not same and got != v:
                raise ValueError(f"{parquet_path}: row {i} field {k}: {got!r} != {v!r}")
