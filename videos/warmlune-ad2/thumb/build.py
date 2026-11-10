#!/usr/bin/env python3
"""WarmLune ad v2 covers: 9:16 (Reels), 1:1 (feed / grid), 16:9 (YouTube / link preview).

  python3 thumb/build.py v|s|w   -> writes thumb/index.html, then snapshot it into renders/

Problem -> solution: the hero is her smiling and lifting the belt (S3, 4.5 s); a round, desaturated "before"
inset shows the pain moment (S1, 4 s) with a red cross. No price (the ad pushes to the inbox).
"""
import sys
from pathlib import Path

D = Path(__file__).parent
v = sys.argv[1] if len(sys.argv) > 1 else "v"
W, H = {"v": (1080, 1920), "s": (1080, 1080), "w": (1920, 1080)}[v]
CORAL, GOLD, PLUM = "#E8446A", "#FFB347", "#3A0F22"

CSS = f"""
@font-face {{ font-family:"Noto Sans Bengali"; src:url(media/fonts/noto-bengali.woff2) format("woff2"); font-weight:400 800; font-display:block; }}
@font-face {{ font-family:"Noto Color Emoji"; src:url(media/fonts/NotoColorEmoji.ttf) format("truetype"); font-display:block; }}
@font-face {{ font-family:"Montserrat"; src:url(media/fonts/montserrat-latin-800-normal.woff2) format("woff2"); font-weight:800; font-display:block; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:{PLUM}; }}
#root {{ position:relative; width:100%; height:100%; overflow:hidden; color:#fff;
  font-family:"Noto Sans Bengali", "Noto Color Emoji", sans-serif; }}
.hero {{ position:absolute; object-fit:cover; filter:saturate(1.08) contrast(1.04); }}
.shade {{ position:absolute; inset:0; pointer-events:none; }}
.brand {{ position:absolute; font-family:"Montserrat", sans-serif; font-weight:800; letter-spacing:.24em; white-space:nowrap;
  text-shadow:0 0 18px rgba(255,190,90,.75), 0 2px 10px rgba(0,0,0,.45); }}
.brand sup {{ font-size:.38em; letter-spacing:0; vertical-align:1.5em; }}
.hook {{ position:absolute; font-weight:800; line-height:1.18; text-shadow:0 4px 18px rgba(0,0,0,.55);
  -webkit-text-stroke:5px rgba(40,6,20,.45); paint-order:stroke fill; }}
.hook .c {{ color:#FF8FAB; -webkit-text-stroke:5px rgba(40,6,20,.55); text-shadow:0 0 22px rgba(232,68,106,.55), 0 4px 14px rgba(0,0,0,.5); }}
.chips {{ position:absolute; display:flex; flex-wrap:wrap; gap:14px; }}
.chip {{ background:rgba(255,255,255,.94); color:{PLUM}; border-radius:999px; font-weight:800; white-space:nowrap;
  box-shadow:0 8px 22px -8px rgba(0,0,0,.5); }}
.cta {{ position:absolute; background:{CORAL}; color:#fff; border-radius:999px; font-weight:800; white-space:nowrap;
  box-shadow:0 0 0 4px rgba(255,255,255,.9), 0 16px 40px -10px rgba(0,0,0,.6); }}
.inset {{ position:absolute; border-radius:50%; overflow:hidden; border:7px solid #fff; box-shadow:0 14px 36px -10px rgba(0,0,0,.6); }}
.inset img {{ width:100%; height:100%; object-fit:cover; object-position:58% 30%; transform:scale(1.5); transform-origin:58% 30%;
  filter:grayscale(.75) brightness(.85); }}
.x {{ position:absolute; border-radius:50%; background:#FF4444; color:#fff; display:flex; align-items:center; justify-content:center;
  font-family:"Montserrat"; font-weight:800; box-shadow:0 6px 16px -4px rgba(0,0,0,.6); }}
.tag {{ position:absolute; font-weight:800; white-space:nowrap; text-shadow:0 2px 8px rgba(0,0,0,.7); }}
"""


def inset(x, y, d, label=True):
    t = int(d * 0.3)
    lab = (f'<div class="tag" style="left:{x}px;top:{y + d + 6}px;width:{d}px;text-align:center;font-size:{int(d * 0.14)}px">আগে</div>'
           if label else "")
    return (f'<div class="inset" style="left:{x}px;top:{y}px;width:{d}px;height:{d}px"><img src="media/thumb_pain.jpg" alt="" /></div>'
            f'<div class="x" style="left:{x + d - t * 0.85:.0f}px;top:{y - t * 0.1:.0f}px;width:{t}px;height:{t}px;font-size:{t * 0.62:.0f}px">✕</div>{lab}')


def chips(x, y, size, wrap_w):
    items = ["🔥 হিট + ম্যাসাজ", "🪶 তারবিহীন", "✅ ৭ দিন গ্যারান্টি"]
    inner = "".join(f'<span class="chip" style="font-size:{size}px;padding:{size * .28:.0f}px {size * .62:.0f}px {size * .2:.0f}px">{c}</span>' for c in items)
    return f'<div class="chips" style="left:{x}px;top:{y}px;width:{wrap_w}px">{inner}</div>'


HOOK = 'পিরিয়ডের ব্যথা?<br><span class="c">উষ্ণ আরাম ৩-৪ সেকেন্ডে</span>'
if v == "v":
    body = f"""
<img class="hero" src="media/thumb_hero.jpg" style="left:0;top:0;width:{W}px;height:{H}px;object-position:50% 50%" alt="" />
<div class="shade" style="background:linear-gradient(180deg, rgba(58,15,34,.55) 0%, rgba(58,15,34,0) 9%, rgba(58,15,34,0) 38%,
  rgba(58,15,34,.72) 42%, rgba(58,15,34,.72) 53%, rgba(58,15,34,0) 57%, rgba(58,15,34,0) 70%, rgba(58,15,34,.9) 76%, {PLUM} 92%)"></div>
<div class="brand" style="left:0;width:{W}px;text-align:center;text-indent:.24em;top:40px;font-size:54px">WARMLUNE<sup>™</sup></div>
{inset(40, 250, 230)}
<div class="hook" style="left:54px;top:800px;width:900px;font-size:86px">{HOOK}</div>
{chips(54, 1465, 36, 900)}
<div class="cta" style="left:54px;top:1560px;font-size:46px;padding:16px 44px 12px">💬 ইনবক্সে অর্ডার করুন</div>"""
elif v == "s":
    body = f"""
<img class="hero" src="media/thumb_hero.jpg" style="left:430px;top:-70px;width:650px;height:1156px;object-position:50% 50%" alt="" />
<div class="shade" style="background:linear-gradient(90deg, {PLUM} 0%, {PLUM} 38%, rgba(58,15,34,.55) 46%, rgba(58,15,34,0) 56%)"></div>
<div class="brand" style="left:48px;top:44px;font-size:40px">WARMLUNE<sup>™</sup></div>
<div class="hook" style="left:48px;top:140px;width:520px;font-size:64px">{HOOK}</div>
{chips(48, 470, 28, 470)}
{inset(52, 690, 190)}
<div class="cta" style="left:300px;top:780px;font-size:30px;padding:12px 26px 9px">💬 ইনবক্সে<br>অর্ডার করুন</div>"""
else:
    body = f"""
<img class="hero" src="media/thumb_hero.jpg" style="left:900px;top:-230px;width:1020px;height:1813px;object-position:50% 50%" alt="" />
<div class="shade" style="background:linear-gradient(90deg, {PLUM} 0%, {PLUM} 44%, rgba(58,15,34,.55) 50%, rgba(58,15,34,0) 58%)"></div>
<div class="brand" style="left:80px;top:80px;font-size:48px">WARMLUNE<sup>™</sup></div>
<div class="hook" style="left:80px;top:190px;width:840px;font-size:92px">{HOOK}</div>
{chips(80, 560, 34, 820)}
<div class="cta" style="left:80px;top:830px;font-size:44px;padding:16px 42px 12px">💬 ইনবক্সে অর্ডার করুন</div>
{inset(1690, 250, 200)}"""

(D / "index.html").write_text(f"""<!doctype html><html lang="bn"><head><meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" /><title>WarmLune cover</title><style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="1" data-width="{W}" data-height="{H}">{body}</div>
<script src="media/gsap.min.js"></script>
<script>window.__timelines = window.__timelines || {{}}; window.__timelines["main"] = gsap.timeline({{ paused: true }});</script>
</body></html>""", encoding="utf-8")
print("built", v, W, H)
