#!/usr/bin/env python3
"""seen-ammu prep: 6 slots (PT-5 was a byte-identical duplicate of PT-4, so 6 clips), each clip trimmed to its best
window, cover 1080x1920, 30 fps, muted, with handles for the crossfades; film-grain tile; build/timeline.json."""
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "build"
# slot: (source in-point, slot start, slot end) -- black gap 24.0-24.5 between slots 3 and 4; end card 48.5-51.0 on slot 6
SLOTS = [(0.0, 0.0, 8.0), (2.0, 8.0, 16.0), (1.0, 16.0, 24.0), (1.5, 24.5, 32.5), (0.5, 32.5, 40.5), (0.0, 40.5, 51.0)]
XF = 0.3   # half of the 0.6 s crossfade (slots 4->5, 5->6)
TOTAL, END_CARD = 51.0, 48.5


def main():
    tl = {"total": TOTAL, "end_card": END_CARD, "slots": []}
    for n, (src_in, t0, t1) in enumerate(SLOTS, 1):
        pre = XF if n in (5, 6) else 0.0           # crossfaded-in clips start early
        post = XF if n in (4, 5) else 0.0          # crossfaded-out clips run late
        start, dur = t0 - pre, (t1 - t0) + pre + post
        s_in = max(0.0, src_in - pre)
        vf = (f"fps=30,scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,"
              f"tpad=stop_mode=clone:stop_duration=2,trim=duration={dur:.3f}")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s_in:.3f}", "-i", str(ROOT / "assets/clips" / f"0{n}.mp4"), "-vf", vf, "-an",
                        "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p", str(B / f"c{n}.mp4")], check=True)
        tl["slots"].append({"n": n, "start": t0, "end": t1, "clip_start": round(start, 3), "clip_dur": round(dur, 3)})
        print(f"  slot {n}: {t0:5.2f}-{t1:5.2f}  clip {start:5.2f}+{dur:.2f}s from {s_in:.2f}s")
    # film grain: seeded mono noise tile (deterministic), shifted on the timeline
    rng = np.random.default_rng(7)
    g = (rng.normal(128, 46, (640, 640))).clip(0, 255).astype(np.uint8)
    Image.fromarray(g, "L").save(B / "grain.png")
    (B / "timeline.json").write_text(json.dumps(tl, indent=1))


if __name__ == "__main__":
    main()
