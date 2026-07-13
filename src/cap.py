"""The cap — screws onto the nozzle's collar and seals the dispensing tip.

Interior, mouth-up (z=0 at the mouth, = nozzle z NOZZLE_COLLAR_Z0 seated):
  nut     female Ø13/Ø11 pitch-4 thread — cadkit.threads threaded_rod as the
          nut cutter at NOMINAL size (clearance lives on the male collar);
  neck    45° narrowing from the thread bore to the cone cavity;
  cavity  taper hugging the dispensing cone at CAP_CONE_CLR per side;
  pocket  45° cone the nozzle's Ø4 tip rim wedges into, placed
          CAP_SEAL_PRELOAD short of nominal seat — screwing tight loads this
          line seal, not a shoulder.

All down-facing interior surfaces are ≥45°; the nut bore is the library's
self-supporting profile. PRINT: mouth DOWN, axis vertical, no supports.
"""

from cadkit.threads import threaded_rod

from .dimensions import (
    CAP_CONE_CLR,
    CAP_OD,
    CAP_SEAL_PRELOAD,
    CAP_THREAD_MAJOR_D,
    CAP_THREAD_MINOR_D,
    CAP_THREAD_PITCH,
    CAP_THREAD_TURNS,
    CAP_TOP_FLAT_D,
    NOZZLE_COLLAR_Z0,
    NOZZLE_CONE_BASE_D,
    NOZZLE_CONE_LEN,
    NOZZLE_CONE_Z0,
    NOZZLE_TIP_OD,
    NOZZLE_TIP_Z,
)
from .thread_socket import _cone, _cyl

# ── Interior stack (cap coords: nozzle z minus NOZZLE_COLLAR_Z0) ─────────────
NUT_H = CAP_THREAD_TURNS * CAP_THREAD_PITCH            # 8.0 thread section
NUT_Z0 = -0.5                                          # rod overshoots the mouth
NECK_Z0 = NUT_Z0 + NUT_H                               # 7.5 — top of the nut cutter
CAVITY_D0 = NOZZLE_CONE_BASE_D + 2 * CAP_CONE_CLR      # 10.0 cavity over the cone base
NECK_H = (CAP_THREAD_MAJOR_D - CAVITY_D0) / 2.0        # 1.5 — 45° neck-down
CAVITY_Z0 = NECK_Z0 + NECK_H                           # 9.0

TIP_Z = NOZZLE_TIP_Z - NOZZLE_COLLAR_Z0                # 21.0 tip plane at seat
POCKET_D0 = NOZZLE_TIP_OD + 1.0                        # 5.0 pocket base Ø
POCKET_TIP_D = 0.8                                     # truncated pocket apex
# Tip rim (Ø NOZZLE_TIP_OD) meets the 45° pocket half-way up; place that
# contact circle CAP_SEAL_PRELOAD below the seated tip plane.
POCKET_Z0 = TIP_Z - CAP_SEAL_PRELOAD - (POCKET_D0 - NOZZLE_TIP_OD) / 2.0   # 20.2
POCKET_H = (POCKET_D0 - POCKET_TIP_D) / 2.0            # 2.1 — 45° cone
POCKET_TOP_Z = POCKET_Z0 + POCKET_H                    # 22.3 interior ceiling

# ── Exterior ─────────────────────────────────────────────────────────────────
SHELL_CYL_H = 19.0                                     # cylinder, then 45° cone
CAP_CONE_H = (CAP_OD - CAP_TOP_FLAT_D) / 2.0           # 6.5
CAP_TOTAL_H = SHELL_CYL_H + CAP_CONE_H                 # 25.5
assert CAP_TOTAL_H - POCKET_TOP_Z >= 1.0, "roof too thin above the seal pocket"

# The cavity taper must clear the dispensing cone all the way up.
_cone_d_at = lambda zc: (NOZZLE_CONE_BASE_D
                         - (NOZZLE_CONE_BASE_D - NOZZLE_TIP_OD)
                         * (zc - (NOZZLE_CONE_Z0 - NOZZLE_COLLAR_Z0)) / NOZZLE_CONE_LEN)
_cavity_d_at = lambda zc: (CAVITY_D0
                           - (CAVITY_D0 - POCKET_D0) * (zc - CAVITY_Z0)
                           / (POCKET_Z0 - CAVITY_Z0))
for _zc in (CAVITY_Z0, 12.0, 16.0, POCKET_Z0):
    assert _cavity_d_at(_zc) > _cone_d_at(_zc) + 0.5, \
        f"cap cavity pinches the dispensing cone at z={_zc}"


def build_cap():
    body = _cyl(CAP_OD, SHELL_CYL_H)
    body = body.union(_cone(CAP_OD, CAP_TOP_FLAT_D, CAP_CONE_H, SHELL_CYL_H))
    # Mouth-edge chamfer while smooth (chamfer → cut, never after).
    body = body.edges("<Z").chamfer(0.6)

    # Smooth interior first: neck-down, cone cavity, seal pocket.
    body = body.cut(_cone(CAP_THREAD_MAJOR_D, CAVITY_D0, NECK_H, NECK_Z0))
    body = body.cut(_cone(CAVITY_D0, POCKET_D0, POCKET_Z0 - CAVITY_Z0, CAVITY_Z0))
    body = body.cut(_cone(POCKET_D0, POCKET_TIP_D, POCKET_H, POCKET_Z0))

    # Nut thread LAST: the library rod at nominal size, overshot past the
    # mouth; its baked-in end bevels give the thread entry chamfer.
    nut = threaded_rod(minor_d=CAP_THREAD_MINOR_D, major_d=CAP_THREAD_MAJOR_D,
                       pitch=CAP_THREAD_PITCH, length=NUT_H, z=NUT_Z0)
    return body.cut(nut, clean=False)
