#!/usr/bin/env python3
"""Stacked "watch me cook" Reel: face-cam top, screen step bottom, seam captions.

  python3 scripts/build.py [--render]

Reads steps.json. Footage lives in assets/footage/ (hook.mp4, face.mp4, s1.mp4 ...,
payout.png, optional music.mp3). Any missing file becomes a grey stand-in card so
timing and captions can be previewed before filming.
"""
import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOOT = ROOT / "assets" / "footage"
CLI = ["node", "/root/.claude/plugins/cache/hyperframes/hyperframes/0.8.152/skills/hyperframes/scripts/plugin-cli.mjs"]
W, H = 1080, 1920


def placeholder(label, w, h):
    from PIL import Image, ImageDraw, ImageFont

    slug = "".join(c if c.isalnum() else "-" for c in label.lower()).strip("-")
    path = ROOT / "assets" / f"placeholder-{slug}.png"
    if not path.exists():
        im = Image.new("RGB", (w, h), (52, 52, 56))
        d = ImageDraw.Draw(im)
        d.rectangle([12, 12, w - 13, h - 13], outline=(90, 90, 96), width=4)
        try:
            f = ImageFont.load_default(size=56)
        except TypeError:
            f = ImageFont.load_default()
        d.text((w / 2, h / 2), label, fill=(170, 170, 176), font=f, anchor="mm")
        im.save(path)
    return path.relative_to(ROOT).as_posix()


def media(name, label, w, h, start, dur, cls, eid, offset=0.0):
    """<video> for real footage (muted: music carries the audio), <img> stand-in otherwise."""
    attrs = f'id="{eid}" class="clip {cls}" data-start="{start:.3f}" data-duration="{dur:.3f}" data-track-index="1"'
    f = FOOT / name if name else None
    if f and f.exists() and f.suffix == ".mp4":
        trim = f' data-media-start="{offset:.3f}"' if offset else ""
        return f'<video {attrs} src="assets/footage/{name}"{trim} muted playsinline></video>'
    src = f"assets/footage/{name}" if f and f.exists() else placeholder(label, w, h)
    return f'<img {attrs} src="{src}" alt="" />'


def main():
    cfg = json.loads((ROOT / "steps.json").read_text())
    els, js, t = [], [], 0.0

    hook = cfg["hook"]
    d = hook["hold"]
    els.append(media(hook["clip"], "HOOK: drink / snack", W, H, t, d, "full", "hook"))
    els.append(f'<div id="hooktxt" class="clip band" data-start="0" data-duration="{d:.3f}" data-track-index="3">'
               f'{html.escape(hook["text"])}</div>')
    t += d

    steps_start = t
    for i, s in enumerate(cfg["steps"], 1):
        d = s["hold"]
        sid = f"s{i}"
        els.append(media(s["clip"], f"SCREEN: step {i}", W, H // 2, t, d, "bottom", sid))
        els.append(f'<div id="{sid}cap" class="clip cap" data-start="{t:.3f}" data-duration="{d:.3f}" data-track-index="3">'
                   f'{html.escape(s["caption"])}</div>')
        js.append(f'tl.fromTo("#{sid}", {{ scale: 1 }}, {{ scale: 1.05, duration: {d:.3f}, ease: "none" }}, {t:.3f});')
        t += d
    # one continuous face-cam across all steps, so the stare never jumps
    els.append(media(cfg["face"], "FACE CAM", W, H // 2, steps_start, t - steps_start, "top", "face"))

    p = cfg["payout"]
    d = p["hold"]
    els.append(media(p["image"], "REAL payout screenshot", W, H, t, d, "full", "payout"))
    els.append(f'<div id="paycap" class="clip cap" data-start="{t:.3f}" data-duration="{d:.3f}" data-track-index="3" '
               f'style="top:auto;bottom:22%">{html.escape(p["caption"])}</div>')
    js.append(f'tl.fromTo("#payout", {{ scale: 1 }}, {{ scale: 1.12, duration: {d:.3f}, ease: "power1.inOut" }}, {t:.3f});')
    t += d

    total = round(t, 3)
    if (FOOT / cfg.get("music", "")).is_file():
        els.append(f'<audio id="music" src="assets/footage/{cfg["music"]}" data-start="0" data-duration="{total}" '
                   f'data-track-index="4" data-volume="0.8"></audio>')
    page = PAGE.replace("{{TOTAL}}", str(total)).replace("{{ELS}}", "\n      ".join(els)) \
               .replace("{{JS}}", "\n      ".join(js))
    (ROOT / "index.html").write_text(page)
    print(f"built hook + {len(cfg['steps'])} steps + payout, {total}s")
    if "--render" in sys.argv:
        out = ROOT / "renders" / "money-pov.mp4"
        r = subprocess.run(CLI + ["render", str(ROOT), "-o", str(out), "-q", "delivery"], capture_output=True, text=True)
        print("\n".join(l for l in r.stdout.splitlines() if "MB" in l or "rror" in l))
        share = out.with_name("money-pov-share.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out), "-c:v", "libx264", "-crf", "22", "-preset", "slow",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(share)], check=True)
        print("share:", share)


PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Watch Me Cook</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #000; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #000; font-family: "Montserrat", sans-serif; }
      .full { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
      .top { position: absolute; left: 0; top: 0; width: 100%; height: 50%; object-fit: cover; }
      .bottom { position: absolute; left: 0; top: 50%; width: 100%; height: 50%; object-fit: cover; transform-origin: 50% 0%; }
      .band { position: absolute; left: 0; top: 0; width: 100%; height: 420px; background: #000; z-index: 10;
        display: flex; align-items: flex-end; justify-content: center; padding: 0 70px 34px; text-align: center;
        color: #fff; font-size: 46px; font-weight: 600; line-height: 1.22; }
      .cap { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); z-index: 10; white-space: nowrap;
        color: #fff; font-size: 40px; font-weight: 600; letter-spacing: 0.005em;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.9), 0 0 14px rgba(0, 0, 0, 0.7); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{{TOTAL}}" data-width="1080" data-height="1920" data-fps="30">
      {{ELS}}
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
