#!/usr/bin/env python3
"""SaHa GoLD ad mix -> media/mix.wav. Brief: voice 0 dB on top; BGM -12 dB under voice, up to -6 dB in gaps;
bass hit at 0.5 s; water under beat 5 at -15 dB (Clip-5's own splash audio); whooshes on the two whip pans. -14 LUFS."""
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "media"
SR = 48000


def rms(x):
    return float(np.sqrt(np.mean(x ** 2)) + 1e-9)


def dec(p, extra=()):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), *extra, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


tl = json.loads((ROOT / "timeline.json").read_text())
N = int(round(tl["total"] * SR))
voice = dec(MD / "voice.wav")[:N]
voice = np.vstack([voice, np.zeros((N - len(voice), 2), np.float32)])

# BGM envelope: -6 dB in gaps, -12 dB under each voice line, 0.15 s ramps (gain relative to the bed's own level)
bgm = dec(MD / "src" / "bgm.wav")[:N]
bgm = np.vstack([bgm, np.zeros((N - len(bgm), 2), np.float32)])
db = np.full(N, -6.0)
for b in tl["beats"]:
    s, e = b["voice"]
    db[int((s - 0.1) * SR):int((e + 0.05) * SR)] = -12.0
k = int(0.15 * SR)
db = np.convolve(np.pad(db, (k, k), mode="edge"), np.ones(k) / k, mode="same")[k:-k]
speech = np.concatenate([voice[int(b["voice"][0] * SR):int(b["voice"][1] * SR)] for b in tl["beats"]])
bed = bgm * (rms(speech) / rms(bgm)) * (10 ** (db / 20))[:, None]      # 0 dB = voice level; -12 under voice, -6 in gaps
fo = int(0.8 * SR)
bed[-fo:] *= np.linspace(1, 0, fo)[:, None]

fx = np.zeros((N, 2), np.float32)


def place(x, t, peak):
    x = x / (np.abs(x).max() or 1) * peak
    o = int(round(t * SR))
    n = min(len(x), N - o)
    fx[o:o + n] += x[:n]


place(dec(MD / "sfx" / "impact_hit.wav"), 0.5, 0.95)                       # bass hit on the flash
for n in (2, 5):                                                           # whip pans
    place(dec(MD / "sfx" / "whoosh_fast.wav"), tl["beats"][n - 1]["start"] - 0.2, 0.45)
# water: Clip-5 audio stretched to the beat's playback speed, -15 dB under the voice (RMS), 0.3 s fades
b5 = tl["beats"][4]
water = dec(MD / "src" / "Clip-5.mp4", ["-af", f"atempo={b5['speed']:.3f}"])
s0, s1 = b5["start"], b5["end"]
water = water[:int((s1 - s0 + 0.2) * SR)]
f = int(0.3 * SR)
water[:f] *= np.linspace(0, 1, f)[:, None]
water[-f:] *= np.linspace(1, 0, f)[:, None]
vs, ve = b5["voice"]
v_rms = rms(voice[int(vs * SR):int(ve * SR)])
water *= v_rms * 10 ** (-15 / 20) / rms(water)
o = int(s0 * SR)
fx[o:o + len(water)] += water[:N - o]

raw = MD / "mix_raw.wav"
sf.write(raw, voice + bed + fx, SR, subtype="FLOAT")
meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                      capture_output=True, text=True).stderr
mm = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
norm = (f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={mm['input_i']}:measured_TP={mm['input_tp']}:"
        f"measured_LRA={mm['input_lra']}:measured_thresh={mm['input_thresh']}:offset={mm['target_offset']}")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", f"{norm},aresample={SR},apad=whole_len={N},atrim=end_sample={N}",
                "-ar", str(SR), "-ac", "2", str(MD / "mix.wav")], check=True)
raw.unlink()
print("mix.wav", tl["total"], "s")
