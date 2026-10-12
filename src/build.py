"""Superglue cap — main build script.

Run from the repo root:
  py -3.12 -m src.build              # build all parts + assembly
  py -3.12 -m src.build --part NAME  # build only one part
  py -3.12 -m src.build --list       # list available part names

Writes one STEP per printed part and hands a coloured assembly straight to
the web viewer (cadkit.web), whose page states the build number.

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
from cadkit.web import show
from cadkit.step_export import export_print
from cadkit.orientation import (PrintOrientation as PO,
                                require_declared, unconfirmed)

from .cap import build_cap
from .dimensions import (
    BOTTLES,
    CAP_THREAD_MINOR_D,
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

# ── PRINT ORIENTATION — each printed part's bed face, declared once, where
# cadkit's export can read it (cadkit/AGENTS.md; the contract exists because
# a MISSING declaration used to look exactly like a deliberate "models as
# printed", and a part on another project shipped standing on its end).
#
# Nothing new is being decided here: every part's note above already said
# FLAT MOUTH DOWN, NO SUPPORTS, and every part is modelled that way — the
# flat mouth at z = 0, the part growing up off it. So all five are `None`,
# "models as printed". cadkit.tools.suggest_orientation independently ranks
# None first for all five.
#
# CONFIRMED: this is the geometry's own orientation, not an assumption — the
# mouth is the one large flat face, the 45° seal pocket is cut to be
# self-supporting from it, and the macbeath socket has been printed and fits.
# (The loctite FIT is still pending; that is a thread-size question, not an
# orientation one, and it does not make the bed face a guess.)
_MOUTH_DOWN = "flat mouth DOWN on the bed, no supports — the mouth is the "              "one large flat face and the 45 deg seal geometry is cut to "              "be self-supporting from it"
PRINT_ORIENTATION = {
    "nozzle_macbeath": PO(None, _MOUTH_DOWN + "; socket print-validated"),
    "nozzle_loctite":  PO(None, _MOUTH_DOWN),
    "cap":             PO(None, _MOUTH_DOWN + "; the rim lands flat on the "
                                "shoulder and the tip seals into the 45 deg "
                                "pocket, both printed from this face"),
    "macbeath_coupon": PO(None, _MOUTH_DOWN + "; a coupon prints on the same "
                                "face as the part it stands in for, or it "
                                "tests a print nobody makes"),
    "loctite_coupon":  PO(None, _MOUTH_DOWN + "; same face as its part"),
}
require_declared(set(PARTS), PRINT_ORIENTATION)


def _export(name):
    obj, path, note = PARTS[name]
    export_print(obj, PRINT_ORIENTATION[name], str(OUT / path))
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


# ── Build counter — bumped every full build, shown on the viewer page ────────
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
    print(f"Assembly: {len(assembly.children)} parts  [build #{build_n}]", flush=True)
    show(assembly, root=OUT, build=build_n)


def main() -> None:
    p = argparse.ArgumentParser(prog="src.build", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--part", help="Build only this part (skips assembly).")
    p.add_argument("--list", action="store_true", help="List part names and exit.")
    args = p.parse_args()

    # 🚩 an UNCONFIRMED bed face is a guess nobody has checked — and the bed
    # face decides which faces are overhangs, so work done on top of a guess
    # can be silently wrong. Say so on every build (cadkit AGENTS.md).
    flagged = unconfirmed(PRINT_ORIENTATION)
    if flagged:
        print("UNCONFIRMED print orientation (confirm with the user BEFORE "
              "working on these parts): " + ", ".join(flagged), flush=True)

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
