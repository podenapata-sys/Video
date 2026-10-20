#!/usr/bin/env python3
"""Final sound mix: voice + looping 60Hz drone + door rattle + doorbell, with the drone drop.

  python3 scripts/mix.py      (run after scripts/voice.py; writes assets/vo/mix.wav)

Cue times come from voice_map.json, so they follow the voice if pauses change.
"""
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
SFX = ROOT / "assets" / "sfx"
SR = 48000
DRONE_DB = -25.0      # drone RMS level (dBFS)
RATTLE_GAIN_DB = 14   # the rattle file is very quiet (peak -21.8 dBFS)
BELL_GAIN_DB = -6
CEILING = 10 ** (-1 / 20)  # keep peaks under -1 dBFS


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()


def db(x):
    return 10 ** (x / 20)


def sentence(vmap, chunk, idx):
    return next(s for s in vmap if s["chunk"] == chunk and s["sentence"] == idx)


def ramp(n, up=True):
    r = np.linspace(0, 1, n, dtype=np.float32)[:, None]
    return r if up else 1 - r


def place(bus, clip, t, gain_db=0.0, cut_at=None):
    a = int(t * SR)
    if cut_at is not None:  # hard stop, with a 10ms fade so it doesn't click
        clip = clip[: max(0, int(cut_at * SR) - a)].copy()
        clip[-480:] *= ramp(min(480, len(clip)), up=False)
    bus[a:a + len(clip)] += clip[: len(bus) - a] * db(gain_db)


def drone_bed(n):
    """Loop the 1s drone with 60ms crossfades so the seam is inaudible, then set its RMS to DRONE_DB."""
    d = load(SFX / "drone.mp3")
    xf = int(0.06 * SR)
    loop = d[:-xf].copy()
    loop[:xf] = loop[:xf] * ramp(xf) + d[-xf:] * ramp(xf, up=False)
    bed = np.tile(loop, (n // len(loop) + 1, 1))[:n]
    rms = np.sqrt(np.mean(bed ** 2))
    return bed * (db(DRONE_DB) / rms)


def main():
    vmap = json.loads((ROOT / "voice_map.json").read_text())
    voice = load(ROOT / "assets" / "vo" / "voice.wav")
    n = len(voice) + int(0.6 * SR)
    mix = np.zeros((n, 2), dtype=np.float32)
    mix[: len(voice)] += voice

    # 1. drone under everything: 3s fade in, 2s fade out
    bed = drone_bed(n)
    env = np.ones((n, 1), dtype=np.float32)
    env[: 3 * SR] = ramp(3 * SR)
    env[-2 * SR:] = ramp(2 * SR, up=False)

    # 3b. drone drop: dead silence for 2s from "Apologies.", then creep back over 1s
    apol = sentence(vmap, 3, 23)["start"]
    a, b = int((apol - 0.03) * SR), int((apol + 2.0) * SR)
    env[a:b] = 0
    env[b:b + SR] = ramp(SR)
    mix += bed * env

    # 2. door rattle: on "If the handle moves" (Rule 4), just as the word "moves" lands
    handle = sentence(vmap, 3, 6)
    place(mix, load(SFX / "door-rattle.mp3"), handle["start"] + 0.85, RATTLE_GAIN_DB)

    # 3a. doorbell right after "And if the doorbell rings—", cut off dead at "Apologies."
    rings = sentence(vmap, 3, 22)
    place(mix, load(SFX / "doorbell.mp3"), rings["end"] + 0.05, BELL_GAIN_DB, cut_at=apol - 0.03)

    peak = float(np.max(np.abs(mix)))
    if peak > CEILING:  # soft-limit only the samples above the ceiling
        over = np.abs(mix) > CEILING * 0.9
        knee = CEILING * 0.9
        mix[over] = np.sign(mix[over]) * (knee + (CEILING - knee) * np.tanh((np.abs(mix[over]) - knee) / (CEILING - knee)))
    sf.write(ROOT / "assets" / "vo" / "mix.wav", mix, SR)
    print(f"mix.wav {n / SR:.2f}s  peak before limit {20 * np.log10(peak):.1f} dBFS, after {20 * np.log10(np.max(np.abs(mix))):.1f} dBFS")
    print(f"cues: rattle {handle['start'] + 0.85:.2f}s | doorbell {rings['end'] + 0.05:.2f}-{apol - 0.03:.2f}s | drone off {apol - 0.03:.2f}-{apol + 2:.2f}s")


if __name__ == "__main__":
    main()
