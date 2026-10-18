"""Success rate vs generalized compliance G, medium lattice: the project's
main figure (CLAUDE.md 7), from saved runs only.

Series (each from its trials.jsonl; the run ID is printed on the figure):
  E1 pilot, baseline setup        run 20261017T062232Z_b5aac2a (20 seeds per G)
  calibration step 2, combined    run 20261017T111457Z_cc9bd78 (5 seeds per G)
  H1 test, combined, fresh seeds  run 20261018T071302Z_d73fb14 (10 seeds per G, medium only)
Error bars: 95% Wilson score intervals. Simulation results.

  python scripts/plot_success_vs_G.py [--out media/success_vs_G.png]
"""

import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
# name, run, variant, colour, marker, (label point index, label offset in points)
SERIES = [
    ("E1 pilot (baseline setup)", "results/E1_pilot/20261017T062232Z_b5aac2a", None, "#2a78d6", "o", (-1, (12, -14))),
    (
        "Calibration step 2 (combined setup)",
        "results/calib_step2/20261017T111457Z_cc9bd78",
        "combined",
        "#eb6834",
        "s",
        (-1, (12, 14)),
    ),
    (
        "H1 test, fresh seeds (combined setup)",
        "results/h1_mechanism/20261018T071302Z_d73fb14",
        "combined",
        "#1baf7a",
        "^",
        (1, (-30, 22)),
    ),
]
INK, MUTED, GRID, SURFACE = "#1f1f1e", "#6b6a64", "#e4e3de", "#fcfcfb"


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def series(run, variant):
    rows = [json.loads(x) for x in (ROOT / run / "trials.jsonl").read_text().splitlines() if x.strip()]
    rows = [r for r in rows if r["law"] == "paper" and r["density"] == "medium" and r.get("variant") == variant]
    out = {}
    for G in sorted({r["G"] for r in rows}):
        rs = [r for r in rows if r["G"] == G and r["outcome"] != "diverged"]
        out[G] = (sum(r["outcome"] == "success" for r in rs), len(rs))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "media" / "success_vs_G.png"))
    a = ap.parse_args()
    fig, ax = plt.subplots(figsize=(12.8, 8.0), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    offsets = (-0.018, 0.0, 0.018)
    for (name, run, variant, color, marker, (li, loff)), dx in zip(SERIES, offsets):
        s = series(run, variant)
        Gs = sorted(s)
        stats = [wilson(*s[G]) for G in Gs]
        xs = [G + dx for G in Gs]
        ps = [p for p, _, _ in stats]
        ax.plot(xs, ps, color=color, lw=2, zorder=3)
        ax.errorbar(
            xs,
            ps,
            yerr=[[p - lo for p, lo, _ in stats], [hi - p for p, _, hi in stats]],
            fmt="none",
            ecolor=color,
            elinewidth=1.2,
            capsize=0,
            alpha=0.55,
            zorder=2,
        )
        ax.scatter(
            xs,
            ps,
            s=70,
            marker=marker,
            color=color,
            edgecolors=SURFACE,
            linewidths=2,
            zorder=4,
            label=f"{name}  (n = {s[Gs[0]][1]} per G, run {Path(run).name})",
        )
        # Direct label (identity is never colour alone), placed clear of the other series.
        ax.annotate(
            name.split(" (")[0],
            (xs[li], ps[li]),
            xytext=loff,
            textcoords="offset points",
            va="center",
            fontsize=10.5,
            color=INK,
        )
    ax.set_xlim(-0.08, 1.8)
    ax.set_ylim(-0.04, 1.06)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5])
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("Generalized compliance G  (0 = stiff, 1.5 = loose)", color=INK, fontsize=11)
    ax.set_ylabel("Trials crossing the lattice", color=INK, fontsize=11)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=10)
    ax.set_title("Success rate vs compliance, medium post lattice", loc="left", color=INK, fontsize=14, pad=14)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=1, frameon=False, fontsize=9, labelcolor=INK)
    fig.text(
        0.01,
        0.01,
        "MuJoCo simulation, not hardware. Error bars: 95% Wilson intervals. "
        "Step-2 and H1 rows share one setup; the pre-registered step-2 outcome was 'inconclusive'.",
        fontsize=8.5,
        color=MUTED,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=SURFACE)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
