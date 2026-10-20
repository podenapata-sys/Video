#!/usr/bin/env python3
"""Join the 4 ElevenLabs chunks into one voice track, with punchline pauses.

  python3 scripts/voice.py

- chunks play 1 -> 4 with a CHUNK_GAP breath between them
- pauses.json: [{"chunk": 1, "sentence": 7, "extra": 1.2}, ...] inserts extra
  silence in the gap right BEFORE sentence N (0-based) of that chunk
- writes assets/vo/voice.wav and voice_map.json (every sentence's final start/end)
"""
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
VO = ROOT / "assets" / "vo"
SR = 44100
CHUNK_GAP = 0.8
FADE = int(0.005 * SR)  # 5ms fades at every cut, no clicks


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def sentences(path, dur):
    """Speech spans between pauses (silencedetect -35dB / 0.3s)."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=noise=-35dB:d=0.3", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    spans, cur = [], 0.0
    for s, e in zip(starts, ends + [dur]):
        if s - cur > 0.15:
            spans.append([cur, s])
        cur = e
    if dur - cur > 0.15:
        spans.append([cur, dur])
    return spans


def main():
    pauses = json.loads((ROOT / "pauses.json").read_text()) if (ROOT / "pauses.json").exists() else []
    out, vmap, t = [], [], 0.0
    for c in range(1, 5):
        audio = decode(VO / f"chunk{c}.mp3")
        dur = len(audio) / SR
        spans = sentences(VO / f"chunk{c}.mp3", dur)
        extra = {p["sentence"]: p.get("extra", 1.2) for p in pauses if p["chunk"] == c}
        pos, shift = 0, 0.0  # sample cursor in this chunk, seconds added so far
        for i, (s, e) in enumerate(spans):
            if i in extra and i > 0:
                cut = int((spans[i - 1][1] + s) / 2 * SR)  # middle of the silence before this sentence
                piece = audio[pos:cut].copy()
                piece[-FADE:] *= np.linspace(1, 0, FADE)
                out.append(piece)
                out.append(np.zeros(int(extra[i] * SR), dtype=np.float32))
                pos = cut
                shift += extra[i]
            vmap.append({"chunk": c, "sentence": i, "start": round(t + s + shift, 3), "end": round(t + e + shift, 3)})
        tail = audio[pos:].copy()
        if pos:
            tail[:FADE] *= np.linspace(0, 1, FADE)
        out.append(tail)
        t += dur + shift
        if c < 4:
            out.append(np.zeros(int(CHUNK_GAP * SR), dtype=np.float32))
            t += CHUNK_GAP
    voice = np.concatenate(out)
    sf.write(VO / "voice.wav", voice, SR)
    (ROOT / "voice_map.json").write_text(json.dumps(vmap, indent=1))
    print(f"voice.wav {len(voice) / SR:.2f}s, {len(vmap)} sentences, {len(pauses)} punchline pauses")


if __name__ == "__main__":
    main()
