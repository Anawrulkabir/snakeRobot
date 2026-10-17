"""Watch the model run the serpenoid gait with the configured actuation (default: implementation A).

For inspection only, not an experiment. Masses and other placeholders still
apply.

  mjpython scripts/view_model.py --G 0.75           # macOS, interactive viewer
  python scripts/view_model.py --G 0.75             # Linux/Windows viewer
  python scripts/view_model.py --G 0 --video out.mp4   # headless, needs ffmpeg
"""

import argparse
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mujoco  # noqa: E402

from snake import config as cfgmod  # noqa: E402
from snake.model_builder import build_model  # noqa: E402
from snake.sim import make_controller  # noqa: E402


def controller(model, G):
    g = cfgmod.load("gait.yaml")["wave"]
    _, ctrl = make_controller(
        model, cfgmod.load(), math.radians(g["amplitude_deg"]), g["spatial_freq"], g["temporal_freq"], G=G
    )
    return ctrl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", help="write an mp4 instead of opening the viewer")
    ap.add_argument("--seconds", type=float, default=24.0)
    ap.add_argument(
        "--G",
        type=float,
        default=cfgmod.load("gait.yaml")["compliance"]["G"],
        help="generalized compliance (paper Eq. 3)",
    )
    args = ap.parse_args()

    ph = cfgmod.placeholders(cfgmod.load_raw()) + cfgmod.placeholders(cfgmod.load_raw("gait.yaml"))
    print(f"NOTE: {len(ph)} placeholder values in use: {', '.join(ph)}")

    m = build_model()
    d = mujoco.MjData(m)
    ctrl = controller(m, args.G)

    if args.video:
        import mediapy

        frames = []
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        cam.trackbodyid = m.body("seg3").id
        cam.distance, cam.elevation, cam.azimuth = 1.2, -60, 90
        with mujoco.Renderer(m, height=480, width=640) as r:
            while d.time < args.seconds:
                ctrl(d)
                mujoco.mj_step(m, d)
                if len(frames) < d.time * 30:
                    r.update_scene(d, camera=cam)
                    frames.append(r.render())
        mediapy.write_video(args.video, frames, fps=30)
        print(f"wrote {len(frames)} frames to {args.video}")
        return

    import mujoco.viewer

    with mujoco.viewer.launch_passive(m, d) as v:
        while v.is_running():
            t0 = time.time()
            ctrl(d)
            mujoco.mj_step(m, d)
            v.sync()
            time.sleep(max(0.0, m.opt.timestep - (time.time() - t0)))


if __name__ == "__main__":
    main()
