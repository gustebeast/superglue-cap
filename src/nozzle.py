"""The nozzle — screws onto the bottle, dispenses through a ~35 mm cone.
Built per BottleSpec: the macbeath and loctite variants differ ONLY in the
skirt (socket bore/pitch/depth → skirt Ø and shoulder height); everything
above the flat shoulder is identical, so one cap fits every variant.

Bottom-up: ribbed threaded skirt (the spec's bottle socket) running up to a
FLAT annular shoulder — the cap's flat mouth rim lands on it for a clean
flat contact — then the HALF-TURN male collar (2-start, 8 mm lead,
cadkit.threads multistart), then the dispensing cone up to the tip.

Inside, above the socket: the 45° ceiling funnels to the shared Ø7.3 throat
exactly at the shoulder plane, and from there ONE continuous cone (~6°) runs
unbroken through the collar and the whole dispenser to the Ø0.8 orifice —
no mid-channel kink. (A single cone from the full socket bore is impossible:
it would be wider than the Ø12.4 collar around it.)

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

from cadkit.threads import cut_multistart_thread

from .dimensions import (
    CAP_THREAD_SPACING,
    CAP_THREAD_STARTS,
    GRIP_RIB_Z0,
    NOZZLE_COLLAR_LEN,
    NOZZLE_COLLAR_MAJOR_D,
    NOZZLE_COLLAR_MINOR_D,
    NOZZLE_CONE_BASE_D,
    NOZZLE_ORIFICE_D,
    NOZZLE_RIB_N,
    NOZZLE_THROAT_D,
    NOZZLE_TIP_OD,
)
from .grip import add_grip_ribs
from .thread_socket import _cone, _cyl, socket_cutter


def build_nozzle(spec):
    shoulder = spec.shoulder_z
    cone_z0 = shoulder + NOZZLE_COLLAR_LEN
    tip_z = spec.tip_z

    # Smooth blank: skirt up to the FLAT shoulder → collar (crest Ø) → cone.
    body = _cyl(spec.skirt_od, shoulder)
    body = body.union(_cyl(NOZZLE_COLLAR_MAJOR_D, NOZZLE_COLLAR_LEN, z=shoulder))
    body = body.union(_cone(NOZZLE_CONE_BASE_D, NOZZLE_TIP_OD,
                            tip_z - cone_z0, cone_z0))
    # Ribs run to the bed and the mouth face stays FLAT (no bottom chamfer)
    # — maximum first-layer area; elephant's foot is the slicer's job.
    body = add_grip_ribs(body, spec.skirt_od, NOZZLE_RIB_N,
                         GRIP_RIB_Z0, shoulder - GRIP_RIB_Z0)

    # The continuous internal cone — Ø7.3 throat at the shoulder plane to the
    # Ø0.8 orifice — plus a short orifice overshoot through the tip face
    # (dodges the coincident face). The socket ceiling cut below overlaps it
    # seamlessly: the 45° funnel is wider below the shoulder, this cone above.
    body = body.cut(_cone(NOZZLE_THROAT_D, NOZZLE_ORIFICE_D,
                          tip_z - shoulder, shoulder))
    body = body.cut(_cyl(NOZZLE_ORIFICE_D, 1.5, z=tip_z - 0.5))

    # Threads LAST. Half-turn collar valleys first (the blank is still
    # cheap), then the bottle socket (its ceiling cone tops out below the
    # collar valleys' radius, so the two cuts never overlap).
    body = cut_multistart_thread(body, NOZZLE_COLLAR_MINOR_D,
                                 NOZZLE_COLLAR_MAJOR_D, CAP_THREAD_SPACING,
                                 CAP_THREAD_STARTS, NOZZLE_COLLAR_LEN,
                                 z=shoulder)
    body = body.cut(socket_cutter(spec, spec.skirt_depth, cone_ceiling=True),
                    clean=False)
    return body
