#!/usr/bin/env python3
"""WarmLune 55 s Reels ad v2 -> index.html (HyperFrames, 1080x1920, fixed 10-scene timeline from the brief).

  python3 scripts/audio.py && python3 scripts/build.py

Clip mapping (by content; the uploaded PT numbers did not match the shot list, user-approved):
S1 PT-1, S2 PT-2, S3 PT-10 opening (no "holds up the belt" clip exists), S4 PT-3, S5 PT-4, S6 PT-5, S7 PT-6, S8 PT-7
(PT-8 is a near-duplicate), S9 PT-9, S10 PT-10 later part. Captions are animated per word (never per character).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H, TOTAL = 1080, 1920, 55.0
CUTS = [0, 4, 8, 13, 18, 23, 28, 33, 40, 48, 55]
CORAL, GOLD, RED, GREEN = "#E8446A", "#FFB347", "#FF4444", "#4CAF50"
CLIP = {1: "S1_pain", 2: "S2_hotwater", 3: "S3_reveal", 4: "S4_button", 5: "S5_wearing", 6: "S6_relax",
        7: "S7_flatlay", 8: "S8_order", 9: "S9_trust", 10: "S10_hero"}
MEDIA_START = {10: 1.0}                     # S3 uses PT-10 from 0 s, S10 from 1 s
XF56 = 0.8                                  # S5 -> S6 slow crossfade
# caption centre per scene (bottom third), moved where the belt sits in that band (checked on frames)
CAP_Y = {2: 0.74, 4: 0.74, 5: 0.80, 6: 0.74, 7: 0.76, 8: 0.70, 9: 0.68}
EMOJI = '"Noto Color Emoji"'


def win(n):
    a, b = CUTS[n - 1], CUTS[n]
    if n == 6:
        a -= XF56 / 2
    if n == 5:
        b += XF56 / 2
    return a, b


def words(text, cls="w"):
    return " ".join(f'<span class="{cls}">{w}</span>' for w in text.split())


def main():
    html, js = [], []
    # ---------------- scenes ----------------
    for n in range(1, 11):
        a, b = win(n)
        ms = MEDIA_START.get(n, 0.0)
        grade = "dim" if n <= 2 else ("hero" if n == 10 else "bright")
        html.append(f'''
  <div class="scene" id="s{n}" style="z-index:{n}"><div class="push" id="p{n}"><div class="cam" id="cam{n}">
    <video id="v{n}" class="clip" src="media/{CLIP[n]}.mp4" muted playsinline data-start="{a:.3f}" data-duration="{b - a:.3f}"
      data-media-start="{ms:.3f}" data-track-index="{n}"></video></div></div><div class="grade {grade}"></div></div>''')
        if n == 1:   # scene 1 is visible from frame 0 (under the black fade-in)
            html[-1] = html[-1].replace('id="s1" style="z-index:1"', 'id="s1" style="z-index:1;visibility:visible"', 1)
            js.append(f'tl.set("#s1", {{autoAlpha:0}}, {b:.3f});')
        else:
            js.append(f'tl.set("#s{n}", {{autoAlpha:0}}, 0); tl.set("#s{n}", {{autoAlpha:1}}, {a:.3f}); tl.set("#s{n}", {{autoAlpha:0}}, {b:.3f});')
        # gentle life on every shot; S10 settles from the punch-in
        if n == 10:
            js.append(f'tl.fromTo("#cam10", {{scale:1.08}}, {{scale:1.0, duration:0.45, ease:"power3.out"}}, {a:.3f});')
            js.append(f'tl.to("#cam10", {{scale:1.04, duration:{b - a - 0.45:.3f}, ease:"none"}}, {a + 0.45:.3f});')
        else:
            js.append(f'tl.fromTo("#cam{n}", {{scale:1.0}}, {{scale:1.04, duration:{b - a:.3f}, ease:"none"}}, {a:.3f});')
    # S5 -> S6 crossfade: S6 fades in over S5
    a6, _ = win(6)
    js.append(f'tl.fromTo("#s6", {{autoAlpha:0}}, {{autoAlpha:1, duration:{XF56}, ease:"sine.inOut", immediateRender:false}}, {a6:.3f});')
    # black in / out
    js.append('tl.fromTo("#black", {opacity:1}, {opacity:0, duration:0.5, ease:"sine.out"}, 0);')
    js.append('tl.to("#black", {opacity:1, duration:0.5, ease:"sine.in"}, 54.5);')
    # S2 -> S3 white flash (0.3 s): peak on the cut
    js.append('tl.fromTo("#flash", {opacity:0}, {opacity:1, duration:0.1, ease:"none"}, 7.9); tl.to("#flash", {opacity:0, duration:0.2, ease:"sine.out"}, 8.0);')
    # S9 -> S10 punch-in: S9 pushes in over its last 0.25 s
    js.append('tl.to("#p9", {scale:1.12, duration:0.25, ease:"power2.in"}, 47.75);')

    # ---------------- captions (bottom third, per-word reveal 0.1 s apart) ----------------
    caps = []
    def cap(cid, n, inner, t_in, t_out, style="", anim="fade", icon=""):
        y = CAP_Y.get(n, 0.74) * H
        caps.append(f'<div class="cap" id="{cid}" style="top:{y:.0f}px;{style}">{icon}{inner}</div>')
        js.append(f'tl.set("#{cid}", {{autoAlpha:1}}, {t_in:.3f});')
        ws = f"#{cid} .w"
        if anim == "left":
            js.append(f'tl.fromTo("#{cid}", {{x:-140}}, {{x:0, duration:0.45, ease:"power3.out"}}, {t_in:.3f});')
        elif anim == "right":
            js.append(f'tl.fromTo("#{cid}", {{x:140}}, {{x:0, duration:0.45, ease:"power3.out"}}, {t_in:.3f});')
        elif anim == "pop":
            js.append(f'tl.fromTo("#{cid}", {{scale:0.6}}, {{scale:1, duration:0.45, ease:"back.out(2.6)"}}, {t_in:.3f});')
        js.append(f'tl.fromTo("{ws}", {{autoAlpha:0, y:16}}, {{autoAlpha:1, y:0, duration:0.25, ease:"power2.out", stagger:0.1}}, {t_in:.3f});')
        if icon:
            js.append(f'tl.fromTo("#{cid} .ic", {{autoAlpha:0, scale:0.5}}, {{autoAlpha:1, scale:1, duration:0.3, ease:"back.out(2)"}}, {t_in:.3f});')
        js.append(f'tl.to("#{cid}", {{autoAlpha:0, duration:0.3, ease:"power1.in"}}, {t_out - 0.3:.3f});')

    ic = lambda e: f'<span class="ic">{e}</span>'
    cap("c2", 2, words("গরম পানির ব্যাগ"), 4.5, 7.8, "", "left", ic("❌"))
    cap("c4", 4, words("৩০ সেকেন্ডে গরম", "w gold"), 14.0, 18.0, "", "pop", ic("⚡"))
    cap("c5", 5, words("৩ হিট লেভেল + ম্যাসাজ", "w coral"), 19.0, 23.0, "", "right", ic("🔥"))
    cap("c6", 6, words("তারবিহীন ও হালকা"), 24.0, 28.0, "font-size:40px;", "fade", ic("🪶"))
    cap("c7", 7, words("গিফট বক্স প্যাকেজ"), 29.0, 33.0, "", "fade", ic("🎁"))
    cap("c9", 9, words("৭ দিন রিপ্লেসমেন্ট গ্যারান্টি", "w green"), 41.0, 47.4, "", "pop", ic("✅"))
    # S8: two stacked pills
    y8 = CAP_Y[8] * H
    caps.append(f'<div class="pillcap" id="c8a" style="top:{y8 - 50:.0f}px">{ic("💬")}{words("ইনবক্স করুন")}</div>')
    caps.append(f'<div class="pillcap" id="c8b" style="top:{y8 + 62:.0f}px">{ic("💰")}{words("ক্যাশ অন ডেলিভারি")}</div>')
    for cid, t in (("c8a", 34.0), ("c8b", 34.5)):
        js.append(f'tl.fromTo("#{cid}", {{autoAlpha:0, x:-120}}, {{autoAlpha:1, x:0, duration:0.3, ease:"power3.out"}}, {t:.3f});')
        js.append(f'tl.fromTo("#{cid} .w", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.2, stagger:0.1}}, {t:.3f});')
        js.append(f'tl.to("#{cid}", {{autoAlpha:0, duration:0.3}}, 39.2);')
    # S3: WARMLUNE with golden glow + shimmer
    js.append('tl.fromTo("#brand3", {autoAlpha:0, scale:0.8}, {autoAlpha:1, scale:1, duration:0.5, ease:"power2.out"}, 9.0);')
    js.append('tl.fromTo("#brand3 .shine", {xPercent:-160}, {xPercent:260, duration:1.4, ease:"sine.inOut"}, 9.3);')
    js.append('tl.to("#brand3", {autoAlpha:0, duration:0.3}, 12.7);')

    # ---------------- S10 CTA (top 55%, over a dark-pink panel) ----------------
    js.append('tl.fromTo("#panel", {opacity:0}, {opacity:1, duration:0.5, ease:"sine.out"}, 48.2);')
    js.append('tl.fromTo("#cta1", {autoAlpha:0}, {autoAlpha:1, duration:0.4}, 48.5);')
    js.append('tl.fromTo("#cta2", {autoAlpha:0, scale:0.9}, {autoAlpha:1, scale:1, duration:0.45, ease:"back.out(1.8)"}, 49.0);')
    js.append('tl.fromTo("#cta3 .w", {autoAlpha:0, y:12}, {autoAlpha:1, y:0, duration:0.3, stagger:0.1}, 49.5); tl.set("#cta3", {autoAlpha:1}, 49.5);')
    js.append('tl.fromTo("#cta4", {autoAlpha:0, y:40}, {autoAlpha:1, y:0, duration:0.4, ease:"power3.out"}, 50.0);')
    t = 50.6
    while t + 1.5 <= 54.6:   # seek-safe pulse loop: 100 -> 105 -> 100 % every 1.5 s
        js.append(f'tl.to("#cta4", {{scale:1.05, duration:0.75, ease:"sine.inOut", yoyo:true, repeat:1}}, {t:.2f});')
        t += 1.5
    js.append('tl.fromTo("#cta5", {autoAlpha:0}, {autoAlpha:1, duration:0.4}, 50.5);')

    css = f"""
@font-face {{ font-family:"Noto Sans Bengali"; src:url(media/fonts/noto-bengali.woff2) format("woff2"); font-weight:400 800; font-display:block; }}
@font-face {{ font-family:"Noto Color Emoji"; src:url(media/fonts/NotoColorEmoji.ttf) format("truetype"); font-display:block; }}
@font-face {{ font-family:"Montserrat"; src:url(media/fonts/montserrat-latin-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; }}
@font-face {{ font-family:"Montserrat"; src:url(media/fonts/montserrat-latin-800-normal.woff2) format("woff2"); font-weight:800; font-display:block; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:#000; }}
#root {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; font-family:"Noto Sans Bengali", {EMOJI}, sans-serif; color:#fff; }}
.scene {{ position:absolute; inset:0; overflow:hidden; visibility:hidden; }}
.push, .cam {{ position:absolute; inset:0; }}
.cam video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
.grade {{ position:absolute; inset:0; pointer-events:none; }}
.grade.dim {{ background:linear-gradient(180deg, rgba(20,30,60,.30), rgba(10,15,35,.42)); mix-blend-mode:multiply; backdrop-filter:saturate(.72) brightness(.88); }}
.grade.bright {{ background:radial-gradient(1100px 1300px at 55% 40%, rgba(255,214,190,.18), rgba(255,180,190,.06) 70%); mix-blend-mode:soft-light; backdrop-filter:saturate(1.06) brightness(1.03); }}
.grade.hero {{ backdrop-filter:saturate(1.08); }}
#flash {{ position:absolute; inset:0; z-index:60; background:#fff; opacity:0; pointer-events:none; }}
#black {{ position:absolute; inset:0; z-index:90; background:#000; opacity:1; pointer-events:none; }}
.cap {{ position:absolute; left:54px; width:{W - 108}px; translate:0 -50%; z-index:40; text-align:center; visibility:hidden;
  font-weight:800; font-size:48px; line-height:1.3; text-shadow:0 2px 8px rgba(0,0,0,.6); white-space:nowrap; }}
.cap .w {{ display:inline-block; }}
.cap .ic {{ display:inline-block; margin-right:14px; font-family:{EMOJI}; font-weight:400; }}
.w.gold {{ color:{GOLD}; }} .w.coral {{ color:{CORAL}; }} .w.green {{ color:{GREEN}; }}
#c2 {{ color:#fff; }}
#c2 .w {{ text-decoration:line-through; text-decoration-color:{RED}; text-decoration-thickness:5px; }}
.pillcap {{ position:absolute; left:50%; translate:-50% -50%; z-index:40; visibility:hidden; white-space:nowrap;
  background:rgba(0,0,0,.5); border-radius:999px; padding:12px 40px 10px; font-weight:800; font-size:48px; text-shadow:0 2px 8px rgba(0,0,0,.6); }}
.pillcap .w {{ display:inline-block; }}
.pillcap .ic {{ display:inline-block; margin-right:14px; font-family:{EMOJI}; font-weight:400; }}
#brand3 {{ position:absolute; top:{0.24 * H:.0f}px; left:0; width:100%; text-align:center; z-index:40; visibility:hidden;
  font-family:"Montserrat", sans-serif; font-weight:800; font-size:64px; letter-spacing:.24em; text-indent:.24em;
  text-shadow:0 0 18px rgba(255,190,90,.85), 0 0 42px rgba(255,170,60,.55), 0 2px 8px rgba(0,0,0,.5); }}
#brand3 .spark {{ font-family:{EMOJI}; letter-spacing:0; margin-right:18px; }}
#brand3 .clipbox {{ position:relative; display:inline-block; overflow:hidden; padding:0 6px; }}
#brand3 .shine {{ position:absolute; top:0; bottom:0; left:0; width:30%; background:linear-gradient(100deg, transparent, rgba(255,240,200,.85), transparent);
  mix-blend-mode:screen; }}
#brand3 sup, #cta1 sup {{ font-size:.38em; letter-spacing:0; vertical-align:1.5em; }}
#panel {{ position:absolute; left:0; top:0; width:100%; height:{0.58 * H:.0f}px; z-index:30; opacity:0; pointer-events:none;
  background:linear-gradient(180deg, rgba(70,14,36,.86) 0%, rgba(90,20,48,.78) 62%, rgba(90,20,48,0) 100%); }}
.cta {{ position:absolute; left:0; width:100%; text-align:center; z-index:41; visibility:hidden; text-shadow:0 2px 8px rgba(0,0,0,.6); }}
#cta1 {{ top:{0.085 * H:.0f}px; font-family:"Montserrat", sans-serif; font-weight:800; font-size:52px; letter-spacing:.24em; text-indent:.24em; }}
#cta2 {{ top:{0.155 * H:.0f}px; font-weight:800; font-size:80px; color:{CORAL}; text-shadow:0 2px 10px rgba(0,0,0,.45), 0 0 1px #fff; }}
#cta3 {{ top:{0.245 * H:.0f}px; font-weight:400; font-size:36px; }}
#cta3 .w {{ display:inline-block; }}
#cta4 {{ top:{0.31 * H:.0f}px; left:50%; width:auto; translate:-50% 0; white-space:nowrap; background:{CORAL}; color:#fff; border-radius:999px;
  padding:16px 40px; font-weight:800; font-size:44px; display:flex; align-items:center; gap:14px; box-shadow:0 14px 36px -10px rgba(0,0,0,.55); }}
#cta4 svg {{ width:40px; height:40px; }}
#cta5 {{ top:{0.405 * H:.0f}px; font-size:28px; font-weight:400; }}
"""
    arrow = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" d="M4 12h15M13 6l6 6-6 6"/></svg>'
    body = f"""<!doctype html>
<html lang="bn"><head><meta charset="UTF-8" /><meta name="viewport" content="width={W}, height={H}" />
<title>WarmLune 55s ad</title><style>{css}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="{W}" data-height="{H}">
{''.join(html)}
  <div id="brand3"><span class="spark">✨</span><span class="clipbox">WARMLUNE<sup>™</sup><span class="shine"></span></span></div>
  {''.join(caps)}
  <div id="panel"></div>
  <div class="cta" id="cta1">WARMLUNE<sup>™</sup></div>
  <div class="cta" id="cta2">মাত্র ৳১,০৯৯</div>
  <div class="cta" id="cta3">{words("তারবিহীন হিটিং ও ম্যাসাজ বেল্ট")}</div>
  <div class="cta" id="cta4"><span>অর্ডার করুন</span>{arrow}</div>
  <div class="cta" id="cta5">ক্যাশ অন ডেলিভারি · ৭ দিন গ্যারান্টি</div>
  <div id="flash"></div>
  <div id="black"></div>
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
    (ROOT / "index.html").write_text(body, encoding="utf-8")
    print("built index.html")


if __name__ == "__main__":
    main()
