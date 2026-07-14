"""Grip ribs — vertical half-round ridges around a cylindrical section.

Shared by the nozzle skirt and the cap shell. Union the ribs while the body
is still SMOOTH (before any thread boolean — rule 6 in THREADS_README.md).
"""

import math

import cadquery as cq

from .dimensions import GRIP_RIB_D


def add_grip_ribs(body, od, n, z0, h):
    """n ribs of Ø GRIP_RIB_D centred on the Ø od surface, spanning [z0, z0+h].
    One union: all ribs are extruded together off a polar point set. Each
    rib's bottom edge gets a 45° chamfer — a flat rib underside is an
    unsupported overhang shelf; the chamfer makes it self-supporting (only a
    0.1 mm flat ring remains, below one extrusion width)."""
    r = od / 2.0
    pts = [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n))
           for i in range(n)]
    ribs = (cq.Workplane("XY").workplane(offset=z0)
            .pushPoints(pts).circle(GRIP_RIB_D / 2.0).extrude(h))
    ribs = ribs.edges("<Z").chamfer(0.5)
    return body.union(ribs)
