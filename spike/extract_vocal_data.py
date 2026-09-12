#!/usr/bin/env python3
"""Extract lyrics, singable lines, and raw per-staff MIDI from the pre-merge
Audiveris parse of the vocal book (rt.musicxml — 21 raw per-system parts).

IMPORTANT: all 21 parts share ONE common timeline (verified: every part's
highestTime lands around quarter 704-712, and note offsets between
same-labeled "Voice" fragments never collide at the same offset despite
overlapping ranges) — they are parallel/complementary staves, not sequential
fragments to be concatenated end-to-end. This script uses each note's real
`.offset` directly.

This lyric timeline is NOT the same clock as the already-shipped
licensed/vocal-midi-v3/*.mid files (a separately reprocessed export that
lost the original bar structure — flat 120bpm/4/4, ~696 quarters total vs.
rt.musicxml's ~712). This script does NOT attempt to regenerate merged
solo/tenor/bass MIDI from these raw staves — vocal-midi-v3 stays the
authoritative note data for playback. Reconciling the two timelines (so a
lyric quarter-offset here points at the right moment in vocal-midi-v3
playback) is a separate alignment step, not solved here — flagged in the
output's `notes` field rather than silently assumed correct.

Group heuristic (matches the one described in licensed/drive-upload's
lbal-config.json, since the original merge_parts.py that produced the
already-shipped vocals-*.mid files no longer exists as a file):
  - partName == "Voice" (no OCR'd label survived)      -> solo
  - otherwise, bass clef                                -> bass
  - otherwise (treble clef, an OCR'd label present)     -> tenor
This is a first guess for `rawParts[].assignedTo`; the admin part-merge
editor is where a human corrects it if wrong.

Outputs (into --out-dir):
  lyrics.json        - [{quarter, text, syllabic}], solo line only, sorted
                        by real offset across all solo-classified parts
  lines.json         - naive line grouping (break on end-of-sentence
                        punctuation) — admin-confirmable, not final
  raw-parts.json     - metadata for each of the 21 original staves
  raw/staff-NN.mid   - one MIDI file per original staff (unmerged), using
                       each staff's own real offsets
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from music21 import converter, stream, instrument


def classify(part: stream.Part) -> str:
    name = (part.partName or "").strip()
    if name == "Voice":
        return "solo"
    clefs = {c.name for c in part.flatten().getElementsByClass("Clef")}
    return "bass" if "bass" in clefs and "treble" not in clefs else "tenor"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("musicxml")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out = Path(args.out_dir)
    (out / "raw").mkdir(parents=True, exist_ok=True)

    sc = converter.parse(args.musicxml)
    raw_parts = []
    lyric_tuples = []  # (offset, text, syllabic)
    group_notes = {"solo": [], "tenor": [], "bass": []}  # (offset, note) across all parts

    for i, part in enumerate(sc.parts):
        group = classify(part)
        notes = list(part.flatten().notes)
        dur = float(part.highestTime)

        staff_id = f"p{i}"
        holder = stream.Score()
        inst = instrument.Instrument()
        inst.midiProgram = {"solo": 53, "tenor": 52, "bass": 52}[group]
        p_out = stream.Part()
        p_out.insert(0, inst)
        for n in notes:
            p_out.insert(n.offset, n)
        midi_path = out / "raw" / f"staff-{staff_id}.mid"
        holder.insert(0, p_out)
        holder.write("midi", fp=str(midi_path))

        if group == "solo":
            for n in notes:
                for ly in n.lyrics:
                    lyric_tuples.append((float(n.offset), ly.text or "", ly.syllabic or "single"))

        for n in notes:
            group_notes[group].append((float(n.offset), n))

        raw_parts.append({
            "staffId": staff_id,
            "partName": part.partName,
            "midiFile": f"raw/staff-{staff_id}.mid",
            "noteCount": len(notes),
            "lyricCount": sum(1 for n in notes if n.lyrics),
            "assignedTo": group,
            "offsetRange": [round(min((float(n.offset) for n in notes), default=0), 2),
                            round(max((float(n.offset) for n in notes), default=0), 2)],
            "quarterLength": round(dur, 4),
        })

    # Merged group MIDI, built from real offsets across all raw staves in that
    # group (verified zero exact-offset collisions between same-labeled
    # fragments) — supersedes licensed/vocal-midi-v3, whose export process
    # silently compressed some inter-phrase rests, drifting its timeline away
    # from the lyrics' real one. This way notes and lyrics share one clock by
    # construction.
    program = {"solo": 53, "tenor": 52, "bass": 52}
    for group, pairs in group_notes.items():
        holder = stream.Score()
        inst = instrument.Instrument()
        inst.midiProgram = program[group]
        p_out = stream.Part()
        p_out.insert(0, inst)
        for offset, n in pairs:
            p_out.insert(offset, n)
        holder.insert(0, p_out)
        holder.write("midi", fp=str(out / f"vocals-{group}.mid"))
        print(f"{group}: {len(pairs)} notes -> vocals-{group}.mid")

    lyric_tuples.sort(key=lambda t: t[0])
    lyrics = [{"quarter": round(q, 4), "text": t, "syllabic": s} for q, t, s in lyric_tuples]
    print("solo lyric syllables:", len(lyrics))

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

    (out / "lyrics.json").write_text(json.dumps(lyrics, indent=2))
    (out / "lines.json").write_text(json.dumps(lines, indent=2))
    (out / "raw-parts.json").write_text(json.dumps(raw_parts, indent=2))
    print(f"wrote {len(lyrics)} lyrics, {len(lines)} lines, {len(raw_parts)} raw parts to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
