#!/usr/bin/env python3
"""Future Stack promo: talking-head clips -> jump-cut segment list, voice track, timeline.json.

  python3 scripts/timeline.py      (run from videos/futurestack-promo/)

One clip per script section (PT-1 hook ... PT-6 close). Silence is cut (user request): leading/trailing silence goes,
and every inner pause of PAUSE_CUT s or longer is removed (PAD kept on each side), giving jump cuts. The picture
alternates a 1.0 / 1.1 zoom per segment (build.py) so the cuts read as deliberate.
"""
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "media"
SR = 48000
PAUSE_CUT, PAD, LEAD, TAIL = 0.30, 0.06, 0.05, 0.15
END_HOLD = 1.1      # after the last word: blow-away effect
END_CARD = 5.0      # brief: end card, no voice, 5 s


def dec(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def silences(a, d=0.12, noise=-38):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                        f"silencedetect=noise={noise}dB:d={d}", "-f", "null", "-"], input=a.tobytes(), capture_output=True)
    e = p.stderr.decode()
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", e)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", e)]
    return list(zip(st, en + [len(a) / SR] * (len(st) - len(en))))


def speech_segments(a):
    dur = len(a) / SR
    sil = silences(a)
    start, end = 0.0, dur
    inner = []
    for s, e in sil:
        if s < 0.02:
            start = e
        elif e >= dur - 0.02:
            end = s
        else:
            inner.append((s, e))
    segs, cur = [], max(0.0, start - LEAD)
    for s, e in inner:
        if e - s >= PAUSE_CUT:
            segs.append((cur, s + PAD))
            cur = e - PAD
    segs.append((cur, min(dur, end + TAIL)))
    return segs


def main():
    t = 0.0
    segments, sections, voice = [], [], []
    for n in range(1, 7):
        a = dec(MD / "clips" / f"pt{n}.mp4")
        segs = speech_segments(a)
        sec_start = t
        sec_audio = []
        for i, (s, e) in enumerate(segs):
            seg = a[int(s * SR):int(e * SR)].copy()
            f = int(0.006 * SR)
            seg[:f] *= np.linspace(0, 1, f)
            seg[-f:] *= np.linspace(1, 0, f)
            sec_audio.append(seg)
            segments.append({"clip": n, "seg": i, "src_in": round(s, 3), "src_out": round(e, 3), "t": round(t, 3),
                             "dur": round(e - s, 3)})
            t += e - s
        sa = np.concatenate(sec_audio)
        sf.write(MD / f"sec{n}.wav", sa, SR)
        voice.append(sa)
        cut = sum(e - s for s, e in segs)
        print(f"  section {n}: {sec_start:6.2f}-{t:6.2f}  ({len(segs)} segment(s), kept {cut:.2f}s of {len(a)/SR:.2f}s)")
        sections.append({"n": n, "start": round(sec_start, 3), "end": round(t, 3)})
    speech_end = t
    total = round(speech_end + END_HOLD + END_CARD, 3)
    v = np.concatenate(voice)
    v = np.concatenate([v, np.zeros(int((total - speech_end) * SR) + 10, np.float32)])[:int(round(total * SR))]
    sf.write(MD / "voice.wav", np.stack([v, v], 1), SR)
    (ROOT / "timeline.json").write_text(json.dumps({"segments": segments, "sections": sections, "speech_end": round(speech_end, 3),
                                                    "blow_at": round(speech_end, 3), "card_at": round(speech_end + END_HOLD, 3),
                                                    "total": total}, indent=1))
    print(f"speech {speech_end:.2f}s, end card {speech_end + END_HOLD:.2f}-{total:.2f}s, {len(segments)} segments")


if __name__ == "__main__":
    main()
