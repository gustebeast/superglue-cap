"""Superglue cap — main build script.

Run from the repo root:
  py -3.12 -m src.build              # build all parts + assembly
  py -3.12 -m src.build --part NAME  # build only one part
  py -3.12 -m src.build --list       # list available part names

Writes one STEP per printed part plus a coloured assembly.step that the
shared FreeCAD viewer hub opens (floating 3-D build number included).

Current phase: THREAD-FIT COUPON ONLY — test_bottle_socket.step, an open
female-threaded tube that must spin onto the bottle's neck thread before the
real dispenser tip + cap get built around the same socket_cutter().
"""
import argparse
import pathlib
import sys

import cadquery as cq

from cadkit.cq_colors import color
from cadkit.freecad import show
from cadkit.step_export import export_step

from .cap import build_cap
from .dimensions import (
    CAP_EXPLODE_Z,
    CAP_SEAT_Z,
    CAP_THREAD_MINOR_D,
    COUNTER_Z,
    NOZZLE_COLLAR_LEN,
    NOZZLE_COLLAR_MINOR_D,
    NOZZLE_COLLAR_Z0,
    NOZZLE_SOCKET_TURNS,
)
from .nozzle import build_nozzle
from .thread_socket import (
    build_socket_coupon,
    probe_socket_thread,
    probe_thread_band,
)

# Anchor every output to the project folder, regardless of launch cwd.
OUT = pathlib.Path(__file__).resolve().parent.parent

# ── Palette (dark-viewer friendly; black is reserved for TPU) ────────────────
COLOR = {
    "nozzle":        "#E0973C",   # warm amber — dispensing piece
    "cap":           "#6FAE54",   # leaf green — sealing cap
    "socket_coupon": "#6B8AAB",   # slate blue — test piece, not a product part
    "build_counter": "#F0A878",   # salmon accent
}

# Coupon offset: off to the side of the nozzle in the assembly + overlap gate.
COUPON_DX = 40.0

nozzle = build_nozzle()
cap = build_cap()
socket_coupon = build_socket_coupon()
# A silent OCCT helix failure looks like a clean part — always probe every
# thread: the nozzle's bottle socket, its male collar, and the cap's nut.
probe_socket_thread(nozzle, "nozzle socket", turns=NOZZLE_SOCKET_TURNS)
# Quarter-turn bands are short (~1-2 ridge crossings per angle), so ≥2
# transitions is the gate — still catches all-solid / all-void no-ops.
probe_thread_band(nozzle, r=NOZZLE_COLLAR_MINOR_D / 2 + 0.15,
                  z0=NOZZLE_COLLAR_Z0 + 0.3,
                  z1=NOZZLE_COLLAR_Z0 + NOZZLE_COLLAR_LEN - 0.3,
                  label="nozzle collar", min_transitions=2)
probe_thread_band(cap, r=CAP_THREAD_MINOR_D / 2 + 0.15,
                  z0=0.5, z1=5.5, label="cap nut", min_transitions=2)
probe_socket_thread(socket_coupon, "socket_coupon")

# Map of part name → (workplane, output filename, optional note).
PARTS = {
    "nozzle": (nozzle, "nozzle.step",
               "screws onto the bottle; flat shoulder for the cap rim, "
               "dispensing cone to a Ø0.8 orifice — print mouth (chamfered "
               "end) DOWN, no supports; clear the orifice with a pin or "
               "slice at 0.2"),
    "cap": (cap, "cap.step",
            "screws onto the nozzle collar; mouth rim lands flat on the "
            "shoulder, tip seals into the 45° pocket — print mouth DOWN, "
            "no supports"),
    "socket_coupon": (socket_coupon, "test_bottle_socket.step",
                      "thread-fit coupon (validated: fits the bottle) — print "
                      "mouth DOWN, axis vertical, no supports"),
}


def _export(name):
    obj, path, note = PARTS[name]
    export_step(obj, str(OUT / path))
    suffix = f"  ({note})" if note else ""
    print(f"Wrote {path}{suffix}")


def collect_components():
    """Placed parts at as-built (SEATED) positions for tools/check_overlaps.py
    — the cap screwed home on the collar, where its designed contact with the
    nozzle (thread flanks + the preloaded tip seal) is a whitelisted pair."""
    return [("nozzle", nozzle),
            ("cap", cap.translate((0, 0, CAP_SEAT_Z))),
            ("socket_coupon", socket_coupon.translate((COUPON_DX, 0, 0)))]


# ── Build counter — floating 3-D number, bumped every full build ─────────────
_COUNTER = pathlib.Path(__file__).resolve().parent.parent / "tools" / "build_counter.txt"


def _bump_build_counter() -> int:
    try:
        n = int(_COUNTER.read_text().strip()) + 1
    except (OSError, ValueError):
        n = 1
    try:
        _COUNTER.parent.mkdir(parents=True, exist_ok=True)
        _COUNTER.write_text(f"{n}\n")
    except OSError:
        pass
    return n


def _build_counter_model(n: int):
    """Upright number floating above the parts. None if the text engine
    hiccups — a font failure must never break the build."""
    try:
        return cq.Workplane("XZ").center(0, COUNTER_Z).text(str(n), 10, 2)
    except Exception:
        return None


def _export_assembly():
    build_n = _bump_build_counter()
    assembly = (
        cq.Assembly(name="superglue_cap")
        .add(nozzle, name="nozzle", color=color(COLOR["nozzle"]))
        # Cap floated above the tip so the collar threads + pocket stay visible.
        .add(cap.translate((0, 0, CAP_EXPLODE_Z)), name="cap",
             color=color(COLOR["cap"]))
        # Validated fit coupon, kept off to the side per the coupon rule.
        .add(socket_coupon.translate((COUPON_DX, 0, 0)), name="socket_coupon",
             color=color(COLOR["socket_coupon"]))
    )
    counter = _build_counter_model(build_n)
    if counter is not None:
        assembly.add(counter, name="build_counter", color=color(COLOR["build_counter"]))
    assembly.save(str(OUT / "assembly.step"), mode="default")
    print(f"Wrote assembly.step  [build #{build_n}]", flush=True)
    show(str(OUT / "assembly.step"))


def main() -> None:
    p = argparse.ArgumentParser(prog="src.build", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--part", help="Build only this part (skips assembly).")
    p.add_argument("--list", action="store_true", help="List part names and exit.")
    args = p.parse_args()

    if args.list:
        print("assembly")
        for name in PARTS:
            print(name)
        return

    if args.part:
        if args.part == "assembly":
            _export_assembly()
            return
        if args.part not in PARTS:
            print(f"unknown part: {args.part!r}. Use --list to see options.", file=sys.stderr)
            sys.exit(2)
        _export(args.part)
        return

    for name in PARTS:
        _export(name)
    _export_assembly()


if __name__ == "__main__":
    main()
