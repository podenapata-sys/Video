#!/usr/bin/env python3
"""Clinic Reel mix -> build/mix.wav: voiceover master, music looped (2 s equal-power crossfade) and sidechain-ducked
under the voice, subtle SFX (Reel Kit set; the brief's sfx/ folder was not provided), two-pass loudnorm I=-14, TP=-1."""
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "build"
SFX = ROOT.parent.parent / "kits" / "reel-kit" / "assets" / "sfx"
SR = 48000


def dec(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


tl = json.loads((B / "timeline.json").read_text())
N = int(round(tl["total"] * SR))
pad = lambda x: np.vstack([x[:N], np.zeros((max(0, N - len(x)), 2), np.float32)])
voice = pad(dec(B / "voice.wav"))
m = dec(ROOT / "audio" / "music.wav")
xf, bed = int(2.0 * SR), m.copy()
while len(bed) < N:
    r = np.linspace(0, np.pi / 2, xf)[:, None]
    bed = np.vstack([bed[:-xf], bed[-xf:] * np.cos(r) + m[:xf] * np.sin(r), m[xf:]])
bed = bed[:N].copy()
fi, fo = int(0.5 * SR), int(1.5 * SR)
bed[:fi] *= np.linspace(0, 1, fi)[:, None]
bed[-fo:] *= np.linspace(1, 0, fo)[:, None]
sf.write(B / "bed_raw.wav", bed, SR)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(B / "bed_raw.wav"), "-i", str(B / "voice.wav"), "-filter_complex",
                "[0:a]volume=-9dB[m];[1:a]volume=4,aformat=channel_layouts=stereo[k];[m][k]sidechaincompress=threshold=0.02:ratio=8:attack=30:release=450:makeup=1[d]",
                "-map", "[d]", "-ar", str(SR), "-ac", "2", str(B / "bed.wav")], check=True)
(B / "bed_raw.wav").unlink()
mix = voice + pad(dec(B / "bed.wav"))
fx = np.zeros((N, 2), np.float32)
for c in json.loads((B / "sfx.json").read_text()):
    x = dec(SFX / f"{c['sfx']}.wav")
    x = x / (np.abs(x).max() or 1) * c["gain"]
    o = int(round(c["t"] * SR))
    n = min(len(x), N - o)
    if n > 0:
        fx[o:o + n] += x[:n]
raw = B / "mix_raw.wav"
sf.write(raw, mix + fx * 0.5, SR, subtype="FLOAT")
meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.7:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
mm = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
norm = (f"loudnorm=I=-14:TP=-1.7:LRA=11:linear=true:measured_I={mm['input_i']}:measured_TP={mm['input_tp']}:"
        f"measured_LRA={mm['input_lra']}:measured_thresh={mm['input_thresh']}:offset={mm['target_offset']}")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", f"{norm},aresample={SR},apad=whole_len={N},atrim=end_sample={N}",
                "-ar", str(SR), "-ac", "2", str(B / "mix.wav")], check=True)
raw.unlink()
print("mix.wav", tl["total"], "s")
