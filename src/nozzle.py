"""The nozzle — screws onto the bottle, dispenses through a standard glue cone.

Bottom-up: threaded skirt (the print-validated bottle socket, full-wall
threads), 45° shoulder, male collar for the cap (cadkit.threads cut_thread —
the print-proven Ø13/Ø11 pitch-4 profile, shrunk CAP_THREAD_CLR for fit),
then the dispensing cone with a Ø2 glue channel to the tip.

Boolean order (THREADS_README rules): the whole exterior is built SMOOTH
first, the plain glue channel is cut while everything is still cheap, and the
two thread cuts come LAST (collar valleys, then the socket cutter — their
regions don't overlap, so neither no-ops the other).

PRINT: mouth (chamfered end) DOWN on the bed, axis vertical, no supports —
the cone is up-facing, the channel is a vertical bore.
"""

from cadkit.threads import cut_thread

from .dimensions import (
    CAP_THREAD_PITCH,
    NOZZLE_CHANNEL_D,
    NOZZLE_COLLAR_LEN,
    NOZZLE_COLLAR_MAJOR_D,
    NOZZLE_COLLAR_MINOR_D,
    NOZZLE_COLLAR_Z0,
    NOZZLE_CONE_BASE_D,
    NOZZLE_CONE_LEN,
    NOZZLE_CONE_Z0,
    NOZZLE_SKIRT_DEPTH,
    NOZZLE_SKIRT_OD,
    NOZZLE_SOCKET_TURNS,
    NOZZLE_TIP_OD,
    NOZZLE_TIP_Z,
)
from .thread_socket import _cone, _cyl, socket_cutter


def build_nozzle():
    # Smooth blank: skirt → 45° shoulder → collar (crest Ø) → dispensing cone.
    body = _cyl(NOZZLE_SKIRT_OD, NOZZLE_SKIRT_DEPTH)
    body = body.union(_cone(NOZZLE_SKIRT_OD, NOZZLE_COLLAR_MAJOR_D,
                            NOZZLE_COLLAR_Z0 - NOZZLE_SKIRT_DEPTH,
                            NOZZLE_SKIRT_DEPTH))
    body = body.union(_cyl(NOZZLE_COLLAR_MAJOR_D, NOZZLE_COLLAR_LEN,
                           z=NOZZLE_COLLAR_Z0))
    body = body.union(_cone(NOZZLE_CONE_BASE_D, NOZZLE_TIP_OD,
                            NOZZLE_CONE_LEN, NOZZLE_CONE_Z0))
    # Mouth-edge chamfer while smooth (chamfer → cut, never after).
    body = body.edges("<Z").chamfer(0.6)

    # Glue channel — a plain bore from inside the future socket cavity out
    # through the tip (overshoot both ends; it only crosses smooth faces).
    body = body.cut(_cyl(NOZZLE_CHANNEL_D, NOZZLE_TIP_Z - 8.0 + 1.0, z=8.0))

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
