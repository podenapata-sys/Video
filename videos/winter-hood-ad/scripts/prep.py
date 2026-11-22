#!/usr/bin/env python3
"""Winter hood ad prep: measure the 6 VO lines, lay out 6 beats totalling exactly 30.00 s (VO 0.2 s after each clip
start; beat = VO + lead + tail, spare time to the beats shorter than their brief length), build/voice.wav, muted
1080x1920 30 fps clips at 1.0x that freeze on their last frame when the voice runs longer, and build/timeline.json."""
import json
import subprocess
import unicodedata
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "build"
A = ROOT / "assets"
SR = 48000
TOTAL, LEAD, TAIL = 30.0, 0.2, 0.15
BRIEF = [3, 3, 4, 6, 7, 7]
# beat -> (source clip, source in-point, crop zoom, crop centre x, crop centre y)
SRC = {n: (f"PT-{n}", 0.0, 1.0, .5, .5) for n in range(1, 7)}
# what each VO says (Whisper-checked); the caption shows these words, timed to the voice
CAPS = json.loads((ROOT / "scripts/captions.json").read_text(encoding="utf-8"))
HARD = {2}                               # beat 2 starts on a hard cut
WHIP = {3}                               # beat 3 starts with a whip-pan
XF = 0.2                                 # 6-frame dissolve


def dec(p, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def silences(x, d=0.12, noise=-40):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", f"silencedetect=n={noise}dB:d={d}", "-f", "null", "-"],
                       input=x.tobytes(), capture_output=True).stderr.decode()
    out, s = [], None
    for ln in r.splitlines():
        if "silence_start" in ln:
            s = float(ln.split("silence_start:")[1])
        elif "silence_end" in ln and s is not None:
            out.append((max(0.0, s), float(ln.split("silence_end:")[1].split()[0])))
            s = None
    if s is not None:
        out.append((s, len(x) / SR))
    return out


def syl(w):
    return max(1, sum(1 for c in w if unicodedata.category(c) == "Lo" or c.isalnum()))


def align(x, words):
    """Words -> (start, end) inside one VO: speech chunks between pauses; each pause snaps to the word boundary whose
    syllable fraction best matches it (DP, punctuation preferred); words inside a chunk spread by syllable weight."""
    L = len(x) / SR
    sil = silences(x)
    head = next((e for s, e in sil if s < 0.03), 0.0)
    tail = next((s for s, e in sil if e >= L - 0.1), L)
    pauses = [(s, e) for s, e in sil if s > head + 0.05 and e < tail - 0.05]
    chunks, cur = [], head
    for s, e in pauses:
        chunks.append((cur, s))
        cur = e
    chunks.append((cur, tail))
    wt = [syl(w) for w in words]
    cum = np.cumsum([0] + wt) / sum(wt)
    speech = sum(b - a for a, b in chunks)
    punct = [w[-1] in "।,?!." for w in words]
    fr, acc = [], 0.0
    for a, b in chunks[:-1]:
        acc += b - a
        fr.append(acc / speech)
    P, K = len(fr), len(words)
    if P >= K:                                          # more pauses than gaps between words: keep the longest
        keep = sorted(sorted(range(P), key=lambda i: pauses[i][1] - pauses[i][0])[-(K - 1):]) if K > 1 else []
        return _spread(merge(chunks, keep), words)
    INF = 1e9
    dp = [[INF] * (K + 1) for _ in range(P + 1)]
    bk = [[0] * (K + 1) for _ in range(P + 1)]
    dp[0][0] = 0.0
    for i in range(1, P + 1):
        for k in range(1, K):
            for j in range(k):
                c = dp[i - 1][j] + abs(cum[k] - fr[i - 1]) + (0 if punct[k - 1] else 0.06)
                if c < dp[i][k]:
                    dp[i][k], bk[i][k] = c, j
    k = min(range(1, K), key=lambda k: dp[P][k]) if P else 0
    cuts = [0] * (P + 1)
    for i in range(P, 0, -1):
        cuts[i] = k
        k = bk[i][k]
    cuts = (cuts if P else [0]) + [K]
    return _spread(chunks, words, cuts)


def merge(chunks, keep):
    out, a = [], chunks[0][0]
    for i in range(len(chunks) - 1):
        if i in keep:
            out.append((a, chunks[i][1]))
            a = chunks[i + 1][0]
    out.append((a, chunks[-1][1]))
    return out


def _spread(chunks, words, cuts=None):
    if cuts is None:
        cuts = list(range(len(chunks))) + [len(words)]
    res = []
    for (a, b), c0, c1 in zip(chunks, cuts[:-1], cuts[1:]):
        grp = words[c0:c1]
        g = [syl(w) for w in grp]
        t = a
        for w, gw in zip(grp, g):
            d = (b - a) * gw / sum(g)
            res.append((round(t, 3), round(t + d, 3)))
            t += d
    return res


def main():
    B.mkdir(exist_ok=True)
    vo, speech = {}, []
    for i in range(1, 7):
        x = dec(A / f"voice/PT-{i}.mp3")
        sil = silences(x, d=0.1)
        L = len(x) / SR
        end = next((s for s, e in sil if e >= L - 0.1), L)
        x = x[:int((end + 0.06) * SR)]
        n = int(0.02 * SR)
        x[-n:] *= np.linspace(1, 0, n)
        vo[i] = x
        speech.append(len(x) / SR)
    need = [LEAD + s + TAIL for s in speech]
    # the VO lines fill most of 30 s, so each beat is its VO + lead + a short tail, and the spare time goes to the
    # beats that are shorter than their brief length (in proportion to the shortfall)
    dur = list(need)
    extra = TOTAL - sum(dur)
    assert extra >= 0, extra
    short = [max(0.0, b - nd) for b, nd in zip(BRIEF, need)]
    for i in range(6):
        dur[i] += extra * short[i] / sum(short)
    beats, t = [], 0.0
    for i, d in enumerate(dur, 1):
        beats.append({"n": i, "start": round(t, 3), "end": round(t + d, 3)})
        t += d
    beats[-1]["end"] = TOTAL
    voice = np.zeros(int(TOTAL * SR), np.float32)
    spans, words = {}, []
    for b in beats:
        i = b["n"]
        at = b["start"] + LEAD
        o = int(round(at * SR))
        voice[o:o + len(vo[i])] += vo[i][:len(voice) - o]
        spans[i] = [round(at, 3), round(at + len(vo[i]) / SR, 3)]
        ws = CAPS[str(i)].split()
        for w, (a, e) in zip(ws, align(vo[i], ws)):
            words.append({"beat": i, "w": w, "start": round(at + a, 3), "end": round(at + e, 3)})
    sf.write(B / "voice.wav", np.stack([voice, voice], 1), SR)
    # clips: handles for the dissolves; forward once (slowed to >=0.8x if the beat is longer), then hold
    for b in beats:
        n = b["n"]
        src, sin, z, cx, cy = SRC[n]
        pre = 0.0 if n == 1 or n in HARD or n in WHIP else XF / 2
        post = 0.0 if n == 6 or (n + 1) in HARD or (n + 1) in WHIP else XF / 2
        b["clip_start"], b["clip_dur"] = round(b["start"] - pre, 3), round(b["end"] - b["start"] + pre + post, 3)
        L = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(A / f"src/{src}.mp4")],
                                 capture_output=True, text=True).stdout) - sin
        speed = 1.0                                   # never slowed: freeze the last frame instead
        crop = (f"crop=iw/{z}:ih/{z}:(iw-iw/{z})*{cx}:(ih-ih/{z})*{cy}," if z > 1 else "")
        hold = f"trim=duration={b['clip_dur'] - 3.0:.3f},setpts=PTS-STARTPTS," if n == 6 else ""   # final CTA frame holds 3 s
        vf = (f"{hold}setpts=PTS/{speed:.3f},fps=30,{crop}scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,"
              f"tpad=stop_mode=clone:stop_duration=10,trim=duration={b['clip_dur']:.3f}")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{sin}", "-i", str(A / f"src/{src}.mp4"), "-vf", vf, "-an", "-c:v", "libx264", "-crf", "15",
                        "-preset", "slow", "-pix_fmt", "yuv420p", str(B / f"c{n}.mp4")], check=True)
        b["src"], b["speed"], b["hold_from"] = src, round(speed, 3), round(b["clip_start"] + L / speed, 3)
        print(f"  beat {n}: {b['start']:6.2f}-{b['end']:6.2f} ({b['end'] - b['start']:.2f}s)  {src} x{speed:.2f}  VO {spans[n][0]:.2f}-{spans[n][1]:.2f}")
    tl = {"total": TOTAL, "beats": beats, "spans": {str(k): v for k, v in spans.items()}, "words": words}
    (B / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    print("total", TOTAL)


if __name__ == "__main__":
    main()
