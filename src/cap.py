"""The cap — quarter-turn onto the nozzle collar; flat mouth rim lands on the
nozzle's flat shoulder while the tip seals into a 45° pocket.

Interior, mouth-up (z=0 at the mouth, = nozzle z NOZZLE_SHOULDER_Z seated):
  nut     female 4-start quarter-turn thread (src/quick_thread.py cutter at
          NOMINAL Ø13/Ø11 — clearance lives on the male collar);
  neck    45° narrowing from the thread bore to the cone cavity;
  cavity  taper hugging the 50 mm dispensing cone at CAP_CONE_CLR per side;
  pocket  45° cone the nozzle's Ø3 tip rim wedges into, CAP_SEAL_PRELOAD
          (0.15) past nominal — small enough that the plastic gives and the
          mouth rim still closes flat on the shoulder. Torque loads both.

All down-facing interior surfaces are ≥45°. Ribbed outside for grip.
PRINT: mouth DOWN, axis vertical, no supports.
"""

from .dimensions import (
    CAP_CONE_CLR,
    CAP_NUT_H,
    CAP_OD,
    CAP_RIB_N,
    CAP_SEAL_PRELOAD,
    CAP_THREAD_MAJOR_D,
    CAP_TOP_FLAT_D,
    GRIP_RIB_Z0,
    NOZZLE_CONE_BASE_D,
    NOZZLE_CONE_Z0,
    NOZZLE_SHOULDER_Z,
    NOZZLE_TIP_OD,
    NOZZLE_TIP_Z,
)
from .grip import add_grip_ribs
from .quick_thread import quick_nut_cutter
from .thread_socket import _cone, _cyl

# ── Interior stack (cap coords: nozzle z minus NOZZLE_SHOULDER_Z) ────────────
NUT_Z0 = -0.5                                          # cutter overshoots the mouth
NECK_Z0 = NUT_Z0 + CAP_NUT_H + 0.5                     # 6.0 — top of the nut band
CAVITY_D0 = NOZZLE_CONE_BASE_D + 2 * CAP_CONE_CLR      # 11.0 cavity over the cone base
NECK_H = (CAP_THREAD_MAJOR_D - CAVITY_D0) / 2.0        # 1.0 — 45° neck-down
CAVITY_Z0 = NECK_Z0 + NECK_H                           # 7.0

TIP_Z = NOZZLE_TIP_Z - NOZZLE_SHOULDER_Z               # 35.0 tip plane at seat
POCKET_D0 = NOZZLE_TIP_OD + 1.0                        # 4.0 pocket base Ø
POCKET_TIP_D = 0.8                                     # truncated pocket apex
# Tip rim (Ø NOZZLE_TIP_OD) meets the 45° pocket half-way up; place that
# contact circle CAP_SEAL_PRELOAD below the seated tip plane.
POCKET_Z0 = TIP_Z - CAP_SEAL_PRELOAD - (POCKET_D0 - NOZZLE_TIP_OD) / 2.0   # 34.35
POCKET_H = (POCKET_D0 - POCKET_TIP_D) / 2.0            # 1.6 — 45° cone
POCKET_TOP_Z = POCKET_Z0 + POCKET_H                    # 35.95 interior ceiling

# ── Exterior ─────────────────────────────────────────────────────────────────
SHELL_CYL_H = 33.0                                     # cylinder, then 45° cone
CAP_CONE_H = (CAP_OD - CAP_TOP_FLAT_D) / 2.0           # 6.5
CAP_TOTAL_H = SHELL_CYL_H + CAP_CONE_H                 # 39.5
assert CAP_TOTAL_H - POCKET_TOP_Z >= 1.0, "roof too thin above the seal pocket"

# The cavity taper must clear the dispensing cone all the way up.
_cone_d_at = lambda zc: (NOZZLE_CONE_BASE_D
                         - (NOZZLE_CONE_BASE_D - NOZZLE_TIP_OD)
                         * (zc - (NOZZLE_CONE_Z0 - NOZZLE_SHOULDER_Z))
                         / (NOZZLE_TIP_Z - NOZZLE_CONE_Z0))
_cavity_d_at = lambda zc: (CAVITY_D0
                           - (CAVITY_D0 - POCKET_D0) * (zc - CAVITY_Z0)
                           / (POCKET_Z0 - CAVITY_Z0))
for _zc in (CAVITY_Z0, 15.0, 25.0, POCKET_Z0):
    assert _cavity_d_at(_zc) > _cone_d_at(_zc) + 0.5, \
        f"cap cavity pinches the dispensing cone at z={_zc}"


def build_cap():
    body = _cyl(CAP_OD, SHELL_CYL_H)
    body = body.union(_cone(CAP_OD, CAP_TOP_FLAT_D, CAP_CONE_H, SHELL_CYL_H))
    body = add_grip_ribs(body, CAP_OD, CAP_RIB_N,
                         GRIP_RIB_Z0, SHELL_CYL_H - GRIP_RIB_Z0)
    # Mouth-edge chamfer while smooth (chamfer → cut, never after).
    body = body.edges("<Z").chamfer(0.6)

    # Smooth interior first: neck-down, cone cavity, seal pocket.
    body = body.cut(_cone(CAP_THREAD_MAJOR_D, CAVITY_D0, NECK_H, NECK_Z0))
    body = body.cut(_cone(CAVITY_D0, POCKET_D0, POCKET_Z0 - CAVITY_Z0, CAVITY_Z0))
    body = body.cut(_cone(POCKET_D0, POCKET_TIP_D, POCKET_H, POCKET_Z0))

    # Nut thread LAST: the quarter-turn cutter at nominal size, overshot past
    # the mouth; its entry bevel gives the thread lead-in chamfer.
    nut = quick_nut_cutter(CAP_NUT_H + 0.5, z=NUT_Z0)
    return body.cut(nut, clean=False)
