#!/usr/bin/env python3
"""Winter Fleece Hood reel (3 clips + voice) -> index.html (HyperFrames 0.9.23: timed muted <video class="clip">, one paused GSAP
timeline on window.__timelines["main"], fromTo with immediateRender:false, no negative positions, finite repeats only)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "build/timeline.json").read_text(encoding="utf-8"))
BT = {b["n"]: b for b in TL["beats"]}
W = TL["words"]
TOTAL = TL["total"]
YEL = "#FFD60A"
PRICE = "৳৪৯০"
T = lambda x: f"{x:.3f}"
html, js = [], []
st = lambda n: BT[n]["start"]
en = lambda n: BT[n]["end"]
LINE_START = {w["line"]: w["start"] for w in reversed(W)}

# ------------------------------------------------------------------ footage + grades
COLD = "saturate(.9) hue-rotate(-8deg) brightness(.98)"
WARMN = "saturate(1.03) sepia(.06)"
FILT = {1: COLD, 2: COLD, 3: WARMN}
for n in (1, 2, 3):
    b = BT[n]
    html.append(f'<div class="shot" id="sh{n}" style="z-index:{n}"><div class="mv" id="mv{n}" data-layout-allow-overflow><video id="v{n}" class="clip" '
                f'src="build/c{n}.mp4" muted playsinline style="filter:{FILT[n]}" data-start="{T(b["clip_start"])}" data-duration="{T(b["clip_dur"])}" '
                f'data-media-start="0" data-track-index="{n}"></video></div></div>')
    cs, cd = b["clip_start"], b["clip_dur"]
    if n == 1:
        js.append('tl.fromTo("#mv1", {scale:1.0}, {scale:1.08, duration:1.0, ease:"power2.out", immediateRender:false}, 0);')
        js.append(f'tl.fromTo("#mv1", {{scale:1.08}}, {{scale:1.14, duration:{T(en(1) - 1.0)}, ease:"none", immediateRender:false}}, 1.0);')
    elif n == 2:
        js.append(f'tl.fromTo("#mv2", {{scale:1.0}}, {{scale:1.1, duration:{T(cd)}, ease:"none", immediateRender:false}}, {T(cs)});')
    else:       # gentle push that stops where the final CTA frame holds (last 3 s)
        js.append(f'tl.fromTo("#mv3", {{scale:1.0}}, {{scale:1.04, duration:{T(TOTAL - 3 - cs)}, ease:"sine.out", immediateRender:false}}, {T(cs)});')
js.append('tl.set("#sh1", {opacity:1}, 0); tl.set("#cold", {opacity:1}, 0);')
js.append('tl.set("#flash", {opacity:1}, 0); tl.set("#flash", {opacity:0}, 0.3);')
w = st(2)          # 1 -> 2 whip-pan + white flash, grade back to warm neutral
js.append(f'tl.fromTo("#sh1", {{x:0, filter:"blur(0px)"}}, {{x:-1080, filter:"blur(22px)", duration:0.24, ease:"power3.in", immediateRender:false}}, {T(w - 0.12)});')
js.append(f'tl.set("#sh2", {{opacity:1}}, {T(w - 0.12)});')
js.append(f'tl.fromTo("#sh2", {{x:1080, filter:"blur(22px)"}}, {{x:0, filter:"blur(0px)", duration:0.24, ease:"power3.out", immediateRender:false}}, {T(w - 0.12)});')
js.append(f'tl.set("#sh1", {{opacity:0}}, {T(w + 0.12)});')
js.append(f'tl.fromTo("#wflash", {{opacity:0.9}}, {{opacity:0, duration:0.2, ease:"power2.out", immediateRender:false}}, {T(w + 0.1)});')
js.append(f'tl.fromTo("#v2", {{filter:"{COLD}"}}, {{filter:"{WARMN}", duration:0.6, ease:"sine.out", immediateRender:false}}, {T(w + 0.1)});')
js.append(f'tl.fromTo("#cold", {{opacity:1}}, {{opacity:0, duration:0.6, ease:"sine.out", immediateRender:false}}, {T(w + 0.1)});')
c3 = st(3)         # 2 -> 3 six-frame cross-dissolve
js.append(f'tl.fromTo("#sh3", {{opacity:0}}, {{opacity:1, duration:0.2, ease:"none", immediateRender:false}}, {T(c3 - 0.1)});')
js.append(f'tl.set("#sh2", {{opacity:0}}, {T(c3 + 0.1)});')

# ------------------------------------------------------------------ hook text
html.append('<div id="hook" class="big"><span>শীতে বের হলেই এই অবস্থা? <i class="emo">🥶</i></span></div><div id="hook2" class="big"><span>ঠান্ডা বাতাসে কান-মুখ জমে যায়</span></div>')
js.append('tl.fromTo("#hook", {autoAlpha:0, scale:1.6, y:-30}, {autoAlpha:1, scale:1, y:0, duration:0.45, ease:"back.out(2.6)"}, 0.2);')
js.append('tl.fromTo("#hook2", {autoAlpha:0, y:16}, {autoAlpha:1, y:0, duration:0.5, ease:"power2.out"}, 2.5);')
js.append(f'tl.to(["#hook", "#hook2"], {{autoAlpha:0, duration:0.12}}, {T(w - 0.12)});')

# ------------------------------------------------------------------ detail badges from the right, 0.8 s apart, from voice line 3
BADGES = [("🧶", "নরম ফ্লিস লাইনিং"), ("😷", "মুখ ঢাকা"), ("🪢", "দড়ি দিয়ে ফিট")]
html.append('<div id="badges">' + "".join(f'<div class="badge" id="bd{i}"><i class="emo">{e}</i>{t}</div>' for i, (e, t) in enumerate(BADGES)) + '</div>')
for i in range(3):
    js.append(f'tl.fromTo("#bd{i}", {{autoAlpha:0, x:120, scale:0.9}}, {{autoAlpha:1, x:0, scale:1, duration:0.32, ease:"back.out(2.2)"}}, {T(LINE_START[3] + 0.8 * i)});')
js.append(f'tl.to("#badges", {{autoAlpha:0, duration:0.15}}, {T(en(2) - 0.15)});')

# ------------------------------------------------------------------ word-by-word captions (pages of <= 2 lines)
pages, cur = [], []
for wd in W:
    n = sum(len(x["w"]) + 1 for x in cur)
    if cur and (cur[-1]["line"] != wd["line"] and (cur[-1]["beat"] != wd["beat"] or n >= 12) or n + len(wd["w"]) > 30 or (cur[-1]["w"][-1] in "।,?" and n >= 12)):
        pages.append(cur)
        cur = []
    cur.append(wd)
pages.append(cur)
k = 0
for p, pg in enumerate(pages):
    bt = pg[0]["beat"]
    cls = "cap hi" if bt == 3 else "cap"
    spans = "".join(f'<span class="w" id="w{k + i}">{x["w"]}</span> ' for i, x in enumerate(pg))
    html.append(f'<div class="{cls}" id="pg{p}">{spans.strip()}</div>')
    nxt = pages[p + 1][0]["start"] if p + 1 < len(pages) and pages[p + 1][0]["beat"] == bt else None
    p_end = min(nxt - 0.02, en(bt) - 0.05) if nxt else (en(bt) - 0.05 if bt != 3 else TOTAL)
    js.append(f'tl.set("#pg{p}", {{autoAlpha:1}}, {T(pg[0]["start"] - 0.02)});')
    for i, x in enumerate(pg):
        a = x["start"]
        b2 = pg[i + 1]["start"] if i + 1 < len(pg) else min(x["end"] + 0.25, p_end)
        js.append(f'tl.fromTo("#w{k + i}", {{autoAlpha:0, scale:0.8}}, {{autoAlpha:1, scale:1, duration:0.12, ease:"back.out(2)"}}, {T(a)});')
        js.append(f'tl.set("#w{k + i}", {{color:"{YEL}"}}, {T(a)}); tl.set("#w{k + i}", {{color:"#FFFFFF"}}, {T(b2)});')
    if bt != 3 or nxt:
        js.append(f'tl.set("#pg{p}", {{autoAlpha:0}}, {T(p_end)});')
    k += len(pg)

# ------------------------------------------------------------------ CTA (offsets from the brief, relative to the beat start); stays to the end
html.append(f'<div id="price"><div class="pc big2" id="pc0">দুই কালারে পাওয়া যাচ্ছে</div><div class="pc pill green" id="pc1">ক্যাশ অন ডেলিভারি</div>'
            f'<div class="pc" id="pc2"><b>{PRICE}</b></div></div>')
for i, d in enumerate((0.3, 1.2, 1.8)):
    js.append(f'tl.fromTo("#pc{i}", {{autoAlpha:0, y:80}}, {{autoAlpha:1, y:0, duration:0.4, ease:"back.out(1.8)"}}, {T(c3 + d)});')
bt_on = c3 + 2.0
html.append('<div id="arrow"><svg viewBox="0 0 60 70" width="66" height="76"><path d="M30 4 V56 M8 36 L30 62 L52 36" fill="none" stroke="#fff" '
            'stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/></svg></div>'
            '<div id="cta"><div id="ctab"><div id="ctain"><svg viewBox="0 0 48 48" width="56" height="56"><path d="M24 4C12.4 4 4 12.3 4 23.2c0 5.7 2.3 10.6 6.2 14V44l6-3.3c2.4.7 5 1 7.8 1 '
            '11.6 0 20-8.3 20-19.2S35.6 4 24 4z" fill="#fff"/><path d="M12 28l8.5-9 4.4 4.6 8.1-4.6-8.5 9-4.4-4.6z" fill="#7B3CFF"/></svg>এখনই মেসেজ করুন</div></div></div>')
js.append(f'tl.fromTo("#cta", {{autoAlpha:0, y:80, scale:0.9}}, {{autoAlpha:1, y:0, scale:1, duration:0.35, ease:"back.out(2)"}}, {T(bt_on)});')
reps = int((TOTAL - bt_on - 0.4) / 0.9)
js.append(f'tl.fromTo("#ctab", {{scale:1}}, {{scale:1.06, duration:0.45, ease:"sine.inOut", yoyo:true, repeat:{reps * 2 - 1}, immediateRender:false}}, {T(bt_on + 0.35)});')
js.append(f'tl.fromTo("#arrow", {{autoAlpha:0, y:-20}}, {{autoAlpha:1, y:0, duration:0.3}}, {T(bt_on + 0.2)});')
js.append(f'tl.fromTo("#arrow", {{y:0}}, {{y:22, duration:0.4, ease:"sine.inOut", yoyo:true, repeat:{int((TOTAL - bt_on - 0.6) / 0.4) - 1}, immediateRender:false}}, {T(bt_on + 0.5)});')

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
#cold {{ position:absolute; inset:0; z-index:11; pointer-events:none; opacity:0; background:#3C78C8; mix-blend-mode:soft-light; }}
#flare {{ position:absolute; left:420px; top:-260px; width:1000px; height:1000px; z-index:13; pointer-events:none; opacity:0; mix-blend-mode:screen;
  background:radial-gradient(circle at 50% 50%, rgba(255,236,190,.95) 0%, rgba(255,196,110,.45) 22%, rgba(255,160,60,0) 62%); }}
.emo {{ font-style:normal; font-family:"Badge Emoji",sans-serif; -webkit-text-stroke:0; }}
.big {{ position:absolute; left:40px; width:1000px; z-index:39; text-align:center; font-family:"Hind Siliguri",sans-serif; font-weight:700; color:#fff; }}
.big span, .big p {{ display:inline-block; {STROKE} }}
#hook {{ top:170px; z-index:61; visibility:hidden; font-size:100px; line-height:1.28; }}
#hook2 {{ top:440px; visibility:hidden; font-size:66px; line-height:1.3; }}
#tiles {{ position:absolute; left:40px; width:1000px; top:200px; z-index:39; display:flex; justify-content:center; gap:18px; }}
.tile {{ visibility:hidden; font-family:"Hind Siliguri",sans-serif; font-weight:700; font-size:64px; line-height:1.2; color:#111; background:rgba(255,255,255,.95);
  padding:14px 34px 8px; border-radius:24px; box-shadow:0 10px 26px rgba(0,0,0,.35); }}
.cap {{ position:absolute; left:80px; width:920px; bottom:330px; z-index:40; text-align:center; visibility:hidden;
  font-family:"Hind Siliguri","Poppins",sans-serif; font-weight:700; font-size:74px; line-height:1.32; text-wrap:balance; }}
.cap.hi {{ bottom:560px; }}
.w {{ display:inline-block; color:#fff; visibility:hidden; {STROKE} transform-origin:50% 70%; }}
#badges {{ position:absolute; right:60px; top:330px; z-index:38; display:flex; flex-direction:column; align-items:flex-end; gap:22px; }}
.badge {{ visibility:hidden; display:flex; align-items:center; gap:14px; padding:14px 30px 10px 20px; border-radius:60px; font-family:"Hind Siliguri",sans-serif; font-weight:700;
  font-size:50px; line-height:1.2; color:#111; background:rgba(255,255,255,.95); box-shadow:0 10px 30px rgba(0,0,0,.35); width:max-content; }}
.badge .emo {{ font-size:46px; }}
#price {{ position:absolute; left:0; width:1080px; top:190px; z-index:38; display:flex; flex-direction:column; align-items:center; gap:24px; }}
.pc {{ visibility:hidden; }}
#pc2 b {{ display:block; font-family:"Poppins","Hind Siliguri",sans-serif; font-weight:800; font-size:170px; line-height:1.1; color:#111; background:{YEL};
  padding:18px 64px 6px; border-radius:40px; box-shadow:0 16px 40px rgba(0,0,0,.4); transform:rotate(-3deg); }}
.pill {{ font-family:"Hind Siliguri",sans-serif; font-weight:700; font-size:58px; line-height:1.25; padding:16px 50px 12px; border-radius:80px; box-shadow:0 12px 30px rgba(0,0,0,.35); color:#fff; }}
.pill.green {{ background:#0F8A3C; }}
.big2 {{ font-family:"Hind Siliguri",sans-serif; font-weight:700; font-size:80px; line-height:1.25; color:#fff; {STROKE} }}
#arrow {{ position:absolute; left:507px; bottom:420px; z-index:41; visibility:hidden; filter:drop-shadow(0 4px 8px rgba(0,0,0,.6)); }}
#cta {{ position:absolute; left:230px; width:620px; bottom:250px; height:150px; z-index:41; visibility:hidden; }}
#ctab {{ position:absolute; inset:0; }}
#ctain {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; gap:18px; border-radius:80px; font-family:"Hind Siliguri",sans-serif; font-weight:700;
  font-size:58px; color:#fff; background:linear-gradient(100deg,#0A84FF 0%,#7B3CFF 60%,#E040A0 100%); box-shadow:0 14px 40px rgba(60,60,255,.55); padding-top:6px; }}
#wm {{ position:absolute; left:40px; bottom:262px; z-index:50; font-family:"Poppins",sans-serif; font-weight:700; font-size:28px; color:#fff; opacity:.6;
  -webkit-text-stroke:5px #000; paint-order:stroke fill; text-shadow:0 2px 6px rgba(0,0,0,.7); }}
#wflash {{ position:absolute; inset:0; z-index:58; background:#fff; opacity:0; pointer-events:none; }}
#flash {{ position:absolute; inset:0; z-index:59; background:#000; opacity:0; pointer-events:none; }}
"""
shots = [h for h in html if h.startswith('<div class="shot"')]
rest = [h for h in html if not h.startswith('<div class="shot"')]
out = f"""<!doctype html>
<html lang="bn" data-resolution="portrait"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<title>Winter Fleece Hood</title><style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="1080" data-height="1920">
{chr(10).join(shots)}
<div id="cold"></div>
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
