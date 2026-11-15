#!/usr/bin/env python3
"""Mix -> build/mix.wav: voiceover from 0.5 s; music looped/trimmed, ~15 dB below the voice (RMS), ducked a further
4 dB while the voice speaks (line spans, 0.15 s ramps), fade in 1 s / out 2 s; loudnorm -14 LUFS, TP -1.5."""
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "build"
SR = 48000


def dec(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


rms = lambda x: float(np.sqrt(np.mean(x ** 2)) + 1e-9)
tl = json.loads((B / "timeline.json").read_text(encoding="utf-8"))
N = int(round(tl["total"] * SR))
voice = np.zeros((N, 2), np.float32)
v = dec(ROOT / "assets/voiceover.mp3")
o = int(tl["voice_at"] * SR)
voice[o:o + len(v)] = v[:N - o]
m = dec(ROOT / "assets/music.wav")
xf, bed = int(2.0 * SR), m.copy()
while len(bed) < N:
    r = np.linspace(0, np.pi / 2, xf)[:, None]
    bed = np.vstack([bed[:-xf], bed[-xf:] * np.cos(r) + m[:xf] * np.sin(r), m[xf:]])
bed = bed[:N].copy()
speech = np.concatenate([voice[int(l["start"] * SR):int(l["end"] * SR)] for l in tl["lines"]])
db = np.full(N, -15.0)
for l in tl["lines"]:
    db[int((l["start"] - 0.1) * SR):int((l["end"] + 0.1) * SR)] = -19.0
k = int(0.15 * SR)
db = np.convolve(np.pad(db, (k, k), mode="edge"), np.ones(k) / k, mode="same")[k:-k]
bed = bed * (rms(speech) / rms(bed)) * (10 ** (db / 20))[:, None]
fi, fo = int(1.0 * SR), int(2.0 * SR)
bed[:fi] *= np.linspace(0, 1, fi)[:, None]
bed[-fo:] *= np.linspace(1, 0, fo)[:, None]
raw = B / "mix_raw.wav"
sf.write(raw, voice + bed, SR, subtype="FLOAT")
meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
mm = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
norm = (f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={mm['input_i']}:measured_TP={mm['input_tp']}:"
        f"measured_LRA={mm['input_lra']}:measured_thresh={mm['input_thresh']}:offset={mm['target_offset']}")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", f"{norm},aresample={SR},apad=whole_len={N},atrim=end_sample={N}",
                "-ar", str(SR), "-ac", "2", str(B / "mix.wav")], check=True)
raw.unlink()
print("mix.wav", tl["total"], "s")
