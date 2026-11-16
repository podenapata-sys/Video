#!/usr/bin/env python3
"""seen-ammu mix -> build/mix.wav: emotional piano bed (from the মায়ের দুটো থালা upload) looped with a crossfade,
fade in 1 s / out 2 s, dipped ~10 dB under the slot-5 voice note (same span as the waveform), soft UI SFX; -14 LUFS."""
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "build"
SFX = ROOT.parent.parent / "kits/reel-kit/assets/sfx"
SR = 48000


def dec(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


tl = json.loads((B / "timeline.json").read_text())
env = json.loads((B / "music_env.json").read_text())
N = int(round(tl["total"] * SR))
m = dec(ROOT / "assets/music.wav")
xf, bed = int(2.5 * SR), m.copy()
while len(bed) < N:
    r = np.linspace(0, np.pi / 2, xf)[:, None]
    bed = np.vstack([bed[:-xf], bed[-xf:] * np.cos(r) + m[:xf] * np.sin(r), m[xf:]])
bed = bed[:N].copy()
db = np.zeros(N)
a, b = env["dip"]
db[int(a * SR):int(b * SR)] = -10.0
k = int(0.3 * SR)
db = np.convolve(np.pad(db, (k, k), mode="edge"), np.ones(k) / k, mode="same")[k:-k]
bed *= (10 ** (db / 20))[:, None]
fi, fo = int(1.0 * SR), int(2.0 * SR)
bed[:fi] *= np.linspace(0, 1, fi)[:, None]
bed[-fo:] *= np.linspace(1, 0, fo)[:, None]
fx = np.zeros((N, 2), np.float32)
for c in json.loads((B / "sfx.json").read_text()):
    x = dec(SFX / f"{c['sfx']}.wav")
    x = x / (np.abs(x).max() or 1) * c["gain"]
    o = int(round(c["t"] * SR))
    n = min(len(x), N - o)
    if n > 0:
        fx[o:o + n] += x[:n]
bed_rms = float(np.sqrt(np.mean(bed ** 2)) + 1e-9)
raw = B / "mix_raw.wav"
sf.write(raw, bed / bed_rms * 0.12 + fx * 0.35, SR, subtype="FLOAT")
meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
mm = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
norm = (f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={mm['input_i']}:measured_TP={mm['input_tp']}:"
        f"measured_LRA={mm['input_lra']}:measured_thresh={mm['input_thresh']}:offset={mm['target_offset']}")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", f"{norm},aresample={SR},apad=whole_len={N},atrim=end_sample={N}",
                "-ar", str(SR), "-ac", "2", str(B / "mix.wav")], check=True)
raw.unlink()
print("mix.wav", tl["total"], "s")
