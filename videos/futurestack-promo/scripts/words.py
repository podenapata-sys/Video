#!/usr/bin/env python3
"""Word timings for the Future Stack promo -> words.json (global seconds).

  python3 scripts/words.py        (after scripts/timeline.py)

1. OpenAI whisper (medium, language "bn", word_timestamps) transcribes each section's tightened voice (media/secN.wav)
   for TIMING only.
2. The user's script is the text: script words are aligned to whisper's words by order, weighted by character length
   (difflib on the time-ordered sequences). If whisper misses or splits words, script words take times interpolated
   from the nearest anchors. Subtitles always show the user's wording.
"""
import difflib
import json
import re
from pathlib import Path

import whisper

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "media"

SCRIPT = {
    1: "আপনার পেজে মেসেজ আসে, কিন্তু সেল হয় না? সমস্যা আপনার প্রোডাক্টে না। সমস্যা এই ৩টা জায়গায়।",
    2: "এক নম্বর: দেরিতে রিপ্লাই। কাস্টমার দাম জিজ্ঞেস করে ১ ঘণ্টা অপেক্ষা করে না, পাশের পেজে চলে যায়। এআই চ্যাটবট রাত ২টাতেও সেকেন্ডে উত্তর দেয়।",
    3: "দুই নম্বর: ফলো-আপ নেই। যে আজ কেনেনি, কাল তাকে কেউ মনে করিয়ে দেয়নি। অটোমেশন নিজে থেকেই রিমাইন্ডার পাঠায়।",
    4: "তিন নম্বর: শুধু ফেসবুক পেজের ওপর ভরসা। নিজের ল্যান্ডিং পেজ না থাকলে কাস্টমার আপনাকে সিরিয়াস ব্যবসা ভাবে না।",
    5: "কমেন্টে GROW লিখুন। আমার টিম ফ্রিতে আপনার পেজ দেখে বলে দেবে কোথায় কাস্টমার হারাচ্ছেন।",
    6: "ভালো প্রোডাক্ট যথেষ্ট না। কাস্টমার যেন হারিয়ে না যায়, সেটাই আসল গ্রোথ।",
}
PUNCT = re.compile(r"[,.।?!:;—\-\"'“”]")


def norm(w):
    return PUNCT.sub("", w).strip().lower()


def align(script_words, asr):
    """Map each script word to (start, end) using whisper words as anchors."""
    sw = [norm(w) for w in script_words]
    aw = [norm(x["word"]) for x in asr]
    # character-level alignment between the two joined strings gives robust word anchors
    sj = " ".join(sw)
    aj = " ".join(aw)
    sm = difflib.SequenceMatcher(None, sj, aj, autojunk=False)
    # char index -> asr word index
    a_idx, pos = [], 0
    for i, w in enumerate(aw):
        a_idx += [i] * len(w) + [i]
    s_starts, pos = [], 0
    for w in sw:
        s_starts.append(pos)
        pos += len(w) + 1
    cmap = {}
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            cmap[a + k] = b + k
    times = []
    for i, w in enumerate(sw):
        hits = [a_idx[cmap[c]] for c in range(s_starts[i], s_starts[i] + max(1, len(w))) if c in cmap and cmap[c] < len(a_idx)]
        if hits:
            j0, j1 = min(hits), max(hits)
            times.append((asr[j0]["start"], asr[j1]["end"]))
        else:
            times.append(None)
    # interpolate gaps between anchors by character weight
    n = len(times)
    i = 0
    while i < n:
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < n and times[j] is None:
            j += 1
        t0 = times[i - 1][1] if i > 0 else (asr[0]["start"] if asr else 0.0)
        t1 = times[j][0] if j < n else (asr[-1]["end"] if asr else t0 + 0.4 * (j - i))
        wts = [max(1, len(sw[k])) for k in range(i, j)]
        tot = sum(wts)
        acc = t0
        for k, wt in zip(range(i, j), wts):
            d = (t1 - t0) * wt / tot
            times[k] = (acc, acc + d)
            acc += d
        i = j
    # monotonic, non-overlapping
    out, prev = [], 0.0
    for s, e in times:
        s = max(s, prev)
        e = max(e, s + 0.05)
        out.append((round(s, 3), round(e, 3)))
        prev = s
    return out


def refine(words):
    """Split runs of script words that landed on the same whisper word, by character length."""
    out = [dict(w) for w in words]
    i = 0
    while i < len(out):
        j = i
        while j + 1 < len(out) and out[j + 1]["section"] == out[i]["section"] and abs(out[j + 1]["start"] - out[i]["start"]) < 0.06:
            j += 1
        nxt = out[j + 1]["start"] if j + 1 < len(out) and out[j + 1]["section"] == out[i]["section"] else max(w["end"] for w in out[i:j + 1])
        span_end = max(nxt, max(w["end"] for w in out[i:j + 1]))
        if j > i or out[i]["end"] - out[i]["start"] < 0.1:
            t0 = out[i]["start"]
            wts = [max(1, len(norm(w["text"]))) for w in out[i:j + 1]]
            tot = sum(wts)
            acc = t0
            for k, wt in zip(range(i, j + 1), wts):
                d = (span_end - t0) * wt / tot
                out[k]["start"], out[k]["end"] = round(acc, 3), round(acc + d, 3)
                acc += d
        i = j + 1
    return out


def main():
    import sys
    if "--refine" in sys.argv:
        words = refine(json.loads((ROOT / "words.json").read_text(encoding="utf-8")))
        (ROOT / "words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
        for w in words:
            print(f"  {w['section']} {w['start']:6.2f}-{w['end']:6.2f} {w['text']}")
        return
    tl = json.loads((ROOT / "timeline.json").read_text())
    model = whisper.load_model("medium")
    words, report = [], []
    for sec in tl["sections"]:
        n = sec["n"]
        res = model.transcribe(str(MD / f"sec{n}.wav"), language="bn", word_timestamps=True, fp16=False,
                               initial_prompt=SCRIPT[n], condition_on_previous_text=False)
        asr = [w for seg in res["segments"] for w in seg.get("words", [])]
        report.append({"section": n, "whisper_text": res["text"].strip()})
        sw = SCRIPT[n].split()
        for k, (w, (s, e)) in enumerate(zip(sw, align(sw, asr))):
            words.append({"section": n, "i": k, "text": w, "start": round(sec["start"] + s, 3), "end": round(sec["start"] + e, 3)})
        print(f"S{n} whisper: {res['text'].strip()}")
    words = refine(words)
    (ROOT / "words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "out" / "whisper_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    for w in words:
        print(f"  {w['section']} {w['start']:6.2f}-{w['end']:6.2f} {w['text']}")


if __name__ == "__main__":
    main()
