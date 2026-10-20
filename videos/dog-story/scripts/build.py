#!/usr/bin/env python3
"""Map the 10 story clips onto the voice timeline and build index.html.

  python3 scripts/build.py [--render]

Run scripts/voice.py first. The timeline is split into 10 segments (clip 1 -> 10,
story order); every boundary snaps to the nearest pause between sentences, so a
cut never lands mid-sentence. Each clip is slowed to fill its segment (frame-blend
slow motion) and gets a slow Ken Burns push on top.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "src" / "story.mp4"
CLIPS = ROOT / "assets" / "clips"
CLI = ["node", "/root/.claude/plugins/cache/hyperframes/hyperframes/0.8.152/skills/hyperframes/scripts/plugin-cli.mjs"]
N, CLIP_LEN, DIP = 10, 10.0417, 0.4


def duration(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout)


def boundaries(vmap, total):
    """10 segment starts; each interior cut sits in the middle of the sentence gap nearest total*i/N."""
    gaps = [(a["end"] + b["start"]) / 2 for a, b in zip(vmap, vmap[1:])]
    cuts = [0.0]
    for i in range(1, N):
        target = total * i / N
        cuts.append(round(min((g for g in gaps if g > cuts[-1] + 5), key=lambda g: abs(g - target)), 3))
    return cuts + [total]


def stretch(i, seg):
    """Slow clip i to exactly `seg` seconds (24fps frame blend), 1920x1080, no audio."""
    out = CLIPS / f"c{i + 1:02d}.mp4"
    src_len = min(CLIP_LEN, duration(SRC) - i * CLIP_LEN) - 0.05  # stay clear of the next clip's first frame
    k = seg / src_len
    if out.exists() and abs(duration(out) - seg) < 0.25:  # blend output can run ~0.15s short
        return out
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{i * CLIP_LEN:.3f}", "-t", f"{src_len:.3f}", "-i", str(SRC),
                    "-map", "0:v:0", "-an", "-vf",
                    f"scale=1920:1080:flags=lanczos,setpts={k:.4f}*PTS,minterpolate=fps=24:mi_mode=blend",
                    "-t", f"{seg:.3f}", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", str(out)],
                   check=True)
    return out


def main():
    vmap = json.loads((ROOT / "voice_map.json").read_text())
    total = round(duration(ROOT / "assets" / "vo" / "voice.wav") + 0.6, 3)  # short tail after the last word
    cuts = boundaries(vmap, total)
    CLIPS.mkdir(exist_ok=True)
    els, js = [], []
    for i in range(N):
        a, b = cuts[i], cuts[i + 1]
        seg = round(b - a, 3)
        clip = stretch(i, seg)
        els.append(f'<video id="v{i}" class="clip shot" src="assets/clips/{clip.name}" data-start="{a:.3f}" '
                   f'data-duration="{seg:.3f}" data-track-index="1" muted playsinline></video>')
        x = 2 if i % 2 == 0 else -2  # alternate pan direction
        js.append(f'tl.fromTo("#v{i}", {{ scale: 1.0, xPercent: {-x / 2} }}, {{ scale: 1.08, xPercent: {x / 2}, duration: {seg:.3f}, ease: "none" }}, {a:.3f});')
        if i:  # dip to black across the cut
            js.append(f'tl.fromTo("#dip", {{ opacity: 1 }}, {{ opacity: 0, duration: {DIP}, ease: "power1.out", immediateRender: false }}, {a:.3f});')
            js.append(f'tl.fromTo("#dip", {{ opacity: 0 }}, {{ opacity: 1, duration: {DIP}, ease: "power1.in", immediateRender: false }}, {a - DIP:.3f});')
        print(f"clip {i + 1:2d}: {a:7.2f} -> {b:7.2f}  ({seg:5.2f}s, x{seg / CLIP_LEN:.2f} slow)")
    js.insert(0, 'tl.fromTo("#dip", { opacity: 1 }, { opacity: 0, duration: 0.8, ease: "power1.out" }, 0);')
    js.append(f'tl.fromTo("#dip", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6, ease: "power1.in", immediateRender: false }}, {total - 0.6:.3f});')
    # final mix (voice + drone + SFX) from scripts/mix.py when present, else the dry voice
    track = "mix.wav" if (ROOT / "assets" / "vo" / "mix.wav").exists() else "voice.wav"
    els.append(f'<audio id="vo" src="assets/vo/{track}" data-start="0" data-duration="{total}" data-track-index="4" data-volume="1"></audio>')
    (ROOT / "index.html").write_text(PAGE.replace("{{TOTAL}}", str(total)).replace("{{ELS}}", "\n      ".join(els))
                                     .replace("{{JS}}", "\n      ".join(js)))
    (ROOT / "segments.json").write_text(json.dumps([{"clip": i + 1, "start": cuts[i], "end": cuts[i + 1]} for i in range(N)], indent=1))
    print(f"built {total}s")
    if "--render" in sys.argv:
        out = ROOT / "renders" / "dog-story.mp4"
        r = subprocess.run(CLI + ["render", str(ROOT), "-o", str(out), "-q", "delivery"], capture_output=True, text=True)
        print("\n".join(l for l in r.stdout.splitlines() if "MB" in l or "rror" in l))
        share = out.with_name("dog-story-share.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out), "-c:v", "libx264", "-crf", "20", "-preset", "slow",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(share)], check=True)
        print("share:", share)


PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>Dog Story</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1920px; height: 1080px; overflow: hidden; background: #000; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #000; }
      .shot { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
      #vignette { position: absolute; inset: 0; z-index: 5; pointer-events: none;
        background: radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%); }
      #dip { position: absolute; inset: 0; z-index: 6; background: #000; opacity: 1; pointer-events: none; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{{TOTAL}}" data-width="1920" data-height="1080" data-fps="24">
      {{ELS}}
      <div id="vignette"></div>
      <div id="dip"></div>
    </div>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      {{JS}}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    main()
