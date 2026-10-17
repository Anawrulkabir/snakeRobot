"""Overhead 3D clip of a logged lattice trial, rendered offscreen by MuJoCo.

Replays the trial (scripts/animate_trial.py replay: same config snapshot,
checked against the log), then re-poses the model from the recorded qpos and
renders with a fixed camera looking straight down. Needs an offscreen GL
backend: in the cloud sandbox, OSMesa (apt-get install libosmesa6, software
rendering; EGL failed without a GPU, 2026-10-17).

  MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa python scripts/render_trial_3d.py \
      results/E1_pilot/<run_id> --seed 1001 --G 0.75 --out media/x.mp4 --size 1920x1080 --duration 15

Cameras (--camera):
  overhead  orthographic top view framing the whole trajectory (default)
  angled    perspective, following the body from behind and above
  closeup   perspective, close to one joint (--joint), cable anchor sites
            enlarged and coloured (left red, right green), cables (tendons) shown
Output by extension: .mp4 (H.264, yuv420p), .gif, or with --still T a .png
frame at sim time T ("end" = last frame). A text box (run, seed, G, settings,
time, speed, "simulation, not hardware") is drawn on every frame. Joints at the
servo cap have their two adjacent segments tinted red.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import mujoco  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from animate_trial import replay, variant_label  # noqa: E402

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def overlay(img, lines, scale):
    im = Image.fromarray(img)
    dr = ImageDraw.Draw(im)
    f = font(max(12, int(18 * scale)))
    pad = int(10 * scale)
    w = max(dr.textlength(t, font=f) for t in lines)
    h = len(lines) * f.size * 1.25
    dr.rounded_rectangle(
        [pad, pad, pad + w + 2 * pad, pad + h + 2 * pad], radius=pad, fill=(255, 255, 255, 220), outline=(150, 150, 150)
    )
    for i, t in enumerate(lines):
        dr.text((2 * pad, 2 * pad + i * f.size * 1.25), t, fill=(0, 0, 0), font=f)
    return np.asarray(im)


def setup_view(m, rec, camera, joint, W, H, view=None, bound_frames=None):
    """Display-only changes (the trial has already run) and the camera."""
    for k in range(len(rec["posts"])):
        m.geom_rgba[m.geom(f"post{k}").id] = [0.45, 0.45, 0.5, 1.0]
    m.geom_matid[m.geom("floor").id] = -1
    m.geom_rgba[m.geom("floor").id] = [0.85, 0.87, 0.9, 1.0]
    m.vis.global_.offwidth, m.vis.global_.offheight = max(W, 640), max(H, 480)
    opt = mujoco.MjvOption()
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    frames = rec["frames"]
    if camera == "overhead":
        if view is not None:
            lo, hi = np.array([view[0], view[2]]), np.array([view[1], view[3]])
        else:
            src = bound_frames if bound_frames is not None else frames
            xy = np.array([p for f in src for c in f["capsules"] for p in c])
            margin = 0.08 if bound_frames is not None else 0.3
            lo, hi = xy.min(axis=0) - margin, xy.max(axis=0) + margin
        cam.lookat[:] = [*(lo + hi) / 2, 0.0]
        cam.elevation, cam.azimuth = -90.0, 90.0  # straight down, +x to the right
        cam.distance = 3.0
        m.vis.global_.orthographic = 1  # true top view; fovy is then the view height in metres
        m.vis.global_.fovy = max(hi[1] - lo[1], (hi[0] - lo[0]) * H / W)
    else:
        m.vis.global_.orthographic = 0
        m.vis.global_.fovy = 45
        if camera == "angled":
            cam.elevation, cam.azimuth, cam.distance = -32.0, 215.0, 0.95
        else:  # closeup
            cam.elevation, cam.azimuth, cam.distance = -55.0, 200.0, 0.22
            for side, rgba in (("l", [0.85, 0.1, 0.1, 1]), ("r", [0.1, 0.6, 0.1, 1])):
                for i in range(len(frames[0]["yaw"])):
                    for end in ("front", "rear"):
                        sid = m.site(f"seg{i}_{end}_{side}").id
                        m.site_rgba[sid] = rgba
                        m.site_size[sid] = [0.0035, 0, 0]
            opt.flags[mujoco.mjtVisFlag.mjVIS_TENDON] = True
            # The anchors (+-L_c = 20 mm off the centreline) lie inside the 25 mm-radius
            # capsules, so the capsules are drawn see-through here.
            for i in range(len(frames[0]["yaw"])):
                m.geom_rgba[m.geom(f"seg{i}_body").id, 3] = 0.3
    return cam, opt


def follow(cam, f, camera, joint, prev):
    """Tracking target for the perspective cameras, lightly smoothed."""
    if camera == "angled":
        target = np.mean([np.mean(c, axis=0) for c in f["capsules"]], axis=0)
    elif camera == "closeup":
        target = np.array(f["anchors"][joint - 1])
    else:
        return prev
    target = target if prev is None else 0.85 * prev + 0.15 * target
    cam.lookat[:] = [target[0], target[1], 0.02]
    return target


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--G", type=float, required=True)
    ap.add_argument("--law", default="paper")
    ap.add_argument("--variant")
    ap.add_argument("--camera", choices=["overhead", "angled", "closeup"], default="overhead")
    ap.add_argument("--joint", type=int, default=3, help="closeup: joint 1..6 (1 = behind the head)")
    ap.add_argument("--t0", type=float, default=0.0)
    ap.add_argument("--seconds", type=float, help="sim seconds to show (default: to the end)")
    ap.add_argument("--speed", type=float, default=2.0, help="x real time")
    ap.add_argument("--duration", type=float, help="clip length in s; overrides --speed")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--still", help="one PNG frame at this sim time, or 'end'")
    ap.add_argument("--view", help="overhead: x0,x1,y0,y1 in metres (default: the trajectory)")
    ap.add_argument("--tight", action="store_true", help="overhead: frame only the frames shown")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    W, H = (int(v) for v in a.size.split("x"))
    row, r, rec = replay(a.run_dir, a.seed, a.G, a.law, a.variant)
    print(f"replay matches log ({row['outcome']}, {row['cycles_elapsed']:.2f} cycles)")
    m = rec["model"]
    frames = rec["frames"]
    ts = np.array([f["t"] for f in frames])
    t_last = ts[-1]
    t1 = t_last if a.seconds is None else min(t_last, a.t0 + a.seconds)
    if a.still is not None:
        times = [t_last if a.still == "end" else float(a.still)]
    else:
        speed = (t1 - a.t0) / a.duration if a.duration else a.speed
        times = list(np.arange(a.t0, t1, speed / a.fps)) + [t1] * a.fps  # hold the last frame 1 s
    shown = [frames[min(int(np.searchsorted(ts, t)), len(frames) - 1)] for t in times]
    view = [float(v) for v in a.view.split(",")] if a.view else None
    cam, opt = setup_view(m, rec, a.camera, a.joint, W, H, view, shown if a.tight else None)
    d = mujoco.MjData(m)
    seg_geoms = [m.geom(f"seg{i}_body").id for i in range(len(frames[0]["yaw"]))]
    seg_rgba = m.geom_rgba[seg_geoms].copy()
    renderer = mujoco.Renderer(m, H, W)
    G = "tight spool" if a.law == "tight_spool" else f"G = {a.G}"
    run = Path(a.run_dir)
    head = [f"{run.parent.name}  run {run.name}", f"seed {a.seed}   {G}"]
    if a.variant:
        head.append(f"settings: {variant_label(run, a.variant)}")
    imgs, prev = [], None
    for t in times:
        f = frames[min(int(np.searchsorted(ts, t)), len(frames) - 1)]
        d.qpos[:] = f["qpos"]
        mujoco.mj_forward(m, d)
        m.geom_rgba[seg_geoms] = seg_rgba
        for j, cap in enumerate(f["at_cap"]):  # joint j+1 joins segments j and j+1
            if cap:
                m.geom_rgba[seg_geoms[j]] = m.geom_rgba[seg_geoms[j + 1]] = [0.9, 0.15, 0.1, 1.0]
        prev = follow(cam, f, a.camera, a.joint, prev)
        renderer.update_scene(d, camera=cam, scene_option=opt)
        renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW] = a.camera == "angled"
        end = f"{row['outcome']} at {row['cycles_elapsed']:.2f} cycles" if t >= t_last else "running"
        lines = head + [f"t = {f['t']:6.1f} s   cycle {f['t'] / rec['period_s']:5.2f}   {end}"]
        if a.still is None:
            lines.append(f"{(times[1] - times[0]) * a.fps:.1f}x real time")
        lines.append(
            "red segments: joint at servo cap"
            if a.camera != "closeup"
            else "red/green dots: left/right cable anchors; lines: cables"
        )
        lines.append("simulation, not hardware")
        imgs.append(overlay(renderer.render(), lines, H / 1080))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix == ".png":
        Image.fromarray(imgs[0]).save(out)
    elif out.suffix == ".mp4":
        import mediapy

        mediapy.write_video(str(out), imgs, fps=a.fps, codec="h264", crf=23)
    else:
        # Pillow, not mediapy: ffmpeg's GIF encoder rejected the pixel format here.
        pil = [Image.fromarray(i).convert("P", palette=Image.ADAPTIVE, colors=128) for i in imgs]
        pil[0].save(out, save_all=True, append_images=pil[1:], duration=int(1000 / a.fps), loop=0, optimize=True)
    print(f"saved {out} ({len(imgs)} frames, {out.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
