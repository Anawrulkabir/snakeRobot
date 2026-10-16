"""Generate the planar snake MJCF from config/robot.yaml (docs/model_plan.md).

Frames: the head points along +x. Segment i's body origin is the joint pin at
its front; for the head that pin is virtual. The segment's front face is L_j
behind its pin and its rear face is L_j ahead of the next pin, as in paper
Fig. S4. Hinge axes are +z, so a positive joint angle lengthens the left
(+y) cable, which is the paper's sign convention for alpha (Eq. S1).
tests/test_model_builder.py checks this sign against Eq. S1.

Contact groups (contype/conaffinity bits):
  floor  1/0  touches feet only
  foot   0/1  floor only
  body   4/6  posts and non-adjacent segments (MuJoCo skips parent-child pairs)
  post   2/0  bodies only (posts are added by snake/arena.py, milestone 4)
"""
import xml.etree.ElementTree as ET

import mujoco

from snake import config as cfgmod

FLOOR = dict(contype="1", conaffinity="0")
FOOT = dict(contype="0", conaffinity="1")
BODY = dict(contype="4", conaffinity="6")


def _fmt(*xs):
    return " ".join(f"{x:.9g}" for x in xs)


def _check(c):
    b, cab, g = c["body"], c["cable"], c["ground"]
    r = b["segment_width"] / 2
    if b["segment_pitch"] <= 2 * cab["joint_offset"]:
        raise ValueError("segment_pitch must exceed 2*joint_offset (segment would have no length)")
    if cab["half_spacing"] > r:
        raise ValueError("cable half_spacing (L_c) must lie inside the segment width")
    if b["ride_height"] <= r:
        raise ValueError("ride_height must exceed the capsule radius, or the body drags on the floor")
    if not 0 < g["foot_radius"] <= b["ride_height"]:
        raise ValueError("foot_radius must be in (0, ride_height]")


def build_mjcf(c=None):
    """Return the MJCF XML string for the config dict c (default: config/robot.yaml)."""
    c = c or cfgmod.load()
    _check(c)
    b, m, j, cab, s, g, sim = (c[k] for k in ("body", "mass", "joint", "cable", "servo", "ground", "sim"))
    n, p, r = b["n_segments"], b["segment_pitch"], b["segment_width"] / 2
    Lj, Lc, h = cab["joint_offset"], cab["half_spacing"], b["ride_height"]

    root = ET.Element("mujoco", model="planar_snake")
    ET.SubElement(root, "compiler", angle="radian", autolimits="true")
    ET.SubElement(root, "option", timestep=_fmt(sim["timestep"]), integrator=sim["integrator"])
    ET.SubElement(root, "visual").append(ET.Element("global", offwidth="1280", offheight="720"))

    asset = ET.SubElement(root, "asset")
    ET.SubElement(asset, "texture", name="grid", type="2d", builtin="checker", width="512",
                  height="512", rgb1=".85 .85 .85", rgb2=".75 .75 .75")
    ET.SubElement(asset, "material", name="grid", texture="grid", texrepeat="10 10")

    world = ET.SubElement(root, "worldbody")
    ET.SubElement(world, "light", pos="0 0 3", dir="0 0 -1", directional="true")
    ET.SubElement(world, "geom", name="floor", type="plane", size="5 5 0.1", material="grid",
                  friction=_fmt(g["friction_sliding"], 0.005, 0.0001), **FLOOR)

    seg_len = p - 2 * Lj                # face to face
    x_front, x_rear = -Lj, -(p - Lj)    # face positions in the segment frame
    x_mid = -p / 2
    hinge_limit = j["hard_limit_deg"] * 3.141592653589793 / 180

    parent = world
    for i in range(n):
        if i == 0:
            body = ET.SubElement(parent, "body", name="seg0", pos=_fmt(0, 0, h))
            # Planar root (G1): x/y/z slides + yaw hinge, no roll or pitch.
            for name, typ, axis in (("root_x", "slide", "1 0 0"), ("root_y", "slide", "0 1 0"),
                                    ("root_z", "slide", "0 0 1"), ("root_yaw", "hinge", "0 0 1")):
                ET.SubElement(body, "joint", name=name, type=typ, axis=axis, damping="0", armature="0")
        else:
            body = ET.SubElement(parent, "body", name=f"seg{i}", pos=_fmt(-p, 0, 0))
            ET.SubElement(body, "joint", name=f"j{i}", type="hinge", axis="0 0 1",
                          range=_fmt(-hinge_limit, hinge_limit),
                          stiffness=_fmt(j["stiffness"]), damping=_fmt(j["damping"]))

        mass = m["segment"] + (m["head_extra"] if i == 0 else 0.0)
        # Inertia of a solid box seg_len x width x width (model_plan.md section 1).
        w = 2 * r
        ixx = mass * (w**2 + w**2) / 12
        iyy = mass * (seg_len**2 + w**2) / 12
        ET.SubElement(body, "inertial", pos=_fmt(x_mid, 0, 0), mass=_fmt(mass),
                      diaginertia=_fmt(ixx, iyy, iyy))
        ET.SubElement(body, "geom", name=f"seg{i}_body", type="capsule", size=_fmt(r),
                      fromto=_fmt(x_front, 0, 0, x_rear, 0, 0), mass="0",
                      rgba="0.85 0.45 0.1 1" if i == 0 else "0.9 0.6 0.2 1", **BODY)
        ET.SubElement(body, "geom", name=f"seg{i}_foot", type="sphere", size=_fmt(g["foot_radius"]),
                      pos=_fmt(x_mid, 0, -(h - g["foot_radius"])), mass="0",
                      friction=_fmt(g["friction_sliding"], 0.005, 0.0001), rgba="0.2 0.2 0.2 1", **FOOT)
        # Cable anchor sites on both faces (paper Fig. S4).
        for side, y in (("l", Lc), ("r", -Lc)):
            ET.SubElement(body, "site", name=f"seg{i}_front_{side}", pos=_fmt(x_front, y, 0), size="0.003")
            ET.SubElement(body, "site", name=f"seg{i}_rear_{side}", pos=_fmt(x_rear, y, 0), size="0.003")
        parent = body

    # Cables as spatial tendons from segment i's rear face to segment i+1's front
    # face. No length limit yet: they only measure length until implementation B.
    tendon = ET.SubElement(root, "tendon")
    for i in range(1, n):
        for side in ("l", "r"):
            t = ET.SubElement(tendon, "spatial", name=f"cable{i}_{side}", width="0.001")
            ET.SubElement(t, "site", site=f"seg{i-1}_rear_{side}")
            ET.SubElement(t, "site", site=f"seg{i}_front_{side}")

    # Stiff body for E0: a position servo per joint, torque capped at stall.
    act = ET.SubElement(root, "actuator")
    for i in range(1, n):
        ET.SubElement(act, "position", name=f"servo{i}", joint=f"j{i}", kp=_fmt(s["kp"]),
                      forcerange=_fmt(-s["stall_torque"], s["stall_torque"]))

    ET.indent(root)
    return ET.tostring(root, encoding="unicode")


def build_model(c=None):
    return mujoco.MjModel.from_xml_string(build_mjcf(c))


if __name__ == "__main__":
    import sys

    raw = cfgmod.load_raw()
    ph = cfgmod.placeholders(raw)
    if ph:
        print(f"WARNING: {len(ph)} placeholder values in use: {', '.join(ph)}", file=sys.stderr)
    print(build_mjcf(cfgmod.values(raw)))
