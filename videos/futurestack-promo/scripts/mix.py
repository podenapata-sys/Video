#!/usr/bin/env python3
"""Future Stack promo audio: voice (jump-cut) + looped, ducked music + SFX cues -> media/mix.wav at -14 LUFS.

  python3 scripts/mix.py          (after build.py, which writes sfx.json)
"""
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "media"
SR = 48000


def dec(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def main():
    tl = json.loads((ROOT / "timeline.json").read_text())
    total = tl["total"]
    N = int(round(total * SR))
    voice = dec(MD / "voice.wav")[:N]
    voice = np.vstack([voice, np.zeros((N - len(voice), 2), np.float32)])
    # music: loop the 30 s bed with a 2 s equal-power crossfade, fade in 0.6 s, out 1.5 s
    m = dec(MD / "music" / "bgm.wav")
    xf = int(2.0 * SR)
    bed = m.copy()
    while len(bed) < N:
        a, b = bed[-xf:], m[:xf]
        r = np.linspace(0, np.pi / 2, xf)[:, None]
        bed = np.vstack([bed[:-xf], a * np.cos(r) + b * np.sin(r), m[xf:]])
    bed = bed[:N].copy()
    fi, fo = int(0.6 * SR), int(1.5 * SR)
    bed[:fi] *= np.linspace(0, 1, fi)[:, None]
    bed[-fo:] *= np.linspace(1, 0, fo)[:, None]
    sf.write(MD / "bed_raw.wav", bed, SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(MD / "bed_raw.wav"), "-i", str(MD / "voice.wav"), "-filter_complex",
                    "[0:a]volume=-4dB[m];[1:a]volume=4[k];[m][k]sidechaincompress=threshold=0.015:ratio=10:attack=30:release=400:makeup=1[d]",
                    "-map", "[d]", "-ar", str(SR), "-ac", "2", str(MD / "bed.wav")], check=True)
    (MD / "bed_raw.wav").unlink()
    bed = dec(MD / "bed.wav")[:N]
    bed = np.vstack([bed, np.zeros((N - len(bed), 2), np.float32)])
    # sfx
    fx = np.zeros((N, 2), np.float32)
    for c in json.loads((ROOT / "sfx.json").read_text()):
        x = dec(MD / "sfx" / f"{c['sfx']}.wav")
        peak = np.abs(x).max() or 1.0
        x = x / peak * c["gain"]
        o = int(round(c["t"] * SR))
        n = min(len(x), N - o)
        if n > 0:
            fx[o:o + n] += x[:n]
    raw = MD / "mix_raw.wav"
    sf.write(raw, voice + bed + fx * 0.6, SR, subtype="FLOAT")
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                           "-f", "null", "-"], capture_output=True, text=True).stderr
    mm = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    norm = (f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={mm['input_i']}:measured_TP={mm['input_tp']}:"
            f"measured_LRA={mm['input_lra']}:measured_thresh={mm['input_thresh']}:offset={mm['target_offset']}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", f"{norm},aresample={SR},apad=whole_len={N},atrim=end_sample={N}",
                    "-ar", str(SR), "-ac", "2", str(MD / "mix.wav")], check=True)
    raw.unlink()
    print("mix.wav", total, "s")


if __name__ == "__main__":
    main()
