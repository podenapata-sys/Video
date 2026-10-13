#!/usr/bin/env python3
"""Generate the product-photo clips for the LED clock ad as HyperFrames projects.

  python3 scripts/build_clips.py [--price 1250]

Writes clips/<name>/index.html for clip2_pushin, clip3_orbit, clip4_pullback and
clip6_offer. Every move is a transform of the ORIGINAL photo (no generated pixels),
so the clock digits can never be altered.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1920
SRC_W, SRC_H = 1522, 1033          # assets/clock.png
K = W / SRC_W                      # fit-width scale
HERO_H = round(SRC_H * K)          # 733
HERO_TOP = (H - HERO_H) // 2       # 593
DIGITS = (840, 560)                # centre of the "02:30" block in source px
OX, OY = DIGITS[0] * K, DIGITS[1] * K
DX, DY = W / 2 - OX, HERO_H / 2 - OY   # translate that brings the digits to frame centre
ZOOM = 1.75
# clock glass polygon (source px) -> % of hero, for the specular sweep
PANEL = [(230, 355), (1280, 345), (1283, 715), (232, 800)]
PANEL_CSS = ", ".join(f"{x / SRC_W * 100:.1f}% {y / SRC_H * 100:.1f}%" for x, y in PANEL)

BASE_CSS = f"""
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: #1a140f; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #1a140f; }}
      #backdrop {{ position: absolute; inset: -80px; }}
      #backdrop img {{ width: 100%; height: 100%; object-fit: cover; filter: blur(40px) brightness(0.62) saturate(1.1); display: block; }}
      #hero {{ position: absolute; left: 0; top: {HERO_TOP}px; width: {W}px; height: {HERO_H}px;
        transform-origin: {OX:.1f}px {OY:.1f}px; }}
      #hero img, #hero2 img {{ width: 100%; height: 100%; display: block;
        -webkit-mask-image: linear-gradient(180deg, transparent 0%, #000 9%, #000 91%, transparent 100%);
        mask-image: linear-gradient(180deg, transparent 0%, #000 9%, #000 91%, transparent 100%); }}
      #vignette {{ position: absolute; inset: 0; pointer-events: none;
        background: radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0) 45%, rgba(20,12,4,0.55) 100%); }}
      #sweep {{ position: absolute; inset: 0; clip-path: polygon({PANEL_CSS}); overflow: hidden; pointer-events: none; }}
      #band {{ position: absolute; top: -20%; left: 0; width: 22%; height: 140%;
        background: linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.32) 50%, rgba(255,255,255,0) 100%); }}
"""


def page(title, body, css, js, dur=5):
    return f"""<!doctype html>
<html lang="bn">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>{title}</title>
    <script src="assets/gsap.min.js"></script>
    <style>{BASE_CSS}{css}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="{W}" data-height="{H}" data-fps="30">
{body}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
{js}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


PHOTO_LAYERS = """      <div id="backdrop"><img src="assets/clock-bg.png" alt="" /></div>
      <div id="hero"><img src="assets/clock.png" alt="LED digital desk clock" />{extra}</div>
      <div id="vignette"></div>"""

CLIPS = {
    "clip2_pushin": (
        PHOTO_LAYERS.format(extra=""),
        "",
        f"""      tl.fromTo("#hero", {{ scale: 1, x: 0, y: 0 }}, {{ scale: {ZOOM}, x: {DX:.1f}, y: {DY:.1f}, duration: 5, ease: "sine.inOut" }}, 0);
      tl.fromTo("#backdrop", {{ scale: 1 }}, {{ scale: 1.12, duration: 5, ease: "sine.inOut" }}, 0);""",
    ),
    "clip3_orbit": (
        PHOTO_LAYERS.format(extra='<div id="sweep"><div id="band"></div></div>'),
        "",
        f"""      tl.fromTo("#hero", {{ scale: 1.5, x: {DX - 30:.1f}, y: {DY:.1f}, rotationY: -7, transformPerspective: 1800 }},
        {{ scale: 1.55, x: {DX + 30:.1f}, y: {DY:.1f}, rotationY: 7, transformPerspective: 1800, duration: 5, ease: "sine.inOut" }}, 0);
      tl.fromTo("#backdrop", {{ x: 40 }}, {{ x: -40, duration: 5, ease: "sine.inOut" }}, 0);
      tl.fromTo("#band", {{ x: -300 }}, {{ x: 1250, duration: 2.6, ease: "power1.inOut" }}, 1.1);""",
    ),
    "clip4_pullback": (
        PHOTO_LAYERS.format(extra=""),
        "",
        f"""      tl.fromTo("#hero", {{ scale: {ZOOM}, x: {DX:.1f}, y: {DY:.1f} }}, {{ scale: 1, x: 0, y: 0, duration: 5, ease: "sine.inOut" }}, 0);
      tl.fromTo("#backdrop", {{ scale: 1.12 }}, {{ scale: 1, duration: 5, ease: "sine.inOut" }}, 0);""",
    ),
}


def offer_clip(price):
    css = """
      @font-face { font-family: "Hind Siliguri"; font-weight: 600; src: url("assets/fonts/hind-siliguri-bengali-600-normal.woff2") format("woff2");
        unicode-range: U+0951-0952, U+0964-0965, U+0980-09FE, U+1CD0-1CF9, U+200C-200D, U+20B9, U+25CC, U+A8F1; }
      @font-face { font-family: "Hind Siliguri"; font-weight: 700; src: url("assets/fonts/hind-siliguri-bengali-700-normal.woff2") format("woff2");
        unicode-range: U+0951-0952, U+0964-0965, U+0980-09FE, U+1CD0-1CF9, U+200C-200D, U+20B9, U+25CC, U+A8F1; }
      @font-face { font-family: "Hind Siliguri"; font-weight: 600; src: url("assets/fonts/hind-siliguri-latin-600-normal.woff2") format("woff2"); }
      @font-face { font-family: "Hind Siliguri"; font-weight: 700; src: url("assets/fonts/hind-siliguri-latin-700-normal.woff2") format("woff2"); }""" + f"""
      #offer {{ position: absolute; left: 70px; right: 70px; top: {HERO_TOP + HERO_H - 120}px; display: flex; flex-direction: column;
        align-items: center; gap: 30px; text-align: center; font-family: "Hind Siliguri", sans-serif; }}
      #offer .price {{ font-size: 120px; font-weight: 700; color: #ffffff; line-height: 1.1; text-shadow: 0 6px 24px rgba(0,0,0,0.6); }}
      #offer .price b {{ color: #ffd43b; }}
      #offer .deliv {{ font-size: 54px; font-weight: 600; color: #ffffff; background: rgba(18, 140, 74, 0.92); border-radius: 999px; padding: 14px 44px; }}
      #offer .btn {{ margin-top: 20px; font-size: 56px; font-weight: 700; color: #15171c; background: #ffd43b; border-radius: 999px; padding: 28px 64px; }}
      #hero2 {{ position: absolute; left: 0; top: {HERO_TOP - 300}px; width: {W}px; height: {HERO_H}px; border-radius: 0; }}
"""
    body = f"""      <div id="backdrop"><img src="assets/clock-bg.png" alt="" /></div>
      <div id="hero2"><img src="assets/clock.png" alt="LED digital desk clock" /></div>
      <div id="vignette"></div>
      <div id="offer">
        <div class="price">মাত্র <b>৳{price}</b></div>
        <div class="deliv">ঢাকায় ডেলিভারি ফ্রি</div>
        <div class="btn">ইনবক্স করে অর্ডার করুন</div>
      </div>"""
    js = """      tl.fromTo("#hero2", { scale: 1.06, y: 0 }, { scale: 1, y: 0, duration: 5, ease: "sine.out" }, 0);
      tl.fromTo("#offer .price", { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.45, ease: "back.out(2)" }, 0.2);
      tl.fromTo("#offer .deliv", { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }, 0.6);
      tl.fromTo("#offer .btn", { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }, 0.9);
      tl.to("#offer .btn", { scale: 1.07, duration: 0.45, yoyo: true, repeat: 7, ease: "sine.inOut" }, 1.4);"""
    return body, css, js


def main():
    price = sys.argv[sys.argv.index("--price") + 1] if "--price" in sys.argv else "[X]"
    clips = dict(CLIPS)
    clips["clip6_offer"] = offer_clip(price)
    for name, (body, css, js) in clips.items():
        d = ROOT / "clips" / name
        (d / "assets").mkdir(parents=True, exist_ok=True)
        for f in ("gsap.min.js", "clock.png", "clock-bg.png"):
            shutil.copy(ROOT / "assets" / f, d / "assets" / f)
        for f in ("hyperframes.json", "package.json"):
            if (ROOT / f).exists():
                shutil.copy(ROOT / f, d / f)
        if name == "clip6_offer":
            shutil.copytree(ROOT / "assets" / "fonts", d / "assets" / "fonts", dirs_exist_ok=True)
        (d / "index.html").write_text(page(name, body, css, js))
        print("built", d)


if __name__ == "__main__":
    main()
