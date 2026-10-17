"""Does 1 or 2 servos per joint fit in one segment? (Fahad 2026-10-17)

Segment interior: a cylinder of diameter segment_width - 2*wall and length
case_length - 2*wall (config/robot.yaml; wall is a proposal below). Each
servo is a box (config/servos.yaml) in any of its 6 orientations. Two
servos: side by side across the width, or end to end along the axis.
A box arrangement fits if its cross-section diagonal <= interior diameter and
its length <= interior length. Spools, horns, wiring and the wheel mount are
NOT included, so a 'fits' here is necessary, not sufficient.
  python scripts/servo_fit.py   # writes results/servo_fit/<run_id>/summary.json
"""
import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from snake import config as cfgmod  # noqa: E402
from snake.model_builder import segment_masses  # noqa: E402
from snake.runlog import new_run  # noqa: E402

WALL = 0.002   # m, proposal (printed shell wall); not a measured value


def arrangements(size, n):
    """Yield (name, cross_a, cross_b, length) for n identical boxes."""
    for a, b, L in set(itertools.permutations(size)):
        if n == 1:
            yield ("single", a, b, L)
        else:
            yield ("side_by_side", 2 * a, b, L)
            yield ("end_to_end", a, b, 2 * L)


def main():
    cfg = cfgmod.load()
    servos = yaml.safe_load(open(ROOT / "config" / "servos.yaml"))
    D = (cfg["body"]["segment_width"] - 2 * WALL) * 1000
    Lin = (cfg["body"]["case_length"] - 2 * WALL) * 1000
    out = {"interior_diameter_mm": D, "interior_length_mm": Lin, "wall_m": WALL, "servos": {}}
    for name, s in servos.items():
        size = s["size_mm"]["value"]
        for n in (1, 2):
            best = None
            for arr, a, b, L in arrangements(size, n):
                diag = math.hypot(a, b)
                fits = diag <= D and L <= Lin
                cand = {"arrangement": arr, "cross_mm": [a, b], "length_mm": L,
                        "cross_diagonal_mm": diag, "fits": fits,
                        "width_needed_mm": diag + 2 * WALL * 1000, "case_length_needed_mm": L + 2 * WALL * 1000}
                key = (not fits, max(diag - D, 0) + max(L - Lin, 0), diag)
                if best is None or key < best[0]:
                    best = (key, cand)
            c = cfgmod.load()
            c["mass"]["servo"] = s["mass_kg"]["value"]
            c["mass"]["servos_per_joint"] = n
            seg = segment_masses(c)
            total = sum(seg) + c["body"]["n_segments"] * c["mass"]["wheel"]
            out["servos"][f"{name}_x{n}"] = {
                **best[1],
                "body_segment_mass_kg": seg[1] + c["mass"]["wheel"],
                "head_mass_kg": seg[0] + c["mass"]["wheel"],
                "robot_mass_kg": total,
            }
    run_dir = new_run("servo_fit")
    (run_dir / "summary.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=1))
    print(f"saved {run_dir}")


if __name__ == "__main__":
    main()
