"""Environment check for CLAUDE.md section 3, step 1.

Runs four checks and prints a block to paste into docs/progress.md:
  1. `import mujoco` works
  2. a tiny model steps headless
  3. `mujoco.viewer` opens a window (skipped with --no-viewer)
  4. offscreen rendering to a video file works

Usage:
  python scripts/check_env.py               # all four checks
  python scripts/check_env.py --no-viewer   # headless machines

If offscreen rendering fails, retry with an explicit GL backend, e.g.
  MUJOCO_GL=egl python scripts/check_env.py      (Linux, GPU)
  MUJOCO_GL=osmesa python scripts/check_env.py   (Linux, software)
  MUJOCO_GL=glfw python scripts/check_env.py     (Windows/macOS default)
"""
import argparse
import os
import platform
import sys
import time
import traceback

# A falling box on a plane: enough to exercise contact, stepping and rendering.
TINY_XML = """
<mujoco>
  <option timestep="0.002"/>
  <worldbody>
    <light pos="0 0 3"/>
    <geom type="plane" size="1 1 0.1"/>
    <body pos="0 0 0.5">
      <freejoint/>
      <geom type="box" size="0.05 0.05 0.05" mass="0.1"/>
    </body>
  </worldbody>
</mujoco>
"""

results = {}


def check(name, fn):
    try:
        detail = fn()
        results[name] = ("PASS", detail or "")
    except Exception as exc:  # report the exact error, as section 3 asks
        results[name] = ("FAIL", f"{type(exc).__name__}: {exc}")
        traceback.print_exc()


def step_headless():
    import mujoco
    m = mujoco.MjModel.from_xml_string(TINY_XML)
    d = mujoco.MjData(m)
    z0 = d.qpos[2]
    for _ in range(1000):  # 2 s of sim time
        mujoco.mj_step(m, d)
    z1 = d.qpos[2]
    # The box (half-height 0.05) should have fallen and come to rest on the plane.
    if not (0.03 < z1 < 0.07):
        raise RuntimeError(f"box height after 2 s is {z1:.4f} m, expected ~0.05 m")
    return f"box fell from z={z0:.3f} m to z={z1:.4f} m in 2 s sim time"


def open_viewer(seconds=3.0):
    import mujoco
    import mujoco.viewer
    m = mujoco.MjModel.from_xml_string(TINY_XML)
    d = mujoco.MjData(m)
    with mujoco.viewer.launch_passive(m, d) as v:
        t_end = time.time() + seconds
        while v.is_running() and time.time() < t_end:
            mujoco.mj_step(m, d)
            v.sync()
            time.sleep(m.opt.timestep)
    return f"passive viewer opened for {seconds:.0f} s"


def render_video(path):
    import mujoco
    import mediapy
    m = mujoco.MjModel.from_xml_string(TINY_XML)
    d = mujoco.MjData(m)
    frames = []
    with mujoco.Renderer(m, height=240, width=320) as r:
        for i in range(500):
            mujoco.mj_step(m, d)
            if i % 17 == 0:  # ~30 fps at dt=0.002
                r.update_scene(d)
                frames.append(r.render())
    mediapy.write_video(path, frames, fps=30)
    size = os.path.getsize(path)
    if size == 0:
        raise RuntimeError("video file is empty")
    return f"{len(frames)} frames -> {path} ({size} bytes)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-viewer", action="store_true")
    args = ap.parse_args()

    out_dir = "env_check_output"
    os.makedirs(out_dir, exist_ok=True)

    def imp():
        import mujoco
        return f"mujoco {mujoco.__version__}"

    check("1. import mujoco", imp)
    check("2. headless step", step_headless)
    if args.no_viewer:
        results["3. viewer window"] = ("SKIPPED", "--no-viewer")
    else:
        check("3. viewer window", open_viewer)
    check("4. offscreen video", lambda: render_video(os.path.join(out_dir, "tiny.mp4")))

    try:
        import mujoco
        mj_ver = mujoco.__version__
    except Exception:
        mj_ver = "not importable"

    print("\n---- paste into docs/progress.md ----")
    print(f"- OS: {platform.platform()}")
    print(f"- Python: {sys.version.split()[0]}")
    print(f"- MuJoCo: {mj_ver}")
    print(f"- MUJOCO_GL: {os.environ.get('MUJOCO_GL', '(unset)')}")
    for name, (status, detail) in results.items():
        print(f"- {name}: {status} — {detail}")
    print("-------------------------------------")
    sys.exit(0 if all(s != "FAIL" for s, _ in results.values()) else 1)


if __name__ == "__main__":
    main()
