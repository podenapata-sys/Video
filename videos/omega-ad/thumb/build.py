#!/usr/bin/env python3
"""Omega Dental ad covers: 9:16 (Reels), 16:9 (YouTube), 1:1 (feed).

  python3 thumb/build.py v|w|s   -> writes thumb/index.html, then snapshot it

Cover text from kit/copy.md ("ক্লিনিক আছে, ওয়েবসাইট নেই?") beside the phone mockup of 01-home-hero.png.
9:16 keeps the headline inside the centre 1080x1080 (the profile-grid crop) and the 9:16 safe zone.
"""
import sys
from pathlib import Path

D = Path(__file__).parent
v = sys.argv[1] if len(sys.argv) > 1 else "v"
W, H = {"v": (1080, 1920), "w": (1920, 1080), "s": (1080, 1080)}[v]

CSS = """
@font-face{font-family:"Noto Sans Bengali";src:url(fonts/noto-bengali.woff2) format("woff2");font-weight:400 800;font-display:block}
@font-face{font-family:"Sora";src:url(fonts/sora.woff2) format("woff2");font-weight:600 800;font-display:block}
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:%dpx; height:%dpx; overflow:hidden; background:#F4F8FA; }
#root { position:relative; width:100%%; height:100%%; overflow:hidden; font-family:"Noto Sans Bengali","Sora",sans-serif;
  background:radial-gradient(1200px 1000px at 72%% 62%%, #CDEFE7 0%%, #F4F8FA 62%%); }
.en { font-family:"Sora","Noto Sans Bengali",sans-serif; }
.head { position:absolute; font-weight:800; line-height:1.18; color:#13294E; }
.head .q { display:block; color:#F08A24; }
.tag { position:absolute; display:inline-flex; align-items:center; gap:14px; background:#13294E; color:#fff; border-radius:999px;
  font-weight:700; padding:14px 30px 12px; }
.tag i { width:16px; height:16px; border-radius:50%%; background:#57C3AD; display:block; }
.brand { position:absolute; font-weight:800; color:#2C8A78; letter-spacing:.5px; }
.ph { position:absolute; transform-origin:0 0; }
.phone { width:600px; aspect-ratio:1170/2532; border-radius:76px; padding:22px; background:#0E1B33; transform:rotate(4deg);
  box-shadow:0 60px 120px -40px rgba(19,41,78,.55), 0 0 0 3px #22345a inset; }
.phone .screen { width:100%%; height:100%%; border-radius:56px; overflow:hidden; background:#fff; }
.phone .screen img { width:100%%; display:block; }
""" % (W, H)

PH = '<div class="phone"><div class="screen"><img src="assets/screens/phone/01-home-hero.png" alt="" /></div></div>'
if v == "v":
    body = f"""
<div class="head" style="left:80px;top:430px;width:860px;font-size:104px">ক্লিনিক আছে,<span class="q">ওয়েবসাইট নেই?</span></div>
<div class="tag" style="left:80px;top:300px;font-size:38px"><i></i>ডেন্টাল ক্লিনিকের জন্য</div>
<div class="ph" style="left:270px;top:800px;transform:scale(1.0)">{PH}</div>
<div class="brand en" style="left:80px;top:700px;font-size:40px">Future Stack Solutions</div>"""
elif v == "w":
    body = f"""
<div class="tag" style="left:120px;top:250px;font-size:40px"><i></i>ডেন্টাল ক্লিনিকের জন্য</div>
<div class="head" style="left:120px;top:350px;width:1050px;font-size:130px">ক্লিনিক আছে,<span class="q">ওয়েবসাইট নেই?</span></div>
<div class="brand en" style="left:120px;top:800px;font-size:44px">Future Stack Solutions</div>
<div class="ph" style="left:1290px;top:110px;transform:scale(0.82)">{PH}</div>"""
else:
    body = f"""
<div class="tag" style="left:70px;top:250px;font-size:30px"><i></i>ডেন্টাল ক্লিনিকের জন্য</div>
<div class="head" style="left:70px;top:330px;width:560px;font-size:80px">ক্লিনিক আছে,<span class="q">ওয়েবসাইট নেই?</span></div>
<div class="brand en" style="left:70px;top:720px;font-size:32px">Future Stack Solutions</div>
<div class="ph" style="left:640px;top:120px;transform:scale(0.62)">{PH}</div>"""

(D / "index.html").write_text(f"""<!doctype html><html lang="bn"><head><meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" /><title>Omega cover</title><style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="1" data-width="{W}" data-height="{H}">{body}</div>
<script src="assets/gsap.min.js"></script>
<script>window.__timelines = window.__timelines || {{}}; window.__timelines["main"] = gsap.timeline({{ paused: true }});</script>
</body></html>""")
print("built", v, W, H)
