"""Superglue cap — all shared constants (one source of truth).

Replacement dispenser tip + cap for a superglue bottle. The bottle's neck
thread was measured by hand (calipers, 2026-07-12):

  * thread OD (male major)  Ø13.0
  * thread pitch            2.0 mm crest-to-crest
  * thread depth            ~1.0 mm  (=> male minor ~Ø11)
  * SINGLE start, ~2 turns  (confirmed by eye: one ridge end at the rim)

A symmetric 45° FDM thread (cadkit.threads) is geometrically impossible at
this pitch/depth combo — two 45° flanks × 1 mm depth consume the whole 2 mm
pitch, and cadkit's cutter additionally needs depth < pitch/2 − 0.6 (valley
overshoot) ≈ 0.4 mm, which would leave ~0.15 mm of engagement. So the female
socket uses a project-local ASYMMETRIC (buttress-style) profile instead, in
src/thread_socket.py:

  * ridge UNDERSIDE at 45°  — the only down-facing surface, self-supporting
    when the part prints with its mouth on the bed (axis vertical);
  * ridge TOP at 15° from horizontal — an up-facing surface, so it carries
    no overhang constraint and frees the axial room the 45° profile lacks;
  * ridge tip shortened to ~0.5 mm radial engagement (the bottle's V-thread
    root is never reached; flank/crest contact does the holding, plenty for
    a cap).

Printer: Bambu, 0.4 mm nozzle (0.2 available if the fit needs it), axis
vertical, no supports.
"""

# ── Bottle neck (male thread, measured) ──────────────────────────────────────
BOTTLE_MAJOR_D = 13.0    # male thread crest Ø
BOTTLE_MINOR_D = 11.0    # male thread root Ø (major − 2 × measured depth)
BOTTLE_PITCH   = 2.0     # axial crest-to-crest, single start
BOTTLE_TURNS   = 2.0     # engagement length ≈ 4 mm of thread on the neck

# ── Female socket thread (printed, asymmetric profile) ──────────────────────
# v2 (fit iteration, 2026-07-13): the v1 socket (bore Ø13.4 / tip Ø12.0 off
# the measured Ø13 crest) was undersized on the actual bottle — the user
# re-specified the socket DIRECTLY: bore Ø15.3, thread height 0.8, tip Ø13.7.
# Tip Ø13.7 > the originally measured male crest Ø13.0, so the real neck is
# bigger than first measured (BOTTLE_* above are stale until re-measured —
# the socket dims below are now the source of truth for fit).
SOCKET_BORE_D      = 15.3                # groove-root bore (user-specified ID)
SOCKET_RIDGE_TIP_D = 13.7                # female ridge tip Ø (= bore − 2 × 0.8)
RIDGE_TIP_FLAT     = 0.4                 # axial flat on the ridge tip (≥ 1 extrusion)
RIDGE_TOP_SLOPE_DEG = 15.0               # up-facing top flank, from horizontal
SOCKET_ENTRY_LEAD  = 1.2                 # smooth bore below the first ridge
                                         # (clears elephant's foot, starts square)
SOCKET_MOUTH_CHAMFER = 0.8               # conical flare at the mouth (easy start)

# FIT VERDICT (print-tested 2026-07-13, 0.4 nozzle): bore Ø15.3 / tip Ø13.7 /
# pitch 2 / 2 turns THREADS ONTO THE BOTTLE — these are the validated numbers.
SOCKET_WALL = 2.6                        # wall behind the thread (≥ 6 perimeters at 0.4)

# ── Thread-fit coupon (test_bottle_socket.step) ──────────────────────────────
COUPON_OD   = SOCKET_BORE_D + 2 * SOCKET_WALL   # 20.5
COUPON_H    = SOCKET_ENTRY_LEAD + BOTTLE_TURNS * BOTTLE_PITCH + 0.8   # 6.0 — open tube

# ── Nozzle (nozzle.step) — screws onto the bottle, dispenses ────────────────
# Bottom-up stack (all z from the bottle-socket mouth):
#   skirt    Ø20.5 × 11.5 — the validated bottle socket (old cap's depth),
#            threads the whole vertical wall;
#   shoulder 45° cone necking Ø20.5 → the cap collar Ø;
#   collar   male thread the CAP screws onto (cadkit.threads profile below);
#   cone     the dispensing cone, Ø9 → Ø4 tip, with a Ø2 glue channel.
# Interior: the socket's 45° ceiling cone narrows from the bore to the glue
# channel (self-supporting mouth-down), then the channel runs to the tip.
NOZZLE_SKIRT_DEPTH = 11.5                # interior vertical-wall depth (old cap)
NOZZLE_SKIRT_OD    = SOCKET_BORE_D + 2 * SOCKET_WALL   # 20.5
# Threads run the WHOLE skirt wall: as many WHOLE turns as fit above the
# entry lead (sweep height must be whole turns — a partial turn wipes the
# part). 11.5 − 1.2 = 10.3 → 5 turns, thread top at 11.2, 0.3 under ceiling.
NOZZLE_SOCKET_TURNS = int((NOZZLE_SKIRT_DEPTH - SOCKET_ENTRY_LEAD) // BOTTLE_PITCH)  # 5
assert SOCKET_ENTRY_LEAD + NOZZLE_SOCKET_TURNS * BOTTLE_PITCH < NOZZLE_SKIRT_DEPTH

# ── Nozzle ↔ cap thread — QUARTER-TURN (4-start, 16 mm lead) ─────────────────
# The cap seals in a 90° turn: 4 starts at LEAD 16 advance 4 mm per quarter
# turn. The local cross-section is IDENTICAL to the print-proven Ø13/Ø11
# pitch-4 profile (depth 1.0, 1.0 flats, 45° flanks, ridges 4 mm apart) —
# only the helix steepens (~24° lead angle). cadkit.threads' public cutters
# are single-start, so src/quick_thread.py composes the same valley-sweep
# recipe (whole-turn sweeps, 4-pt quad, sequential clean=False cuts).
# Clearance goes on the MALE side (shrink the screw, keep the nut nominal).
CAP_THREAD_MAJOR_D = 13.0                # female nut nominal
CAP_THREAD_MINOR_D = 11.0
CAP_THREAD_LEAD    = 16.0                # mm advance per full turn
CAP_THREAD_STARTS  = 4
CAP_THREAD_SPACING = CAP_THREAD_LEAD / CAP_THREAD_STARTS      # 4.0 ridge spacing
CAP_THREAD_CLR     = 0.6                 # diametral, off the male collar
NOZZLE_COLLAR_MAJOR_D = CAP_THREAD_MAJOR_D - CAP_THREAD_CLR   # 12.4
NOZZLE_COLLAR_MINOR_D = CAP_THREAD_MINOR_D - CAP_THREAD_CLR   # 10.4
NOZZLE_COLLAR_LEN  = 6.0                 # 1.5 ridge spacings of engagement

# Nozzle stack z's (FLAT shoulder → collar → dispensing cone).
# The skirt→collar transition is a FLAT annular step, not a cone: the cap's
# flat mouth rim lands on it for a clean flat contact when fully screwed on
# (a conical shoulder left an awkward gap under the cap rim). The step is
# up-facing, so printability is unchanged. It sits high enough that the 45°
# socket ceiling inside has narrowed clear of the collar wall.
# The dispensing tip stays the standard cone (Ø9 → Ø4 over 13), with the
# internal channel tapering from the Ø5 throat to a Ø0.8 orifice at the tip.
NOZZLE_SHOULDER_Z = 15.5                 # flat shoulder plane — the cap's seat
NOZZLE_COLLAR_Z0 = NOZZLE_SHOULDER_Z
NOZZLE_CONE_Z0   = NOZZLE_COLLAR_Z0 + NOZZLE_COLLAR_LEN       # 21.0
NOZZLE_TIP_Z     = 50.0                  # total dispenser height (user spec)
NOZZLE_CONE_BASE_D = 10.0                # must pass under the cap's Ø11 ridge tips
NOZZLE_TIP_OD      = 2.4                 # flat tip rim (the sealing edge) — 0.8 wall
                                         # around the Ø0.8 orifice (2 perimeters)
NOZZLE_ORIFICE_D = 0.8                   # minimum inner Ø, at the tip face
# Interior: ONE continuous cone from the shoulder plane to the orifice. A
# single cone can't start at the full socket bore (Ø15.3 at z=11.5 would
# still be Ø7+ inside the Ø12.4 collar — fatter than the collar), so the 45°
# socket ceiling funnels down exactly to the shoulder plane, and the
# continuous cone takes over from there — sized so it clears the collar
# thread roots by ≥1.2 mm.
NOZZLE_THROAT_Z  = NOZZLE_SHOULDER_Z
NOZZLE_THROAT_D  = SOCKET_BORE_D - 2 * (NOZZLE_SHOULDER_Z - NOZZLE_SKIRT_DEPTH)  # 7.3
_INT_R_AT = lambda z: (NOZZLE_THROAT_D / 2
                       - (NOZZLE_THROAT_D - NOZZLE_ORIFICE_D) / 2
                       * (z - NOZZLE_THROAT_Z) / (NOZZLE_TIP_Z - NOZZLE_THROAT_Z))
assert NOZZLE_COLLAR_MINOR_D / 2 - _INT_R_AT(NOZZLE_COLLAR_Z0) >= 1.2, \
    "collar wall too thin over the internal cone — shrink NOZZLE_THROAT_D"
assert NOZZLE_CONE_BASE_D / 2 - _INT_R_AT(NOZZLE_CONE_Z0) >= 1.2, \
    "cone-base wall too thin over the internal cone"
assert NOZZLE_TIP_OD / 2 - _INT_R_AT(NOZZLE_TIP_Z) >= 0.75, "tip wall too thin"

# ── Cap (cap.step) — screws onto the collar, mouth lands FLAT on the shoulder ─
# Interior, mouth-up: nut thread section (threaded_rod cutter, nominal), a 45°
# neck-down, a taper hugging the dispensing cone (+0.5/side), then a 45°
# conical SEAL POCKET for the tip rim. Fully screwed on, the cap's flat mouth
# rim closes on the nozzle's flat shoulder (the clean contact area) while the
# tip rim wedges CAP_SEAL_PRELOAD into the pocket — small enough that the
# plastic gives and BOTH contacts engage.
CAP_OD           = 18.0
CAP_WALL_MIN     = (CAP_OD - CAP_THREAD_MAJOR_D) / 2          # 2.5 behind the nut
CAP_NUT_H        = NOZZLE_COLLAR_LEN     # 6.0 — female thread band at the mouth
CAP_SEAL_PRELOAD = 0.15                  # tip/pocket interpenetration at seat
CAP_CONE_CLR     = 0.5                   # radial clearance around the dispensing cone
CAP_TOP_FLAT_D   = 5.0                   # truncated top (no needle apex)
CAP_SEAT_Z       = NOZZLE_SHOULDER_Z     # mouth plane = the flat shoulder, seated

# ── Grip ribs (both pieces) ──────────────────────────────────────────────────
# Vertical half-round ribs around the cylindrical sections — print cleanly
# with the axis vertical. They start above the mouth chamfer and stop where
# the exterior turns conical (rib tops are up-facing there).
GRIP_RIB_D  = 1.2                        # rib Ø (protrudes ~0.6)
GRIP_RIB_Z0 = 0.8                        # above the 0.6 mouth chamfer
NOZZLE_RIB_N = 20                        # around the Ø20.5 skirt (~3.2 mm spacing)
CAP_RIB_N    = 16                        # around the Ø18 shell

# ── Assembly viz ─────────────────────────────────────────────────────────────
CAP_EXPLODE_Z = NOZZLE_TIP_Z + 10.0      # cap floats above the nozzle tip
COUNTER_Z = 115.0                        # build number float height

# ── Invariants ───────────────────────────────────────────────────────────────
assert SOCKET_RIDGE_TIP_D < SOCKET_BORE_D, "thread height must be positive"
assert SOCKET_BORE_D > BOTTLE_MAJOR_D, "bore must clear the male crest"
# (Ridge-vs-male-flank checks retired: BOTTLE_MAJOR/MINOR_D are stale — the v1
# coupon proved them undersized. Re-add once the neck is re-measured.)
