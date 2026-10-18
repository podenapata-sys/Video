#!/usr/bin/env python3
"""Kinetic Bangla subtitles over the Rosemary Rice Water UGC clip.

  python3 scripts/build.py [--render]

Beat times are snapped to the footage's scene cuts and speech pauses
(cuts: 3.0 10.0 10.9 13.3 18.85 22.3 23.35 26.85). Text positions (y %) keep
clear of her face and the bottle in each shot; 22.3-23.35 (bottle close-up)
deliberately has no text.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ["node", "/root/.claude/plugins/cache/hyperframes/hyperframes/0.8.152/skills/hyperframes/scripts/plugin-cli.mjs"]
TOTAL = 28.85

els, js = [], []


def words(lid, text):
    """'চুল *পড়ছে?*' -> spans; *x* marks a rosemary-green keyword."""
    out = []
    for i, w in enumerate(text.split()):
        k = w.startswith("*")
        w = w.strip("*").replace("_", " ")
        out.append(f'<span class="w{" k" if k else ""}" id="{lid}-w{i}">{w}</span>')
    return "".join(out)


def line(lid, y, text, size=64, x=50, cls="", inner=None):
    return (f'<div class="pos" style="left:{x}%;top:{y}%"><div class="line {cls}" id="{lid}" '
            f'style="font-size:{size}px">{inner or words(lid, text)}</div></div>')


def beat(bid, start, end, body):
    els.append(f'      <div id="{bid}" class="clip beat" data-start="{start}" data-duration="{round(end - start, 3)}" '
               f'data-track-index="2">{body}</div>')
    js.append(f'tl.fromTo("#{bid}", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.2, immediateRender: false }}, {end - 0.2:.3f});')


def show(lid, t):
    js.append(f'tl.fromTo("#{lid}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.15 }}, {t:.3f});')


def pop(lid, t, stagger=0.07, ease="back.out(2.2)"):
    show(lid, t)
    js.append(f'tl.fromTo("#{lid} .w", {{ opacity: 0, scale: 0.85, y: 14 }}, '
              f'{{ opacity: 1, scale: 1, y: 0, duration: 0.3, ease: "{ease}", stagger: {stagger} }}, {t:.3f});')


# 1. Hook (0-3.0): big question before she speaks, second line on her first words (2.07)
beat("b1", 0, 3.0, line("l1a", 61, "চুল *পড়ছে?*", 150, cls="hook") + line("l1b", 70.5, "দিন দিন *পাতলা* লাগছে?", 66))
show("l1a", 0.12)
js.append('tl.fromTo("#l1a .w", { opacity: 0, scale: 0.5 }, { opacity: 1, scale: 1, duration: 0.32, ease: "back.out(2.6)", stagger: 0.1 }, 0.12);')
pop("l1b", 2.07)
js.append('tl.fromTo("#l1b-w2", { scale: 1 }, { scale: 1.14, duration: 0.18, yoyo: true, repeat: 1, ease: "sine.inOut", immediateRender: false }, 2.45);')

# 2. (3.0-5.0) slow fade
beat("b2", 3.0, 5.0, line("l2", 68, "আমিও ভাবতাম...", 72))
js.append('tl.fromTo("#l2", { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.7, ease: "power2.out" }, 3.1);')

# 3. (5.0-8.3) "শুধু Shampoo" first, then "বদলালেই হবে!?" with a bounce on হবে
beat("b3", 5.0, 8.3, line("l3a", 64, "শুধু *Shampoo*", 78) + line("l3b", 72, "বদলালেই *হবে!?*", 72))
pop("l3a", 5.1)
show("l3b", 6.4)
js.append('tl.fromTo("#l3b-w0", { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.3, ease: "power2.out" }, 6.4);')
js.append('tl.fromTo("#l3b-w1", { opacity: 0, y: -40, scale: 0.9 }, { opacity: 1, y: 0, scale: 1, duration: 0.55, ease: "bounce.out" }, 6.9);')

# 4. (8.3-10.0) curiosity reveal + slow zoom
beat("b4", 8.3, 10.0, line("l4", 68, "কিন্তু *আসলেই* কি তাই?", 72))
show("l4", 8.4)
js.append('tl.fromTo("#l4 .w", { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.35, ease: "power2.out", stagger: 0.16 }, 8.4);')
js.append('tl.fromTo("#l4", { scale: 1 }, { scale: 1.07, duration: 1.5, ease: "none", immediateRender: false }, 8.4);')

# 5. (10.0-13.33) top band, the bottle fills the middle of these shots
beat("b5", 10.0, 13.33, line("l5a", 13, "তাই আমার", 54, x=44) + line("l5b", 17.8, "*Hair_Care_Routine*-এ...", 74, x=44, inner=
     '<span class="w k" id="l5b-w0">Hair Care Routine</span><span class="w" id="l5b-w1">-এ...</span>'))
pop("l5a", 10.15)
pop("l5b", 10.6, stagger=0.15)

# 6. (13.33-16.55) product name: strongest moment, green bar wipes behind Rosemary
beat("b6", 13.33, 16.55,
     line("l6a", 57, "", 118, inner='<span class="w hl" id="l6a-w0"><i class="bar" id="l6bar"></i><b>Rosemary</b></span>')
     + line("l6b", 65, "Rice Water Hair Spray 🌿", 64))
show("l6a", 13.45)
js.append('tl.fromTo("#l6a-w0", { opacity: 0, scale: 0.8 }, { opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2)" }, 13.45);')
js.append('tl.fromTo("#l6bar", { scaleX: 0 }, { scaleX: 1, duration: 0.45, ease: "power3.inOut" }, 13.7);')
pop("l6b", 14.1, stagger=0.09)

# 7. (16.55-18.85) ingredient micro-cards
cards = ["Rosemary Leaf Extract", "Panthenol", "Peppermint Oil"]
beat("b7", 16.55, 18.85, "".join(
    f'<div class="pos" style="left:50%;top:{56 + 7.5 * i}%"><div class="card" id="c{i}"><i class="dot"></i>{c}</div></div>'
    for i, c in enumerate(cards)))
for i in range(3):
    js.append(f'tl.fromTo("#c{i}", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }}, {16.65 + 0.55 * i:.3f});')

# 8. (18.85-22.3) Spray -> Massage -> Routine, each word lights up as it lands
beat("b8", 18.85, 22.3, line("l8", 15, "Spray → Massage → Routine", 68))
show("l8", 19.0)
for i, t in enumerate([19.0, 19.0, 19.9, 19.9, 20.8]):
    js.append(f'tl.fromTo("#l8-w{i}", {{ opacity: 0, x: -16 }}, {{ opacity: 1, x: 0, duration: 0.3, ease: "power2.out" }}, {t + 0.12 * (i % 2):.3f});')
for i, t in [(0, 19.0), (2, 19.9), (4, 20.8)]:
    js.append(f'tl.fromTo("#l8-w{i}", {{ color: "#ffffff" }}, {{ color: "#8fd889", duration: 0.2, immediateRender: false }}, {t:.3f});')
    if i < 4:
        js.append(f'tl.fromTo("#l8-w{i}", {{ color: "#8fd889" }}, {{ color: "#ffffff", duration: 0.2, immediateRender: false }}, {t + 0.9:.3f});')

# 9. (23.35-25.0) easier — after the spray close-up
beat("b9", 23.35, 25.0, line("l9a", 62.5, "Hair Care এখন", 64) + line("l9b", 70, "*আরও_সহজ* ✨", 100, cls="bright"))
pop("l9a", 23.45)
pop("l9b", 23.85, stagger=0.12)

# 10. (25.0-26.85) premium price reveal
beat("b10", 25.0, 26.85, line("l10a", 56.5, "মাত্র", 60) + line("l10b", 64, "", 150, cls="price",
     inner='<span class="w" id="l10b-w0">1199 <em>BDT</em></span>'))
pop("l10a", 25.05)
show("l10b", 25.3)
js.append('tl.fromTo("#l10b-w0", { opacity: 0, scale: 0.9 }, { opacity: 1, scale: 1.05, duration: 0.35, ease: "power2.out" }, 25.3);')
js.append('tl.fromTo("#l10b-w0", { scale: 1.05 }, { scale: 1, duration: 0.3, ease: "power2.inOut", immediateRender: false }, 25.66);')

# 11. (26.85-end) CTA over the packshot, above the bottle and box
els.append(f'''      <div id="b11" class="clip beat" data-start="26.85" data-duration="{round(TOTAL - 26.85, 3)}" data-track-index="2">
        {line("l11", 12.5, "", 46, inner='<span class="w">আজ থেকেই</span><span class="w k">Hair Care Routine</span><span class="w">-এ যোগ করুন</span>')}
        <div class="pos" style="left:50%;top:18.6%"><div class="btn" id="btn">আজই অর্ডার করুন</div></div>
      </div>''')
js.append('tl.fromTo("#l11", { opacity: 0, y: 60 }, { opacity: 1, y: 0, duration: 0.45, ease: "power3.out" }, 26.9);')
js.append('tl.fromTo("#btn", { opacity: 0, y: 50, scale: 0.9 }, { opacity: 1, y: 0, scale: 1, duration: 0.4, ease: "back.out(2)" }, 27.25);')
js.append(f'tl.fromTo("#btn", {{ scale: 1 }}, {{ scale: 1.07, duration: 0.24, yoyo: true, repeat: 3, ease: "sine.inOut", immediateRender: false }}, {TOTAL - 1:.3f});')


PAGE = """<!doctype html>
<html lang="bn">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Rosemary Hair Spray UGC</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      @font-face { font-family: "Hind Siliguri"; font-weight: 700; src: url("assets/fonts/hind-siliguri-bengali-700-normal.woff2") format("woff2");
        unicode-range: U+0951-0952, U+0964-0965, U+0980-09FE, U+1CD0-1CF9, U+200C-200D, U+20B9, U+25CC, U+A8F1; }
      @font-face { font-family: "Hind Siliguri"; font-weight: 700; src: url("assets/fonts/hind-siliguri-latin-700-normal.woff2") format("woff2"); }
      @font-face { font-family: "Noto Color Emoji"; src: url("assets/fonts/NotoColorEmoji.ttf") format("truetype"); }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #000; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #000;
        font-family: "Hind Siliguri", "Noto Color Emoji", sans-serif; font-weight: 700; }
      video.clip { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
      .beat { position: absolute; inset: 0; z-index: 5; }
      .pos { position: absolute; transform: translate(-50%, -50%); }
      .line { color: #fff; white-space: nowrap; line-height: 1.3; padding: 0.1em 0.42em 0.02em; border-radius: 0.32em;
        background: rgba(8, 14, 10, 0.42); text-shadow: 0 3px 12px rgba(0, 0, 0, 0.6); opacity: 0; }
      .w { display: inline-block; margin: 0 0.12em; }
      .k { color: #8fd889; }
      .hook { background: rgba(8, 14, 10, 0.5); }
      .bright .k { color: #a8f0a0; text-shadow: 0 0 18px rgba(143, 216, 137, 0.55), 0 3px 12px rgba(0, 0, 0, 0.6); }
      .hl { position: relative; padding: 0 0.2em; }
      .hl b { position: relative; }
      .bar { position: absolute; inset: 0.1em 0 0.02em; background: #2f8a55; border-radius: 0.18em; transform-origin: left center; }
      .price em { font-style: normal; color: #8fd889; }
      .card { display: flex; align-items: center; gap: 18px; padding: 14px 34px; border-radius: 24px; white-space: nowrap;
        background: rgba(18, 58, 36, 0.8); border: 2px solid rgba(143, 216, 137, 0.6); color: #fff; font-size: 50px;
        line-height: 1.25; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35); opacity: 0; }
      .dot { width: 16px; height: 16px; border-radius: 50%; background: #8fd889; flex: none; }
      .btn { padding: 16px 56px 10px; border-radius: 999px; background: #2f8a55; color: #fff; font-size: 52px; white-space: nowrap;
        line-height: 1.3; box-shadow: 0 10px 26px rgba(0, 0, 0, 0.35), inset 0 0 0 2px rgba(255, 255, 255, 0.25); opacity: 0; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{{TOTAL}}" data-width="1080" data-height="1920" data-fps="30">
      <video id="ugc" class="clip" src="assets/ugc.mp4" data-start="0" data-duration="{{TOTAL}}" data-track-index="1" data-has-audio="true" playsinline></video>
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

(ROOT / "index.html").write_text(PAGE.replace("{{TOTAL}}", str(TOTAL)).replace("{{ELS}}", "\n".join(els))
                                 .replace("{{JS}}", "\n      ".join(js)))
print(f"built {len(els)} beats, {TOTAL}s")
if "--render" in sys.argv:
    out = ROOT / "renders" / "hair-spray-subtitled.mp4"
    r = subprocess.run(CLI + ["render", str(ROOT), "-o", str(out), "-q", "delivery"], capture_output=True, text=True)
    print("\n".join(l for l in r.stdout.splitlines() if "MB" in l or "rror" in l))
    share = out.with_name("hair-spray-subtitled-share.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out), "-c:v", "libx264", "-crf", "22", "-preset", "slow",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(share)], check=True)
    print("share:", share)
