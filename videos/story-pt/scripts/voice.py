#!/usr/bin/env python3
"""Silence-cut the 18 ElevenLabs lines into one voice track, with word timings.

  python3 scripts/voice.py

- each line (assets/vo/NN.mp3) is trimmed to its speech, and any pause inside it
  longer than MAX_PAUSE is shortened to MAX_PAUSE
- lines are joined with GAP of silence (LONG_GAP before the final question)
- every word is force-aligned with pocketsphinx against the script text
- writes assets/vo/voice.wav, lines.json and words.json (times in the final track)
"""
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from pocketsphinx import Decoder

ROOT = Path(__file__).resolve().parent.parent
VO = ROOT / "assets" / "vo"
SR = 48000
LEAD = 0.15        # silence before the first word
GAP = 0.14         # between lines
LONG_GAP = {18: 0.7}  # beat before "Do you open it?"
MAX_PAUSE = 0.28   # longest pause kept inside a line
TAIL = 0.06        # room left after the last word of a line
FADE = int(0.005 * SR)

LINES = [
    "The text came at two fourteen a.m.", "It was from no name.", "Then the phone buzzed again.",
    "Stay indoors. Do not answer.", "Her apartment is on floor nine.", "The stairs are the only way down.",
    "Rule number one. Don't answer unknown calls.", "It's her mother's voice.", "Rule number two. Count the stairs.",
    "Count every step.", "There's one more step than there should be.", "Rule number three. Porch light off.",
    "The lobby light is on. Don't go toward it.", "Someone is already in the doorway.",
    "Rule number four. Never say yes to the door.", 'It asks, "Can I come in?"',
    "It says her name right. It says it wrong.", "Do you open it?",
]


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def silences(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=noise=-35dB:d=0.12", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(st, en + [None] * (len(st) - len(en))))


def faded(x):
    x = x.copy()
    if len(x) > 2 * FADE:
        x[:FADE] *= np.linspace(0, 1, FADE)
        x[-FADE:] *= np.linspace(1, 0, FADE)
    return x


def cut_line(path):
    """Speech of one line with head/tail trimmed and inner pauses capped."""
    audio = decode(path)
    dur = len(audio) / SR
    keep, cur = [], 0.0
    for s, e in silences(path):
        e = dur if e is None else e
        if s <= 0.01:                      # leading silence
            cur = max(0.0, e - 0.03)
        elif e >= dur - 0.01:              # trailing silence
            keep.append((cur, min(dur, s + TAIL)))
            cur = dur
        elif e - s > MAX_PAUSE:            # long pause inside the line
            mid = (s + e) / 2
            keep.append((cur, mid - MAX_PAUSE / 2))
            cur = mid + MAX_PAUSE / 2
    if cur < dur:
        keep.append((cur, dur))
    return np.concatenate([faded(audio[int(a * SR):int(b * SR)]) for a, b in keep])


def words_of(line):
    line = line.replace("a.m.", "a m")
    return [w for w in re.sub(r"[^a-z' ]", " ", line.lower()).split() if w.strip("'")]


def align(audio, line):
    pcm16 = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                            "-f", "s16le", "-ar", "16000", "-ac", "1", "-"], input=audio.tobytes(),
                           capture_output=True, check=True).stdout
    dec = Decoder(samprate=16000, bestpath=False, loglevel="FATAL", beam=1e-100, wbeam=1e-80, pbeam=1e-100)
    dec.set_align_text(" ".join(words_of(line)))
    dec.start_utt()
    dec.process_raw(pcm16, full_utt=True)
    dec.end_utt()
    segs = [(re.sub(r"\(\d+\)$", "", s.word), s.start_frame / 100, (s.end_frame + 1) / 100) for s in dec.seg()
            if s.word not in ("<s>", "</s>", "<sil>", "(NULL)")]
    assert len(segs) == len(words_of(line)), f"aligned {len(segs)} of {len(words_of(line))}: {line}"
    return segs


def main():
    out = [np.zeros(int(LEAD * SR), dtype=np.float32)]
    t, lines, words = LEAD, [], []
    for n, text in enumerate(LINES, 1):
        if n > 1:
            g = LONG_GAP.get(n, GAP)
            out.append(np.zeros(int(g * SR), dtype=np.float32))
            t += g
        a = cut_line(VO / f"{n:02d}.mp3")
        segs = align(a, text)
        lines.append({"line": n, "start": round(t, 3), "end": round(t + len(a) / SR, 3), "text": text})
        words += [{"line": n, "word": w, "start": round(t + s, 3), "end": round(t + e, 3)} for w, s, e in segs]
        out.append(a)
        t += len(a) / SR
    out.append(np.zeros(int(0.4 * SR), dtype=np.float32))
    voice = np.concatenate(out)
    sf.write(VO / "voice.wav", voice, SR)
    (ROOT / "lines.json").write_text(json.dumps(lines, indent=1))
    (ROOT / "words.json").write_text(json.dumps(words, indent=1))
    raw = sum(len(decode(VO / f"{n:02d}.mp3")) for n in range(1, 19)) / SR
    print(f"voice.wav {len(voice) / SR:.2f}s (raw lines {raw:.2f}s), {len(words)} words")
    for l in lines:
        print(f"{l['line']:02d} {l['start']:6.2f}-{l['end']:6.2f}  {l['text']}")


if __name__ == "__main__":
    main()
