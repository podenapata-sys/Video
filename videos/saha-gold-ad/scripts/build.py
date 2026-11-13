#!/usr/bin/env python3
"""SaHa GoLD ad -> index.html (HyperFrames, 1080x1920, 30 s). Beat map from the client brief; times from timeline.json
(beats follow the voice) and words.json (overlays land on the spoken word; fallback = the brief's offset in the beat)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "timeline.json").read_text())
B = {b["n"]: b for b in TL["beats"]}
WORDS = json.loads((ROOT / "words.json").read_text(encoding="utf-8")) if (ROOT / "words.json").exists() else []
TOTAL = TL["total"]
GOLD, YELLOW, WA_,   RED, WATER = "#F2C14E", "#FFD60A", "#25D366", "#E63946", "#3FA9F5"
html, js = [], []


def w(beat, prefix, fallback):
    """Start of the first word in a beat starting with prefix (whisper); else beat start + fallback offset."""
    for x in WORDS:
        if x["beat"] == beat and x["text"].startswith(prefix):
            return x["start"]
    return B[beat]["start"] + fallback


def T(x):
    return f"{x:.3f}"


# ------------------------------------------------------------------ shots (one wrapper per beat, later beats on top)
for n in range(1, 7):
    b = B[n]
    t0 = max(0.0, b["clip_t"])
    ms = t0 - b["clip_t"]
    html.append(f'<div class="shot" id="sh{n}" style="z-index:{n}"><div class="mv" id="mv{n}">'
                f'<video id="v{n}" class="clip" src="media/b{n}.mp4" muted playsinline data-start="{T(t0)}" '
                f'data-duration="{T(min(b["clip_t"] + b["clip_dur"], TOTAL) - t0)}" data-media-start="{T(ms)}" data-track-index="{n}"></video></div></div>')

b1, b2, b3, b4, b5, b6 = (B[n] for n in range(1, 7))
# entries / transitions
js.append('tl.set("#sh1", {autoAlpha:1}, 0.5);')   # 0-0.5 s: black (root bg)
# B1 -> B2: whip pan right (0.3 s) -- picture travels left, motion blur
t = b2["start"]
js.append(f'tl.set("#sh2", {{autoAlpha:1, x:1080}}, {T(t - 0.15)});')
js.append(f'tl.to("#sh1", {{x:-1080, filter:"blur(36px)", duration:0.3, ease:"power2.in"}}, {T(t - 0.15)});')
js.append(f'tl.fromTo("#sh2", {{x:1080, filter:"blur(36px)"}}, {{x:0, filter:"blur(0px)", duration:0.3, ease:"power2.out", immediateRender:false}}, {T(t - 0.15)});')
js.append(f'tl.set("#sh1", {{autoAlpha:0}}, {T(t + 0.16)});')
# B2 -> B3: cross dissolve 0.5 s
t = b3["start"]
js.append(f'tl.fromTo("#sh3", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.5, ease:"none"}}, {T(t - 0.25)});')
js.append(f'tl.set("#sh2", {{autoAlpha:0}}, {T(t + 0.26)});')
# B3 -> B4: hard cut on the beat
t = b4["start"]
js.append(f'tl.set("#sh4", {{autoAlpha:1}}, {T(t)}); tl.set("#sh3", {{autoAlpha:0}}, {T(t)});')
# B4 -> B5: whip pan left (0.3 s)
t = b5["start"]
js.append(f'tl.set("#sh5", {{autoAlpha:1, x:-1080}}, {T(t - 0.15)});')
js.append(f'tl.to("#sh4", {{x:1080, filter:"blur(36px)", duration:0.3, ease:"power2.in"}}, {T(t - 0.15)});')
js.append(f'tl.fromTo("#sh5", {{x:-1080, filter:"blur(36px)"}}, {{x:0, filter:"blur(0px)", duration:0.3, ease:"power2.out", immediateRender:false}}, {T(t - 0.15)});')
js.append(f'tl.set("#sh4", {{autoAlpha:0}}, {T(t + 0.16)});')
# B5 -> B6: fade to black 0.5 s
t = b6["start"]
js.append(f'tl.fromTo("#fade", {{opacity:0}}, {{opacity:1, duration:0.25, ease:"power1.in"}}, {T(t - 0.25)});')
js.append(f'tl.set("#sh6", {{autoAlpha:1}}, {T(t)}); tl.set("#sh5", {{autoAlpha:0}}, {T(t)});')
js.append(f'tl.to("#fade", {{opacity:0, duration:0.25, ease:"power1.out"}}, {T(t)});')

# camera moves (on the inner .mv so they never fight the transition x/blur on .shot)
js.append(f'tl.fromTo("#mv1", {{scale:1.0}}, {{scale:1.07, duration:{T(b1["end"] + 0.2)}, ease:"none"}}, 0);')
js.append(f'tl.fromTo("#mv2", {{scale:1.05, rotation:-1.2, x:-24}}, {{scale:1.09, rotation:1.2, x:24, duration:{T(b2["end"] - b2["start"] + 0.6)}, ease:"sine.inOut"}}, {T(b2["start"] - 0.2)});')
js.append(f'tl.fromTo("#mv3", {{scale:1.0}}, {{scale:1.06, duration:{T(b3["end"] - b3["start"] + 0.4)}, ease:"none"}}, {T(b3["start"] - 0.25)});')
js.append(f'tl.fromTo("#mv4", {{scale:1.0}}, {{scale:1.04, duration:{T(b4["end"] - b4["start"] + 0.2)}, ease:"none"}}, {T(b4["start"])});')
js.append(f'tl.fromTo("#mv5", {{scale:1.0}}, {{scale:1.03, duration:{T(b5["end"] - b5["start"] + 0.2)}, ease:"none"}}, {T(b5["start"] - 0.15)});')
js.append(f'tl.fromTo("#mv6", {{scale:1.14, y:-110}}, {{scale:1.0, y:-110, duration:{T(TOTAL - b6["start"])}, ease:"sine.out"}}, {T(b6["start"])});')

# ------------------------------------------------------------------ BEAT 1: black 0.5 s, flash + shake + bass hit, "বিদ্যুৎ নেই?"
html.append('<div id="flash"></div>')
js.append('tl.fromTo("#flash", {opacity:0.95}, {opacity:0, duration:0.22, ease:"power2.out", immediateRender:false}, 0.5);')
for k, (dx, dy) in enumerate([(9, -6), (-8, 7), (6, 5), (-5, -4), (3, 2), (0, 0)]):
    js.append(f'tl.set("#stage", {{x:{dx}, y:{dy}}}, {T(0.5 + k * 0.04)});')
html.append('<div class="ov big" id="t1">বিদ্যুৎ নেই?</div>')
js.append('tl.fromTo("#t1", {autoAlpha:0, scale:1.45}, {autoAlpha:1, scale:1, duration:0.22, ease:"power4.out"}, 0.5);')
js.append('tl.to("#t1", {autoAlpha:0, scale:0.96, duration:0.35, ease:"power1.in"}, 2.72);')

# ------------------------------------------------------------------ BEAT 2: SaHa GoLD + ১২V ব্যাটারিচালিত
t_brand = w(2, "সাহা", 0.9)
t_12v = w(2, "বারো", 2.4)
html.append('<div class="ov" id="brand"><div class="gold">SaHa GoLD</div><div class="sub12" id="t12v">১২V ব্যাটারিচালিত</div></div>')
js.append(f'tl.fromTo("#brand", {{autoAlpha:0, y:20}}, {{autoAlpha:1, y:0, duration:0.6, ease:"power2.out"}}, {T(t_brand)});')
js.append(f'tl.fromTo("#brand .gold", {{textShadow:"0 0 0px rgba(242,193,78,0)"}}, {{textShadow:"0 0 46px rgba(242,193,78,.85)", duration:0.8, yoyo:true, repeat:1, ease:"sine.inOut"}}, {T(t_brand)});')
js.append(f'tl.fromTo("#t12v", {{autoAlpha:0, y:16}}, {{autoAlpha:1, y:0, duration:0.35, ease:"power2.out"}}, {T(t_12v)});')
js.append(f'tl.to("#brand", {{autoAlpha:0, duration:0.3}}, {T(b2["end"] - 0.15)});')

# ------------------------------------------------------------------ BEAT 3: features, stacked on the left, each on its word
t_cu = w(3, "তামার", 0.3)
t_ss = w(3, "স্টেইনলেস", 1.3)
t_sz = w(3, "এক", 2.8)
html.append('''<div class="ov chip goldtxt" id="f1">তামার কয়েল</div>
<svg id="arrow" viewBox="0 0 400 260"><defs><marker id="ah" markerWidth="10" markerHeight="10" refX="6" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#F2C14E"/></marker></defs>
<path id="apath" d="M20,30 C170,20 290,80 360,215" fill="none" stroke="#F2C14E" stroke-width="10" stroke-linecap="round" marker-end="url(#ah)"/></svg>
<div class="ov chip" id="f2">স্টেইনলেস বডি</div>
<div class="ov chip sizes" id="f3">১″ ও ২″ সাইজ</div>''')
js.append(f'tl.fromTo("#f1", {{autoAlpha:0, x:-60}}, {{autoAlpha:1, x:0, duration:0.3, ease:"power3.out"}}, {T(t_cu)});')
js.append(f'tl.fromTo("#apath", {{strokeDasharray:520, strokeDashoffset:520}}, {{strokeDashoffset:0, duration:0.45, ease:"power2.out"}}, {T(t_cu + 0.15)});')
js.append(f'tl.fromTo("#arrow", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.1}}, {T(t_cu + 0.15)});')
js.append(f'tl.fromTo("#f2", {{autoAlpha:0, x:-60}}, {{autoAlpha:1, x:0, duration:0.3, ease:"power3.out"}}, {T(t_ss)});')
js.append(f'tl.fromTo("#f3", {{autoAlpha:0, y:40}}, {{autoAlpha:1, y:0, duration:0.3, ease:"back.out(2)"}}, {T(t_sz)});')
js.append(f'tl.set("#f1, #f2, #f3, #arrow", {{autoAlpha:0}}, {T(b3["end"])});')

# ------------------------------------------------------------------ BEAT 4: ৩টি ক্যাপ ফ্রি! + FREE badge
t_free = w(4, "ফ্রি", 2.2)
html.append('<div class="ov offer" id="caps">৩টি ক্যাপ ফ্রি!</div><div id="badge"><span>FREE</span></div>')
js.append(f'tl.fromTo("#caps", {{autoAlpha:0, scale:1.8}}, {{autoAlpha:1, scale:1, duration:0.28, ease:"back.out(2.4)"}}, {T(t_free)});')
js.append(f'tl.fromTo("#badge", {{autoAlpha:0, x:260, rotation:200}}, {{autoAlpha:1, x:0, rotation:14, duration:0.45, ease:"back.out(1.6)"}}, {T(t_free + 0.5)});')
js.append(f'tl.to("#caps, #badge", {{autoAlpha:0, duration:0.15}}, {T(b4["end"] - 0.15)});')

# ------------------------------------------------------------------ BEAT 5: money shot, minimal text
t_nopower = w(5, "বিদ্যুৎ", 2.4)
html.append(f'''<div class="ov water" id="w5"><svg viewBox="0 0 24 32" width="64" height="86"><path d="M12 1C8 9 3 15 3 21a9 9 0 0 0 18 0c0-6-5-12-9-20z" fill="{WATER}"/>
<path d="M8 22a4 4 0 0 0 4 4" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round"/></svg><span>বিদ্যুৎ ছাড়াই সেচ!</span></div>''')
js.append(f'tl.fromTo("#w5", {{autoAlpha:0, y:40}}, {{autoAlpha:1, y:0, duration:0.4, ease:"power3.out"}}, {T(t_nopower)});')
js.append(f'tl.to("#w5", {{autoAlpha:0, duration:0.2}}, {T(b5["end"] - 0.25)});')

# ------------------------------------------------------------------ BEAT 6: end card / CTA
wa_svg = ('<svg viewBox="0 0 24 24" width="62" height="62"><path fill="#fff" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm5.3 14.1c-.2.6-1.3 '
          '1.2-1.8 1.2-.5.1-1 .2-3.3-.7-2.8-1.1-4.6-4-4.7-4.2-.1-.2-1.1-1.5-1.1-2.9s.7-2 1-2.3c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.4 0 .5l-.3.5-.4.4c-.1.1-.3.3-.1.6.2.3.7 '
          '1.2 1.6 1.9 1.1 1 2 1.3 2.3 1.4.3.1.5.1.6-.1l.9-1c.2-.3.4-.2.6-.1l1.9.9c.3.1.5.2.5.3.1.2.1.8-.1 1.4z"/></svg>')
html.append(f'''<div class="ov" id="order">অর্ডার করুন</div>
<div class="ov offer adv" id="adv">মাত্র ৳২০০ অ্যাডভান্স</div>
<div id="wabar">{wa_svg}<span>01711-054645</span></div>
<div class="ov" id="shop">Vaitoo Online Bazar</div>
<div id="vig"></div>''')
js.append(f'tl.fromTo("#order", {{autoAlpha:0, y:-20}}, {{autoAlpha:1, y:0, duration:0.5, ease:"power2.out"}}, 23.5);')
js.append('tl.fromTo("#adv", {autoAlpha:0, scale:1.6}, {autoAlpha:1, scale:1, duration:0.3, ease:"back.out(2.2)"}, 24.5);')
js.append('tl.fromTo("#wabar", {autoAlpha:0, y:260}, {autoAlpha:1, y:0, duration:0.5, ease:"power3.out"}, 25.5);')
js.append('tl.fromTo("#shop", {autoAlpha:0}, {autoAlpha:1, duration:0.4}, 26.5);')
js.append('tl.to("#wabar, #adv", {scale:1.03, duration:0.5, yoyo:true, repeat:5, ease:"sine.inOut"}, 27.0);')
js.append(f'tl.fromTo("#vig", {{opacity:0}}, {{opacity:1, duration:0.5, ease:"none"}}, {T(TOTAL - 0.5)});')

CSS = f"""
@font-face {{ font-family:"Hind Siliguri"; src:url(media/fonts/hind-siliguri-bengali-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; unicode-range:U+0980-09FE,U+200C-200D,U+25CC; }}
@font-face {{ font-family:"Hind Siliguri"; src:url(media/fonts/hind-siliguri-latin-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; unicode-range:U+0000-00FF,U+2000-206F; }}
@font-face {{ font-family:"Sora"; src:url(media/fonts/sora.woff2) format("woff2"); font-weight:600 800; font-display:block; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#000; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#000; font-family:"Hind Siliguri", sans-serif; color:#fff; }}
#stage {{ position:absolute; inset:0; }}
.shot {{ position:absolute; inset:0; opacity:0; overflow:hidden; }}
.mv {{ position:absolute; inset:0; }}
.mv video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
#black {{ position:absolute; inset:0; background:#000; z-index:40; }}
#flash {{ position:absolute; inset:0; background:#fff; z-index:41; opacity:0; }}
#fade {{ position:absolute; inset:0; background:#000; z-index:39; opacity:0; }}
.ov {{ position:absolute; z-index:30; visibility:hidden; font-weight:700; text-align:center; left:0; width:100%;
  text-shadow:0 6px 26px rgba(0,0,0,.75); paint-order:stroke fill; -webkit-text-stroke:8px rgba(0,0,0,.55); }}
.big {{ top:400px; font-size:150px; line-height:1.2; }}
#brand {{ top:190px; }}
.gold {{ font-family:"Sora"; font-weight:800; font-size:140px; letter-spacing:-.01em; color:{GOLD}; -webkit-text-stroke:7px rgba(20,12,0,.85); }}
.sub12 {{ margin-top:6px; font-size:66px; visibility:hidden; }}
.chip {{ left:56px; width:auto; padding:10px 30px 2px; border-radius:20px; background:rgba(0,0,0,.55); font-size:66px; -webkit-text-stroke:0; }}
.goldtxt {{ color:{GOLD}; }}
#f1 {{ top:640px; }} #f2 {{ top:770px; }}
.sizes {{ top:1450px; left:50%; translate:-50% 0; font-size:72px; }}
#arrow {{ position:absolute; left:430px; top:690px; width:400px; height:260px; z-index:30; visibility:hidden; filter:drop-shadow(0 4px 10px rgba(0,0,0,.6)); }}
.offer {{ color:{YELLOW}; -webkit-text-stroke:12px rgba(0,0,0,.85); }}
#caps {{ top:1290px; font-size:124px; }}
#badge {{ position:absolute; right:60px; top:230px; width:230px; height:230px; border-radius:50%; background:{RED}; z-index:31; visibility:hidden;
  display:flex; align-items:center; justify-content:center; box-shadow:0 0 0 10px rgba(255,255,255,.9), 0 20px 40px rgba(0,0,0,.5); }}
#badge span {{ font-family:"Sora"; font-weight:800; font-size:64px; color:#fff; letter-spacing:.02em; }}
.water {{ top:1400px; display:flex; align-items:center; justify-content:center; gap:18px; font-size:82px; }}
.water svg {{ filter:drop-shadow(0 4px 10px rgba(0,0,0,.6)); }}
#order {{ top:140px; font-size:128px; }}
.adv {{ top:320px; font-size:84px; }}
#wabar {{ position:absolute; left:90px; width:900px; top:1420px; height:120px; border-radius:999px; background:linear-gradient(180deg,#1E9E50,#137A3C); z-index:31; visibility:hidden;
  display:flex; align-items:center; justify-content:center; gap:22px; box-shadow:0 18px 40px rgba(0,0,0,.5); }}
#wabar span {{ font-family:"Sora"; font-weight:800; font-size:62px; color:#fff; letter-spacing:.01em; }}
#shop {{ top:1560px; font-family:"Sora"; font-weight:600; font-size:40px; -webkit-text-stroke:0; }}
#vig {{ position:absolute; inset:0; z-index:45; opacity:0; pointer-events:none; background:radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0) 45%, rgba(0,0,0,.75) 100%); }}
"""

shots = [h for h in html if h.startswith('<div class="shot"')]
rest = [h for h in html if not h.startswith('<div class="shot"')]
page = f"""<!doctype html>
<html lang="bn"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<title>SaHa GoLD ad</title><style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="1080" data-height="1920">
<div id="stage">
{chr(10).join(shots)}
<div id="fade"></div>
</div>
{chr(10).join(rest)}
<audio id="mix" src="media/mix.wav" data-start="0" data-duration="{TOTAL:.3f}" data-track-index="20"></audio>
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
print(f"built index.html: {TOTAL}s, {'whisper' if WORDS else 'fallback'} word anchors")
