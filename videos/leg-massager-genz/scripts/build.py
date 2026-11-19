#!/usr/bin/env python3
"""Leg Massager Gen-Z ad -> index.html (HyperFrames 0.9.23: timed muted <video class="clip">, one paused GSAP timeline on
window.__timelines["main"], fromTo with immediateRender:false, no negative positions, finite repeats only)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "build/timeline.json").read_text(encoding="utf-8"))
BT = {b["n"]: b for b in TL["beats"]}
SP = {int(k): v for k, v in TL["spans"].items()}
TOTAL = TL["total"]
YEL = "#FFD60A"
RING = json.loads((ROOT / "scripts/ring.json").read_text())      # control-unit position + press time in beat 5
T = lambda x: f"{x:.3f}"
html, js = [], []
st = lambda n: BT[n]["start"]
en = lambda n: BT[n]["end"]

# ------------------------------------------------------------------ footage
FILT = {1: "saturate(1.02)", 2: "saturate(.55) contrast(1.03)", 3: "saturate(.55)", 4: "saturate(1.12) sepia(.1)", 5: "saturate(1.12) sepia(.1)",
        6: "saturate(1.12) sepia(.12)", 7: "saturate(1.12) sepia(.1) brightness(1.1)", 8: "saturate(1.08) sepia(.06)", 9: "saturate(1.1) sepia(.06)"}
for n in range(1, 10):
    b = BT[n]
    html.append(f'<div class="shot" id="sh{n}" style="z-index:{n}"><div class="mv" id="mv{n}" data-layout-allow-overflow><video id="v{n}" class="clip" '
                f'src="build/c{n}.mp4" muted playsinline style="filter:{FILT[n]}" data-start="{T(b["clip_start"])}" data-duration="{T(b["clip_dur"])}" '
                f'data-media-start="0" data-track-index="{n}"></video></div></div>')
    cs, cd = b["clip_start"], b["clip_dur"]
    if n == 1:      # punch-in 100 -> 108 % on the cut out of the black flash, then a slow push
        js.append(f'tl.fromTo("#mv1", {{scale:1.0}}, {{scale:1.08, duration:0.35, ease:"power3.out", immediateRender:false}}, 0.4);')
        js.append(f'tl.fromTo("#mv1", {{scale:1.08}}, {{scale:1.13, duration:{T(en(1) - 0.75)}, ease:"none", immediateRender:false}}, 0.75);')
    elif n == 6:    # slow zoom-out
        js.append(f'tl.fromTo("#mv6", {{scale:1.12}}, {{scale:1.0, duration:{T(cd)}, ease:"sine.out", immediateRender:false}}, {T(cs)});')
    elif n == 2:    # slow push-in continues the hook's tension
        js.append(f'tl.fromTo("#mv2", {{scale:1.0}}, {{scale:1.06, duration:{T(cd)}, ease:"none", immediateRender:false}}, {T(cs)});')
    else:
        js.append(f'tl.fromTo("#mv{n}", {{scale:1.0}}, {{scale:1.05, duration:{T(cd)}, ease:"none", immediateRender:false}}, {T(cs)});')
js.append('tl.set("#sh1", {opacity:1}, 0);')
# 0.4 s black flash cut
js.append('tl.set("#flash", {opacity:1}, 0); tl.set("#flash", {opacity:0}, 0.4);')
js.append('tl.fromTo("#wflash", {opacity:0.85}, {opacity:0, duration:0.18, ease:"power2.out", immediateRender:false}, 0.4);')
# 1 -> 2 hard cut
js.append(f'tl.set("#sh2", {{opacity:1}}, {T(st(2))}); tl.set("#sh1", {{opacity:0}}, {T(st(2))});')
# 2 -> 3 whip-pan (0.24 s): outgoing flies left, incoming arrives from the right, motion blur both ways
w = st(3)
js.append(f'tl.fromTo("#sh2", {{x:0, filter:"blur(0px)"}}, {{x:-1080, filter:"blur(22px)", duration:0.24, ease:"power3.in", immediateRender:false}}, {T(w - 0.12)});')
js.append(f'tl.set("#sh3", {{opacity:1}}, {T(w - 0.12)});')
js.append(f'tl.fromTo("#sh3", {{x:1080, filter:"blur(22px)"}}, {{x:0, filter:"blur(0px)", duration:0.24, ease:"power3.out", immediateRender:false}}, {T(w - 0.12)});')
js.append(f'tl.set("#sh2", {{opacity:0}}, {T(w + 0.12)});')
# colour returns to warm on beat 3
js.append(f'tl.fromTo("#v3", {{filter:"saturate(.55) sepia(0)"}}, {{filter:"saturate(1.14) sepia(.12)", duration:0.9, ease:"sine.out", immediateRender:false}}, {T(w + 0.15)});')
# all other joins: 6-frame cross-dissolve centred on the cut
for n in range(4, 10):
    t = st(n)
    js.append(f'tl.fromTo("#sh{n}", {{opacity:0}}, {{opacity:1, duration:0.2, ease:"none", immediateRender:false}}, {T(t - 0.1)});')
    js.append(f'tl.set("#sh{n - 1}", {{opacity:0}}, {T(t + 0.1)});')
# beat 6 warm vignette, beat 7 sun flare
js.append(f'tl.fromTo("#warmvig", {{opacity:0}}, {{opacity:1, duration:0.5, immediateRender:false}}, {T(st(6))});')
js.append(f'tl.to("#warmvig", {{opacity:0, duration:0.2}}, {T(en(6) - 0.1)});')
js.append(f'tl.fromTo("#flare", {{opacity:0, x:40, y:-20}}, {{opacity:0.85, x:0, y:0, duration:0.8, ease:"sine.out", immediateRender:false}}, {T(st(7))});')
js.append(f'tl.to("#flare", {{x:-60, y:30, duration:{T(en(7) - st(7) - 0.9)}, ease:"none"}}, {T(st(7) + 0.8)});')
js.append(f'tl.to("#flare", {{opacity:0, duration:0.2}}, {T(en(7) - 0.1)});')

# ------------------------------------------------------------------ hook text
html.append('<div id="hook"><span>সারাদিন বসে থাকো?</span></div>')
js.append('tl.fromTo("#hook", {autoAlpha:0, scale:1.6, y:-30}, {autoAlpha:1, scale:1, y:0, duration:0.45, ease:"back.out(2.6)"}, 0.2);')
js.append(f'tl.to("#hook", {{autoAlpha:0, y:-20, duration:0.2}}, {T(en(1) - 0.2)});')

# ------------------------------------------------------------------ word-by-word captions (pages of <= 2 lines)
words = TL["words"]
pages, cur = [], []
for wd in words:
    n = sum(len(x["w"]) + 1 for x in cur)
    if cur and (cur[-1]["beat"] != wd["beat"] or n + len(wd["w"]) > 32 or (cur[-1]["w"][-1] in "।,?" and n >= 12)):
        pages.append(cur)
        cur = []
    cur.append(wd)
pages.append(cur)
NOCAP = {8}                                 # beat 8 shows the price card instead
k = 0
for p, pg in enumerate(pages):
    bt = pg[0]["beat"]
    if bt in NOCAP:
        continue
    cls = "cap hi" if bt == 9 else "cap"
    spans = "".join(f'<span class="w" id="w{k + i}">{x["w"]}</span> ' for i, x in enumerate(pg))
    html.append(f'<div class="{cls}" id="pg{p}">{spans.strip()}</div>')
    nxt = pages[p + 1][0]["start"] if p + 1 < len(pages) and pages[p + 1][0]["beat"] == bt else None
    p_end = min(nxt - 0.02, en(bt) - 0.05) if nxt else (en(bt) - 0.05 if bt != 9 else TOTAL)
    js.append(f'tl.set("#pg{p}", {{autoAlpha:1}}, {T(pg[0]["start"] - 0.02)});')
    for i, x in enumerate(pg):
        a = x["start"]
        b2 = pg[i + 1]["start"] if i + 1 < len(pg) else min(x["end"] + 0.25, p_end)
        js.append(f'tl.fromTo("#w{k + i}", {{autoAlpha:0, scale:0.8}}, {{autoAlpha:1, scale:1, duration:0.12, ease:"back.out(2)"}}, {T(a)});')
        js.append(f'tl.set("#w{k + i}", {{color:"{YEL}"}}, {T(a)}); tl.set("#w{k + i}", {{color:"#FFFFFF"}}, {T(b2)});')
    if bt != 9 or nxt:
        js.append(f'tl.set("#pg{p}", {{autoAlpha:0}}, {T(p_end)});')
    k += len(pg)

# ------------------------------------------------------------------ beat 4 badges
BADGES = [("🔋", "USB Charge"), ("🧵", "Soft Fabric"), ("✋", "Easy Use")]
a4, b4 = SP[4]
html.append('<div id="badges">' + "".join(f'<div class="badge" id="bd{i}"><i>{e}</i>{t}</div>' for i, (e, t) in enumerate(BADGES)) + '</div>')
w4 = [x for x in TL["words"] if x["beat"] == 4]
cue4 = [w4[0]["start"]] + [w4[i + 1]["start"] for i, x in enumerate(w4[:-1]) if x["w"].endswith(",")]
for i in range(3):
    t = cue4[i]
    js.append(f'tl.fromTo("#bd{i}", {{autoAlpha:0, x:-60, scale:0.85}}, {{autoAlpha:1, x:0, scale:1, duration:0.3, ease:"back.out(2.2)"}}, {T(t)});')
js.append(f'tl.to("#badges", {{autoAlpha:0, duration:0.15}}, {T(en(4) - 0.15)});')

# ------------------------------------------------------------------ beat 5 blue glow ring on the control unit (pulses after the press)
html.append(f'<div id="ring" style="left:{RING["x"] - 110}px;top:{RING["y"] - 110}px"></div>')
t0 = BT[5]["clip_start"] + RING["src_t"]
js.append(f'tl.set("#ring", {{autoAlpha:1}}, {T(t0)});')
for i in range(3):
    js.append(f'tl.fromTo("#ring", {{scale:0.55, opacity:1}}, {{scale:1.35, opacity:0, duration:0.55, ease:"power2.out", immediateRender:false}}, {T(t0 + i * 0.6)});')
js.append(f'tl.set("#ring", {{autoAlpha:0}}, {T(min(t0 + 1.8, en(5) - 0.1))});')

# ------------------------------------------------------------------ beat 8 price card (slides up 0.3 s apart, from the price line)
a8 = SP[8][0]
html.append('<div id="price"><div class="pc" id="pc0"><b>৳২,২৯৯</b></div>'
            '<div class="pc pill green" id="pc1">সারাদেশে ফ্রি ডেলিভারি</div>'
            '<div class="pc pill yellow" id="pc2">ক্যাশ অন ডেলিভারি</div></div>')
w8 = [x for x in TL["words"] if x["beat"] == 8]
cue8 = [a8, next(x["start"] for x in w8 if x["w"].startswith("সারাদেশে")), next(x["start"] for x in w8 if x["w"].startswith("ক্যাশ"))]
for i in range(3):
    js.append(f'tl.fromTo("#pc{i}", {{autoAlpha:0, y:90}}, {{autoAlpha:1, y:0, duration:0.4, ease:"back.out(1.8)"}}, {T(cue8[i])});')
js.append(f'tl.to("#price", {{autoAlpha:0, duration:0.1}}, {T(en(8) - 0.1)});')

# ------------------------------------------------------------------ beat 9 CTA (stays to the end)
s9 = st(9)
html.append('<div id="arrow"><svg viewBox="0 0 60 70" width="66" height="76"><path d="M30 4 V56 M8 36 L30 62 L52 36" fill="none" stroke="#fff" '
            'stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/></svg></div>'
            '<div id="cta"><svg viewBox="0 0 48 48" width="58" height="58"><path d="M24 4C12.4 4 4 12.3 4 23.2c0 5.7 2.3 10.6 6.2 14V44l6-3.3c2.4.7 5 1 7.8 1 '
            '11.6 0 20-8.3 20-19.2S35.6 4 24 4z" fill="#fff"/><path d="M12 28l8.5-9 4.4 4.6 8.1-4.6-8.5 9-4.4-4.6z" fill="#7B3CFF"/></svg>Send Message</div>')
js.append(f'tl.fromTo("#cta", {{autoAlpha:0, y:80, scale:0.9}}, {{autoAlpha:1, y:0, scale:1, duration:0.35, ease:"back.out(2)"}}, {T(s9 + 0.1)});')
reps = int((TOTAL - s9 - 0.5) / 0.9)
js.append(f'tl.fromTo("#ctab", {{scale:1}}, {{scale:1.06, duration:0.45, ease:"sine.inOut", yoyo:true, repeat:{reps * 2 - 1}, immediateRender:false}}, {T(s9 + 0.45)});')
js.append(f'tl.fromTo("#arrow", {{autoAlpha:0, y:-20}}, {{autoAlpha:1, y:0, duration:0.3}}, {T(s9 + 0.3)});')
js.append(f'tl.fromTo("#arrow", {{y:0}}, {{y:22, duration:0.4, ease:"sine.inOut", yoyo:true, repeat:{int((TOTAL - s9 - 0.7) / 0.4) - 1}, immediateRender:false}}, {T(s9 + 0.6)});')

FONTS = "".join(f'@font-face {{ font-family:"Hind Siliguri"; src:url(fonts/hind-siliguri-{sub}-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; '
                f'unicode-range:{"U+0964-0965,U+0980-09FE,U+200C-200D,U+25CC" if sub == "bengali" else "U+0000-00FF,U+2000-206F"}; }}\n' for sub in ("bengali", "latin")) + \
    "".join(f'@font-face {{ font-family:"Poppins"; src:url(fonts/poppins-latin-{w}-normal.woff2) format("woff2"); font-weight:{w}; font-display:block; '
            f'unicode-range:U+0000-00FF,U+2000-206F; }}\n' for w in (700, 800)) + \
    '@font-face { font-family:"Badge Emoji"; src:url(fonts/noto-emoji-subset.ttf) format("truetype"); font-display:block; }\n'
STROKE = "-webkit-text-stroke:12px #000; paint-order:stroke fill; text-shadow:0 6px 18px rgba(0,0,0,.55);"
CSS = FONTS + f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#000; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#000; font-family:"Poppins","Hind Siliguri",sans-serif; color:#fff; }}
.shot {{ position:absolute; inset:0; opacity:0; overflow:hidden; }}
.mv {{ position:absolute; inset:0; }}
.mv video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
#warmvig {{ position:absolute; inset:0; z-index:12; pointer-events:none; opacity:0; background:radial-gradient(ellipse 78% 62% at 50% 48%, rgba(0,0,0,0) 52%, rgba(70,30,0,.55) 100%); }}
#flare {{ position:absolute; left:420px; top:-260px; width:1000px; height:1000px; z-index:13; pointer-events:none; opacity:0; mix-blend-mode:screen;
  background:radial-gradient(circle at 50% 50%, rgba(255,236,190,.95) 0%, rgba(255,196,110,.45) 22%, rgba(255,160,60,0) 62%); }}
#hook {{ position:absolute; left:40px; width:1000px; top:170px; z-index:61; text-align:center; visibility:hidden; transform-origin:50% 50%; }}
#hook span {{ font-family:"Hind Siliguri",sans-serif; font-weight:700; font-size:104px; line-height:1.3; color:#fff; {STROKE} }}
.cap {{ position:absolute; left:80px; width:920px; bottom:330px; z-index:40; text-align:center; visibility:hidden;
  font-family:"Hind Siliguri","Poppins",sans-serif; font-weight:700; font-size:76px; line-height:1.32; text-wrap:balance; }}
.cap.hi {{ bottom:640px; }}
.w {{ display:inline-block; color:#fff; visibility:hidden; {STROKE} transform-origin:50% 70%; }}
#badges {{ position:absolute; left:70px; top:300px; z-index:38; display:flex; flex-direction:column; gap:22px; }}
.badge {{ visibility:hidden; display:flex; align-items:center; gap:16px; padding:16px 32px 16px 20px; border-radius:60px; font-family:"Poppins",sans-serif; font-weight:700;
  font-size:44px; color:#111; background:rgba(255,255,255,.94); box-shadow:0 10px 30px rgba(0,0,0,.35); width:max-content; }}
.badge i {{ font-style:normal; font-size:44px; font-family:"Badge Emoji",sans-serif; }}
#ring {{ position:absolute; width:220px; height:220px; z-index:30; border-radius:50%; border:9px solid #39B8FF; visibility:hidden;
  box-shadow:0 0 34px 12px rgba(40,160,255,.75), inset 0 0 28px 6px rgba(40,160,255,.6); }}
#price {{ position:absolute; left:0; width:1080px; top:330px; z-index:38; display:flex; flex-direction:column; align-items:center; gap:28px; }}
.pc {{ visibility:hidden; }}
#pc0 b {{ display:block; font-family:"Poppins","Hind Siliguri",sans-serif; font-weight:800; font-size:210px; line-height:1.05; color:#fff; letter-spacing:-2px;
  -webkit-text-stroke:14px #000; paint-order:stroke fill; text-shadow:0 10px 30px rgba(0,0,0,.5); }}
.pill {{ font-family:"Hind Siliguri",sans-serif; font-weight:700; font-size:56px; line-height:1.25; padding:16px 46px 12px; border-radius:80px; box-shadow:0 12px 30px rgba(0,0,0,.35); }}
.pill.green {{ background:#0F8A3C; color:#fff; }}
.pill.yellow {{ background:{YEL}; color:#111; }}
#arrow {{ position:absolute; left:507px; bottom:420px; z-index:41; visibility:hidden; filter:drop-shadow(0 4px 8px rgba(0,0,0,.6)); }}
#cta {{ position:absolute; left:240px; width:600px; bottom:250px; height:150px; z-index:41; visibility:hidden; }}
#ctab {{ position:absolute; inset:0; }}
#ctain {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; gap:18px; border-radius:80px; font-family:"Poppins",sans-serif; font-weight:800;
  font-size:54px; color:#fff; background:linear-gradient(100deg,#0A84FF 0%,#7B3CFF 60%,#E040A0 100%); box-shadow:0 14px 40px rgba(60,60,255,.55); }}
#wm {{ position:absolute; left:48px; bottom:262px; z-index:50; font-family:"Poppins",sans-serif; font-weight:700; font-size:28px; color:#fff; opacity:.6;
  -webkit-text-stroke:5px #000; paint-order:stroke fill; text-shadow:0 2px 6px rgba(0,0,0,.7); }}
#wflash {{ position:absolute; inset:0; z-index:58; background:#fff; opacity:0; pointer-events:none; }}
#flash {{ position:absolute; inset:0; z-index:59; background:#000; opacity:0; pointer-events:none; }}
"""
page_html = "\n".join(html).replace('<div id="cta">', '<div id="cta"><div id="ctab"><div id="ctain">').replace("Send Message</div>", "Send Message</div></div></div>")
shots = [h for h in page_html.split("\n") if h.startswith('<div class="shot"')]
rest = [h for h in page_html.split("\n") if not h.startswith('<div class="shot"')]
hook_i = [i for i, h in enumerate(rest) if h.startswith('<div id="hook"')]
out = f"""<!doctype html>
<html lang="bn" data-resolution="portrait"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<title>Leg Massager — Gen-Z self-care</title><style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="1080" data-height="1920">
{chr(10).join(shots)}
<div id="warmvig"></div><div id="flare"></div>
{chr(10).join(rest)}
<div id="wm">Bakaina.com</div>
<div id="wflash"></div><div id="flash"></div>
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
(ROOT / "index.html").write_text(out, encoding="utf-8")
print(f"built index.html {TOTAL}s, {k} caption words, {len(pages)} pages")
