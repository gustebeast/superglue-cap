"""Superglue cap — all shared constants (one source of truth).

Replacement dispenser (NOZZLE) + quarter-turn sealing CAP for superglue
bottles, in TWO bottle variants (one printed cap fits both nozzles —
everything above the flat shoulder is identical; only the bottle socket,
and therefore the shoulder height, differs):

  * MACBEATH — the original bottle. Socket dims print-validated 2026-07-13
    (0.4 nozzle): bore Ø15.3 / ridge tip Ø13.7 / pitch 2 / single start /
    11.5 mm neck engagement. (The neck was first hand-measured Ø13 major /
    Ø11 minor / depth 1 — the v1 coupon proved that undersized; the socket
    dims below are the source of truth for fit.)
  * LOCTITE — measured 2026-07-13: bore Ø18 / ridge tip Ø16 (thread height
    1.0) / pitch 3 / 11 mm neck engagement. PRINT-FIT PENDING — coupon
    exported as test_loctite_socket.step.

The female socket uses the project-local ASYMMETRIC (buttress) profile —
45° ridge underside (self-supporting, mouth-down print), gentle up-facing
top flank — because a symmetric 45° thread can't reach these depth/pitch
ratios (see src/thread_socket.py). The nozzle↔cap joint is a cadkit
multistart thread that seals in a HALF TURN.

Printer: Bambu, 0.4 mm nozzle (0.2 available), axis vertical, no supports.
"""

import math

# ── Female bottle-socket profile (shared by both variants) ───────────────────
SOCKET_WALL          = 2.6               # skirt wall behind the thread (≥6 perims)
RIDGE_TIP_FLAT       = 0.4               # axial flat on the ridge tip (≥1 extrusion)
RIDGE_TOP_SLOPE_DEG  = 15.0              # up-facing top flank, from horizontal
SOCKET_MOUTH_CHAMFER = 0.0               # NO mouth flare: the mouth face is the
                                         # bed-contact ring, and the smooth entry
                                         # bore guides the bottle fine (restore
                                         # ~0.4 here if starting feels fiddly)
SOCKET_VALLEY_OVERSHOOT = 0.25           # valley cut past the bore wall (thread_socket)


class BottleSpec:
    """One bottle variant: the measured/validated FEMALE socket dims, plus
    everything derived from them. `bore_d`/`ridge_tip_d` are the printed
    socket's IDs (clearances already included — they're what fits)."""

    def __init__(self, name, bore_d, ridge_tip_d, pitch, skirt_depth):
        self.name = name
        self.bore_d = bore_d              # socket ID at the groove roots
        self.ridge_tip_d = ridge_tip_d    # socket ID across the ridge tips
        self.pitch = pitch                # axial crest-to-crest, single start
        self.skirt_depth = skirt_depth    # how deep the neck enters (bore length)

    @property
    def skirt_od(self):
        return self.bore_d + 2 * SOCKET_WALL

    @property
    def thread_z0(self):
        # Helix start BELOW the floor, so the first ridge emerges THROUGH the
        # mouth face and its cross-section widens the bed-contact ring (same
        # trick as the cap's nut). This is the start point that MAXIMIZES
        # bottom surface: the ridge's up-facing flank at the wall last touches
        # z=0 when the helix starts at −(tip half-flat + wall_depth·tan(top
        # slope)) — starting lower adds no floor material, higher gives some
        # up. The 0.25 margin also keeps the sweep's start face clear of the
        # cutter blank's bottom (a near-coincident face grazes).
        wall_depth = (self.bore_d - self.ridge_tip_d) / 2
        return -(RIDGE_TIP_FLAT / 2
                 + wall_depth * math.tan(math.radians(RIDGE_TOP_SLOPE_DEG))
                 + 0.25)

    @property
    def top_rise(self):
        # How far the LAST ridge's up-facing flank extends ABOVE the helix
        # top, at the bore wall.
        return (RIDGE_TIP_FLAT / 2
                + (self.bore_d / 2 + SOCKET_VALLEY_OVERSHOOT - self.ridge_tip_d / 2)
                * math.tan(math.radians(RIDGE_TOP_SLOPE_DEG)))

    @property
    def socket_turns(self):
        # WHOLE turns above the (below-floor) helix start (a partial turn
        # wipes the part), leaving room for the last ridge's top flank below
        # the ceiling so the thread touches the wall over its complete path.
        return int((self.skirt_depth - self.thread_z0 - self.top_rise)
                   // self.pitch)

    @property
    def shoulder_z(self):
        # The 45° socket ceiling funnels from the bore down to the shared
        # throat Ø; the flat shoulder sits where it gets there.
        return self.skirt_depth + (self.bore_d - NOZZLE_THROAT_D) / 2

    @property
    def tip_z(self):
        return self.shoulder_z + DISPENSER_H

    # Thread-fit coupon (test_<name>_socket.step): 2 turns, open tube.
    coupon_turns = 2

    @property
    def coupon_h(self):
        return (self.thread_z0 + self.coupon_turns * self.pitch
                + self.top_rise + 0.3)


MACBEATH = BottleSpec("macbeath", bore_d=15.3, ridge_tip_d=13.7,
                      pitch=2.0, skirt_depth=11.5)
LOCTITE = BottleSpec("loctite", bore_d=18.0, ridge_tip_d=16.0,
                     pitch=3.0, skirt_depth=11.0)
BOTTLES = (MACBEATH, LOCTITE)

# ── Nozzle ↔ cap thread — HALF-TURN (2-start, 8 mm lead) ─────────────────────
# 180° of rotation advances 4 mm — cap goes from caught to sealed in a half
# turn. Cross-section = the print-proven Ø13/Ø11 pitch-4 profile; cut with
# cadkit.threads' multistart family (upstreamed from this project). The 12°
# lead angle self-locks far better than the earlier 24° quarter-turn version.
# Clearance on the MALE side (nut stays nominal).
CAP_THREAD_MAJOR_D = 13.0                # female nut nominal
CAP_THREAD_MINOR_D = 11.0
CAP_THREAD_LEAD    = 8.0                 # mm advance per full turn
CAP_THREAD_STARTS  = 2
CAP_THREAD_SPACING = CAP_THREAD_LEAD / CAP_THREAD_STARTS      # 4.0 ridge spacing
CAP_THREAD_CLR     = 0.6                 # diametral, off the male collar
NOZZLE_COLLAR_MAJOR_D = CAP_THREAD_MAJOR_D - CAP_THREAD_CLR   # 12.4
NOZZLE_COLLAR_MINOR_D = CAP_THREAD_MINOR_D - CAP_THREAD_CLR   # 10.4
NOZZLE_COLLAR_LEN  = 6.0                 # 1.5 ridge spacings of engagement

# ── Dispenser above the shoulder (IDENTICAL for every variant) ───────────────
# All z's here are RELATIVE to the flat shoulder plane (= the cap's seat).
# Interior: ONE continuous cone from the Ø7.3 throat at the shoulder plane to
# the Ø0.8 orifice — no mid-channel kink. (It can't start at the full socket
# bore: that would be wider than the Ø12.4 collar around it.)
NOZZLE_THROAT_D    = 7.3                 # continuous cone base, AT the shoulder
DISPENSER_H        = 34.5                # shoulder → tip
NOZZLE_CONE_BASE_D = 10.0                # exterior cone base (clears Ø11 ridges)
NOZZLE_TIP_OD      = 2.4                 # flat tip rim — 0.8 wall at the orifice
NOZZLE_ORIFICE_D   = 0.8                 # minimum inner Ø, at the tip face


def _INT_R_AT(dz):
    """Internal-cone radius at height dz above the shoulder plane."""
    return (NOZZLE_THROAT_D / 2
            - (NOZZLE_THROAT_D - NOZZLE_ORIFICE_D) / 2 * dz / DISPENSER_H)


assert NOZZLE_COLLAR_MINOR_D / 2 - _INT_R_AT(0.0) >= 1.2, \
    "collar wall too thin over the internal cone — shrink NOZZLE_THROAT_D"
assert NOZZLE_CONE_BASE_D / 2 - _INT_R_AT(NOZZLE_COLLAR_LEN) >= 1.2, \
    "cone-base wall too thin over the internal cone"
assert NOZZLE_TIP_OD / 2 - _INT_R_AT(DISPENSER_H) >= 0.75, "tip wall too thin"

# ── Cap (cap.step, ONE for all variants) ─────────────────────────────────────
# A 1.6 mm SHELL following the dispensing cone; thread boss + ribs grow
# outward from it. Mouth rim lands flat on the shoulder while the tip rim
# wedges CAP_SEAL_PRELOAD into the 45° pocket (plastic gives; both engage).
CAP_WALL         = 1.6                   # shell thickness over the cavity
CAP_BOSS_OD      = CAP_THREAD_MAJOR_D + 2 * CAP_WALL          # 16.2 thread boss
CAP_NUT_H        = NOZZLE_COLLAR_LEN     # 6.0 — female thread band at the mouth
CAP_SEAL_PRELOAD = 0.15                  # tip/pocket interpenetration at seat
CAP_CONE_CLR     = 0.5                   # radial clearance around the dispensing cone
CAP_TOP_FLAT_D   = 2.0                   # truncated top (no needle apex)

# ── Grip ribs (both pieces) ──────────────────────────────────────────────────
GRIP_RIB_D  = 1.2                        # rib Ø (protrudes ~0.6)
GRIP_RIB_Z0 = 0.0                        # ribs start ON the bed: extra first-layer
                                         # area (mouth faces are FLAT — no bottom
                                         # chamfer; use slicer elephant-foot comp)
NOZZLE_RIB_N = 20                        # around the skirt
CAP_RIB_N    = 16                        # around the thread boss

# ── Assembly viz ─────────────────────────────────────────────────────────────
COUNTER_Z = 115.0                        # build number float height

# ── Per-variant invariants ───────────────────────────────────────────────────
for _b in BOTTLES:
    assert _b.ridge_tip_d < _b.bore_d, f"{_b.name}: thread height must be positive"
    assert _b.socket_turns >= 2, f"{_b.name}: too shallow for 2 socket turns"
    assert _b.thread_z0 + _b.socket_turns * _b.pitch < _b.skirt_depth, \
        f"{_b.name}: socket thread must end inside the skirt"
    # The LAST ridge's up-facing flank must also stay on the wall (below the
    # ceiling), so the thread touches the wall over its complete path.
    assert (_b.thread_z0 + _b.socket_turns * _b.pitch + _b.top_rise
            <= _b.skirt_depth), f"{_b.name}: last ridge runs into the ceiling"
    assert _b.bore_d > NOZZLE_THROAT_D, f"{_b.name}: bore narrower than the throat"
