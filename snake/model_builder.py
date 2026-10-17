"""Generate the planar snake MJCF from config/robot.yaml (docs/model_plan.md).

Frames: the head points along +x. Segment i's body origin is the joint pin at
its front; for the head that pin is virtual. The case (capsule) is centred
between the pins, with length body.case_length. The cable anchors sit L_j
behind the front pin and L_j ahead of the next pin, as in paper Fig. S4. Hinge axes are +z, so a positive joint angle lengthens the left
(+y) cable, which is the paper's sign convention for alpha (Eq. S1).
tests/test_model_builder.py checks this sign against Eq. S1.

Ground contact (G3, option 1): one passive wheel under each segment centre.
Its axle runs across the body (local y), so the wheel rolls along the body
axis and resists only by sliding when pushed sideways. That is where the
forward/sideways anisotropy comes from; scripts/drag_test.py measures it.

Mass placement: joint i's servo(s) sit in segment i, the segment behind the
joint. The paper's cables are spooled in one case and "fixed onto the case
ahead" (p. 53). So the head carries no servo, only the electronics.

Contact groups (contype/conaffinity bits):
  floor  1/0  touches wheels only
  wheel  0/1  floor only
  body   4/6  posts and non-adjacent segments (MuJoCo skips parent-child pairs)
  post   2/0  bodies only (posts are added by snake/arena.py, milestone 4)
"""
import math
import xml.etree.ElementTree as ET

import mujoco

from snake import config as cfgmod

FLOOR = dict(contype="1", conaffinity="0")
WHEEL = dict(contype="0", conaffinity="1")
BODY = dict(contype="4", conaffinity="6")


def _fmt(*xs):
    return " ".join(f"{x:.9g}" for x in xs)


def _check(c):
    b, cab, g, m = c["body"], c["cable"], c["ground"], c["mass"]
    r = b["segment_width"] / 2
    if g["model"] != "wheels":
        raise ValueError(f"ground.model {g['model']!r} not implemented (G3 chose wheels)")
    if b["segment_pitch"] <= 2 * cab["joint_offset"]:
        raise ValueError("segment_pitch must exceed 2*joint_offset (anchors would cross)")
    if not 0 < b["case_length"] < b["segment_pitch"]:
        raise ValueError("case_length must be positive and shorter than segment_pitch")
    if cab["half_spacing"] > r:
        raise ValueError("cable half_spacing (L_c) must lie inside the segment width")
    if b["ride_height"] <= r:
        raise ValueError("ride_height must exceed the capsule radius, or the body drags on the floor")
    if not 0 < g["wheel_radius"] <= b["ride_height"]:
        raise ValueError("wheel_radius must be in (0, ride_height]")
    if g["axle_friction_timeconst"] < 2 * c["sim"]["timestep"]:
        raise ValueError("axle_friction_timeconst must be >= 2 x timestep")
    if cab["l0_per_R"] < 1:
        raise ValueError("cable.l0_per_R must be >= 1, or Eq. 3 commands cables shorter than exact")
    if g["anisotropy_ratio"] <= 1:
        raise ValueError("anisotropy_ratio must exceed 1 (rolling-friction law needs R > 1)")
    if c["sim"]["cone"] != "elliptic":
        raise ValueError("the rolling-resistance law assumes sim.cone = elliptic")
    if not 0 < m["wheel"] < m["hardware"]:
        raise ValueError("mass.wheel must be positive and part of mass.hardware")


def segment_masses(c):
    """Rigid-body mass of each segment, excluding its wheel (kg). Head first."""
    m, n = c["mass"], c["body"]["n_segments"]
    base = m["shell"] + m["hardware"] - m["wheel"]
    servos = m["servos_per_joint"] * m["servo"]
    return [base + (m["head_electronics"] if i == 0 else servos) for i in range(n)]


POST = dict(contype="2", conaffinity="0")


def build_mjcf(c=None, drag_rig=False, posts=None, post_radius=None, post_height=None, post_friction=None):
    """Return the MJCF XML string for config dict c (default: config/robot.yaml).

    drag_rig=True adds velocity actuators on root_x and root_y and a stiff
    position actuator on root_yaw, used by scripts/drag_test.py.
    posts: optional (N, 2) array of post centres (snake/arena.py), added as
    fixed vertical cylinders that collide with the body capsules only.
    """
    c = c or cfgmod.load()
    _check(c)
    b, m, j, cab, s, g, sim = (c[k] for k in ("body", "mass", "joint", "cable", "servo", "ground", "sim"))
    n, p, r = b["n_segments"], b["segment_pitch"], b["segment_width"] / 2
    Lj, Lc, h = cab["joint_offset"], cab["half_spacing"], b["ride_height"]
    rw, mu = g["wheel_radius"], g["friction_sliding"]
    floor_friction = _fmt(mu, 0.005, 0.0001)
    # Wheel tyre contact: condim 6 adds torsional and rolling friction; both
    # scale with the wheel load N. With an elliptic cone, sliding force f and
    # rolling torque tau share one limit: (f/mu)^2 + (tau/mu_roll)^2 <= N^2.
    # Dragging a free wheel forward, tau = f r, so f = mu N / sqrt(1 + (mu r / mu_roll)^2).
    # Sideways, f = mu N. For a sideways/forward ratio R:
    #     mu_roll = mu r / sqrt(R^2 - 1)
    # independent of segment mass (derived here, checked by tests/test_wheels.py).
    # At that limit the tyre partly skids instead of rolling cleanly; the
    # force law is the intended one, the wheel spin rate is not.
    mu_roll = mu * rw / math.sqrt(g["anisotropy_ratio"] ** 2 - 1)
    tyre_friction = _fmt(mu, g["torsional_friction"], mu_roll)

    root = ET.Element("mujoco", model="planar_snake")
    ET.SubElement(root, "compiler", angle="radian", autolimits="true")
    ET.SubElement(root, "option", timestep=_fmt(sim["timestep"]), integrator=sim["integrator"],
                  cone=sim["cone"])
    ET.SubElement(root, "visual").append(ET.Element("global", offwidth="1280", offheight="720"))

    asset = ET.SubElement(root, "asset")
    ET.SubElement(asset, "texture", name="grid", type="2d", builtin="checker", width="512",
                  height="512", rgb1=".85 .85 .85", rgb2=".75 .75 .75")
    ET.SubElement(asset, "material", name="grid", texture="grid", texrepeat="10 10")

    world = ET.SubElement(root, "worldbody")
    ET.SubElement(world, "light", pos="0 0 3", dir="0 0 -1", directional="true")
    ET.SubElement(world, "geom", name="floor", type="plane", size="5 5 0.1", material="grid",
                  friction=floor_friction, **FLOOR)

    # Structure (case) and cable anchors are separate parameters, so moving the
    # anchors does not change the body's shape or inertia.
    if posts is not None:
        for k, (px, py) in enumerate(posts):
            ET.SubElement(world, "geom", name=f"post{k}", type="cylinder",
                          size=_fmt(post_radius, post_height / 2), pos=_fmt(px, py, post_height / 2),
                          friction=_fmt(post_friction, 0.005, 0.0001), priority="2",
                          rgba="0.95 0.95 0.95 1", **POST)
            # priority="2": the post's friction is used for body-post contacts.
            # Without it MuJoCo takes the larger of the two geoms' values, and
            # the capsules' default 1.0 overrode the configured value
            # (lattice diagnosis, run 20261016T185419Z_91e48fc).

    seg_len = b["case_length"]                          # case, face to face
    x_mid = -p / 2
    x_front, x_rear = x_mid + seg_len / 2, x_mid - seg_len / 2
    x_anchor_front, x_anchor_rear = -Lj, -(p - Lj)      # paper Fig. S4: L_j from each pin
    hinge_limit = math.radians(j["hard_limit_deg"])
    masses = segment_masses(c)

    parent = world
    for i in range(n):
        if i == 0:
            body = ET.SubElement(parent, "body", name="seg0", pos=_fmt(0, 0, h))
            # Planar root (G1): x/y/z slides + yaw hinge, no roll or pitch.
            for name, typ, axis in (("root_x", "slide", "1 0 0"), ("root_y", "slide", "0 1 0"),
                                    ("root_z", "slide", "0 0 1"), ("root_yaw", "hinge", "0 0 1")):
                ET.SubElement(body, "joint", name=name, type=typ, axis=axis)
        else:
            body = ET.SubElement(parent, "body", name=f"seg{i}", pos=_fmt(-p, 0, 0))
            ET.SubElement(body, "joint", name=f"j{i}", type="hinge", axis="0 0 1",
                          range=_fmt(-hinge_limit, hinge_limit),
                          stiffness=_fmt(j["stiffness"]), damping=_fmt(j["damping"]),
                          frictionloss=_fmt(j["frictionloss"]))
            # Optional out-of-plane compliance (chatter diagnosis, not the
            # approved model): springs that let each segment tilt or rise a
            # little, so the 7 wheels are no longer forced onto one rigid plane.
            vc = b["vertical_compliance"]
            if vc != "none":
                k, damp = _fmt(b["vertical_stiffness"]), _fmt(b["vertical_damping"])
                if vc == "rollpitch":
                    for nm, ax in (("roll", "1 0 0"), ("pitch", "0 1 0")):
                        ET.SubElement(body, "joint", name=f"{nm}{i}", type="hinge", axis=ax,
                                      stiffness=k, damping=damp)
                elif vc == "slide":
                    ET.SubElement(body, "joint", name=f"lift{i}", type="slide", axis="0 0 1",
                                  stiffness=k, damping=damp)
                else:
                    raise ValueError(f"unknown body.vertical_compliance {vc!r}")

        # Inertia of a solid box seg_len x width x width (model_plan.md section 1).
        mass, w = masses[i], 2 * r
        ET.SubElement(body, "inertial", pos=_fmt(x_mid, 0, 0), mass=_fmt(mass),
                      diaginertia=_fmt(mass * 2 * w**2 / 12, mass * (seg_len**2 + w**2) / 12,
                                       mass * (seg_len**2 + w**2) / 12))
        ET.SubElement(body, "geom", name=f"seg{i}_body", type="capsule", size=_fmt(r),
                      fromto=_fmt(x_front, 0, 0, x_rear, 0, 0), mass="0",
                      rgba="0.85 0.45 0.1 1" if i == 0 else "0.9 0.6 0.2 1", **BODY)
        if i == 0:
            ET.SubElement(body, "site", name="head_tip", pos=_fmt(x_front + r, 0, 0), size="0.004")
        # Cable anchor sites on both faces (paper Fig. S4).
        for side, y in (("l", Lc), ("r", -Lc)):
            ET.SubElement(body, "site", name=f"seg{i}_front_{side}", pos=_fmt(x_anchor_front, y, 0), size="0.003")
            ET.SubElement(body, "site", name=f"seg{i}_rear_{side}", pos=_fmt(x_anchor_rear, y, 0), size="0.003")

        # Passive wheel: axle along local y, so it rolls along the body axis.
        wheel = ET.SubElement(body, "body", name=f"wheel{i}", pos=_fmt(x_mid, 0, -(h - rw)))
        ET.SubElement(wheel, "joint", name=f"axle{i}", type="hinge", axis="0 1 0",
                      frictionloss=_fmt(g["axle_friction"]),
                      solreffriction=_fmt(g["axle_friction_timeconst"], 1))
        ET.SubElement(wheel, "geom", name=f"wheel{i}_tyre", type="cylinder",
                      size=_fmt(rw, g["wheel_half_width"]), zaxis="0 1 0", mass=_fmt(m["wheel"]),
                      friction=tyre_friction, condim="6", priority="1",
                      solref=_fmt(g["contact_timeconst"], 1),
                      rgba="0.2 0.2 0.2 1", **WHEEL)
        parent = body

    # Cables as spatial tendons from segment i-1's rear face to segment i's
    # front face. No length limit yet: they only measure length until
    # implementation B.
    tendon = ET.SubElement(root, "tendon")
    for i in range(1, n):
        for side in ("l", "r"):
            t = ET.SubElement(tendon, "spatial", name=f"cable{i}_{side}", width="0.001")
            ET.SubElement(t, "site", site=f"seg{i-1}_rear_{side}")
            ET.SubElement(t, "site", site=f"seg{i}_front_{side}")

    # Joint actuation, torque capped at servo stall:
    #   position:     stiff position servo (E0); ctrl = target angle.
    #   compliance_A: torque motor; ctrl = torque from snake/actuation.py.
    act = ET.SubElement(root, "actuator")
    for i in range(1, n):
        if s["actuation"] == "position":
            ET.SubElement(act, "position", name=f"servo{i}", joint=f"j{i}", kp=_fmt(s["kp"]),
                          forcerange=_fmt(-s["stall_torque"], s["stall_torque"]))
        elif s["actuation"] == "compliance_A":
            ET.SubElement(act, "motor", name=f"servo{i}", joint=f"j{i}", gear="1",
                          ctrlrange=_fmt(-s["stall_torque"], s["stall_torque"]),
                          forcerange=_fmt(-s["stall_torque"], s["stall_torque"]))
        else:
            raise ValueError(f"unknown servo.actuation {s['actuation']!r}")
    if drag_rig:
        ET.SubElement(act, "velocity", name="drag_x", joint="root_x", kv="50")
        ET.SubElement(act, "velocity", name="drag_y", joint="root_y", kv="50")
        ET.SubElement(act, "position", name="hold_yaw", joint="root_yaw", kp="50", kv="5")

    ET.indent(root)
    return ET.tostring(root, encoding="unicode")


def build_model(c=None, drag_rig=False, **post_kw):
    return mujoco.MjModel.from_xml_string(build_mjcf(c, drag_rig, **post_kw))


if __name__ == "__main__":
    import sys

    raw = cfgmod.load_raw()
    ph = cfgmod.placeholders(raw)
    if ph:
        print(f"WARNING: {len(ph)} placeholder values in use: {', '.join(ph)}", file=sys.stderr)
    print(build_mjcf(cfgmod.values(raw)))
