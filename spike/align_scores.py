#!/usr/bin/env python3
"""Align a separately-scanned piano score against the vocal score.

The two books are printed with matching bar numbers, but Audiveris renumbers
measures from 1 per movement, so the printed numbers don't survive the parse.
Instead this aligns on *musical anchors* — the bars where the key or time
signature changes — which are unmistakable landmarks that both scans share.

It reports the offset it found and how well the anchors agree, so a bad
alignment is visible rather than silent.

Usage:
    python spike/align_scores.py vocal.mxl piano.mxl [more-vocal.mxl ...]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from music21 import converter, stream


def anchors(score: stream.Score) -> tuple[list[tuple[int, str]], int]:
    """Bars where key or meter changes, as (bar_index, label), plus bar count."""
    part = score.parts[0] if score.parts else score
    measures = list(part.getElementsByClass(stream.Measure))
    found, key, meter = [], None, None
    for i, m in enumerate(measures):
        for ks in m.getElementsByClass("KeySignature"):
            if ks.sharps != key:
                key = ks.sharps
                found.append((i, f"key{ks.sharps:+d}"))
        for ts in m.getElementsByClass("TimeSignature"):
            if ts.ratioString != meter:
                meter = ts.ratioString
                found.append((i, f"time{ts.ratioString}"))
    return found, len(measures)


def best_offset(vocal: list[tuple[int, str]], piano: list[tuple[int, str]],
                span: int) -> tuple[int, int, int]:
    """Offset maximising matching anchors. Returns (offset, matched, possible)."""
    labels_v = {i: lab for i, lab in vocal}
    best = (0, -1, len(piano))
    for off in range(-span, span + 1):
        hits = sum(1 for i, lab in piano if labels_v.get(i + off) == lab)
        if hits > best[1]:
            best = (off, hits, len(piano))
    return best


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vocal", help="vocal score MusicXML (repeat for multi-movement exports)")
    ap.add_argument("piano", help="piano score MusicXML")
    ap.add_argument("--extra-vocal", nargs="*", default=[],
                    help="further vocal movements, in order, appended to the first")
    ap.add_argument("--span", type=int, default=40, help="offsets to search either way")
    args = ap.parse_args()

    v_anchors: list[tuple[int, str]] = []
    v_bars = 0
    for path in [args.vocal, *args.extra_vocal]:
        a, n = anchors(converter.parse(path))
        v_anchors += [(i + v_bars, lab) for i, lab in a]
        v_bars += n
        print(f"  vocal  {Path(path).name}: {n} bars, anchors {[f'{i}:{l}' for i, l in a]}")

    p_anchors, p_bars = anchors(converter.parse(args.piano))
    print(f"  piano  {Path(args.piano).name}: {p_bars} bars, "
          f"anchors {[f'{i}:{l}' for i, l in p_anchors]}")

    off, matched, possible = best_offset(v_anchors, p_anchors, args.span)
    print(f"\n  vocal bars {v_bars}  vs  piano bars {p_bars}  (difference {v_bars - p_bars:+d})")
    print(f"  best offset: {off:+d} bars — {matched}/{possible} anchors agree")

    if possible and matched == possible and abs(v_bars - p_bars) <= 2:
        print("  VERDICT: confident. Align piano bar n to vocal bar n%+d." % off)
    elif matched >= max(1, possible // 2):
        print("  VERDICT: partial. Some anchors agree; needs a human to confirm.")
    else:
        print("  VERDICT: no reliable alignment — the two parses disagree too much.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
