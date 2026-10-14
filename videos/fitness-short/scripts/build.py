#!/usr/bin/env python3
"""Assemble the illustrated transformation Short from story.json + images/NN.png.

  python3 scripts/build.py [--render]

Missing images fall back to generated blue placeholder frames, so timing and
dialogue can be previewed before the real illustrations exist.
"""
import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ["node", "/root/.claude/plugins/cache/hyperframes/hyperframes/0.8.152/skills/hyperframes/scripts/plugin-cli.mjs"]
W, H = 1080, 1920
BLUE = (30, 143, 225)


def placeholder(n, path):
    from PIL import Image, ImageDraw, ImageFont

    im = Image.new("RGB", (W, H), BLUE)
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.load_default(size=90)
    except TypeError:
        f = ImageFont.load_default()
    d.text((W / 2, H * 0.62), f"SHOT {n:02d}", fill=(255, 255, 255), font=f, anchor="mm")
    for x in (330, 750):  # two stand-in figures
        d.ellipse([x - 45, 820, x + 45, 910], fill=(20, 60, 110))
        d.rounded_rectangle([x - 70, 920, x + 70, 1400], 40, fill=(20, 60, 110))
    im.save(path)


def main():
    story = json.loads((ROOT / "story.json").read_text())
    program = story.get("program", "[PROGRAM]")
    els, js, t = [], [], 0.0
    for i, shot in enumerate(story["shots"]):
        n, d = i + 1, float(shot["hold"])
        img = ROOT / "images" / shot["image"]
        if not img.exists():
            img = ROOT / "images" / f"placeholder-{n:02d}.png"
            if not img.exists():
                placeholder(n, img)
        sid = f"shot{n:02d}"
        labels = ""
        for j, ln in enumerate(shot.get("lines", [])):
            txt = html.escape(ln["text"].replace("[PROGRAM]", program)).upper()
            big = " big" if txt == "READ CAPTION" else ""
            labels += f'<div class="say{big}" id="{sid}-l{j}" style="left:{ln["x"]}%;top:{ln["y"]}%">{txt}</div>'
            delay = 0.12 + (0.22 * j if len(shot["lines"]) > 1 else 0)
            js.append(f'tl.fromTo("#{sid}-l{j}", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.15, ease: "back.out(2.5)" }}, {t + delay:.3f});')
            if big:
                js.append(f'tl.to("#{sid}-l{j}", {{ scale: 1.1, duration: 0.3, yoyo: true, repeat: {max(1, int((d - 0.6) / 0.3) - 1)}, ease: "sine.inOut" }}, {t + 0.5:.3f});')
        dark = '<div class="dark"></div>' if shot.get("dark") else ""
        els.append(f'''      <div id="{sid}" class="clip shot" data-start="{t:.3f}" data-duration="{d:.3f}" data-track-index="1">
        <div class="kb"><img src="images/{img.name}" alt="" /></div>{dark}{labels}
      </div>''')
        js.append(f'tl.fromTo("#{sid} .kb", {{ scale: 1.0 }}, {{ scale: 1.04, duration: {d:.3f}, ease: "none" }}, {t:.3f});')
        if shot.get("dark"):
            js.append(f'tl.fromTo("#{sid} .dark", {{ opacity: 0 }}, {{ opacity: 0.72, duration: 0.25 }}, {t:.3f});')
        if shot.get("flash"):
            js.append(f'tl.fromTo("#flash", {{ opacity: 0.9 }}, {{ opacity: 0, duration: 0.3, ease: "power2.out", immediateRender: false }}, {t:.3f});')
        if shot.get("punch"):
            js.append(f'tl.fromTo("#{sid}", {{ scale: 1.12 }}, {{ scale: 1, duration: 0.35, ease: "expo.out" }}, {t:.3f});')
        t += d
    total = round(t, 3)
    music = ROOT / "music.mp3"
    audio = (f'      <audio id="music" src="music.mp3" data-start="0" data-duration="{total}" data-track-index="4" data-volume="0.9"></audio>\n'
             if music.exists() else "")
    page = PAGE.replace("{{ELS}}", "\n".join(els)).replace("{{JS}}", "\n      ".join(js)) \
               .replace("{{TOTAL}}", str(total)).replace("{{AUDIO}}", audio)
    (ROOT / "index.html").write_text(page)
    print(f"built {len(story['shots'])} shots, {total}s")
    if "--render" in sys.argv:
        (ROOT / "renders").mkdir(exist_ok=True)
        r = subprocess.run(CLI + ["render", str(ROOT), "-o", str(ROOT / "renders" / "short.mp4"), "-q", "delivery"],
                           capture_output=True, text=True)
        print("\n".join(l for l in r.stdout.splitlines() if "MB" in l or "rror" in l))


PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Transformation Short</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #1e8fe1; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #1e8fe1; font-family: "Montserrat", sans-serif; }
      .shot { position: absolute; inset: 0; overflow: hidden; }
      .kb { width: 100%; height: 100%; }
      .kb img { width: 100%; height: 100%; object-fit: cover; display: block; }
      .dark { position: absolute; inset: 0; background: #021022; opacity: 0; }
      .say { position: absolute; transform: translate(-50%, -50%); max-width: 460px; text-align: center; white-space: normal;
        color: #ffd43b; font-size: 38px; font-weight: 800; line-height: 1.12; letter-spacing: 0.01em;
        text-shadow: 0 2px 0 #0b2a4a, 0 0 10px rgba(5, 25, 50, 0.55); }
      .say.big { font-size: 64px; max-width: 900px; padding: 14px 34px; border-radius: 18px; background: rgba(5, 25, 50, 0.78); white-space: nowrap; }
      #flash { position: absolute; inset: 0; background: #fff; opacity: 0; pointer-events: none; z-index: 50; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{{TOTAL}}" data-width="1080" data-height="1920" data-fps="30">
{{ELS}}
      <div id="flash"></div>
{{AUDIO}}    </div>
    <script>
      const tl = gsap.timeline({ paused: true });
      {{JS}}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    main()
