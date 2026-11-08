#!/usr/bin/env python3
"""WARMLUNE Reels ad -> index.html (HyperFrames composition, 1080x1920).

  python3 scripts/voice.py && python3 scripts/words.py && python3 scripts/build.py

Scenes follow timing.json (voice-driven grid); captions follow words.json (one <span> per word, never per character).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1920
T = json.loads((ROOT / "timing.json").read_text())
WORDS = json.loads((ROOT / "words.json").read_text(encoding="utf-8"))
TOTAL = T["total"]
SC = {s["n"]: s for s in T["scenes"]}
XF = 0.4      # crossfade length (centred on each cut)
FLASH = 0.5   # 3 -> 4 warm-pink flash
PINK = "#F7A8C4"

# camera per scene: (scale from, scale to, transform-origin, x drift px, y drift px)
CAM = {
    1: (1.00, 1.12, "50% 28%", 0, 18),      # slow push toward her face
    2: (1.00, 1.12, "36% 42%", 24, 0),      # push, anchored left of centre (different from 1)
    3: (1.12, 1.00, "50% 40%", -20, 0),     # slow pull-out
    4: (1.12, 1.00, "50% 46%", 0, 46),      # pull back + rise (product travels up)
    5: (1.00, 1.12, "46% 40%", -28, -22),   # diagonal push toward the LCD
    6: (1.00, 1.08, "50% 38%", 0, 12),      # gentle push
    7: (1.12, 1.00, "50% 34%", 0, 0),       # slow pull-back
    8: (1.06, 1.00, "50% 62%", 0, 0),       # slow settle, product stays low; top 35% free for the end card
}
# caption vertical centre (fraction of height), chosen from snapshot frames to stay off faces and the product:
# 1-5 sit in the requested 62-70% band. In 6-7 the worn belt passes through that band, so the caption moves up to
# the chest (48%, below the face). In 8 the product fills 40-85%, so it sits at 35.5%, between the end card
# (top 30%) and the product.
CAP_Y = {1: 0.66, 2: 0.66, 3: 0.66, 4: 0.66, 5: 0.66, 6: 0.48, 7: 0.48, 8: 0.355}


def chunks(words):
    """2-4 word caption chunks, split at the script's phrase breaks."""
    phrases, cur = [], []
    for w in words:
        cur.append(w)
        if w["break"]:
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    # a 1-word phrase joins its neighbour when the result stays <= 4 words
    merged = []
    for p in phrases:
        if merged and (len(p) == 1 or len(merged[-1]) == 1) and len(merged[-1]) + len(p) <= 4:
            merged[-1] = merged[-1] + p
        else:
            merged.append(p)
    out = []
    for p in merged:
        n = len(p)
        if n <= 4:
            out.append(p)
            continue
        k = -(-n // 4)  # number of chunks
        sizes = [n // k + (1 if i < n % k else 0) for i in range(k)]
        i = 0
        for s in sizes:
            out.append(p[i:i + s])
            i += s
    return out


def main():
    js, html = [], []
    # ---- scenes -------------------------------------------------------------------------------------------------
    for n in range(1, 9):
        s = SC[n]
        a = max(0.0, s["start"] - (XF / 2 if n not in (1, 4) else 0))
        b = min(TOTAL, s["start"] + s["length"] + (XF / 2 if n not in (3, 8) else 0))
        grade = "cool" if n <= 3 else "warm"
        html.append(f'''
  <div class="scene" id="s{n}" style="z-index:{n}">
    <div class="cam" id="cam{n}"><video id="v{n}" class="clip" src="assets/clips/scene{n}.mp4" muted playsinline
      data-start="{a:.3f}" data-duration="{b - a:.3f}" data-media-start="0" data-track-index="{n}"></video></div>
    <div class="grade {grade}"></div>
  </div>''')
        f0, f1, origin, dx, dy = CAM[n]
        js.append(f'tl.fromTo("#cam{n}", {{scale:{f0}, x:0, y:0, transformOrigin:"{origin}"}}, '
                  f'{{scale:{f1}, x:{dx}, y:{dy}, duration:{b - a:.3f}, ease:"power1.inOut"}}, {a:.3f});')
        # visibility: hidden outside the window, crossfade in with a little blur (not after the 3->4 flash)
        js.append(f'tl.set("#s{n}", {{autoAlpha:0}}, 0);')
        if n == 1 or n == 4:
            js.append(f'tl.set("#s{n}", {{autoAlpha:1}}, {a:.3f});')
        else:
            js.append(f'tl.fromTo("#s{n}", {{autoAlpha:0, filter:"blur(6px)"}}, {{autoAlpha:1, filter:"blur(0px)", '
                      f'duration:{XF}, ease:"sine.inOut"}}, {a:.3f});')
        if n < 8 and n != 3:  # outgoing scene blurs slightly under the incoming one
            js.append(f'tl.fromTo("#s{n}", {{filter:"blur(0px)"}}, {{filter:"blur(6px)", duration:{XF}, '
                      f'ease:"sine.inOut", immediateRender:false}}, {b - XF:.3f});')
        js.append(f'tl.set("#s{n}", {{autoAlpha:0}}, {b:.3f});')
    # 3 -> 4: soft warm-pink light flash over the cut
    cut = SC[4]["start"]
    js.append(f'tl.fromTo("#flash", {{opacity:0}}, {{opacity:0.85, duration:{FLASH * 0.4:.2f}, ease:"sine.in"}}, {cut - FLASH * 0.4:.3f});')
    js.append(f'tl.to("#flash", {{opacity:0, duration:{FLASH * 0.6:.2f}, ease:"sine.out"}}, {cut:.3f});')
    # scene 4 light sweep across the product
    s4 = SC[4]["start"]
    js.append(f'tl.fromTo("#sweep", {{x:-900}}, {{x:1300, duration:1.8, ease:"sine.inOut"}}, {s4 + 0.9:.3f});')
    js.append(f'tl.fromTo("#sweep", {{opacity:0}}, {{opacity:1, duration:0.4, ease:"sine.out"}}, {s4 + 0.9:.3f});')
    js.append(f'tl.to("#sweep", {{opacity:0, duration:0.4, ease:"sine.in"}}, {s4 + 2.3:.3f});')

    # ---- captions -----------------------------------------------------------------------------------------------
    by_scene = {}
    for w in WORDS:
        by_scene.setdefault(w["scene"], []).append(w)
    cap_html, sync = [], []
    cid = 0
    for n in range(1, 9):
        cs = chunks(by_scene[n])
        scene_end = SC[n]["start"] + SC[n]["length"]
        for j, ch in enumerate(cs):
            t0 = max(SC[n]["start"], ch[0]["start"] - 0.12)
            nxt = cs[j + 1][0]["start"] - 0.12 if j + 1 < len(cs) else scene_end - 0.05
            t1 = min(nxt, max(ch[-1]["end"] + 0.25, t0 + 0.6), scene_end - 0.05)
            spans = []
            for k, w in enumerate(ch):
                spans.append(f'<span class="w" id="c{cid}w{k}">{w["text"]}</span>')
            cap_html.append(f'<div class="cap" id="c{cid}" style="top:{CAP_Y[n] * H:.0f}px">{" ".join(spans)}</div>')
            if n <= 3:  # calm: soft fade / rise
                js.append(f'tl.fromTo("#c{cid}", {{autoAlpha:0, y:18}}, {{autoAlpha:1, y:0, duration:0.3, ease:"power2.out"}}, {t0:.3f});')
            else:       # snappier pop
                js.append(f'tl.fromTo("#c{cid}", {{autoAlpha:0, scale:0.86}}, {{autoAlpha:1, scale:1, duration:0.2, ease:"back.out(2.2)"}}, {t0:.3f});')
            js.append(f'tl.to("#c{cid}", {{autoAlpha:0, duration:0.15, ease:"power1.in"}}, {t1 - 0.15:.3f});')
            for k, w in enumerate(ch):
                ws, we = w["start"], min(w["end"], t1 - 0.15)
                js.append(f'tl.fromTo("#c{cid}w{k}", {{color:"#FFFFFF", scale:1}}, {{color:"{PINK}", scale:1.08, duration:0.08, '
                          f'ease:"power2.out", immediateRender:false}}, {ws:.3f});')
                if k + 1 < len(ch):  # back to white when the next word lights up
                    js.append(f'tl.to("#c{cid}w{k}", {{color:"#FFFFFF", scale:1, duration:0.1, ease:"power1.out"}}, {ch[k + 1]["start"]:.3f});')
                sync.append((w["text"], ws))
            cid += 1

    # ---- graphics -----------------------------------------------------------------------------------------------
    s4, s5, s6, s8 = (SC[k]["start"] for k in (4, 5, 6, 8))
    end4, end5, end6 = (SC[k]["start"] + SC[k]["length"] for k in (4, 5, 6))
    js.append(f'tl.fromTo("#meet", {{autoAlpha:0, y:14}}, {{autoAlpha:1, y:0, duration:0.9, ease:"power2.out"}}, {s4 + 0.5:.3f});')
    js.append(f'tl.to("#meet", {{autoAlpha:0, duration:0.3}}, {end4 - 0.3:.3f});')
    w5 = by_scene[5]
    for k, idx in enumerate((0, 3, 6)):  # তিনটি / LCD / ভাইব্রেশন
        js.append(f'tl.fromTo("#chip{k}", {{autoAlpha:0, scale:0.6}}, {{autoAlpha:1, scale:1, duration:0.28, ease:"back.out(2.4)"}}, {w5[idx]["start"]:.3f});')
    js.append(f'tl.to(".chip5", {{autoAlpha:0, duration:0.25}}, {end5 - 0.3:.3f});')
    w6 = by_scene[6]
    js.append(f'tl.fromTo("#chip6", {{autoAlpha:0, scale:0.6}}, {{autoAlpha:1, scale:1, duration:0.28, ease:"back.out(2.4)"}}, {w6[1]["start"]:.3f});')
    js.append(f'tl.to("#chip6", {{autoAlpha:0, duration:0.25}}, {end6 - 0.3:.3f});')
    ec = TOTAL - 3.0
    js.append(f'tl.fromTo("#logo", {{autoAlpha:0, scale:0.94}}, {{autoAlpha:1, scale:1, duration:1.0, ease:"power2.out"}}, {ec:.3f});')
    js.append(f'tl.fromTo("#tagline", {{autoAlpha:0, y:12}}, {{autoAlpha:1, y:0, duration:0.7, ease:"power2.out"}}, {ec + 0.45:.3f});')
    js.append(f'tl.fromTo("#cta", {{autoAlpha:0, scale:0.8}}, {{autoAlpha:1, scale:1, duration:0.35, ease:"back.out(2)"}}, {ec + 0.9:.3f});')
    for p in range(2):  # two gentle pulses
        js.append(f'tl.to("#cta", {{scale:1.07, duration:0.3, ease:"sine.inOut", yoyo:true, repeat:1}}, {ec + 1.4 + p * 0.75:.3f});')

    css = f"""
@font-face {{ font-family:"Noto Sans Bengali"; src:url(assets/fonts/noto-bengali.woff2) format("woff2"); font-weight:400 800; font-display:block; }}
@font-face {{ font-family:"Cormorant"; src:url(assets/fonts/cormorant-garamond-latin-300-normal.woff2) format("woff2"); font-weight:300; font-display:block; }}
@font-face {{ font-family:"Cormorant"; src:url(assets/fonts/cormorant-garamond-latin-500-normal.woff2) format("woff2"); font-weight:500; font-display:block; }}
@font-face {{ font-family:"Cormorant"; src:url(assets/fonts/cormorant-garamond-latin-400-italic.woff2) format("woff2"); font-weight:400; font-style:italic; font-display:block; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:#1b1416; }}
#root {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; }}
.scene {{ position:absolute; inset:0; overflow:hidden; visibility:hidden; }}
.cam {{ position:absolute; inset:0; will-change:transform; }}
.cam video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
.grade {{ position:absolute; inset:0; pointer-events:none; }}
.grade.cool {{ background:linear-gradient(180deg, rgba(150,175,215,.20), rgba(120,140,185,.16)); mix-blend-mode:soft-light; backdrop-filter:saturate(.78); }}
.grade.warm {{ background:radial-gradient(900px 1100px at 55% 45%, rgba(255,196,214,.30), rgba(247,168,196,.14) 60%, rgba(255,214,190,.12));
  mix-blend-mode:soft-light; backdrop-filter:saturate(1.06); }}
#flash {{ position:absolute; inset:0; z-index:20; opacity:0; pointer-events:none;
  background:radial-gradient(800px 1000px at 50% 48%, #FFF1F5 0%, #FFD3E1 45%, #F7A8C4 100%); }}
#sweep {{ position:absolute; top:-200px; left:0; width:360px; height:2400px; z-index:5; opacity:0; pointer-events:none; transform:rotate(18deg);
  background:linear-gradient(90deg, rgba(255,255,255,0), rgba(255,245,248,.38), rgba(255,255,255,0)); mix-blend-mode:screen; }}
.cap {{ position:absolute; left:{0.05 * W:.0f}px; width:{0.80 * W:.0f}px; transform-origin:50% 50%; translate:0 -50%; z-index:30;
  text-align:center; font-family:"Noto Sans Bengali", sans-serif; font-weight:700; font-size:66px; line-height:1.35; color:#fff;
  -webkit-text-stroke:7px rgba(52,14,30,.62); paint-order:stroke fill;
  text-shadow:0 3px 16px rgba(25,8,16,.6), 0 1px 3px rgba(25,8,16,.7); visibility:hidden; }}
.w {{ display:inline-block; transform-origin:50% 60%; }}
#meet {{ position:absolute; top:{0.115 * H:.0f}px; left:0; width:100%; text-align:center; z-index:30; visibility:hidden;
  font-family:"Cormorant", serif; font-weight:500; font-size:76px; letter-spacing:.02em; color:#5A2236;
  text-shadow:0 1px 14px rgba(255,240,244,.7); }}
.chip {{ position:absolute; left:50%; translate:-50% 0; z-index:30; visibility:hidden; white-space:nowrap;
  background:#fff; color:#D9668F; border-radius:999px; padding:18px 44px 16px; font-family:"Cormorant", serif; font-weight:500;
  font-size:50px; letter-spacing:.02em; box-shadow:0 12px 34px -10px rgba(120,40,70,.35); }}
#logo {{ position:absolute; top:{0.085 * H:.0f}px; left:0; width:100%; text-align:center; z-index:30; visibility:hidden;
  font-family:"Cormorant", serif; font-weight:500; font-size:104px; letter-spacing:.34em; text-indent:.34em; color:#5A2236;
  text-shadow:0 1px 18px rgba(255,240,244,.75); }}
#logo sup {{ font-size:.32em; letter-spacing:0; vertical-align:2.1em; }}
#tagline {{ position:absolute; top:{0.165 * H:.0f}px; left:0; width:100%; text-align:center; z-index:30; visibility:hidden;
  font-family:"Cormorant", serif; font-style:italic; font-weight:400; font-size:52px; color:#6E3348; text-shadow:0 1px 12px rgba(255,240,244,.8); }}
#cta {{ position:absolute; top:{0.235 * H:.0f}px; left:50%; translate:-50% 0; z-index:30; visibility:hidden; white-space:nowrap;
  background:{PINK}; color:#4A1A2C; border-radius:999px; padding:22px 56px 20px; font-family:"Noto Sans Bengali", sans-serif;
  font-weight:700; font-size:50px; box-shadow:0 16px 40px -12px rgba(160,50,90,.55); display:flex; align-items:center; gap:18px; }}
#cta svg {{ width:50px; height:50px; }}
"""
    chat = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#4A1A2C" d="M12 3C6.5 3 2 6.8 2 11.5c0 2.4 1.2 4.6 3.1 6.1'
            'L4.4 21l3.9-1.9c1.2.4 2.4.6 3.7.6 5.5 0 10-3.8 10-8.5S17.5 3 12 3z"/></svg>')
    body = f"""<!doctype html>
<html lang="bn"><head><meta charset="UTF-8" /><meta name="viewport" content="width={W}, height={H}" />
<title>WARMLUNE Reels ad</title><style>{css}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="{W}" data-height="{H}">
{''.join(html)}
  <div id="sweep"></div>
  <div id="flash"></div>
  <div id="meet">Meet Your Comfort Companion</div>
  <div class="chip chip5" id="chip0" style="top:{0.115 * H:.0f}px">3 Heat Levels</div>
  <div class="chip chip5" id="chip1" style="top:{0.18 * H:.0f}px">LCD Display</div>
  <div class="chip chip5" id="chip2" style="top:{0.245 * H:.0f}px">Vibration Massage</div>
  <div class="chip" id="chip6" style="top:{0.115 * H:.0f}px">Cordless · Rechargeable</div>
  {''.join(cap_html)}
  <div id="logo">WARMLUNE<sup>™</sup></div>
  <div id="tagline">A Little Warmth, A Little More Comfort.</div>
  <div id="cta"><span>অর্ডার করতে ইনবক্স করো</span>{chat}</div>
  <audio id="mix" src="assets/mix.wav" data-start="0" data-duration="{TOTAL:.3f}" data-track-index="20"></audio>
</div>
<script src="assets/gsap.min.js"></script>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["main"] = tl;
</script>
</body></html>
"""
    (ROOT / "index.html").write_text(body, encoding="utf-8")
    (ROOT / "out" / "caption_sync.json").write_text(json.dumps(sync, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"built index.html: {TOTAL:.2f}s, {cid} caption chunks, {len(sync)} words")


if __name__ == "__main__":
    main()
