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
