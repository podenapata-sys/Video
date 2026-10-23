#!/usr/bin/env python3
"""Align the 95 script lines to the 6 voiceover chunks -> timing.json.

  python3 scripts/align.py

Transcription is unavailable, so each chunk is cut into speech spans (pauses >= 0.3s)
and the spans are grouped onto that chunk's script lines with dynamic programming:
a line's spoken length should match its character count at the chunk's own speaking
rate, and boundaries between lines prefer the longest pauses.
"""
import glob
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RANGES = [(1, 15), (16, 32), (33, 52), (53, 66), (67, 82), (83, 95)]
GAP_BONUS = 2.0  # how strongly a line boundary prefers a long pause
PRIOR_W = 1.0    # pull toward the pocketsphinx forced-alignment line starts (timing_fa.json)


def spans(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "silencedetect=noise=-38dB:d=0.12", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                               capture_output=True, text=True).stdout)
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    out, cur = [], 0.0
    for s, e in zip(st, en + [dur]):
        if s - cur > 0.15:
            out.append((cur, s))
        cur = e
    if dur - cur > 0.15:
        out.append((cur, dur))
    return out, dur


def weight(text):
    return len(re.sub(r"[^A-Za-z0-9]", "", text)) + 4  # letters, plus a little per-line overhead


def align(sp, lines, prior=None):
    """Group consecutive spans onto lines; returns list of (first_span, last_span) per line."""
    n, m = len(lines), len(sp)
    talk = sum(e - s for s, e in sp)
    rate = talk / sum(weight(t) for t in lines)  # seconds per character for this chunk
    exp = [weight(t) * rate for t in lines]
    INF = float("inf")
    dp = [[INF] * (m + 1) for _ in range(n + 1)]
    back = [[0] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0.0
    for i in range(1, n + 1):
        for j in range(i, m - (n - i) + 1):
            for k in range(i - 1, j):  # line i takes spans k..j-1
                if dp[i - 1][k] == INF:
                    continue
                d = sp[j - 1][1] - sp[k][0]  # spoken extent incl. inner pauses
                cost = ((d - exp[i - 1]) / max(0.6, exp[i - 1])) ** 2
                if j < m:  # boundary after this line: reward a long pause
                    cost -= GAP_BONUS * min(1.2, sp[j][0] - sp[j - 1][1])
                if prior:  # forced-alignment guess for where this line starts (capped: it can drift)
                    cost += PRIOR_W * min(4.0, abs(sp[k][0] - prior[i - 1])) ** 2 / 4.0
                c = dp[i - 1][k] + cost
                if c < dp[i][j]:
                    dp[i][j], back[i][j] = c, k
    groups, j = [], m
    for i in range(n, 0, -1):
        k = back[i][j]
        groups.append((k, j - 1))
        j = k
    return groups[::-1], exp


def main():
    scenes = {s["scene"]: s["text"] for s in json.loads((ROOT / "scenes.json").read_text())}
    files = sorted(glob.glob(str(ROOT / "assets" / "vo" / "VO_Chunk_*.mp3")))
    out = []
    for c, (f, (a, b)) in enumerate(zip(files, RANGES), 1):
        sp, dur = spans(f)
        lines = [scenes[i] for i in range(a, b + 1)]
        fa = ROOT / "timing_fa.json"
        prior = [x["start"] for x in json.loads(fa.read_text()) if x["chunk"] == c] if fa.exists() else None
        groups, exp = align(sp, lines, prior)
        for (k, j), num, e in zip(groups, range(a, b + 1), exp):
            s, t = sp[k][0], sp[j][1]
            out.append({"scene": num, "chunk": c, "start": round(s, 3), "end": round(t, 3), "spans": j - k + 1,
                        "expected": round(e, 2), "text": scenes[num]})
            flag = "  <-- check" if abs((t - s) - e) > max(1.2, 0.5 * e) else ""
            print(f"{num:02d} c{c} {s:6.2f}-{t:6.2f} ({t - s:4.1f}s vs ~{e:4.1f}) x{j - k + 1}  {scenes[num][:60]}{flag}")
        print(f"   chunk {c}: {len(sp)} spans, {dur:.1f}s")
    (ROOT / "timing.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
