#!/usr/bin/env python3
"""seen-ammu -> index.html + build/sfx.json + build/music_env.json.
HyperFrames 0.9.23 contract: data-start/data-duration/data-media-start, class="clip", one paused GSAP timeline on
window.__timelines["main"], set/to/fromTo only, deterministic (seeded) values. Generic chat UI: no app names or logos."""
import json
import math
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "build"
TL = json.loads((B / "timeline.json").read_text())
S = {s["n"]: s for s in TL["slots"]}
TOTAL, END = TL["total"], TL["end_card"]
GOLD, TEAL = "#F2C46B", "#0F4C5C"
T = lambda x: f"{x:.3f}"
html, js, sfx = [], [], []
st = lambda n: S[n]["start"]
CUE = TL["cues"]


def cue(name, t, gain):
    sfx.append({"sfx": name, "t": round(t, 3), "gain": gain})


def gold(text):
    for wd in ("রিপ্লাই", "ভাত", "মা"):
        text = re.sub(f"(?<![\\u0980-\\u09FF]){wd}" if wd == "মা" else wd, f"<b>{wd}</b>", text)
    return text


# ------------------------------------------------------------------ shots
for n in range(1, 7):
    s = S[n]
    html.append(f'<div class="shot" id="sh{n}" style="z-index:{n}"><div class="mv" id="mv{n}" data-layout-allow-overflow><video id="v{n}" class="clip" '
                f'src="build/c{n}.mp4" muted playsinline data-start="{T(s["clip_start"])}" data-duration="{T(s["clip_dur"])}" data-media-start="0" '
                f'data-track-index="{n}"></video></div></div>')
    js.append(f'tl.fromTo("#mv{n}", {{scale:1.0}}, {{scale:1.04, duration:{T(s["clip_dur"])}, ease:"none", immediateRender:false}}, {T(s["clip_start"])});')
js.append('tl.set("#sh1", {opacity:1}, 0);')
js.append('tl.fromTo("#black", {opacity:1}, {opacity:0, duration:0.5, ease:"power1.out", immediateRender:false}, 0);')

# RGB-split glitch cuts 1->2, 2->3 (0.25 s): channel-split copies of the incoming clip, offset and jittered
for n in (2, 3):
    t = st(n)
    s = S[n]
    chans = "".join(f'<video id="g{n}{c}" class="clip gch {c}" src="build/c{n}.mp4" muted playsinline data-start="{T(t)}" data-duration="0.267" '
                    f'data-media-start="{0.001 * (i + 1):.3f}" data-track-index="{10 + i}"></video>' for i, c in enumerate("rgb"))
    html.append(f'<div class="glitch" id="gl{n}" style="z-index:{n}"><div class="gbars" id="gb{n}"></div>{chans}</div>')
    js.append(f'tl.set("#sh{n - 1}", {{x:-18}}, {T(t - 0.08)}); tl.set("#sh{n - 1}", {{x:14}}, {T(t - 0.04)});')
    js.append(f'tl.set("#gl{n}", {{opacity:1}}, {T(t)}); tl.set("#sh{n - 1}", {{opacity:0, x:0}}, {T(t)});')
    for k, (dr, db, by) in enumerate([(30, -30, 300), (-22, 26, 1100), (14, -12, 700), (6, -6, 1500)]):
        tk = t + k * 0.06
        js.append(f'tl.set("#g{n}r", {{x:{dr}}}, {T(tk)}); tl.set("#g{n}b", {{x:{db}}}, {T(tk)}); tl.set("#gb{n}", {{y:{by}}}, {T(tk)});')
    js.append(f'tl.set("#sh{n}", {{opacity:1}}, {T(t + 0.25)}); tl.set("#gl{n}", {{opacity:0}}, {T(t + 0.25)});')
    cue("glitch_digital", t - 0.05, 0.45)
    cue("whoosh_fast", t - 0.1, 0.25)
# hard cut to black 3 -> 4 (24.0-24.5 black), then hard cut in
js.append(f'tl.set("#sh3", {{opacity:0}}, {T(S[3]["end"])}); tl.set("#sh4", {{opacity:1}}, {T(st(4))});')
# soft crossfades 4->5, 5->6 (0.6 s)
for n in (5, 6):
    js.append(f'tl.fromTo("#sh{n}", {{opacity:0}}, {{opacity:1, duration:0.6, ease:"sine.inOut", immediateRender:false}}, {T(st(n) - 0.3)});')
    js.append(f'tl.set("#sh{n - 1}", {{opacity:0}}, {T(st(n) + 0.3)});')

# ------------------------------------------------------------------ overlays (generic UI)
# slot 1: incoming call card (lower-middle, over the keyboard/desk) -> red decline slides away
t0 = st(1)
html.append('''<div class="ov" id="call"><div class="cav">আ</div><div class="cname">আম্মু</div><div class="csub" id="csub">মোবাইল · কল আসছে…</div>
<div class="cbtns"><div class="cb dec" id="dec"><svg viewBox="0 0 24 24" width="54" height="54"><path fill="#fff" d="M12 9c-1.6 0-3.2.3-4.6.8v3.1c0 .4-.2.7-.6.9-1 .5-1.9 1.1-2.6 1.8-.2.2-.4.3-.7.3-.3 0-.5-.1-.7-.3L.3 13.1c-.2-.2-.3-.4-.3-.7 0-.3.1-.5.3-.7C3.3 8.8 7.4 7 12 7s8.7 1.8 11.7 4.7c.2.2.3.4.3.7 0 .3-.1.5-.3.7l-2.5 2.5c-.2.2-.4.3-.7.3-.3 0-.5-.1-.7-.3-.8-.7-1.6-1.3-2.6-1.8-.3-.2-.6-.5-.6-.9V9.8C15.2 9.3 13.6 9 12 9z"/></svg></div>
<div class="cb acc"><svg viewBox="0 0 24 24" width="50" height="50"><path fill="#fff" d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1l-2.3 2.2z"/></svg></div></div></div>''')
js.append(f'tl.fromTo("#call", {{autoAlpha:0, y:80, scale:0.94}}, {{autoAlpha:1, y:0, scale:1, duration:0.4, ease:"power3.out"}}, {T(t0 + 0.3)});')
js.append(f'tl.fromTo(".cav", {{boxShadow:"0 0 0 0px rgba(255,255,255,.35)"}}, {{boxShadow:"0 0 0 26px rgba(255,255,255,0)", duration:0.8, repeat:1, ease:"sine.out"}}, {T(t0 + 0.5)});')
tdec = CUE["decline"]                               # on "কেটে দিতাম"
js.append(f'tl.to("#dec", {{x:520, duration:0.35, ease:"power2.in"}}, {T(tdec)});')
js.append(f'tl.set("#csub", {{textContent:"কল কেটে দেওয়া হয়েছে"}}, {T(tdec + 0.3)});')
js.append(f'tl.to("#call", {{autoAlpha:0, y:120, duration:0.35, ease:"power2.in"}}, {T(tdec + 0.9)});')
cue("pop_notification", t0 + 0.3, 0.3)
cue("click_ui", tdec, 0.45)
cue("whoosh_fast", tdec + 0.05, 0.2)

# slot 2: chat bubble + Seen + typing dots that never resolve (top)
t0 = st(2)
html.append('''<div class="ov" id="chat2"><div class="chdr"><div class="sav">আ</div><span>আম্মু</span></div>
<div class="bub in" id="b2">বাবা, ভাত খেয়েছো?<small>রাত ১০:১২</small></div>
<div class="seen" id="seen2">Seen ✓✓</div>
<div class="dots" id="dots2"><i id="d0"></i><i id="d1"></i><i id="d2"></i></div></div>''')
js.append(f'tl.fromTo("#chat2", {{autoAlpha:0, y:-40}}, {{autoAlpha:1, y:0, duration:0.35, ease:"power3.out"}}, {T(t0 + 0.35)});')
js.append(f'tl.fromTo("#b2", {{autoAlpha:0, scale:0.75, transformOrigin:"0% 100%"}}, {{autoAlpha:1, scale:1, duration:0.25, ease:"back.out(2)"}}, {T(t0 + 0.6)});')
tseen = CUE["seen"]                                 # on "Seen হতো"
tdots, tdots_end = tseen + 0.5, S[2]["end"] - 0.6
reps = max(1, int((tdots_end - tdots) / 0.3) - 1) | 1   # odd -> ends low
js.append(f'tl.fromTo("#seen2", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.2}}, {T(tseen)});')
js.append(f'tl.fromTo("#dots2", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.2}}, {T(tdots)});')
for k in range(3):
    js.append(f'tl.fromTo("#d{k}", {{y:0, opacity:0.4}}, {{y:-10, opacity:1, duration:0.3, yoyo:true, repeat:{reps}, ease:"sine.inOut", immediateRender:false}}, {T(tdots + k * 0.15)});')
js.append(f'tl.to("#dots2", {{autoAlpha:0, duration:0.3}}, {T(tdots_end)});')
js.append(f'tl.to("#chat2", {{autoAlpha:0, duration:0.2}}, {T(S[2]["end"] - 0.25)});')
cue("pop_notification", t0 + 0.6, 0.3)
cue("click_ui", tseen, 0.25)

# slot 3: notification stack from the top
t0 = st(3)
html.append('<div class="ov" id="nst"><div class="nhead" id="nh">আম্মু: <b>৩টি মিসড কল</b></div>' + "".join(
    f'<div class="ncard" id="nc{k}"><div class="nicon">📞</div><div><div class="nt">আম্মু</div><div class="nm">মিসড কল · {tm}</div></div></div>'
    for k, tm in enumerate(("রাত ৯:৪০", "রাত ১০:০৫", "রাত ১০:৩১"))) + '</div>')
js.append(f'tl.set("#nst", {{visibility:"visible"}}, {T(t0 + 0.5)});')
for k in range(3):
    js.append(f'tl.fromTo("#nc{k}", {{autoAlpha:0, y:-160}}, {{autoAlpha:1, y:0, duration:0.35, ease:"back.out(1.4)"}}, {T(t0 + 0.5 + k * 0.55)});')
    cue("pop_notification", t0 + 0.5 + k * 0.55, 0.28)
js.append(f'tl.fromTo("#nh", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.25}}, {T(t0 + 2.2)});')
js.append(f'tl.to("#nst", {{autoAlpha:0, y:-80, duration:0.3, ease:"power2.in"}}, {T(S[3]["end"] - 0.45)});')

# slot 5 (source PT-6): unread counter -> 47, voice-note waveform playing while the music dips
t0 = st(5)
bars = "".join(f'<i class="wb" id="wb{k}" style="height:{14 + int(46 * abs(math.sin(k * 0.9) * math.cos(k * 0.37)))}px"></i>' for k in range(32))
html.append(f'''<div class="ov" id="inbox"><div class="row"><div class="sav">আ</div><div class="rtxt"><div class="nt">আম্মু</div><div class="nm">🎤 ভয়েস মেসেজ</div></div>
<div class="badge" id="badge">০</div></div>
<div class="vn" id="vn"><div class="play" id="play">▶</div><div class="wave">{bars}<div class="prog" id="prog"></div></div><span class="vt" id="vt">০:০৪</span></div></div>''')
js.append(f'tl.fromTo("#inbox", {{autoAlpha:0, y:-40}}, {{autoAlpha:1, y:0, duration:0.35, ease:"power3.out"}}, {T(t0 + 0.4)});')
BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
for k, val in enumerate([3, 9, 17, 26, 34, 41, 45, 47]):
    js.append(f'tl.set("#badge", {{textContent:"{str(val).translate(BN)}"}}, {T(t0 + 0.7 + k * 0.13)});')
js.append(f'tl.fromTo("#badge", {{scale:1}}, {{scale:1.25, duration:0.12, yoyo:true, repeat:1, immediateRender:false}}, {T(t0 + 1.62)});')
cue("pop_notification", t0 + 1.62, 0.3)
VN0, VN1 = CUE["voice_note"]                    # voice note plays; music dips over the same span (mix.py)
js.append(f'tl.fromTo("#vn", {{autoAlpha:0, y:30}}, {{autoAlpha:1, y:0, duration:0.3, ease:"power3.out"}}, {T(VN0 - 0.5)});')
js.append(f'tl.set("#play", {{textContent:"❚❚"}}, {T(VN0)}); tl.set("#play", {{textContent:"▶"}}, {T(VN1)});')
js.append(f'tl.fromTo("#prog", {{scaleX:0}}, {{scaleX:1, duration:{T(VN1 - VN0)}, ease:"none", immediateRender:false}}, {T(VN0)});')
for k in range(32):
    js.append(f'tl.fromTo("#wb{k}", {{scaleY:0.35}}, {{scaleY:1, duration:0.2, yoyo:true, repeat:{9 + k % 3}, ease:"sine.inOut", immediateRender:false}}, {T(VN0 + (k % 6) * 0.04)});')
for k, sec in enumerate([3, 2, 1, 0]):
    js.append(f'tl.set("#vt", {{textContent:"০:০{str(sec).translate(BN)}"}}, {T(VN0 + 1.0 + k * 1.0)});')
js.append(f'tl.to("#inbox", {{autoAlpha:0, duration:0.3}}, {T(S[5]["end"] - 0.35)});')
cue("click_ui", VN0, 0.3)

# slot 6 (source PT-7): types the reply -> bubble -> Delivered
t0 = st(6)
reply = "আম্মু, ভাত খেয়েছি"
clusters, cur = [], ""
for ch in reply:                                    # grapheme-ish clusters so Bangla conjuncts never break mid-typing
    if cur and (unicodedata.category(ch) in ("Mn", "Mc") or cur.endswith("্") or ch == "্"):
        cur += ch
    else:
        if cur:
            clusters.append(cur)
        cur = ch
clusters.append(cur)
html.append('''<div class="ov" id="chat6"><div class="chdr"><div class="sav">আ</div><span>আম্মু</span></div>
<div class="bub in old">বাবা, ভাত খেয়েছো?</div>
<div class="bub out" id="b6">আম্মু, ভাত খেয়েছি<small id="del">Delivered ✓✓</small></div>
<div class="inp"><span id="typed"></span><i class="caret" id="caret"></i><div class="send" id="send">➤</div></div></div>''')
js.append(f'tl.fromTo("#chat6", {{autoAlpha:0, y:-40}}, {{autoAlpha:1, y:0, duration:0.35, ease:"power3.out"}}, {T(t0 + 0.5)});')
tt, acc = CUE["reply_type"] + 0.2, ""
for k, c in enumerate(clusters):
    acc += c
    js.append(f'tl.set("#typed", {{textContent:"{acc}"}}, {T(tt + k * 0.17)});')
cue("typing_keys", tt, 0.3)
tsend = tt + len(clusters) * 0.17 + 0.35
js.append(f'tl.fromTo("#send", {{scale:1}}, {{scale:0.8, duration:0.08, yoyo:true, repeat:1, immediateRender:false}}, {T(tsend)});')
js.append(f'tl.set("#typed", {{textContent:""}}, {T(tsend + 0.1)});')
js.append(f'tl.fromTo("#b6", {{autoAlpha:0, scale:0.75, transformOrigin:"100% 100%"}}, {{autoAlpha:1, scale:1, duration:0.25, ease:"back.out(2)"}}, {T(tsend + 0.12)});')
js.append(f'tl.fromTo("#del", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.2}}, {T(tsend + 1.0)});')
js.append(f'tl.to("#chat6", {{autoAlpha:0, duration:0.3}}, {T(END - 0.3)});')
cue("click_ui", tsend, 0.35)
cue("pop_notification", tsend + 0.12, 0.3)
cue("chime_success", tsend + 1.0, 0.3)

# ------------------------------------------------------------------ kinetic captions (one phrase at a time)
cid = 0
for c in TL["captions"]:                            # phrase chunks timed to the voiceover (prep.py)
    s0, s1 = c["start"] - 0.05, min(c["end"], END)
    html.append(f'<div class="cap" id="cp{cid}"><span>{gold(c["text"])}</span></div>')
    js.append(f'tl.fromTo("#cp{cid}", {{autoAlpha:0, scale:0.85}}, {{autoAlpha:1, scale:1, duration:0.18, ease:"back.out(2.2)"}}, {T(s0)});')
    js.append(f'tl.to("#cp{cid}", {{autoAlpha:0, duration:0.15}}, {T(s1 - 0.17)});')
    cid += 1

# ------------------------------------------------------------------ tag (first 3 s), grain, end card
html.append('<div id="tag">সত্য ঘটনা থেকে অনুপ্রাণিত</div>')
js.append('tl.fromTo("#tag", {autoAlpha:0, x:-20}, {autoAlpha:1, x:0, duration:0.4, ease:"power2.out"}, 0.3);')
js.append('tl.to("#tag", {autoAlpha:0, duration:0.3}, 2.7);')
k = 0
while k * (1 / 12) < TOTAL:                         # seek-safe grain: deterministic offsets, 12 changes / s
    js.append(f'tl.set("#grain", {{backgroundPosition:"{(k * 211) % 640}px {(k * 367) % 640}px"}}, {T(k / 12)});')
    k += 1
html.append('<div id="dark"></div><div id="endtxt">আজই <b>মা</b>কে <b>রিপ্লাই</b> দিন</div>')
js.append(f'tl.fromTo("#dark", {{opacity:0}}, {{opacity:0.62, duration:0.5, ease:"power1.out", immediateRender:false}}, {T(END)});')
js.append(f'tl.fromTo("#endtxt", {{autoAlpha:0, scale:0.9}}, {{autoAlpha:1, scale:1, duration:0.35, ease:"back.out(1.8)"}}, {T(END + 0.2)});')
js.append(f'tl.to("#black", {{opacity:1, duration:0.45, ease:"power1.in"}}, {T(TOTAL - 0.45)});')
cue("chime_success", END + 0.2, 0.25)

FONTS = "".join(f'@font-face {{ font-family:"Hind Siliguri"; src:url(fonts/hind-siliguri-{sub}-{w}-normal.woff2) format("woff2"); font-weight:{w}; font-display:block; '
                f'unicode-range:{"U+0964-0965,U+0980-09FE,U+200C-200D,U+25CC" if sub == "bengali" else "U+0000-00FF,U+2000-206F,U+2190-22FF"}; }}\n'
                for w in (600, 700) for sub in ("bengali", "latin"))
CSS = FONTS + f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#000; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#000; font-family:"Hind Siliguri", sans-serif; color:#fff; }}
.shot {{ position:absolute; inset:0; opacity:0; overflow:hidden; }}
.mv {{ position:absolute; inset:0; }}
.mv video, .gch {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; filter:saturate(.88) contrast(1.08) brightness(.95); }}
.glitch {{ position:absolute; inset:0; opacity:0; background:#000; overflow:hidden; isolation:isolate; }}
.gch {{ mix-blend-mode:screen; }}
.gch.r {{ filter:url(#fr); }} .gch.g {{ filter:url(#fg); }} .gch.b {{ filter:url(#fb); }}
.gbars {{ position:absolute; left:0; top:0; width:100%; height:140px; z-index:5; background:repeating-linear-gradient(0deg, rgba(255,255,255,.12) 0 4px, rgba(0,0,0,0) 4px 12px); mix-blend-mode:screen; }}
#teal {{ position:absolute; inset:0; z-index:10; background:{TEAL}; mix-blend-mode:soft-light; opacity:.42; pointer-events:none; }}
#amber {{ position:absolute; inset:0; z-index:11; background:radial-gradient(ellipse 70% 55% at 50% 45%, rgba(255,170,80,.30), rgba(255,170,80,0) 70%); mix-blend-mode:overlay; pointer-events:none; }}
#vig {{ position:absolute; inset:0; z-index:12; pointer-events:none; background:radial-gradient(ellipse 78% 64% at 50% 48%, rgba(0,0,0,0) 58%, rgba(0,0,0,.48) 100%); }}
#grain {{ position:absolute; inset:0; z-index:13; pointer-events:none; background:url(build/grain.png); background-size:640px 640px; opacity:.08; mix-blend-mode:overlay; }}
.ov {{ position:absolute; z-index:30; visibility:hidden; font-family:"Hind Siliguri", sans-serif; }}
#call {{ left:150px; top:900px; width:780px; padding:34px 40px 36px; border-radius:36px; background:rgba(22,26,32,.82); border:1px solid rgba(255,255,255,.12);
  display:flex; flex-direction:column; align-items:center; box-shadow:0 30px 80px -20px rgba(0,0,0,.8); }}
.cav {{ width:130px; height:130px; border-radius:50%; background:#5B6B7A; display:flex; align-items:center; justify-content:center; font-size:64px; font-weight:700; }}
.cname {{ margin-top:14px; font-size:62px; font-weight:700; }}
.csub {{ font-size:32px; font-weight:600; color:#C9D2DC; }}
.cbtns {{ margin-top:26px; width:100%; display:flex; justify-content:space-between; padding:0 40px; }}
.cb {{ width:116px; height:116px; border-radius:50%; display:flex; align-items:center; justify-content:center; }}
.cb.dec {{ background:#E5484D; }} .cb.acc {{ background:#30A46C; }}
#chat2, #chat6 {{ left:90px; top:190px; width:900px; padding:24px 28px 28px; border-radius:30px; background:rgba(245,247,250,.95); color:#14181F; box-shadow:0 24px 60px -18px rgba(0,0,0,.7); }}
.chdr {{ display:flex; align-items:center; gap:16px; font-size:36px; font-weight:700; padding-bottom:16px; border-bottom:1px solid #DDE2E8; margin-bottom:18px; }}
.sav {{ width:64px; height:64px; border-radius:50%; background:#5B6B7A; color:#fff; display:flex; align-items:center; justify-content:center; font-size:32px; font-weight:700; }}
.bub {{ max-width:78%; font-size:44px; font-weight:700; line-height:1.35; padding:14px 26px 10px; border-radius:28px; }}
.bub small {{ display:block; font-size:28px; font-weight:600; opacity:.6; margin-top:2px; }}
.bub.in {{ background:#E4E8ED; color:#14181F; border-bottom-left-radius:8px; }}
.bub.out {{ background:#2F6FDB; color:#fff; margin-left:auto; margin-top:14px; border-bottom-right-radius:8px; visibility:hidden; }}
.bub.out small {{ text-align:right; visibility:hidden; opacity:.85; }}
.bub.old {{ font-size:34px; opacity:.75; }}
.seen {{ font-size:28px; font-weight:600; color:#6B7684; margin:8px 0 0 10px; visibility:hidden; }}
.dots {{ margin:14px 0 0 0; width:120px; height:60px; border-radius:30px; background:#E4E8ED; display:flex; align-items:center; justify-content:center; gap:10px; visibility:hidden; }}
.dots i {{ width:14px; height:14px; border-radius:50%; background:#7B8794; display:block; }}
.inp {{ margin-top:22px; display:flex; align-items:center; min-height:84px; border-radius:42px; background:#fff; border:2px solid #DDE2E8; padding:8px 12px 4px 30px; font-size:42px; font-weight:700; color:#14181F; }}
.caret {{ display:inline-block; width:3px; height:44px; background:#2F6FDB; margin-left:4px; }}
.send {{ margin-left:auto; width:66px; height:66px; border-radius:50%; background:#2F6FDB; color:#fff; display:flex; align-items:center; justify-content:center; font-size:30px; }}
#nst {{ left:80px; top:150px; width:920px; display:flex; flex-direction:column; gap:14px; }}
.nhead {{ font-size:38px; font-weight:700; text-shadow:0 2px 12px rgba(0,0,0,.8); visibility:hidden; padding-left:8px; }}
.nhead b {{ color:{GOLD}; }}
.ncard {{ display:flex; align-items:center; gap:22px; padding:20px 26px 16px; border-radius:28px; background:rgba(242,245,248,.92); color:#14181F; visibility:hidden; box-shadow:0 16px 40px -14px rgba(0,0,0,.7); }}
.nicon {{ width:72px; height:72px; border-radius:18px; background:#E5484D; display:flex; align-items:center; justify-content:center; font-size:38px; }}
.nt {{ font-size:36px; font-weight:700; line-height:1.2; }} .nm {{ font-size:30px; font-weight:600; color:#5A6271; }}
#inbox {{ left:90px; top:190px; width:900px; display:flex; flex-direction:column; gap:16px; }}
.row {{ display:flex; align-items:center; gap:20px; padding:22px 28px 18px; border-radius:28px; background:rgba(242,245,248,.94); color:#14181F; }}
.rtxt {{ flex:1; }}
.badge {{ min-width:84px; height:84px; padding:0 18px; border-radius:42px; background:#E5484D; color:#fff; display:flex; align-items:center; justify-content:center; font-size:44px; font-weight:700; padding-top:6px; }}
.vn {{ display:flex; align-items:center; gap:18px; padding:20px 26px; border-radius:28px; background:rgba(242,245,248,.94); color:#14181F; visibility:hidden; }}
.play {{ width:80px; height:80px; border-radius:50%; background:#2F6FDB; color:#fff; display:flex; align-items:center; justify-content:center; font-size:30px; flex:none; }}
.wave {{ position:relative; flex:1; height:72px; display:flex; align-items:center; gap:6px; }}
.wb {{ width:10px; border-radius:5px; background:#8A96A3; display:block; }}
.prog {{ position:absolute; inset:0; background:linear-gradient(90deg, rgba(47,111,219,.28), rgba(47,111,219,.28)); transform-origin:0% 50%; border-radius:8px; mix-blend-mode:multiply; }}
.vt {{ font-size:32px; font-weight:700; color:#5A6271; }}
.cap {{ position:absolute; left:90px; width:900px; bottom:300px; z-index:40; text-align:center; visibility:hidden; }}
.cap span {{ display:inline-block; font-weight:700; font-size:60px; line-height:1.38; color:#fff; text-shadow:0 2px 8px rgba(0,0,0,.75), 0 6px 26px rgba(0,0,0,.55); }}
.cap b, #endtxt b {{ color:{GOLD}; font-weight:700; }}
#tag {{ position:absolute; left:70px; top:120px; z-index:41; visibility:hidden; font-size:32px; font-weight:600; color:#E9EEF2; padding:8px 20px 4px;
  border-left:4px solid {GOLD}; background:rgba(0,0,0,.35); border-radius:0 12px 12px 0; }}
#dark {{ position:absolute; inset:0; z-index:44; background:#000; opacity:0; }}
#endtxt {{ position:absolute; left:90px; width:900px; top:50%; translate:0 -50%; z-index:45; text-align:center; visibility:hidden; font-size:84px; font-weight:700; line-height:1.3;
  text-shadow:0 4px 24px rgba(0,0,0,.6); }}
#black {{ position:absolute; inset:0; z-index:60; background:#000; opacity:1; pointer-events:none; }}
"""
SVG = '''<svg width="0" height="0" style="position:absolute"><defs>
<filter id="fr"><feColorMatrix type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"/></filter>
<filter id="fg"><feColorMatrix type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0"/></filter>
<filter id="fb"><feColorMatrix type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0"/></filter></defs></svg>'''
shots = [h for h in html if h.startswith('<div class="shot"') or h.startswith('<div class="glitch"')]
rest = [h for h in html if h not in shots]
page = f"""<!doctype html>
<html lang="bn" data-resolution="portrait"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<title>Seen, Ammu</title><style>{CSS}</style></head>
<body>{SVG}
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="1080" data-height="1920">
{chr(10).join(shots)}
<div id="teal"></div><div id="amber"></div><div id="vig"></div><div id="grain"></div>
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
(B / "sfx.json").write_text(json.dumps(sorted(sfx, key=lambda x: x["t"]), indent=1))
(B / "music_env.json").write_text(json.dumps({"dip": [round(VN0 - 0.3, 3), round(VN1 + 0.3, 3)]}))
print(f"built index.html {TOTAL}s, {cid} captions, {len(sfx)} sfx, voice note {VN0:.2f}-{VN1:.2f}s")
