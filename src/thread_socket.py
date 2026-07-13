"""Female bottle-neck socket thread — project-local ASYMMETRIC profile.

WHY NOT cadkit.threads: the bottle is a single-start pitch-2 × depth-1 thread,
and a symmetric 45° trapezoid can't exist there (see src/dimensions.py). This
module cuts a buttress-style female thread instead — ridge underside at 45°
(the only down-facing surface: self-supporting with the mouth on the bed),
ridge top at RIDGE_TOP_SLOPE_DEG from horizontal (up-facing: no constraint).

It still obeys every rule that cadkit/THREADS_README.md paid builds to learn:
  * the valley profile is a 4-POINT quad, swept with isFrenet;
  * the thread is CUT from a smooth crest-Ø blank, never grown as a ridge;
  * sweep height is WHOLE turns and ends INSIDE the blank;
  * one segment only (4 mm ≪ the ~100 mm single-sweep limit);
  * clean=False on every thread boolean, and no heal()/ShapeFix afterwards;
  * never trust the eye: probe_socket_thread() classifies solid/void up the
    ridge band and the build FAILS if the pattern doesn't alternate.

Both the fit coupon and the real cap cut their socket with the SAME
socket_cutter() — the coupon is the real geometry, per the coupon rule in
cadkit/AGENTS.md.
"""

import math

import cadquery as cq

from .dimensions import (
    BOTTLE_PITCH,
    BOTTLE_TURNS,
    COUPON_H,
    COUPON_OD,
    RIDGE_TIP_FLAT,
    RIDGE_TOP_SLOPE_DEG,
    SOCKET_BORE_D,
    SOCKET_ENTRY_LEAD,
    SOCKET_MOUTH_CHAMFER,
    SOCKET_RIDGE_TIP_D,
)

_OVERSHOOT = 0.25        # radial overshoot of the valley past the blank crest
_END_OVER = 0.5          # smooth-bore overshoot past the body faces (dodges
                         # coincident-face booleans, cuts only air)


def _cyl(d, h, z=0.0):
    return cq.Workplane("XY").workplane(offset=z).circle(d / 2.0).extrude(h)


def _cone(d_bottom, d_top, h, z):
    return (cq.Workplane("XY").workplane(offset=z).circle(d_bottom / 2.0)
            .workplane(offset=h).circle(d_top / 2.0).loft())


def _valley_sweep(z0, turns=BOTTLE_TURNS):
    """The helical valley cutter (ONE whole-turn-height segment), base at z0.

    Cut from the crest-Ø blank, the valley becomes the female RIDGE. Quad in
    the XZ plane, (radius, axial) coordinates:

        tip flat RIDGE_TIP_FLAT wide at r_tip;
        LOWER edge drops 1:1 outward   -> ridge underside at 45° (down-facing);
        UPPER edge rises tan(15°) outward -> ridge top (up-facing, no limit).
    """
    r_tip = SOCKET_RIDGE_TIP_D / 2.0
    r_os = SOCKET_BORE_D / 2.0 + _OVERSHOOT
    d_os = r_os - r_tip
    top_rise = math.tan(math.radians(RIDGE_TOP_SLOPE_DEG))
    f = RIDGE_TIP_FLAT

    width_at_os = f + d_os * (1.0 + top_rise)
    assert width_at_os < BOTTLE_PITCH, (
        f"valley width {width_at_os:.2f} ≥ pitch {BOTTLE_PITCH}: adjacent turns "
        f"would self-overlap into an invalid cutter (silent no-op)")

    gpts = [(r_tip, -f / 2.0),
            (r_os, -f / 2.0 - d_os),              # 45° underside flank
            (r_os, f / 2.0 + d_os * top_rise),    # 15° top flank
            (r_tip, f / 2.0)]

    h = math.ceil(turns - 1e-6) * BOTTLE_PITCH            # WHOLE turns
    assert h <= 72.0, "tile in segments past ~72mm (see thread_segments)"
    r_mid = (r_tip + SOCKET_BORE_D / 2.0) / 2.0
    sweep = (cq.Workplane("XZ").polyline(gpts).close()
             .sweep(cq.Workplane("XY").add(
                 cq.Wire.makeHelix(pitch=BOTTLE_PITCH, height=h, radius=r_mid)),
                 isFrenet=True))
    return sweep.translate((0, 0, z0))


def socket_cutter(total_len, over_hi=_END_OVER, cone_ceiling=False,
                  turns=BOTTLE_TURNS):
    """The complete socket cutter for a body whose mouth face is at z=0 and
    which extends up to z=total_len: flared mouth + smooth entry bore + the
    threaded band (`turns` WHOLE turns starting at SOCKET_ENTRY_LEAD).
    Subtract with clean=False.

    cone_ceiling=True makes a BLIND socket that closes as a 45° cone rising
    from the bore at z=total_len (apex at total_len + bore radius) — the
    self-supporting ceiling for a solid-roof cap printed mouth-down. over_hi
    is ignored in that case (the cone IS the top end).

    Built smooth-first (cyl + mouth cone + ceiling cone), thread cut LAST —
    booleans on the finished helix are the slow/fragile ones.
    """
    thread_top = SOCKET_ENTRY_LEAD + turns * BOTTLE_PITCH
    assert thread_top < total_len, "thread must end inside the socket"

    if cone_ceiling:
        over_hi = 0.0
    blank = _cyl(SOCKET_BORE_D, total_len + _END_OVER + over_hi, z=-_END_OVER)
    mouth_d = SOCKET_BORE_D + 2.0 * SOCKET_MOUTH_CHAMFER
    blank = (blank
             .union(_cyl(mouth_d, _END_OVER, z=-_END_OVER))
             .union(_cone(mouth_d, SOCKET_BORE_D, SOCKET_MOUTH_CHAMFER, 0.0)))
    if cone_ceiling:
        # 45° ceiling: Ø bore at total_len narrowing to a near-apex. A true
        # apex makes loft() unhappy; a Ø0.2 top face is below one extrusion
        # width, so it slices as a point anyway.
        blank = blank.union(_cone(SOCKET_BORE_D, 0.2,
                                  (SOCKET_BORE_D - 0.2) / 2.0, total_len))
    return blank.cut(_valley_sweep(SOCKET_ENTRY_LEAD, turns), clean=False)


def build_socket_coupon():
    """test_bottle_socket.step — open tube (no top), the real socket geometry.

    PRINT: mouth (chamfered end) DOWN on the bed, axis vertical, no supports.
    The profile is asymmetric, so orientation matters: printed the other way
    up, the 15° ridge tops become unprintable overhangs.
    """
    body = _cyl(COUPON_OD, COUPON_H)
    # Outer grip chamfers BEFORE the thread boolean (fillet/chamfer → cut).
    body = body.edges().chamfer(0.6)
    return body.cut(socket_cutter(COUPON_H, over_hi=_END_OVER), clean=False)


def probe_socket_thread(wp, label="socket", turns=BOTTLE_TURNS):
    """Crest solid/void probe (the ONLY reliable thread-failure detector).

    Marches up Z at a radius just outside the ridge tip: a healthy female
    thread alternates ridge (#) and groove (.); a silently-failed one is all
    '#' (no bore / wiped cutter) or all '.' (valley cut no-oped → smooth
    bore). Raises RuntimeError on a bad pattern.

    Probes at θ=90° and θ=270°, NEVER θ=0: the helix seam (start/end profile
    faces) lies exactly in the y=0 plane, and the classifier reports those
    boundary faces as not-inside — a healthy thread reads broken there.
    """
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.TopAbs import TopAbs_State
    from OCP.gp import gp_Pnt

    shape = wp.val().wrapped
    r = SOCKET_RIDGE_TIP_D / 2.0 + 0.15
    z0 = SOCKET_ENTRY_LEAD + 0.1
    z1 = SOCKET_ENTRY_LEAD + turns * BOTTLE_PITCH - 0.1
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
        if "#" not in pattern or "." not in pattern or transitions < 3:
            raise RuntimeError(
                f"{label}: thread probe failed at theta={theta_deg:.0f} "
                f"({transitions} transitions) — the helix boolean silently "
                f"no-oped or wiped; see THREADS_README.md")
