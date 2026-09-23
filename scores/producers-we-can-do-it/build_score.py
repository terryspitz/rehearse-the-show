#!/usr/bin/env python3
"""Hand transcription: "We Can Do It!" (The Producers) -> MusicXML.

Source: an 8-page piano/conductor excerpt (mm.6-91, "#5 We Can Do It! [r 4/02]",
Miller Music Service) covering the Max/Leo underscored dialogue scene and the
"We Can Do It!" hook and its reprises. The scan has no page for mm.1-5, and the
excerpt itself ends mid-phrase at m.91 ("I can't...") - that is where the
source PDF stops, not a transcription cutoff.

There is no reliable automated OMR path for a score this dense (see
docs/research-libraries.md #2) so this was transcribed by eye from the scan.
Two confidence tiers:

  - Vocal line + lyrics: transcribed note-by-note from the vocal staff. This is
    the part that matters for rehearsal and is the most carefully read.
  - Piano part: the source is actually a 2-stave conductor's reduction with
    cues for strings/brass/winds/timp etc, not a piano part. Reproducing every
    orchestral ornament (grace-note runs, tremoli, glissandi) note-for-note
    isn't meaningful on a piano, so this is a harmonic reduction -- bass note
    + comping chord at the harmonic rhythm implied by the two staves -- rather
    than a literal transcription of every notehead.

Treat this like any OMR output: a first-pass draft to check against the score,
not a guaranteed-accurate performance edition.

Run:
    python build_score.py                    # writes we-can-do-it.musicxml
    python ../../spike/score_to_parts.py we-can-do-it.musicxml -o build/
"""

from __future__ import annotations

from music21 import chord, clef, instrument, key, metadata, meter, note, stream, tempo

# The scan is missing its first page; the excerpt starts at m.6 of the cue.
FIRST_MEASURE = 6

# Rough BPM per marked tempo change ("A tempo, Slow 4" / "Slow 2" / Leo's closing
# patter) -- the score gives no metronome numbers, so these are reasonable
# guesses for a rehearsal tempo, not the show's actual tempo. Adjust freely.
TEMPO_CHANGES = {6: 88, 17: 104, 82: 136}

VOCAL_MEASURES: list[tuple[str | None, list[tuple[str | None, float, str | None]]]] = [
    # (time signature if it changes this measure, [(pitch or None=rest, quarterLength, lyric)])
    # --- mm 6-8: "A tempo, Slow 4" -- spoken dialogue over underscore, nobody sings ---
    ("4/4", [(None, 4.0, None)]),
    (None, [(None, 4.0, None)]),
    (None, [(None, 4.0, None)]),
    # --- mm 9-10: Max, patter verse 1 (Lewis & Clark) ---
    (None, [(None, 1.0, None), ("Bb4", 0.25, "What"), ("Bb4", 0.25, "did"), ("Bb4", 0.25, "Lew-"), ("Bb4", 0.25, "-is"),
             ("Bb4", 0.25, "say"), ("Bb4", 0.25, "to"), ("Bb4", 0.5, "Clark"), ("Bb4", 1.0, "when")]),
    (None, [("Bb4", 0.25, "ev-"), ("Bb4", 0.25, "-'ry-"), ("C5", 0.25, "-thing"), ("D5", 0.25, "looked"),
             ("C5", 2.0, "bleak?"), (None, 1.0, None)]),
    # --- mm 11-12: patter verse 2 (Hillary & Tenzing) ---
    (None, [("Bb4", 0.25, "What"), ("Bb4", 0.25, "did"), ("Bb4", 0.25, "Sir"), ("Bb4", 0.25, "Ed-"),
             ("Bb4", 0.25, "-mund"), ("Bb4", 0.25, "say"), ("Bb4", 0.25, "to"), ("Bb4", 0.25, "Ten-"),
             ("Bb4", 0.25, "-zing"), ("Bb4", 0.25, "as"), ("Bb4", 0.25, "they"), ("Bb4", 0.25, "strug-"),
             ("Bb4", 0.25, "-gled"), ("Bb4", 0.25, "t'ward"), ("C5", 0.25, "Ev-"), ("D5", 0.25, "-er-")]),
    (None, [("C5", 1.0, "-est's"), ("D5", 2.0, "peak?"), (None, 1.0, None)]),
    # --- mm 13-14: patter verse 3 (Washington), explicit triplets + meter change ---
    ("7/4", [("Bb4", 1.0, "What"), ("Bb4", 1 / 3, "did"), ("Bb4", 1 / 3, "Wash-"), ("Bb4", 1 / 3, "-ing-"),
              ("Bb4", 1 / 3, "-ton"), ("Bb4", 1 / 3, "say"), ("Bb4", 1 / 3, "to"), ("Bb4", 1.0, "his"),
              ("Bb4", 1.0, "troops"), ("C5", 0.5, "as"), ("D5", 1.5, "they")]),
    ("4/4", [("C5", 2.0, "crossed"), ("Bb4", 0.5, "the"), ("Bb4", 0.5, "Del-"), ("C5", 0.5, "-a-"), ("D5", 0.5, "-ware?")]),
    # --- mm 15-16: punchline, Leo speaks (not sung), Max pickup ---
    (None, [(None, 0.5, None), ("C5", 0.5, "I'm"), ("Bb4", 1.0, "sure"), ("Bb4", 0.5, "you're"),
             ("Ab4", 0.5, "well"), ("G4", 0.5, "a-"), ("F4", 0.5, "-ware!")]),
    (None, [(None, 3.0, None), ("C5", 0.5, "We"), ("D5", 0.5, "can")]),
    # --- mm 17-32: "Slow 2" -- the "We Can Do It!" hook, F major, 2/4 ---
    ("2/4", [("F5", 0.5, "do"), ("D5", 1.5, "it!")]),
    (None, [("C5", 0.5, "We"), (None, 0.5, None), ("D5", 0.5, "can"), (None, 0.5, None)]),
    (None, [("F5", 0.5, "do"), ("D5", 1.5, "it!")]),
    (None, [("C5", 0.5, "We"), (None, 0.5, None), ("D5", 0.5, "can"), (None, 0.5, None)]),
    (None, [("F5", 1.0, "do"), ("D5", 1.0, "it,")]),
    (None, [("C5", 1.0, "me"), ("Bb4", 1.0, "and")]),
    (None, [("F4", 2.0, "you!")]),
    (None, [("C5", 0.5, "We"), (None, 0.5, None), ("D5", 0.5, "can"), (None, 0.5, None)]),
    (None, [("F5", 0.5, "do"), ("D5", 1.5, "it!")]),
    (None, [("C5", 0.5, "We"), (None, 0.5, None), ("D5", 0.5, "can"), (None, 0.5, None)]),
    (None, [("F5", 0.5, "do"), ("D5", 1.5, "it!")]),
    (None, [("C5", 0.5, "We"), (None, 0.5, None), ("D5", 0.5, "can"), (None, 0.5, None)]),
    (None, [("F5", 1.0, "make"), ("D5", 1.0, "our")]),
    (None, [("C5", 1.0, "dreams"), ("Bb4", 1.0, "come")]),
    (None, [("F4", 2.0, "true!")]),
    (None, [(None, 1.0, None), ("C5", 0.5, "Ev'-"), ("D5", 0.5, "-ry-")]),
    # --- mm 33-40: "A tempo" verse, still 2/4 ---
    (None, [("F5", 1.0, "-thing"), ("D5", 1.0, "you've")]),
    (None, [("C5", 1.0, "ev-"), ("Bb4", 1.0, "-er")]),
    (None, [("A4", 1.0, "want-"), ("Bb4", 1.0, "-ed")]),
    (None, [("C5", 1.0, "is"), ("D5", 1.0, "just")]),
    (None, [("F5", 1.0, "wait-"), ("D5", 1.0, "-ing")]),
    (None, [("C5", 1.0, "to"), ("Bb4", 1.0, "be")]),
    (None, [("A4", 2.0, "had")]),
    (None, [("A4", 1.0, None), (None, 1.0, None)]),
    # --- mm 41-44: bridge ---
    (None, [("F5", 0.5, "Beau-"), ("E5", 0.5, "-ti-"), ("D5", 0.5, "-ful"), ("C5", 0.5, "girls")]),
    (None, [("C5", 0.5, None), (None, 0.5, None), ("D5", 0.5, "wear-"), ("C5", 0.5, "-ing")]),
    (None, [("D5", 0.5, "no-"), ("C5", 0.5, "-thing"), ("D5", 0.5, "but"), ("E5", 0.5, "pearls")]),
    (None, [("E5", 0.5, None), (None, 0.5, None), ("D5", 0.5, "Ca-"), (None, 0.5, None)]),
    # --- mm 45-48 ---
    (None, [("C5", 0.5, "-ress-"), ("Bb4", 0.5, "-ing"), ("A4", 0.5, "you"), ("G4", 0.5, "un-")]),
    (None, [("A4", 0.5, "-dress-"), ("Bb4", 0.5, "-ing"), ("C5", 0.5, "you"), ("D5", 0.5, "and")]),
    (None, [("F5", 0.5, "driv-"), ("Eb5", 0.5, "-ing"), ("D5", 0.5, "you"), ("C5", 0.5, "mad!")]),
    (None, [(None, 1.0, None), ("C5", 0.5, "We"), ("D5", 0.5, "can")]),
    # --- mm 49-52 ---
    (None, [("F5", 0.5, "do"), ("D5", 1.5, "it!")]),
    (None, [("C5", 0.5, "We"), (None, 0.5, None), ("D5", 0.5, "can"), (None, 0.5, None)]),
    (None, [("F5", 0.5, "do"), ("D5", 1.5, "it!")]),
    (None, [("C5", 0.5, "This"), (None, 0.5, None), ("D5", 0.5, "is"), (None, 0.5, None)]),
    # --- mm 53-56 ---
    (None, [("D5", 1.0, "not"), ("C5", 1.0, "the")]),
    (None, [("Bb4", 1.0, "time"), ("A4", 1.0, "to")]),
    (None, [("F4", 1.0, "shirk!"), (None, 1.0, None)]),
    (None, [(None, 0.5, None), ("C5", 0.5, "We"), (None, 0.5, None), ("D5", 0.5, "can")]),
    # --- mm 57-60 ---
    (None, [("F5", 0.5, "do"), ("D5", 1.5, "it!")]),
    (None, [("C5", 0.5, "You"), ("Bb4", 1.5, "won't")]),
    (None, [("A4", 0.5, "rue"), ("G4", 1.5, "it")]),
    (None, [(None, 1.0, None), ("Bb4", 0.5, "say"), ("C5", 0.5, '"good-')]),
    # --- mm 61-64 ---
    (None, [("D5", 1.0, "-bye\""), ("C5", 1.0, "to")]),
    (None, [("Bb4", 1.0, "pet-"), ("A4", 1.0, "-ty")]),
    (None, [("F4", 2.0, "clerk!")]),
    (None, [(None, 0.5, None), ("C5", 0.5, "Hi,"), (None, 0.5, None), ("D5", 0.5, "pro-")]),
    # --- mm 65-68 ---
    (None, [("F5", 0.5, "-du-"), ("D5", 1.5, "-cer!")]),
    (None, [("C5", 1.0, "Yes"), ("Bb4", 1.0, "pro-")]),
    (None, [("A4", 1.0, "-du-"), ("F4", 1.0, "-cer!")]),
    (None, [(None, 0.5, None), ("C5", 0.5, "I"), (None, 0.5, None), ("D5", 0.5, "mean")]),
    # --- mm 69-72 ---
    (None, [("D5", 1.0, "you"), ("C5", 1.0, "sir,")]),
    (None, [("Bb4", 1.0, "go"), ("A4", 1.0, "be-")]),
    (None, [("F4", 2.0, "-serk!")]),
    (None, [(None, 0.5, None), ("C5", 0.5, "We"), (None, 0.5, None), ("D5", 0.5, "can")]),
    # --- mm 73-76 ---
    (None, [("F5", 0.5, "do"), ("D5", 1.5, "it!")]),
    (None, [("C5", 0.5, "We"), (None, 0.5, None), ("D5", 0.5, "can"), (None, 0.5, None)]),
    (None, [("F5", 0.5, "do"), ("D5", 1.5, "it!")]),
    (None, [(None, 1.0, None), ("C5", 0.5, "And"), ("D5", 0.5, "I")]),
    # --- mm 77-81 ---
    (None, [("F5", 2.0, "know")]),
    (None, [("Eb5", 2.0, "it's")]),
    (None, [("D5", 2.0, "gon-")]),
    (None, [("C5", 2.0, "-na")]),
    (None, [("Bb4", 1.0, "work!"), (None, 1.0, None)]),
    # --- mm 82-84: Leo, 4/4, patter again ---
    ("4/4", [("Bb4", 1.0, "What"), ("Bb4", 1.0, "do"), ("Bb4", 1.0, "I"), ("Bb4", 1.0, "say?")]),
    (None, [("Bb4", 1 / 3, "Fin-"), ("Bb4", 1 / 3, "'lly"), ("Bb4", 1 / 3, "a"), ("Bb4", 1 / 3, "chance"),
             ("Bb4", 1 / 3, "to"), ("Bb4", 1 / 3, "be"), ("Bb4", 1 / 3, "a"), ("Bb4", 1 / 3, "Broad-"),
             ("Bb4", 1 / 3, "-way"), ("C5", 1.0, "pro-")]),
    (None, [("D5", 2.0, "-du-cer"), (None, 2.0, None)]),
    # --- mm 85-87 ---
    (None, [("Bb4", 1.0, "What"), ("Bb4", 1.0, "do"), ("Bb4", 1.0, "I"), ("Bb4", 1.0, "say?")]),
    (None, [("Bb4", 1 / 3, "Fin-"), ("Bb4", 1 / 3, "'lly"), ("Bb4", 1 / 3, "a"), ("Bb4", 1 / 3, "chance"),
             ("Bb4", 1 / 3, "to"), ("Bb4", 1 / 3, "make"), ("Bb4", 1 / 3, "my"), ("Bb4", 1 / 3, "dream"),
             ("Bb4", 1 / 3, "come"), ("C5", 1.0, "true")]),
    (None, [("D5", 2.0, "sir"), (None, 2.0, None)]),
    # --- mm 88-91: final button, excerpt ends mid-phrase ---
    (None, [(None, 1.0, None), ("Bb4", 1 / 3, "What"), ("Bb4", 1 / 3, "do"), ("Bb4", 1 / 3, "I"),
             ("Bb4", 2.0, "say?")]),
    (None, [("Bb4", 1 / 3, "What"), ("Bb4", 1 / 3, "do"), ("Bb4", 1 / 3, "I"), ("Bb4", 1 / 3, "say?"),
             ("Bb4", 1 / 3, "Here's"), ("Bb4", 1 / 3, "what"), ("Bb4", 1 / 3, "I"), ("Bb4", 1 / 3, "say"),
             ("Bb4", 1 / 3, "to"), ("C5", 1.0, "you,")]),
    (None, [("D5", 2.0, "sir!"), (None, 1.0, None), ("Bb4", 0.5, "I"), ("A4", 0.5, "can't")]),
    (None, [("G4", 1.0, None), (None, 3.0, None)]),
]

# Piano reduction: (bass pitch or None, chord pitches or None, quarterLength) events per
# measure, filling the measure's total duration. A harmonic sketch of the two
# accompaniment staves (see module docstring) rather than a literal transcription.
PIANO_MEASURES: list[list[tuple[str | None, list[str] | None, float]]] = [
    # mm 6-8: dramatic underscore, Bb minor
    [("Bb2", ["Bb3", "Db4", "F4"], 4.0)],
    [("Bb2", ["Bb3", "Db4", "F4"], 4.0)],
    [("Gb2", ["Gb3", "Bb3", "Db4"], 4.0)],
    # mm 9-10 patter (verse 1)
    [("Bb2", ["Bb3", "Db4", "F4"], 2.0), ("Gb2", ["Gb3", "Bb3", "Db4"], 2.0)],
    [("Bb2", ["Bb3", "Db4", "F4"], 4.0)],
    # mm 11-12 patter (verse 2)
    [("Bb2", ["Bb3", "Db4", "F4"], 2.0), ("F2", ["F3", "A3", "C4"], 2.0)],
    [("F2", ["F3", "A3", "C4"], 4.0)],
    # mm 13-14 patter (verse 3), 7/4 then 4/4
    [("Bb2", ["Bb3", "Db4", "F4"], 7.0)],
    [("Gb2", ["Gb3", "Bb3", "Db4"], 4.0)],
    # mm 15-16
    [("Bb2", ["Bb3", "Db4", "F4"], 4.0)],
    [("F2", ["C4", "F4", "A4"], 4.0)],
    # mm 17-32: F major hook, I - vi - IV - V oom-pah (2 beats/bar)
    [("F2", ["F3", "A3", "C4"], 2.0)],
    [("D2", ["D3", "F3", "A3"], 2.0)],
    [("Bb1", ["Bb2", "D3", "F3"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    [("F2", ["F3", "A3", "C4"], 2.0)],
    [("D2", ["D3", "F3", "A3"], 2.0)],
    [("Bb1", ["Bb2", "D3", "F3"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    [("F2", ["F3", "A3", "C4"], 2.0)],
    [("D2", ["D3", "F3", "A3"], 2.0)],
    [("Bb1", ["Bb2", "D3", "F3"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    [("F2", ["F3", "A3", "C4"], 2.0)],
    [("D2", ["D3", "F3", "A3"], 2.0)],
    [("Bb1", ["Bb2", "D3", "F3"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    # mm 33-40 verse, F - Bb - C7 - F
    [("F2", ["F3", "A3", "C4"], 2.0)],
    [("Bb1", ["Bb2", "D3", "F3"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    [("F2", ["F3", "A3", "C4"], 2.0)],
    [("Bb1", ["Bb2", "D3", "F3"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    [("F2", ["F3", "A3", "C4"], 2.0)],
    [("F2", ["F3", "A3", "C4"], 2.0)],
    # mm 41-44 bridge, Dm - Gm - C7 - F (with pickup)
    [("D2", ["D3", "F3", "A3"], 2.0)],
    [("G2", ["G3", "Bb3", "D4"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    # mm 45-48
    [("F2", ["F3", "A3", "C4"], 2.0)],
    [("Bb1", ["Bb2", "D3", "F3"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    [("F1", ["F2", "A2", "C3", "F3"], 2.0)],
    # mm 49-52
    [("F2", ["F3", "A3", "C4"], 2.0)],
    [("D2", ["D3", "F3", "A3"], 2.0)],
    [("Bb1", ["Bb2", "D3", "F3"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    # mm 53-56
    [("D2", ["D3", "F3", "A3"], 2.0)],
    [("G1", ["G2", "Bb2", "D3"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    # mm 57-60
    [("F2", ["F3", "A3", "C4"], 2.0)],
    [("Bb1", ["Bb2", "D3", "F3"], 2.0)],
    [("Eb2", ["Eb3", "G3", "Bb3"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    # mm 61-64
    [("F2", ["F3", "A3", "C4"], 2.0)],
    [("Bb1", ["Bb2", "D3", "F3"], 2.0)],
    [("F1", ["F2", "A2", "C3", "F3"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    # mm 65-68
    [("F2", ["F3", "A3", "C4"], 2.0)],
    [("Bb1", ["Bb2", "D3", "F3"], 2.0)],
    [("G2", ["G3", "Bb3", "D4"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    # mm 69-72
    [("F2", ["F3", "A3", "C4"], 2.0)],
    [("Bb1", ["Bb2", "D3", "F3"], 2.0)],
    [("F1", ["F2", "A2", "C3", "F3"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    # mm 73-76
    [("F2", ["F3", "A3", "C4"], 2.0)],
    [("D2", ["D3", "F3", "A3"], 2.0)],
    [("Bb1", ["Bb2", "D3", "F3"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    # mm 77-81: building to the button
    [("F2", ["F3", "Bb3", "D4"], 2.0)],
    [("G2", ["G3", "C4", "Eb4"], 2.0)],
    [("A2", ["A3", "D4", "F4"], 2.0)],
    [("Bb2", ["Bb3", "D4", "G4"], 2.0)],
    [("C2", ["C3", "E3", "G3", "Bb3"], 2.0)],
    # mm 82-84: sustained dramatic chords under Leo's patter
    [("Bb2", ["Bb3", "Db4", "F4"], 4.0)],
    [("Bb2", ["Bb3", "Db4", "F4"], 4.0)],
    [("Gb2", ["Gb3", "Bb3", "Db4"], 4.0)],
    # mm 85-87
    [("Bb2", ["Bb3", "Db4", "F4"], 4.0)],
    [("Bb2", ["Bb3", "Db4", "F4"], 4.0)],
    [("Gb2", ["Gb3", "Bb3", "Db4"], 4.0)],
    # mm 88-91
    [("Bb2", ["Bb3", "Db4", "F4"], 4.0)],
    [("Bb2", ["Bb3", "Db4", "F4"], 4.0)],
    [("Gb2", ["Gb3", "Bb3", "Db4"], 4.0)],
    [("F1", ["F2", "A2", "C3"], 4.0)],
]


def build_vocal_part() -> stream.Part:
    part = stream.Part(id="Vocal")
    part.partName = "Vocal (Max/Leo)"
    part.insert(0, instrument.Vocalist())
    part.insert(0, clef.TrebleClef())
    part.insert(0, key.KeySignature(-5))
    for i, (ts, events) in enumerate(VOCAL_MEASURES):
        m = stream.Measure(number=FIRST_MEASURE + i)
        if ts is not None:
            m.timeSignature = meter.TimeSignature(ts)
        if (FIRST_MEASURE + i) in TEMPO_CHANGES:
            m.insert(0, tempo.MetronomeMark(number=TEMPO_CHANGES[FIRST_MEASURE + i]))
        for pitch_name, ql, lyric in events:
            n = note.Rest(quarterLength=ql) if pitch_name is None else note.Note(pitch_name, quarterLength=ql)
            if lyric:
                n.lyric = lyric
            m.append(n)
        part.append(m)
    return part


def build_piano_part() -> stream.Part:
    part = stream.Part(id="Piano")
    part.partName = "Piano"
    part.insert(0, instrument.Piano())
    part.insert(0, clef.BassClef())
    part.insert(0, key.KeySignature(-5))
    # time signatures mirror the vocal part; reuse the same measure boundaries
    vocal_ts = [ts for ts, _ in VOCAL_MEASURES]
    for i, (ts, events) in enumerate(zip(vocal_ts, PIANO_MEASURES)):
        m = stream.Measure(number=FIRST_MEASURE + i)
        if ts is not None:
            m.timeSignature = meter.TimeSignature(ts)
        for bass_pitch, chord_pitches, ql in events:
            pitches = ([bass_pitch] if bass_pitch else []) + (chord_pitches or [])
            el = chord.Chord(pitches, quarterLength=ql) if pitches else note.Rest(quarterLength=ql)
            m.append(el)
        part.append(m)
    return part


def main() -> None:
    score = stream.Score()
    score.metadata = metadata.Metadata()
    score.metadata.title = "We Can Do It!"
    score.metadata.movementName = "We Can Do It! (mm.6-91, hand transcription)"
    score.metadata.composer = "Mel Brooks / Glen Kelly (The Producers)"

    score.append(build_vocal_part())
    score.append(build_piano_part())

    out_path = "we-can-do-it.musicxml"
    score.write("musicxml", fp=out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
