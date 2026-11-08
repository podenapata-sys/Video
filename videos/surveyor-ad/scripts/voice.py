#!/usr/bin/env python3
"""Surveyor ad: voice lines -> scene grid + clip fitting (timing.json) and the voice track.

  python3 scripts/voice.py        (run from videos/surveyor-ad/)

The voice drives the timeline (user's brief):
- each line keeps every word; only leading/trailing silence is trimmed (30 ms of air kept)
- scenes 1-7: 0.4 s lead + voice + 0.6 s tail (1.2 s after scenes 1, 3, 7); scene 8: 0.4 s + voice + 2 s hold
- over 82 s -> padding shrinks in steps, never the voice
Clip fit: trim when long; when short, slow down (never below 0.8x); still short -> hold the last frame (slow zoom).
Writes assets/vo/trim/voN.wav, assets/vo/voice.wav and timing.json.
"""
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
VO = ROOT / "assets" / "vo"
TRIM = VO / "trim"
SR, FPS = 48000, 30
MAX_TOTAL = 82.0
OVERLAP = 0.4          # visual overlap per cut (transitions)
MIN_RATE = 0.8
# clips whose own audio is AI speech or music (measured: syllabic modulation / harmonic drone) -> muted
MUTED = {2: "AI dialogue", 4: "AI dialogue", 7: "tonal music drone", 8: "tonal music drone"}
# (lead, tail, long tail for 1/3/7, final hold for 8)
STEPS = [(0.4, 0.6, 1.2, 2.0), (0.4, 0.5, 1.0, 2.0), (0.3, 0.4, 0.8, 1.8), (0.25, 0.3, 0.6, 1.5)]


def frames(t):
    return round(t * FPS) / FPS


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def silences(a, d, noise=-40):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                        f"silencedetect=noise={noise}dB:d={d}", "-f", "null", "-"], input=a.tobytes(), capture_output=True)
    err = p.stderr.decode()
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(st, en + [None] * (len(st) - len(en))))


def trim_ends(a):
    dur = len(a) / SR
    lead, end = 0.0, dur
    for s, e in silences(a, 0.04):
        if s < 0.01:
            lead = max(0.0, (e or dur) - 0.03)
        if e is None or e >= dur - 0.02:
            end = min(end, s + 0.03)
    out = a[int(lead * SR):int(end * SR)].copy()
    f = int(0.005 * SR)
    out[:f] *= np.linspace(0, 1, f)
    out[-f:] *= np.linspace(1, 0, f)
    return out


def clip_len(n):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(ROOT / "assets" / "clips" / f"scene{n}.mp4")], capture_output=True, text=True).stdout)


def main():
    TRIM.mkdir(parents=True, exist_ok=True)
    lines = []
    for n in range(1, 9):
        a = trim_ends(decode(VO / f"vo{n}.mp3"))
        sf.write(TRIM / f"vo{n}.wav", a, SR)
        lines.append(len(a) / SR)
    for lead, tail, long_tail, hold in STEPS:
        lens = [frames(lead + d + (hold if n == 8 else long_tail if n in (1, 3, 7) else tail)) for n, d in enumerate(lines, 1)]
        if sum(lens) <= MAX_TOTAL:
            break
    total = round(sum(lens), 4)
    scenes, t = [], 0.0
    print(f"padding: lead {lead}, tail {tail}, long tail {long_tail}, final hold {hold}; total {total:.2f}s")
    for n, (d, L) in enumerate(zip(lines, lens), 1):
        need = L + (OVERLAP if n < 8 else 0) + (OVERLAP / 2 if n > 1 else 0)  # visible span incl. transitions
        src = clip_len(n) - 0.05
        rate = 1.0 if src >= need else max(MIN_RATE, src / need)
        play = src / rate                     # how long the clip actually runs at that rate
        hold_from = None if play >= need else round(play, 3)   # then the frozen last frame takes over
        scenes.append({"n": n, "start": round(t, 4), "length": L, "vo_at": round(t + lead, 4), "speech": round(d, 3),
                       "rate": round(rate, 4), "clip_play": round(min(play, need), 3), "hold_from": hold_from,
                       "muted": n in MUTED, "mute_reason": MUTED.get(n, "")})
        print(f"  scene {n}: {t:6.3f}-{t + L:6.3f} ({L:.3f}s) voice {t + lead:.3f}-{t + lead + d:.3f}  clip rate {rate:.2f}"
              f"{'  + hold last frame from ' + str(hold_from) + 's' if hold_from else ''}{'  [muted: ' + MUTED[n] + ']' if n in MUTED else ''}")
        t += L
    N = int(round(total * SR))
    v = np.zeros(N, np.float32)
    for s in scenes:
        a, _ = sf.read(TRIM / f"vo{s['n']}.wav", dtype="float32")
        o = int(round(s["vo_at"] * SR))
        v[o:o + len(a)] += a[:N - o]
    sf.write(VO / "voice.wav", np.stack([v, v], 1), SR)
    (ROOT / "timing.json").write_text(json.dumps({"total": total, "lead": lead, "scenes": scenes}, indent=1))


if __name__ == "__main__":
    main()
