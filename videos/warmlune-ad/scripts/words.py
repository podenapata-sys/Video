#!/usr/bin/env python3
"""Word timings for the exact script words -> words.json (global seconds).

  python3 scripts/words.py        (after scripts/voice.py)

Whisper could not run in this environment (huggingface.co, where the model lives, is blocked), so timing comes from the
voice itself:
1. speech/pause map of each tightened line (silencedetect + 10 ms RMS envelope)
2. the script's phrase breaks (, । ... ? !) are matched to the detected pauses by a monotonic DP on relative position
3. inside each phrase, words are spread over the speech time by syllable weight (Bangla vowel nuclei)
4. each word onset snaps to the deepest energy dip within +-110 ms (the gap between words)
Caption text is the user's script, never a transcription. Display swaps: ওয়ার্মলুন -> WarmLune, এল-সি-ডি -> LCD.
"""
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
SR = 48000

SCRIPT = [
    "মাসের ওই কয়েকটা দিন... ভেতরের কষ্টটা শুধু আমরাই বুঝি।",
    "ক্লাস, কাজ, সবকিছু অপেক্ষা করছে... কিন্তু শরীরটা যেন আর সঙ্গ দেয় না।",
    "প্ল্যান বদলে যায়... আর তখন দরকার, একটু নিজের যত্ন।",
    "তোমার আরামের মুহূর্তের জন্য... পরিচিত হও, ওয়ার্মলুনের সঙ্গে।",
    "তিনটি হিট লেভেল, এল-সি-ডি ডিসপ্লে, আর ভাইব্রেশন ম্যাসাজ।",
    "পুরোপুরি তারবিহীন, রিচার্জেবল... বই পড়ো, বিশ্রাম নাও, যেখানে খুশি।",
    "পিরিয়ড তোমার জীবনের একটা অংশ... পুরো জীবন নয়।",
    "ওয়ার্মলুন... কঠিন দিনে, একটু উষ্ণ আরাম। অর্ডার করতে, এখনই ইনবক্স করো।",
]
DISPLAY = {"ওয়ার্মলুনের": "WarmLune-এর", "ওয়ার্মলুন...": "WarmLune...", "এল-সি-ডি": "LCD"}
BREAK = re.compile(r"(\.\.\.|[,।?!])$")


def syllables(w):
    n = 0
    for i, ch in enumerate(w):
        o = ord(ch)
        nxt = w[i + 1] if i + 1 < len(w) else ""
        if 0x0985 <= o <= 0x0994:
            n += 1
        elif (0x0995 <= o <= 0x09B9 or 0x09DC <= o <= 0x09DF) and nxt != "্":
            n += 1
        elif ch == "-":
            n += 0.3
    return max(1.0, n) + 0.35  # + a little for the word joint


def envelope(a):
    h = int(SR * 0.01)
    k = len(a) // h
    return 20 * np.log10(np.sqrt(np.mean(a[:k * h].reshape(k, h) ** 2, axis=1)) + 1e-7)


def pauses(a):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                        "silencedetect=noise=-36dB:d=0.11", "-f", "null", "-"], input=a.astype(np.float32).tobytes(),
                       capture_output=True)
    err = p.stderr.decode()
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    dur = len(a) / SR
    return [(s, e) for s, e in zip(st, en) if s > 0.05 and e < dur - 0.05]


def align(words, a):
    dur = len(a) / SR
    ps = pauses(a)
    w = np.array([syllables(x) for x in words])
    cw = np.concatenate([[0], np.cumsum(w)]) / w.sum()
    breaks = [i + 1 for i, x in enumerate(words[:-1]) if BREAK.search(x)]  # word index after each break
    # speech-time coordinate (pauses removed) for matching
    speech = dur - sum(e - s for s, e in ps)
    def speech_pos(t):
        return (t - sum(min(e, t) - s for s, e in ps if s < t)) / speech
    pp = [speech_pos((s + e) / 2) for s, e in ps]
    # DP: assign each break to a distinct pause (monotonic) or none; cost = position mismatch, penalty for unmatched
    B, P = len(breaks), len(pp)
    INF = 1e9
    D = np.full((B + 1, P + 1), INF)
    D[0, :] = 0
    choice = {}
    for i in range(1, B + 1):
        for j in range(0, P + 1):
            best = D[i - 1, j] + 0.4  # break with no pause
            arg = None
            if j > 0:
                strength = min((ps[j - 1][1] - ps[j - 1][0]) / 0.35, 1.0)  # longer pause = surer break
                for jj in range(j):
                    c = D[i - 1, jj] + abs(cw[breaks[i - 1]] - pp[j - 1]) * 2 - 0.25 * strength
                    if c < best:
                        best, arg = c, jj
            D[i, j] = best
            choice[i, j] = arg
    j = int(np.argmin(D[B]))
    match = {}
    for i in range(B, 0, -1):
        arg = choice[i, j]
        if arg is not None:
            match[breaks[i - 1]] = ps[j - 1]
            j = arg
    # anchors: (word index, time). Start at 0, end at dur; matched breaks -> pause end (next phrase starts there)
    anchors = [(0, 0.0)] + sorted((k, p[1]) for k, p in match.items()) + [(len(words), dur)]
    ends_at = {k: p[0] for k, p in match.items()}  # previous phrase ends at pause start
    starts = np.zeros(len(words))
    for (k0, t0), (k1, t1) in zip(anchors, anchors[1:]):
        t_end = ends_at.get(k1, t1) if k1 < len(words) else t1
        ww = w[k0:k1]
        acc = t0 + np.concatenate([[0], np.cumsum(ww)[:-1]]) / ww.sum() * (t_end - t0)
        starts[k0:k1] = acc
    # snap to the deepest dip (word gap) within +-110 ms, except phrase starts already on a pause end
    env = envelope(a)
    for k in range(1, len(words)):
        if k in match:
            continue
        c = int(starts[k] * 100)
        lo, hi = max(1, c - 11), min(len(env) - 1, c + 11)
        dip = lo + int(np.argmin(env[lo:hi]))
        starts[k] = dip / 100 + 0.02
    starts = np.maximum.accumulate(starts)
    ends = list(starts[1:]) + [dur]
    for k in match:
        ends[k - 1] = match[k][0]
    return [(float(s), float(e)) for s, e in zip(starts, ends)], ps, match


def main():
    timing = json.loads((ROOT / "timing.json").read_text())
    out = []
    for sc, line in zip(timing["scenes"], SCRIPT):
        words = line.split()
        a, _ = sf.read(ROOT / "assets" / "vo" / "tight" / f"vo{sc['n']}.wav", dtype="float32")
        times, ps, match = align(words, a)
        print(f"vo{sc['n']}: {len(words)} words, {len(ps)} pauses, breaks matched {sorted(match)}")
        for k, (word, (s, e)) in enumerate(zip(words, times)):
            out.append({"scene": sc["n"], "i": k, "word": word, "text": DISPLAY.get(word, word),
                        "start": round(sc["vo_at"] + s, 3), "end": round(sc["vo_at"] + e, 3),
                        "break": bool(BREAK.search(word))})
    (ROOT / "words.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for x in out:
        print(f"  {x['scene']} {x['start']:6.2f}-{x['end']:6.2f} {x['text']}")


if __name__ == "__main__":
    main()
