#!/usr/bin/env python3
"""করিম চাচার সাইকেল -> index.html (HyperFrames 0.9.23: data-start/data-duration/data-media-start, class="clip",
one paused GSAP timeline on window.__timelines["main"], set/to/fromTo, seeded/deterministic values)."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "build"
TL = json.loads((B / "timeline.json").read_text(encoding="utf-8"))
S = {s["n"]: s for s in TL["slots"]}
SP = TL["spans"]
TOTAL, END = TL["total"], TL["end_card"]
GOLD = "#F2C46B"
T = lambda x: f"{x:.3f}"
html, js = [], []


def gold(text, words=("সাইকেল",)):
    for w in words:
        text = text.replace(w, f"<b>{w}</b>")
    return text


# ------------------------------------------------------------------ clips + transitions
for n in range(1, 7):
    s = S[n]
    html.append(f'<div class="shot" id="sh{n}" style="z-index:{n}"><div class="mv" id="mv{n}" data-layout-allow-overflow><video id="v{n}" class="clip" '
                f'src="build/c{n}.mp4" muted playsinline data-start="{T(s["clip_start"])}" data-duration="{T(s["clip_dur"])}" data-media-start="0" '
                f'data-track-index="{n}"></video></div></div>')
    if n in (1, 3, 4, 5):      # slow Ken Burns push-in
        js.append(f'tl.fromTo("#mv{n}", {{scale:1.0}}, {{scale:1.05, duration:{T(s["clip_dur"])}, ease:"none", immediateRender:false}}, {T(s["clip_start"])});')
    elif n == 6:               # gentle pull-out
        js.append(f'tl.fromTo("#mv6", {{scale:1.07}}, {{scale:1.0, duration:{T(s["clip_dur"])}, ease:"sine.out", immediateRender:false}}, {T(s["clip_start"])});')
js.append('tl.set("#sh1", {opacity:1}, 0);')
js.append('tl.fromTo("#black", {opacity:1}, {opacity:0, duration:0.5, ease:"power1.out", immediateRender:false}, 0);')
for n in (2, 3, 5, 6):         # 0.5 s crossfades centred on the cut
    t = S[n]["start"]
    js.append(f'tl.fromTo("#sh{n}", {{opacity:0}}, {{opacity:1, duration:0.5, ease:"sine.inOut", immediateRender:false}}, {T(t - 0.25)});')
    js.append(f'tl.set("#sh{n - 1}", {{opacity:0}}, {T(t + 0.25)});')
# soft dip to black 3 -> 4 (0.6 s gap)
t3, t4 = S[3]["end"], S[4]["start"]
js.append(f'tl.fromTo("#dip", {{opacity:0}}, {{opacity:1, duration:0.3, ease:"power1.in", immediateRender:false}}, {T(t3 - 0.3)});')
js.append(f'tl.set("#sh3", {{opacity:0}}, {T(t3)}); tl.set("#sh4", {{opacity:1}}, {T(t4)});')
js.append(f'tl.fromTo("#dip", {{opacity:1}}, {{opacity:0, duration:0.3, ease:"power1.out", immediateRender:false}}, {T(t4)});')

# ------------------------------------------------------------------ dust particles on clips 1, 2, 3, 6 (seeded, slow drift)
def lcg(seed):
    while True:
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        yield seed / 0x7FFFFFFF


for n in (1, 2, 3, 6):
    s = S[n]
    r = lcg(97 + n)
    dots = []
    for k in range(38):
        x, y, sz, o = 40 + next(r) * 1000, 120 + next(r) * 1500, 3 + next(r) * 6, 0.25 + next(r) * 0.4
        dots.append(f'<i class="dust" id="dt{n}_{k}" style="left:{x:.0f}px;top:{y:.0f}px;width:{sz:.1f}px;height:{sz:.1f}px;opacity:{o:.2f}"></i>')
        dx, dy = (next(r) - 0.5) * 120, -(40 + next(r) * 140)
        js.append(f'tl.fromTo("#dt{n}_{k}", {{x:0, y:0}}, {{x:{dx:.0f}, y:{dy:.0f}, duration:{T(s["end"] - s["start"] + 0.5)}, ease:"sine.inOut", immediateRender:false}}, {T(max(0.0, s["start"] - 0.25))});')
    html.append(f'<div class="dustwrap" id="dw{n}">{"".join(dots)}</div>')
    js.append(f'tl.fromTo("#dw{n}", {{opacity:0}}, {{opacity:1, duration:0.6, immediateRender:false}}, {T(max(0, s["start"] - 0.25))});')
    js.append(f'tl.to("#dw{n}", {{opacity:0, duration:0.5}}, {T(s["end"] - 0.25)});')

# ------------------------------------------------------------------ letter card (clips 4 and 5), lines revealed with Tanvir's voice
lines = TL["letter"]
for slot, key in ((4, "t1"), (5, "t2")):
    ls = [l for l in lines if l["line"] == key]
    body = "".join(f'<p class="ll" id="ll{slot}_{i}">{l["text"]}</p>' for i, l in enumerate(ls))
    html.append(f'<div class="letter" id="lt{slot}"><div class="paper"></div><div class="ltxt">{body}</div></div>')
    a, b = SP[key]
    js.append(f'tl.fromTo("#lt{slot}", {{autoAlpha:0, y:40}}, {{autoAlpha:1, y:0, duration:0.6, ease:"power2.out"}}, {T(a - 0.35)});')
    for i, l in enumerate(ls):
        js.append(f'tl.fromTo("#ll{slot}_{i}", {{autoAlpha:0, y:14, clipPath:"inset(0% 100% 0% 0%)"}}, {{autoAlpha:1, y:0, clipPath:"inset(0% 0% 0% 0%)", duration:0.9, ease:"power1.out"}}, {T(l["start"])});')
    end = (S[4]["end"] - 0.3) if slot == 4 else (SP["n5"][0] - 0.35)
    js.append(f'tl.to("#lt{slot}", {{autoAlpha:0, duration:0.4}}, {T(end)});')
html.append('<div id="label">ছেলের চিঠি</div>')
js.append(f'tl.fromTo("#label", {{autoAlpha:0, y:10}}, {{autoAlpha:1, y:0, duration:0.5}}, {T(SP["t1"][0] - 0.35)});')
js.append(f'tl.to("#label", {{autoAlpha:0, duration:0.2}}, {T(S[4]["end"] - 0.3)});')
js.append(f'tl.to("#label", {{autoAlpha:1, duration:0.4}}, {T(SP["t2"][0] - 0.35)});')
js.append(f'tl.to("#label", {{autoAlpha:0, duration:0.4}}, {T(SP["n5"][0] - 0.35)});')

# ------------------------------------------------------------------ narrator captions
for i, c in enumerate(TL["captions"]):
    html.append(f'<div class="cap" id="cp{i}"><span>{gold(c["text"])}</span></div>')
    js.append(f'tl.fromTo("#cp{i}", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.2, ease:"none"}}, {T(c["start"] - 0.05)});')
    js.append(f'tl.to("#cp{i}", {{autoAlpha:0, duration:0.2, ease:"none"}}, {T(min(c["end"], END) - 0.2)});')

# ------------------------------------------------------------------ grain, end card
k = 0
while k / 12 < TOTAL:
    js.append(f'tl.set("#grain", {{backgroundPosition:"{(k * 211) % 640}px {(k * 367) % 640}px"}}, {T(k / 12)});')
    k += 1
html.append('<div id="dark"></div><div id="endtxt">আপনার বাবার সাথে শেষ কবে <b>এক কাপ চা</b> খেয়েছেন?<small>মা-বাবার জন্য সময় রাখুন</small></div>')
js.append(f'tl.fromTo("#dark", {{opacity:0}}, {{opacity:0.58, duration:0.45, ease:"power1.out", immediateRender:false}}, {T(END)});')
js.append(f'tl.fromTo("#endtxt", {{autoAlpha:0, y:16}}, {{autoAlpha:1, y:0, duration:0.4, ease:"power2.out"}}, {T(END + 0.1)});')
js.append(f'tl.fromTo("#black", {{opacity:0}}, {{opacity:1, duration:0.4, ease:"power1.in", immediateRender:false}}, {T(TOTAL - 0.4)});')

FONTS = "".join(f'@font-face {{ font-family:"Hind Siliguri"; src:url(fonts/hind-siliguri-{sub}-{w}-normal.woff2) format("woff2"); font-weight:{w}; font-display:block; '
                f'unicode-range:{"U+0964-0965,U+0980-09FE,U+200C-200D,U+25CC" if sub == "bengali" else "U+0000-00FF,U+2000-206F"}; }}\n'
                for w in (600, 700) for sub in ("bengali", "latin")) + \
    '@font-face { font-family:"Galada"; src:url(fonts/galada-bengali-400-normal.woff2) format("woff2"); font-weight:400; font-display:block; unicode-range:U+0964-0965,U+0980-09FE,U+200C-200D,U+25CC; }\n' + \
    '@font-face { font-family:"Atma"; src:url(fonts/atma-bengali-600-normal.woff2) format("woff2"); font-weight:600; font-display:block; unicode-range:U+0964-0965,U+0980-09FE,U+200C-200D,U+25CC; }\n'
CSS = FONTS + f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#000; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#000; font-family:"Hind Siliguri", sans-serif; color:#fff; }}
.shot {{ position:absolute; inset:0; opacity:0; overflow:hidden; }}
.mv {{ position:absolute; inset:0; }}
.mv video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; filter:sepia(.18) saturate(1.08) contrast(.94) brightness(1.02); }}
#amber {{ position:absolute; inset:0; z-index:10; pointer-events:none; background:#E8A85A; mix-blend-mode:soft-light; opacity:.38; }}
#lift {{ position:absolute; inset:0; z-index:11; pointer-events:none; background:#2A1E14; mix-blend-mode:screen; opacity:.32; }}
#vig {{ position:absolute; inset:0; z-index:12; pointer-events:none; background:radial-gradient(ellipse 80% 66% at 50% 47%, rgba(0,0,0,0) 56%, rgba(20,10,0,.5) 100%); }}
#grain {{ position:absolute; inset:0; z-index:13; pointer-events:none; background:url(build/grain.png); background-size:640px 640px; opacity:.07; mix-blend-mode:overlay; }}
.dustwrap {{ position:absolute; inset:0; z-index:14; pointer-events:none; opacity:0; }}
.dust {{ position:absolute; border-radius:50%; background:rgba(255,224,168,.9); box-shadow:0 0 6px 2px rgba(255,206,130,.45); }}
.letter {{ position:absolute; left:70px; width:940px; top:1030px; z-index:30; visibility:hidden; padding:44px 50px 36px; }}
.paper {{ position:absolute; inset:0; border-radius:10px; opacity:.75;
  background:radial-gradient(ellipse at 50% 40%, rgba(255,250,236,1) 0%, rgba(243,229,200,1) 60%, rgba(214,190,150,1) 100%),
    repeating-linear-gradient(8deg, rgba(150,120,80,.06) 0 2px, rgba(0,0,0,0) 2px 7px);
  background-blend-mode:multiply; box-shadow:0 20px 50px -14px rgba(0,0,0,.65), inset 0 0 40px rgba(150,110,60,.35); }}
.ltxt {{ position:relative; }}
.ll {{ font-family:"Galada","Atma","Hind Siliguri",cursive; font-size:54px; line-height:1.45; color:#3A2614; visibility:hidden; margin-bottom:10px; }}
#label {{ position:absolute; left:70px; top:960px; z-index:31; visibility:hidden; font-weight:700; font-size:40px; color:{GOLD};
  text-shadow:0 2px 10px rgba(0,0,0,.8); padding:4px 18px 0; border-left:5px solid {GOLD}; }}
.cap {{ position:absolute; left:90px; width:900px; bottom:260px; z-index:40; text-align:center; visibility:hidden; }}
.cap span {{ display:inline-block; font-weight:700; font-size:58px; line-height:1.4; color:#fff; text-shadow:0 2px 8px rgba(0,0,0,.75), 0 6px 26px rgba(0,0,0,.55); }}
.cap b, #endtxt b {{ color:{GOLD}; font-weight:700; }}
#dark {{ position:absolute; inset:0; z-index:44; background:#000; opacity:0; }}
#endtxt {{ position:absolute; left:90px; width:900px; top:50%; translate:0 -50%; z-index:45; text-align:center; visibility:hidden; font-size:70px; font-weight:700; line-height:1.35;
  text-shadow:0 4px 24px rgba(0,0,0,.6); }}
#endtxt small {{ display:block; margin-top:28px; font-size:38px; font-weight:600; opacity:.6; }}
#black {{ position:absolute; inset:0; z-index:60; background:#000; opacity:1; pointer-events:none; }}
#dip {{ position:absolute; inset:0; z-index:59; background:#000; opacity:0; pointer-events:none; }}
"""
shots = [h for h in html if h.startswith('<div class="shot"')]
rest = [h for h in html if h not in shots]
page = f"""<!doctype html>
<html lang="bn" data-resolution="portrait"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<title>করিম চাচার সাইকেল</title><style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="1080" data-height="1920">
{chr(10).join(shots)}
<div id="amber"></div><div id="lift"></div><div id="vig"></div><div id="grain"></div>
{chr(10).join(rest)}
<div id="dip"></div><div id="black"></div>
<audio id="mix" src="build/mix.wav" data-start="0" data-duration="{TOTAL:.3f}" data-track-index="20"></audio>
</div>
<script src="media/gsap.min.js"></script>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["main"] = tl;
</script>
</body></html>
"""
(ROOT / "index.html").write_text(page, encoding="utf-8")
print(f"built index.html {TOTAL}s, {len(TL['captions'])} captions, {len(lines)} letter lines")
