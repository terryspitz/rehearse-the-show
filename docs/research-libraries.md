# Library research: score → MIDI → rehearsal player

Research pass for a web-based singing practice app for amateur musical theatre.
Target use case: *"give me 'Luck Be a Lady' from Guys and Dolls, let me mute the
band, solo the tenor line, loop bars 33–48 and see the words go by."*

Researched August 2026. Every recommendation below is a judgement call about a
moving target — the OMR field in particular has changed a lot in the last 18
months.

---

## 0. TL;DR — recommended stack

| Stage | Recommendation | Why |
|---|---|---|
| Find scores | **No automated web search.** Catalogue-first: IMSLP API for public domain, user upload for everything else | See §1 — this is a legal constraint, not a technical one |
| PDF → MusicXML | **Audiveris 5.9** as the default engine, **homr** as a second opinion | Audiveris is the only one with real multi-staff/multi-part system handling, which is exactly what a vocal score is |
| MusicXML → parts/MIDI | **music21** (Python) | Already verified working in `spike/score_to_parts.py`; gives per-part MIDI, tempo map and lyric timeline in one pass |
| Score rendering | **Verovio** (`verovio` npm/WASM) | MusicXML in, SVG out, plus `renderToTimemap()` which gives note-level playback sync for free |
| Audio | **spessasynth_lib** (SF2 synth) or **smplr** (sampled instruments) | Both do per-channel gain, which *is* the mixer |
| Glue | **musicxml-player** as a reference implementation, not necessarily a dependency | It has already solved render↔playback sync; worth reading even if we rebuild |

Fallback for when OMR fails (it will, often): **Demucs** stem separation over a
rehearsal recording, for a coarse vocals/accompaniment mix.

---

## 1. Stage 1: finding and downloading PDFs — read this first

**This is the stage that constrains the whole product, and the constraint is
legal rather than technical.**

Musical theatre repertoire is the *least* free category of sheet music there is.
"Luck Be a Lady" (Frank Loesser, 1950) is in copyright in the US until 2046, and
in the UK/EU until 2039 (Loesser died 1969). More importantly, MT vocal scores
aren't sold at all in the normal sense: [MTI](https://www.mtishows.com/licensing-an-mti-musical)
and Concord **rent** the vocal books, piano-conductor score and orchestra parts
to a licensed production, ship them ~2 months before opening, and require them
back afterwards. MTI's terms explicitly state the licence does not grant the
right to make a mechanical recording of the show "rehearsal, performance or
otherwise."

So an app that automatically searches the web for a PDF of a vocal score and
downloads it is, for essentially the entire MT canon, an app for finding
infringing copies. That's a bad foundation regardless of one's view of the
ethics — it's also fragile (the sources are whack-a-mole file lockers) and it
would make the app unshippable to the schools and am-dram societies who are the
actual users.

### What to build instead

The good news: the target user is almost always a cast member in a production
that has **already licensed the show and been shipped a legitimate vocal book**.
So invert stage 1:

1. **User upload is the primary path.** "Photograph or scan your vocal book
   page" / "drop in the PDF your MD sent you." Process it, keep the derived MIDI
   scoped to that user or that production, don't build a shared library of
   derived works. This is the same posture ChoraLine and the various
   scan-to-play apps take.
2. **A production workspace.** MD uploads once, cast members join by code. This
   matches how the licence actually works (per-production) and is a better
   product anyway — the MD sets tempi, marks cuts, defines loops.
3. **Catalogued legal sources for the free tier**, so the app is useful before
   anyone uploads anything:
   - **IMSLP** — genuinely public domain, and has a real API. Two endpoints: a
     worklist API (complete index, 1000 records/page) and the standard MediaWiki
     API for per-work detail and file manifests with direct PDF links. The
     [`imslp`](https://pypi.org/project/imslp/) Python package
     ([source](https://github.com/jlumbroso/imslp)) wraps this via `mwclient`.
     Note IMSLP's rules explicitly forbid mass downloading — cache politely,
     rate limit, identify the client. Coverage for MT is near zero (it's a
     classical archive), but it covers Gilbert & Sullivan, operetta, and
     pre-1930 material, which is a real slice of am-dram.
   - **MuseScore.com** — 1.5M+ user scores in MusicXML/MIDI, and a lot of MT
     transcriptions. But: copyrighted works need MuseScore Pro (~$49/yr) because
     they pay licensors, and there is **no official public search/download API**
     (the `musescore-downloader` / `dl-librescore` tools work by bypassing that,
     which we should not build on). Realistic use: deep-link the user to
     MuseScore and let them export MusicXML themselves, then upload it to us.
     That skips OMR entirely and gives a far better result.
   - **CPDL / ChoralWiki** — public domain choral, MediaWiki-backed like IMSLP,
     often has MusicXML already.
   - **Open Score / Sheet Music International** for scanned PD material.

### Verdict on stage 1

Don't build a crawler. Build: (a) an upload/ingest pipeline, (b) an IMSLP+CPDL
catalogue connector for the PD corpus, (c) a "paste a MusicXML/MIDI file"
fast path that skips OMR entirely. **Where the user can supply MusicXML rather
than PDF, everything downstream gets dramatically better** — that's worth
surfacing in the UI as the recommended route.

---

## 2. Stage 2: PDF → MusicXML (optical music recognition)

This is the hardest, lowest-fidelity link in the chain, and it's worth being
blunt: **OMR on a dense piano-vocal score is not a solved problem.** A Guys and
Dolls vocal score page has a piano reduction (2 staves, dense chords, cue notes
in small print), a vocal staff with lyrics and often divisi, rehearsal marks,
tempo text, cuts, and handwritten pencil markings. Every open-source engine
below was primarily evaluated on cleaner material than that.

### The candidates

**[Audiveris](https://github.com/Audiveris/audiveris)** — Java, AGPL-3.0,
v5.9.0 (Dec 2025). The mature one. Classical CV+ML pipeline with an interactive
editor for fixing recognition errors, exports MusicXML 4.0 and MIDI. **Its key
advantage for us is architectural, not accuracy**: it models systems, staves,
part-groups and multi-staff instruments properly, so a piano-vocal system comes
out as structured parts. It also handles multi-page PDFs natively and has a
batch CLI (`-batch -export`), so it drops straight into a server pipeline.
Downside: JVM dependency in the container, and it is slow (tens of seconds to
minutes per page). The interactive editor is desktop-only, but that's arguably
fine — the MD fixes the score once, on a laptop, before the cast uses it.

**[homr](https://pypi.org/project/homr/)** — Python 3.11–3.15, AGPL-3.0,
v0.7.0 (Jun 2026). Segmentation model (adapted from oemer) + vision transformer
encoder/decoder. Described by oemer's own author as "an awesome improved version
of this project... more dedicated and powerful deep learning model, offering
greater robustness to image quality." Fast (~15s/page), and clearly the strongest
of the pure-ML options right now. **Limitations that matter to us**: focuses on
pitch and rhythm on treble/bass clefs, and explicitly neglects dynamics,
articulations and double accidentals. Also — critically — I found no evidence it
extracts **lyrics**, and its stated scope is pitch/rhythm. For a *singing*
practice app, losing the words is a big deal.

**[oemer](https://github.com/BreezeWhite/oemer)** — Python, end-to-end deep
learning, `pip install oemer`. Designed for phone photos of sheet music, handles
skew. Superseded in quality by homr. Western notation only, no handwriting.
Worth keeping as a low-dependency option for the "photograph your part" mobile
flow, but not as the primary engine.

**[PDF2Muse](https://github.com/thedivergentai/PDF2Muse)** — thin CLI that
rasterises PDF pages, runs oemer per page, stitches the MusicXML back together,
and can shell out to the MuseScore CLI for `.mscx`. Useful as a *reference for
the page-stitching logic* (which is a real problem — OMR engines work per-image,
scores are multi-page and parts must be concatenated across page breaks). Its
own README warns the pipeline "may produce weak or malformed notation, even for
clean PDFs" and that every score needs review. Take the stitching idea, not the
dependency.

### On accuracy numbers

There is now a proper benchmark: the [Sheet Music Benchmark
(SMB)](https://arxiv.org/abs/2506.10488), 685 pages spanning monophony,
pianoform and quartet textures, plus **OMR-NED**, a normalised edit distance
metric that scores individual elements (noteheads, beams, pitches, accidentals)
rather than a single blunt symbol error rate. There's an open benchmark
comparing Audiveris, homr and oemer on SMB with OMR-NED. **Recommendation: don't
take anyone's marketing accuracy claim — run our own two-page eval** on a real
piano-vocal page (a public domain G&S vocal score from IMSLP is a legal, honest
proxy for a Guys and Dolls page) and score the three engines on: parts detected,
lyrics captured, pitch accuracy, and how mangled the piano reduction is.

### Commercial options, for completeness

Worth knowing about as an escape hatch, all paid APIs/SDKs: **PlayScore 2**
(mobile-first, good at playback from photos), **SmartScore NG**, **Soundslice**'s
scanning importer (very good, and their player is essentially the product we're
describing), **Newzik**'s MusicXML conversion. If OMR quality turns out to be the
thing that kills the product, buying it is a legitimate answer.

### Verdict on stage 2

> **Update — this has now been tested.** See
> [omr-evaluation.md](omr-evaluation.md) for results on a real *Guys and Dolls*
> vocal book. Short version: homr's note data is decent, but it extracts **no
> lyrics at all**, doesn't name its parts, and flattens any page whose systems
> have differing staff counts into a single line. Audiveris remains untested
> (its build is unreachable from this sandbox) and is now a must-test rather
> than a default. The review step is load-bearing, not polish.

Default to **Audiveris in batch mode** for uploaded PDFs (best part structure,
handles multipage, exports lyrics), with **homr** available as a per-page second
opinion for photos and for pages Audiveris chokes on. Treat OMR output as a
*draft*: build a review/correct step into the product from day one rather than
pretending the conversion is clean. And make "upload MusicXML instead" a
first-class, prominently offered path.

---

## 3. Stage 3: MusicXML → per-part MIDI + rehearsal metadata

The easy, well-solved stage. **[music21](https://music21.org)** (MIT, Python)
does all of it in one library: parse MusicXML/MEI/MIDI, walk `score.parts`,
export any subset to MIDI, read lyrics off notes, and resolve tempo marks.

`spike/score_to_parts.py` in this repo is a working, tested implementation. On
`bach/bwv66.6` (music21's corpus, a real SATB chorale) it produces:

```
Bach chorale: 4 parts, 10 measures
  00-soprano   group=soprano   |  01-alto  group=alto
  02-tenor     group=tenor     |  03-bass  group=bass
```

…one `.mid` per part, a combined `mix.mid`, and a `score.json` carrying the
measure/beat map (quarter offset → seconds, time signature per bar) and a lyric
timeline with syllable-level `begin`/`middle`/`end` markers — verified separately
on a synthetic lyric score. That JSON is exactly the contract the browser player
needs for the beat counter, the loop-by-bar UI and the bouncing-ball lyrics.

Other libraries considered:

- **[mido](https://mido.readthedocs.io)** — low-level MIDI file/message I/O.
  Right tool if we need to hand-assemble a MIDI file with specific
  channel/program assignments, or rewrite tempo maps. Complements music21.
- **[pretty_midi](https://github.com/craffel/pretty-midi)** — nice
  `Instrument`-centric model with times in absolute seconds. Good for analysis
  and for generating the per-part audio render offline; overlaps music21 for our
  purposes.
- **[miditoolkit](https://pypi.org/project/miditoolkit/)** — supports tempo,
  time signature, markers **and lyrics**, plus piano-roll conversion. Useful if
  we ever ingest MIDI-with-lyrics files directly (a lot of the old choral MIDI
  archives are exactly that).
- **Verovio's `renderToMIDI()`** — can do MusicXML→MIDI entirely client-side.
  Attractive for a no-backend prototype; less control over per-part splitting.

### The SATB problem — a real gotcha, though not the worst one

> **Update:** testing found a bigger structural problem than divisi — systems
> whose staff count changes mid-page. See
> [omr-evaluation.md §3](omr-evaluation.md). Divisi is below; read both.


**In a musical theatre vocal score, SATB parts are usually not separate parts.**
The chorus is typically notated on one or two staves with divisi — two voices per
staff, stems up/down — not four labelled parts the way a choral octavo has. So
`score.parts` will hand back something like `["Voice", "Piano"]`, not
`["Soprano", "Alto", "Tenor", "Bass"]`.

Getting a real SATB mixer therefore needs voice splitting: within a staff, split
by music21 `Voice` objects where the notation has them, and fall back to
stem-direction / chord-member splitting (top note → soprano, bottom → alto) where
it doesn't. `spike/score_to_parts.py` currently classifies parts by name and
lyric presence, which is right for choral MusicXML but **will need the divisi
splitter added before it handles a real MT vocal score**. This is the single
biggest piece of unbudgeted work in the pipeline, and it's worth prototyping
early against a real page. Related risk: OMR reliably confusing which divisi
voice a notehead belongs to, which makes the splitter's input noisy too.

---

## 4. Stage 4: the browser player

### Rendering the score

**[Verovio](https://github.com/rism-digital/verovio)** (RISM Digital, LGPL) is
the recommendation. C++ compiled to WASM with a JS toolkit, native MEI with
MusicXML and Humdrum importers, renders to SVG. Two toolkit methods make it the
right choice for us specifically:

- `renderToMIDI()` → base64 MIDI of the rendered score.
- `renderToTimemap()` → array of `{tstamp (ms), qstamp (quarters), tempo, on[],
  off[]}` entries keyed to SVG element IDs. **This is note-level playback
  synchronisation handed to you on a plate** — highlight the current note, follow
  the cursor, auto-turn the page, and derive loop points from clicked bars.

**[OpenSheetMusicDisplay](https://github.com/opensheetmusicdisplay/opensheetmusicdisplay)**
(VexFlow-based, by PhonicScore) is the main alternative — arguably nicer default
engraving and a built-in playback cursor. Its companion
**[osmd-audio-player](https://github.com/jimutt/osmd-audio-player)** already
implements exactly our mixer: play/pause/repeat and **per-instrument volume**,
with configurable instruments and tempo change. Its own README calls it early
and breaking-change-prone, and it's been quiet, but the demo proves the concept
and the code is a good read.

### Making sound

The mixer is, technically, just per-channel gain nodes. Options:

- **[spessasynth_lib](https://github.com/spessasus/SpessaSynth)** — a real
  SF2/DLS SoundFont synthesiser in Web Audio, with full MIDI channel handling.
  Best sound quality per byte, and channel-level control is native. This is what
  `musicxml-player` uses.
- **[smplr](https://github.com/danigb/smplr)** — sampled instruments for Web
  Audio, zero setup, can read `.sf2` directly. The maintained successor to
  `soundfont-player` (which is archived and points here). Simplest path to
  "sounds like a piano, not a beep."
- **[soundfont-player](https://github.com/danigb/soundfont-player)** — archived.
  Only relevant because half the tutorials online still use it. Use smplr.
- **[Tone.js](https://tonejs.github.io)** — not a synth for our purposes but an
  excellent transport/scheduling layer: `Tone.Transport` gives sample-accurate
  looping, tempo ramps, and a metronome click, which covers "looping" and "count
  beats" directly.
- **WebAudioFont** — another prerendered-soundfont option, good quality, similar
  role to smplr.

A distinctive quality win available cheaply: **render the vocal lines with a
"vocal-ish" patch (choir aahs / voice oohs) and pan each SATB part**, so soloing
the tenor sounds like a singer rather than a marimba. Cyberbass's well-known
weakness is that everything is a piano beep with no dynamics; not repeating that
is real product differentiation.

### Pre-built integrations worth reading before building

- **[musicxml-player](https://github.com/infojunkie/musicxml-player)**
  (TypeScript, GPL-3.0, active) — loads MusicXML, renders via Verovio or OSMD or
  pre-rendered assets, plays via Web Audio (spessasynth_lib) or Web MIDI, syncs
  through timemaps and handles repeats/jumps. Closest existing thing to our
  player. **GPL-3.0 is a real licensing decision** — fine for an open-source app,
  a constraint if this ever goes closed/commercial. Same applies to Audiveris and
  homr (AGPL-3.0), though running AGPL software as a server-side batch tool
  without modifying it is the ordinary case.
- **html-midi-player** (Magenta) — `<midi-player>`/`<midi-visualizer>` web
  components. Great for a 30-minute proof that our generated MIDI plays; not
  enough control for a real mixer.
- **music21j** — JS port of music21 with bundled soundfonts. Interesting but
  narrower than Verovio for rendering.

---

## 5. The escape hatch: audio stem separation

If OMR quality on real vocal scores turns out to be unusable, there's a
completely different route to the same product: take an audio rehearsal track and
split it. **[Demucs](https://github.com/adefossez/demucs)** v4 (`htdemucs`,
hybrid transformer) separates vocals/drums/bass/other, with `--two-stems=vocals`
for a karaoke split and `htdemucs_6s` adding piano and guitar.

Honest assessment: this gives a *vocals vs band* fader, not an SATB mixer —
source separation cannot pull an alto line out of a four-part chorus. And the
same licensing problem applies with knobs on (separating a cast recording is
making a derivative of a commercial recording). Useful as a supplementary
feature over user-supplied audio, not as the core.

---

## 6. Proposed architecture

```
                    ┌──────────────── ingest ────────────────┐
   user upload ────▶│ PDF ─┬─▶ Audiveris (batch) ─┐          │
   IMSLP/CPDL ─────▶│      └─▶ homr (per page)  ──┤          │
   MusicXML/MIDI ──▶│  (skips OMR entirely) ──────┴─▶ MusicXML
                    └────────────────────────────────────────┘
                                      │
                              review & correct  ← MD fixes OMR errors, marks cuts
                                      │
                          music21 (score_to_parts.py)
                                      │
              ┌───────────────────────┼───────────────────────┐
        parts/*.mid              score.json                mix.mid
     (one per voice/inst)   measures · beats · lyrics
                                      │
                    ┌─────────────────▼─────────────────┐
                    │  browser: Verovio SVG + timemap   │
                    │  spessasynth/smplr per-part gain  │
                    │  Tone.Transport loop + metronome  │
                    └───────────────────────────────────┘
```

Suggested build order, riskiest-first:

1. **Player against known-good MusicXML** (a PD SATB chorale). Proves the mixer,
   looping, beat count and lyric display with zero OMR risk. `score.json` from
   the spike is already the input format.
2. **Divisi/voice splitter** in music21 — the SATB problem from §3, prototyped
   against a real piano-vocal page.
3. **OMR bake-off** — Audiveris vs homr vs oemer on two real pages, scored
   honestly. This decides whether stage 2 is viable at all.
4. **Ingest + review UI** — upload, convert, correct.
5. **Production workspaces** — the licensing-shaped feature that makes it
   shippable.

## 7. Open questions

- Does Audiveris's MusicXML carry lyrics reliably enough to drive the words
  display, or do we need a separate text pass? (Test in step 3.)
- Transposition — MT keys get changed constantly for a given cast. music21 can
  transpose trivially; worth making a first-class control.
- Cuts and "safety" bars: real productions cut bars. The review step needs to
  express that, and the timemap has to survive it.
- Do we need offline audio rendering (server-side FluidSynth → per-part MP3) for
  weak mobile devices, or is Web Audio synthesis enough everywhere?
- Licence posture for the app itself, given AGPL/GPL components (§4).
