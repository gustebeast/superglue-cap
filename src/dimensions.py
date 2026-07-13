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

# ── Cap (cap.step) — solid conical roof, prints mouth-down, no supports ─────
# The old cap's interior is 11.5 deep: that much VERTICAL bore wall (threads
# in its lower band, same validated socket), then the ceiling closes as a 45°
# cone (a flat ceiling would be an unprintable bridge). The exterior follows:
# Ø20.5 cylinder, then a 45° cone truncated to a small flat (a sharp apex
# prints badly; the flat keeps ≥1 mm of solid above the interior apex).
CAP_SOCKET_DEPTH = 11.5                  # interior vertical-wall depth (old cap)
CAP_OD           = SOCKET_BORE_D + 2 * SOCKET_WALL   # 20.5
CAP_TOP_FLAT_D   = 3.0                   # truncated cone tip flat
# Threads run the WHOLE vertical wall (like the old cap), not just the
# bottle's 2 measured turns: as many WHOLE turns as fit above the entry lead
# (sweep height must be whole turns — a partial turn wipes the part).
# 11.5 − 1.2 = 10.3 → 5 turns, thread top at 11.2, 0.3 under the ceiling.
CAP_SOCKET_TURNS = int((CAP_SOCKET_DEPTH - SOCKET_ENTRY_LEAD) // BOTTLE_PITCH)  # 5
assert SOCKET_ENTRY_LEAD + CAP_SOCKET_TURNS * BOTTLE_PITCH < CAP_SOCKET_DEPTH

# ── Assembly viz ─────────────────────────────────────────────────────────────
COUNTER_Z = 30.0                         # build number float height

# ── Invariants ───────────────────────────────────────────────────────────────
assert SOCKET_RIDGE_TIP_D < SOCKET_BORE_D, "thread height must be positive"
assert SOCKET_BORE_D > BOTTLE_MAJOR_D, "bore must clear the male crest"
# (Ridge-vs-male-flank checks retired: BOTTLE_MAJOR/MINOR_D are stale — the v1
# coupon proved them undersized. Re-add once the neck is re-measured.)
