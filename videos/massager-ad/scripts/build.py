#!/usr/bin/env python3
"""Massager ad -> index.html: 10 x 3 s scenes, 0.3 s crossfades, 100->105 % zoom per scene, a caption per scene on a
semi-transparent black bar (Noto Sans Bengali 700, 64 px), WhatsApp + phone end card. Seek-safe GSAP, finite repeats."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "build/timeline.json").read_text())
S = TL["scenes"]
TOTAL = TL["total"]
PHONE = "01632932249"
CAPS = ["ঘাড়ে ব্যথা? 😩", "শরীরের যেকোনো জায়গায় কাজ করে ✅", "এই মিনি ম্যাসাজার দিয়ে সমাধান! 💪", "কভার খুলে লাগিয়ে নিন 🔧", "শুধু বসিয়ে দিন ⚡",
        "৮ মোড\u00a0| ১৯ লেভেল\u00a0| LCD ডিসপ্লে 🎛️", "ব্যথার অস্বস্তি আর না! 🚫", "ঘরে বসেই আরাম নিন 🛋️", "হাতে, পায়ে, পিঠে\u00a0— যেখানে খুশি 🎯", "অর্ডার করতে কল/WhatsApp করুন 📞"]
EMO = set("😩✅💪🔧⚡🎛🚫🛋🎯📞️")
T = lambda x: f"{x:.3f}"
html, js = [], []


def emo(t):
    out, buf = [], ""
    for ch in t:
        if ch in EMO:
            buf += ch
        else:
            if buf:
                out.append(f'<i class="emo">{buf}</i>')
                buf = ""
            out.append(ch)
    if buf:
        out.append(f'<i class="emo">{buf}</i>')
    return "".join(out)


for s in S:
    n = s["n"]
    html.append(f'<div class="shot" id="sh{n}" style="z-index:{n}"><div class="mv" id="mv{n}" data-layout-allow-overflow><video id="v{n}" class="clip" src="build/s{n}.mp4" '
                f'muted playsinline data-start="{T(s["clip_start"])}" data-duration="{T(s["clip_dur"])}" data-media-start="0" data-track-index="{n}"></video></div></div>')
    js.append(f'tl.fromTo("#mv{n}", {{scale:1.0}}, {{scale:1.05, duration:{T(s["clip_dur"])}, ease:"none", immediateRender:false}}, {T(s["clip_start"])});')
    if n == 1:
        js.append('tl.set("#sh1", {opacity:1}, 0);')
    else:
        js.append(f'tl.fromTo("#sh{n}", {{opacity:0}}, {{opacity:1, duration:0.3, ease:"none", immediateRender:false}}, {T(s["start"] - 0.15)});')
        js.append(f'tl.set("#sh{n - 1}", {{opacity:0}}, {T(s["start"] + 0.15)});')
    html.append(f'<div class="cap" id="cp{n}"><span>{emo(CAPS[n - 1])}</span></div>')
    a = s["start"] + (0.15 if n > 1 else 0.1)
    js.append(f'tl.fromTo("#cp{n}", {{autoAlpha:0, y:24}}, {{autoAlpha:1, y:0, duration:0.25, ease:"power2.out"}}, {T(a)});')
    if n < 10:
        js.append(f'tl.to("#cp{n}", {{autoAlpha:0, duration:0.15, ease:"none"}}, {T(s["end"] - 0.15)});')

# end card: WhatsApp icon + phone number
s10 = S[9]["start"]
WA = ('<svg viewBox="0 0 64 64" width="150" height="150"><circle cx="32" cy="32" r="31" fill="#25D366"/>'
      '<path d="M32 13c-10.5 0-19 8.3-19 18.6 0 3.6 1.1 7 2.9 9.8L13 51l9.9-2.9c2.7 1.5 5.8 2.3 9.1 2.3 10.5 0 19-8.3 19-18.6S42.5 13 32 13z" fill="#fff"/>'
      '<path d="M25.2 22.6c-.5-1.1-1-1.1-1.5-1.1h-1.3c-.4 0-1.2.2-1.8.8s-2.3 2.2-2.3 5.4 2.4 6.3 2.7 6.7c.3.4 4.6 7.2 11.3 9.8 5.6 2.2 6.7 1.8 7.9 1.7 '
      '1.2-.1 3.9-1.6 4.5-3.1.6-1.5.6-2.8.4-3.1-.2-.3-.6-.4-1.3-.8s-3.9-1.9-4.5-2.1c-.6-.2-1-.3-1.5.3-.4.6-1.7 2.1-2.1 2.6-.4.4-.8.5-1.4.2-.7-.3-2.8-1-5.3-3.3'
      '-2-1.7-3.3-3.9-3.7-4.5-.4-.7 0-1 .3-1.4.3-.3.7-.8 1-1.2.3-.4.4-.7.7-1.1.2-.4.1-.8 0-1.2-.2-.3-1.4-3.4-2-4.6z" fill="#25D366"/></svg>')
html.append(f'<div id="endcard"><div id="ecin"><div id="wa">{WA}</div><div id="num">{PHONE}</div><div id="sub">কল / WhatsApp</div></div></div>')
js.append(f'tl.fromTo("#endcard", {{autoAlpha:0, scale:0.6}}, {{autoAlpha:1, scale:1, duration:0.5, ease:"back.out(2.2)"}}, {T(s10 + 0.3)});')
reps = int((TOTAL - s10 - 1.0) / 0.9)
js.append(f'tl.fromTo("#ecin", {{scale:1}}, {{scale:1.05, duration:0.45, ease:"sine.inOut", yoyo:true, repeat:{reps * 2 - 1}, immediateRender:false}}, {T(s10 + 0.85)});')

CSS = """
@font-face { font-family:"Noto Sans Bengali"; src:url(fonts/noto-sans-bengali-bengali-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; unicode-range:U+0951-0952,U+0964-0965,U+0980-09FE,U+1CD0,U+1CD2,U+1CD5-1CD6,U+1CD8,U+1CE1,U+1CEA,U+1CED,U+1CF2,U+1CF5-1CF7,U+200C-200D,U+20B9,U+25CC,U+A8F1; }
@font-face { font-family:"Noto Sans Bengali"; src:url(fonts/noto-sans-bengali-latin-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; unicode-range:U+0000-00FF,U+2000-206F; }
@font-face { font-family:"Poppins"; src:url(fonts/poppins-latin-800-normal.woff2) format("woff2"); font-weight:800; font-display:block; unicode-range:U+0000-00FF,U+2000-206F; }
@font-face { font-family:"Ad Emoji"; src:url(fonts/emoji-subset.ttf) format("truetype"); font-display:block; }
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:#000; }
#root { position:relative; width:1080px; height:1920px; overflow:hidden; background:#000; font-family:"Noto Sans Bengali", sans-serif; color:#fff; }
.shot { position:absolute; inset:0; opacity:0; overflow:hidden; }
.mv { position:absolute; inset:0; }
.mv video { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }
.cap { position:absolute; left:60px; width:960px; bottom:250px; z-index:40; display:flex; justify-content:center; visibility:hidden; }
.cap span { display:inline-block; max-width:960px; padding:18px 40px 22px; border-radius:24px; background:rgba(0,0,0,.58); font-weight:700; font-size:64px;
  line-height:1.35; text-align:center; color:#fff; text-shadow:0 2px 8px rgba(0,0,0,.5); text-wrap:balance; }
.emo { font-style:normal; font-family:"Ad Emoji", sans-serif; }
#endcard { position:absolute; left:90px; width:900px; top:620px; z-index:45; visibility:hidden; }
#ecin { display:flex; flex-direction:column; align-items:center; gap:14px; padding:46px 30px 40px; border-radius:44px; background:rgba(0,0,0,.62);
  box-shadow:0 20px 60px rgba(0,0,0,.45); }
#wa { filter:drop-shadow(0 8px 20px rgba(37,211,102,.45)); }
#num { font-family:"Poppins", sans-serif; font-weight:800; font-size:112px; line-height:1.1; color:#fff; letter-spacing:2px; }
#sub { font-weight:700; font-size:52px; color:#25D366; }
"""
shots = [h for h in html if h.startswith('<div class="shot"')]
rest = [h for h in html if not h.startswith('<div class="shot"')]
out = f"""<!doctype html>
<html lang="bn" data-resolution="portrait"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<title>Mini Massager Ad</title><style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="1080" data-height="1920">
{chr(10).join(shots)}
{chr(10).join(rest)}
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
srt = []
fmt = lambda t: f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(round(t % 1 * 1000)):03d}"
for s, c in zip(S, CAPS):
    srt.append(f"{s['n']}\n{fmt(s['start'])} --> {fmt(s['end'])}\n{c.replace(chr(160), ' ')}\n")

(ROOT / "out").mkdir(exist_ok=True)
(ROOT / "out/captions.srt").write_text("\n".join(srt), encoding="utf-8")
print("built", TOTAL)
