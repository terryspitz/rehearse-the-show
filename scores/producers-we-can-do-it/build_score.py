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
    #
    # Pitches below were corrected using homr (github.com/liebharc/homr), an
    # open-source OMR model, run against isolated crops of just the vocal
    # staff (see ../../scores/producers-we-can-do-it/README.md "Correcting
    # the vocal line" for how). The original by-eye pass had the "We Can Do
    # It!" hook a full octave too high; homr's readings (cross-checked
    # against the printed lyrics/rhythm, which it doesn't extract) confirm
    # the hook actually sits low (C4-D4), and rises a step or an octave with
    # each reprise -- a rising sequence across the number, not flat
    # repetition. Rhythm/lyrics are unchanged from the original pass.
    #
    # --- mm 6-8: "A tempo, Slow 4" -- spoken dialogue over underscore, nobody sings ---
    ("4/4", [(None, 4.0, None)]),
    (None, [(None, 4.0, None)]),
    (None, [(None, 4.0, None)]),
    # --- mm 9-10: Max, patter verse 1 (Lewis & Clark) -- monotone Ab4 throughout ---
    (None, [(None, 1.0, None), ("Ab4", 0.25, "What"), ("Ab4", 0.25, "did"), ("Ab4", 0.25, "Lew-"), ("Ab4", 0.25, "-is"),
             ("Ab4", 0.25, "say"), ("Ab4", 0.25, "to"), ("Ab4", 0.5, "Clark"), ("Ab4", 1.0, "when")]),
    (None, [("Ab4", 0.25, "ev-"), ("Ab4", 0.25, "-'ry-"), ("Ab4", 0.25, "-thing"), ("Ab4", 0.25, "looked"),
             ("Ab4", 2.0, "bleak?"), (None, 1.0, None)]),
    # --- mm 11-12: patter verse 2 (Hillary & Tenzing) -- also monotone Ab4 ---
    (None, [("Ab4", 0.25, "What"), ("Ab4", 0.25, "did"), ("Ab4", 0.25, "Sir"), ("Ab4", 0.25, "Ed-"),
             ("Ab4", 0.25, "-mund"), ("Ab4", 0.25, "say"), ("Ab4", 0.25, "to"), ("Ab4", 0.25, "Ten-"),
             ("Ab4", 0.25, "-zing"), ("Ab4", 0.25, "as"), ("Ab4", 0.25, "they"), ("Ab4", 0.25, "strug-"),
             ("Ab4", 0.25, "-gled"), ("Ab4", 0.25, "t'ward"), ("Ab4", 0.25, "Ev-"), ("Ab4", 0.25, "-er-")]),
    (None, [("Ab4", 1.0, "-est's"), ("Ab4", 2.0, "peak?"), (None, 1.0, None)]),
    # --- mm 13-14: patter verse 3 (Washington) -- monotone steps up to B4 (natural) ---
    ("7/4", [("B4", 1.0, "What"), ("B4", 1 / 3, "did"), ("B4", 1 / 3, "Wash-"), ("B4", 1 / 3, "-ing-"),
              ("B4", 1 / 3, "-ton"), ("B4", 1 / 3, "say"), ("B4", 1 / 3, "to"), ("B4", 1.0, "his"),
              ("B4", 1.0, "troops"), ("B4", 0.5, "as"), ("B4", 1.5, "they")]),
    ("4/4", [("B4", 2.0, "crossed"), ("B4", 0.5, "the"), ("B4", 0.5, "Del-"), ("B4", 0.5, "-a-"), ("B4", 0.5, "-ware?")]),
    # --- mm 15-16: punchline (rises B4->D5), Leo speaks (not sung), Max pickup drops low ---
    (None, [(None, 0.5, None), ("B4", 0.5, "I'm"), ("B4", 0.5, "sure"), ("B4", 0.5, "you're"),
             ("D5", 0.25, "well"), ("D5", 0.25, "a-"), ("D5", 1.5, "-ware!")]),
    (None, [(None, 3.0, None), ("D4", 0.5, "We"), ("Bb3", 0.5, "can")]),
    # --- mm 17-32: "Slow 2" -- the "We Can Do It!" hook, F major, 2/4 -- base register C4/D4 ---
    ("2/4", [("C4", 0.5, "do"), ("D4", 1.5, "it!")]),
    (None, [("Bb3", 0.5, "We"), (None, 0.5, None), ("D4", 0.5, "can"), (None, 0.5, None)]),
    (None, [("C4", 0.5, "do"), ("D4", 1.5, "it!")]),
    (None, [("Bb3", 0.5, "We"), (None, 0.5, None), ("D4", 0.5, "can"), (None, 0.5, None)]),
    (None, [("C4", 1.0, "do"), ("D4", 1.0, "it,")]),
    (None, [("C4", 1.0, "me"), ("Bb3", 1.0, "and")]),
    (None, [("F4", 2.0, "you!")]),
    (None, [("Eb4", 0.5, "We"), (None, 0.5, None), ("G4", 0.5, "can"), (None, 0.5, None)]),
    # --- reprise a step up: F4/G4 ---
    (None, [("F4", 0.5, "do"), ("G4", 1.5, "it!")]),
    (None, [("Eb4", 0.5, "We"), (None, 0.5, None), ("G4", 0.5, "can"), (None, 0.5, None)]),
    (None, [("F4", 0.5, "do"), ("G4", 1.5, "it!")]),
    (None, [("Eb4", 0.5, "We"), (None, 0.5, None), ("G4", 0.5, "can"), (None, 0.5, None)]),
    (None, [("A4", 1.0, "make"), ("G4", 1.0, "our")]),
    (None, [("F4", 1.0, "dreams"), ("Eb4", 1.0, "come")]),
    (None, [("F4", 2.0, "true!")]),
    (None, [(None, 1.0, None), ("G4", 0.5, "Ev'-"), ("A4", 0.5, "-ry-")]),
    # --- mm 33-40: "A tempo" verse, still 2/4 -- A4 plateau descending to G4 ---
    (None, [("A4", 1.0, "-thing"), ("A4", 1.0, "you've")]),
    (None, [("A4", 1.0, "ev-"), ("A4", 1.0, "-er")]),
    (None, [("Bb4", 0.5, "want-"), ("A4", 1.5, "-ed")]),
    (None, [(None, 0.5, None), ("A4", 1.0, "is"), ("F4", 0.5, "just")]),
    (None, [("G4", 1.0, "wait-"), ("G4", 1.0, "-ing")]),
    (None, [("G4", 1.0, "to"), ("G4", 1.0, "be")]),
    (None, [("G4", 2.0, "had")]),
    (None, [("G4", 1.0, None), (None, 1.0, None)]),
    # --- mm 41-44: bridge, chromatic rise E4->A4 then a dip and rise to Bb4 ---
    (None, [("E4", 0.5, "Beau-"), ("F4", 0.5, "-ti-"), ("F#4", 0.5, "-ful"), ("G4", 0.5, "girls")]),
    (None, [("G4", 0.5, None), (None, 0.5, None), ("E4", 0.5, "wear-"), ("C4", 0.5, "-ing")]),
    (None, [("F4", 0.5, "no-"), ("G4", 0.5, "-thing"), ("G#4", 0.5, "but"), ("A4", 0.5, "pearls")]),
    (None, [("A4", 0.5, None), (None, 0.5, None), ("Bb4", 0.5, "Ca-"), (None, 0.5, None)]),
    # --- mm 45-48: descending run C5->Bb3 into the next "We can" pickup ---
    (None, [("C5", 0.5, "-ress-"), ("C5", 0.5, "-ing"), ("C5", 0.5, "you"), ("A4", 0.5, "un-")]),
    (None, [("C5", 0.5, "-dress-"), ("C5", 0.5, "-ing"), ("C5", 0.5, "you"), ("Bb4", 0.5, "and")]),
    (None, [("A4", 0.5, "driv-"), ("Ab4", 0.5, "-ing"), ("G4", 0.5, "you"), ("F4", 0.5, "mad!")]),
    (None, [(None, 1.0, None), ("D4", 0.5, "We"), ("Bb3", 0.5, "can")]),
    # --- mm 49-52: hook returns to base register C4/D4 ---
    (None, [("C4", 0.5, "do"), ("D4", 1.5, "it!")]),
    (None, [("Bb3", 0.5, "We"), (None, 0.5, None), ("D4", 0.5, "can"), (None, 0.5, None)]),
    (None, [("C4", 0.5, "do"), ("D4", 1.5, "it!")]),
    (None, [("Bb3", 0.5, "This"), (None, 0.5, None), ("D4", 0.5, "is"), (None, 0.5, None)]),
    # --- mm 53-56: stepwise descent to a low cadence, then pickup ---
    (None, [("D4", 1.0, "not"), ("C4", 1.0, "the")]),
    (None, [("Bb3", 1.0, "time"), ("A3", 1.0, "to")]),
    (None, [("Bb3", 1.0, "shirk!"), (None, 1.0, None)]),
    (None, [(None, 0.5, None), ("E4", 0.5, "We"), (None, 0.5, None), ("C4", 0.5, "can")]),
    # --- mm 57-60: reprise at F4/G4 again ("do it! You won't rue it") ---
    (None, [("F4", 0.5, "do"), ("G4", 1.5, "it!")]),
    (None, [("F4", 0.5, "You"), ("G4", 1.5, "won't")]),
    (None, [("F4", 0.5, "rue"), ("G4", 1.5, "it")]),
    (None, [(None, 1.0, None), ("E4", 0.5, "say"), ("G4", 0.5, '"good-')]),
    # --- mm 61-64: descending phrase F4->C5 leap ---
    (None, [("F4", 1.0, "-bye\""), ("G4", 1.0, "to")]),
    (None, [("F4", 1.0, "pet-"), ("Eb4", 1.0, "-ty")]),
    (None, [("C5", 2.0, "clerk!")]),
    (None, [(None, 0.5, None), ("D5", 1.0, "Hi,"), ("Bb4", 0.5, "pro-")]),
    # --- mm 65-68: hook rhythm reused, up an octave (C5/D5) -- the "producer" tag ---
    (None, [("C5", 0.5, "-du-"), ("D5", 1.5, "-cer!")]),
    (None, [("Bb4", 0.5, "Yes"), (None, 0.5, None), ("D5", 0.5, "pro-"), (None, 0.5, None)]),
    (None, [("C5", 0.5, "-du-"), ("D5", 1.5, "-cer!")]),
    (None, [("Bb4", 0.5, "I"), (None, 0.5, None), ("D5", 0.5, "mean"), (None, 0.5, None)]),
    # --- mm 69-72 ---
    (None, [("C5", 1.0, "you"), ("D5", 1.0, "sir,")]),
    (None, [("C5", 1.0, "go"), ("Bb4", 1.0, "be-")]),
    (None, [("D5", 2.0, "-serk!")]),
    (None, [(None, 0.5, None), ("Bb4", 0.5, "We"), (None, 0.5, None), ("D5", 0.5, "can")]),
    # --- mm 73-76: hook at climax register (C5/D5) again ---
    (None, [("C5", 0.5, "do"), ("D5", 1.5, "it!")]),
    (None, [("Bb4", 0.5, "We"), (None, 0.5, None), ("D5", 0.5, "can"), (None, 0.5, None)]),
    (None, [("C5", 0.5, "do"), ("D5", 1.5, "it!")]),
    (None, [(None, 1.0, None), ("Bb4", 0.5, "And"), ("D5", 0.5, "I")]),
    # --- mm 77-81: the button, peaking at Eb5 then descending to the final chord ---
    (None, [("Eb5", 2.0, "know")]),
    (None, [("D5", 2.0, "it's")]),
    (None, [("Bb4", 2.0, "gon-")]),
    (None, [("C5", 2.0, "-na")]),
    (None, [("Bb4", 1.0, "work!"), (None, 1.0, None)]),
    # --- mm 82-84: Leo, 4/4, patter again -- monotone F4, rising tag to Ab4 ---
    ("4/4", [(None, 1.0, None), ("F4", 1 / 3, "What"), ("F4", 1 / 3, "do"), ("F4", 1 / 3, "I"), ("F4", 2.0, "say?")]),
    (None, [("F4", 1 / 3, "Fin-"), ("F4", 1 / 3, "'lly"), ("F4", 1 / 3, "a"), ("F4", 1 / 3, "chance"),
             ("F4", 1 / 3, "to"), ("F4", 1 / 3, "be"), ("F4", 1 / 3, "a"), ("F4", 1 / 3, "Broad-"),
             ("F4", 1 / 3, "-way"), ("F4", 1.0, "pro-")]),
    (None, [("Ab4", 2.0, "-du-cer"), (None, 2.0, None)]),
    # --- mm 85-87: same shape, rising tag now to B4 ---
    (None, [(None, 1.0, None), ("F4", 1 / 3, "What"), ("F4", 1 / 3, "do"), ("F4", 1 / 3, "I"), ("F4", 2.0, "say?")]),
    (None, [("F4", 1 / 3, "Fin-"), ("F4", 1 / 3, "'lly"), ("F4", 1 / 3, "a"), ("F4", 1 / 3, "chance"),
             ("F4", 1 / 3, "to"), ("F4", 1 / 3, "make"), ("F4", 1 / 3, "my"), ("F4", 1 / 3, "dream"),
             ("F4", 1 / 3, "come"), ("F4", 1.0, "true")]),
    (None, [("B4", 2.0, "sir"), (None, 2.0, None)]),
    # --- mm 88-91: final button, excerpt ends mid-phrase -- tag rises to C5 then falls ---
    (None, [(None, 1.0, None), ("F4", 1 / 3, "What"), ("F4", 1 / 3, "do"), ("F4", 1 / 3, "I"),
             ("F4", 2.0, "say?")]),
    (None, [("F4", 1 / 3, "What"), ("F4", 1 / 3, "do"), ("F4", 1 / 3, "I"), ("F4", 1 / 3, "say?"),
             ("F4", 1 / 3, "Here's"), ("F4", 1 / 3, "what"), ("F4", 1 / 3, "I"), ("F4", 1 / 3, "say"),
             ("F4", 1 / 3, "to"), ("C5", 1.0, "you,")]),
    (None, [("C5", 2.0, "sir!"), (None, 1.0, None), ("A4", 0.5, "I"), ("G4", 0.5, "can't")]),
    (None, [("F4", 1.0, None), (None, 3.0, None)]),
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
