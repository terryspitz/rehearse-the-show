# "We Can Do It!" (The Producers) — hand transcription

MIDI + MusicXML for the Max/Leo "We Can Do It!" underscored dialogue scene,
built for the rehearsal-player pipeline in this repo.

## Source

An 8-page piano/conductor excerpt supplied by the user (`#5 "We Can Do It!"
[r 4/02]`, Miller Music Service), covering measures 6–91. The scan is missing
its first page (mm.1–5) and the excerpt itself ends mid-phrase at m.91
("I can't...") — that's where the source PDF stops, not where this
transcription gives up.

## Why hand transcription, not OMR — and where OMR still helped

`docs/research-libraries.md` §2 already concludes that automated OMR on a
dense piano-conductor reduction (divisi, tremolo, cue text like `(Stgs)`,
`(Hn/Tbns)`, grace-note runs, frequent meter changes) is unreliable. That
holds for the *whole 3-stave system* — no engine handles that cleanly, and
Audiveris itself couldn't be installed in this session (its release JARs are
served from GitHub, which this sandbox can't reach directly; only PyPI is
open). But it doesn't mean OMR is useless here: **homr**
([github.com/liebharc/homr](https://github.com/liebharc/homr), pip-installable,
AGPL-3.0) is a single-staff/monophonic-focused vision-transformer OMR model,
and cropping just the vocal staff out of each system (excluding the two
accompaniment staves) plays exactly to that strength.

That's what corrected the vocal line after the first pass had it a full
octave too high with a partly-invented contour. Cropping each system down to
just the vocal staff (`homr <cropped-system.png>` → MusicXML) gave verified
pitches without ever running OMR on the messy 3-stave original. The `homr`
readings turned up a real musical pattern the first pass missed entirely:
the "We Can Do It!" hook is a **rising sequence** — it starts low (C4/D4),
steps up (F4/G4) and returns to it, jumps up an octave for the "producer"
reprises (C5/D5), and peaks at Eb5 for "This is gonna work!" before Leo's
spoken/patter close drops back to F4. `build_score.py`'s current pitches
reflect that; see the git history for the original (wrong) flat-octave pass.

Two different confidence levels still apply:

- **Vocal line + lyrics** — lyrics are complete and in order (homr doesn't
  extract lyrics, so those are still the by-eye read, cross-checked against
  the pitch data by position). Pitches for the "We Can Do It!" hook and its
  reprises are now homr-verified. The three "What did X say to Y" patter
  verses (mm.9–14) and Leo's closing patter (mm.82–91) are still simplified
  to a near-monotone pitch with a rising tag at the end, but that monotone
  pitch itself, and where it steps, is also homr-verified now, not guessed.
- **Piano part** — the source is actually a 2-stave *conductor's* reduction
  with cues for strings/brass/winds/timpani etc, not a piano part. Copying
  every orchestral ornament (grace-note runs, tremoli, harp glissandi) onto a
  piano note-for-note isn't meaningful, so this is a harmonic reduction — a
  bass note plus a comping chord at the harmonic rhythm implied by the two
  staves — rather than a literal transcription of every notehead. This part
  is still the by-eye pass, unverified by OMR.

If you want to re-verify or re-derive any of this: install `homr` in a venv
(it needs `antlr4-python3-runtime==4.9.3`, whose sdist fails to build under
current `setuptools` — install `setuptools==58.2.0` first, then `homr`), crop
a system image down to just the staff you want read, and run
`homr <crop.png>`. It writes a `.musicxml` file with its reading.

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
