#!/usr/bin/env python3
"""Spike: MusicXML -> per-part MIDI + rehearsal metadata.

This is the second half of the pipeline (after OMR produces MusicXML). It proves
the bit the player depends on: that a score can be split into independently
mixable parts, and that lyrics/beats/measures can be exported as a timeline the
browser can follow.

Usage:
    python spike/score_to_parts.py <score.musicxml|corpus-path> -o out/
    python spike/score_to_parts.py bach/bwv66.6 -o out/bwv66      # music21 corpus

Outputs, in <out>/:
    parts/<n>-<slug>.mid   one MIDI file per part (soprano, alto, ..., piano)
    mix.mid                the whole score, one channel per part
    score.json             part manifest + measure/beat map + lyric timeline
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from music21 import converter, corpus, instrument, midi, stream, tempo

# Heuristics for guessing which mixer group a part belongs to. Musical theatre
# vocal scores rarely label parts cleanly, so this is a best guess the user can
# override in the UI.
VOICE_PATTERNS = [
    ("soprano", r"\bsop(rano)?\b|\bs\.?\b|\bdescant\b"),
    ("alto", r"\balto?\b|\bcontralto\b|\ba\.?\b|\bmezzo\b"),
    ("tenor", r"\bten(or)?\b|\bt\.?\b"),
    ("bass", r"\bbass?\b|\bbaritone\b|\bb\.?\b"),
]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "part"


def classify(part: stream.Part, index: int) -> tuple[str, str]:
    """Return (display_name, group) for a part."""
    name = (part.partName or part.id or f"Part {index + 1}").strip()
    haystack = f"{name} {part.partAbbreviation or ''}".lower()

    for group, pattern in VOICE_PATTERNS:
        if re.search(pattern, haystack):
            return name, group

    inst = part.getInstrument(returnDefault=True)
    if isinstance(inst, instrument.Vocalist) or part.flatten().getElementsByClass("Lyric"):
        return name, "voice"
    if part.flatten().notes and any(n.lyric for n in part.flatten().notes):
        return name, "voice"
    return name, "instrument"


def beat_map(score: stream.Score) -> list[dict]:
    """Measure-by-measure map: offset in quarter notes, seconds, tempo, beats."""
    flat = score.flatten()
    marks = [(float(mm.offset), mm.getQuarterBPM()) for mm in flat.getElementsByClass(tempo.MetronomeMark)]
    if not marks or marks[0][0] > 0:
        marks.insert(0, (0.0, 120.0))

    def seconds_at(q: float) -> float:
        secs, prev_q, bpm = 0.0, 0.0, marks[0][1]
        for mark_q, mark_bpm in marks:
            if mark_q >= q:
                break
            secs += (mark_q - prev_q) * 60.0 / bpm
            prev_q, bpm = mark_q, mark_bpm
        return secs + (q - prev_q) * 60.0 / bpm

    measures = []
    top = score.parts[0] if score.parts else score
    for m in top.getElementsByClass(stream.Measure):
        ts = m.timeSignature or m.getContextByClass("TimeSignature")
        measures.append(
            {
                "number": m.number,
                "quarter": float(m.offset),
                "seconds": round(seconds_at(float(m.offset)), 4),
                "beats": ts.numerator if ts else 4,
                "beatUnit": ts.denominator if ts else 4,
            }
        )
    return measures


def lyric_timeline(part: stream.Part, seconds_at) -> list[dict]:
    events = []
    for n in part.flatten().notes:
        if not n.lyric:
            continue
        events.append(
            {
                "quarter": round(float(n.getOffsetInHierarchy(part)), 4),
                "seconds": round(seconds_at(float(n.getOffsetInHierarchy(part))), 4),
                "text": n.lyric,
                "syllabic": getattr(n.lyrics[0], "syllabic", None) if n.lyrics else None,
            }
        )
    return events


def write_part_midi(part: stream.Part, path: Path) -> None:
    holder = stream.Score()
    holder.insert(0, part)
    mf = midi.translate.streamToMidiFile(holder)
    mf.open(str(path), "wb")
    mf.write()
    mf.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("score", help="path to MusicXML/MIDI, or a music21 corpus path")
    ap.add_argument("-o", "--out", default="out", help="output directory")
    args = ap.parse_args()

    src = Path(args.score)
    score = converter.parse(str(src)) if src.exists() else corpus.parse(args.score)
    score = score.expandRepeats() if score.recurse().getElementsByClass("RepeatMark") else score

    out = Path(args.out)
    (out / "parts").mkdir(parents=True, exist_ok=True)

    measures = beat_map(score)

    def seconds_at(q: float) -> float:
        prev = measures[0] if measures else {"quarter": 0.0, "seconds": 0.0}
        for m in measures:
            if m["quarter"] > q:
                break
            prev = m
        # linear within the measure at the measure's local tempo
        rate = 0.5
        if len(measures) > 1 and prev is not measures[-1]:
            nxt = measures[measures.index(prev) + 1]
            span_q = nxt["quarter"] - prev["quarter"]
            if span_q:
                rate = (nxt["seconds"] - prev["seconds"]) / span_q
        return prev["seconds"] + (q - prev["quarter"]) * rate

    manifest = []
    for i, part in enumerate(score.parts):
        name, group = classify(part, i)
        slug = f"{i:02d}-{slugify(name)}"
        write_part_midi(part, out / "parts" / f"{slug}.mid")
        inst = part.getInstrument(returnDefault=True)
        manifest.append(
            {
                "id": slug,
                "name": name,
                "group": group,
                "midiProgram": inst.midiProgram if inst.midiProgram is not None else 0,
                "midiFile": f"parts/{slug}.mid",
                "lyrics": lyric_timeline(part, seconds_at),
            }
        )

    mf = midi.translate.streamToMidiFile(score)
    mf.open(str(out / "mix.mid"), "wb")
    mf.write()
    mf.close()

    doc = {
        "title": (md.title or md.movementName if (md := score.metadata) else None) or src.stem,
        "composer": (score.metadata.composer if score.metadata else None),
        "durationSeconds": round(seconds_at(float(score.highestTime)), 3),
        "measures": measures,
        "parts": manifest,
    }
    (out / "score.json").write_text(json.dumps(doc, indent=2))

    print(f"{doc['title']}: {len(manifest)} parts, {len(measures)} measures -> {out}")
    for p in manifest:
        print(f"  {p['id']:<24} group={p['group']:<10} lyrics={len(p['lyrics'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
