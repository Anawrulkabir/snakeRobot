"""Top-view replay of a lattice trial as an animated GIF (matplotlib, no OpenGL).

Re-runs the trial from the run's own config snapshot (same seed and
condition, so the same start pose and wave phase) with recording on, and
checks that the replay ends exactly as logged (outcome, end time and final
CoM displacement). A mismatch stops the script.

Drawn per frame:
  - posts as grey circles; the finish line (lattice far edge) as a dashed line;
  - segments as capsules at their true width;
  - the commanded wave as a faint overlay: the body shape the commanded
    angles alpha would give, hung from the actual head segment;
  - joints at the servo cap (>= overload fraction of stall) or on a hard stop
    as red dots; other joints as small dark dots;
  - a text box with time, cycle, G and how the trial ended.

  python scripts/animate_trial.py results/E1_pilot/<run_id> --seed 1001 --G 0.75
  python scripts/animate_trial.py results/E1_pilot/<run_id> --seed 1001 --montage 0,0.5,0.75,1.0,1.25,1.5
Options: --law tight_spool, --variant <name> (calibration runs), --frame-dt 1.0 (sim s per frame),
--fps 16, --out media/<name>.gif
"""

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

from snake import config as cfgmod  # noqa: E402
from snake.trial import run_lattice_trial  # noqa: E402

_spec = importlib.util.spec_from_file_location("run_sweep", ROOT / "experiments" / "run_sweep.py")
run_sweep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_sweep)


def replay(run_dir, seed, G, law="paper", variant=None, density=None):
    """Re-run one logged trial with recording. Returns (logged row, replay result, record)."""
    run_dir = Path(run_dir)
    cdir = run_dir / "config"
    load = lambda n: cfgmod.values(cfgmod.yaml.safe_load(open(cdir / n)))  # noqa: E731
    cfg, arena, mc, ex = load("robot.yaml"), load("arena.yaml"), load("metrics.yaml"), load("experiment.yaml")["run"]
    density = density or ex["densities"][0]
    Gkey = None if law == "tight_spool" else G
    key = run_sweep.key(variant, density, law, Gkey, seed)
    rows = {r["key"]: r for r in map(json.loads, (run_dir / "trials.jsonl").read_text().splitlines())}
    if key not in rows:
        raise KeyError(f"{key} not in {run_dir.name}/trials.jsonl")
    row = rows[key]
    A, xi = ex["gait_by_density"][density]
    if variant is not None:
        A *= run_sweep.apply_overrides(ex["variants"][variant], cfg, arena, mc)
    rec = {}
    r = run_lattice_trial(
        cfg, arena, mc, density, A, xi, ex["temporal_freq_hz"], law, 0.0 if Gkey is None else Gkey, seed, record=rec
    )
    got = (r["outcome"], r["t_end_s"], r["final_com_dx_m"])
    want = (row["outcome"], row["t_end_s"], row["final_com_dx_m"])
    if got != want:
        raise RuntimeError(f"replay does not match the log for {key}: {got} vs {want}")
    return row, r, rec


def variant_label(run_dir, variant):
    """'friction_0.1 (lattice.post_friction = 0.1)': the settings a calibration variant changes."""
    if variant is None:
        return ""
    ex = cfgmod.values(cfgmod.yaml.safe_load(open(Path(run_dir) / "config" / "experiment.yaml")))["run"]
    ov = ", ".join(f"{k.split('.', 1)[1]} = {v}" for k, v in ex["variants"][variant].items())
    return f"{variant} ({ov})" if ov else variant


def commanded_shape(f, pitch):
    """Body centreline the commanded angles would give, hung from the actual
    head segment: joint i+1 sits one pitch behind joint i along segment i,
    and segment i's yaw is the head yaw plus the commanded angles up to i."""
    anchors = np.array(f["anchors"])
    yaw = f["yaw"][0]
    pts = [anchors[0]]
    for a in f["alpha"]:
        yaw += a
        pts.append(pts[-1] - pitch * np.array([math.cos(yaw), math.sin(yaw)]))
    head = np.array(f["capsules"][0])
    front = head[np.argmax(np.linalg.norm(head - anchors[0], axis=1))]
    return np.vstack([front, pts])


def bounds(rec):
    xy = np.array([p for f in rec["frames"] for c in f["capsules"] for p in c])
    lo, hi = xy.min(axis=0) - 0.25, xy.max(axis=0) + 0.25
    span = max(hi - lo)
    mid = (lo + hi) / 2
    return mid[0] - span / 2, mid[0] + span / 2, mid[1] - span / 2, mid[1] + span / 2


class Panel:
    def __init__(self, ax, row, rec, title, pts_per_m, box, fs=7):
        self.ax, self.row, self.rec = ax, row, rec
        x0, x1, y0, y1 = box
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(title, fontsize=fs + 2)
        for p in rec["posts"]:
            ax.add_patch(Circle(p, rec["post_radius"], color="0.75", zorder=1))
        ax.axvline(rec["finish_x"], color="0.5", ls="--", lw=0.8)
        self.body = LineCollection(
            [], linewidths=2 * rec["capsule_radius"] * pts_per_m, colors="tab:blue", capstyle="round", zorder=3
        )
        ax.add_collection(self.body)
        # On top of the body, thin: when the joints track, it lies on the centreline.
        (self.cmd,) = ax.plot([], [], color="tab:orange", alpha=0.8, lw=1.0, zorder=4.5)
        k = (fs / 7) ** 2  # marker areas scale with the font size
        self.head = ax.scatter([], [], s=28 * k, marker="o", facecolors="white", edgecolors="k", zorder=5.5)
        self.ok = ax.scatter([], [], s=6 * k, c="k", zorder=4)
        self.red = ax.scatter([], [], s=30 * k, c="red", zorder=5)
        self.txt = ax.text(
            0.02,
            0.98,
            "",
            transform=ax.transAxes,
            va="top",
            fontsize=fs,
            family="monospace",
            bbox=dict(boxstyle="round", fc="white", ec="0.7", alpha=0.85),
            zorder=6,
        )

    def draw(self, t):
        frames = self.rec["frames"]
        i = min(int(np.searchsorted([f["t"] for f in frames], t)), len(frames) - 1)
        f = frames[i]
        self.body.set_segments(f["capsules"])
        c = commanded_shape(f, self.rec["segment_pitch"])
        self.cmd.set_data(c[:, 0], c[:, 1])
        self.head.set_offsets([c[0]])
        an = np.array(f["anchors"])
        bad = np.array(f["at_cap"]) | np.array(f["on_stop"])
        self.ok.set_offsets(an[~bad] if (~bad).any() else np.empty((0, 2)))
        self.red.set_offsets(an[bad] if bad.any() else np.empty((0, 2)))
        done = t >= frames[-1]["t"]
        G = "tight spool" if self.row["law"] == "tight_spool" else f"G = {self.row['G']}"
        end = f"{self.row['outcome']} at {self.row['cycles_elapsed']:.2f} cyc" if done else "running"
        self.txt.set_text(f"t = {f['t']:6.1f} s\ncycle {f['t'] / self.rec['period_s']:5.2f}\n{G}\n{end}")
        return [self.body, self.cmd, self.head, self.ok, self.red, self.txt]


def animate(panels_data, out, frame_dt, fps, ncols, size_in=3.6, suptitle="", px=None, still=None):
    """Write a GIF (PillowWriter) or MP4 (H.264, yuv420p), or with still=t one PNG
    frame at time t (still="end": the last frame). px=(width, height) fixes the
    pixel size (dpi 100); otherwise the figure is sized from size_in at dpi 80."""
    n = len(panels_data)
    nrows = math.ceil(n / ncols)
    if n == 1:
        size_in = 5.5
    if px:
        figsize, dpi = (px[0] / 100, px[1] / 100), 100
    else:
        figsize, dpi = (size_in * ncols, size_in * nrows + 0.9), 80
    fs = 7 if not px else max(7, round(px[1] / 1080 * 15))
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, squeeze=False)
    top_in, bottom_in = 0.75 * fs / 7, 0.45 * fs / 7
    fig.subplots_adjust(
        left=0.02,
        right=0.98,
        top=1 - top_in / figsize[1],
        bottom=bottom_in / figsize[1],
        wspace=0.05,
        hspace=0.15,
    )
    # One scale for every panel, so the panels can be compared directly.
    bs = np.array([bounds(rec) for _, rec, _ in panels_data])
    span = max(bs[:, 1].max() - bs[:, 0].min(), bs[:, 3].max() - bs[:, 2].min())
    cx, cy = (bs[:, 0].min() + bs[:, 1].max()) / 2, (bs[:, 2].min() + bs[:, 3].max()) / 2
    box = (cx - span / 2, cx + span / 2, cy - span / 2, cy + span / 2)
    # Capsule width in points from the real (square, equal-aspect) axes size.
    pos = axes.flat[0].get_position()
    side_in = min(pos.width * figsize[0], pos.height * figsize[1])
    pts_per_m = side_in * 72 / span
    panels = [Panel(ax, row, rec, title, pts_per_m, box, fs) for ax, (row, rec, title) in zip(axes.flat, panels_data)]
    for ax in list(axes.flat)[n:]:
        ax.axis("off")
    fig.suptitle(suptitle, fontsize=fs + 2, y=0.995)
    fig.text(
        0.5,
        0.01,
        "blue: body, white dot = head   orange: commanded shape   red: joint at servo cap "
        "or on hard stop\ngrey: posts   dashed: finish line (lattice far edge)",
        ha="center",
        fontsize=fs,
    )
    t_end = max(p.rec["frames"][-1]["t"] for p in panels)
    out.parent.mkdir(parents=True, exist_ok=True)
    if still is not None:
        t = t_end if still == "end" else float(still)
        for p in panels:
            p.draw(t)
        fig.savefig(out, dpi=dpi)
        plt.close(fig)
        return 1
    times = np.arange(0.0, t_end + frame_dt, frame_dt)
    times = np.append(times, [t_end] * int(fps))  # hold the last frame for 1 s
    anim = FuncAnimation(fig, lambda k: [a for p in panels for a in p.draw(times[k])], frames=len(times), blit=False)
    if out.suffix == ".mp4":
        writer = FFMpegWriter(fps=fps, codec="libx264", extra_args=["-pix_fmt", "yuv420p", "-crf", "23"])
    else:
        writer = PillowWriter(fps=fps)
    anim.save(out, writer=writer, dpi=dpi)
    plt.close(fig)
    return len(times)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--G", type=float)
    ap.add_argument("--montage", help="comma-separated G values")
    ap.add_argument("--law", default="paper")
    ap.add_argument("--variant")
    ap.add_argument("--frame-dt", type=float, default=1.0)
    ap.add_argument("--fps", type=int, default=16)
    ap.add_argument("--out", help=".gif, .mp4 or (with --still) .png")
    ap.add_argument("--size", help="WIDTHxHEIGHT in pixels, e.g. 1920x1080")
    ap.add_argument("--duration", type=float, help="clip length in s (sets --frame-dt from the longest trial)")
    ap.add_argument("--still", help="write one PNG frame at this sim time in s, or 'end'")
    a = ap.parse_args()
    run_dir = Path(a.run_dir)
    Gs = [float(g) for g in a.montage.split(",")] if a.montage else [a.G]
    data = []
    for G in Gs:
        row, r, rec = replay(run_dir, a.seed, G, a.law, a.variant)
        print(
            f"G={G} seed={a.seed}: replay matches log ({row['outcome']}, {row['cycles_elapsed']:.2f} cycles, "
            f"final CoM dx {row['final_com_dx_m']:.4f} m)"
        )
        label = "tight spool" if a.law == "tight_spool" else f"G = {G}"
        data.append((row, rec, label))
    if a.duration:
        t_end = max(rec["frames"][-1]["t"] for _, rec, _ in data)
        a.frame_dt = t_end / max(1.0, (a.duration - 1.0) * a.fps)  # last 1 s holds the final frame
    tag = f"montage_seed{a.seed}" if a.montage else f"seed{a.seed}_{a.law}_G{a.G}"
    out = Path(a.out) if a.out else ROOT / "media" / f"{run_dir.parent.name}_{tag}.gif"
    title = (
        f"{run_dir.parent.name}  run {run_dir.name}  seed {a.seed}\n"
        + (f"settings: {variant_label(run_dir, a.variant)}\n" if a.variant else "")
        + ("" if a.still else f"{a.frame_dt * a.fps:.1f}x real time  |  ")
        + "simulation, not hardware"
    )
    px = tuple(int(v) for v in a.size.split("x")) if a.size else None
    nf = animate(data, out, a.frame_dt, a.fps, ncols=3 if len(data) > 1 else 1, suptitle=title, px=px, still=a.still)
    print(f"saved {out} ({nf} frames, {out.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
