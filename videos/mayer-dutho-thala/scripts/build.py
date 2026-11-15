#!/usr/bin/env python3
"""মায়ের দুটো থালা -> index.html (HyperFrames 0.9.23: data-start/duration/media-start, class="clip", one paused GSAP
timeline on window.__timelines["main"]). Times from build/timeline.json (prep.py)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "build/timeline.json").read_text(encoding="utf-8"))
CLIPS, LINES, TOTAL, END = TL["clips"], TL["lines"], TL["total"], TL["end_card"]
GOLD = "#F2C46B"
T = lambda x: f"{x:.3f}"
html, js = [], []

# ------------------------------------------------------------------ clips: crossfade 0.4 s (centred on the cut), dip to black 4->5
for c in CLIPS:
    n = c["n"]
    pre = 0.0 if n in (1, 5) else 0.2            # incoming clip starts 0.2 s early so the 0.4 s crossfade is centred on the line start
    t0 = max(0.0, c["start"] - pre)
    t1 = min(TOTAL, c["end"] + (0.2 if n < 6 else 0.0) + (0.3 if n == 4 else 0.0))
    html.append(f'<div class="shot" id="sh{n}" style="z-index:{n}"><div class="mv" id="mv{n}" data-layout-allow-overflow><video id="v{n}" class="clip" src="build/c{n}.mp4" muted playsinline '
                f'data-start="{T(t0)}" data-duration="{T(t1 - t0)}" data-media-start="0" data-track-index="{n}"></video></div></div>')
    js.append(f'tl.fromTo("#mv{n}", {{scale:1.0}}, {{scale:1.06, duration:{T(t1 - t0)}, ease:"none", immediateRender:false}}, {T(t0)});')   # Ken Burns
    if n == 1:
        js.append('tl.set("#sh1", {opacity:1}, 0);')
    elif n == 5:                                   # dip to black 0.6 s: black up over 0.3, cut, black down over 0.3
        t = c["start"]
        js.append(f'tl.fromTo("#black", {{opacity:0}}, {{opacity:1, duration:0.3, ease:"power1.in", immediateRender:false}}, {T(t - 0.3)});')
        js.append(f'tl.set("#sh5", {{opacity:1}}, {T(t)}); tl.set("#sh4", {{opacity:0}}, {T(t)});')
        js.append(f'tl.to("#black", {{opacity:0, duration:0.3, ease:"power1.out"}}, {T(t)});')
    else:
        js.append(f'tl.fromTo("#sh{n}", {{opacity:0}}, {{opacity:1, duration:0.4, ease:"none", immediateRender:false}}, {T(c["start"] - 0.2)});')
        js.append(f'tl.set("#sh{n - 1}", {{opacity:0}}, {T(c["start"] + 0.2)});')
# fade from black over the first 0.5 s
js.append('tl.fromTo("#black", {opacity:1}, {opacity:0, duration:0.5, ease:"power1.out", immediateRender:false}, 0);')

# ------------------------------------------------------------------ captions: one short phrase at a time
caps = TL["captions"]
merged = []
pending = None                                     # phrases under 0.8 s join the NEXT phrase on the same line, else the previous one
for i, c in enumerate(caps):
    c = dict(c)
    if pending:
        c["text"], c["start"] = pending["text"] + " " + c["text"], pending["start"]
        pending = None
    nxt_same = i + 1 < len(caps) and caps[i + 1]["line"] == c["line"]
    if c["end"] - c["start"] < 0.8 and nxt_same:
        pending = c
    elif c["end"] - c["start"] < 0.8 and merged and merged[-1]["line"] == c["line"]:
        merged[-1]["text"] += " " + c["text"]
        merged[-1]["end"] = c["end"]
    else:
        merged.append(c)
for i, c in enumerate(merged):
    t0 = c["start"] - 0.05
    nxt = merged[i + 1]["start"] - 0.05 if i + 1 < len(merged) else END
    same_line_next = i + 1 < len(merged) and merged[i + 1]["line"] == c["line"]
    t1 = nxt if same_line_next else min(nxt, c["end"] + 0.6)
    text = c["text"].replace("আম্মু।", '<span class="gold">আম্মু।</span>').replace("মাকে ফোন করেছেন?", '<span class="gold">মাকে ফোন করেছেন?</span>')
    html.append(f'<div class="cap" id="cap{i}"><span>{text}</span></div>')
    js.append(f'tl.fromTo("#cap{i}", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.2, ease:"none"}}, {T(t0)});')
    js.append(f'tl.to("#cap{i}", {{autoAlpha:0, duration:0.2, ease:"none"}}, {T(t1 - 0.2)});')

# ------------------------------------------------------------------ end card: darkened final frame + text, then fade to black
html.append('<div id="dark"></div><div id="endtxt">আজই মাকে<br>একটা ফোন করুন</div>')
js.append(f'tl.fromTo("#dark", {{opacity:0}}, {{opacity:0.55, duration:0.4, ease:"power1.out", immediateRender:false}}, {T(END)});')
js.append(f'tl.fromTo("#endtxt", {{autoAlpha:0, y:16}}, {{autoAlpha:1, y:0, duration:0.4, ease:"power2.out"}}, {T(END + 0.1)});')
js.append(f'tl.to("#black", {{opacity:1, duration:0.5, ease:"power1.in"}}, {T(TOTAL - 0.5)});')

CSS = f"""
@font-face {{ font-family:"Noto Sans Bengali"; src:url(fonts/noto-sans-bengali-bengali-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; unicode-range:U+0951-0952,U+0964-0965,U+0980-09FE,U+1CD0,U+1CD2,U+1CD5-1CD6,U+1CD8,U+1CE1,U+1CEA,U+1CED,U+1CF2,U+1CF5-1CF7,U+200C-200D,U+20B9,U+25CC,U+A8F1; }}
@font-face {{ font-family:"Noto Sans Bengali"; src:url(fonts/noto-sans-bengali-latin-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; unicode-range:U+0000-00FF,U+2000-206F; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#000; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#000; font-family:"Noto Sans Bengali", sans-serif; }}
.shot {{ position:absolute; inset:0; opacity:0; overflow:hidden; }}
.mv {{ position:absolute; inset:0; }}
.mv video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; filter:sepia(.12) saturate(1.08) brightness(.98) contrast(1.03); }}
#warm {{ position:absolute; inset:0; z-index:10; background:rgba(255,170,90,.06); mix-blend-mode:soft-light; pointer-events:none; }}
#vig {{ position:absolute; inset:0; z-index:11; pointer-events:none; background:radial-gradient(ellipse 75% 62% at 50% 48%, rgba(0,0,0,0) 55%, rgba(0,0,0,.5) 100%); }}
.cap {{ position:absolute; left:90px; width:900px; bottom:250px; z-index:30; text-align:center; visibility:hidden; }}
.cap span {{ display:inline-block; color:#fff; font-weight:700; font-size:58px; line-height:1.4;
  text-shadow:0 2px 6px rgba(0,0,0,.75), 0 4px 22px rgba(0,0,0,.55); }}
.cap .gold {{ color:{GOLD}; font-size:1.15em; display:inline; }}
#dark {{ position:absolute; inset:0; z-index:40; background:#000; opacity:0; }}
#endtxt {{ position:absolute; left:90px; width:900px; top:50%; translate:0 -50%; z-index:41; text-align:center; visibility:hidden;
  color:#fff; font-weight:700; font-size:76px; line-height:1.35; text-shadow:0 4px 24px rgba(0,0,0,.6); }}
#black {{ position:absolute; inset:0; z-index:60; background:#000; opacity:1; pointer-events:none; }}
"""
shots = html[:6]
rest = html[6:]
page = f"""<!doctype html>
<html lang="bn"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<title>মায়ের দুটো থালা</title><style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="1080" data-height="1920">
{chr(10).join(shots)}
<div id="warm"></div><div id="vig"></div>
{chr(10).join(rest)}
<div id="black"></div>
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
print(f"built index.html {TOTAL:.2f}s, {len(merged)} captions")
for c in merged:
    print(f"  {c['start']:6.2f} L{c['line']} {c['text']}")
