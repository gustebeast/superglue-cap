"""Quarter-turn thread — 4-start, 16 mm lead, between the nozzle collar and cap.

WHY NOT cadkit.threads directly: threaded_rod/cut_thread are single-start,
and a multi-start thread can't reuse thread_segments' quad (its flats derive
from the full pitch; at LEAD 16 the valleys would be 7 mm wide and adjacent
starts would erase each other). This module sweeps the SAME print-proven
cross-section as the Ø13/Ø11 pitch-4 thread — depth 1.0, 1.0 flats, 45°
flanks, ridges CAP_THREAD_SPACING (4 mm) apart — along 4 steeper helices.

THREADS_README rules kept: 4-point quads; sweeps are exactly ONE whole turn
(LEAD tall) each; different starts' valleys never overlap (3.6 mm wide at
the overshoot < 4 mm spacing); cut SEQUENTIALLY with clean=False, never
unioned; threads cut LAST on otherwise-finished smooth bodies; nothing gets
heal()ed afterwards. The build probes every thread band.
"""

import math

import cadquery as cq

from .dimensions import (
    CAP_THREAD_LEAD,
    CAP_THREAD_MAJOR_D,
    CAP_THREAD_MINOR_D,
    CAP_THREAD_SPACING,
    CAP_THREAD_STARTS,
    NOZZLE_COLLAR_MAJOR_D,
    NOZZLE_COLLAR_MINOR_D,
)
from .thread_socket import _cone, _cyl

_OVERSHOOT = 0.3


def _valley_sweeps(minor_d, major_d, z0):
    """One whole-turn (LEAD-tall) valley sweep per start, based at z0, phase
    360°·z0/LEAD so the pattern is position-independent. The quad is the
    pitch-4 profile: flats from the 4 mm ridge SPACING, not the 16 mm lead."""
    core_r = minor_d / 2.0
    crest_r = major_d / 2.0
    depth = crest_r - core_r
    flat = (CAP_THREAD_SPACING - 2.0 * depth) / 2.0          # 1.0
    assert flat >= 0.6, "flats too small — valleys would self-overlap"
    hw_root = flat / 2.0
    hw_out = flat / 2.0 + (depth + _OVERSHOOT)
    assert 2.0 * hw_out < CAP_THREAD_SPACING, \
        "adjacent starts' valleys overlap — invalid cutter (silent no-op)"
    gpts = [(core_r, -hw_root), (crest_r + _OVERSHOOT, -hw_out),
            (crest_r + _OVERSHOOT, hw_out), (core_r, hw_root)]
    r_mid = (core_r + crest_r) / 2.0
    base = (cq.Workplane("XZ").polyline(gpts).close()
            .sweep(cq.Workplane("XY").add(
                cq.Wire.makeHelix(pitch=CAP_THREAD_LEAD, height=CAP_THREAD_LEAD,
                                  radius=r_mid)), isFrenet=True))
    phase = 360.0 * z0 / CAP_THREAD_LEAD
    return [base.rotate((0, 0, 0), (0, 0, 1), phase + 360.0 * i / CAP_THREAD_STARTS)
            .translate((0, 0, z0))
            for i in range(CAP_THREAD_STARTS)]


def cut_male_quick_thread(body, z0):
    """Cut the 4 collar valleys into a finished-smooth nozzle body. Sweeps
    base at the collar root (below is the solid shoulder — starting lower
    would gouge it) and run out upward past the collar into air."""
    for seg in _valley_sweeps(NOZZLE_COLLAR_MINOR_D, NOZZLE_COLLAR_MAJOR_D, z0):
        body = body.cut(seg, clean=False)
    return body


def quick_nut_cutter(length, z=0.0):
    """Female nut cutter (nominal size): crest-Ø rod over [z, z+length] with
    the 4 valleys carved, plus a conical entry bevel at the bottom (mirrors
    threaded_rod's lead-in). Sweeps are based a spacing below the rod so the
    band is fully covered; outside the rod they cut air."""
    rod = _cyl(CAP_THREAD_MAJOR_D, length, z=z)
    for seg in _valley_sweeps(CAP_THREAD_MINOR_D, CAP_THREAD_MAJOR_D,
                              z - CAP_THREAD_SPACING):
        rod = rod.cut(seg, clean=False)
    core_r = CAP_THREAD_MINOR_D / 2.0
    run = 2.0
    bevel = CAP_THREAD_MAJOR_D / 2.0 + 1.0
    bot = (_cyl(2 * bevel, run, z=z)
           .cut(_cone(2 * core_r, 2 * bevel, run, z)))
    return rod.cut(bot, clean=False)
