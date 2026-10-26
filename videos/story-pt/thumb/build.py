#!/usr/bin/env python3
"""Shorts / Reels covers (1080x1920) for "The 2:14 Text".

  python3 thumb/build.py phone|peep   -> writes thumb/index.html, then snapshot it

Key text stays inside the centre 1080x1080 square (y 420-1500), which is what the Shorts grid crops to,
and clear of the bottom 15% where the Shorts / Reels UI sits.
"""
import sys
from pathlib import Path

D = Path(__file__).parent
v = sys.argv[1] if len(sys.argv) > 1 else "phone"

CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:#000; }
#root { position:relative; width:100%; height:100%; overflow:hidden; background:#000; font-family:"Montserrat", sans-serif; }
.bg { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }
.shade { position:absolute; inset:0; }
.head { position:absolute; left:40px; right:40px; text-align:center; color:#fff; font-weight:900; line-height:1.0;
  -webkit-text-stroke:14px #000; paint-order:stroke fill; text-shadow:0 10px 34px rgba(0,0,0,0.9); }
.head b { color:#ffd23f; }
.head i { font-style:normal; color:#ff3b3b; }
.clock { position:absolute; left:0; right:0; text-align:center; font-family:"JetBrains Mono", monospace; font-weight:800; color:#ff3b3b;
  text-shadow:0 0 50px rgba(255,40,40,0.8), 0 8px 24px #000; }
.clock .am { font-size:0.4em; margin-left:18px; }
.pill { position:absolute; left:50%; transform:translateX(-50%); background:#e3242b; color:#fff; font-size:44px; font-weight:900;
  letter-spacing:0.06em; padding:14px 40px 12px; border-radius:999px; white-space:nowrap; box-shadow:0 10px 30px rgba(0,0,0,0.6); }
"""

if v == "phone":
    body = """
<img class="bg" src="assets/phone.jpg" alt="" />
<div class="shade" style="background:linear-gradient(180deg,rgba(0,0,0,0.85) 0%,rgba(0,0,0,0) 40%,rgba(0,0,0,0) 54%,rgba(0,0,0,0.9) 66%,#000 100%)"></div>
<div class="clock" style="top:430px;font-size:210px">2:14<span class="am">AM</span></div>
<div class="pill" style="top:700px">UNKNOWN NUMBER</div>
<div class="head" style="top:1170px;font-size:140px"><b>DON'T</b><br>OPEN IT</div>
"""
else:
    body = """
<img class="bg" src="assets/peep.jpg" alt="" style="top:-170px" />
<div class="shade" style="background:linear-gradient(180deg,rgba(0,0,0,0) 50%,rgba(0,0,0,0.9) 61%,#000 100%)"></div>
<div class="head" style="top:1180px;font-size:140px">NEVER SAY<br><i>YES</i></div>
"""

(D / "index.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" /><title>Thumbnail</title><style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="1" data-width="1080" data-height="1920">{body}</div>
<script src="assets/gsap.min.js"></script>
<script>window.__timelines = window.__timelines || {{}}; window.__timelines["main"] = gsap.timeline({{ paused: true }});</script>
</body></html>""")
print("built", v)
