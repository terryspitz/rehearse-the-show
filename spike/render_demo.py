#!/usr/bin/env python3
"""Spike: render listenable rehearsal mixes from a score.

Demonstrates what the browser mixer will do, but offline: render every part
separately, then mix them at different gains to produce the practice tracks a
singer actually wants — full mix, "my part forward", "my part alone with a
click".

Requires fluidsynth + a GM soundfont, and ffmpeg for mp3 encoding:
    apt-get install fluidsynth fluid-soundfont-gm ffmpeg

Usage:
    python spike/render_demo.py bach/bwv10.7 -o demo/
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from music21 import corpus, converter, instrument, stream

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_to_parts import beat_map, classify, slugify

SR = 44100

# General MIDI programs. Choir Aahs for voices so a soloed line sounds like a
# singer rather than a marimba — the thing CyberBass et al. get wrong.
PROGRAM = {"soprano": 52, "alto": 52, "tenor": 52, "bass": 52, "voice": 52,
           "solo": 53, "instrument": 0}

# Spread the voices across the stereo field so parts stay separable by ear even
# in the full mix.
PAN = {"soprano": -0.5, "alto": -0.18, "solo": 0.0, "tenor": 0.18, "bass": 0.5}

# name -> (description, {group: gain}, click?). Groups absent from a score are
# simply skipped, so the same presets work for SATB choral and for a show's
# solo + male-chorus layout.
FULL = {"soprano": 1.0, "alto": 1.0, "solo": 1.0, "tenor": 1.0, "bass": 1.0}
QUIET = {k: 0.22 for k in FULL}

MIXES = {
    "full-mix": ("everything balanced", FULL, False),
    "tenor-forward": ("tenor loud, everything else quiet underneath",
                      {**QUIET, "tenor": 1.0}, False),
    "tenor-alone-with-click": ("tenor only, with a metronome count",
                               {k: 0.0 for k in FULL} | {"tenor": 1.0}, True),
}


def render_part(part: stream.Part, group: str, midi_path: Path, wav_path: Path, soundfont: Path) -> np.ndarray:
    """Write one part to MIDI, render it to audio, return a mono float array."""
    holder = stream.Score()
    inst = instrument.Instrument()
    inst.midiProgram = PROGRAM.get(group, 0)
    part = part.flatten().notesAndRests.stream()
    part.insert(0, inst)
    holder.insert(0, part)
    holder.write("midi", fp=str(midi_path))

    subprocess.run(
        ["fluidsynth", "-ni", "-F", str(wav_path), "-r", str(SR), "-g", "0.7",
         str(soundfont), str(midi_path)],
        check=True, capture_output=True,
    )
    with wave.open(str(wav_path), "rb") as w:
        frames = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
        if w.getnchannels() == 2:
            frames = frames.reshape(-1, 2).mean(axis=1)
    return frames


def click_track(measures: list[dict], length: int) -> np.ndarray:
    """A woodblock-ish tick on every beat, accented on beat 1 of each bar."""
    out = np.zeros(length, dtype=np.float32)
    for i, m in enumerate(measures):
        nxt = measures[i + 1]["seconds"] if i + 1 < len(measures) else m["seconds"] + 2.0
        beats = max(1, m["beats"])
        step = (nxt - m["seconds"]) / beats
        for b in range(beats):
            start = int((m["seconds"] + b * step) * SR)
            if start >= length:
                continue
            n = min(int(0.035 * SR), length - start)
            t = np.arange(n) / SR
            freq, amp = (1600.0, 0.28) if b == 0 else (1100.0, 0.16)
            out[start:start + n] += (amp * np.sin(2 * np.pi * freq * t) * np.exp(-t * 90)).astype(np.float32)
    return out


def to_stereo(mono: np.ndarray, pan: float, gain: float) -> np.ndarray:
    """Equal-power pan. pan is -1 (left) .. +1 (right)."""
    angle = (pan + 1) * np.pi / 4
    return gain * np.stack([mono * np.cos(angle), mono * np.sin(angle)], axis=1)


def write_audio(stereo: np.ndarray, base: Path) -> Path:
    peak = float(np.abs(stereo).max()) or 1.0
    pcm = (np.clip(stereo / peak * 0.89, -1, 1) * 32767).astype("<i2")
    wav = base.with_suffix(".wav")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    if shutil.which("ffmpeg"):
        mp3 = base.with_suffix(".mp3")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-b:a", "192k", str(mp3)], check=True)
        wav.unlink()
        return mp3
    return wav


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("score", help="path to MusicXML, or a music21 corpus path")
    ap.add_argument("-o", "--out", default="demo", help="output directory")
    ap.add_argument("--soundfont", default="/usr/share/sounds/sf2/FluidR3_GM.sf2")
    ap.add_argument(
        "--assign", default="",
        help="override the guessed part groups, e.g. '0=solo,1=tenor,2=bass'. "
             "OMR output rarely names its parts, so this stands in for the "
             "review step where a human maps staves to voices.",
    )
    args = ap.parse_args()

    src = Path(args.score)
    score = converter.parse(str(src)) if src.exists() else corpus.parse(args.score)
    out = Path(args.out)
    work = out / "parts"
    work.mkdir(parents=True, exist_ok=True)

    measures = beat_map(score)

    assigned = {}
    for item in filter(None, args.assign.split(",")):
        idx, _, group = item.partition("=")
        assigned[int(idx)] = group.strip()

    streams: dict[str, list[np.ndarray]] = {}
    for i, part in enumerate(score.parts):
        name, group = classify(part, i)
        group = assigned.get(i, group)
        slug = f"{i:02d}-{slugify(name)}"
        print(f"  rendering {name} -> {group}")
        audio = render_part(part, group, work / f"{slug}.mid", work / f"{slug}.wav", Path(args.soundfont))
        streams.setdefault(group, []).append(audio)

    length = max(len(a) for group in streams.values() for a in group)
    padded = {
        g: np.sum([np.pad(a, (0, length - len(a))) for a in items], axis=0)
        for g, items in streams.items()
    }

    for mix_name, (desc, gains, want_click) in MIXES.items():
        stereo = np.zeros((length, 2), dtype=np.float32)
        for group, gain in gains.items():
            if gain and group in padded:
                stereo += to_stereo(padded[group], PAN.get(group, 0.0), gain)
        if want_click:
            click = click_track(measures, length)
            stereo += np.stack([click, click], axis=1)
        path = write_audio(stereo, out / mix_name)
        print(f"  {path.name:<32} {desc}")

    for wav in work.glob("*.wav"):
        wav.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
