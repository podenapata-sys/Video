#!/usr/bin/env python3
"""SaHa GoLD ad prep: voice lines -> tightened, laid out back to back -> beat timeline; clips retimed to the beats.

  python3 scripts/prep.py            -> media/voice.wav, timeline.json, media/b1..b6.mp4
  python3 scripts/prep.py --words    -> words.json (whisper word times, aligned to the script)

Beat boundaries follow the voice (brief: "every word matches a scene"), total fixed at 30.0 s.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "media"
SR = 48000
TOTAL = 30.0
FIRST_VOICE = 0.6          # 0.5 s black, flash + bass hit at 0.5, voice right after
GAP = 0.28                 # silence between lines (the transition sits in it)
SCRIPT = [
    "সেচ দিতে গিয়ে বিদ্যুতের জন্য বসে থাকেন?",
    "এবার পরিচয় হোক সাহা গোল্ড, বারো ভোল্ট ব্যাটারিচালিত ওয়াটার পাম্প।",
    "তামার কয়েল, স্টেইনলেস স্টিল বডি — এক ইঞ্চি আর দুই ইঞ্চি, দুই সাইজে পাচ্ছেন।",
    "দুই ইঞ্চি মডেলে তিনটি ক্যাপ একদম ফ্রি!",
    "যেকোনো পুকুর, নদী বা জলাশয় থেকে সরাসরি সেচ দিন, বিদ্যুৎ ছাড়াই।",
    "অর্ডার করতে এখনই যোগাযোগ করুন। দুইশো টাকা অ্যাডভান্স দিয়ে অর্ডার কনফার্ম করুন।",
]


def dec(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def silences(a, d=0.12, noise=-40):
    e = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                        f"silencedetect=noise={noise}dB:d={d}", "-f", "null", "-"], input=a.tobytes(), capture_output=True).stderr.decode()
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", e)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", e)]
    return list(zip(st, en + [len(a) / SR] * (len(st) - len(en))))


def tighten(a):
    """Trim head/tail silence, shrink inner pauses longer than 0.25 s to 0.15 s."""
    dur = len(a) / SR
    start, end, inner = 0.0, dur, []
    for s, e in silences(a):
        if s < 0.02:
            start = max(0.0, e - 0.03)
        elif e >= dur - 0.02:
            end = min(dur, s + 0.08)
        elif e - s > 0.25:
            inner.append((s + 0.075, e - 0.075))
    keep, cur = [], start
    for s, e in inner:
        keep.append((cur, s))
        cur = e
    keep.append((cur, end))
    f = int(0.005 * SR)
    parts = []
    for s, e in keep:
        p = a[int(s * SR):int(e * SR)].copy()
        p[:f] *= np.linspace(0, 1, f)
        p[-f:] *= np.linspace(1, 0, f)
        parts.append(p)
    return np.concatenate(parts)


def prep():
    lines = [tighten(dec(MD / "src" / f"PT-{i}.mp3")) for i in range(1, 7)]
    lens = [len(x) / SR for x in lines]
    v = np.zeros(int(TOTAL * SR), np.float32)
    t, spans = FIRST_VOICE, []
    for x, L in zip(lines, lens):
        o = int(round(t * SR))
        v[o:o + len(x)] += x
        spans.append((round(t, 3), round(t + L, 3)))
        t += L + GAP
    assert spans[-1][1] < TOTAL - 1.0, f"voice too long: ends {spans[-1][1]:.2f}"
    sf.write(MD / "voice.wav", np.stack([v, v], 1), SR)
    # beat boundaries: midway in each inter-line gap; beat 1 starts at 0, beat 6 ends at TOTAL
    bounds = [0.0] + [round((spans[i][1] + spans[i + 1][0]) / 2, 3) for i in range(5)] + [TOTAL]
    beats = [{"n": i + 1, "start": bounds[i], "end": bounds[i + 1], "voice": spans[i]} for i in range(6)]
    (ROOT / "timeline.json").write_text(json.dumps({"total": TOTAL, "beats": beats}, indent=1))
    for b in beats:
        print(f"  beat {b['n']}: {b['start']:5.2f}-{b['end']:5.2f}  voice {b['voice'][0]:5.2f}-{b['voice'][1]:5.2f}")
    # clips: each covers [start - H, end + H] so transitions have handles; whole clip content is used
    H = 0.35
    for b in beats:
        src = MD / "src" / f"Clip-{b['n']}.mp4"
        cl = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)],
                                  capture_output=True, text=True).stdout)
        need = (b["end"] - b["start"]) + 2 * H
        hold = 0.0
        if b["n"] == 6:                      # end card: 0.8x then hold the last frame (CSS zoom-out keeps it alive)
            speed = 0.8
            hold = max(0.0, need - cl / speed)
        else:
            speed = cl / need
        vf = (f"setpts=PTS/{speed:.4f},fps=30,scale=1080:1920:flags=lanczos,setsar=1"
              + (f",tpad=stop_mode=clone:stop_duration={hold + 0.1:.2f}" if hold else "") + f",trim=duration={need:.3f}")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", vf, "-an", "-c:v", "libx264", "-crf", "15", "-preset", "slow",
                        "-pix_fmt", "yuv420p", str(MD / f"b{b['n']}.mp4")], check=True)
        b.update({"clip_t": round(b["start"] - H, 3), "clip_dur": round(need, 3), "speed": round(speed, 3)})
        print(f"  b{b['n']}.mp4  speed {speed:.2f}x  {need:.2f}s" + (f" (+hold {hold:.2f}s)" if hold else ""))
    (ROOT / "timeline.json").write_text(json.dumps({"total": TOTAL, "beats": beats}, indent=1))


def words():
    import difflib
    import whisper
    tl = json.loads((ROOT / "timeline.json").read_text())
    model = whisper.load_model("medium")
    v16 = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(MD / "voice.wav"), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                                       capture_output=True, check=True).stdout, np.float32).copy()   # whisper arrays must be 16 kHz
    out = []
    for b, text in zip(tl["beats"], SCRIPT):
        s0, s1 = b["voice"]
        seg = v16[int(s0 * 16000):int(s1 * 16000) + 1600]
        res = model.transcribe(seg, language="bn", word_timestamps=True, fp16=False, initial_prompt=text, condition_on_previous_text=False)
        asr = [w for sg in res["segments"] for w in sg.get("words", [])]
        print(f"  B{b['n']} heard: {res['text'].strip()}")
        norm = lambda w: re.sub(r"[,.।?!:;—\-\"'“”]", "", w).strip()
        sw, aw = [norm(w) for w in text.split()], [norm(x["word"]) for x in asr]
        sj, aj = " ".join(sw), " ".join(aw)
        a_idx = []
        for i, w in enumerate(aw):
            a_idx += [i] * (len(w) + 1)
        cmap = {a + k: c + k for a, c, n in difflib.SequenceMatcher(None, sj, aj, autojunk=False).get_matching_blocks() for k in range(n)}
        pos, L = 0, s1 - s0
        for i, (raw, w) in enumerate(zip(text.split(), sw)):
            hits = [a_idx[cmap[c]] for c in range(pos, pos + max(1, len(w))) if c in cmap and cmap[c] < len(a_idx)]
            st = asr[min(hits)]["start"] if hits else None
            if st is None:                    # interpolate by character position
                st = L * pos / max(1, len(sj))
            out.append({"beat": b["n"], "i": i, "text": raw, "start": round(s0 + st, 3)})
            pos += len(w) + 1
    (ROOT / "words.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for w in out:
        print(f"  b{w['beat']} {w['start']:6.2f} {w['text']}")


if __name__ == "__main__":
    if "--phrases" not in sys.argv:
        words() if "--words" in sys.argv else prep()


def phrase_words():
    """No-whisper word times: the script's punctuation phrases map 1:1 onto the voice's pauses (silencedetect on
    voice.wav inside each line); words inside a phrase are spread by character length."""
    tl = json.loads((ROOT / "timeline.json").read_text())
    v = dec(MD / "voice.wav")
    out = []
    for b, text in zip(tl["beats"], SCRIPT):
        s0, s1 = b["voice"]
        seg = v[int(s0 * SR):int(s1 * SR)]
        chunks, cur = [], 0.0
        for s, e in silences(seg, d=0.1, noise=-40):
            if 0.05 < s and e < (s1 - s0) - 0.05:
                chunks.append((cur, s))
                cur = e
        chunks.append((cur, s1 - s0))
        # snap every measured pause to the word boundary whose character position best matches the pause's time position
        ws = [x for x in text.split() if x != "—"]
        cum = np.cumsum([0] + [max(1, len(x)) for x in ws]) / sum(max(1, len(x)) for x in ws)
        L = s1 - s0
        speech = sum(z - a for a, z in chunks)
        cuts, lo = [0], 1
        acc = 0.0
        for a, z in chunks[:-1]:
            acc += z - a
            frac = acc / speech
            k = min(range(lo, len(ws)), key=lambda j: abs(cum[j] - frac)) if lo < len(ws) else len(ws)
            cuts.append(k)
            lo = k + 1
        cuts.append(len(ws))
        i = 0
        for (a, z), (c0, c1) in zip(chunks, zip(cuts[:-1], cuts[1:])):
            grp = ws[c0:c1]
            if not grp:
                continue
            wts = [max(1, len(x)) for x in grp]
            t = a
            for x, wt in zip(grp, wts):
                out.append({"beat": b["n"], "i": i, "text": x, "start": round(s0 + t, 3)})
                t += (z - a) * wt / sum(wts)
                i += 1
    (ROOT / "words.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for w in out:
        print(f"  b{w['beat']} {w['start']:6.2f} {w['text']}")


if __name__ == "__main__" and "--phrases" in sys.argv:
    phrase_words()
