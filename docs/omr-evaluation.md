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
| **Audiveris 5.9.0** | Ran, after clearing two build blockers. (1) `javax.media:jai-core:1.1.3` is not on Maven Central and lives on `repository.jboss.org`, which this sandbox's network policy blocks — but **no Audiveris source file imports `javax.media.jai`**; it is declared only for the JPEG2000 codec, so deleting that one line in `app/build.gradle` resolves the graph, at the cost of JPEG2000 input that scanned scores don't use. (2) 5.9.0 needs JDK 25 (`invalid source release: 25`); `openjdk-25-jdk-headless` is in the Ubuntu archive. Batch mode then works headless: ~30 s/page. |

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

### Finding 5 — Audiveris is the only engine that reads words and part names

This is the result that matters, and it reverses the interim conclusion. On
pages 216 and 220 Audiveris produced:

- **Lyrics — around 38 syllables across the two pages**, syllabified, attached
  to notes. OCR quality is mediocre (`yﬂu'vc` for "you've", `tn` for "to",
  `151` for "be", `ﬂy` for "dy") but the text is recognisably there and
  correctable: `Luck if yﬂu'vc av er been la ﬂy to be gin with`. Compare zero
  from both other engines, on every page.
- **Part names read off the staff labels** — parts correctly named `T` and `B`,
  plus several variants of the `Ens.` bracket label OCR'd as `Ell.`, `Elsi.`,
  `E15.`, `En.`. Imperfect, but it is *reading the labels at all*, which is the
  information the mixer needs and which neither other engine attempts.
- **Three-staff parts modelled as such** — the log shows
  `Part#1{ staves[3] configs:[5]}`, i.e. it understands a bracketed group of
  three staves as one structure.

Its failure here is **over-segmentation**: 9 logical parts across two pages
where there should be 3. The varying system layout makes it create new logical
parts rather than matching staves to existing ones — the same underlying
difficulty that defeats homr, failing in the opposite direction.

**That direction matters enormously.** Merging over-segmented parts in a review
UI is a few clicks. Un-interleaving three parts that have been concatenated
end-to-end, as homr does on page 216, is not recoverable at all — the
information about what was simultaneous is simply gone. An engine that splits
too much is a usable starting point; an engine that flattens is not.

It is not clean: one `NullPointerException` while exporting a fermata
(`PartwiseBuilder.processFermata`) was logged, though the export still
completed.

### Finding 6 — the full-score comparison

All 10 pages, both viable engines, against ground truth:

| | Ground truth | homr | Audiveris 5.9 |
|---|---|---|---|
| Notes | — | 620 | **619** |
| **Lyric syllables** | ~300 | **0** | **283** |
| Divisi kept as chords | present | 41 (wrong parts) | 16 |
| Logical parts | 3 (Sky, `T`, `B`) | 18 | 20 |
| Staff labels read | `Sky`, `T`, `B`, `Ens.` | none | `T`, `B`, and `Ens.` as `Ell.`/`Els.`/`E15.`/`En.` |
| Time | — | ~15 s/page | ~30 s/page |

The note yield is a dead heat — 619 against 620. Everything that separates them
is structure and text, and there Audiveris wins outright: **283 syllables against
zero**, plus real staff labels.

Audiveris also split the score into two "movements" at a key change, which is
harmless: movement 1 is the 40-bar opening solo section as a **single correct
part with 74 syllables attached**, exactly right. The over-segmentation is all
in movement 2, where the ensemble writing starts.

Neither engine gets the part count right. But 20-parts-to-merge is an afternoon
in a review UI; homr's page-216 output is unrecoverable.

### Finding 7 — nothing homr produces is *named*, and divisi lands on the wrong part

homr labels its output `Voice`, `Piano`, `Piano`. There is no `Sky` / `T` / `B`,
because the engine doesn't read the staff labels. Worse, on page 220 the divisi
chords were attached to part 0 — the *solo* line, which has no chords at all in
the original — rather than to the `T` staff where they belong.

So the mixer cannot be built automatically from this output. Which is the
answer to the question the research doc left open.

## 4. What this changes about the plan

**"Upload a PDF, get a mixer with no human in the loop" does not work today.**
Note accuracy is fine. What no engine gets fully right is the *structure* —
which line is which — and only Audiveris gets the lyrics at all.

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
3. **Audiveris is the engine to build on**, confirmed rather than assumed. It
   is the only one that reads lyrics and staff labels, and its structural
   failure mode (over-segmenting parts) is recoverable in review where homr's
   (flattening parts into sequence) is not. Budget work for merging its logical
   parts and for cleaning up its lyric OCR — not for replacing it.

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
