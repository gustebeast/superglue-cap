"""The cap — solid conical roof over the print-validated socket thread.

Silhouette: Ø CAP_OD cylinder for the CAP_SOCKET_DEPTH of vertical wall, then
a 45° cone truncated to a small top flat. Interior: the shared socket_cutter()
(the exact geometry the fit coupon validated) with its cone_ceiling, so every
down-facing surface — thread undersides, ceiling — is 45°.

PRINT: mouth (chamfered end) DOWN on the bed, axis vertical, no supports.
"""

import cadquery as cq

from .dimensions import (
    CAP_OD,
    CAP_SOCKET_DEPTH,
    CAP_SOCKET_TURNS,
    CAP_TOP_FLAT_D,
    SOCKET_BORE_D,
)
from .thread_socket import _cone, _cyl, socket_cutter

# Exterior 45° cone: base Ø CAP_OD at the top of the cylindrical wall, rising
# 1:1 to the truncation flat.
CAP_CONE_H = (CAP_OD - CAP_TOP_FLAT_D) / 2.0        # 8.75
CAP_TOTAL_H = CAP_SOCKET_DEPTH + CAP_CONE_H         # 20.25
# Interior ceiling apex (bore cone, 45° from Ø15.3) — must stay under the
# exterior with solid margin at the centreline.
_CEILING_APEX_Z = CAP_SOCKET_DEPTH + (SOCKET_BORE_D - 0.2) / 2.0   # 19.05
assert CAP_TOTAL_H - _CEILING_APEX_Z >= 1.0, "roof too thin at the apex"


def build_cap():
    body = _cyl(CAP_OD, CAP_SOCKET_DEPTH)
    body = body.union(_cone(CAP_OD, CAP_TOP_FLAT_D, CAP_CONE_H, CAP_SOCKET_DEPTH))
    # Mouth-edge chamfer BEFORE the thread boolean (chamfer → cut, never after).
    body = body.edges("<Z").chamfer(0.6)
    return body.cut(socket_cutter(CAP_SOCKET_DEPTH, cone_ceiling=True,
                                  turns=CAP_SOCKET_TURNS),
                    clean=False)
