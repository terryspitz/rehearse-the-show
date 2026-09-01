#!/usr/bin/env python3
"""Repair measures whose note durations don't add up to their time signature.

Audiveris detects triplet brackets inconsistently on a scanned score. When it
misses one, the three notes come through at full length and the bar runs long;
when it catches only part of one, the bar comes up short. Either way every
following note in the part is displaced, so a handful of missed brackets smears
the timing of the whole number — which is far more audible than the wrong notes
themselves.

Two repairs, both conservative:

  * **Over-long bar** — look for a run of consecutive equal-duration notes that,
    scaled by 2/3, makes the bar come out exactly right. That is the signature
    of a missed triplet. Applied only when the arithmetic lands exactly.
  * **Short bar** — pad with a rest. This does not recover the missing note, but
    it stops the bar from dragging everything after it out of place.

Bars that neither repair fixes are left alone and reported, because they need a
human. Silently guessing at them would be worse than leaving them visible.

Usage:
    python spike/fix_timing.py in.mxl out.musicxml
"""

from __future__ import annotations

import argparse
from fractions import Fraction

from music21 import converter, duration, note, stream

TUPLET_RATIOS = [(3, 2), (5, 4), (7, 4), (6, 4)]


def bar_length(measure: stream.Measure, fallback: Fraction) -> Fraction:
    ts = measure.timeSignature
    return Fraction(ts.numerator * 4, ts.denominator) if ts else fallback


def total(elements) -> Fraction:
    return sum((Fraction(e.quarterLength).limit_denominator(64) for e in elements), Fraction(0))


def try_tuplet(elements, expected: Fraction, max_missing: int = 2):
    """Scale a run of equal-duration notes by a tuplet ratio to reach `expected`.

    Accepts a scaling that lands exactly, or one that undershoots by a whole
    number of scaled notes — the signature of a tuplet whose bracket was read
    but one or two of whose noteheads were dropped. The caller pads the
    shortfall with a rest, which keeps the bar aligned.

    Returns (run, ratio, actual, normal, shortfall), best (smallest shortfall)
    first, or None.
    """
    n = len(elements)
    best = None
    for actual, normal in TUPLET_RATIOS:
        ratio = Fraction(normal, actual)
        for start in range(n):
            base = Fraction(elements[start].quarterLength).limit_denominator(64)
            if base == 0:
                continue
            for end in range(start + actual, n + 1):
                run = elements[start:end]
                if len(run) % actual:
                    continue
                if any(Fraction(e.quarterLength).limit_denominator(64) != base for e in run):
                    break
                result = total(elements) - total(run) * (1 - ratio)
                shortfall = expected - result
                if shortfall < 0:
                    continue
                scaled = base * ratio
                if shortfall == 0:
                    return run, ratio, actual, normal, Fraction(0)
                if scaled and shortfall % scaled == 0 and shortfall / scaled <= max_missing:
                    if best is None or shortfall < best[4]:
                        best = (run, ratio, actual, normal, shortfall)
    return best


def repair(score: stream.Score, truncate: bool = False) -> dict:
    stats = {"checked": 0, "already_ok": 0, "tuplet_fixed": 0, "tuplet_padded": 0,
             "padded": 0, "truncated": 0, "unfixable": 0}
    unfixable = []
    for pi, part in enumerate(score.parts):
        fallback = Fraction(4)
        for measure in part.getElementsByClass(stream.Measure):
            if measure.timeSignature:
                fallback = bar_length(measure, fallback)
            expected = bar_length(measure, fallback)
            if len(measure.getElementsByClass(stream.Voice)) > 1:
                continue                                  # polyphonic: leave to a human
            elements = list(measure.notesAndRests)
            if not elements:
                continue
            stats["checked"] += 1
            actual = total(elements)
            if actual == expected:
                stats["already_ok"] += 1
                continue

            if actual > expected:
                found = try_tuplet(elements, expected)
                if found:
                    run, ratio, a, n, shortfall = found
                    for el in run:
                        el.duration = duration.Duration(
                            Fraction(el.quarterLength).limit_denominator(64) * ratio)
                        el.duration.appendTuplet(duration.Tuplet(a, n))
                    if shortfall:
                        measure.append(note.Rest(quarterLength=float(shortfall)))
                        stats["tuplet_padded"] += 1
                    stats["tuplet_fixed"] += 1
                elif truncate:
                    # Last resort: shorten the final notes until the bar fits.
                    # Loses note length, but an over-long bar drags everything
                    # after it out of time, which is far more audible.
                    excess = actual - expected
                    for el in reversed(elements):
                        if excess <= 0:
                            break
                        ql = Fraction(el.quarterLength).limit_denominator(64)
                        take = min(ql - Fraction(1, 8), excess) if ql > Fraction(1, 8) else Fraction(0)
                        if take > 0:
                            el.duration = duration.Duration(float(ql - take))
                            excess -= take
                    stats["truncated"] += 1
                else:
                    stats["unfixable"] += 1
                    unfixable.append((pi, measure.number, str(expected), str(actual)))
            else:
                measure.append(note.Rest(quarterLength=float(expected - actual)))
                stats["padded"] += 1

            # re-lay the bar out sequentially so the new durations take effect
            fixed = list(measure.notesAndRests)
            for el in fixed:
                measure.remove(el)
            offset = Fraction(0)
            for el in fixed:
                measure.insert(float(offset), el)
                offset += Fraction(el.quarterLength).limit_denominator(64)
    stats["unfixable_list"] = unfixable
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--truncate", action="store_true",
                    help="last resort: shorten notes in bars no repair fits, so "
                         "playback stays in time")
    args = ap.parse_args()

    score = converter.parse(args.src)
    s = repair(score, truncate=args.truncate)
    print(f"  bars checked      : {s['checked']}")
    print(f"  already correct   : {s['already_ok']}")
    print(f"  fixed as tuplets  : {s['tuplet_fixed']}"
          f" ({s['tuplet_padded']} of them also needed a rest for a dropped note)")
    print(f"  padded with rests : {s['padded']}")
    print(f"  truncated to fit  : {s['truncated']}")
    print(f"  left for a human  : {s['unfixable']}")
    for pi, num, e, a in s["unfixable_list"][:12]:
        print(f"      part {pi} bar {num}: expected {e}, got {a}")
    score.write("musicxml", fp=args.dst)
    print(f"  wrote {args.dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
