# "We Can Do It!" (The Producers) — hand transcription

MIDI + MusicXML for the Max/Leo "We Can Do It!" underscored dialogue scene,
built for the rehearsal-player pipeline in this repo.

## Source

An 8-page piano/conductor excerpt supplied by the user (`#5 "We Can Do It!"
[r 4/02]`, Miller Music Service), covering measures 6–91. The scan is missing
its first page (mm.1–5) and the excerpt itself ends mid-phrase at m.91
("I can't...") — that's where the source PDF stops, not where this
transcription gives up.

## Why hand transcription, not OMR

`docs/research-libraries.md` §2 already concludes that automated OMR on a
dense piano-conductor reduction (divisi, tremolo, cue text like `(Stgs)`,
`(Hn/Tbns)`, grace-note runs, frequent meter changes) is unreliable, and that
output should be treated as a draft regardless. This session didn't have a
working Audiveris install available, so the score was read by eye from the
scanned pages and entered directly as a `music21` stream in `build_score.py`.
Treat it exactly like OMR output: a first-pass draft to check against the
original score, not a guaranteed-accurate performance edition.

Two different confidence levels apply:

- **Vocal line + lyrics** — transcribed note-by-note from the vocal staff.
  This is the part that matters for rehearsal, and is the most carefully
  read. Lyrics are complete and in order; pitches/rhythms for the "We Can Do
  It!" hook and its reprises are fairly confident, the three "What did X say
  to Y" patter verses (mm.9–14) and Leo's closing patter (mm.82–91) are
  simplified to a repeated pitch with a rising tag, since the source notates
  those as fast, near-monotone comic delivery.
- **Piano part** — the source is actually a 2-stave *conductor's* reduction
  with cues for strings/brass/winds/timpani etc, not a piano part. Copying
  every orchestral ornament (grace-note runs, tremoli, harp glissandi) onto a
  piano note-for-note isn't meaningful, so this is a harmonic reduction — a
  bass note plus a comping chord at the harmonic rhythm implied by the two
  staves — rather than a literal transcription of every notehead.

Tempo: the score doesn't give metronome marks, only tempo *text* ("A tempo,
Slow 4", "Slow 2", and an unmarked faster feel for Leo's closing patter).
`TEMPO_CHANGES` in `build_score.py` picks reasonable BPMs for each; adjust
freely, an MD will always want to set these by ear anyway.

## Regenerating

```bash
pip install music21
python build_score.py                                  # -> we-can-do-it.musicxml
python ../../spike/score_to_parts.py we-can-do-it.musicxml -o build/
```

Produces `build/parts/*.mid` (vocal, piano), `build/mix.mid`, and
`build/score.json` (measure/beat map + syllable-level lyric timeline), per
the contract in the top-level README.

To fix a wrong note or rhythm: edit the `VOCAL_MEASURES` / `PIANO_MEASURES`
tables in `build_score.py` (each entry is `(pitch_or_None, quarterLength,
lyric_or_None)` for a measure) and re-run the two commands above.
