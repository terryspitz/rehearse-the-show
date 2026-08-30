#!/usr/bin/env python3
"""Merge Audiveris's over-segmented logical parts into singable voice parts.

Audiveris mints a new logical part whenever a system's staff layout changes, so
a show number that alternates solo and chorus writing comes back as a dozen
fragments instead of three continuous lines. This folds them back together
using two things Audiveris *does* get right: the OCR'd staff label and the clef.

This is the automated half of the review step. A human still confirms it.

Usage:
    python spike/merge_parts.py out.mid score.mxl [score2.mxl ...] [--split]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from music21 import chord, clef, instrument, midi, note, stream

# Audiveris OCRs the bracket label "Ens." as Ell./Elsi./E15./En./Els. and so on,
# and mangles T and B less often. Match generously, then fall back to clef.
LABEL_RULES = [
    ("tenor", r"^t$|^ten|^e[l1][l1s5]|^en\.?$|^els"),
    ("bass",  r"^b|^11$"),
]


def route(part: stream.Part) -> str:
    name = (part.partName or "").strip().lower().replace("“", "").replace("‘", "")
    for group, pattern in LABEL_RULES:
        if re.search(pattern, name):
            return group
    clefs = {type(c) for c in part.recurse().getElementsByClass(clef.Clef)}
    if clef.BassClef in clefs and clef.TrebleClef not in clefs:
        return "bass"
    return "solo"


GROUPS = ["solo", "tenor", "bass"]
PROGRAM = {"solo": 53, "tenor": 52, "bass": 52}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", help="output .mid path (a stem, if --split)")
    ap.add_argument("scores", nargs="+", help="MusicXML files, in playing order")
    ap.add_argument("--split", action="store_true", help="also write one file per group")
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
