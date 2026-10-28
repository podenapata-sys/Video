#!/usr/bin/env python3
"""Build "এক কাপ চা, একটা অ্যালগরিদম" (60 s, Bangla): index.html (16:9) and reels.html (9:16).

  python3 scripts/voice.py           # voiceover -> scene grid, subtitles, cues, mix, re-timed clips (timing.json)
  python3 scripts/build.py [--render]

- six 10 s clips back to back (muted); the voiceover mix is the only audio
- writes index.html (16:9) and reels/index.html (9:16, its own project sharing fonts/ and assets/ by symlink)
- clip-anchored layers (band wipe, ১৪০ plate, speech-bubble fix, closing navy) live in #clipbox, in 1920x1080
  clip coordinates; in 9:16 #clipbox is the full-width clip scaled to 1080x608 and centred on an ink-navy field
- persistent overlay: crosshairs, red progress bar, chapter tags, three squares
- subtitles (lower third / below the clip), headline moments and the closing card per the brief
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ["node", "/root/.claude/plugins/cache/hyperframes/hyperframes/0.8.152/skills/hyperframes/scripts/plugin-cli.mjs"]
FPS = 30
F = 1 / FPS
CREAM, RED, BLUE, NAVY, BLACK, GRAY = "#E6DACB", "#FF3B1F", "#2B36F5", "#141824", "#111111", "#6E6E78"
CLIPS = ["scene1", "scene2", "scene3", "scene4", "scene5", "closing"]
TAGS = ["সকালের ভিড়", "অচেনা কাস্টমার", "পরীক্ষা", "ভয়", "উত্তর"]
BN = "০১২৩৪৫৬৭৮৯"

LAYOUT = {
    "16x9": dict(W=1920, H=1080, clip=(0, 0, 1.0), field=False,
                 tag=(64, 56), sub_css="left:0;right:0;bottom:70px;", sub_font=30, sub_max=1300,
                 h1=(96, 150, 72), h1_line1=BLACK, count=dict(right=110, top=96, size=160),
                 stamp=(150, 420, 88), labels=(300, 480, 1440, 44),
                 close=(390, 76, 28)),
    "9x16": dict(W=1080, H=1920, clip=(0, 656, 0.5625), field=True,
                 tag=(64, 150), sub_css="left:0;right:0;top:1312px;", sub_font=38, sub_max=960,
                 h1=(64, 300, 72), h1_line1="#FFFFFF", count=dict(right=72, top=250, size=160),
                 stamp=(80, 330, 88), labels=(470, 270, 810, 44),
                 close=(760, 64, 28)),
}


def bn(n):
    return "".join(BN[int(c)] for c in str(n))


def wipe(js, sel, at, frames, overshoot=True):
    """Text wipes up out of its mask: expo-out with ~5% overshoot, then settles."""
    d = frames * F
    if overshoot:
        js.append(f'tl.fromTo("{sel}", {{ yPercent: 110 }}, {{ yPercent: -5, duration: {d * 0.72:.4f}, ease: "expo.out" }}, {at:.4f});')
        js.append(f'tl.to("{sel}", {{ yPercent: 0, duration: {d * 0.28:.4f}, ease: "power2.out" }}, {at + d * 0.72:.4f});')
    else:
        js.append(f'tl.fromTo("{sel}", {{ yPercent: 110 }}, {{ yPercent: 0, duration: {d:.4f}, ease: "expo.out" }}, {at:.4f});')


def build(kind, timing):
    L = LAYOUT[kind]
    W, H = L["W"], L["H"]
    cx, cy, cs = L["clip"]
    els, clipbox, js = [], [], []
    scenes, cues, total = timing["scenes"], timing["cues"], timing["total"]
    S = [sc["start"] for sc in scenes]
    Ln = [sc["length"] for sc in scenes]

    def ct(i, t):  # a moment in clip i's own 10 s timeline -> composition time (clips are slowed to fit the voice)
        return S[i] + t * Ln[i] / 10.0

    # ---- clips (muted), on the 10 s grid; hard cuts
    for i, name in enumerate(CLIPS):
        clipbox.append(f'<video id="v{i}" class="shot" src="assets/clips/{name}.mp4" data-start="{S[i]:.4f}" '
                       f'data-duration="{Ln[i]:.4f}" data-track-index="1" muted playsinline></video>')
    # scene3 -> scene4: an ink-navy band wipes down over 8 frames, covering the cut, then clears downward
    clipbox.append('<div id="band"></div>')
    js.append(f'tl.fromTo("#band", {{ scaleY: 0, transformOrigin: "50% 0%" }}, {{ scaleY: 1, duration: {4 * F:.4f}, ease: "power2.in" }}, {S[3] - 4 * F:.4f});')
    js.append(f'tl.fromTo("#band", {{ scaleY: 1, transformOrigin: "50% 100%" }}, {{ scaleY: 0, duration: {4 * F:.4f}, ease: "power2.out", immediateRender: false }}, {S[3]:.4f});')
    # scene2: the clip's speech bubble carries leaked English prompt text ("expo-out overshoot");
    # cover its text with a bubble-coloured patch that pops with it, and give Rahim his line
    b0, k2 = ct(1, 6.967), Ln[1] / 10.0
    clipbox.append(f'<div id="bubfix" class="clip" data-start="{b0:.4f}" data-duration="{S[2] - b0:.4f}" data-track-index="3">'
                   '<div id="bubin">কম্পিউটার?</div></div>')
    js.append(f'tl.fromTo("#bubin", {{ scale: 0.3 }}, {{ scale: 1.12, duration: {0.233 * k2:.4f}, ease: "expo.out" }}, {b0:.4f});')
    js.append(f'tl.to("#bubin", {{ scale: 1.0, duration: {0.267 * k2:.4f}, ease: "power2.inOut" }}, {ct(1, 7.4):.4f});')
    # scene3: navy plate over the clip's own baked counter, under our ১৪০
    c0, c1 = cues["count"] - 0.1, S[3] - 0.05
    clipbox.append(f'<div id="plate" class="clip" data-start="{c0:.4f}" data-duration="{c1 - c0:.4f}" data-track-index="3"></div>')
    # closing: the clip's own headline is legible but worded differently and sits exactly where ours goes
    clipbox.append(f'<div id="closebg" class="clip" data-start="{S[5]:.4f}" data-duration="{Ln[5]:.4f}" data-track-index="3"></div>')

    # ---- persistent overlay
    cross = ('<svg width="22" height="22" viewBox="0 0 22 22"><circle cx="11" cy="11" r="6" fill="none" stroke="#6E6E78" stroke-width="1.5"/>'
             '<path d="M11 0V22M0 11H22" stroke="#6E6E78" stroke-width="1.5"/></svg>')
    for pos in ("left:28px;top:28px", "right:28px;top:28px", "left:28px;bottom:28px", "right:28px;bottom:28px"):
        els.append(f'<div class="cross" style="{pos}">{cross}</div>')
    els.append('<div id="barbox"><div id="bar"></div></div>')
    js.append(f'tl.fromTo("#bar", {{ scaleX: 0 }}, {{ scaleX: 1, duration: {total}, ease: "none" }}, 0);')
    tx, ty = L["tag"]
    for i, label in enumerate(TAGS):
        els.append(f'<div id="tag{i}" class="clip tag" data-start="{S[i]:.4f}" data-duration="{Ln[i]:.4f}" data-track-index="5" '
                   f'style="left:{tx}px;top:{ty}px"><div class="mask"><div class="in" id="tagin{i}">'
                   f'<span class="num">{bn(0)}{bn(i + 1)}</span><span class="tlab">{label}</span></div></div></div>')
        wipe(js, f"#tagin{i}", S[i] + (0.1 if i == 0 else 0), 6)
    els.append('<div id="squares"><i style="background:#FF3B1F"></i><i style="background:#2B36F5"></i><i style="background:#6E6E78"></i></div>')

    # ---- subtitles
    for k, c in enumerate(timing["subs"]):
        els.append(f'<div id="sub{k}" class="clip subs" data-start="{c["start"]:.3f}" data-duration="{c["end"] - c["start"]:.3f}" '
                   f'data-track-index="6" data-layout-allow-caption-zone="true" style="{L["sub_css"]}"><div class="mask sm">'
                   f'<div class="in box" id="subin{k}">{c["text"]}</div></div></div>')
        wipe(js, f"#subin{k}", c["start"], 6)

    # ---- headlines
    hx, hy, hs = L["h1"]
    els.append(f'<div id="h1" class="clip head" data-start="1" data-duration="4" data-track-index="7" style="left:{hx}px;top:{hy}px;font-size:{hs}px">'
               f'<div class="mask"><div class="in" id="h1a" style="color:{L["h1_line1"]}">এক কাপ চা,</div></div>'
               f'<div class="mask"><div class="in" id="h1b" style="color:{RED}">একটা অ্যালগরিদম</div></div></div>')
    wipe(js, "#h1a", 1.0, 8)
    wipe(js, "#h1b", 1.0 + 4 * F, 8)
    c = L["count"]
    els.append(f'<div id="count" class="clip" data-start="{c0:.4f}" data-duration="{c1 - c0:.4f}" data-track-index="7" style="right:{c["right"]}px;top:{c["top"]}px">'
               f'<div class="mask"><div class="in" id="countin"><div id="num" style="font-size:{c["size"]}px">{bn(80)}</div>'
               f'<div id="cap">কাপ / দিন</div></div></div></div>')
    wipe(js, "#countin", c0, 8)
    js.append('const BN = "০১২৩৪৫৬৭৮৯"; const numEl = document.getElementById("num"); const cnt = { v: 80 };')
    js.append('const showCount = () => { numEl.textContent = String(Math.round(cnt.v)).replace(/[0-9]/g, (d) => BN[d]); };')
    js.append(f'tl.fromTo(cnt, {{ v: 80 }}, {{ v: 143, duration: 1.0, ease: "expo.out", onUpdate: showCount }}, {c0 + 0.05:.4f});')
    js.append(f'tl.to(cnt, {{ v: 140, duration: 0.2, ease: "power2.out", onUpdate: showCount }}, {c0 + 1.05:.4f});')
    sx, sy, ss = L["stamp"]
    s0 = cues["stamp"] - 0.05
    els.append(f'<div id="stampc" class="clip" data-start="{s0:.4f}" data-duration="{S[4] - 0.05 - s0:.4f}" data-track-index="7" style="left:{sx}px;top:{sy}px">'
               f'<div id="stamp" style="font-size:{ss}px">বদলি?</div></div>')
    js.append(f'tl.fromTo("#stamp", {{ scale: 1.2, rotation: -6, opacity: 0 }}, {{ scale: 1, rotation: -6, opacity: 1, duration: 0.133, ease: "expo.out" }}, {s0:.4f});')
    js.append(f'tl.fromTo("#stamp", {{ x: -7 }}, {{ x: 7, duration: 0.0333, ease: "none", yoyo: true, repeat: 1, immediateRender: false }}, {s0 + 0.133:.4f});')
    js.append(f'tl.to("#stamp", {{ x: 0, duration: 0.0333, ease: "none" }}, {s0 + 0.2:.4f});')
    ly, lx1, lx2, lsz = L["labels"]
    l0 = cues["labels"] - 0.05
    ld = S[5] - 0.05 - l0
    els.append(f'<div id="lab1" class="clip plab" data-start="{l0:.4f}" data-duration="{ld:.4f}" data-track-index="7" style="left:{lx1 - 300}px;top:{ly}px;font-size:{lsz}px">'
               f'<div class="mask"><div class="in" id="lab1in" style="color:{BLUE}">হিসাব রাখে মেশিন</div></div></div>')
    els.append(f'<div id="lab2" class="clip plab" data-start="{l0:.4f}" data-duration="{ld:.4f}" data-track-index="7" style="left:{lx2 - 300}px;top:{ly}px;font-size:{lsz}px">'
               f'<div class="mask"><div class="in" id="lab2in" style="color:{RED}">যত্ন নেয় মানুষ</div></div></div>')
    wipe(js, "#lab1in", l0, 8)
    wipe(js, "#lab2in", l0 + 10 * F, 8)
    top, csz, ssz = L["close"]
    q1, q3 = cues["close"][0] - 0.05, cues["close"][1] - 0.05
    els.append(f'<div id="close" class="clip" data-start="{S[5]:.4f}" data-duration="{Ln[5]:.4f}" data-track-index="8" style="top:{top}px">'
               f'<div class="mask"><div class="in" id="cl1" style="font-size:{csz}px;color:#FFFFFF">এআই আপনার জায়গা নেয় না।</div></div>'
               f'<div class="mask"><div class="in" id="cl2" style="font-size:{csz}px;color:{RED}">নেয় আপনার কাজের বোঝা।</div></div></div>')
    els.append(f'<div id="close3" class="clip" data-start="{q3:.4f}" data-duration="{total - q3:.4f}" data-track-index="8" style="top:{top + int(csz * 2 * 1.3) + 40}px">'
               f'<div class="mask"><div class="in" id="cl3" style="font-size:{ssz}px">শুধু সাহস করে তাকে সুযোগ দিতে হয়।</div></div></div>')
    wipe(js, "#cl1", q1, 8)
    wipe(js, "#cl2", q1 + 10 * F, 8)
    wipe(js, "#cl3", q3, 8)

    audio = ""
    if (ROOT / "assets" / "vo" / "mix.wav").exists():
        audio = f'<audio id="vo" src="assets/vo/mix.wav" data-start="0" data-duration="{total}" data-track-index="9" data-volume="1"></audio>'

    grain = ("url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'>"
             "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' seed='7'/>"
             "<feColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.09 0'/></filter>"
             "<rect width='240' height='240' filter='url(%23n)'/></svg>\")")
    field = '<div id="field"></div>' if L["field"] else ""
    return (PAGE.replace("{{TOTAL}}", str(total)).replace("{{W}}", str(W)).replace("{{H}}", str(H)).replace("{{TITLE}}", f"Tea Stall Algorithm {kind}")
            .replace("{{CX}}", str(cx)).replace("{{CY}}", str(cy)).replace("{{CS}}", str(cs))
            .replace("{{FIELD}}", field).replace("{{GRAIN}}", grain).replace("{{CLIPBOX}}", "\n          ".join(clipbox))
            .replace("{{ELS}}", "\n      ".join(els)).replace("{{AUDIO}}", audio).replace("{{JS}}", "\n      ".join(js))
            .replace("{{SUBFONT}}", str(L["sub_font"])).replace("{{SUBMAX}}", str(L["sub_max"])))


PAGE = """<!doctype html>
<html lang="bn">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={{W}}, height={{H}}" />
    <title>{{TITLE}}</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      @font-face { font-family: "Hind Siliguri"; src: url("fonts/HindSiliguri-Regular.ttf") format("truetype"); font-weight: 400; }
      @font-face { font-family: "Hind Siliguri"; src: url("fonts/HindSiliguri-SemiBold.ttf") format("truetype"); font-weight: 600; }
      @font-face { font-family: "Hind Siliguri"; src: url("fonts/HindSiliguri-Bold.ttf") format("truetype"); font-weight: 700; }
      @font-face { font-family: "Noto Sans Bengali"; src: url("fonts/NotoSansBengali-Variable.ttf") format("truetype"); font-weight: 100 900; }
      @font-face { font-family: "IBM Plex Mono"; src: url("fonts/IBMPlexMono-Regular.ttf") format("truetype"); font-weight: 400; }
      @font-face { font-family: "IBM Plex Mono"; src: url("fonts/IBMPlexMono-Medium.ttf") format("truetype"); font-weight: 500; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: {{W}}px; height: {{H}}px; overflow: hidden; background: #141824; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #141824;
        font-family: "Hind Siliguri", "Noto Sans Bengali", sans-serif; }
      #field { position: absolute; inset: 0; background-color: #141824; background-image: {{GRAIN}}; }
      #clipbox { position: absolute; left: {{CX}}px; top: {{CY}}px; width: 1920px; height: 1080px; overflow: hidden;
        transform: scale({{CS}}); transform-origin: 0 0; }
      .shot { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; object-fit: cover; }
      #band { position: absolute; inset: 0; background: #141824; z-index: 4; transform: scaleY(0); }
      #bubfix { position: absolute; left: 646px; top: 160px; width: 200px; height: 96px; z-index: 3; }
      #bubin { width: 100%; height: 100%; background: #F5F1E5; border-radius: 36px; display: flex; align-items: center;
        justify-content: center; font-weight: 600; font-size: 30px; color: #111111; transform-origin: -34px 155px; }
      #plate { position: absolute; left: 1340px; top: 40px; width: 560px; height: 540px; background: #141824; z-index: 3; }
      #closebg { position: absolute; inset: 0; background: #141824; z-index: 3; }
      .cross { position: absolute; width: 22px; height: 22px; z-index: 20; }
      .cross svg { display: block; }
      #barbox { position: absolute; left: 0; top: 0; width: 100%; height: 3px; z-index: 21; }
      #bar { width: 100%; height: 100%; background: #FF3B1F; transform-origin: 0 50%; }
      #squares { position: absolute; left: 64px; bottom: 40px; display: flex; gap: 6px; z-index: 20; }
      #squares i { display: block; width: 8px; height: 8px; }
      .mask { overflow: hidden; padding-top: 0.12em; }
      .in { display: block; will-change: transform; }
      .tag { position: absolute; width: auto; height: auto; z-index: 19; }
      .tag .in { display: flex; align-items: center; gap: 8px; }
      .tag .num { display: block; background: #111111; color: #FFFFFF; font-weight: 600; font-size: 22px; line-height: 1;
        padding: 6px 9px 4px; }
      .tag .tlab { display: block; color: #6E6E78; font-weight: 600; font-size: 22px; line-height: 1.2; background: #E6DACB;
        padding: 3px 10px 1px; }
      .subs { position: absolute; height: auto; text-align: center; z-index: 18; }
      .subs .sm { display: inline-block; max-width: {{SUBMAX}}px; vertical-align: top; }
      .subs .box { display: inline-block; background: #111111; color: #FFFFFF; border-left: 3px solid #FF3B1F;
        padding: 10px 18px; font-weight: 600; font-size: {{SUBFONT}}px; line-height: 1.4; text-align: center; }
      .head { position: absolute; width: auto; height: auto; font-weight: 700; line-height: 1.18; z-index: 17; }
      #count { position: absolute; width: auto; height: auto; text-align: right; z-index: 17; }
      #num { color: #FF3B1F; font-weight: 700; line-height: 1.0; }
      #cap { color: #6E6E78; font-weight: 600; font-size: 30px; line-height: 1.2; }
      #stampc { position: absolute; width: auto; height: auto; z-index: 17; }
      #stamp { display: inline-block; color: #FF3B1F; font-weight: 700; line-height: 1.05; border: 4px solid #FF3B1F;
        padding: 6px 26px 0; border-radius: 6px; }
      .plab { position: absolute; width: 600px; height: auto; text-align: center; font-weight: 700; line-height: 1.2; z-index: 17; }
      .plab .in { display: inline-block; background: #E6DACB; padding: 6px 20px 2px; border-left: 3px solid currentColor; }
      #close, #close3 { position: absolute; left: 0; width: 100%; height: auto; text-align: center; font-weight: 700;
        line-height: 1.3; z-index: 17; }
      #close3 .in { color: #6E6E78; font-weight: 400; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{{TOTAL}}" data-width="{{W}}" data-height="{{H}}" data-fps="30">
      {{FIELD}}
      <div id="clipbox">
          {{CLIPBOX}}
      </div>
      {{ELS}}
      {{AUDIO}}
    </div>
    <script>
      const tl = gsap.timeline({ paused: true });
      {{JS}}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def main():
    timing = json.loads((ROOT / "timing.json").read_text())
    (ROOT / "index.html").write_text(build("16x9", timing))
    (ROOT / "reels" / "index.html").write_text(build("9x16", timing))  # its own project: one root composition each
    print(f"built index.html + reels/index.html, {len(timing["subs"])} subtitles, {timing["total"]:.2f}s, audio: {(ROOT / 'assets/vo/mix.wav').exists()}")
    if "--render" in sys.argv:
        for proj, name in ((ROOT, "tea-stall-algorithm-16x9.mp4"), (ROOT / "reels", "tea-stall-algorithm-9x16.mp4")):
            out = ROOT / "renders" / name
            args = CLI + ["render", str(proj), "-o", str(out), "--fps", "30", "--quality", "delivery"]
            r = subprocess.run(args, capture_output=True, text=True)
            print("\n".join(l for l in (r.stdout + r.stderr).splitlines() if "MB" in l or "rror" in l or "beginframe" in l or "screenshot" in l))


if __name__ == "__main__":
    main()
