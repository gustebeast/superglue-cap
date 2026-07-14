"""Female bottle-neck socket thread — project-local ASYMMETRIC profile,
parameterized by a BottleSpec (two bottle variants share this code).

WHY NOT cadkit.threads: the bottles are single-start threads whose depth is
at/near pitch/2 (macbeath: pitch 2 × depth 0.8; loctite: pitch 3 × depth
1.0), and a symmetric 45° trapezoid can't exist there. This module cuts a
buttress-style female thread instead — ridge underside at 45° (the only
down-facing surface: self-supporting with the mouth on the bed), ridge top
at RIDGE_TOP_SLOPE_DEG from horizontal (up-facing: no constraint).

It still obeys every rule that cadkit/THREADS_README.md paid builds to learn:
  * the valley profile is a 4-POINT quad, swept with isFrenet;
  * the thread is CUT from a smooth crest-Ø blank, never grown as a ridge;
  * sweep height is WHOLE turns and ends INSIDE the blank;
  * one segment only (≤ ~10 mm ≪ the ~100 mm single-sweep limit);
  * clean=False on every thread boolean, and no heal()/ShapeFix afterwards;
  * never trust the eye: probe_socket_thread() classifies solid/void up the
    ridge band and the build FAILS if the pattern doesn't alternate.

Both the fit coupons and the real nozzles cut their socket with the SAME
socket_cutter() — a coupon is the real geometry, per the coupon rule in
cadkit/AGENTS.md.
"""

import math

import cadquery as cq

from .dimensions import (
    RIDGE_TIP_FLAT,
    RIDGE_TOP_SLOPE_DEG,
    SOCKET_MOUTH_CHAMFER,
    SOCKET_VALLEY_OVERSHOOT as _OVERSHOOT,
    SOCKET_WALL,
)
_END_OVER = 0.5          # smooth-bore overshoot past the body faces (dodges
                         # coincident-face booleans, cuts only air)


def _cyl(d, h, z=0.0):
    return cq.Workplane("XY").workplane(offset=z).circle(d / 2.0).extrude(h)


def _cone(d_bottom, d_top, h, z):
    return (cq.Workplane("XY").workplane(offset=z).circle(d_bottom / 2.0)
            .workplane(offset=h).circle(d_top / 2.0).loft())


def _valley_sweep(spec, z0, turns):
    """The helical valley cutter (ONE whole-turn-height segment), base at z0.

    Cut from the crest-Ø blank, the valley becomes the female RIDGE. Quad in
    the XZ plane, (radius, axial) coordinates:

        tip flat RIDGE_TIP_FLAT wide at the ridge-tip radius;
        LOWER edge drops 1:1 outward   -> ridge underside at 45° (down-facing);
        UPPER edge rises tan(15°) outward -> ridge top (up-facing, no limit).
    """
    r_tip = spec.ridge_tip_d / 2.0
    r_os = spec.bore_d / 2.0 + _OVERSHOOT
    d_os = r_os - r_tip
    top_rise = math.tan(math.radians(RIDGE_TOP_SLOPE_DEG))
    f = RIDGE_TIP_FLAT

    width_at_os = f + d_os * (1.0 + top_rise)
    assert width_at_os < spec.pitch, (
        f"{spec.name}: valley width {width_at_os:.2f} ≥ pitch {spec.pitch}: "
        f"adjacent turns would self-overlap into an invalid cutter (silent no-op)")

    gpts = [(r_tip, -f / 2.0),
            (r_os, -f / 2.0 - d_os),              # 45° underside flank
            (r_os, f / 2.0 + d_os * top_rise),    # 15° top flank
            (r_tip, f / 2.0)]

    h = math.ceil(turns - 1e-6) * spec.pitch              # WHOLE turns
    assert h <= 72.0, "tile in segments past ~72mm (see thread_segments)"
    r_mid = (r_tip + spec.bore_d / 2.0) / 2.0
    sweep = (cq.Workplane("XZ").polyline(gpts).close()
             .sweep(cq.Workplane("XY").add(
                 cq.Wire.makeHelix(pitch=spec.pitch, height=h, radius=r_mid)),
                 isFrenet=True))
    return sweep.translate((0, 0, z0))


def socket_cutter(spec, total_len, over_hi=_END_OVER, cone_ceiling=False,
                  turns=None):
    """The complete socket cutter for a body whose mouth face is at z=0 and
    which extends up to z=total_len: flared mouth + smooth entry bore + the
    threaded band (`turns` WHOLE turns starting at spec.entry_lead, which is
    derived so the first ridge's underside reaches the wall ABOVE the mouth
    chamfer; default turns = the spec's full-skirt count). clean=False.

    cone_ceiling=True makes a BLIND socket that closes as a 45° cone rising
    from the bore at z=total_len — the self-supporting ceiling for a nozzle
    printed mouth-down. over_hi is ignored in that case.

    Built smooth-first (cyl + mouth cone + ceiling cone), thread cut LAST —
    booleans on the finished helix are the slow/fragile ones.
    """
    if turns is None:
        turns = spec.socket_turns
    thread_top = spec.entry_lead + turns * spec.pitch
    assert thread_top < total_len, "thread must end inside the socket"

    if cone_ceiling:
        over_hi = 0.0
    blank = _cyl(spec.bore_d, total_len + _END_OVER + over_hi, z=-_END_OVER)
    mouth_d = spec.bore_d + 2.0 * SOCKET_MOUTH_CHAMFER
    blank = (blank
             .union(_cyl(mouth_d, _END_OVER, z=-_END_OVER))
             .union(_cone(mouth_d, spec.bore_d, SOCKET_MOUTH_CHAMFER, 0.0)))
    if cone_ceiling:
        # 45° ceiling: Ø bore at total_len narrowing to a near-apex. A true
        # apex makes loft() unhappy; a Ø0.2 top face is below one extrusion
        # width, so it slices as a point anyway.
        blank = blank.union(_cone(spec.bore_d, 0.2,
                                  (spec.bore_d - 0.2) / 2.0, total_len))
    return blank.cut(_valley_sweep(spec, spec.entry_lead, turns), clean=False)


def build_socket_coupon(spec):
    """test_<name>_socket.step — open tube (no top), the real socket geometry
    at the spec's coupon turn count.

    PRINT: mouth (chamfered end) DOWN on the bed, axis vertical, no supports.
    The profile is asymmetric, so orientation matters: printed the other way
    up, the 15° ridge tops become unprintable overhangs.
    """
    body = _cyl(spec.bore_d + 2 * SOCKET_WALL, spec.coupon_h)
    # Outer grip chamfers BEFORE the thread boolean (fillet/chamfer → cut).
    body = body.edges().chamfer(0.6)
    return body.cut(socket_cutter(spec, spec.coupon_h, over_hi=_END_OVER,
                                  turns=spec.coupon_turns), clean=False)


def probe_thread_band(wp, r, z0, z1, label="thread", min_transitions=3):
    """Crest solid/void probe (the ONLY reliable thread-failure detector).

    Marches up Z at radius r through the thread band [z0, z1]: a healthy
    thread alternates solid (#) and void (.); a silently-failed one is all
    '#' or all '.'. Raises RuntimeError on a bad pattern. Works for any
    thread — the custom socket and cadkit.threads cuts alike.

    Probes at θ=90° and θ=270°, NEVER θ=0: the helix seam (start/end profile
    faces) lies exactly in the y=0 plane, and the classifier reports those
    boundary faces as not-inside — a healthy thread reads broken there.
    """
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.TopAbs import TopAbs_State
    from OCP.gp import gp_Pnt

    shape = wp.val().wrapped
    n = 60
    for theta_deg in (90.0, 270.0):
        th = math.radians(theta_deg)
        x, y = r * math.cos(th), r * math.sin(th)
        pat = []
        for i in range(n + 1):
            z = z0 + (z1 - z0) * i / n
            c = BRepClass3d_SolidClassifier(shape, gp_Pnt(x, y, z), 1e-6)
            pat.append("#" if c.State() == TopAbs_State.TopAbs_IN else ".")
        pattern = "".join(pat)
        transitions = sum(1 for a, b in zip(pattern, pattern[1:]) if a != b)
        print(f"[probe {label}] theta={theta_deg:.0f} r={r:.2f}  {pattern}")
        if "#" not in pattern or "." not in pattern or transitions < min_transitions:
            raise RuntimeError(
                f"{label}: thread probe failed at theta={theta_deg:.0f} "
                f"({transitions} transitions) — the helix boolean silently "
                f"no-oped or wiped; see THREADS_README.md")


def probe_socket_thread(wp, spec, turns=None, label=None):
    """Probe the bottle-socket thread band of a part built on socket_cutter()."""
    if turns is None:
        turns = spec.socket_turns
    probe_thread_band(
        wp,
        r=spec.ridge_tip_d / 2.0 + 0.15,
        z0=spec.entry_lead + 0.1,
        z1=spec.entry_lead + turns * spec.pitch - 0.1,
        label=label or f"{spec.name} socket")
