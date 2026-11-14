#!/usr/bin/env python3
"""Clinic Reel -> index.html + build/sfx.json (HyperFrames 0.9.23; data-start/duration/media-start, class="clip",
one paused GSAP timeline on window.__timelines["main"], set/to/fromTo only). Look and timing: the client brief."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "build"
TL = json.loads((B / "timeline.json").read_text())
WORDS = json.loads((B / "words.json").read_text(encoding="utf-8"))
SEC = {s["n"]: s for s in TL["sections"]}
FIT = {f["n"]: f for f in TL["fit"]}
VO, CARD, TOTAL = TL["voice"], TL["card_at"], TL["total"]
BLUE, INK, MUTED, WHITE, SOFT, OK, DANGER, CTA = "#1A4FE0", "#12151A", "#5A6271", "#FFFFFF", "#EEF3FF", "#0E7350", "#C2261C", "#FF3B1F"
F = 1 / 30
html, js, sfx = [], [], []
T = lambda x: f"{x:.3f}"


def st(n):
    return SEC[n]["start"]


def nxt(n):
    return SEC[n + 1]["start"] if n < 6 else CARD


def w(sec, prefix, nth=0, default=None):
    hits = [x for x in WORDS if x["section"] == sec and x["text"].startswith(prefix)]
    if len(hits) > nth:
        return hits[nth]["start"]
    if default is None:
        raise KeyError(f"{prefix} not in S{sec}")
    return default


def cue(name, t, gain):
    sfx.append({"sfx": name, "t": round(t, 3), "gain": gain})


# ------------------------------------------------------------------ shots
for n in range(1, 7):
    f = FIT[n]
    t0 = st(n)
    dur = min(f["dur"] + 0.35, TOTAL - t0)
    html.append(f'<div class="shot" id="sh{n}" style="z-index:{n}"><div class="mv" id="mv{n}"><video id="v{n}" class="clip" src="build/s{n}.mp4" muted playsinline '
                f'data-start="{T(t0)}" data-duration="{T(dur)}" data-media-start="0" data-track-index="{n}"></video></div></div>')
    if f["hold"]:
        js.append(f'tl.fromTo("#mv{n}", {{scale:1}}, {{scale:1.04, duration:{T(f["hold"])}, ease:"none", immediateRender:false}}, {T(f["hold_at"])});')
js.append('tl.set("#sh1", {opacity:1}, 0);')
for n in range(2, 7):
    t = st(n)
    if n == 5:      # S4 -> S5: 8-frame upward slide
        js.append(f'tl.fromTo("#sh5", {{opacity:1, y:1920}}, {{y:0, duration:{T(8 * F)}, ease:"power3.out", immediateRender:false}}, {T(t)});')
        js.append(f'tl.set("#sh4", {{opacity:0}}, {T(t + 8 * F)});')
        cue("whoosh_fast", t - 0.08, 0.35)
    else:           # hard cut + 4-frame white flash at 15 %
        js.append(f'tl.set("#sh{n}", {{opacity:1}}, {T(t)}); tl.set("#sh{n - 1}", {{opacity:0}}, {T(t)});')
        js.append(f'tl.set("#flash", {{opacity:0.15}}, {T(t)}); tl.set("#flash", {{opacity:0}}, {T(t + 4 * F)});')

# ------------------------------------------------------------------ headlines + chips
HEAD = {1: (None, "ক্যান্সেল রোগী", "হারানো রোগী না"), 2: ("০১", "ক্যান্সেল মানে", "হারানো না"),
        3: ("০২", "আগে একটা", "সংখ্যা ঠিক করুন"), 4: ("০৩", "ওয়েবসাইট ≠", "বুকিং সিস্টেম"), 6: (None, "ধরে রাখাই", "আসল গ্রোথ")}
for n, (chip, l1, l2) in HEAD.items():
    t0, t1 = st(n) + 0.03, nxt(n)
    l1h = l1.replace("≠", '<span class="lat">≠</span>')
    html.append(f'<div class="hblock" id="hb{n}">' + (f'<div class="chip" id="ch{n}">{chip}</div>' if chip else "")
                + f'<div class="panel"><div class="ln"><span class="l1" id="h{n}a">{l1h}</span></div><div class="ln"><span class="l2" id="h{n}b">{l2}</span></div></div></div>')
    js.append(f'tl.set("#hb{n}", {{visibility:"visible"}}, {T(st(n))}); tl.set("#hb{n}", {{visibility:"hidden"}}, {T(t1)});')
    d = 0.0
    if chip:
        js.append(f'tl.fromTo("#ch{n}", {{scale:0.8}}, {{scale:1, duration:{T(8 * F)}, ease:"back.out(1.25)", immediateRender:false}}, {T(t0)});')
        cue("pop_notification", t0, 0.3)
        d = 4 * F
    js.append(f'tl.fromTo("#h{n}a", {{yPercent:110}}, {{yPercent:0, duration:{T(10 * F)}, ease:"power3.out", immediateRender:false}}, {T(t0 + d)});')
    js.append(f'tl.fromTo("#h{n}b", {{yPercent:110}}, {{yPercent:0, duration:{T(10 * F)}, ease:"power3.out", immediateRender:false}}, {T(t0 + d + 6 * F)});')

# ------------------------------------------------------------------ S3 stat card ("বুকিং", "মিসড কল")
tb, tm = w(3, "বুকিং"), w(3, "মিসড")
html.append('<div id="stat"><div class="sl" id="st1">📅 মাসে কয়টা বুকিং?</div><div class="sl" id="st2">📞 কয়টা মিসড কল?</div></div>')
js.append(f'tl.fromTo("#stat", {{autoAlpha:0, scale:0.8}}, {{autoAlpha:1, scale:1, duration:{T(8 * F)}, ease:"back.out(1.6)"}}, {T(tb)});')
js.append(f'tl.fromTo("#st1", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.01}}, {T(tb)});')
js.append(f'tl.fromTo("#st2", {{autoAlpha:0, y:16}}, {{autoAlpha:1, y:0, duration:{T(6 * F)}, ease:"power2.out"}}, {T(tm)});')
js.append(f'tl.set("#stat", {{autoAlpha:0}}, {T(nxt(3))});')
cue("pop_notification", tb, 0.3)
cue("click_ui", tm, 0.3)

# ------------------------------------------------------------------ persistent CTA pill (S2 start -> S5 start)
html.append('<div id="cpill">কমেন্টে <b class="sora">CLINIC</b> লিখুন → ফ্রি চেক</div>')
js.append(f'tl.fromTo("#cpill", {{autoAlpha:1, x:-1000}}, {{x:0, duration:{T(8 * F)}, ease:"power3.out", immediateRender:false}}, {T(st(2) + 0.2)});')
# S4: the woman's face sits under the headline panel and the pill would land on her chin -> pill moves to just
# above the subtitles (subtitle box top >= 1470 for 2 lines; pill 50 px tall + 16 px gap), over the phone, no face
js.append(f'tl.set("#cpill", {{top:1404}}, {T(st(4))});')
for n in (3, 4):
    js.append(f'tl.fromTo("#cpill", {{scale:1}}, {{scale:1.04, duration:0.2, yoyo:true, repeat:1, ease:"sine.inOut", immediateRender:false}}, {T(st(n) + 0.35)});')
js.append(f'tl.to("#cpill", {{x:-1000, duration:{T(8 * F)}, ease:"power2.in"}}, {T(st(5))});')
js.append(f'tl.set("#cpill", {{autoAlpha:0}}, {T(st(5) + 8 * F)});')

# ------------------------------------------------------------------ S5 CTA caption boxes, one per phrase
caps = [("কমেন্টে", 'কমেন্টে <b class="sora blue">CLINIC</b> লিখুন'), ("ফ্রিতে", "ফ্রি চেক পান"), ("কতজন", "কতজন রোগী হারাচ্ছেন")]
html.append('<div id="ctas">' + "".join(f'<div class="cbox" id="cb{i}">{t}</div>' for i, (_, t) in enumerate(caps)) + '</div>')
for i, (wd, _) in enumerate(caps):
    t = max(w(5, wd), st(5) + 8 * F) if i == 0 else w(5, wd)
    js.append(f'tl.fromTo("#cb{i}", {{autoAlpha:0, scale:0.8}}, {{autoAlpha:1, scale:1, duration:{T(8 * F)}, ease:"back.out(1.7)"}}, {T(t)});')
    cue("pop_notification", t, 0.32)
js.append(f'tl.set("#ctas", {{autoAlpha:0}}, {T(nxt(5))});')

# ------------------------------------------------------------------ subtitles
NUMWORDS = {"এক", "দুই", "তিন", "চার", "পাঁচ", "ছয়", "সাত", "আট", "নয়", "দশ", "৩টা"}


def chunks(ws):
    """Split at commas/full stops; long phrases split into balanced parts of <= 7 words (no 1-word orphans);
    a number never ends a chunk (৩টা শিক্ষা, পাঁচ মিনিটে stay together)."""
    phrases, cur = [], []
    for x in ws:
        cur.append(x)
        if x["text"][-1] in "।,?:!":
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    out = []
    for ph in phrases:
        n = len(ph)
        parts = -(-n // 7)
        size = -(-n // parts)
        i = 0
        while i < n:
            j = min(n, i + size)
            while j < n and (any(c in "০১২৩৪৫৬৭৮৯" for c in ph[j - 1]["text"]) or ph[j - 1]["text"] in NUMWORDS):
                j += 1
            out.append(ph[i:j])
            i = j
    return out


cid = 0
subs = []
for n in (1, 2, 3, 4, 6):
    cs = chunks([x for x in WORDS if x["section"] == n])
    for j, ch in enumerate(cs):
        t0 = ch[0]["start"] - 0.03
        t1 = cs[j + 1][0]["start"] - 0.03 if j + 1 < len(cs) else min(nxt(n), CARD)
        text = " ".join(x["text"] for x in ch).replace(" —", "")
        subs.append(f'<div class="sub" id="s{cid}"><span class="sbox">{text}</span></div>')
        js.append(f'tl.set("#s{cid}", {{visibility:"visible"}}, {T(t0)});')
        js.append(f'tl.fromTo("#s{cid} .sbox", {{clipPath:"inset(100% 0% 0% 0%)", y:18}}, {{clipPath:"inset(0% 0% 0% 0%)", y:0, duration:{T(5 * F)}, ease:"power2.out", immediateRender:false}}, {T(t0)});')
        js.append(f'tl.set("#s{cid}", {{visibility:"hidden"}}, {T(t1)});')
        cid += 1

# ------------------------------------------------------------------ persistent: progress bar + logo tile
html.append('<div id="prog"></div><div id="ltile"><img src="logo.png" alt="FutureStack Solutions" /></div>')
js.append(f'tl.fromTo("#prog", {{scaleX:0}}, {{scaleX:1, duration:{T(VO)}, ease:"none", immediateRender:false}}, 0);')
js.append(f'tl.set("#ltile", {{autoAlpha:0}}, {T(CARD)});')

# ------------------------------------------------------------------ end card
wa = ""
html.append(f'''<div id="card"><img id="elogo" src="logo.png" alt="FutureStack Solutions" />
<div class="ei" id="e1"><span class="blue">কাজ করুক এআই,</span><br><span class="ink">বাড়ুক আপনার ব্যবসা।</span></div>
<div class="ei" id="e2">স্মার্ট ব্যবসার পেছনে, <span class="blue">ফিউচার স্ট্যাক</span></div>
<div id="e3"></div>
<div class="ei" id="e4">যোগাযোগ করুন</div>
<div class="ei" id="e5">+880 1632-932249</div>
<div class="ei" id="e6"><span>এখনই কল বা হোয়াটসঅ্যাপ করুন</span></div></div>''')
js.append(f'tl.fromTo("#card", {{autoAlpha:1, yPercent:100}}, {{yPercent:0, duration:{T(10 * F)}, ease:"expo.out", immediateRender:false}}, {T(CARD)});')
js.append(f'tl.fromTo("#elogo", {{opacity:0, scale:0.92}}, {{opacity:1, scale:1, duration:{T(12 * F)}, ease:"power2.out", immediateRender:false}}, {T(CARD + 10 * F)});')
t = CARD + 10 * F + 0.3
for i, sel in enumerate(("#e1", "#e2", "#e3", "#e4", "#e5", "#e6")):
    ti = t + i * 0.35
    if sel == "#e3":
        js.append(f'tl.fromTo("#e3", {{scaleX:0}}, {{scaleX:1, duration:0.35, ease:"power2.out", immediateRender:false}}, {T(ti)});')
    else:
        js.append(f'tl.fromTo("{sel}", {{clipPath:"inset(100% 0% 0% 0%)", y:30}}, {{clipPath:"inset(0% 0% 0% 0%)", y:0, duration:0.3, ease:"power3.out", immediateRender:false}}, {T(ti)});')
t6 = t + 5 * 0.35 + 0.3
k = 0
while t6 + k * 1.2 + 1.2 <= TOTAL:
    js.append(f'tl.fromTo("#e6", {{scale:1}}, {{scale:1.04, duration:0.6, yoyo:true, repeat:1, ease:"sine.inOut", immediateRender:false}}, {T(t6 + k * 1.2)});')
    k += 1
cue("chime_success", CARD + 0.1, 0.35)
cue("pop_notification", t + 5 * 0.35, 0.3)

FONTS = "".join(f'@font-face {{ font-family:"Hind Siliguri"; src:url(fonts/hind-siliguri-bengali-{wt}-normal.woff2) format("woff2"); font-weight:{wt}; font-display:block; unicode-range:U+0980-09FE,U+200C-200D,U+25CC; }}\n'
                f'@font-face {{ font-family:"Hind Siliguri"; src:url(fonts/hind-siliguri-latin-{wt}-normal.woff2) format("woff2"); font-weight:{wt}; font-display:block; unicode-range:U+0000-00FF,U+2000-206F,U+2190-22FF; }}\n'
                for wt in (500, 600, 700))
CSS = FONTS + f"""
@font-face {{ font-family:"Sora"; src:url(fonts/sora-latin-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; }}
@font-face {{ font-family:"Instrument Sans"; src:url(fonts/instrument-sans-latin-600-normal.woff2) format("woff2"); font-weight:600; font-display:block; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:{WHITE}; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:{WHITE}; color:{INK}; font-family:"Hind Siliguri","Instrument Sans",sans-serif; }}
.shot {{ position:absolute; inset:0; opacity:0; overflow:hidden; }}
.mv {{ position:absolute; inset:0; }}
.mv video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
#flash {{ position:absolute; inset:0; background:{WHITE}; opacity:0; z-index:20; pointer-events:none; }}
.sora {{ font-family:"Sora","Instrument Sans",sans-serif; font-weight:700; }}
.lat {{ font-family:"Sora","Instrument Sans",sans-serif; font-weight:700; }}
.blue {{ color:{BLUE}; }} .ink {{ color:{INK}; }}
.hblock {{ position:absolute; left:72px; top:180px; max-width:936px; z-index:30; visibility:hidden; }}
.chip {{ position:absolute; left:0; bottom:calc(100% + 16px); background:{BLUE}; color:{WHITE}; font-weight:700; font-size:40px; line-height:1;
  padding:14px 28px 8px; border-radius:999px; transform-origin:0% 100%; }}
.panel {{ display:inline-block; background:rgba(255,255,255,.92); border-radius:20px; padding:24px 32px; box-shadow:0 8px 24px rgba(11,13,17,0.12); }}
.ln {{ overflow:hidden; font-weight:700; font-size:84px; line-height:1.25; white-space:nowrap; }}
.ln span {{ display:inline-block; }}
.l1 {{ color:{INK}; }} .l2 {{ color:{BLUE}; }}
#stat {{ position:absolute; right:72px; top:560px; z-index:31; visibility:hidden; background:{WHITE}; border-radius:20px; padding:20px 28px 14px;
  box-shadow:0 8px 24px rgba(11,13,17,0.12); border-left:6px solid {BLUE}; transform-origin:100% 0%; }}
.sl {{ font-weight:700; font-size:44px; line-height:1.4; color:{INK}; visibility:hidden; font-family:"Hind Siliguri","Instrument Sans",sans-serif; }}
#cpill {{ position:absolute; left:72px; top:454px; z-index:31; visibility:hidden; background:{BLUE}; color:{WHITE}; font-weight:600; font-size:30px;
  padding:12px 28px 6px; border-radius:999px; transform-origin:0% 50%; }}
#cpill .sora {{ font-size:28px; }}
#ctas {{ position:absolute; left:0; width:100%; top:560px; z-index:32; display:flex; flex-direction:column; align-items:center; gap:12px; }}
.cbox {{ visibility:hidden; background:{WHITE}; color:{INK}; border-radius:16px; padding:10px 24px 2px; font-weight:700; font-size:60px; line-height:1.35;
  box-shadow:0 8px 24px rgba(11,13,17,0.12); }}
.cbox .sora {{ font-size:56px; }}
.sub {{ position:absolute; left:90px; width:900px; bottom:300px; z-index:35; text-align:center; visibility:hidden; }}
.sbox {{ position:relative; display:inline-block; max-width:900px; background:{INK}; color:{WHITE}; font-weight:600; font-size:46px; line-height:1.45;
  padding:10px 20px 6px 28px; border-radius:14px; }}
.sbox::before {{ content:""; position:absolute; left:0; top:10px; bottom:10px; width:4px; border-radius:2px; background:{BLUE}; }}
#prog {{ position:absolute; left:0; top:0; width:1080px; height:6px; background:{BLUE}; transform-origin:0% 50%; z-index:60; }}
#ltile {{ position:absolute; right:48px; top:48px; z-index:40; background:{WHITE}; border-radius:14px; padding:8px 12px; box-shadow:0 4px 12px rgba(11,13,17,0.10); }}
#ltile img {{ height:56px; display:block; }}
#card {{ position:absolute; inset:0; z-index:70; visibility:hidden; background:{WHITE}; display:flex; flex-direction:column; align-items:center; text-align:center; padding-top:420px; }}
#elogo {{ width:700px; display:block; }}
#e1 {{ margin-top:30px; font-weight:700; font-size:54px; line-height:1.3; max-width:900px; }}
#e2 {{ margin-top:18px; font-weight:600; font-size:34px; color:{MUTED}; }}
#e3 {{ margin-top:22px; width:520px; height:2px; background:{BLUE}; transform-origin:50% 50%; }}
#e4 {{ margin-top:20px; font-weight:700; font-size:64px; color:{INK}; line-height:1.2; }}
#e5 {{ margin-top:6px; font-family:"Sora","Instrument Sans",sans-serif; font-weight:700; font-size:72px; color:{BLUE}; line-height:1.2; }}
#e6 {{ margin-top:20px; background:{CTA}; color:{WHITE}; border-radius:999px; padding:16px 44px 10px; font-weight:600; font-size:30px; }}
"""

shots = html[:6]
rest = html[6:]
page = f"""<!doctype html>
<html lang="bn"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<title>Clinic Reel</title><style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="1080" data-height="1920">
{chr(10).join(shots)}
<div id="flash"></div>
{chr(10).join(rest)}
{chr(10).join(subs)}
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
(B / "sfx.json").write_text(json.dumps(sorted(sfx, key=lambda x: x["t"]), indent=1))
print(f"built index.html {TOTAL:.2f}s, {cid} subtitle chunks, {len(sfx)} sfx")
