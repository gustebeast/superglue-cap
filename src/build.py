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

from .dimensions import COUNTER_Z
from .thread_socket import build_socket_coupon, probe_socket_thread

# Anchor every output to the project folder, regardless of launch cwd.
OUT = pathlib.Path(__file__).resolve().parent.parent

# ── Palette (dark-viewer friendly; black is reserved for TPU) ────────────────
COLOR = {
    "socket_coupon": "#6B8AAB",   # slate blue — test piece, not a product part
    "build_counter": "#F0A878",   # salmon accent
}

socket_coupon = build_socket_coupon()
# A silent OCCT helix failure looks like a clean part — always probe.
probe_socket_thread(socket_coupon, "socket_coupon")

# Map of part name → (workplane, output filename, optional note).
PARTS = {
    "socket_coupon": (socket_coupon, "test_bottle_socket.step",
                      "thread-fit coupon — print mouth (chamfered end) DOWN, "
                      "axis vertical, no supports; must spin onto the bottle"),
}


def _export(name):
    obj, path, note = PARTS[name]
    export_step(obj, str(OUT / path))
    suffix = f"  ({note})" if note else ""
    print(f"Wrote {path}{suffix}")


def collect_components():
    """Placed parts at as-built positions, for tools/check_overlaps.py."""
    return [("socket_coupon", socket_coupon)]


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
        .add(socket_coupon, name="socket_coupon",
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
