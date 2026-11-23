"""Winter hood reel prep: one 29.8 s voice split into its 7 lines at the measured pauses (placed 0.2 s in, never sped up),
3 beats (hook = lines 1-2, detail = 3-6, CTA = 7), words aligned per line, clips slowed (motion-interpolated) then frozen,
CTA clip holding its final frame for the last 3 s; build/voice.wav and build/timeline.json."""
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
TOTAL, LEAD = 30.5, 0.2
CAPS = json.loads((ROOT / "scripts/captions.json").read_text(encoding="utf-8"))
LINES = {1: [1, 2], 2: [3, 4, 5, 6], 3: [7]}
SRC = {1: ("A", 0.0, 0.55), 2: ("C", 0.0, 0.55), 3: ("B", 0.8, 1.0)}   # (clip, in-point, slowest speed)
XF = 0.2


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
    x = dec(A / "vo.mp3")
    L = len(x) / SR
    sil = [(a, e) for a, e in silences(x, d=0.25, noise=-40) if e - a >= 0.25]
    inner = [(a, e) for a, e in sil if a > 0.1 and e < L - 0.1]
    assert len(inner) == len(CAPS) - 1, inner
    bounds = [0.0] + [(a + e) / 2 for a, e in inner] + [L]
    voice = np.zeros(int(TOTAL * SR), np.float32)
    o = int(LEAD * SR)
    voice[o:o + len(x)] = x[:len(voice) - o]
    sf.write(B / "voice.wav", np.stack([voice, voice], 1), SR)
    words, spans = [], {}
    for li, text in enumerate(CAPS):
        a, e = bounds[li], bounds[li + 1]
        seg = x[int(a * SR):int(e * SR)]
        beat = next(b for b, ls in LINES.items() if li + 1 in ls)
        ws = text.split()
        for w, (s0, s1) in zip(ws, align(seg, ws)):
            words.append({"beat": beat, "line": li + 1, "w": w, "start": round(LEAD + a + s0, 3), "end": round(LEAD + a + s1, 3)})
        spans.setdefault(beat, []).append([round(LEAD + a, 3), round(LEAD + e, 3)])
    cut = {2: LEAD + bounds[2], 3: LEAD + bounds[6]}
    beats = [{"n": 1, "start": 0.0, "end": round(cut[2], 3)}, {"n": 2, "start": round(cut[2], 3), "end": round(cut[3], 3)},
             {"n": 3, "start": round(cut[3], 3), "end": TOTAL}]
    for b in beats:
        n = b["n"]
        src, sin, slow = SRC[n]
        pre = 0.0 if n in (1, 2) else XF / 2          # 1->2 whip-pan, 2->3 dissolve
        post = XF / 2 if n == 2 else 0.0
        b["clip_start"], b["clip_dur"] = round(b["start"] - pre, 3), round(b["end"] - b["start"] + pre + post, 3)
        Ls = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(A / f"src/{src}.mp4")],
                                  capture_output=True, text=True).stdout) - sin
        if n == 3:     # CTA: play until total - 3 s, then the final frame holds for the last 3 s
            play = min(Ls, b["clip_dur"] - 3.0)
            speed, pre_f = 1.0, f"trim=duration={play:.3f},setpts=PTS-STARTPTS,fps=30,"
        else:          # slowed (motion-interpolated) to fill more of the slot, then freeze; never looped
            speed = max(slow, min(1.0, Ls / b["clip_dur"]))
            pre_f = f"setpts=PTS/{speed:.3f},minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1,"
        vf = (f"{pre_f}scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,unsharp=5:5:0.6,"
              f"tpad=stop_mode=clone:stop_duration=20,trim=duration={b['clip_dur']:.3f}")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{sin}", "-i", str(A / f"src/{src}.mp4"), "-vf", vf, "-an", "-c:v", "libx264", "-crf", "15",
                        "-preset", "slow", "-pix_fmt", "yuv420p", str(B / f"c{n}.mp4")], check=True)
        b["src"], b["speed"] = src, round(speed, 3)
        print(f"  beat {n}: {b['start']:6.2f}-{b['end']:6.2f}  {src} x{speed:.2f}")
    tl = {"total": TOTAL, "beats": beats, "spans": {str(k): [v[0][0], v[-1][1]] for k, v in spans.items()}, "lines": spans, "words": words}
    (B / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    print("total", TOTAL, "voice", round(L, 2), "bounds", [round(v, 2) for v in bounds])


if __name__ == "__main__":
    main()
