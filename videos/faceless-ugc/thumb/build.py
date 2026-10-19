#!/usr/bin/env python3
"""Shorts thumbnails (1080x1920) for the two Content Rewards videos.

  python3 thumb/build.py faceless|split   -> writes thumb/index.html, then snapshot it

Key text stays inside the centre 1080x1080 square, which is what the Shorts grid crops to.
Only real numbers from the screen recording are shown ($2.00 per 1K views).
"""
import sys
from pathlib import Path

D = Path(__file__).parent
v = sys.argv[1] if len(sys.argv) > 1 else "faceless"

CSS = """
@font-face { font-family: "Noto Color Emoji"; src: url("assets/fonts/NotoColorEmoji.ttf") format("truetype"); }
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:#0b0b0d; }
#root { position:relative; width:100%; height:100%; overflow:hidden; background:#0b0b0d; font-family:"Montserrat", "Noto Color Emoji", sans-serif; }
.head { position:absolute; left:50px; right:50px; text-align:center; color:#fff; font-weight:900; line-height:1.04;
  letter-spacing:-0.01em; text-shadow:0 6px 24px rgba(0,0,0,0.8); }
.head b { color:#ffcc33; }
.badge { position:absolute; background:#ffcc33; color:#111; font-weight:900; border-radius:22px; box-shadow:0 14px 34px rgba(0,0,0,0.5); }
.pill { position:absolute; left:50%; transform:translateX(-50%); background:#e3242b; color:#fff; font-size:50px; font-weight:800;
  padding:16px 44px 14px; border-radius:999px; white-space:nowrap; box-shadow:0 10px 26px rgba(0,0,0,0.5); }
"""

if v == "faceless":
    body = """
<div class="head" style="top:330px;font-size:92px;white-space:nowrap">THIS SITE <b>PAYS YOU</b><br>TO POST VIDEOS 👀</div>
<div id="card"><img src="assets/rates.png" alt="" /><i id="ring"></i></div>
<div class="badge" style="left:50%;top:1250px;font-size:84px;padding:18px 40px 12px;white-space:nowrap;transform:translateX(-50%) rotate(3deg)">$2 / 1K VIEWS</div>
<div class="pill" style="top:1560px">Comment LINK 👇</div>
"""
    CSS += """
#card { position:absolute; left:60px; top:760px; width:960px; transform:rotate(-3deg); border-radius:26px; overflow:hidden;
  box-shadow:0 24px 60px rgba(0,0,0,0.6); border:4px solid #fff; }
#card img { display:block; width:100%; }
#ring { position:absolute; left:2px; top:80px; width:200px; height:108px; border:7px solid #ffcc33; border-radius:18px; }
"""
else:
    body = """
<img id="face" src="assets/face.jpg" alt="" />
<img id="screen" src="assets/discover.jpg" alt="" />
<div id="band">Trying to make a <b>doctor salary</b><br>in 67 mins 🧑‍🍳</div>
<div class="badge" style="left:50%;top:880px;transform:translateX(-50%) rotate(-3deg);font-size:72px;padding:16px 36px 10px;white-space:nowrap">$2 / 1K VIEWS?</div>
<div class="pill" style="top:1560px">Comment LINK 👇</div>
"""
    CSS += """
#face { position:absolute; left:0; top:340px; width:100%; height:620px; object-fit:cover; object-position:50% 30%; }
#screen { position:absolute; left:0; top:960px; width:100%; height:960px; object-fit:cover; object-position:35% 50%; }
#band { position:absolute; left:0; top:0; width:100%; height:340px; background:#000; padding:150px 30px 0;
  text-align:center; color:#fff; font-size:54px; font-weight:900; line-height:1.12; white-space:nowrap; }
#band b { color:#ffcc33; }
"""

(D / "index.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" /><title>Thumbnail</title><style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="1" data-width="1080" data-height="1920">{body}</div>
<script src="assets/gsap.min.js"></script>
<script>window.__timelines = window.__timelines || {{}}; window.__timelines["main"] = gsap.timeline({{ paused: true }});</script>
</body></html>""")
print("built", v)
