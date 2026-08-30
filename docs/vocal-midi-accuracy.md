# Where the vocal MIDI doesn't match the PDF

Audiveris 5.9 on the scanned *Guys & Dolls* vocal book (pages 212–221, 140 dpi
JPEG), merged into three lines by `spike/merge_parts.py`. MIDI lives in
`licensed/vocal-midi/` — gitignored.

## What's right

**The opening is essentially perfect.** Bars 1–4 against the printed page:

| | Printed | Parsed |
|---|---|---|
| Key / meter | 5♭, cut common | 5♭, `2/2` ✅ |
| Pickup | rest + quarter on A♭4 | `rest/1.0  A-4/1.0` ✅ |
| Bar 1 | C♭5 A♭4 C♮5 A♭4, four quarters | `C-5 A-4 C5 A-4` all `/1.0` ✅ |
| Bar 2 | F4 half + rest + quarter | `F4/2.0  rest/1.0  A-4/1.0` ✅ |
| Bar 4 | half + rest + D♭4 | `F4/2.0  rest/1.0  D-4/1.0` ✅ |

Pitches, rhythms, the C♭/C♮ accidental pair and the pickup are all correct.
**Note-level recognition is not the problem.** Everything below is structure and
text.

## What's wrong, worst first

### 1. About 30 bars are missing — roughly one bar in six

The parse spans **147 bars**. The printed book reaches **bar 183** on the last
page and runs a little beyond. The independently-scanned piano score, at 300 dpi,
parses to **190 bars** and is almost certainly right.

I checked whether multi-bar rests were hiding the difference: they aren't —
Audiveris read every `<multiple-rest>` as `1`, so the printed "2 bars rest"
symbols each collapsed to a single bar. That accounts for part of the loss; the
rest is bars dropped outright in the low-resolution scan.

**Consequence:** bar numbers in the MIDI drift progressively out of step with
your book. By the end they are ~30 bars early. Any "go to bar 104" feature would
land in the wrong place.

### 2. The Bass line is about 60% missing

| | Notes |
|---|---|
| Tenor | 179 |
| Bass | **72** (40% of tenor) |

The Crapshooters sing homophonically — the `B` staff mirrors `T` rhythm for
rhythm through "Roll 'em", "Luck be a lady", "Roll will ya". So the two counts
should be close to equal. **24 bars have a tenor note and no bass note at all**;
only 1 has the reverse.

**Consequence:** the bass fader is unusable as it stands. This is the single
worst defect for the app's purpose.

### 3. Lyrics are there but roughly a third are garbled

283 syllables captured. Against a hand-built list of the song's actual words,
**at least 60% come through correctly** — a floor, not a ceiling, since my word
list was incomplete and some flagged tokens are in fact right.

The errors are systematic, not random, which means they're fixable:

- The `ﬁ`/`ﬂ` **ligature glyphs stand in for various letters** — `la ﬂy` = "la-dy",
  `eve ﬂing` = "eve-ning". The commonest single error.
- **Digits substituted for letters**: `R911` = "Roll", `151` = "be", `011` = "on",
  `d};` and `{1}?` = "dy".
- `u`↔`n`↔`m` confusion: `nut` = "out", `mmn fnr dﬂuht` = "room for doubt",
  `Cam in'`/`Cum in'` = "Comin'", `yﬂu'vc` = "you've".
- **Page furniture read as lyrics.** The footer `#25 — Luck Be A Lady` appears in
  the lyric stream twice as `#25` and twice as `Lady`. Words that were never sung
  are now attached to notes.

### 4. Sixteen key signatures where the score has three

The book goes 5♭ → 2♯ → 3♭. The parse reports key changes at 16 points,
including impossible rapid alternations (`key+0`, `key-1`, `key-2`, `key-3` within
a few bars). The piano scan, at 300 dpi, found exactly the right three.

**Consequence:** accidentals are mis-assigned around each spurious change, and
this is why `spike/align_scores.py` cannot match the two books — only 1 of 10
musical anchors agrees.

### 5. The parts needed merging before the MIDI was usable

Audiveris emitted **20 logical parts** for 3 lines, minting a new one at every
change of system layout. `spike/merge_parts.py` folds them back by OCR'd staff
label (`T`, `B`, and the many manglings of `Ens.` — `Ell.`, `Elsi.`, `E15.`,
`En.`) plus clef. That heuristic is doing real work and is unverified bar by bar;
treat the part assignment as a first guess.

## The one thing that would fix most of this

**Rescan the vocal book at 300 dpi bitonal**, matching the piano score you
supplied. Same engine, same song, same afternoon:

| | Vocal book (140 dpi JPEG) | Piano score (300 dpi bitonal) |
|---|---|---|
| Logical parts | 20 for 3 lines | **2 for 2 staves** ✅ |
| Bars | 154 (~30 short) | **190** ✅ |
| Key signatures | 16, mostly spurious | **3, all correct** ✅ |
| Meter changes | missed | **2/2→4/4→2/2 at bars 21/23** ✅ |

Every defect above except the lyric OCR is plausibly a resolution artefact. The
lyric errors are a separate, tractable job: a targeted Tesseract pass over the
lyric band beneath each staff, with a song-specific word list, rather than
general full-page OCR.

---

# Update: up-resing fixed most of this

No higher-resolution vocal book was available, so the question became whether
up-resing the scan we have would help. It does — substantially.

## Why it works: it was a scale problem, not only an information one

| | Staff interline |
|---|---|
| Vocal book, as supplied | **8 px** |
| Piano score (parsed cleanly) | **20 px** |

Audiveris estimates interline spacing and its symbol classifiers are built
around roughly 20 px. At 8 px the vocal book sits far outside the engine's
operating window. Scaling by 2.5× adds no new information, but it puts the
input exactly where the piano score already was — which is why interpolation
helps here despite the usual intuition that it can't.

## Results, whole score, same engine and settings

| | As supplied | Up-resed 2.5× |
|---|---|---|
| Bars | 154 | **176** (piano says 190) |
| Notes | 619 | **769** |
| Lyric syllables | 283 | **427** |
| …of which clean | 179 (63%) | **380 (89%)** |
| Key signatures | 7 distinct, 4 spurious | **3: −5, −3, +2 — exactly right** |
| Bass notes ÷ tenor notes | 40% | **79%** |
| Logical parts (truth: 3) | 20 | 21 — unchanged |

Qualitatively: `Luck 151 a gun ﬂu man see` became
`Stick with me, ba by, I'm the fel low you came in with`.

## The clever step made it worse

Sauvola adaptive thresholding was the obvious thing to try, since the piano PDF
is bitonal and clean while the vocal is JPEG with ringing round every glyph. On
the two test pages it recovered six more syllables but cost key-signature
accuracy (3 distinct instead of the correct 2) and part count (9 vs 7). Plain
Lanczos resizing wins. `spike/upres.py` therefore binarizes only on request.

## Alignment now works

With correct key signatures the two books line up — but not the way the first
aligner assumed. All 10 anchors match **in sequence**, while the drift grows
monotonically:

```
anchor      vocal  piano  drift
key-5           0      0     +0
time4/4        20     21     +1
key+2          43     45     +2
key-3          56     63     +7
key-5          72     79     +7
key+2         112    123    +11
key-3         129    141    +12
key-5         143    157    +14
```

That is not a constant offset — it is the vocal parse falling steadily behind
as each printed multi-bar rest collapses to a single measure. `align_scores.py`
now matches anchors as a sequence and emits a piecewise-linear bar map
(`0→0  20→21  43→45  56→63  72→79  112→123  129→141  143→157  176→190`).

## What up-resing did *not* fix

**Part over-segmentation is unchanged** — 21 logical parts for 3 lines. That is
structural, not a resolution artefact, exactly as predicted: Audiveris mints a
new logical part whenever a system's staff count changes, and no amount of
input quality alters that.

It did, however, force a better solution. The label-text heuristic in
`merge_parts.py` broke completely on the up-resed scan, because the OCR
manglings changed: `Ens.` came out as `Bus.`, `Eu.`, `£13.`, and `T` as `'I'`.
Matching that text is a losing game. What is stable is that **the solo staff
carries no printed label at all**, so Audiveris leaves its default "Voice",
while every ensemble staff is labelled and yields *something*. Routing on label
*presence* plus clef, rather than label content, survives both scans.
