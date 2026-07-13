"""Overlap checker for the superglue cap.

Project glue over the shared engine in ``cadkit/overlap_check.py``: supplies
the seated parts (``src.build.collect_components``) and the project's
``intended()`` whitelist, then the engine reports UNINTENDED interpenetrations.

  py -3.12 -m tools.check_overlaps            # report unintended overlaps
  py -3.12 -m tools.check_overlaps --all      # also list intended contacts
  py -3.12 -m tools.check_overlaps --serial   # single-process (baseline/debug)

Exit code is the number of unintended overlapping pairs (0 = clean).

The cap is checked SEATED on the nozzle collar: their thread flanks and the
preloaded tip-in-pocket seal are the designed contact, hence whitelisted.
"""
from __future__ import annotations

import argparse
import sys

from cadkit.overlap_check import run

INTENDED: set[frozenset[str]] = {frozenset({"nozzle", "cap"})}


def intended(na, nb) -> bool:
    if "build_counter" in (na, nb):
        return True
    return frozenset({na, nb}) in INTENDED


def main():
    ap = argparse.ArgumentParser(description="Superglue-cap overlap checker.")
    ap.add_argument("--all", action="store_true", help="also list intended contacts")
    ap.add_argument("--serial", action="store_true", help="single-process (baseline/debug)")
    ap.add_argument("-j", "--jobs", type=int, default=None,
                    help="worker processes (default: cores/2)")
    args = ap.parse_args()

    from src.build import collect_components       # heavy: deferred so workers skip it
    comps = [(n, wp.val()) for n, wp in collect_components()]
    jobs = 1 if args.serial else args.jobs
    sys.exit(run(comps, intended, jobs=jobs, show_all=args.all))


if __name__ == "__main__":
    main()
