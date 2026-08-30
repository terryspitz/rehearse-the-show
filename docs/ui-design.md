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
  loop points.
- Lyrics per part rather than one shared line (needs the OCR work from the
  [OMR evaluation](omr-evaluation.md)).
- Tempo without pitch change — free once playback is synthesised from MIDI
  rather than from rendered stems.
- The part-mapping review step, which is what turns Audiveris output into these
  faders.
