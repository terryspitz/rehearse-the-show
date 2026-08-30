#!/usr/bin/env python3
"""Score an OMR engine's MusicXML against what the page actually contains.

The interesting question for this app isn't "how many noteheads did it get
right" — it's whether the output has enough *structure* to build a mixer from:
distinct parts, a stable staff count, chords where the score has divisi, and
lyrics attached to the right line.

Usage:
    python spike/omr_report.py engine-output.musicxml [more.musicxml ...]
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from music21 import chord, converter, stream


def report(path: Path) -> None:
    try:
        score = converter.parse(str(path))
    except Exception as exc:  # OMR output is frequently malformed
        print(f"\n{path.name}: FAILED TO PARSE — {type(exc).__name__}: {exc}")
        return

    parts = list(score.parts) or [score]
    print(f"\n{path.name}")
    print(f"  parts: {len(parts)}")

    for i, part in enumerate(parts):
        notes = list(part.flatten().notes)
        chords = [n for n in notes if isinstance(n, chord.Chord)]
        sizes = Counter(len(c.pitches) for c in chords)
        lyrics = [n.lyric for n in notes if n.lyric]
        measures = part.getElementsByClass(stream.Measure)
        clefs = {c.sign + str(c.line) for c in part.recurse().getElementsByClass("Clef")}
        keys = {k.sharps for k in part.recurse().getElementsByClass("KeySignature")}
        voices = sum(1 for _ in part.recurse().getElementsByClass(stream.Voice))

        print(
            f"  [{i}] name={part.partName or part.id!r:<14} "
            f"measures={len(measures):<4} notes={len(notes):<5} "
            f"chords={len(chords)} {dict(sizes) if sizes else ''}"
        )
        print(
            f"      lyrics={len(lyrics):<4} explicit-voices={voices:<3} "
            f"clefs={sorted(clefs)} key-sig-sharps={sorted(keys)}"
        )
        if lyrics:
            print(f"      text: {' '.join(lyrics[:16])}")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    for arg in sys.argv[1:]:
        report(Path(arg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
