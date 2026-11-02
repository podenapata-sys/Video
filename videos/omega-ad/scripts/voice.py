#!/usr/bin/env python3
"""ElevenLabs scene lines (assets/vo/vo01..vo09.mp3) -> scene grid, cues and a -14 LUFS voice track per cut.

  python3 scripts/voice.py     (then scripts/build.py)

The lines run longer than the storyboard's slots, so the grid follows the voice (user's choice):
- inner pauses longer than MAX_PAUSE are shortened; each phrase's start is recorded
- scene length = max(storyboard length, LEAD + speech + TAIL); the CTA holds CTA_HOLD after its line (kit minimums)
- "30s" (also used by square and wide) keeps the natural voice; "15s" (scenes 1, 3, 5, 7, 9) speeds it up 8%
- cues: scene-relative times at which build.py brings in the element the voice is saying
Writes timing.json and assets/vo/voice-<cut>.wav (stereo, compressed, two-pass loudnorm to -14 LUFS).
"""
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
VO = ROOT / "assets" / "vo"
SR = 48000
MAX_PAUSE, LEAD, TAIL = 0.35, 0.15, 0.2
CTA_HOLD = {"30s": 1.5, "15s": 1.2}  # the kit's minimum final hold per cut
ORIG = {1: 3.0, 2: 4.0, 3: 3.5, 4: 3.0, 5: 3.5, 6: 2.5, 7: 3.5, 8: 3.0, 9: 4.0}  # storyboard scene lengths
CUTS = {"30s": (list(range(1, 10)), 1.0), "15s": ([1, 3, 5, 7, 9], 1.08)}


def decode(path, tempo):
    af = ["-af", f"atempo={tempo}"] if tempo != 1.0 else []
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), *af, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def silences(a, d):
    """Silence spans in a decoded clip (ffmpeg silencedetect on the samples)."""
    p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                        f"silencedetect=noise=-35dB:d={d}", "-f", "null", "-"], input=a.tobytes(), capture_output=True)
    err = p.stderr.decode()
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(st, en + [None] * (len(st) - len(en))))


def tighten(path, tempo):
    """Clip with leading/trailing silence trimmed and long inner pauses shortened; phrase start times."""
    a = decode(path, tempo)
    dur = len(a) / SR
    lead, end = 0.0, dur
    for s, e in silences(a, 0.04):
        if s < 0.01:
            lead = max(0.0, (e or dur) - 0.03)
            break
    inner = []
    for s, e in silences(a, 0.2):
        if e is None or e >= dur - 0.1:
            end = min(end, s + 0.05)
        elif s > lead + 0.05:
            inner.append((s, e))
    pieces, starts, t, cur = [], [], 0.0, lead
    for s, e in inner + [(end, None)]:
        starts.append(round(t, 3))
        seg = a[int(cur * SR):int(s * SR)]
        pieces.append(seg)
        t += len(seg) / SR
        if e is None:
            break
        gap = min(e - s, MAX_PAUSE)
        mid = (s + e) / 2
        pieces.append(a[int((mid - gap / 2) * SR):int((mid + gap / 2) * SR)])
        t += gap
        cur = e
    out = np.concatenate(pieces)
    f = int(0.004 * SR)
    out[:f] *= np.linspace(0, 1, f)
    out[-f:] *= np.linspace(1, 0, f)
    return out, starts


def cues_for(n, ph, speech):
    """Scene-relative times (s) for the elements the voice names."""
    p = [LEAD + s for s in ph]
    get = lambda i, d: round(p[i], 3) if i < len(p) else d
    return {1: {"b": get(1, LEAD + 2.0)},
            2: {"q0": get(0, LEAD), "q1": get(1, LEAD + 1.0), "q2": round(get(1, LEAD + 1.0) + 0.45, 3), "cap": get(2, LEAD + 2.2)},
            3: {"s": get(2, LEAD + 2.4)},
            5: {"s": get(1, LEAD + 1.8)},
            7: {"sw": get(1, LEAD + 1.6)},
            8: {"t1": get(1, LEAD + 1.6)},
            9: {"wa": get(1, LEAD + 2.2)}}.get(n, {})


def normalise(src, dst):
    """Stereo, gentle 3:1 compression, two-pass (measured, linear) loudnorm to -14 LUFS, exact length."""
    n = sf.info(src).frames
    comp = "acompressor=threshold=-24dB:ratio=3:attack=5:release=120:makeup=4dB"
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-af", f"{comp},loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                           "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    norm = (f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
            f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", f"{comp},{norm},apad=whole_len={n}",
                    "-ar", str(SR), "-ac", "2", str(dst)], check=True)  # no -t: it cuts short after loudnorm


def main():
    timing = {}
    for cut, (scenes, tempo) in CUTS.items():
        track, grid, cues, t = [], [], {}, 0.0
        for n in scenes:
            audio, ph = tighten(VO / f"vo{n:02d}.mp3", tempo)
            speech = len(audio) / SR
            need = LEAD + speech + (CTA_HOLD[cut] if n == 9 else TAIL)
            length = round(round(max(ORIG[n] if cut == "30s" else 0, need) * 30) / 30, 4)  # whole frames
            seg = np.zeros(int(round(length * SR)), np.float32)
            o = int(LEAD * SR)
            seg[o:o + len(audio)] = audio
            track.append(seg)
            grid.append({"n": n, "start": round(t, 4), "length": length})
            cues[n] = cues_for(n, ph, speech)
            print(f"{cut} scene {n}: {length:5.2f}s  speech {speech:4.2f}s  phrases at {[round(LEAD + s, 2) for s in ph]}")
            t += length
        total = round(t, 4)
        raw = VO / f"voice-{cut}-raw.wav"
        sf.write(raw, np.concatenate(track), SR)
        normalise(raw, VO / f"voice-{cut}.wav")
        raw.unlink()
        timing[cut] = {"total": total, "scenes": grid, "cues": cues}
        print(f"{cut}: total {total:.2f}s")
    (ROOT / "timing.json").write_text(json.dumps(timing, indent=1))


if __name__ == "__main__":
    main()
