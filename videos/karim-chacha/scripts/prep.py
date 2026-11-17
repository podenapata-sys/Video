#!/usr/bin/env python3
"""করিম চাচার সাইকেল prep: split the two voice files into the 7 lines at their measured pauses, normalise each
line to -20 LUFS, lay out the slots (voice 0.4 s into each clip; clips hold their last frame when a line is longer),
prepare the clips (muted, 30 fps, cover 1080x1920; clip 5 at 0.85x; scene 2 reuses PT-1 reframed on the cycle),
film grain, and build/timeline.json with caption and letter-line times."""
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "build"
V = ROOT / "assets/voice"
SR = 48000
# line spans in the source files (s), from silencedetect (narrator: 5 lines; Tanvir: 2 lines)
LINES = {"n1": ("narrator_lines", 0.00, 8.87), "n2": ("narrator_lines", 9.69, 15.65), "n3": ("narrator_lines", 16.29, 21.56),
         "n5": ("narrator_lines", 22.15, 26.32), "n6": ("narrator_lines", 26.85, 32.53),
         "t1": ("tanvir_lines", 0.21, 8.50), "t2": ("tanvir_lines", 8.97, 15.14)}
# caption phrases: (line, source start, text). n5 has no inner pause, so it splits by syllable share.
CAPS = [("n1", 0.00, "প্রতি বিকেলে, পোস্টঅফিসের সামনে এসে দাঁড়াতেন করিম চাচা…"),
        ("n1", 4.88, "হাতে একটা পুরনো সাইকেল,"),
        ("n1", 6.70, "আর চোখে ছেলের চিঠির অপেক্ষা।"),
        ("n2", 9.69, "ছেলে একদিন সাইকেলটা বিক্রি করতে বলেছিল…"),
        ("n2", 12.65, "কিন্তু এই সাইকেলেই তো তিনি তাকে রোজ স্কুলে নিয়ে যেতেন।"),
        ("n3", 16.29, "সেদিন পোস্টমাস্টার তার হাতে একটা খাম তুলে দিলেন…"),
        ("n3", 19.93, "এবারের খামটা ছিল অন্যরকম।"),
        ("n5", 22.15, "চিঠিটা বুকে জড়িয়ে ধরে"),
        ("n5", 23.95, "করিম চাচার চোখ বেয়ে অশ্রু গড়িয়ে পড়ল।"),
        ("n6", 26.85, "পাঁচ বছরের অপেক্ষা শেষ…"),
        ("n6", 28.99, "কাল সকালের সূর্যটা যেন তার জীবনের সবচেয়ে সুন্দর সকাল।")]
LETTER = [("t1", 0.21, "বাবা, পাঁচ বছর ধরে আমি শুধু টাকা পাঠিয়েছি…"),
          ("t1", 4.69, "তোমার সাথে এক কাপ চা খাওয়ার সময় পাইনি।"),
          ("t1", 7.49, "কাল আমি দেশে ফিরছি।"),
          ("t2", 8.97, "তুমি তোমার সেই পুরনো সাইকেলটা নিয়ে স্টেশনে থেকো…"),
          ("t2", 11.92, "আমরা দুজন আবার আগের মতো গল্প করতে করতে বাড়ি ফিরব।")]
# slot -> source clip, speed, voice lines (in order, with gap before), reframe
SLOTS = [(1, "01", 1.00, ["n1"]), (2, "01", 1.00, ["n2"]), (3, "02", 1.00, ["n3"]), (4, "03", 1.00, ["t1"]),
         (5, "04", 0.85, ["t2", "n5"]), (6, "05", 1.00, ["n6"])]
LEAD, MIN_SLOT, TAIL, XF, DIP, END_HOLD = 0.4, 8.0, 0.6, 0.5, 0.6, 1.5


def line_audio(key):
    f, a, b = LINES[key]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, a - 0.05):.3f}", "-to", f"{b + 0.12:.3f}", "-i", str(V / f"{f}.mp3"),
                          "-af", "loudnorm=I=-20:TP=-2:LRA=7", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    n = int(0.01 * SR)
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return x


def main():
    audio = {k: line_audio(k) for k in LINES}
    slots, t, place = [], 0.0, {}
    for n, src, speed, keys in SLOTS:
        at = t + LEAD
        for i, k in enumerate(keys):
            if i:
                at += 0.5                                  # n5 starts 0.5 s after t2 ends
            place[k] = at
            at += len(audio[k]) / SR
        end = max(t + MIN_SLOT, at + TAIL)
        slots.append({"n": n, "src": src, "speed": speed, "start": round(t, 3), "end": round(end, 3), "lines": keys})
        t = end + (DIP if n == 3 else 0.0)
    total = round(slots[-1]["end"] + END_HOLD, 3)
    slots[-1]["end"] = total
    voice = np.zeros(int(round(total * SR)), np.float32)
    spans = {}
    for k, at in place.items():
        o = int(round(at * SR))
        voice[o:o + len(audio[k])] += audio[k][:len(voice) - o]
        spans[k] = [round(at, 3), round(at + len(audio[k]) / SR, 3)]
    sf.write(B / "voice.wav", np.stack([voice, voice], 1), SR)

    def absolute(key, src_t):
        return round(place[key] + (src_t - LINES[key][1]) + 0.05, 3)

    caps = []
    for i, (k, s, txt) in enumerate(CAPS):
        a = absolute(k, s)
        same = i + 1 < len(CAPS) and CAPS[i + 1][0] == k
        b = absolute(k, CAPS[i + 1][1]) if same else spans[k][1] + 0.25
        caps.append({"line": k, "text": txt, "start": a, "end": round(b, 3)})
    letter = [{"line": k, "text": txt, "start": absolute(k, s)} for k, s, txt in LETTER]
    # clips: forward once at their speed, then hold the last frame; handles for the 0.5 s crossfades
    for s in slots:
        n = s["n"]
        pre = XF / 2 if n not in (1, 4) else 0.0
        post = XF / 2 if n not in (3, 6) else 0.0
        s["clip_start"], s["clip_dur"] = round(s["start"] - pre, 3), round(s["end"] - s["start"] + pre + post, 3)
        reframe = "crop=iw/1.45:ih/1.45:(iw-iw/1.45)*0.5:(ih-ih/1.45)*0.78," if n == 2 else ""
        src_in = 1.0 if n == 2 else 0.0
        vf = (f"setpts=PTS/{s['speed']:.3f},fps=30,{reframe}scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,"
              f"tpad=stop_mode=clone:stop_duration=12,trim=duration={s['clip_dur']:.3f}")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{src_in}", "-i", str(ROOT / "assets/clips" / f"{s['src']}.mp4"), "-vf", vf, "-an",
                        "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p", str(B / f"c{n}.mp4")], check=True)
        play = (4.0 - src_in) / s["speed"]
        s["hold_from"] = round(s["clip_start"] + play, 3)
        print(f"  slot {n}: {s['start']:6.2f}-{s['end']:6.2f}  clip {s['src']} x{s['speed']}  plays {play:.1f}s, holds {max(0, s['clip_dur'] - play):.1f}s  lines {s['lines']}")
    rng = np.random.default_rng(11)
    Image.fromarray(rng.normal(128, 44, (640, 640)).clip(0, 255).astype(np.uint8), "L").save(B / "grain.png")
    tl = {"total": total, "end_card": round(total - END_HOLD, 3), "slots": slots, "spans": spans, "captions": caps, "letter": letter}
    (B / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    for k in ("n1", "n2", "n3", "t1", "t2", "n5", "n6"):
        print(f"  {k}: {spans[k][0]:6.2f}-{spans[k][1]:6.2f}")
    print(f"total {total}s")


if __name__ == "__main__":
    main()
