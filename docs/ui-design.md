# UI design: the rehearsal mixer

Live prototype: **https://claude.ai/code/artifact/71ac29d1-738b-482a-a7af-65f91a6fdbf1**
Source in [`design/`](../design/) (`_ui-styles.html` + `_ui-markup.html`; the build step
inlines the score JSON and base64 audio stems).

Phone-first, because that's where it gets used — on a bus, backstage, in a
church hall with headphones.

## What the prior art does

| App | The idea worth stealing |
|---|---|
| [Choir Player](https://www.choirplayer.com/) | SOLO / LYRICS / RESET LEVELS / SECTION / LOOP / SPEED / PITCH as the whole surface. Nothing else. |
| [Choralia](https://www.choralia.net/) | Three *training levels*: your part with clicks → all voices with yours emphasised → all voices equal. A progression, not just faders. |
| [CyberBass](https://cyberbass.org/) | The cautionary one: piano beeps, no dynamics. Proves that sounding decent is itself a feature. |

## Design decisions and why

**Rows, not channel strips.** A studio mixer is vertical faders side by side.
That's a desktop idiom — at 390 px wide, five vertical strips give you 70 px
each, below the [8–12 pt spacing](https://market.gluestack.io/blog/mobile-app-design-best-practices)
that stops mis-taps. One row per part, horizontal fader, full width. Slower to
compare at a glance, far better to actually operate with a thumb.

**Presets are relative to "I'm singing", not absolute.** This is the main idea.
Choir Player makes you build every mix by hand. Here you tell the app your part
once, and every preset re-computes around it: *Mine louder*, *Mine only*,
**Drop mine**. That last one is the one singers actually need and no preset list
usually has — everyone else plays, your line is silent, and you supply it. It's
Choralia's level 3, one tap away.

**Colour is identity, carried everywhere.** Each part keeps one hue across its
badge, edge stripe, fader thumb, pan dot and — later — its notes and lyric line
in the score. Four separated hues (cyan / violet / green / coral) plus a
deliberately desaturated slate for the accompaniment, which should recede.
Amber is reserved for transport and active state, so it never competes.

**Pan is a real feature, hidden by default.** Spatial separation buys
[up to 18 dB of release from masking](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9726925/) —
it is the cheapest way to make one line audible inside a chord, and far more
effective than just turning it up. But it's a set-once control, so it sits
behind the **Stereo** toggle rather than doubling the height of every row.

**The bar counter is the anchor, not a time code.** Rehearsal happens in bar
numbers — "from 104", "top of 25". So the header leads with a large bar number
and beat dots, and looping is expressed as *Bars 5–11*. Seconds are demoted to
small mono type in the transport.

**Count-in before every start.** Singers can't come in cold on a loop. Four
clicks precede playback and continue underneath, toggleable.

**Tempo is per section, not one global number.** The single 60–120% slider in
the transport was wrong the moment we looked at a real number. *Luck Be A Lady*
isn't one tempo: bar 1 is marked *Freely & Dramatically* — rubato, no fixed
pulse — and bar 22 cuts to *Brightly*, a definite up-tempo patter feel with the
triplet runs that prompted the [timing fix](vocal-midi-accuracy.md). Practising
"the fast bit" at 70% while leaving the rubato opening alone is a normal
rehearsal request, and one global slider can't do it — turning it down for the
triplets turns down the ballad too.

Two things worth being honest about, both found by the pipeline rather than
assumed:

- **Section text lives in the score, but only a good scan keeps it.** The
  300 dpi piano score's OMR captured `Freely & Dramatically` and `Brightly` as
  direction text at exactly the right bars. The vocal book — even up-resed —
  captured neither: zero `<words>` tempo directions survived on that scan.
  So section boundaries and labels *can* come from OMR, but only from the
  cleaner source, and only when a human confirms them in the review step.
- **No absolute BPM survives OMR at all.** Neither parse produced a single
  `<metronome>` mark or `<sound tempo>` value, on either book, at any
  resolution — a printed tempo marking like *Freely & Dramatically* is text and
  character, not a number to begin with. So a section's baseline tempo is
  always a human input (tap-tempo or typed BPM in the review step), never
  something the app can read off the page. The per-section slider is a
  **percentage of that baseline**, exactly like the existing global control —
  it's the *scoping* that's new, not the mechanism.

**Design**: a horizontal chip row, same visual language as *Balance*, one chip
per section (`① Freely & Dramatically`, `② Brightly`). Tapping a chip jumps
the playhead to that section's first bar. The transport's tempo slider stays
in the same place but becomes section-scoped: it reads and writes whichever
section the playhead is currently in, and its label names that section —
`78% · Brightly` — so a percentage never sits unlabelled and ambiguous.
Crossing a section boundary during playback swaps the *effective* rate
immediately, not by ramping: the printed tempo change is a hard cut in the
score, so smoothing over it would be lying about the music, not simplifying
the UI. A loop that starts inside a section plays at that section's rate,
full stop, even if a future bar-tap loop editor lets the range cross into the
next section — otherwise a loop's tempo would depend on which lap you're on.

| Section chip | Shows | Tap does |
|---|---|---|
| Inactive | Label, last-set % | Jump playhead to section start, become active |
| Active (playhead inside) | Label, live %, ring in the accent colour | Nothing new — it's already selected |
| Playing across a boundary | Automatically hands off to the next chip | — |

**A bug this surfaced, fixed while building it:** the count-in already in the
transport schedules its "go" moment with `setTimeout`, timed from whichever
tempo was active *when Play was pressed*. Tapping a different section during
that count-in — a very plausible sequence, not an edge case — let the stale
timer fire later and silently snap playback back to the original position.
Fixed by making every real start-of-playback go through one function that
first cancels any pending count-in, and by having that same function
guarantee the render loop is running rather than assuming whoever called it
already started one. Both bugs only showed up under a fast, automated
sequence of taps; a human testing by hand would likely not have hit either —
which is itself the case for testing the interaction programmatically rather
than trusting a manual click-through.


## Palette and type

| Token | Light | Dark |
|---|---|---|
| ground | `#F7F5F0` warm bone | `#0E1218` blue-biased near-black |
| surface | `#FFFFFF` | `#161C25` |
| accent | `#B8791B` | `#F2A83C` amber |
| soprano / alto / tenor / bass / piano | `#1E86AC` `#7B45B8` `#2F7C43` `#C1382A` `#5C6B7C` | `#4FC3E8` `#C08BF0` `#6BBF7A` `#EE6A5F` `#8A9AAC` |

Type: **Oswald** for the title and part badges — a condensed playbill face, the
right register for musical theatre, used sparingly. **IBM Plex Sans** for UI,
**IBM Plex Mono** with tabular figures for bar numbers and timecode.

## Still to build

- Notation view with the Verovio timemap driving a cursor, and tap-a-bar to set
  loop points — the natural way to define section boundaries by hand once one
  exists, rather than only from OCR'd tempo text.
- Lyrics per part rather than one shared line (needs the OCR work from the
  [OMR evaluation](omr-evaluation.md)).
- Tempo without pitch change — free once playback is synthesised from MIDI
  rather than from rendered stems. Per-section tempo (above) makes this more
  urgent, not less: pitch-shifting the rubato opening because you slowed down
  the patter section is a worse bug once tempo is scoped per section.
- The part-mapping review step, which is what turns Audiveris output into
  these faders — and, per above, into section boundaries and their baseline
  BPM as well. One review pass, three outputs.
