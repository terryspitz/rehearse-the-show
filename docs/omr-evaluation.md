# OMR bake-off: a real *Guys and Dolls* vocal book page

This is the step-3 evaluation the [library research](research-libraries.md) said
had to happen before trusting the OMR stage. Test material: a scanned copy of
"Luck Be A Lady", pages 212–221 of a *Guys & Dolls* vocal book, supplied by the
user from their own production materials. Nothing derived from it is committed
to this repo.

## 1. What the source actually is

Worth stating precisely, because it changes the problem:

- **A scan, not a born-digital PDF.** No fonts, no text layer — each page is a
  single 1200×1500 JPEG (≈140 dpi effective). Text extraction yields nothing, so
  OMR is the only route.
- **A singer's book, not a piano-vocal score.** No piano reduction at all — just
  the vocal lines with lyrics, bar numbers, rehearsal marks and cues. That's
  *easier* than the piano-vocal case the research doc worried about: no dense
  chordal accompaniment to mangle.
- **But the layout is harder than a choral octavo**, in four specific ways:

  1. **The staff count changes within a page.** Where Sky sings alone the system
     is one staff. Where the Crapshooters join, it becomes three: Sky (treble),
     then a bracketed `Ens.` group of `T` (treble) and `B` (bass). Page 216 has
     five 1-staff systems followed by one 3-staff system.
  2. **Real divisi.** The `T` staff carries 2- and 3-note chords (bars 174–175),
     as does `B` (bars 168–169).
  3. **Shared lyrics.** The `T` staff's lyric line serves both `T` and `B`.
  4. **Mid-piece key and meter changes** — 5 flats → 2 sharps → 3 flats, and
     cut-common → 4/4.

**Ground truth for staff counts** was measured, not eyeballed, by horizontal
projection of dark pixels (`spike/gt_staves.py` approach — a staff line spans
most of the page width). Total: **79 staves across the 10 pages**.

## 2. Which engines actually ran

| Engine | Result |
|---|---|
| **homr 0.7.0** | Ran on all 10 pages. ~15–40 s/page on CPU. Needed a venv — `antlr4-python3-runtime` won't build against Ubuntu's patched system setuptools (`AttributeError: install_layout`). |
| **oemer** | Ran on one page, but only after two fixes. Current `onnxruntime` 1.29 rejects the bundled model outright (`ConvTranspose ... Attribute pads must not contain negative values`), so it needs pinning to ≤1.20; and `bbox.find_lines` crashes on OpenCV 5, which changed `HoughLinesP`'s return from Nx1x4 to Nx4. With both patched it takes **3m56s per page**, ~16× homr. |
| **Audiveris 5.9** | **Could not be tested in this environment.** Its build needs `javax.media:jai-core:1.1.3`, which is not on Maven Central and lives on `repository.jboss.org` — blocked by this sandbox's network policy (403 at CONNECT). This is an environment limitation, not a defect in Audiveris, and it leaves the engine the research doc *recommended* untested. See §5. |

## 3. homr results, all 10 pages

| Page | True staves | Layout | homr parts | Measures | Notes | Chords | **Lyrics** |
|---|---|---|---|---|---|---|---|
| 212 | 6 | uniform 1-staff | 1 ✅ | 26 | 83 | 0 | **0** |
| 213 | 7 | uniform 1-staff | 1 ✅ | 25 | 58 | 0 | **0** |
| 214 | 7 | uniform 1-staff | 1 ✅ | 26 | 65 | 0 | **0** |
| 215 | 7 | uniform 1-staff | 1 ✅ | 24 | 50 | 0 | **0** |
| 216 | 8 | **mixed** (5×1 + 1×3) | 1 ❌ | 26 | 63 | 0 | **0** |
| 217 | 9 | uniform 3-staff | 3 ✅ | 11 | 60 | 15 | **0** |
| 218 | 8 | **mixed** (3+1+1+3) | 1 ❌ | 23 | 47 | 5 | **0** |
| 219 | 9 | uniform 3-staff | 3 ✅ | 13 | 72 | 5 | **0** |
| 220 | 9 | uniform 3-staff | 3 ✅ | 12 | 61 | 12 | **0** |
| 221 | 9 | uniform 3-staff | 3 ✅ | 13 | 61 | 4 | **0** |
| **Total** | **79** | | **18** | | **620** | | **0** |

### Finding 1 — zero lyrics, on every page

Not a single syllable across ten pages, despite the lyrics being clean printed
text under every vocal staff. This confirms the suspicion flagged in the
research doc: homr's scope is pitch and rhythm. **For a singing practice app
this is disqualifying on its own** — a rehearsal track with no words is half a
product. Lyrics have to come from somewhere else: Audiveris (which runs
Tesseract), a separate OCR pass on the lyric band under each staff, or manual
entry in the review step.

### Finding 2 — the structural failure is precisely predictable

The pattern in the table is clean: **homr is right whenever every system on a
page has the same staff count, and collapses when the count varies mid-page.**
Eight of ten pages are structurally correct. The two failures — 216 and 218 —
are exactly the two pages where the layout changes.

The failure mode is worth naming, because it's worse than "some notes are
wrong": **simultaneity is turned into sequence.** On page 216, homr emitted one
continuous 26-bar line. Rendering that output back through Verovio shows the
Sky line running to bar ~21, then the clef flipping to bass and the key changing
mid-system as the `T` staff and then the `B` staff are appended *end to end*. Three
parts that should sound together are laid out one after another. The audio
render of that page is audibly nonsense — not slightly wrong, structurally wrong.

### Finding 3 — where it works, it works well

On the uniform pages the note data is genuinely good. Comparing page 220 bars
164–167 against homr's output: the rhythm of all three staves matches
(quarter–rest–quarter–quarter, then four quarters, then the dotted-half
cadence), and the 5-flat key signature is correct. Divisi chords survive *as
chords* — 12 of them on page 220, in the 2- and 3-note sizes the score actually
has.

### Finding 4 — oemer is worse here on every axis

With both compatibility fixes applied, oemer on page 220 (ground truth: 3 staves,
12 bars, one key signature of 5 flats, ~12 divisi chords):

| | Ground truth | homr | oemer |
|---|---|---|---|
| Parts | 3 | **3** ✅ | 2 ❌ |
| Measures | 12 | **12** ✅ | 14 ❌ |
| Key signatures on the page | 1 (−5) | **−5** ✅ | −6, −2, +5, +6 ❌ |
| Divisi preserved as chords | ~12 | 12 (wrong part) | **0** ❌ |
| Lyrics | many | 0 ❌ | 0 ❌ |
| Time per page | — | ~15 s | 3m56s |

Finding four different key signatures on a page that has one is the telling
number: it means accidentals are being mis-assigned wholesale. Combined with
losing divisi entirely and needing two source patches just to execute, **oemer
is not a candidate.** This matches its author's own pointer to homr as the
successor project.

### Finding 5 — nothing is *named*, and divisi lands on the wrong part

homr labels its output `Voice`, `Piano`, `Piano`. There is no `Sky` / `T` / `B`,
because the engine doesn't read the staff labels. Worse, on page 220 the divisi
chords were attached to part 0 — the *solo* line, which has no chords at all in
the original — rather than to the `T` staff where they belong.

So the mixer cannot be built automatically from this output. Which is the
answer to the question the research doc left open.

## 4. What this changes about the plan

**The "upload a PDF, get a mixer" flow does not work today.** Not because of
note accuracy — that's decent — but because the two things the mixer needs
most, *which line is which* and *what the words are*, are exactly the two
things this engine doesn't produce.

Three consequences, in order of importance:

1. **The review step is not optional polish — it is load-bearing.** A human has
   to map staves to voice parts once per song. `spike/render_demo.py` now takes
   `--assign 0=solo,1=tenor,2=bass` for exactly this, and with that one line of
   human input the page-220 output renders correct, listenable practice mixes.
   Thirty seconds of MD time per song, not thirty minutes.
2. **Lyrics need their own pipeline.** The lyric band under each staff is clean
   printed text at a predictable vertical offset. A targeted OCR pass (Tesseract
   on the strip between staves, aligned to notehead x-positions) is a tractable
   piece of work and probably more reliable than hoping an OMR engine does it.
3. **Audiveris moves from "default choice" to "must test".** It is the only
   candidate that models part-groups and brackets — the exact thing that breaks
   here — and it runs OCR for lyrics. Both known failures are in its wheelhouse.
   Until it is tested, the OMR stage has no proven engine.

   Note on the blocked build: `javax.media:jai-core` is declared in
   `app/build.gradle` but **no Audiveris source file imports `javax.media.jai`** —
   it is there for the JPEG2000 codec in `jai-imageio-jpeg2000`. Dropping that
   one line lets the build resolve, at the cost of JPEG2000 input support, which
   scanned scores don't use.

**The divisi problem is real but is not the blocker.** The bigger one is
mixed-staff-count systems, which I hadn't anticipated and which is more common
in show scores than divisi — every number where a soloist alternates with the
chorus has it.

## 5. Reproducing this

```bash
pip install homr                      # in a venv; system setuptools breaks antlr4
homr page.png                         # writes page.musicxml next to the image

python spike/omr_report.py page.musicxml               # structural scorecard
python spike/render_demo.py page.musicxml -o demo/ \
    --assign 0=solo,1=tenor,2=bass                     # listenable mixes
```

To test Audiveris where the network allows it:

```bash
git clone --branch 5.9.0 https://github.com/Audiveris/audiveris.git
cd audiveris && ./gradlew build -x test
./gradlew run --args="-batch -export -output out/ score.pdf"
```
