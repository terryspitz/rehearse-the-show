# rehearse-the-show

A web-based singing practice app for amateur musical theatre.

Give it a song from a show, and it should let you: mix the volume of each
instrument and each SATB vocal part independently, follow the lyrics, loop a
tricky section, and count yourself in.

**Status: research spike.** No app yet. What's here is the library research that
decides the architecture, plus one working piece of the pipeline.

## Contents

- **[`docs/research-libraries.md`](docs/research-libraries.md)** — the main
  document. Evaluates options for each stage: finding/downloading scores, PDF →
  MusicXML (OMR), MusicXML → per-part MIDI, and the browser player. Includes a
  recommended stack, a proposed architecture, and a riskiest-first build order.
- **[`spike/score_to_parts.py`](spike/score_to_parts.py)** — working, tested.
  Splits a MusicXML score into one MIDI file per part and emits a `score.json`
  with the measure/beat map and a syllable-level lyric timeline. That JSON is the
  contract the player will consume.
- **[`docs/omr-evaluation.md`](docs/omr-evaluation.md)** — the OMR bake-off run
  against a real *Guys and Dolls* vocal book. What works, what doesn't, and what
  it changes about the plan.
- **[`spike/render_demo.py`](spike/render_demo.py)** — renders listenable
  practice mixes offline (full mix / my part forward / my part alone with a
  click), proving the mixer end to end before any browser code exists.
- **[`spike/omr_report.py`](spike/omr_report.py)** — structural scorecard for an
  OMR engine's MusicXML: parts, measures, chords, lyrics, clefs, key signatures.
- **[`spike/gt_staves.py`](spike/gt_staves.py)** — counts staves in a page image
  by horizontal projection, to get ground truth to judge OMR output against.

## Two findings worth reading before anything else

1. **Automatically searching the web for vocal-score PDFs is the wrong stage 1.**
   Musical theatre scores are rented per-production by MTI/Concord, not sold, and
   essentially the whole canon is in copyright. The app should ingest the score
   the user's production was legitimately shipped, and carry a public-domain
   catalogue (IMSLP, CPDL) for the free tier. See §1 of the research doc.
2. **SATB parts don't exist as separate parts in a vocal score.** The chorus is
   notated with divisi on one or two staves, so getting a four-fader SATB mixer
   needs a voice splitter, not just a part list. See §3.
3. **OMR gives us notes but not the two things the mixer needs most** — which
   line is which, and what the words are. Measured, not guessed: see the
   [evaluation](docs/omr-evaluation.md). A human review step that maps staves to
   voice parts is load-bearing, not optional polish.

## Running the spike

```bash
pip install music21
python spike/score_to_parts.py bach/bwv66.6 -o out/    # a music21 corpus score
python spike/score_to_parts.py my-score.musicxml -o out/
```

Produces `out/parts/*.mid`, `out/mix.mid` and `out/score.json`.

To hear it — renders each part separately, then mixes them at different gains,
which is exactly what the browser mixer will do live:

```bash
apt-get install fluidsynth fluid-soundfont-gm ffmpeg
python spike/render_demo.py bach/bwv10.7 -o demo/
```

Produces `demo/full-mix.mp3`, `demo/tenor-forward.mp3` and
`demo/tenor-alone-with-click.mp3`. Voices are rendered with the GM Choir Aahs
patch and panned across the stereo field (S left → B right) so a soloed line
sounds like a singer and stays separable by ear in the full mix — the thing the
old MIDI-beep choral sites get wrong.
