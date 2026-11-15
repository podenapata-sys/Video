#!/usr/bin/env python3
"""মায়ের দুটো থালা: find the 6 narration lines + caption phrases in assets/voiceover.mp3 (silencedetect + a global fit
of the script's phrase boundaries to the measured pauses, weighted by syllables), plan the clip timeline, and prepare
clips (muted, 30 fps, cover 1080x1920, last frame held as long as the line needs).
  python3 scripts/prep.py   -> build/timeline.json, build/c1..c6.mp4
"""
import json
import re
import subprocess
import unicodedata
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "build"
SR = 48000
LINES = [
    "ঢাকার এই শহরে সে সফল হয়েছে... কিন্তু ফোনের পর্দায় চৌদ্দটা মিসড কল, শুধু একটাই নাম... আম্মু।",
    "গ্রামের বারান্দায়, প্রতি রাতে এক মা দুটো থালা সাজায়... আর একটা থালা ঢেকে রাখে।",
    "সেই রাতে একটা মেসেজ সব থামিয়ে দিল... \"বাবা, ভাত খাইছো?\"",
    "সব সাফল্য ফেলে সে রওনা দিল... মায়ের কাছে।",
    "মাঝরাত। ঘরের বাতিটা তখনো জ্বলছে... কারণ মা জানত, ছেলে একদিন ফিরবেই।",
    "মা কখনো ক্লান্ত হয় না... শুধু অপেক্ষা করে। আজ কি আপনি মাকে ফোন করেছেন?",
]
V0 = 0.5            # voice starts after the 0.5 s fade from black
XF, DIP = 0.4, 0.6  # crossfade; dip to black between clips 4 and 5
END_HOLD = 1.5


def syl(t):
    return max(1, sum(1 for c in t if unicodedata.category(c) == "Lo"))


def phrases(line):
    return [p.strip() for p in re.split(r"(?<=\.\.\.)\s+|(?<=[।?,])\s+|(?<=\?\")\s+", line) if p.strip()]


def main():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ROOT / "assets/voiceover.mp3"), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32)
    L = len(a) / SR
    e = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", "silencedetect=noise=-38dB:d=0.22",
                        "-f", "null", "-"], input=a.tobytes(), capture_output=True).stderr.decode()
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", e)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", e)] + [L]
    sil = list(zip(st, en))
    head = sil[0][1] if sil and sil[0][0] < 0.02 else 0.0
    tail = next((s for s, x in sil if x >= L - 0.02), L)
    pauses = [(s, x) for s, x in sil if s > head + 0.05 and x < tail - 0.02]
    # phrase list with line index
    ph = [(li, p) for li, line in enumerate(LINES) for p in phrases(line)]
    wt = np.array([syl(p) for _, p in ph], float)
    cum = np.cumsum(wt)[:-1] / wt.sum()                       # fraction at each phrase boundary (len = nph-1)
    line_end = [ph[k][0] != ph[k + 1][0] for k in range(len(ph) - 1)]
    chunks, cur = [], head
    for s, x in pauses:
        chunks.append((cur, s))
        cur = x
    chunks.append((cur, tail))
    speech = sum(b - c for c, b in chunks)
    fr, acc = [], 0.0
    for c, b in chunks[:-1]:
        acc += b - c
        fr.append(acc / speech)
    plen = [x - s for s, x in pauses]
    nb, npz = len(cum), len(pauses)
    # DP: boundary k -> pause j (strictly increasing). cost: timing error; line ends prefer long pauses
    INF = 1e9
    dp = np.full((nb + 1, npz + 1), INF)
    bk = np.zeros((nb + 1, npz + 1), int)
    dp[0, :] = 0.0
    for k in range(1, nb + 1):
        best, arg = INF, 0
        for j in range(1, npz + 1):
            if dp[k - 1, j - 1] < best:
                best, arg = dp[k - 1, j - 1], j - 1
            c = abs(cum[k - 1] - fr[j - 1]) + (0.03 * max(0.0, 0.6 - plen[j - 1]) if line_end[k - 1] else 0.0)
            dp[k, j] = best + c
            bk[k, j] = arg
    j = int(np.argmin(dp[nb, 1:])) + 1
    pick = [0] * (nb + 1)
    for k in range(nb, 0, -1):
        pick[k] = j
        j = bk[k, j]
    bounds = [pauses[pick[k] - 1] for k in range(1, nb + 1)]   # (silence start, silence end) after phrase k-1
    starts = [head] + [x for s, x in bounds]
    ends = [s for s, x in bounds] + [tail]
    caps = [{"line": li + 1, "text": p, "start": round(V0 + starts[k], 3), "end": round(V0 + ends[k], 3)} for k, (li, p) in enumerate(ph)]
    lines = []
    for li in range(6):
        cs = [c for c in caps if c["line"] == li + 1]
        lines.append({"n": li + 1, "start": cs[0]["start"], "end": cs[-1]["end"]})
    # clip timeline: clip n starts where line n starts (clip 1 at 0); clip n runs until clip n+1 starts + transition overlap
    clips = []
    for n in range(6):
        t0 = 0.0 if n == 0 else lines[n]["start"]
        t1 = lines[n + 1]["start"] if n < 5 else lines[5]["end"] + 0.6
        clips.append({"n": n + 1, "start": round(t0, 3), "end": round(t1, 3)})
    total = round(clips[-1]["end"] + END_HOLD, 3)
    clips[-1]["end"] = total
    tl = {"voice_len": round(L, 3), "voice_at": V0, "total": total, "end_card": round(total - END_HOLD, 3), "lines": lines, "captions": caps, "clips": clips}
    for c in caps:
        print(f"  L{c['line']} {c['start']:6.2f}-{c['end']:6.2f}  {c['text']}")
    # prepare clips: overlap handle after each clip for the incoming crossfade / dip
    for c in clips:
        need = c["end"] - c["start"] + 0.8
        src = ROOT / "assets/clips" / f"0{c['n']}.mp4"
        cl = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout)
        vf = (f"fps=30,scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,"
              f"tpad=stop_mode=clone:stop_duration={max(0.0, need - cl) + 0.2:.2f},trim=duration={need:.3f}")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", vf, "-an", "-c:v", "libx264", "-crf", "14", "-preset", "slow",
                        "-pix_fmt", "yuv420p", str(B / f"c{c['n']}.mp4")], check=True)
        c["clip_len"], c["hold_from"] = round(cl, 3), round(c["start"] + min(cl, need), 3)
        print(f"  clip {c['n']}: {c['start']:6.2f}-{c['end']:6.2f}  plays {cl:.1f}s, holds last frame {max(0, c['end'] - c['start'] - cl):.2f}s")
    (B / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"total {total:.2f}s (voice {V0:.1f}-{V0 + L:.2f}s)")


if __name__ == "__main__":
    main()
