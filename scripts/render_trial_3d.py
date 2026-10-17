"""Overhead 3D clip of a logged lattice trial, rendered offscreen by MuJoCo.

Replays the trial (scripts/animate_trial.py replay: same config snapshot,
checked against the log), then re-poses the model from the recorded qpos and
renders with a fixed camera looking straight down. Needs an offscreen GL
backend: in the cloud sandbox, OSMesa (apt-get install libosmesa6, software
rendering; EGL failed without a GPU, 2026-10-17).

  MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa python scripts/render_trial_3d.py \
      results/E1_pilot/<run_id> --seed 1001 --G 0.75 --out media/x.gif
Options: --seconds 16 (clip length, from t = 0), --speed 2 (x real time), --fps 10
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import mujoco  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from animate_trial import replay  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--G", type=float, required=True)
    ap.add_argument("--law", default="paper")
    ap.add_argument("--seconds", type=float, default=16.0)
    ap.add_argument("--speed", type=float, default=2.0)
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--width", type=int, default=480)
    ap.add_argument("--height", type=int, default=360)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    row, r, rec = replay(a.run_dir, a.seed, a.G, a.law)
    print(f"replay matches log ({row['outcome']}, {row['cycles_elapsed']:.2f} cycles)")
    m = rec["model"]
    m.vis.global_.offwidth, m.vis.global_.offheight = max(a.width, 640), max(a.height, 480)
    # Display only (the trial has already run): grey posts, darker floor, no shadows.
    for k in range(len(rec["posts"])):
        m.geom_rgba[m.geom(f"post{k}").id] = [0.45, 0.45, 0.5, 1.0]
    m.geom_matid[m.geom("floor").id] = -1
    m.geom_rgba[m.geom("floor").id] = [0.85, 0.87, 0.9, 1.0]
    opt = mujoco.MjvOption()
    m.vis.global_.orthographic = 1  # true top view: post walls not seen in perspective
    d = mujoco.MjData(m)
    frames = rec["frames"]
    ts = np.array([f["t"] for f in frames])
    xy = np.array([p for f in frames for c in f["capsules"] for p in c])
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.lookat[:] = [*(xy.min(axis=0) + xy.max(axis=0)) / 2, 0.0]
    cam.distance = 1.2 * max(np.ptp(xy, axis=0)) + 0.6
    m.vis.global_.fovy = cam.distance * 0.9  # orthographic: fovy is the view height in metres
    cam.elevation, cam.azimuth = -90.0, 90.0  # straight down, +x to the right
    renderer = mujoco.Renderer(m, a.height, a.width)
    renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW] = False
    t_out = np.arange(0.0, min(a.seconds, ts[-1]), a.speed / a.fps)
    imgs = []
    for t in t_out:
        f = frames[min(int(np.searchsorted(ts, t)), len(frames) - 1)]
        d.qpos[:] = f["qpos"]
        mujoco.mj_forward(m, d)
        renderer.update_scene(d, camera=cam, scene_option=opt)
        renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW] = False
        imgs.append(renderer.render())
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Pillow, not mediapy: ffmpeg's GIF encoder rejected the pixel format here.
    pil = [Image.fromarray(i).convert("P", palette=Image.ADAPTIVE, colors=128) for i in imgs]
    pil[0].save(out, save_all=True, append_images=pil[1:], duration=int(1000 / a.fps), loop=0, optimize=True)
    print(f"saved {out} ({len(imgs)} frames, {out.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
