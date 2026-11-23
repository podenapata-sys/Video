#!/usr/bin/env python3
"""Mix -> build/mix.wav: voiceover at 0 dB (master); bgm (30 s, looped only if needed), 23 dB under the
voice (RMS of speech), a further -3 dB across the CTA beat, fade in 1 s / out 2 s; -14 LUFS, TP -1.5."""
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
voice = dec(B / "voice.wav")[:N]
voice = np.vstack([voice, np.zeros((N - len(voice), 2), np.float32)])
m = dec(ROOT / "assets/bgm.wav")
xf, bed = int(2.0 * SR), m.copy()
while len(bed) < N:
    r = np.linspace(0, np.pi / 2, xf)[:, None]
    bed = np.vstack([bed[:-xf], bed[-xf:] * np.cos(r) + m[:xf] * np.sin(r), m[xf:]])
bed = bed[:N].copy()
db = np.zeros(N)
b6 = next(b for b in tl["beats"] if b["n"] == 3)
db[int(b6["start"] * SR):] = -3.0
k = int(0.2 * SR)
db = np.convolve(np.pad(db, (k, k), mode="edge"), np.ones(k) / k, mode="same")[k:-k]
speech = np.concatenate([voice[int(a * SR):int(b * SR)] for a, b in tl["spans"].values()])
bed = bed / rms(bed) * rms(speech) * 10 ** (-23 / 20) * (10 ** (db / 20))[:, None]
fi, fo = int(1.0 * SR), int(2.0 * SR)
bed[:fi] *= np.linspace(0, 1, fi)[:, None]
bed[-fo:] *= np.linspace(1, 0, fo)[:, None]
raw = B / "mix_raw.wav"
sf.write(raw, voice + bed, SR, subtype="FLOAT")
meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-2.0:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
mm = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
norm = (f"loudnorm=I=-14:TP=-2.0:LRA=11:linear=true:measured_I={mm['input_i']}:measured_TP={mm['input_tp']}:"
        f"measured_LRA={mm['input_lra']}:measured_thresh={mm['input_thresh']}:offset={mm['target_offset']}")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", f"{norm},aresample={SR},apad=whole_len={N},atrim=end_sample={N}",
                "-ar", str(SR), "-ac", "2", str(B / "mix.wav")], check=True)
raw.unlink()
print("mix.wav", tl["total"], "s")
