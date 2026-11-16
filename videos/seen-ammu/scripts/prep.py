#!/usr/bin/env python3
"""seen-ammu prep (voice-driven): the voiceover (assets/voiceover.mp3) is split at its 6 story beats (all on measured
pauses) and each piece starts 0.3 s into its slot; slots last as long as their voice piece + breathing room.
6 clips (PT-5 was a byte-identical duplicate of PT-4). Writes build/voice.wav, build/c1..c6.mp4, build/grain.png,
build/timeline.json (slots, caption chunks with absolute times, voice-note span, end card)."""
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "build"
SR = 48000
# beat boundaries in the voiceover (s) -- midpoints of measured pauses
BEATS = [0.0, 6.15, 13.08, 17.70, 26.73, 33.43, None]           # None = end of file
# caption chunks (voice-relative start, text); each runs until the next chunk / the end of its beat
CAPS = [
    (0.00, "মা'র ফোন এলে আমি কেটে দিতাম।"),
    (2.82, "গেমের কাছে তখন বাকি সবকিছু জিরো ছিল।"),
    (6.15, "ওদিকে এক মা প্রতিদিন দু'জনের ভাত বেড়ে রাখত।"),
    (9.67, "মেসেজ পাঠাত…"),
    (10.96, "Seen হতো, রিপ্লাই আসত না।"),
    (13.08, "বন্ধুদের আড্ডায় ফোনটা পড়ে থাকত।"),
    (15.50, "আমি ভাবতাম, এটাই জীবন।"),
    (17.70, "তারপর এক রাতে একটা কল এলো…"),
    (20.31, "মা'র নম্বর থেকে…"),
    (23.05, "সেদিন বুঝলাম, অনেক দেরি হয়ে গেছে…"),
    (26.73, "ফোনে ছিল ৪৭টা না-পড়া মেসেজ।"),
    (29.39, "শেষ ভয়েসে মা শুধু বলেছিল…"),
    (31.59, "“বাবা, ভাত খাইছো?”"),
    (33.43, "একটা ফোন করিস, আর কিছু চাই না…"),
    (37.28, "আজ কি আপনি মাকে রিপ্লাই দিয়েছেন?"),
]
CLIP_IN = [0.0, 1.0, 1.0, 0.0, 0.0, 0.0]       # source in-points (s)
LEAD, GAP, BLACK, END_CARD = 0.3, 0.35, 0.5, 2.5
MIN_SLOT = {3: 5.5}                             # slot 3 needs room for the 3 missed-call cards
XF = 0.3


def dec(p, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def main():
    v = dec(ROOT / "assets/voiceover.mp3")
    L = len(v) / SR
    beats = BEATS[:-1] + [L]
    slots, t, pieces = [], 0.0, []
    for n in range(1, 7):
        b0, b1 = beats[n - 1], beats[n]
        vo_at = t + (0.5 if n == 1 else LEAD)
        pieces.append((vo_at, v[int(b0 * SR):int(b1 * SR)]))
        end = max(vo_at + (b1 - b0) + GAP, t + MIN_SLOT.get(n, 0))
        slots.append({"n": n, "start": round(t, 3), "end": round(end, 3), "vo_at": round(vo_at, 3), "vo_from": b0, "vo_to": round(b1, 3)})
        t = end + (BLACK if n == 3 else 0.0)
    end_card = slots[-1]["end"]
    total = round(end_card + END_CARD, 3)
    slots[-1]["end"] = total
    out = np.zeros(int(round(total * SR)) + SR, np.float32)
    for at, p in pieces:
        f = int(0.008 * SR)
        p = p.copy()
        p[:f] *= np.linspace(0, 1, f)
        p[-f:] *= np.linspace(1, 0, f)
        o = int(round(at * SR))
        out[o:o + len(p)] += p
    out = out[:int(round(total * SR))]
    sf.write(B / "voice.wav", np.stack([out, out], 1), SR)

    def absolute(rel):
        for s in slots:
            if s["vo_from"] - 1e-6 <= rel < s["vo_to"] - 1e-6 or (s["n"] == 6 and rel <= s["vo_to"] + 1e-6):
                return round(s["vo_at"] + rel - s["vo_from"], 3), s["n"]
        raise ValueError(rel)

    caps = []
    for i, (rel, text) in enumerate(CAPS):
        a, n = absolute(rel)
        s = next(x for x in slots if x["n"] == n)
        nxt = absolute(CAPS[i + 1][0])[0] if i + 1 < len(CAPS) and absolute(CAPS[i + 1][0])[1] == n else s["vo_at"] + s["vo_to"] - s["vo_from"] + 0.35
        caps.append({"slot": n, "text": text, "start": a, "end": round(min(nxt, end_card if n == 6 else s["end"]), 3)})
    voice_note = [absolute(29.39)[0], absolute(33.40)[0]]
    cues = {"decline": absolute(1.45)[0], "seen": absolute(10.96)[0], "count47": absolute(26.73)[0], "voice_note": voice_note,
            "reply_type": absolute(33.43)[0], "question": absolute(37.28)[0]}
    # clips: each covers its slot (+ crossfade handles for 4->5, 5->6), cover 1080x1920, 30 fps, muted
    for s in slots:
        n = s["n"]
        pre = XF if n in (5, 6) else 0.0
        post = XF if n in (4, 5) else 0.0
        s["clip_start"], s["clip_dur"] = round(s["start"] - pre, 3), round(s["end"] - s["start"] + pre + post, 3)
        s_in = max(0.0, CLIP_IN[n - 1] - pre)
        vf = (f"fps=30,scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,"
              f"tpad=stop_mode=clone:stop_duration=3,trim=duration={s['clip_dur']:.3f}")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s_in:.3f}", "-i", str(ROOT / "assets/clips" / f"0{n}.mp4"), "-vf", vf, "-an",
                        "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p", str(B / f"c{n}.mp4")], check=True)
        print(f"  slot {n}: {s['start']:6.2f}-{s['end']:6.2f}  voice {s['vo_at']:6.2f}-{s['vo_at'] + s['vo_to'] - s['vo_from']:6.2f}  clip {s['clip_dur']:.2f}s")
    rng = np.random.default_rng(7)
    Image.fromarray(rng.normal(128, 46, (640, 640)).clip(0, 255).astype(np.uint8), "L").save(B / "grain.png")
    tl = {"total": total, "end_card": end_card, "slots": slots, "captions": caps, "cues": cues}
    (B / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    for c in caps:
        print(f"  {c['start']:6.2f}-{c['end']:6.2f} s{c['slot']} {c['text']}")
    print(f"total {total}s, end card {end_card}s, cues {cues}")


if __name__ == "__main__":
    main()
