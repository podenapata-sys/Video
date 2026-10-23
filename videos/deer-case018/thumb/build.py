#!/usr/bin/env python3
"""YouTube thumbnails (1920x1080) for Case 018.

  python3 thumb/build.py eyes|head   -> writes thumb/index.html, then snapshot it

Text stays out of the bottom-right corner, where YouTube draws the duration badge.
The source images carry a "CASE 018" HUD strip along the top; it is cropped off.
"""
import sys
from pathlib import Path

D = Path(__file__).parent
v = sys.argv[1] if len(sys.argv) > 1 else "eyes"

CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1920px; height:1080px; overflow:hidden; background:#000; }
#root { position:relative; width:100%; height:100%; overflow:hidden; background:#000; font-family:"League Gothic", sans-serif; }
.bg { position:absolute; display:block; }
.shade { position:absolute; inset:0; }
.txt { position:absolute; color:#fff; text-transform:uppercase; line-height:0.92; letter-spacing:0.01em;
  -webkit-text-stroke:6px #000; paint-order:stroke fill; text-shadow:0 10px 40px rgba(0,0,0,0.9); }
.txt b { color:#ffd23f; font-weight:400; }
.stamp { position:absolute; left:60px; top:54px; padding:10px 26px 4px; border:7px solid #e3242b; color:#e3242b;
  font-size:84px; letter-spacing:0.06em; transform:rotate(-5deg); background:rgba(0,0,0,0.55); }
.clock { position:absolute; top:60px; right:60px; padding:12px 30px 10px; background:#e3242b; color:#fff;
  font-family:"JetBrains Mono", monospace; font-weight:700; font-size:64px; border-radius:14px;
  box-shadow:0 12px 34px rgba(0,0,0,0.6); }
.clock i { display:inline-block; width:22px; height:22px; border-radius:50%; background:#fff; margin-right:18px; vertical-align:8px; }
"""

if v == "eyes":
    body = """
<img class="bg" src="assets/eyes.jpg" alt="" style="left:-90px;top:-170px;width:2100px;height:1172px" />
<div class="shade" style="background:linear-gradient(180deg,rgba(0,0,0,0) 45%,rgba(0,0,0,0.85) 68%,#000 82%)"></div>
<div class="stamp">CASE 018</div>
<div class="clock"><i></i>3:00 AM</div>
<div class="txt" style="left:70px;top:640px;font-size:150px">If you see this deer&hellip;</div>
<div class="txt" style="left:70px;top:790px;font-size:250px"><b>Don't</b> open the door</div>
"""
else:
    body = """
<img class="bg" src="assets/head.jpg" alt="" style="left:420px;top:-150px;width:2100px;height:1172px" />
<div class="shade" style="background:linear-gradient(90deg,#000 22%,rgba(0,0,0,0.6) 42%,rgba(0,0,0,0) 60%)"></div>
<div class="shade" style="background:linear-gradient(180deg,rgba(0,0,0,0) 55%,#000 75%)"></div>
<div class="stamp">CASE 018</div>
<div class="clock" style="left:70px;right:auto;top:auto;bottom:70px"><i></i>3:00 AM</div>
<div class="txt" style="left:70px;top:200px;font-size:250px">That's<br>not a<br><b>deer.</b></div>
"""

(D / "index.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="UTF-8" />
<meta name="viewport" content="width=1920, height=1080" /><title>Thumbnail</title><style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="1" data-width="1920" data-height="1080">{body}</div>
<script src="assets/gsap.min.js"></script>
<script>window.__timelines = window.__timelines || {{}}; window.__timelines["main"] = gsap.timeline({{ paused: true }});</script>
</body></html>""")
print("built", v)
