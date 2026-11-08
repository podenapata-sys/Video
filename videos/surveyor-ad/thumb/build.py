#!/usr/bin/env python3
"""KDSA surveyor ad covers: 9:16 (Reels), 1:1 (feed), 16:9 (YouTube / link preview).

  python3 thumb/build.py v|s|w   -> writes thumb/index.html, then snapshot it (see renders/)

Problem -> solution in one image: the boundary argument (scene 2) as the hero, the total-station shot (scene 5)
as a round "solution" inset. Bangla hook from the ad. 9:16 keeps hook + chip inside the centre 1080x1080
(profile-grid crop) and nothing in the bottom 15% / right 12% (Reels UI).
"""
import sys
from pathlib import Path

D = Path(__file__).parent
v = sys.argv[1] if len(sys.argv) > 1 else "v"
W, H = {"v": (1080, 1920), "s": (1080, 1080), "w": (1920, 1080)}[v]
NAVY, YEL = "#0B2545", "#FFC107"
logo = (D.parent / "assets" / "logo.png").exists()

CSS = f"""
@font-face {{ font-family:"Hind Siliguri"; src:url(fonts/hind-siliguri-bengali-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; unicode-range:U+0980-09FE,U+200C-200D,U+25CC; }}
@font-face {{ font-family:"Hind Siliguri"; src:url(fonts/hind-siliguri-latin-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; unicode-range:U+0000-00FF,U+2000-206F; }}
@font-face {{ font-family:"Montserrat"; src:url(fonts/montserrat-latin-800-normal.woff2) format("woff2"); font-weight:800; font-display:block; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:{NAVY}; }}
#root {{ position:relative; width:100%; height:100%; overflow:hidden; font-family:"Hind Siliguri", sans-serif; color:#fff; }}
.hero {{ position:absolute; object-fit:cover; filter:saturate(1.12) contrast(1.06); }}
.shade {{ position:absolute; inset:0; pointer-events:none; }}
.hook {{ position:absolute; font-weight:700; line-height:1.18; text-shadow:0 4px 20px rgba(0,0,0,.55); }}
.hook b {{ color:{YEL}; font-weight:700; }}
.chip {{ position:absolute; background:{YEL}; color:{NAVY}; font-weight:700; border-radius:999px; white-space:nowrap;
  box-shadow:0 12px 30px -10px rgba(0,0,0,.55); }}
.svc {{ position:absolute; font-family:"Montserrat", sans-serif; font-weight:800; letter-spacing:.08em; white-space:nowrap;
  text-shadow:0 3px 14px rgba(0,0,0,.6); }}
.inset {{ position:absolute; border-radius:50%; overflow:hidden; border:8px solid {YEL}; box-shadow:0 18px 44px -12px rgba(0,0,0,.65); }}
.inset img {{ width:100%; height:100%; object-fit:cover; object-position:46% 34%; transform:scale(1.55); transform-origin:42% 36%; }}
.tick {{ position:absolute; border-radius:50%; background:#1FB15A; color:#fff; display:flex; align-items:center; justify-content:center;
  font-family:"Montserrat"; font-weight:800; box-shadow:0 8px 20px -6px rgba(0,0,0,.6); }}
.org {{ position:absolute; font-weight:700; line-height:1.25; text-shadow:0 3px 14px rgba(0,0,0,.6); }}
.pill {{ position:absolute; display:flex; align-items:center; gap:14px; background:#fff; color:{NAVY}; border-radius:999px; white-space:nowrap;
  font-family:"Montserrat", sans-serif; font-weight:800; box-shadow:0 14px 34px -12px rgba(0,0,0,.6); }}
.pill svg {{ flex:none; }}
.logo {{ position:absolute; border-radius:50%; background:#fff; padding:6px; }}
.logo img {{ width:100%; height:100%; border-radius:50%; object-fit:contain; }}
"""


def pill(size, x, y, pad):
    ic = int(size * 1.05)
    return (f'<div class="pill" style="left:{x}px;top:{y}px;font-size:{size}px;padding:{pad}px {pad * 1.9:.0f}px">'
            f'<svg width="{ic}" height="{ic}" viewBox="0 0 24 24"><path fill="{NAVY}" d="M12 3C6.5 3 2 6.8 2 11.5c0 2.4 1.2 4.6 3.1 6.1'
            f'L4.4 21l3.9-1.9c1.2.4 2.4.6 3.7.6 5.5 0 10-3.8 10-8.5S17.5 3 12 3z"/><circle cx="8" cy="11.5" r="1.3" fill="#fff"/>'
            f'<circle cx="12" cy="11.5" r="1.3" fill="#fff"/><circle cx="16" cy="11.5" r="1.3" fill="#fff"/></svg>'
            f'<span>WhatsApp: 01911-888183</span></div>')


def inset(x, y, d):
    t = int(d * 0.26)
    return (f'<div class="inset" style="left:{x}px;top:{y}px;width:{d}px;height:{d}px"><img src="assets/hero_s5.jpg" alt="" /></div>'
            f'<div class="tick" style="left:{x + d - t * 0.9:.0f}px;top:{y + d - t * 1.05:.0f}px;width:{t}px;height:{t}px;font-size:{t * 0.6:.0f}px">✓</div>')


def logo_tag(x, y, d):
    return f'<div class="logo" style="left:{x}px;top:{y}px;width:{d}px;height:{d}px"><img src="assets/logo.png" alt="KDSA" /></div>' if logo else ""


HOOK = 'জমির সীমানা নিয়ে<br><b>বিরোধ?</b>'
if v == "v":
    org_x = 54 + (130 if logo else 0)
    body = f"""
<img class="hero" src="assets/hero_s2.jpg" style="left:0;top:0;width:{W}px;height:{H}px;object-position:50% 40%" alt="" />
<div class="shade" style="background:linear-gradient(180deg, rgba(11,37,69,.55) 0%, rgba(11,37,69,0) 24%, rgba(11,37,69,0) 30%,
  rgba(11,37,69,.78) 36%, rgba(11,37,69,.82) 52%, rgba(11,37,69,.15) 60%, rgba(11,37,69,.0) 64%, rgba(11,37,69,.86) 72%, {NAVY} 86%)"></div>
<div class="hook" style="left:54px;top:690px;width:900px;font-size:104px">{HOOK}</div>
<div class="chip" style="left:54px;top:1004px;font-size:44px;padding:14px 34px 10px">সঠিক পরিমাপ • পেশাদার সার্ভে</div>
{inset(600, 1060, 290)}
<div class="svc" style="left:54px;top:1104px;font-size:30px;line-height:1.5">LAND DEMARCATION<br><span style="color:#FFC107">PANTOGRAPH SERVICE</span></div>
{logo_tag(54, 1372, 110)}
<div class="org" style="left:{org_x}px;top:1376px;width:{900 - org_x}px;font-size:46px">খুলনা বিভাগীয় ডিজিটাল<br>সার্ভেয়ার এসোসিয়েশন</div>
{pill(40, 54, 1508, 18)}"""
elif v == "s":
    body = f"""
<img class="hero" src="assets/hero_s2.jpg" style="left:0;top:0;width:{W}px;height:{H}px;object-position:50% 34%" alt="" />
<div class="shade" style="background:linear-gradient(180deg, rgba(11,37,69,.9) 0%, rgba(11,37,69,.6) 24%, rgba(11,37,69,0) 40%,
  rgba(11,37,69,0) 60%, rgba(11,37,69,.88) 80%, {NAVY} 100%)"></div>
<div class="hook" style="left:48px;top:30px;width:620px;font-size:76px">{HOOK}</div>
<div class="chip" style="left:48px;top:232px;font-size:34px;padding:10px 26px 7px">সঠিক পরিমাপ • পেশাদার সার্ভে</div>
{inset(760, 36, 260)}
{logo_tag(48, 838, 96)}
<div class="org" style="left:{48 + (116 if logo else 0)}px;top:836px;font-size:36px">খুলনা বিভাগীয় ডিজিটাল সার্ভেয়ার এসোসিয়েশন</div>
<div class="svc" style="left:{48 + (116 if logo else 0)}px;top:892px;font-size:24px;color:{YEL}">LAND DEMARCATION • PANTOGRAPH</div>
{pill(32, 48, 952, 14)}"""
else:
    body = f"""
<img class="hero" src="assets/hero_s2.jpg" style="left:700px;top:0;width:1220px;height:{H}px;object-position:50% 30%" alt="" />
<div class="shade" style="background:linear-gradient(90deg, {NAVY} 0%, {NAVY} 36%, rgba(11,37,69,.6) 44%, rgba(11,37,69,0) 56%)"></div>
<div class="hook" style="left:80px;top:150px;width:820px;font-size:98px">{HOOK}</div>
<div class="chip" style="left:80px;top:430px;font-size:42px;padding:12px 32px 9px">সঠিক পরিমাপ • পেশাদার সার্ভে</div>
<div class="svc" style="left:80px;top:540px;font-size:32px;color:{YEL}">LAND DEMARCATION • PANTOGRAPH</div>
{logo_tag(80, 640, 110)}
<div class="org" style="left:{80 + (130 if logo else 0)}px;top:646px;font-size:46px">খুলনা বিভাগীয় ডিজিটাল<br>সার্ভেয়ার এসোসিয়েশন</div>
{pill(40, 80, 830, 18)}
{inset(1540, 640, 320)}"""

(D / "index.html").write_text(f"""<!doctype html><html lang="bn"><head><meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" /><title>KDSA cover</title><style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="1" data-width="{W}" data-height="{H}">{body}</div>
<script src="assets/gsap.min.js"></script>
<script>window.__timelines = window.__timelines || {{}}; window.__timelines["main"] = gsap.timeline({{ paused: true }});</script>
</body></html>""", encoding="utf-8")
print("built", v, W, H, "logo" if logo else "no logo")
