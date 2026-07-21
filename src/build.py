"""Superglue cap — main build script.

Run from the repo root:
  py -3.12 -m src.build              # build all parts + assembly
  py -3.12 -m src.build --part NAME  # build only one part
  py -3.12 -m src.build --list       # list available part names

Writes one STEP per printed part plus a coloured assembly.step that the
shared FreeCAD viewer hub opens (floating 3-D build number included).

TWO bottle variants (see src/dimensions.py): nozzle_macbeath (socket
print-validated) and nozzle_loctite (print-fit pending — its coupon is
test_loctite_socket.step). ONE cap fits both: everything above the flat
shoulder is identical.
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
    BOTTLES,
    CAP_THREAD_MINOR_D,
    COUNTER_Z,
    MACBEATH,
    NOZZLE_COLLAR_LEN,
    NOZZLE_COLLAR_MINOR_D,
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
    "nozzle_macbeath": "#E0973C",   # warm amber — original bottle
    "nozzle_loctite":  "#C0574E",   # brick red — loctite bottle
    "cap":             "#6FAE54",   # leaf green — shared sealing cap
    "macbeath_coupon": "#6B8AAB",   # slate blue — test pieces
    "loctite_coupon":  "#8FA8C0",   # lighter slate
    "build_counter":   "#F0A878",   # salmon accent
}

# Assembly / overlap-gate layout (x offsets; cap seats on the macbeath nozzle
# for the gate, floats above it in the viewer).
X_LOCTITE = 48.0
X_COUPON_MAC = -40.0
X_COUPON_LOC = 92.0

nozzles = {b.name: build_nozzle(b) for b in BOTTLES}
cap = build_cap()
coupons = {b.name: build_socket_coupon(b) for b in BOTTLES}

# A silent OCCT helix failure looks like a clean part — always probe every
# thread: each nozzle's bottle socket + collar, the cap's nut, each coupon.
# Half-turn bands are short (~1-2 ridge crossings per angle), so ≥2
# transitions is the gate — still catches all-solid / all-void no-ops.
for _b in BOTTLES:
    probe_socket_thread(nozzles[_b.name], _b, label=f"{_b.name} nozzle socket")
    probe_thread_band(nozzles[_b.name], r=NOZZLE_COLLAR_MINOR_D / 2 + 0.15,
                      z0=_b.shoulder_z + 0.3,
                      z1=_b.shoulder_z + NOZZLE_COLLAR_LEN - 0.3,
                      label=f"{_b.name} collar", min_transitions=2)
    probe_socket_thread(coupons[_b.name], _b, turns=_b.coupon_turns,
                        label=f"{_b.name} coupon")
# The cap nut band is 6 mm against a 4 mm ridge period, so at some angles
# only a ridge EDGE lands in the window (1 transition). The '#'-and-'.'-
# both-present check still catches a no-op (smooth bore = all '.', wiped =
# all '#'), so 1 transition suffices.
probe_thread_band(cap, r=CAP_THREAD_MINOR_D / 2 + 0.15,
                  z0=0.5, z1=5.5, label="cap nut", min_transitions=1)

# Map of part name → (workplane, output filename, optional note).
PARTS = {
    "nozzle_macbeath": (nozzles["macbeath"], "nozzle_macbeath.step",
                        "macbeath-bottle nozzle (socket print-validated) — "
                        "flat mouth DOWN, no supports; pin-clear the Ø0.8 "
                        "orifice or slice at 0.2"),
    "nozzle_loctite": (nozzles["loctite"], "nozzle_loctite.step",
                       "loctite-bottle nozzle (socket fit PENDING — print "
                       "its coupon first) — flat mouth DOWN, no supports"),
    "cap": (cap, "cap.step",
            "shared half-turn cap, fits both nozzles; mouth rim lands flat "
            "on the shoulder, tip seals into the 45° pocket — flat mouth "
            "DOWN, no supports"),
    "macbeath_coupon": (coupons["macbeath"], "test_macbeath_socket.step",
                        "thread-fit coupon (VALIDATED: fits the bottle) — "
                        "flat mouth DOWN, no supports"),
    "loctite_coupon": (coupons["loctite"], "test_loctite_socket.step",
                       "thread-fit coupon (fit PENDING) — flat mouth DOWN, "
                       "no supports"),
}


def _export(name):
    obj, path, note = PARTS[name]
    export_step(obj, str(OUT / path))
    suffix = f"  ({note})" if note else ""
    print(f"Wrote {path}{suffix}")


def collect_components():
    """Placed parts at as-built (SEATED) positions for tools/check_overlaps.py
    — the cap screwed home on the macbeath collar, where its designed contact
    (thread flanks + the preloaded tip seal) is a whitelisted pair."""
    return [("nozzle_macbeath", nozzles["macbeath"]),
            ("cap", cap.translate((0, 0, MACBEATH.shoulder_z))),
            ("nozzle_loctite", nozzles["loctite"].translate((X_LOCTITE, 0, 0))),
            ("macbeath_coupon", coupons["macbeath"].translate((X_COUPON_MAC, 0, 0))),
            ("loctite_coupon", coupons["loctite"].translate((X_COUPON_LOC, 0, 0)))]


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
        .add(nozzles["macbeath"], name="nozzle_macbeath",
             color=color(COLOR["nozzle_macbeath"]))
        # Cap floated above the macbeath tip so the collar + pocket stay visible.
        .add(cap.translate((0, 0, MACBEATH.tip_z + 10.0)), name="cap",
             color=color(COLOR["cap"]))
        .add(nozzles["loctite"].translate((X_LOCTITE, 0, 0)),
             name="nozzle_loctite", color=color(COLOR["nozzle_loctite"]))
        # Fit coupons, kept off to the side per the coupon rule.
        .add(coupons["macbeath"].translate((X_COUPON_MAC, 0, 0)),
             name="macbeath_coupon", color=color(COLOR["macbeath_coupon"]))
        .add(coupons["loctite"].translate((X_COUPON_LOC, 0, 0)),
             name="loctite_coupon", color=color(COLOR["loctite_coupon"]))
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
