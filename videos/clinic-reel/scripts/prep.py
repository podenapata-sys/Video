#!/usr/bin/env python3
"""Clinic Reel prep.
  python3 scripts/prep.py probe   -> input table (build/inputs.md)
  python3 scripts/prep.py voice   -> audio/voiceover.mp3 (+ build/voice.wav), build/timeline.json
  python3 scripts/prep.py words   -> build/words.json (whisper medium, bn, word timestamps; aligned to the brief's script)
  python3 scripts/prep.py clips   -> build/s1..s6.mp4 fitted to their sections (cover 1080x1920, 30 fps)
The voiceover arrived as one file per section (audio/parts/vo1..6.mp3), so section n starts where vo n starts.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
SR = 48000
sys.path.insert(0, str(ROOT.parent.parent / "kits" / "reel-kit" / "kit"))

SCRIPT = [
    "যে রোগী অ্যাপয়েন্টমেন্ট ক্যান্সেল করেছে, সে কি হারিয়ে গেছে? না। আপনি শুধু তাকে আর ফোন করেননি। এই সপ্তাহের এআই নিউজ থেকে ক্লিনিকের জন্য ৩টা শিক্ষা।",
    "এক নম্বর: ক্যান্সেল মানে হারানো না। বিদেশে ডেন্টাল এআই এখন নিজে থেকেই ক্যান্সেল আর অনেকদিন না আসা রোগীদের লিস্ট বানায়। আপনার ক্লিনিকে এই কাজটা হোয়াটসঅ্যাপে অটোমেটিক করা যায়, প্রতিটা রোগীকে নাম ধরে মেসেজ।",
    "দুই নম্বর: বড় বড় কোম্পানি এআই-তে টাকা ঢালছে, কিন্তু খুব কম কোম্পানিই দেখাতে পারছে সেই টাকা ফেরত আসছে কিনা। তাই চ্যাটবট বানানোর আগে একটা সংখ্যা ঠিক করুন, মাসে কয়টা বুকিং, বা কয়টা মিসড কল।",
    "তিন নম্বর: এআই দিয়ে এখন পাঁচ মিনিটে ওয়েবসাইট বানানো যায়। কিন্তু ওয়েবসাইট আর বুকিং সিস্টেম এক জিনিস না। রোগী যদি সাইটে এসে সিরিয়াল দিতে না পারে, সুন্দর ডিজাইন দিয়ে কোনো লাভ নেই।",
    "কমেন্টে ক্লিনিক লিখুন। আমার টিম ফ্রিতে দেখে বলে দেবে আপনার ক্লিনিক প্রতি মাসে কতজন রোগী হারাচ্ছে।",
    "নতুন রোগী আনা কঠিন। যারা একবার এসেছে, তাদের ধরে রাখা সহজ।",
]


def dec(p, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def silences(a, d=0.1, noise=-40, sr=SR):
    e = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", "-af",
                        f"silencedetect=noise={noise}dB:d={d}", "-f", "null", "-"], input=a.tobytes(), capture_output=True).stderr.decode()
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", e)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", e)]
    return list(zip(st, en + [len(a) / sr] * (len(st) - len(en))))


def probe():
    rows = ["| file | duration | resolution | fps | audio |", "|---|---|---|---|---|"]
    files = [*(ROOT / "scenes").glob("scene*.mp4"), *(ROOT / "audio" / "parts").glob("vo*.mp3"), ROOT / "audio" / "music.wav", ROOT / "logo.png"]
    for f in sorted(files):
        j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate,sample_rate,channels,codec_name",
                                       "-of", "json", str(f)], capture_output=True, text=True).stdout or "{}")
        v = next((s for s in j.get("streams", []) if s["codec_type"] == "video"), {})
        a = next((s for s in j.get("streams", []) if s["codec_type"] == "audio"), {})
        dur = j.get("format", {}).get("duration", "-")
        res = f'{v["width"]}x{v["height"]}' if v else "-"
        fps = v.get("r_frame_rate", "-") if v and f.suffix != ".png" else "-"
        au = f'{a["codec_name"]} {a["sample_rate"]} Hz {a["channels"]}ch' if a else "none"
        rows.append(f"| {f.relative_to(ROOT)} | {float(dur):.2f} s | {res} | {fps} | {au} |" if dur != "-" else f"| {f.relative_to(ROOT)} | - | {res} | - | {au} |")
    rows.append("| sfx/ | (not provided, optional) | | | |")
    t = "\n".join(rows)
    (BUILD / "inputs.md").write_text(t + "\n")
    print(t)


def voice():
    parts, spans, t = [], [], 0.0
    for i in range(1, 7):
        a = dec(ROOT / "audio" / "parts" / f"vo{i}.mp3")
        dur = len(a) / SR
        s, e = 0.0, dur
        for x, y in silences(a, d=0.3):
            if x < 0.02:
                s = max(0.0, y - 0.15)
            elif y >= dur - 0.02:
                e = min(dur, x + 0.15)
        seg = a[int(s * SR):int(e * SR)]
        parts.append(seg)
        spans.append({"n": i, "start": round(t, 3), "end": round(t + len(seg) / SR, 3), "trim_in": round(s, 3)})
        t += len(seg) / SR
    v = np.concatenate(parts)
    sf.write(BUILD / "voice.wav", v, SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(BUILD / "voice.wav"), "-c:a", "libmp3lame", "-b:a", "192k", str(ROOT / "audio" / "voiceover.mp3")], check=True)
    vo = round(t, 3)
    tl = {"voice": vo, "speech_end": round(vo + 0.4, 3), "card_at": round(vo + 0.4, 3), "total": round(vo + 0.4 + 5.0, 3), "sections": spans}
    (BUILD / "timeline.json").write_text(json.dumps(tl, indent=1))
    for s in spans:
        print(f"  S{s['n']}: {s['start']:6.2f}-{s['end']:6.2f}  ({s['end'] - s['start']:.2f} s)")
    print(f"voice {vo:.2f}s, end card {tl['card_at']:.2f}-{tl['total']:.2f}s")


def words():
    import whisper
    from reel import align, refine
    tl = json.loads((BUILD / "timeline.json").read_text())
    model = whisper.load_model("medium")
    v16 = dec(BUILD / "voice.wav", 16000)
    v48 = dec(BUILD / "voice.wav")
    out, report = [], []
    for sec, text in zip(tl["sections"], SCRIPT):
        s0, s1 = sec["start"], sec["end"]
        res = model.transcribe(v16[int(s0 * 16000):int(s1 * 16000)], language="bn", word_timestamps=True, fp16=False,
                               initial_prompt=text, condition_on_previous_text=False)
        asr = [w for sg in res["segments"] for w in sg.get("words", [])]
        report.append({"section": sec["n"], "heard": res["text"].strip()})
        print(f"  S{sec['n']} heard: {res['text'].strip()}")
        sw = text.split()
        ws = [{"section": sec["n"], "i": k, "text": w, "start": round(s0 + a, 3), "end": round(s0 + b, 3)} for k, (w, (a, b)) in enumerate(zip(sw, align(sw, asr)))]
        ws = refine(ws)
        # phrase starts: snap a word to the end of a measured pause if one is within 0.35 s (whisper bn timing is loose)
        seg = v48[int(s0 * SR):int(s1 * SR)]
        pauses = [round(s0 + e, 3) for s, e in silences(seg, d=0.12) if 0.05 < s and e < (s1 - s0) - 0.05]
        for p in pauses:
            k = min(range(len(ws)), key=lambda j: abs(ws[j]["start"] - p))
            if abs(ws[k]["start"] - p) <= 0.35:
                ws[k]["start"] = p
                ws[k]["snapped"] = True
        for k in range(1, len(ws)):              # keep monotonic
            ws[k]["start"] = max(ws[k]["start"], ws[k - 1]["start"] + 0.05)
        out += ws
    (BUILD / "words.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (BUILD / "whisper_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    for w in out:
        print(f"  s{w['section']} {w['start']:6.2f}{'*' if w.get('snapped') else ' '} {w['text']}")


def clips():
    tl = json.loads((BUILD / "timeline.json").read_text())
    secs = tl["sections"]
    HANDLE = 0.35                                  # frozen tail under the next section's transition
    fit = []
    for k, s in enumerate(secs):
        D = (s["end"] if k < 5 else tl["card_at"]) - s["start"] if k < 5 else tl["card_at"] - s["start"] + 0.6   # S6 runs into the end-card slide
        if k < 5:
            D = secs[k + 1]["start"] - s["start"]
        src = ROOT / "scenes" / f"scene{k + 1}.mp4"
        cl = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout)
        if D <= cl:
            speed, hold = 1.0, 0.0
        elif D <= cl / 0.8:
            speed, hold = cl / D, 0.0
        else:
            speed, hold = 0.8, D - cl / 0.8
        need = D + HANDLE
        vf = (f"setpts=PTS/{speed:.4f},fps=30,scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,"
              f"tpad=stop_mode=clone:stop_duration={hold + HANDLE + 0.2:.2f},trim=duration={need:.3f}")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", vf, "-an", "-c:v", "libx264", "-crf", "14", "-preset", "slow",
                        "-pix_fmt", "yuv420p", str(BUILD / f"s{k + 1}.mp4")], check=True)
        fit.append({"n": k + 1, "dur": round(D, 3), "speed": round(speed, 3), "hold_at": round(s["start"] + cl / speed, 3) if hold else None, "hold": round(hold, 3)})
        print(f"  s{k + 1}: section {D:5.2f}s  speed {speed:.2f}x" + (f"  hold {hold:.2f}s from {s['start'] + cl / speed:.2f}" if hold else "") + ("  (trimmed)" if D < cl else ""))
    tl["fit"] = fit
    (BUILD / "timeline.json").write_text(json.dumps(tl, indent=1))


def syl(wd):
    """Syllable-ish weight: base letters only (vowel signs, hasanta and marks are Mn/Mc)."""
    import unicodedata
    return max(1, sum(1 for c in wd if unicodedata.category(c)[0] == "L" and unicodedata.category(c) not in ("Mn", "Mc")))


def words2():
    """Pause-driven alignment (whisper's Bangla output here is too garbled to time words): each measured pause is
    snapped to the script word boundary whose syllable fraction best matches the pause's speech-time fraction,
    preferring punctuation boundaries; words inside a speech chunk are spread by syllable weight."""
    tl = json.loads((BUILD / "timeline.json").read_text())
    v = dec(BUILD / "voice.wav")
    out = []
    for sec, text in zip(tl["sections"], SCRIPT):
        s0, s1 = sec["start"], sec["end"]
        seg = v[int(s0 * SR):int(s1 * SR)]
        L = len(seg) / SR
        sil = []
        for x, y in silences(seg, d=0.12, noise=-38):      # merge back-to-back silences (silencedetect can split one pause)
            if sil and x - sil[-1][1] < 0.05:
                sil[-1] = (sil[-1][0], y)
            else:
                sil.append((x, y))
        head = next((e for s, e in sil if s < 0.02), 0.0)
        tail = next((s for s, e in sil if e >= L - 0.02), L)
        pauses = [(s, e) for s, e in sil if s >= 0.02 and e < L - 0.02 and s > head and e < tail]
        chunks, cur = [], head
        for s, e in pauses:
            chunks.append((cur, s))
            cur = e
        chunks.append((cur, tail))
        ws = text.replace(" —", "").split()
        wt = [syl(x) for x in ws]
        cum = np.cumsum([0] + wt) / sum(wt)
        speech = sum(b - a for a, b in chunks)
        punct = [x[-1] in "।,?:!" for x in ws]
        # global fit: pause i -> word boundary k (strictly increasing). cost = timing error + penalty for a pause
        # that does not sit on punctuation (bigger for longer pauses)
        P = len(chunks) - 1
        fr, acc = [], 0.0
        for a, b in chunks[:-1]:
            acc += b - a
            fr.append(acc / speech)
        plen = [e - s for s, e in pauses]
        Kn = len(ws)
        INF = 1e9
        cost = lambda i, k: abs(cum[k] - fr[i]) + (0.0 if punct[k - 1] else min(0.12, 0.05 + plen[i] * 0.25))
        dp = [[INF] * (Kn + 1) for _ in range(P + 1)]
        bk = [[0] * (Kn + 1) for _ in range(P + 1)]
        for k in range(Kn + 1):
            dp[0][k] = 0.0 if k == 0 else INF
        dp[0][0] = 0.0
        for i in range(1, P + 1):
            best, arg = INF, 0
            for k in range(1, Kn):
                if dp[i - 1][k - 1] < best:
                    best, arg = dp[i - 1][k - 1], k - 1
                if best < INF:
                    dp[i][k] = best + cost(i - 1, k)
                    bk[i][k] = arg
        kend = min(range(1, Kn), key=lambda k: dp[P][k]) if P else 0
        cuts = [0] * (P + 1)
        k = kend
        for i in range(P, 0, -1):
            cuts[i] = k
            k = bk[i][k]
        cuts = cuts if P else [0]
        cuts.append(len(ws))
        i = 0
        for (a, b), c0, c1 in zip(chunks, cuts[:-1], cuts[1:]):
            grp = ws[c0:c1]
            if not grp:
                continue
            g = [syl(x) for x in grp]
            t = a
            for x, gw in zip(grp, g):
                d = (b - a) * gw / sum(g)
                out.append({"section": sec["n"], "i": i, "text": x, "start": round(s0 + t, 3), "end": round(s0 + t + d, 3)})
                t += d
                i += 1
        print(f"  S{sec['n']}: {len(chunks)} speech chunks -> " + " | ".join(" ".join(ws[c0:c1]) for c0, c1 in zip(cuts[:-1], cuts[1:])))
    (BUILD / "words.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    {"probe": probe, "voice": voice, "words": words, "words2": words2, "clips": clips}[sys.argv[1]]()
