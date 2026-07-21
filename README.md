# superglue-cap

Parametric replacement **dispenser nozzle + sealing cap** for superglue
bottles, modelled in [CadQuery](https://cadquery.readthedocs.io/) with the
shared [`cadkit`](https://github.com/gustebeast/cadkit) utilities (vendored
under `cadkit/` via git subtree).

The stock dispenser tips on cyanoacrylate bottles clog and shear off; this
replaces them with a printable two-piece set:

- **Nozzle** (~50 mm tall) — screws onto the bottle's neck thread and
  funnels glue through a single continuous internal cone (Ø7.3 throat →
  Ø0.8 orifice, no kinks for glue to pool in) to a slender dispensing tip.
- **Cap** — a 1.6 mm conical shell that follows the nozzle. It closes in a
  **half turn** (2-start, 8 mm lead thread), its flat mouth rim lands on the
  nozzle's flat shoulder, and a 45° internal pocket wedges onto the nozzle's
  tip rim with 0.15 mm of preload — thread torque loads both contacts.

Two bottle variants share all of the code and the same cap — only the
bottle-thread socket differs:

| Variant | Socket bore | Ridge-tip ID | Pitch | Engagement | Status |
|---|---|---|---|---|---|
| `macbeath` | Ø15.3 | Ø13.7 | 2 mm | 11.5 mm | print-validated |
| `loctite`  | Ø18.0 | Ø16.0 | 3 mm | 11.0 mm | fit pending — print its coupon first |

Adding a bottle = adding one `BottleSpec` line in `src/dimensions.py` — or
just using the web generator below with your own measurements.

## Web generator

[`docs/`](docs/) is a browser-based generator (same idea as the
[pantorouter template generator](https://github.com/gustebeast/pantorouter-template-generator)):
measure your bottle's thread with calipers — the page has diagrams for each
measurement — hit Generate, and download STEP/STL for a nozzle, cap, and
thread-fit test piece matched to your bottle. All geometry is built locally in the
browser via [replicad](https://replicad.xyz); nothing is uploaded. The JS
geometry mirrors `src/` constant-for-constant — keep them in sync.

To preview locally (a real HTTP server is needed for the WASM kernel):

```sh
py -3.12 -m http.server 8080 -d docs
# open http://localhost:8080
```

To publish: enable GitHub Pages for the repo, source "main branch /docs".

## Printing

All parts: **flat mouth face down, axis vertical, no supports.**
PETG or PLA, 0.4 mm nozzle, 0.2 mm layers, 3+ walls. Enable your slicer's
elephant-foot compensation (the bottoms are deliberately square for bed
adhesion, and thread ridges reach the first layer). The Ø0.8 orifice prints
tight at 0.4 mm — clear it with a pin, or slice the nozzle at 0.2 mm.

Print the `test_<variant>_socket.step` **coupon** (a few minutes of plastic)
and spin it onto your bottle before committing to the full nozzle.

Note: cyanoacrylate bonds PETG/PLA, so treat the nozzle as a consumable —
or print it in PP, which CA barely sticks to. A PTFE dry-film spray in the
channel makes cured clogs removable.

## Building from source

Requires Python 3.10–3.12 with `cadquery` installed.

```
py -3.12 -m src.build              # all STEPs + assembly.step (+ FreeCAD viewer)
py -3.12 -m src.build --list      # part names
py -3.12 -m src.build --part cap  # one part
py -3.12 -m tools.check_overlaps  # collision gate (0 = clean)
```

`View Assembly.cmd` opens the last-built assembly in FreeCAD (Windows).

## Layout

```
src/
  dimensions.py    every constant + the BottleSpec variants (start here)
  thread_socket.py the asymmetric (buttress) bottle-thread socket + probes
  nozzle.py        nozzle builder (per BottleSpec)
  cap.py           the shared cap builder
  grip.py          grip-rib helper
  build.py         build/export/assembly entry point
tools/
  check_overlaps.py  interpenetration gate over the seated assembly
cadkit/            vendored shared library (threads, export, viewer, ...)
```

Two thread systems live here, and both are probe-gated at build time (a
solid/void march along each helix — OCCT fails silently, so the build fails
loudly instead):

- the **bottle socket** is a project-local asymmetric profile — a 45°
  self-supporting ridge underside with a steep top flank — because these
  bottles' depth-to-pitch ratios are impossible for a symmetric 45° FDM
  thread;
- the **nozzle↔cap** joint uses `cadkit.threads`' multistart family
  (upstreamed from this project), the print-proven Ø13/Ø11 profile on two
  8 mm-lead helices.

## License

[CERN-OHL-S v2](https://cern-ohl.web.cern.ch/) (strongly reciprocal) —
models, code, and site. Use, modify, and sell freely; distribute sources
of derivatives under the same licence.
