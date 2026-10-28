#!/usr/bin/env python3
"""Voiceover chunks -> scene grid, subtitles, cue times, the -14 LUFS mix and re-timed clips.

  python3 scripts/voice.py     (then scripts/build.py)

The six recorded chunks (assets/vo/chunks/c1..c6.mp3: scenes 1-5 and the closing card) are longer than
the brief's 10 s slots, so the grid follows the voice instead of squeezing it:
- pauses inside a chunk longer than MAX_PAUSE are shortened to MAX_PAUSE (speech itself is untouched)
- each scene = LEAD + its speech + TAIL; the closing scene also holds the card for CLOSE_HOLD after the voice
- every phrase (speech between detected pauses) gets its final time; subtitles are runs of phrases
  (PHRASES below), and the headline cues hang off the phrase that says them
- each 10 s clip is slowed to its scene length (frame-blended), so nothing freezes
Writes assets/vo/mix.wav (0.3 s fade-in, 1 s master fade-out, -14 LUFS) and timing.json.
"""
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
VO = ROOT / "assets" / "vo"
CLIPS = ROOT / "assets" / "clips"
SR = 48000
MAX_PAUSE = 0.45
LEAD, TAIL, CLOSE_HOLD = 0.3, 0.45, 2.6

# per chunk: the text of each phrase between pauses (checked against the detected pause count)
PHRASES = [
    ["প্রতিদিন সকাল সাতটায় ঢাকার ব্যস্ত রাস্তায়", "রহিম চাচা তাঁর চায়ের দোকান খোলেন।",
     "বারো বছর ধরে তিনি জানেন, কে দুই চামচ চিনি খায়,", "আর কে বাকি রাখে।"],
    ["এক সন্ধ্যায় বেঞ্চে এসে বসে নাদিয়া,", "এক তরুণ ফ্রিল্যান্সার।", "“চাচা,", "আপনার দোকানটা স্মার্ট করে দিই?”",
     "রহিম চাচা হাসেন,", "“কেটলি আর বেঞ্চ,", "এখানে কম্পিউটার কী করবে?”"],
    ["নাদিয়া বানিয়ে দেয় একটা হোয়াটসঅ্যাপ বট।", "অফিস থেকেই অর্ডার,", "চিনির হিসাবও মনে রাখে।",
     "এক সপ্তাহে দিনে আশি কাপ থেকে বিক্রি দাঁড়ায় একশো চল্লিশে।"],
    ["কিন্তু পাশের দোকানদার মাথা নাড়েন,", "“মেশিন একদিন তোমার জায়গাই নিয়ে নেবে, রহিম।”",
     "সেই রাতে রহিম চাচার ঘুম আসে না।", "নিজের হাতেই কি নিজের বদলি বানাচ্ছেন?"],
    ["তারপর তিনি বোঝেন, বট অর্ডার নিতে পারে,", "কিন্তু ক্লান্ত রিকশাওয়ালার মেয়ের পরীক্ষার খবর নিতে পারে না।",
     "হিসাব রাখে মেশিন,", "যত্ন নেয় মানুষ।", "বছর শেষে রহিম চাচার দোকান তিনটা।"],
    ["এআই আপনার জায়গা নেয় না।", "নেয় আপনার কাজের বোঝা।", "শুধু সাহস করে তাকে সুযোগ দিতে হয়।"],
]
# subtitle chunks = runs of phrase indices (2-3 per scene); the closing card has none
SUBS = [[[0, 1], [2, 3]], [[0, 1], [2, 3], [4, 5, 6]], [[0], [1, 2], [3]], [[0, 1], [2], [3]], [[0, 1], [2, 3], [4]]]


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def silences(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=noise=-35dB:d=0.25", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(st, en + [None] * (len(st) - len(en))))


def tighten(path):
    """Chunk audio with long inner pauses shortened, plus its phrase (start, end) times in the result."""
    a = decode(path)
    dur = len(a) / SR
    lead = 0.0
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=noise=-35dB:d=0.04", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    first = re.search(r"silence_start: ([\d.]+)\s.*?silence_end: ([\d.]+)", err, re.S)
    if first and float(first.group(1)) < 0.01:
        lead = max(0.0, float(first.group(2)) - 0.03)
    inner, end = [], dur
    for s, e in silences(path):
        if e is None or e >= dur - 0.1:  # trailing silence (allow a few ms of codec tail)
            end = min(end, s + 0.05)
        elif s > lead + 0.05:
            inner.append((s, e))
    pieces, phrases, t, cur = [], [], 0.0, lead
    for s, e in inner + [(end, None)]:
        seg = a[int(cur * SR):int(s * SR)]
        phrases.append((t, t + len(seg) / SR))
        pieces.append(seg)
        t += len(seg) / SR
        if e is None:
            break
        gap = min(e - s, MAX_PAUSE)
        mid = (s + e) / 2  # keep the middle of the pause, where it is quietest
        pieces.append(a[int((mid - gap / 2) * SR):int((mid + gap / 2) * SR)])
        t += gap
        cur = e
    out = np.concatenate(pieces)
    f = int(0.004 * SR)
    out[:f] *= np.linspace(0, 1, f)
    out[-f:] *= np.linspace(1, 0, f)
    return out, phrases


def retime_clip(name, length):
    src, dst = CLIPS / "base" / f"{name}.mp4", CLIPS / f"{name}.mp4"
    k = length / 10.0
    vf = f"setpts={k:.5f}*PTS,minterpolate=fps=30:mi_mode=blend" if k > 1.001 else "fps=30"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", vf, "-t", f"{length:.3f}", "-an", "-c:v", "libx264",
                    "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(dst)], check=True)
    return k


def main():
    names = ["scene1", "scene2", "scene3", "scene4", "scene5", "closing"]
    track, scenes, phrase_t = [], [], []
    t = 0.0
    for i, name in enumerate(names):
        audio, ph = tighten(VO / "chunks" / f"c{i + 1}.mp3")
        assert len(ph) == len(PHRASES[i]), f"chunk {i + 1}: {len(ph)} phrases detected, {len(PHRASES[i])} in the script"
        speech = len(audio) / SR
        length = LEAD + speech + (CLOSE_HOLD if name == "closing" else TAIL)
        length = round(round(length * 30) / 30, 4)  # whole frames
        seg = np.zeros(int(round(length * SR)), np.float32)
        o = int(LEAD * SR)
        seg[o:o + len(audio)] = audio[: len(seg) - o]
        track.append(seg)
        scenes.append({"name": name, "start": round(t, 4), "length": length})
        phrase_t.append([(round(t + LEAD + a, 3), round(t + LEAD + b, 3)) for a, b in ph])
        print(f"{name}: {length:6.3f}s  speech {speech:5.2f}s  clip x{length / 10:.3f}")
        t += length
    total = round(t, 4)
    voice = np.concatenate(track)
    sf.write(VO / "voice.wav", voice, SR)
    # -14 LUFS for Facebook: gentle 3:1 compression to tame peaks, then two-pass (measured, linear) loudnorm
    comp = "acompressor=threshold=-24dB:ratio=3:attack=5:release=120:makeup=4dB"
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(VO / "voice.wav"), "-af",
                           f"{comp},loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    m = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    norm = (f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
            f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(VO / "voice.wav"), "-af",
                    f"{comp},{norm},apad=whole_len={int(round(total * SR))},afade=t=in:d=0.3,afade=t=out:st={total - 1:.3f}:d=1",
                    "-ar", str(SR), "-ac", "2", str(VO / "mix.wav")], check=True)  # no -t: it cuts 67 ms early after loudnorm

    subs = []
    for i, runs in enumerate(SUBS):
        sc = scenes[i]
        for r, run in enumerate(runs):
            start = phrase_t[i][run[0]][0] - 0.08
            end = phrase_t[i][runs[r + 1][0]][0] - 0.08 if r + 1 < len(runs) else sc["start"] + sc["length"] - 0.04
            subs.append({"scene": i + 1, "start": round(start, 3), "end": round(end, 3),
                         "text": " ".join(PHRASES[i][k] for k in run)})
    cues = {
        "count": phrase_t[2][3][0],   # "...একশো চল্লিশে"
        "stamp": phrase_t[3][3][0],   # "নিজের হাতেই কি নিজের বদলি..."
        "labels": phrase_t[4][2][0],  # "হিসাব রাখে মেশিন"
        "close": [phrase_t[5][0][0], phrase_t[5][2][0]],  # card lines; the gray line with its own words
    }
    (ROOT / "timing.json").write_text(json.dumps({"total": total, "scenes": scenes, "subs": subs, "cues": cues,
                                                  "phrases": phrase_t}, indent=1, ensure_ascii=False))
    for i, name in enumerate(names):
        retime_clip(name, scenes[i]["length"])
    print(f"total {total:.3f}s")
    for c in subs:
        print(f"{c['start']:6.2f}-{c['end']:6.2f}  {c['text']}")
    print("cues", cues)


if __name__ == "__main__":
    main()
