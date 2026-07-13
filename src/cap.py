"""The cap — screws onto the nozzle's collar and seals flat against the tip.

Interior, mouth-up (z=0 at the mouth, = nozzle z NOZZLE_COLLAR_Z0 seated):
  nut     female Ø13/Ø11 pitch-4 thread — cadkit.threads threaded_rod as the
          nut cutter at NOMINAL size (clearance lives on the male collar);
  neck    45° narrowing from the thread bore to the barrel cavity;
  cavity  snug cylinder around the straight barrel (CAP_BARREL_CLR per side);
  ceiling FLAT, placed CAP_SEAL_PRELOAD short of where the barrel's flat tip
          face lands at nominal seat — screwing tight presses the two flats
          together, a clean flat-on-flat seal loaded by the thread torque.

The Ø8.6 flat ceiling prints as a small bridge (fine at this span); every
other down-facing interior surface is ≥45°. Ribbed outside for grip.
PRINT: mouth DOWN, axis vertical, no supports.
"""

from cadkit.threads import threaded_rod

from .dimensions import (
    CAP_BARREL_CLR,
    CAP_OD,
    CAP_RIB_N,
    CAP_SEAL_PRELOAD,
    CAP_THREAD_MAJOR_D,
    CAP_THREAD_MINOR_D,
    CAP_THREAD_PITCH,
    CAP_THREAD_TURNS,
    CAP_TOP_FLAT_D,
    GRIP_RIB_Z0,
    NOZZLE_BARREL_OD,
    NOZZLE_COLLAR_Z0,
    NOZZLE_TIP_Z,
)
from .grip import add_grip_ribs
from .thread_socket import _cone, _cyl

# ── Interior stack (cap coords: nozzle z minus NOZZLE_COLLAR_Z0) ─────────────
NUT_H = CAP_THREAD_TURNS * CAP_THREAD_PITCH            # 8.0 thread section
NUT_Z0 = -0.5                                          # rod overshoots the mouth
NECK_Z0 = NUT_Z0 + NUT_H                               # 7.5 — top of the nut cutter
CAVITY_D = NOZZLE_BARREL_OD + 2 * CAP_BARREL_CLR       # 8.6 around the barrel
NECK_H = (CAP_THREAD_MAJOR_D - CAVITY_D) / 2.0         # 2.2 — 45° neck-down
CAVITY_Z0 = NECK_Z0 + NECK_H                           # 9.7

TIP_Z = NOZZLE_TIP_Z - NOZZLE_COLLAR_Z0                # 21.0 tip plane at seat
CEILING_Z = TIP_Z - CAP_SEAL_PRELOAD                   # 20.7 flat sealing ceiling

# ── Exterior ─────────────────────────────────────────────────────────────────
SHELL_CYL_H = 18.0                                     # cylinder, then 45° cone
CAP_CONE_H = (CAP_OD - CAP_TOP_FLAT_D) / 2.0           # 6.5
CAP_TOTAL_H = SHELL_CYL_H + CAP_CONE_H                 # 24.5
assert CAP_TOTAL_H - CEILING_Z >= 1.5, "roof too thin above the sealing ceiling"
# Wall at the ceiling corner: the 45° exterior cone must still be clear of
# the cavity radius there.
assert (CAP_OD / 2 - (CEILING_Z - SHELL_CYL_H)) - CAVITY_D / 2 >= 1.5, \
    "shell too thin where the ceiling meets the top cone"
# The barrel must slide through the nut's Ø11 ridge tips.
assert NOZZLE_BARREL_OD <= CAP_THREAD_MINOR_D - 0.6, "barrel fouls the nut ridges"


def build_cap():
    body = _cyl(CAP_OD, SHELL_CYL_H)
    body = body.union(_cone(CAP_OD, CAP_TOP_FLAT_D, CAP_CONE_H, SHELL_CYL_H))
    body = add_grip_ribs(body, CAP_OD, CAP_RIB_N,
                         GRIP_RIB_Z0, SHELL_CYL_H - GRIP_RIB_Z0)
    # Mouth-edge chamfer while smooth (chamfer → cut, never after).
    body = body.edges("<Z").chamfer(0.6)

    # Smooth interior first: 45° neck-down, then the barrel cavity — its flat
    # top face IS the sealing ceiling.
    body = body.cut(_cone(CAP_THREAD_MAJOR_D, CAVITY_D, NECK_H, NECK_Z0))
    body = body.cut(_cyl(CAVITY_D, CEILING_Z - CAVITY_Z0, z=CAVITY_Z0))

    # Nut thread LAST: the library rod at nominal size, overshot past the
    # mouth; its baked-in end bevels give the thread entry chamfer.
    nut = threaded_rod(minor_d=CAP_THREAD_MINOR_D, major_d=CAP_THREAD_MAJOR_D,
                       pitch=CAP_THREAD_PITCH, length=NUT_H, z=NUT_Z0)
    return body.cut(nut, clean=False)
