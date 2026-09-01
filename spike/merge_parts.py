#!/usr/bin/env python3
"""Merge Audiveris's over-segmented logical parts into singable voice parts.

Audiveris mints a new logical part whenever a system's staff layout changes, so
a show number that alternates solo and chorus writing comes back as a dozen
fragments instead of three continuous lines. This folds them back together
using two things Audiveris *does* get right: the OCR'd staff label and the clef.

Routing uses three signals, in order of reliability:

  1. **Clef.** A bass-clef part is the bass line. Unambiguous.
  2. **Whether a label was read at all.** In a show vocal book the solo staff
     carries no printed label, so Audiveris leaves it as its default "Voice";
     the ensemble staves are labelled (T, B, Ens.) so *something* is OCR'd, even
     if it comes out as "Bus." or "£13." or "'I'". Presence of a label is a far
     more robust signal than its content — the manglings change completely
     between scans of the same page.
  3. **Label text**, only to override the above when it is unambiguous.

This is the automated half of the review step. A human still confirms it.

Pass --fix-timing to repair bars whose durations don't match the time signature
before merging (see spike/fix_timing.py). Do that here rather than by writing a
corrected MusicXML in between: music21 picks a `divisions` value that cannot
represent 2/3-quarter tuplets exactly, so a round-trip through MusicXML
reintroduces most of the drift the repair just removed.

Usage:
    python spike/merge_parts.py out.mid score.mxl [score2.mxl ...] [--split]
                                [--fix-timing]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from music21 import chord, clef, instrument, midi, note, stream

UNLABELLED = {"", "voice", "piano", "part"}   # Audiveris defaults = no label was read


def route(part: stream.Part) -> str:
    """Which singable line does this Audiveris logical part belong to?

    Three signals, most reliable first:
      1. Clef — a bass-clef-only part is the bass line. Unambiguous.
      2. Whether a label was read *at all*. The solo staff in a show vocal book
         carries no printed label, so Audiveris leaves its default "Voice"; the
         ensemble staves are labelled (T, B, Ens.) so something is OCR'd, even
         when it comes out as "Bus." or "£13." or "'I'". Label *presence* is far
         more robust than label *content*: the manglings change completely
         between two scans of the same page, but the presence does not.
    """
    clefs = {type(c) for c in part.recurse().getElementsByClass(clef.Clef)}
    if clef.BassClef in clefs and clef.TrebleClef not in clefs:
        return "bass"
    name = re.sub(r"[^a-z0-9]", "", (part.partName or "").lower())
    return "solo" if name in UNLABELLED else "tenor"


GROUPS = ["solo", "tenor", "bass"]
PROGRAM = {"solo": 53, "tenor": 52, "bass": 52}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", help="output .mid path (a stem, if --split)")
    ap.add_argument("scores", nargs="+", help="MusicXML files, in playing order")
    ap.add_argument("--split", action="store_true", help="also write one file per group")
    ap.add_argument("--fix-timing", action="store_true",
                    help="repair bars that don't sum to their time signature first")
    ap.add_argument("--truncate", action="store_true",
                    help="with --fix-timing, also shorten notes in bars no repair "
                         "fits, so playback stays in time")
    args = ap.parse_args()

    from music21 import converter

    merged = {g: stream.Part(id=g) for g in GROUPS}
    for g in GROUPS:
        inst = instrument.Instrument()
        inst.midiProgram = PROGRAM[g]
        merged[g].insert(0, inst)

    cursor = 0.0
    for path in args.scores:
        sc = converter.parse(path)
        if args.fix_timing:
            from fix_timing import repair
            st = repair(sc, truncate=args.truncate)
            print(f"  {Path(path).name}: timing — {st['tuplet_fixed']} tuplets restored, "
                  f"{st['padded']} padded, {st['truncated']} truncated, "
                  f"{st['unfixable']} left for a human")
        span = float(sc.highestTime)
        for part in sc.parts:
            g = route(part)
            for el in part.flatten().notes:
                copy = (chord.Chord(el.pitches) if isinstance(el, chord.Chord)
                        else note.Note(el.pitch))
                copy.quarterLength = el.quarterLength
                merged[g].insert(cursor + float(el.getOffsetInHierarchy(part)), copy)
        print(f"  {Path(path).name}: {len(sc.parts)} parts -> "
              + ", ".join(f"{g}:{len(merged[g].flatten().notes)}" for g in GROUPS))
        cursor += span

    out = Path(args.out)
    combined = stream.Score()
    for g in GROUPS:
        combined.insert(0, merged[g])
    mf = midi.translate.streamToMidiFile(combined)
    mf.open(str(out), "wb"); mf.write(); mf.close()
    print(f"wrote {out}")

    if args.split:
        for g in GROUPS:
            holder = stream.Score(); holder.insert(0, merged[g])
            p = out.with_name(f"{out.stem}-{g}.mid")
            mf = midi.translate.streamToMidiFile(holder)
            mf.open(str(p), "wb"); mf.write(); mf.close()
            print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
