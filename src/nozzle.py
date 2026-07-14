"""The nozzle — screws onto the bottle, dispenses through a standard cone.

Bottom-up: ribbed threaded skirt (the print-validated bottle socket) running
up to a FLAT annular shoulder — the cap's flat mouth rim lands on it for a
clean flat contact — then the male collar for the cap (cadkit.threads
cut_thread — the print-proven Ø13/Ø11 pitch-4 profile, shrunk CAP_THREAD_CLR
for fit), then the dispensing cone (Ø9 → Ø4). Inside, the glue channel
tapers from the Ø5 throat to a Ø0.8 orifice at the tip.

Boolean order (THREADS_README rules): the whole exterior is built SMOOTH
first (ribs included), the plain internal cone is cut while everything is
still cheap, and the two thread cuts come LAST (collar valleys, then the
socket cutter — their regions don't overlap, so neither no-ops the other).
The collar valleys run out downward as a shallow helical notch in the
shoulder's inner rim (r ≤ 6.5) — cosmetic, fully covered by the cap, and
inside the cap's Ø13 mouth ring so the flat contact area stays intact.

PRINT: mouth (chamfered end) DOWN on the bed, axis vertical, no supports.
The Ø0.8 orifice prints on the small side at a 0.4 nozzle; clear it with a
pin, or slice with the 0.2 nozzle for a crisp hole.
"""

from cadkit.threads import cut_thread

from .dimensions import (
    CAP_THREAD_PITCH,
    GRIP_RIB_Z0,
    NOZZLE_COLLAR_LEN,
    NOZZLE_COLLAR_MAJOR_D,
    NOZZLE_COLLAR_MINOR_D,
    NOZZLE_COLLAR_Z0,
    NOZZLE_CONE_BASE_D,
    NOZZLE_CONE_LEN,
    NOZZLE_CONE_Z0,
    NOZZLE_ORIFICE_D,
    NOZZLE_RIB_N,
    NOZZLE_SHOULDER_Z,
    NOZZLE_SKIRT_DEPTH,
    NOZZLE_SKIRT_OD,
    NOZZLE_SOCKET_TURNS,
    NOZZLE_THROAT_D,
    NOZZLE_THROAT_Z,
    NOZZLE_TIP_OD,
    NOZZLE_TIP_Z,
)
from .grip import add_grip_ribs
from .thread_socket import _cone, _cyl, socket_cutter


def build_nozzle():
    # Smooth blank: skirt up to the FLAT shoulder → collar (crest Ø) → cone.
    body = _cyl(NOZZLE_SKIRT_OD, NOZZLE_SHOULDER_Z)
    body = body.union(_cyl(NOZZLE_COLLAR_MAJOR_D, NOZZLE_COLLAR_LEN,
                           z=NOZZLE_COLLAR_Z0))
    body = body.union(_cone(NOZZLE_CONE_BASE_D, NOZZLE_TIP_OD,
                            NOZZLE_CONE_LEN, NOZZLE_CONE_Z0))
    body = add_grip_ribs(body, NOZZLE_SKIRT_OD, NOZZLE_RIB_N,
                         GRIP_RIB_Z0, NOZZLE_SHOULDER_Z - GRIP_RIB_Z0)
    # Mouth-edge chamfer while smooth (chamfer → cut, never after).
    body = body.edges("<Z").chamfer(0.6)

    # Internal dispensing cone — Ø5 throat to the Ø0.8 orifice — plus a short
    # orifice overshoot through the tip face (dodges the coincident face).
    body = body.cut(_cone(NOZZLE_THROAT_D, NOZZLE_ORIFICE_D,
                          NOZZLE_TIP_Z - NOZZLE_THROAT_Z, NOZZLE_THROAT_Z))
    body = body.cut(_cyl(NOZZLE_ORIFICE_D, 1.5, z=NOZZLE_TIP_Z - 0.5))

    # Threads LAST. Male collar valleys first (the blank is still cheap),
    # then the bottle socket (its ceiling cone tops out below the collar
    # valleys' radius, so the two cuts never overlap).
    body = cut_thread(body, minor_d=NOZZLE_COLLAR_MINOR_D,
                      major_d=NOZZLE_COLLAR_MAJOR_D, pitch=CAP_THREAD_PITCH,
                      length=NOZZLE_COLLAR_LEN, z=NOZZLE_COLLAR_Z0)
    body = body.cut(socket_cutter(NOZZLE_SKIRT_DEPTH, cone_ceiling=True,
                                  turns=NOZZLE_SOCKET_TURNS),
                    clean=False)
    return body
