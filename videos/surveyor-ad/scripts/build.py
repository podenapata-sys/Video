#!/usr/bin/env python3
"""Khulna Divisional Digital Surveyor Association Reels ad -> index.html (HyperFrames, 1080x1920).

  python3 scripts/voice.py && python3 scripts/words.py && python3 scripts/music.py && python3 scripts/build.py

Scenes follow timing.json (voice-driven grid); captions and the CTA card follow words.json (one <span> per word).
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1920
T = json.loads((ROOT / "timing.json").read_text())
WORDS = json.loads((ROOT / "words.json").read_text(encoding="utf-8"))
MUS = json.loads((ROOT / "music.json").read_text())
TOTAL = T["total"]
SC = {s["n"]: s for s in T["scenes"]}
YEL, ORANGE, NAVY = "#FFC107", "#FF6B4A", "#0B2545"
TRANS = {1: "cut", 2: "dip", 3: "leak", 4: "xf", 5: "xf", 6: "xf", 7: "push"}  # transition after scene n
XF = 0.4
GRADE = {1: "gold", 2: "cold", 3: "cool", 4: "warm", 5: "warm", 6: "warm", 7: "warm", 8: "vivid"}
# gentle camera per scene: (scale from, to, origin)
CAM = {1: (1.0, 1.06, "50% 35%"), 2: (1.0, 1.04, "50% 30%"), 3: (1.0, 1.05, "50% 30%"), 4: (1.0, 1.05, "50% 45%"),
       5: (1.04, 1.0, "60% 45%"), 6: (1.0, 1.05, "50% 60%"), 7: (1.0, 1.05, "50% 35%"), 8: (1.0, 1.04, "50% 40%")}
# caption centre (fraction of height). 64-72% where it is clear; moved where that band holds the map, papers or
# pantograph (3: documents on the table, 6: pantograph on the map, 7: the plan they hold) - checked on frames.
CAP_Y = {1: 0.68, 2: 0.68, 3: 0.52, 4: 0.61, 5: 0.68, 6: 0.40, 7: 0.50}
# per-chunk override: scene 6 opens on a face close-up (eyes ~40%), so its first chunk sits on his shirt instead
CAP_Y_CHUNK = {(6, 0): 0.77}
COL_L, COL_W = 54, 896          # CTA/caption column: keeps the right 12-15% clear
HEAD_TOP = 0.118 * H


def win(n):
    s = SC[n]
    a = s["start"] - (XF / 2 if n > 1 and TRANS[n - 1] in ("xf", "push") else 0)
    b = s["start"] + s["length"] + (XF / 2 if n < 8 and TRANS[n] in ("xf", "push") else 0)
    return round(max(0, a), 3), round(min(TOTAL, b), 3)


def chunks(words):
    phrases, cur = [], []
    for w in words:
        cur.append(w)
        if w["break"]:
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    merged = []
    for p in phrases:
        same = merged and merged[-1][-1]["speaker"] == p[0]["speaker"]
        if merged and same and (len(p) == 1 or len(merged[-1]) == 1) and len(merged[-1]) + len(p) <= 4:
            merged[-1] = merged[-1] + p
        else:
            merged.append(p)
    out = []
    for p in merged:
        n = len(p)
        if n <= 4:
            out.append(p)
            continue
        k = -(-n // 4)
        sizes = [n // k + (1 if i < n % k else 0) for i in range(k)]
        i = 0
        for s in sizes:
            out.append(p[i:i + s])
            i += s
    return out


def last_frame(n):
    out = ROOT / "assets" / "clips" / f"scene{n}_last.jpg"
    if not out.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.3", "-i", str(ROOT / "assets" / "clips" / f"scene{n}.mp4"),
                        "-update", "1", "-q:v", "2", str(out)], check=True)
    return f"assets/clips/scene{n}_last.jpg"


def main():
    js, html = [], []
    by = {}
    for w in WORDS:
        by.setdefault(w["scene"], []).append(w)
    # ---------------- scenes ----------------
    for n in range(1, 9):
        s = SC[n]
        a, b = win(n)
        span = b - a
        play = min(s["clip_play"], span)
        hold = ""
        if s["hold_from"] is not None and play < span - 0.02:
            hold = (f'<div class="hw" id="hw{n}"><img class="clip still" id="hold{n}" src="{last_frame(n)}" alt="" '
                    f'data-start="{a + play:.3f}" data-duration="{span - play:.3f}" data-track-index="{10 + n}" /></div>')
            js.append(f'tl.fromTo("#hw{n}", {{scale:1}}, {{scale:1.04, duration:{span - play:.3f}, ease:"none"}}, {a + play:.3f});')
        rate = f' data-playback-rate="{s["rate"]}"' if s["rate"] < 0.999 else ""
        html.append(f'''
  <div class="scene" id="s{n}" style="z-index:{n}"><div class="push" id="p{n}"><div class="cam" id="cam{n}">
    <video id="v{n}" class="clip" src="assets/clips/scene{n}.mp4" muted playsinline data-start="{a:.3f}" data-duration="{play:.3f}"
      data-media-start="0"{rate} data-track-index="{n}"></video>{hold}
  </div></div><div class="grade {GRADE[n]}"></div></div>''')
        f0, f1, org = CAM[n]
        js.append(f'tl.fromTo("#cam{n}", {{scale:{f0}, transformOrigin:"{org}"}}, {{scale:{f1}, duration:{span:.3f}, ease:"power1.inOut"}}, {a:.3f});')
        js.append(f'tl.set("#s{n}", {{autoAlpha:0}}, 0);')
        prev = TRANS.get(n - 1)
        if prev in ("xf", "push"):
            if prev == "push":
                js.append(f'tl.fromTo("#p{n}", {{scale:1.1}}, {{scale:1, duration:{XF}, ease:"power2.out"}}, {a:.3f});')
            js.append(f'tl.fromTo("#s{n}", {{autoAlpha:0}}, {{autoAlpha:1, duration:{XF}, ease:"sine.inOut"}}, {a:.3f});')
        else:
            js.append(f'tl.set("#s{n}", {{autoAlpha:1}}, {a:.3f});')
        if n < 8 and TRANS[n] == "push":
            js.append(f'tl.to("#p{n}", {{scale:1.1, duration:{XF}, ease:"power2.in"}}, {b - XF:.3f});')
        js.append(f'tl.set("#s{n}", {{autoAlpha:0}}, {b:.3f});')
    # ---------------- transitions ----------------
    b12, b23, b34 = SC[2]["start"], SC[3]["start"], SC[4]["start"]
    js.append(f'tl.set("#flash", {{opacity:0.92}}, {b12:.4f}); tl.set("#flash", {{opacity:0}}, {b12 + 2 / 30:.4f});')
    js.append(f'tl.to("#p2", {{keyframes:{{x:[-18,15,-11,8,-4,0], y:[6,-5,4,-2,1,0]}}, duration:0.3, ease:"none"}}, {b12:.4f});')
    js.append(f'tl.fromTo("#dark", {{opacity:0}}, {{opacity:1, duration:0.25, ease:"sine.in"}}, {b23 - 0.25:.3f});')
    js.append(f'tl.to("#dark", {{opacity:0, duration:0.25, ease:"sine.out"}}, {b23:.3f});')

    # ---------------- captions (scenes 1-7) ----------------
    cap_html, sync = [], []
    cid = 0
    for n in range(1, 8):
        cs = chunks(by[n])
        send = SC[n]["start"] + SC[n]["length"]
        for j, ch in enumerate(cs):
            t0 = max(SC[n]["start"], ch[0]["start"] - 0.12)
            nxt = cs[j + 1][0]["start"] - 0.12 if j + 1 < len(cs) else send - 0.05
            t1 = min(nxt, max(ch[-1]["end"] + 0.25, t0 + 0.6), send - 0.05)
            thought = ch[0]["speaker"] == "T"
            spans = " ".join(f'<span class="w" id="c{cid}w{k}">{w["text"]}</span>' for k, w in enumerate(ch))
            cy = CAP_Y_CHUNK.get((n, j), CAP_Y[n])
            cap_html.append(f'<div class="cap{" thought" if thought else ""}" id="c{cid}" style="top:{cy * H:.0f}px">{spans}</div>')
            if n <= 3:
                js.append(f'tl.fromTo("#c{cid}", {{autoAlpha:0, y:18}}, {{autoAlpha:{0.8 if thought else 1}, y:0, duration:0.3, ease:"power2.out"}}, {t0:.3f});')
            else:
                js.append(f'tl.fromTo("#c{cid}", {{autoAlpha:0, scale:0.86}}, {{autoAlpha:1, scale:1, duration:0.2, ease:"back.out(2.2)"}}, {t0:.3f});')
            js.append(f'tl.to("#c{cid}", {{autoAlpha:0, duration:0.15, ease:"power1.in"}}, {t1 - 0.15:.3f});')
            for k, w in enumerate(ch):
                col = ORANGE if w["speaker"] == "N" else YEL
                hd = 0.08 if k + 1 == len(ch) else max(0.02, min(0.08, ch[k + 1]["start"] - w["start"] - 0.01))
                js.append(f'tl.fromTo("#c{cid}w{k}", {{color:"#FFFFFF", scale:1}}, {{color:"{col}", scale:1.08, duration:{hd:.3f}, '
                          f'ease:"power2.out", immediateRender:false}}, {w["start"]:.3f});')
                if k + 1 < len(ch):
                    js.append(f'tl.to("#c{cid}w{k}", {{color:"#FFFFFF", scale:1, duration:0.1}}, {ch[k + 1]["start"]:.3f});')
                sync.append((w["text"], w["start"]))
            cid += 1

    # ---------------- headlines (scenes 1-7) ----------------
    heads = []
    def head(hid, inner, t_in, t_out, top=HEAD_TOP, shake=False, cls=""):
        heads.append(f'<div class="head {cls}" id="{hid}" style="top:{top:.0f}px">{inner}</div>')
        js.append(f'tl.fromTo("#{hid}", {{autoAlpha:0, y:-26}}, {{autoAlpha:1, y:0, duration:0.4, ease:"power3.out"}}, {t_in:.3f});')
        if shake:
            js.append(f'tl.to("#{hid}", {{keyframes:{{x:[-10,8,-5,3,0]}}, duration:0.3, ease:"none"}}, {t_in:.3f});')
        js.append(f'tl.to("#{hid}", {{autoAlpha:0, y:-14, duration:0.3, ease:"power1.in"}}, {t_out - 0.3:.3f});')
    end = lambda n: SC[n]["start"] + SC[n]["length"]
    head("h1", "এক টুকরো জমি, হাজারো স্বপ্ন!", SC[1]["start"] + 0.3, SC[1]["start"] + 3.6)
    head("h2", "জমির সীমানা নিয়ে বিরোধ?", b12, b12 + 3.0, shake=True)
    head("h3", "অনুমানের ওপর নয়,<br>প্রয়োজন সঠিক পরিমাপ।", SC[3]["start"] + SC[3]["length"] / 2, end(3))
    head("h4", "আপনার পাশে পেশাদার সার্ভে সেবা।", SC[4]["start"] + 0.3, SC[4]["start"] + 3.8)
    head("h5", f'<span class="en">LAND DEMARCATION</span><span class="sub">জমির পরিমাপ ও সীমানা নির্ধারণ</span>', SC[5]["start"] + 0.15, end(5))
    head("h6", f'<span class="en">PANTOGRAPH SERVICE</span><span class="sub">মৌজা ম্যাপের স্কেলিং ও নকশার কাজ</span>', SC[6]["start"] + 0.15, end(6), cls="left")  # left: clear of the drafter's face
    w7 = by[7]
    for k, (txt, wi) in enumerate([("সঠিক তথ্য।", 5), ("পেশাদার পরিমাপ।", 7), ("বিশ্বস্ত সহযোগিতা।", 9)]):
        head(f"h7_{k}", txt, w7[wi]["start"], end(7), top=0.098 * H + k * 0.058 * H)

    # ---------------- scene 8 CTA ----------------
    w8 = by[8]
    s8a = w8[0]["start"]
    kh = w8[4]["start"]                              # "খুলনা": part B
    land = w8[9]["start"]                            # "ল্যান্ড"
    wa = w8[15]["start"]                             # "হোয়াটসঅ্যাপ"
    fin = w8[18]["start"]                            # "আপনার" (final line)
    js.append(f'tl.fromTo("#cta-head", {{autoAlpha:0, scale:0.82, y:-10}}, {{autoAlpha:1, scale:1, y:0, duration:0.35, ease:"back.out(2.4)"}}, {s8a:.3f});')
    js.append(f'tl.fromTo("#navy", {{opacity:0}}, {{opacity:0.85, duration:0.5, ease:"sine.inOut"}}, {kh:.3f});')
    js.append(f'tl.fromTo("#cam8", {{filter:"blur(0px)"}}, {{filter:"blur(12px)", duration:0.5, ease:"sine.inOut", immediateRender:false}}, {kh:.3f});')
    js.append(f'tl.fromTo("#motif", {{autoAlpha:0}}, {{autoAlpha:0.2, duration:0.6}}, {kh + 0.2:.3f});')
    plot = [(250, 640), (720, 560), (860, 900), (700, 1260), (300, 1330), (150, 960)]
    lines, pegs = [], []
    for k in range(len(plot)):
        (x1, y1), (x2, y2) = plot[k], plot[(k + 1) % len(plot)]
        L = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        lines.append(f'<line id="ln{k}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke-dasharray="{L:.1f}" stroke-dashoffset="{L:.1f}"/>')
        pegs.append(f'<circle id="pg{k}" cx="{x1}" cy="{y1}" r="11"/>')
        t = kh + 0.4 + k * 0.38
        js.append(f'tl.fromTo("#pg{k}", {{scale:0, transformOrigin:"50% 50%"}}, {{scale:1, duration:0.25, ease:"back.out(3)"}}, {t:.3f});')
        js.append(f'tl.fromTo("#ln{k}", {{attr:{{"stroke-dashoffset":{L:.1f}}}}}, {{attr:{{"stroke-dashoffset":0}}, duration:0.4, ease:"power1.inOut"}}, {t + 0.08:.3f});')
    contours = "".join(f'<path class="ct" d="M -100 {y} C 200 {y - 60}, 420 {y + 70}, 640 {y + 10} S 1000 {y - 50}, 1200 {y + 20}"/>' for y in (430, 760, 1110, 1450))
    js.append(f'tl.fromTo("#contours", {{x:-30, y:10}}, {{x:30, y:-10, duration:{TOTAL - kh:.3f}, ease:"none"}}, {kh:.3f});')
    has_logo = (ROOT / "assets" / "logo.png").exists()
    if has_logo:
        js.append(f'tl.fromTo("#logo", {{autoAlpha:0, scale:0.6}}, {{autoAlpha:1, scale:1, duration:0.45, ease:"back.out(2)"}}, {kh:.3f});')
    js.append(f'tl.fromTo("#cta-name", {{autoAlpha:0, y:30}}, {{autoAlpha:1, y:0, duration:0.35, ease:"power2.out"}}, {kh:.3f});')
    js.append(f'tl.fromTo("#cta-en", {{autoAlpha:0, y:30}}, {{autoAlpha:1, y:0, duration:0.35, ease:"power2.out"}}, {land:.3f});')
    js.append(f'tl.fromTo("#cta-ul", {{scaleX:0, transformOrigin:"0% 50%"}}, {{scaleX:1, duration:0.7, ease:"power2.out"}}, {land + 0.3:.3f});')
    js.append(f'tl.fromTo("#pill", {{autoAlpha:0, scale:0.4}}, {{autoAlpha:1, scale:1, duration:0.45, ease:"back.out(2.6)"}}, {wa:.3f});')
    p1 = wa + 0.45                                   # pulse peaks 0.15 s later = bgm3's hit (music.py)
    for k in range(2):
        js.append(f'tl.to("#pill", {{scale:1.08, duration:0.15, ease:"sine.out", yoyo:true, repeat:1}}, {p1 + k * 0.8:.3f});')
    js.append(f'tl.fromTo("#cta-fin", {{autoAlpha:0, y:16}}, {{autoAlpha:0.85, y:0, duration:0.6, ease:"power1.out"}}, {fin:.3f});')
    js.append(f'tl.set("#black", {{opacity:1}}, {TOTAL - 1 / 30:.4f});')
    leak_at = b34 - 0.3

    css = f"""
@font-face {{ font-family:"Hind Siliguri"; src:url(assets/fonts/hind-siliguri-bengali-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; unicode-range:U+0951-0952,U+0964-0965,U+0980-09FE,U+1CD0,U+1CD2,U+1CD5-1CD6,U+1CD8,U+1CE1,U+1CEA,U+1CED,U+1CF2,U+1CF5-1CF7,U+200C-200D,U+20B9,U+25CC,U+A8F1; }}
@font-face {{ font-family:"Hind Siliguri"; src:url(assets/fonts/hind-siliguri-latin-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD; }}
@font-face {{ font-family:"Montserrat"; src:url(assets/fonts/montserrat-latin-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; }}
@font-face {{ font-family:"Montserrat"; src:url(assets/fonts/montserrat-latin-800-normal.woff2) format("woff2"); font-weight:800; font-display:block; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:#000; }}
#root {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; font-family:"Hind Siliguri", sans-serif; }}
.scene {{ position:absolute; inset:0; overflow:hidden; visibility:hidden; }}
.push, .cam, .hw {{ position:absolute; inset:0; }}
.cam video, .cam img {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
.grade {{ position:absolute; inset:0; pointer-events:none; }}
.grade.gold {{ background:radial-gradient(1200px 1400px at 60% 30%, rgba(255,196,96,.30), rgba(255,160,60,.12) 70%); mix-blend-mode:soft-light; backdrop-filter:saturate(1.12); }}
.grade.cold {{ background:linear-gradient(180deg, rgba(120,150,190,.24), rgba(90,115,160,.2)); mix-blend-mode:soft-light; backdrop-filter:saturate(.72) contrast(1.14); }}
.grade.cool {{ background:linear-gradient(180deg, rgba(110,140,185,.26), rgba(80,100,140,.24)); mix-blend-mode:soft-light; backdrop-filter:saturate(.6) brightness(.95); }}
.grade.warm {{ background:radial-gradient(1100px 1300px at 55% 35%, rgba(255,214,160,.20), rgba(255,190,120,.08) 70%); mix-blend-mode:soft-light; backdrop-filter:saturate(1.04); }}
.grade.vivid {{ background:rgba(255,240,220,.06); mix-blend-mode:soft-light; backdrop-filter:saturate(1.16) contrast(1.05); }}
#flash {{ position:absolute; inset:0; z-index:40; background:#fff; opacity:0; pointer-events:none; }}
#dark {{ position:absolute; inset:0; z-index:40; background:#05080d; opacity:0; pointer-events:none; }}
#black {{ position:absolute; inset:0; z-index:90; background:#000; opacity:0; pointer-events:none; }}
.cap {{ position:absolute; left:{COL_L}px; width:{0.80 * W:.0f}px; translate:0 -50%; z-index:30; text-align:center;
  font-weight:700; font-size:64px; line-height:1.38; color:#fff; visibility:hidden;
  -webkit-text-stroke:6px rgba(8,14,26,.55); paint-order:stroke fill;
  text-shadow:0 3px 14px rgba(0,0,0,.6), 0 1px 3px rgba(0,0,0,.7); }}
.cap.thought {{ font-style:italic; font-size:54px; }}
.w {{ display:inline-block; transform-origin:50% 60%; }}
.head {{ position:absolute; left:{COL_L}px; width:{COL_W}px; z-index:35; text-align:center; visibility:hidden;
  color:#fff; font-weight:700; font-size:52px; line-height:1.3; }}
.head > * {{ display:block; }}
.head {{ display:flex; flex-direction:column; align-items:center; }}
.head span.en {{ font-family:"Montserrat", sans-serif; font-weight:800; color:{YEL}; font-size:58px; letter-spacing:.04em; }}
.head span.sub {{ font-size:42px; margin-top:4px; }}
.head {{ padding:16px 34px 14px; border-radius:22px; background:rgba(11,37,69,.78); width:max-content; max-width:{COL_W}px;
  left:{COL_L + COL_W / 2:.0f}px; translate:-50% 0; box-shadow:0 10px 30px -12px rgba(0,0,0,.5); }}
.head span.en {{ white-space:nowrap; }}
.head.left {{ left:{COL_L}px; translate:0 0; max-width:520px; align-items:flex-start; text-align:left; }}
.head.left span.en {{ white-space:normal; }}
#navy {{ position:absolute; inset:0; z-index:20; background:{NAVY}; opacity:0; pointer-events:none; }}
#motif {{ position:absolute; inset:0; z-index:21; opacity:.2; visibility:hidden; pointer-events:none; }}
#motif line, #motif path {{ stroke:{YEL}; stroke-width:3; fill:none; stroke-linecap:round; }}
#motif circle {{ fill:{YEL}; }}
.cta {{ position:absolute; left:{COL_L}px; width:{COL_W}px; z-index:36; text-align:center; visibility:hidden; color:#fff; }}
#cta-head {{ top:{0.14 * H:.0f}px; left:{COL_L + COL_W / 2:.0f}px; width:auto; translate:-50% 0; white-space:nowrap; font-weight:700; font-size:58px;
  background:rgba(11,37,69,.86); padding:18px 40px 14px; border-radius:24px; box-shadow:0 12px 34px -12px rgba(0,0,0,.55); }}
#logo {{ position:absolute; left:{COL_L + COL_W / 2 - 150:.0f}px; top:{0.255 * H:.0f}px; width:300px; height:300px; border-radius:50%; z-index:36;
  background:#fff; padding:10px; visibility:hidden; box-shadow:0 14px 40px -12px rgba(0,0,0,.6); }}
#logo img {{ width:100%; height:100%; border-radius:50%; object-fit:contain; display:block; }}
#cta-name {{ top:{0.44 * H:.0f}px; translate:0 -50%; font-weight:700; font-size:70px; line-height:1.28; text-shadow:0 4px 18px rgba(0,0,0,.45); }}
#cta-en {{ top:{0.52 * H:.0f}px; translate:0 -50%; font-family:"Montserrat", sans-serif; font-weight:700; font-size:38px; color:{YEL}; letter-spacing:.01em; }}
#cta-ul {{ display:block; margin:12px auto 0; width:78%; height:4px; border-radius:2px; background:{YEL}; }}
#pill {{ top:{0.62 * H:.0f}px; left:{COL_L + COL_W / 2:.0f}px; width:auto; translate:-50% -50%; white-space:nowrap; display:flex; align-items:center; gap:18px;
  background:#fff; color:{NAVY}; border-radius:999px; padding:26px 46px 24px; font-family:"Montserrat", sans-serif; font-weight:800; font-size:54px;
  box-shadow:0 18px 44px -14px rgba(0,0,0,.6); }}
#pill svg {{ width:58px; height:58px; flex:none; }}
#cta-fin {{ top:{0.72 * H:.0f}px; translate:0 -50%; font-weight:700; font-size:46px; line-height:1.35; }}
"""
    chat = (f'<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="{NAVY}" d="M12 3C6.5 3 2 6.8 2 11.5c0 2.4 1.2 4.6 3.1 6.1'
            'L4.4 21l3.9-1.9c1.2.4 2.4.6 3.7.6 5.5 0 10-3.8 10-8.5S17.5 3 12 3z"/><circle cx="8" cy="11.5" r="1.3" fill="#fff"/>'
            '<circle cx="12" cy="11.5" r="1.3" fill="#fff"/><circle cx="16" cy="11.5" r="1.3" fill="#fff"/></svg>')
    logo = '<div id="logo"><img src="assets/logo.png" alt="KDSA logo" /></div>' if has_logo else ""
    body = f"""<!doctype html>
<html lang="bn"><head><meta charset="UTF-8" /><meta name="viewport" content="width={W}, height={H}" />
<title>Khulna Digital Surveyor Association ad</title><style>{css}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="{W}" data-height="{H}">
{''.join(html)}
  <div id="navy"></div>
  <svg id="motif" viewBox="0 0 {W} {H}"><g id="contours">{contours}</g>{''.join(lines)}{''.join(pegs)}</svg>
  <div id="flash"></div>
  <div id="dark"></div>
  <div id="leak34" data-composition-id="organic-light-leak-overlay" data-composition-src="compositions/organic-light-leak-overlay.html"
    data-start="{leak_at:.3f}" data-duration="0.6" data-width="{W}" data-height="{H}" data-track-index="30" style="position:absolute;inset:0;z-index:41"></div>
  {''.join(cap_html)}
  {''.join(heads)}
  <div class="cta" id="cta-head">জমির সীমানা নিয়ে দুশ্চিন্তা?</div>
  {logo}
  <div class="cta" id="cta-name">খুলনা বিভাগীয় ডিজিটাল<br>সার্ভেয়ার এসোসিয়েশন</div>
  <div class="cta" id="cta-en">Land Demarcation &amp; Pantograph Services<span id="cta-ul"></span></div>
  <div class="cta" id="pill">{chat}<span>WhatsApp: 01911-888183</span></div>
  <div class="cta" id="cta-fin">আপনার জমি, সঠিক পরিমাপের কাজে<br>আমরা আপনার পাশে।</div>
  <div id="black"></div>
  <audio id="mix" src="assets/mix.wav" data-start="0" data-duration="{TOTAL:.3f}" data-track-index="40"></audio>
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
    sched = {"scene8": {"part_a_headline": s8a, "part_b_khulna": kh, "english_line": land, "whatsapp_pill": wa,
                        "pill_first_pulse_peak": round(p1 + 0.15, 3), "bgm3_hit": MUS["bgm3_hit_at"], "final_line": fin},
             "caption_words": len(sync)}
    (ROOT / "out" / "sync.json").write_text(json.dumps({"schedule": sched, "words": sync}, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"built index.html {TOTAL:.2f}s, {cid} caption chunks, {len(sync)} words, logo={'yes' if has_logo else 'no'}")
    print(json.dumps(sched, indent=1))


if __name__ == "__main__":
    main()
