#!/usr/bin/env python3
"""Align a separately-scanned piano score against the vocal score.

The two books are printed with matching bar numbers, but Audiveris renumbers
measures from 1 per movement, so the printed numbers don't survive the parse.
Instead this aligns on *musical anchors* — the bars where the key or time
signature changes — which are unmistakable landmarks that both scans share.

The two books do NOT differ by a constant offset. Each printed "N bars rest"
in the vocal book collapses to a single measure in the parse, so the vocal
score falls progressively further behind the piano. The alignment is therefore
a monotonic warp: anchors are matched in sequence, and the result is a
piecewise-linear bar map with a different local offset in each segment.

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


def match_sequence(vocal, piano):
    """Align two anchor sequences in order (LCS on labels). Returns matched pairs."""
    V, P = len(vocal), len(piano)
    table = [[0] * (P + 1) for _ in range(V + 1)]
    for i in range(V - 1, -1, -1):
        for j in range(P - 1, -1, -1):
            table[i][j] = (table[i + 1][j + 1] + 1 if vocal[i][1] == piano[j][1]
                           else max(table[i + 1][j], table[i][j + 1]))
    pairs, i, j = [], 0, 0
    while i < V and j < P:
        if vocal[i][1] == piano[j][1]:
            pairs.append((vocal[i][0], piano[j][0], vocal[i][1]))
            i += 1; j += 1
        elif table[i + 1][j] >= table[i][j + 1]:
            i += 1
        else:
            j += 1
    return pairs


def bar_map(pairs, v_bars, p_bars):
    """Piecewise-linear vocal-bar -> piano-bar map through the matched anchors."""
    knots = [(0, 0)] + [(v, p) for v, p, _ in pairs] + [(v_bars, p_bars)]
    seen, clean = set(), []
    for v, p in knots:
        if v not in seen:
            seen.add(v); clean.append((v, p))
    clean.sort()
    return clean


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

    pairs = match_sequence(v_anchors, p_anchors)
    print(f"\n  vocal bars {v_bars}  vs  piano bars {p_bars}  (difference {v_bars - p_bars:+d})")
    print(f"  matched {len(pairs)}/{min(len(v_anchors), len(p_anchors))} anchors in sequence\n")
    print(f"  {'anchor':<12}{'vocal':>7}{'piano':>7}{'drift':>7}")
    for v, pb, lab in pairs:
        print(f"  {lab:<12}{v:>7}{pb:>7}{pb - v:>+7}")

    knots = bar_map(pairs, v_bars, p_bars)
    drifts = [pb - v for v, pb, _ in pairs]
    monotonic = all(b >= a for a, b in zip(drifts, drifts[1:]))
    frac = len(pairs) / max(1, min(len(v_anchors), len(p_anchors)))

    print()
    if frac >= 0.9 and monotonic:
        print(f"  VERDICT: confident. Drift grows {drifts[0]:+d} -> {drifts[-1]:+d} bars, "
              "monotonically — consistent with multi-bar rests collapsing in the vocal parse.")
        print(f"  Use the piecewise map ({len(knots)} knots), not a fixed offset:")
        print("    " + "  ".join(f"{v}->{pb}" for v, pb in knots))
    elif frac >= 0.5:
        print("  VERDICT: partial. Anchors mostly line up; a human should confirm the map.")
    else:
        print("  VERDICT: no reliable alignment — the two parses disagree too much.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
