"""The cap — a HALF TURN onto the nozzle collar; a conical SHELL that
follows the dispensing cone it caps at CAP_WALL thickness. ONE cap fits
every bottle variant: it lives entirely above the flat shoulder, and the
dispenser stack there is identical for all of them (cap coords are relative
to the shoulder plane, where its mouth seats).

Exterior (one revolved profile, mouth-up): flat mouth face → thread BOSS
(Ø16.2 cylinder over the nut band — threads need wall, so the boss grows
outward from the shell) → 45° taper onto the SHELL CONE (= cavity + CAP_WALL,
tracking the nozzle cone all the way up) → a top cone closing over the seal
pocket with CAP_WALL of solid at the centreline. Grip ribs sit on the boss
only — the shell cone stays clean.

Interior (unchanged from the solid version): nut thread (nominal Ø13/Ø11
quarter-turn cutter — clearance lives on the male collar), 45° neck-down,
cavity hugging the cone at CAP_CONE_CLR per side, then the 45° seal pocket
(now with a small Ø1.4 flat ceiling — a trivial bridge — instead of a needle
apex, buying roof margin). CAP_SEAL_PRELOAD (0.15) keeps the tip pressed
into the pocket while the mouth rim closes flat on the shoulder.

All down-facing interior surfaces are ≥45°; every exterior surface faces up.
PRINT: mouth DOWN, axis vertical, no supports.
"""

import cadquery as cq

from cadkit.threads import multistart_rod

from .dimensions import (
    CAP_BOSS_OD,
    CAP_CONE_CLR,
    CAP_NUT_H,
    CAP_RIB_N,
    CAP_SEAL_PRELOAD,
    CAP_THREAD_MAJOR_D,
    CAP_THREAD_MINOR_D,
    CAP_THREAD_SPACING,
    CAP_THREAD_STARTS,
    CAP_TOP_FLAT_D,
    CAP_WALL,
    DISPENSER_H,
    GRIP_RIB_Z0,
    NOZZLE_COLLAR_LEN,
    NOZZLE_CONE_BASE_D,
    NOZZLE_TIP_OD,
)
from .grip import add_grip_ribs
from .thread_socket import _cone

# ── Interior stack (cap coords: nozzle z minus the spec's shoulder_z) ────────
NUT_Z0 = -0.5                                          # cutter overshoots the mouth
NECK_Z0 = NUT_Z0 + CAP_NUT_H + 0.5                     # 6.0 — top of the nut band
CAVITY_D0 = NOZZLE_CONE_BASE_D + 2 * CAP_CONE_CLR      # 11.0 cavity over the cone base
NECK_H = (CAP_THREAD_MAJOR_D - CAVITY_D0) / 2.0        # 1.0 — 45° neck-down
CAVITY_Z0 = NECK_Z0 + NECK_H                           # 7.0

TIP_Z = DISPENSER_H                                    # 34.5 tip plane at seat
POCKET_D0 = NOZZLE_TIP_OD + 1.9                        # 4.3 pocket base Ø — wide
                                                       # enough that the cavity
                                                       # keeps clearing the cone
                                                       # right up to the pocket
POCKET_TIP_D = 1.4                                     # flat pocket ceiling (small bridge)
# Tip rim (Ø NOZZLE_TIP_OD) meets the 45° pocket half-way up; place that
# contact circle CAP_SEAL_PRELOAD below the seated tip plane.
POCKET_Z0 = TIP_Z - CAP_SEAL_PRELOAD - (POCKET_D0 - NOZZLE_TIP_OD) / 2.0   # 33.4
POCKET_H = (POCKET_D0 - POCKET_TIP_D) / 2.0            # 1.45 — 45° cone
POCKET_TOP_Z = POCKET_Z0 + POCKET_H                    # 34.85 interior ceiling

# ── Exterior shell profile ───────────────────────────────────────────────────
BOSS_R = CAP_BOSS_OD / 2.0                             # 8.1
BOSS_TOP = CAVITY_Z0 + 1.0                             # 8.0 — boss covers nut + neck
TOP_Z = POCKET_TOP_Z + CAP_WALL                        # 36.45 — CAP_WALL over the pocket
TOP_FLAT_R = CAP_TOP_FLAT_D / 2.0                      # 1.0

# Shell cone = cavity line + CAP_WALL: r(z) = _C − _M·z. The boss blends onto
# it with a 45° up-facing taper; solve the two lines for the join point.
_M = ((CAVITY_D0 - POCKET_D0) / 2.0) / (POCKET_Z0 - CAVITY_Z0)      # 0.1269
_C = CAVITY_D0 / 2.0 + _M * CAVITY_Z0 + CAP_WALL                    # 7.988
JOIN_Z = (BOSS_R + BOSS_TOP - _C) / (1.0 - _M)                      # 9.29
JOIN_R = BOSS_R - (JOIN_Z - BOSS_TOP)                               # 6.81
SHELL_END_R = _C - _M * POCKET_Z0                                   # 3.75 at the pocket base
assert BOSS_TOP < JOIN_Z < POCKET_Z0, "boss taper misses the shell cone"
assert SHELL_END_R > TOP_FLAT_R, "top cone inverted"

# The cavity taper must clear the dispensing cone all the way up.
_cone_d_at = lambda zc: (NOZZLE_CONE_BASE_D
                         - (NOZZLE_CONE_BASE_D - NOZZLE_TIP_OD)
                         * (zc - NOZZLE_COLLAR_LEN)
                         / (DISPENSER_H - NOZZLE_COLLAR_LEN))
_cavity_d_at = lambda zc: (CAVITY_D0
                           - (CAVITY_D0 - POCKET_D0) * (zc - CAVITY_Z0)
                           / (POCKET_Z0 - CAVITY_Z0))
for _zc in (CAVITY_Z0, 15.0, 25.0, POCKET_Z0):
    assert _cavity_d_at(_zc) > _cone_d_at(_zc) + 0.5, \
        f"cap cavity pinches the dispensing cone at z={_zc}"


def build_cap():
    # One revolved profile: FLAT mouth face (bed adhesion — no bottom
    # chamfer; elephant's foot is the slicer's job), boss, 45° blend, shell
    # cone tracking the cavity, top cone to a small flat. (x = radius, y = z.)
    prof = [(BOSS_R, 0.0), (BOSS_R, BOSS_TOP),
            (JOIN_R, JOIN_Z), (SHELL_END_R, POCKET_Z0),
            (TOP_FLAT_R, TOP_Z), (0.0, TOP_Z), (0.0, 0.0)]
    body = (cq.Workplane("XZ").polyline(prof).close()
            .revolve(360.0, (0, 0, 0), (0, 1, 0)))
    body = add_grip_ribs(body, CAP_BOSS_OD, CAP_RIB_N,
                         GRIP_RIB_Z0, BOSS_TOP - GRIP_RIB_Z0)

    # Smooth interior: neck-down, cone cavity, seal pocket.
    body = body.cut(_cone(CAP_THREAD_MAJOR_D, CAVITY_D0, NECK_H, NECK_Z0))
    body = body.cut(_cone(CAVITY_D0, POCKET_D0, POCKET_Z0 - CAVITY_Z0, CAVITY_Z0))
    body = body.cut(_cone(POCKET_D0, POCKET_TIP_D, POCKET_H, POCKET_Z0))

    # Nut thread LAST: the half-turn multistart cutter (cadkit.threads) at
    # nominal size, overshot past the mouth; its entry bevel = lead-in chamfer.
    nut = multistart_rod(CAP_THREAD_MINOR_D, CAP_THREAD_MAJOR_D,
                         CAP_THREAD_SPACING, CAP_THREAD_STARTS,
                         CAP_NUT_H + 0.5, z=NUT_Z0)
    return body.cut(nut, clean=False)
