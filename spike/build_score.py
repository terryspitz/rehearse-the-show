#!/usr/bin/env python3
"""Build the final lbal-score.json for the in-browser synth player.

Combines:
  - solo/tenor/bass notes + lyrics + lines, extracted from the pre-merge
    Audiveris parse of the vocal book (rt.musicxml -- 21 raw per-system
    parts sharing one timeline; see extract_vocal_data.py's module docstring
    for why this supersedes licensed/vocal-midi-v3).
  - piano notes + real 190-bar measure structure, from the clean piano MXL.
  - vocal-to-piano alignment knots, from align_scores.py's anchor matching.

Departure from the original plan: parts carry an embedded `notes[]` array
(quarter, duration, pitch, velocity) instead of a `midiFile` reference --
the browser scheduler needs a note list either way, and generating one
directly here avoids needing any MIDI-byte parser in JS at all. Simpler to
implement, test, and debug than round-tripping through a binary format.

Usage:
    python spike/build_score.py --out licensed/vocal-raw/lbal-score.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from music21 import converter, stream

from align_scores import anchors, match_sequence, bar_map

BASE = Path(__file__).resolve().parent.parent
VOCAL_XML = BASE / "licensed/vocal-raw/rt.musicxml"
PIANO_XML = BASE / "licensed/piano/e5db4df6-Luck_be_a_lady_piano_score_only.mxl"

PROGRAM = {"solo": 53, "tenor": 52, "bass": 52, "piano": 0}
PAN = {"solo": -0.35, "tenor": 0.15, "bass": 0.5, "piano": 0.0}
LABEL = {"solo": "Sky (solo)", "tenor": "Crapshooters — Tenor",
         "bass": "Crapshooters — Bass", "piano": "Piano"}
WHO = {"solo": "Solo line", "tenor": "Ensemble line", "bass": "Ensemble line",
       "piano": "Accompaniment"}
CHANNEL = {"solo": 0, "tenor": 1, "bass": 2, "piano": 3}


def classify_vocal_staff(part: stream.Part) -> str:
    name = (part.partName or "").strip()
    if name == "Voice":
        return "solo"
    clefs = {c.name for c in part.flatten().getElementsByClass("Clef")}
    return "bass" if "bass" in clefs and "treble" not in clefs else "tenor"


def notes_to_json(notes: list[tuple[float, object]]) -> list[dict]:
    out = []
    for offset, n in notes:
        pitches = n.pitches if hasattr(n, "pitches") else [n.pitch]
        for pit in pitches:
            out.append({
                "quarter": round(offset, 4),
                "duration": round(float(n.quarterLength), 4),
                "pitch": pit.midi,
                "velocity": int(n.volume.velocity) if n.volume.velocity else 80,
            })
    out.sort(key=lambda x: x["quarter"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    vocal_sc = converter.parse(str(VOCAL_XML))
    piano_sc = converter.parse(str(PIANO_XML))

    # ---- vocal: classify raw staves, collect notes+lyrics on the shared timeline ----
    group_notes: dict[str, list[tuple[float, object]]] = {"solo": [], "tenor": [], "bass": []}
    lyric_tuples = []
    raw_parts_out = []

    for i, part in enumerate(vocal_sc.parts):
        group = classify_vocal_staff(part)
        notes = list(part.flatten().notes)
        for n in notes:
            group_notes[group].append((float(n.offset), n))
            if group == "solo":
                for ly in n.lyrics:
                    lyric_tuples.append((float(n.offset), ly.text or "", ly.syllabic or "single"))
        raw_parts_out.append({
            "staffId": f"p{i}",
            "partName": part.partName,
            "assignedTo": group,
            "noteCount": len(notes),
            "notes": notes_to_json([(float(n.offset), n) for n in notes]),
        })

    lyric_tuples.sort(key=lambda t: t[0])
    lyrics = [{"quarter": round(q, 4), "text": t, "syllabic": s} for q, t, s in lyric_tuples]

    lines = []
    cur = {"lyricStart": 0, "text": ""}
    for idx, ly in enumerate(lyrics):
        sep = "" if ly["syllabic"] in ("middle", "end") else (" " if cur["text"] else "")
        cur["text"] += sep + ly["text"]
        ends_line = ly["syllabic"] in ("single", "end") and any(ch in ly["text"] for ch in ".!?,")
        if ends_line or idx == len(lyrics) - 1:
            cur["lyricEnd"] = idx
            cur["quarter"] = lyrics[cur["lyricStart"]]["quarter"]
            cur["confirmed"] = False
            cur["id"] = len(lines)
            lines.append(cur)
            cur = {"lyricStart": idx + 1, "text": ""}

    for i, ly in enumerate(lyrics):
        ly["lineId"] = next((ln["id"] for ln in lines if ln["lyricStart"] <= i <= ln["lyricEnd"]), None)
    for ln in lines:
        ln["text"] = ln["text"].strip()

    # ---- piano: real measure structure + notes ----
    p_piano = piano_sc.parts[0]
    measures = list(p_piano.getElementsByClass(stream.Measure))
    cur_ts, piano_measures = None, []
    for m in measures:
        if m.timeSignature is not None:
            cur_ts = m.timeSignature
        beats = cur_ts.numerator if cur_ts and cur_ts.denominator in (2, 4) else (cur_ts.beatCount if cur_ts else 4)
        piano_measures.append({"quarter": round(float(m.offset), 4), "beats": int(beats)})

    piano_notes = []
    for part in piano_sc.parts:
        for n in part.flatten().notes:
            piano_notes.append((float(n.offset), n))

    # ---- vocal <-> piano alignment knots ----
    v_anchors, v_bars = anchors(vocal_sc)
    p_anchors, p_bars = anchors(piano_sc)
    pairs = match_sequence(v_anchors, p_anchors)
    bar_knots = bar_map(pairs, v_bars, p_bars)

    vocal_bar_offsets = [float(m.offset) for m in vocal_sc.parts[0].getElementsByClass(stream.Measure)]
    piano_bar_offsets = [m["quarter"] for m in piano_measures]
    quarter_knots = [
        [round(vocal_bar_offsets[min(v, len(vocal_bar_offsets) - 1)], 4),
         round(piano_bar_offsets[min(p, len(piano_bar_offsets) - 1)], 4)]
        for v, p in bar_knots
    ]

    # brightly's line anchor: first line whose quarter is >= the "brightly" vocal-bar quarter
    brightly_vocal_bar = 21  # matches licensed/drive-upload/lbal-config.json's sections[1].vocalBar
    brightly_q = vocal_bar_offsets[brightly_vocal_bar]
    brightly_line = next((ln["id"] for ln in lines if ln["quarter"] >= brightly_q), lines[-1]["id"])

    parts = []
    for gid, notes in {**group_notes, "piano": piano_notes}.items():
        parts.append({
            "id": gid, "label": LABEL[gid], "who": WHO[gid], "hue": f"var(--p-{gid[0]})",
            "pan": PAN[gid], "midiProgram": PROGRAM[gid], "midiChannel": CHANNEL[gid],
            "notes": notes_to_json(notes),
        })

    score = {
        "title": "Luck Be A Lady",
        "show": "Guys and Dolls",
        "composer": "Frank Loesser",
        "measures": piano_measures,
        "lyrics": lyrics,
        "lines": lines,
        "sections": [
            {"id": "freely", "label": "Freely & Dramatically", "lineAnchor": 0, "bar": 0,
             "bpm": 60, "bpmIsOverride": False},
            {"id": "brightly", "label": "Brightly", "lineAnchor": brightly_line, "bar": 22,
             "bpm": 150, "bpmIsOverride": False},
        ],
        "vocalAlignment": {
            "description": "Piecewise map, vocal-quarter -> piano-quarter. Admin-editable; applied live by the scheduler.",
            "knots": quarter_knots,
        },
        "parts": parts,
        "rawParts": [{"staffId": r["staffId"], "partName": r["partName"], "assignedTo": r["assignedTo"],
                       "noteCount": r["noteCount"], "notes": r["notes"]} for r in raw_parts_out],
        "notes": {
            "tempo": "Freely & Dramatically ~60bpm, Brightly ~150bpm are starting defaults (checked against reference recordings), not transcribed facts -- admin-adjustable live.",
            "sync": "vocalAlignment is a piecewise map seeded from real key/meter-change anchors shared by both scans (spike/align_scores.py) -- a good starting approximation, admin-correctable by ear.",
            "lyrics": "Solo (Sky) line only, from the pre-merge OMR parse. Line groupings are a naive first pass (break on sentence-ending punctuation) -- confirmed:false until an admin reviews each one. Known OCR noise remains -- see docs/vocal-midi-accuracy.md.",
            "rawParts": "One entry per original OMR staff (pre-merge); assignedTo is a first-guess grouping by clef+label, admin-correctable via the part-merge editor.",
        },
        "sourceRepo": "https://github.com/terryspitz/rehearse-the-show",
        "sourceBranch": "claude/midi-synth-admin",
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(score, indent=2, ensure_ascii=False))
    print(f"wrote {out_path} ({out_path.stat().st_size} bytes)")
    print(f"  lyrics={len(lyrics)} lines={len(lines)} measures={len(piano_measures)} "
          f"rawParts={len(raw_parts_out)} brightly_line={brightly_line}")
    for p in parts:
        print(f"  part {p['id']}: {len(p['notes'])} notes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
