#!/usr/bin/env python3
"""Future Stack promo Reel -> index.html + sfx.json (HyperFrames, 1080x1920).

  python3 scripts/timeline.py && python3 scripts/words.py && python3 scripts/build.py && python3 scripts/mix.py

Style: the reference "effects showcase" (videos/style-ref/STYLE.md) in the FutureStack design system
(brand/futurestack/DESIGN.md, Social & Video): dark grade, right-hand checklist panel, one effect per beat,
hard jump cuts on removed pauses, Bangla subtitles per word in black boxes. Every section effect starts on that
section's first spoken word (= its first cut); in-section moments use whisper word times (words.json).
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1920
TL = json.loads((ROOT / "timeline.json").read_text())
WORDS = json.loads((ROOT / "words.json").read_text(encoding="utf-8"))
SEGS, SECS = TL["segments"], {s["n"]: s for s in TL["sections"]}
TOTAL, BLOW, CARD = TL["total"], TL["blow_at"], TL["card_at"]
BG, SURF, SURF2, BORDER, TEXT, MUTED = "#0B0D11", "#12151A", "#1D2128", "#2E343E", "#F1F3F6", "#A9B0BC"
BLUE, BLUE_HI, GREEN, RED, AMBER, WA = "#5683FF", "#8AA9FF", "#3CC48F", "#F26B5E", "#F0A23B", "#25D366"
FACE = (540, 660)                 # face centre in the 1080x1920 frame (from contact sheets)
BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")

js, html, sfx = [], [], []


def w(sec, text, nth=0):
    """Start time of the nth occurrence of a word (by prefix) in a section."""
    hits = [x for x in WORDS if x["section"] == sec and x["text"].startswith(text)]
    return hits[nth]["start"]


def seg_at(t):
    for s in SEGS:
        if s["t"] - 1e-6 <= t < s["t"] + s["dur"] - 1e-6:
            return s
    return SEGS[-1]


def live_video(vid, t0, t1, cls="", style=""):
    """A muted <video> showing the presenter exactly as the main picture does over [t0, t1] (clamped to one segment)."""
    s = seg_at(t0)
    t1 = min(t1, s["t"] + s["dur"])
    ms = s["src_in"] + (t0 - s["t"])
    return (f'<video id="{vid}" class="clip {cls}" src="media/clips/pt{s["clip"]}.mp4" muted playsinline style="{style}" '
            f'data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-media-start="{ms:.3f}" data-track-index="9"></video>')


def cue(name, t, gain=0.5):
    sfx.append({"sfx": name, "t": round(t, 3), "gain": gain})


def show(sel, t0, t1, fin=0.25, fout=0.2, frm="{autoAlpha:0, y:30}", to="{autoAlpha:1, y:0}"):
    js.append(f'tl.fromTo("{sel}", {frm}, {{...{to}, duration:{fin}, ease:"power3.out"}}, {t0:.3f});')
    js.append(f'tl.to("{sel}", {{autoAlpha:0, duration:{fout}, ease:"power1.in"}}, {t1 - fout:.3f});')


# ------------------------------------------------------------------ presenter (jump cuts)
for k, s in enumerate(SEGS):
    z = 1.0 if k % 2 == 0 else 1.12
    html.append(f'<div class="cam" id="cam{k}" style="transform:scale({z});transform-origin:50% 34%">'
                f'<video id="v{k}" class="clip" src="media/clips/pt{s["clip"]}.mp4" muted playsinline data-start="{s["t"]:.3f}" '
                f'data-duration="{s["dur"]:.3f}" data-media-start="{s["src_in"]:.3f}" data-track-index="1"></video></div>')
    js.append(f'tl.fromTo("#cam{k}", {{scale:{z}}}, {{scale:{z + 0.03:.2f}, duration:{s["dur"]:.3f}, ease:"none"}}, {s["t"]:.3f});')

# ------------------------------------------------------------------ section 1 : hook
s1, s2 = SECS[1]["start"], SECS[2]["start"]
html.append('<div class="titlepills" id="title"><span class="tp">সেল না হওয়ার ৩টা কারণ</span><span class="tp en">by Future Stack</span></div>')
show("#title", 0.05, s2 - 0.05, fin=0.3)
# live cursor + selection box around the face
html.append('''<div id="cursor"><svg viewBox="0 0 24 24" width="64" height="64"><path d="M4 2l16 9-7 2-3 7z" fill="#fff" stroke="#0B0D11" stroke-width="1.5"/></svg>
<span class="ctag">Future Stack</span></div>
<div id="selbox"><i class="h tl"></i><i class="h tr"></i><i class="h bl"></i><i class="h br"></i><span class="dim">1080 × 1920</span></div>''')
js.append('tl.fromTo("#cursor", {autoAlpha:0, x:880, y:1500}, {autoAlpha:1, x:700, y:900, duration:0.8, ease:"power2.inOut"}, 0.1);')
js.append('tl.to("#cursor", {scale:0.85, duration:0.08, yoyo:true, repeat:1}, 0.9);')
cue("click_ui", 0.9, 0.55)
js.append('tl.fromTo("#selbox", {autoAlpha:0, scale:0.9}, {autoAlpha:1, scale:1, duration:0.25, ease:"back.out(2)"}, 0.95);')
js.append('tl.to("#cursor", {x:760, y:1180, autoAlpha:0, duration:0.6, ease:"power2.in"}, 2.3);')
js.append('tl.to("#selbox", {autoAlpha:0, duration:0.25}, 2.6);')
# three numbered problem tiles (on the chest, never on the face), on "সমস্যা এই ৩টা জায়গায়"
tc = w(1, "সমস্যা", 1)
for i, (ico, lab) in enumerate((("⏱", "দেরিতে রিপ্লাই"), ("🔔", "ফলো-আপ নেই"), ("🌐", "শুধু ফেসবুক"))):
    x = 75 + i * 320
    html.append(f'<div class="ptile" id="cl{i}" style="left:{x}px"><span class="pico">{ico}</span><b>{str(i + 1).translate(BN)}</b><span class="plab">{lab}</span></div>')
    js.append(f'tl.fromTo("#cl{i}", {{autoAlpha:0, scale:0.3, y:80, rotation:{(-8, 0, 8)[i]}}}, {{autoAlpha:1, scale:1, y:0, rotation:0, duration:0.32, ease:"back.out(2.2)"}}, {tc + i * 0.14:.3f});')
    js.append(f'tl.to("#cl{i}", {{autoAlpha:0, y:-30, duration:0.15}}, {s2 - 0.15:.3f});')
    cue("pop_notification", tc + i * 0.14, 0.32)
cue("whoosh_fast", tc - 0.05, 0.35)

# ------------------------------------------------------------------ checklist panel (right)
items = [("০১", "দেরিতে রিপ্লাই"), ("০২", "ফলো-আপ নেই"), ("০৩", "শুধু ফেসবুক পেজ"), ("•", "ফ্রি অডিট")]
lis = "".join(f'<li id="pi{i}"><span class="num">{n}</span>{t}</li>' for i, (n, t) in enumerate(items))
html.append(f'<div id="panel"><div class="ph">এই ভিডিওতে <span id="pcount">০০/০৩</span></div><ul>{lis}</ul>'
            f'<div id="pbtn">কমেন্টে <b class="en">GROW</b></div></div>')
js.append(f'tl.fromTo("#panel", {{autoAlpha:0, x:60}}, {{autoAlpha:1, x:0, duration:0.35, ease:"power3.out"}}, {tc + 0.4:.3f});')
for i, sec in enumerate((2, 3, 4, 5)):
    t = SECS[sec]["start"]
    js.append(f'tl.set("#panel li", {{className:""}}, {t:.3f}); tl.set("#pi{i}", {{className:"on"}}, {t:.3f});')
    if i < 3:
        js.append(f'tl.set("#pcount", {{textContent:"{str(i + 1).zfill(2).translate(BN)}/০৩"}}, {t:.3f});')
js.append(f'tl.set("#pbtn", {{className:"gold"}}, {SECS[5]["start"]:.3f});')
js.append(f'tl.fromTo("#pbtn", {{scale:1}}, {{scale:1.08, duration:0.2, yoyo:true, repeat:3, ease:"sine.inOut"}}, {SECS[5]["start"] + 0.1:.3f});')

# section openers: letter dive -- a paper card with a giant numeral cut out of it (footage shows through the glyph),
# then the camera dives through the numeral. Starts on the section's first word ("এক নম্বর" / "দুই নম্বর").
for sec, num in ((2, "০১"), (3, "০২")):
    t = SECS[sec]["start"]
    html.append(f'<div class="dive" id="dv{sec}" data-layout-ignore><span>{num}</span></div>')
    js.append(f'tl.fromTo("#dv{sec}", {{autoAlpha:1, scale:1}}, {{scale:1.08, duration:0.32, ease:"none", immediateRender:false}}, {t:.3f});')
    js.append(f'tl.to("#dv{sec}", {{scale:7, autoAlpha:0, duration:0.34, ease:"power3.in"}}, {t + 0.32:.3f});')
    js.append(f'tl.to("#glitch", {{opacity:0.8, x:-24, duration:0.04, ease:"none"}}, {t + 0.62:.3f});')
    js.append(f'tl.to("#glitch", {{opacity:0, x:0, duration:0.12, ease:"steps(3)"}}, {t + 0.68:.3f});')
    cue("whoosh_fast", t + 0.3, 0.5)
    cue("glitch_digital", t + 0.6, 0.25)

# ------------------------------------------------------------------ section 2 : late reply (predict keys + bot reply)
s3 = SECS[3]["start"]
typed = "Price koto?"
chars = "".join(f'<span class="ch" id="ch{i}">{c if c != " " else "&nbsp;"}</span>' for i, c in enumerate(typed))
html.append(f'''<div class="card" id="chat">
 <div class="chead"><i class="av"></i><span>আপনার পেজ</span><span class="dot"></span></div>
 <div class="bubble cust" id="cbub">Price koto? <small>১০:০২ PM</small></div>
 <div class="seen" id="seen">Seen · <b>১ ঘণ্টা</b> পরও উত্তর নেই</div>
 <div class="left" id="leftp">👋 কাস্টমার পাশের পেজে চলে গেছে</div>
 <div class="bubble bot" id="bot">৳১,২০০ — আজই অর্ডার করবেন? ✅ <small>রাত ২:০০ · ২ সেকেন্ডে</small></div>
 <div class="keys" id="keys"><span class="pk on">Price koto?</span><span class="pk">Delivery?</span><span class="pk">Available?</span></div>
 <div class="input" id="inp">{chars}<i class="caret"></i></div>
</div>''')
t_type = SECS[2]["start"] + 0.75
show("#chat", SECS[2]["start"] + 0.62, s3 - 0.02, fin=0.3)
for i in range(len(typed)):
    js.append(f'tl.fromTo("#ch{i}", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.01}}, {t_type + i * 0.075:.3f});')
cue("typing_keys", t_type, 0.35)
t_send = w(2, "দাম")
js.append(f'tl.set("#inp, #keys", {{display:"none"}}, {t_send:.3f}); tl.set("#cbub", {{display:"block"}}, {t_send:.3f});')
js.append(f'tl.fromTo("#cbub", {{autoAlpha:0, y:20}}, {{autoAlpha:1, y:0, duration:0.25, ease:"back.out(2)"}}, {t_send:.3f});')
cue("pop_notification", t_send, 0.35)
t_wait = w(2, "অপেক্ষা")
js.append(f'tl.set("#seen", {{display:"block"}}, {t_wait:.3f});')
js.append(f'tl.fromTo("#seen", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.25}}, {t_wait:.3f});')
t_left = w(2, "পাশের")
js.append(f'tl.set("#leftp", {{display:"block"}}, {t_left:.3f});')
js.append(f'tl.fromTo("#leftp", {{autoAlpha:0, x:-30}}, {{autoAlpha:1, x:0, duration:0.25, ease:"power3.out"}}, {t_left:.3f});')
t_bot = w(2, "এআই")
js.append(f'tl.set("#seen, #leftp", {{display:"none"}}, {t_bot:.3f}); tl.set("#bot", {{display:"block"}}, {t_bot:.3f});')
js.append(f'tl.fromTo("#bot", {{autoAlpha:0, scale:0.6, transformOrigin:"100% 100%"}}, {{autoAlpha:1, scale:1, duration:0.3, ease:"back.out(2.4)"}}, {t_bot:.3f});')
cue("chime_success", t_bot, 0.45)
hs = [("🌙 রাত ২টাতেও", w(2, "রাত")), ("⚡ সেকেন্ডে উত্তর", w(2, "সেকেন্ডে")), ("✅ অর্ডার কনফার্ম", w(2, "উত্তর"))]
html.append('<div class="hstack" id="hs2">' + "".join(f'<span class="hchip" id="hc2{i}">{t}</span>' for i, (t, _) in enumerate(hs)) + '</div>')
for i, (_, t) in enumerate(hs):
    js.append(f'tl.fromTo("#hc2{i}", {{autoAlpha:0, y:-90, rotation:{(-4, 3, -2)[i]}}}, {{autoAlpha:1, y:0, duration:0.3, ease:"bounce.out"}}, {t:.3f});')
    cue("click_ui", t, 0.3)
js.append(f'tl.to("#hs2", {{autoAlpha:0, y:-40, duration:0.15}}, {s3 - 0.17:.3f});')

# ------------------------------------------------------------------ section 3 : no follow-up (post wall + voice note)
s4 = SECS[4]["start"]
tiles = "".join(f'<div class="tile" id="tw{i}"><i class="av s{i % 5}"></i><span class="ln"></span><span class="tag">কেনেনি</span></div>' for i in range(10))
html.append(f'<div class="card" id="wall"><div class="wh">আজ কেনেনি: <b id="wcount">০</b> জন</div><div class="grid">{tiles}</div></div>')
t_wall = SECS[3]["start"] + 0.62
show("#wall", t_wall, w(3, "অটোমেশন") + 0.05, fin=0.25)
for i in range(10):
    js.append(f'tl.fromTo("#tw{i}", {{autoAlpha:0, scale:0.5}}, {{autoAlpha:1, scale:1, duration:0.2, ease:"back.out(2)"}}, {t_wall + 0.25 + i * 0.07:.3f});')
cue("pop_notification", t_wall + 0.25, 0.35)
for k, val in enumerate([3, 9, 16, 24, 31, 38, 44, 47]):
    js.append(f'tl.set("#wcount", {{textContent:"{str(val).translate(BN)}"}}, {t_wall + 0.3 + k * 0.12:.3f});')
t_auto = w(3, "অটোমেশন")
bars = "".join(f'<i class="bar" id="b{i}" style="height:{14 + int(30 * abs(math.sin(i * 1.7)))}px"></i>' for i in range(26))
html.append(f'''<div class="card" id="vnote"><div class="vrow"><span class="play">▶</span><div class="wave">{bars}</div><span class="vt">০:০৬</span></div>
<div class="vfoot"><span class="vl">🔔 অটো রিমাইন্ডার: “আপনার অর্ডারটা কি কনফার্ম করবেন?”</span><span class="del" id="del">Delivered ✓✓</span></div></div>''')
show("#vnote", t_auto, s4 - 0.02, fin=0.3, frm="{autoAlpha:0, y:60, scale:0.9}", to="{autoAlpha:1, y:0, scale:1}")
for i in range(26):
    js.append(f'tl.fromTo("#b{i}", {{scaleY:0.35}}, {{scaleY:1, duration:0.18, ease:"sine.inOut", yoyo:true, repeat:{8 + i % 3}}}, {t_auto + 0.25 + (i % 7) * 0.03:.3f});')
js.append(f'tl.fromTo("#del", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.2}}, {w(3, "রিমাইন্ডার"):.3f});')
cue("pop_notification", t_auto, 0.4)
cue("chime_success", w(3, "রিমাইন্ডার"), 0.3)
html.append('<div class="hstack" id="hs3"><span class="hchip red" id="hc30">😶 কেউ মনে করায়নি</span><span class="hchip green" id="hc31">🤖 অটো ফলো-আপ চালু</span></div>')
t_noone = w(3, "কেউ")
js.append(f'tl.fromTo("#hc30", {{autoAlpha:0, y:-90}}, {{autoAlpha:1, y:0, duration:0.3, ease:"bounce.out"}}, {t_noone:.3f});')
js.append(f'tl.set("#hc30", {{display:"none"}}, {t_auto:.3f});')
js.append(f'tl.fromTo("#hc31", {{autoAlpha:0, scale:0.4}}, {{autoAlpha:1, scale:1, duration:0.3, ease:"back.out(2.5)"}}, {t_auto:.3f});')
js.append(f'tl.to("#hs3", {{autoAlpha:0, duration:0.12}}, {s4 - 0.14:.3f});')
cue("click_ui", t_noone, 0.3)

# ------------------------------------------------------------------ section 4 : only Facebook (press front + tear + landing b-roll)
s5 = SECS[4]["end"]
t_np, t_tear = SECS[4]["start"], w(4, "নিজের")
# the front page is rendered once to media/np.png (np/ sub-project, see make_np()) so the two torn halves are images
NP_HTML = f'''<div class="np">
 <div class="mast">দৈনিক ব্যবসা</div><div class="dline">ঢাকা · আজকের সংস্করণ · মূল্য: একটি কাস্টমার</div>
 <div class="hl">শুধু ফেসবুক পেজ?<br>কাস্টমার ভাবে “সিরিয়াস না”</div>
 <div class="photo"><img src="media/np_photo.jpg" alt="" /><i class="dots"></i></div>
 <div class="cols"><p>নিজের ওয়েবসাইট ছাড়া ব্যবসা আস্থা হারায়। কেনার আগে কাস্টমার যাচাই করে।</p><p>ল্যান্ডিং পেজ = বিশ্বাস + অর্ডার। Future Stack ৭ দিনে বানিয়ে দেয়।</p></div>
</div>'''
html.append('<div id="npwrap"><div class="npL" id="npL"><img src="media/np.png" alt="" /></div><div class="npR" id="npR"><img src="media/np.png" alt="" /></div></div>')
js.append(f'tl.fromTo("#npwrap", {{autoAlpha:0, scale:1.08}}, {{autoAlpha:1, scale:1, duration:0.22, ease:"power3.out"}}, {t_np:.3f});')
cue("paper_rustle", t_np, 0.5)
js.append(f'tl.to("#npL", {{xPercent:-75, rotation:-9, duration:0.55, ease:"power3.in"}}, {t_tear:.3f});')
js.append(f'tl.to("#npR", {{xPercent:75, rotation:9, duration:0.55, ease:"power3.in"}}, {t_tear:.3f});')
js.append(f'tl.set("#npwrap", {{autoAlpha:0}}, {t_tear + 0.56:.3f});')
cue("paper_tear", t_tear, 0.6)
t_land = w(4, "ল্যান্ডিং")
html.append('<div id="phone"><div class="pscr"><img src="media/screens/phone/01-home-hero.png" alt="" /></div><span class="pl">আপনার নিজের ল্যান্ডিং পেজ ✓</span></div>')
show("#phone", t_land, s5 - 0.02, fin=0.35, frm="{autoAlpha:0, y:220, rotation:-8}", to="{autoAlpha:1, y:0, rotation:-4}")
js.append(f'tl.to("#phone .pscr img", {{yPercent:-38, duration:{s5 - t_land - 0.6:.2f}, ease:"power1.inOut"}}, {t_land + 0.5:.3f});')
cue("whoosh_fast", t_land, 0.4)

# ------------------------------------------------------------------ section 5 : CTA (comment drop)
c5 = SECS[5]["start"]
grow = "".join(f'<span class="gc" id="g{i}">{c}</span>' for i, c in enumerate("GROW"))
html.append(f'''<div id="cbox1" class="cbox"><i class="av"></i><div class="cin">{grow}<i class="caret"></i></div><span class="post">Post</span></div>
<div id="cbox2" class="cbox2">🎁 ফ্রি পেজ অডিট<br><small>কোথায় কাস্টমার হারাচ্ছেন, আমরা দেখিয়ে দেবো</small></div>''')
show("#cbox1", c5, SECS[5]["end"] - 0.02, fin=0.3, frm="{autoAlpha:0, y:-160}", to="{autoAlpha:1, y:0}")
for i in range(4):
    js.append(f'tl.fromTo("#g{i}", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.01}}, {w(5, "GROW") + i * 0.08:.3f});')
cue("pop_notification", c5, 0.45)
cue("typing_keys", w(5, "GROW"), 0.25)
t_team = w(5, "আমার")
show("#cbox2", t_team, SECS[5]["end"] - 0.02, fin=0.3, frm="{autoAlpha:0, y:-120}", to="{autoAlpha:1, y:0}")
cue("pop_notification", t_team, 0.4)

# ------------------------------------------------------------------ section 6 : impact "GROW" then blow away
c6 = SECS[6]["start"]
t_imp_end = w(6, "যথেষ্ট")
html.append(f'<div id="impact">{live_video("impv", c6, t_imp_end, "imp")}<svg id="lines" viewBox="0 0 1080 1920">'
            + "".join(f'<line x1="540" y1="760" x2="{540 + 1400 * math.cos(a / 40 * 2 * math.pi):.0f}" y2="{760 + 1400 * math.sin(a / 40 * 2 * math.pi):.0f}"/>' for a in range(40))
            + '</svg><div class="igrow">GROW</div></div>')
js.append(f'tl.fromTo("#impact", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.04}}, {c6:.3f});')
for k in range(4):
    js.append(f'tl.set("#impact", {{filter:"invert({1 if k % 2 == 0 else 0})"}}, {c6 + 0.12 + k * 0.1:.3f});')
js.append(f'tl.fromTo("#impact .igrow", {{scale:1.4}}, {{scale:1, duration:0.25, ease:"power4.out"}}, {c6:.3f});')
js.append(f'tl.set("#impact", {{autoAlpha:0}}, {t_imp_end:.3f});')
cue("impact_hit", c6, 0.6)
# blow away: the last shot dissolves left-to-right into drifting dust
dust = "".join(f'<i class="dust" id="d{i}" style="left:{(i * 37) % 900 + 90}px;top:{(i * 53) % 900 + 420}px"></i>' for i in range(60))
html.append(f'<div id="dustwrap">{dust}</div>')
js.append(f'tl.to(".cam", {{"--dis":"130%", duration:1.0, ease:"power1.in"}}, {BLOW - 0.05:.3f});')
for i in range(60):
    js.append(f'tl.fromTo("#d{i}", {{autoAlpha:0, x:0, y:0}}, {{autoAlpha:0.9, x:{160 + (i * 29) % 260}, y:{-60 - (i * 17) % 160}, duration:0.9, ease:"power1.out"}}, {BLOW + (i % 12) * 0.05:.3f});')
js.append(f'tl.to("#dustwrap", {{autoAlpha:0, duration:0.3}}, {CARD - 0.25:.3f});')
cue("wind_dust", BLOW - 0.05, 0.55)
for sec in (2, 3):
    js.append(f'tl.set("#panel", {{zIndex:48}}, {SECS[sec]["start"]:.3f}); tl.set("#panel", {{zIndex:30}}, {SECS[sec]["start"] + 0.66:.3f});')
# the panel steps aside for the full-screen moments (newspaper, impact) and leaves before the blow-away
js.append(f'tl.to("#panel", {{autoAlpha:0, duration:0.1}}, {t_np:.3f}); tl.to("#panel", {{autoAlpha:1, duration:0.2}}, {t_tear + 0.5:.3f});')
js.append(f'tl.to("#panel", {{autoAlpha:0, duration:0.05}}, {c6:.3f}); tl.to("#panel", {{autoAlpha:1, duration:0.15}}, {t_imp_end:.3f});')
js.append(f'tl.to("#panel", {{autoAlpha:0, duration:0.3}}, {BLOW:.3f});')

# ------------------------------------------------------------------ end card
html.append(f'''<div id="card">
 <img id="elogo" src="media/logo/logo-dark.png" alt="Future Stack Solutions" />
 <div id="e1">কাজ করুক এআই, বাড়ুক আপনার ব্যবসা।</div>
 <div id="e2">স্মার্ট ব্যবসার পেছনে, ফিউচার স্ট্যাক</div>
 <div id="e3">যোগাযোগ করুন</div>
 <div id="e4"><svg viewBox="0 0 24 24" width="46" height="46"><path fill="#0B0D11" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm5.3 14.1c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .2-3.3-.7-2.8-1.1-4.6-4-4.7-4.2-.1-.2-1.1-1.5-1.1-2.9s.7-2 1-2.3c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.4 0 .5l-.3.5-.4.4c-.1.1-.3.3-.1.6.2.3.7 1.2 1.6 1.9 1.1 1 2 1.3 2.3 1.4.3.1.5.1.6-.1l.9-1c.2-.3.4-.2.6-.1l1.9.9c.3.1.5.2.5.3.1.2.1.8-.1 1.4z"/></svg><span>+880 1632-932249</span></div>
</div>''')
js.append(f'tl.fromTo("#card", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.3}}, {CARD:.3f});')
js.append(f'tl.fromTo("#elogo", {{autoAlpha:0, scale:0.85}}, {{autoAlpha:1, scale:1, duration:0.5, ease:"back.out(1.6)"}}, {CARD + 0.15:.3f});')
for k, sel in enumerate(("#e1", "#e2", "#e3", "#e4")):
    js.append(f'tl.fromTo("{sel}", {{autoAlpha:0, y:30}}, {{autoAlpha:1, y:0, duration:0.4, ease:"power3.out"}}, {CARD + 0.6 + k * 0.35:.3f});')
js.append(f'tl.to("#e4", {{scale:1.06, duration:0.35, yoyo:true, repeat:3, ease:"sine.inOut"}}, {CARD + 2.4:.3f});')
cue("chime_success", CARD + 0.15, 0.4)
cue("pop_notification", CARD + 1.65, 0.3)

# ------------------------------------------------------------------ subtitles (per word, black boxes)
def chunks(ws):
    out, cur = [], []
    for i, x in enumerate(ws):
        cur.append(x)
        glued = x["text"].rstrip("।,?:!").translate(str.maketrans("", "", "০১২৩৪৫৬৭৮৯")) == "" or x["text"] in ("রাত",)
        brk = x["text"][-1] in "।,?:!" and not glued
        if (brk or len(cur) >= 6) and not glued:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


caps = []
cid = 0
for sec in (1, 2, 3, 4, 6):                 # section 5 hidden: the comment-drop boxes carry it (brief)
    ws = [x for x in WORDS if x["section"] == sec]
    cs = chunks(ws)
    end_sec = SECS[sec]["end"]
    for j, ch in enumerate(cs):
        t0 = ch[0]["start"] - 0.05
        if sec == 6:
            t0 = max(t0, t_imp_end)
        t1 = cs[j + 1][0]["start"] - 0.05 if j + 1 < len(cs) else min(end_sec + 0.1, BLOW)
        spans = " ".join(f'<span class="w{" en" if x["text"].startswith("GROW") else ""}" id="s{cid}w{k}">{x["text"]}</span>'
                         for k, x in enumerate(ch))
        caps.append(f'<div class="sub" id="s{cid}"><span class="box">{spans}</span></div>')
        js.append(f'tl.fromTo("#s{cid}", {{autoAlpha:0, scale:0.9}}, {{autoAlpha:1, scale:1, duration:0.12, ease:"back.out(2)"}}, {t0:.3f});')
        js.append(f'tl.to("#s{cid}", {{autoAlpha:0, duration:0.06}}, {t1 - 0.06:.3f});')
        for k, x in enumerate(ch):
            js.append(f'tl.fromTo("#s{cid}w{k}", {{color:"{TEXT}"}}, {{color:"{BLUE_HI}", duration:0.06, immediateRender:false}}, {x["start"]:.3f});')
            if k + 1 < len(ch):
                js.append(f'tl.to("#s{cid}w{k}", {{color:"{TEXT}", duration:0.04}}, {max(ch[k + 1]["start"], x["start"] + 0.07):.3f});')
        cid += 1

css = f"""
@font-face {{ font-family:"Hind Siliguri"; src:url(media/fonts/hind-siliguri-bengali-600-normal.woff2) format("woff2"); font-weight:600; font-display:block; unicode-range:U+0980-09FE,U+200C-200D,U+25CC; }}
@font-face {{ font-family:"Hind Siliguri"; src:url(media/fonts/hind-siliguri-bengali-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; unicode-range:U+0980-09FE,U+200C-200D,U+25CC; }}
@font-face {{ font-family:"Hind Siliguri"; src:url(media/fonts/hind-siliguri-latin-600-normal.woff2) format("woff2"); font-weight:600; font-display:block; unicode-range:U+0000-00FF,U+2000-206F; }}
@font-face {{ font-family:"Hind Siliguri"; src:url(media/fonts/hind-siliguri-latin-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; unicode-range:U+0000-00FF,U+2000-206F; }}
@font-face {{ font-family:"Sora"; src:url(media/fonts/sora.woff2) format("woff2"); font-weight:600 800; font-display:block; }}
@font-face {{ font-family:"Noto Color Emoji"; src:url(media/fonts/NotoColorEmoji.ttf) format("truetype"); font-display:block; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:{BG}; }}
#root {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; color:{TEXT};
  font-family:"Hind Siliguri", "Noto Color Emoji", sans-serif; }}
.cam {{ position:absolute; inset:0; --dis:-30%;
  -webkit-mask-image:linear-gradient(90deg, transparent 0%, transparent var(--dis), #000 calc(var(--dis) + 25%));
  mask-image:linear-gradient(90deg, transparent 0%, transparent var(--dis), #000 calc(var(--dis) + 25%)); }}
.cam video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; filter:brightness(.82) saturate(.86) contrast(1.06); }}
#grade {{ position:absolute; inset:0; pointer-events:none; z-index:2;
  background:radial-gradient(900px 1250px at 50% 38%, rgba(11,13,17,0) 45%, rgba(11,13,17,.72) 100%); }}
#glitch {{ position:absolute; inset:0; z-index:60; opacity:0; pointer-events:none; mix-blend-mode:screen;
  background:repeating-linear-gradient(0deg, rgba(86,131,255,.55) 0 6px, rgba(0,0,0,0) 6px 22px), linear-gradient(90deg, rgba(255,40,80,.35), rgba(60,196,255,.35)); }}
.titlepills {{ position:absolute; top:150px; left:0; width:100%; display:flex; flex-direction:column; align-items:center; gap:14px; z-index:30; visibility:hidden; }}
.tp {{ background:#fff; color:{BG}; font-weight:700; font-size:54px; padding:10px 34px 4px; border-radius:22px; box-shadow:0 10px 30px -10px rgba(0,0,0,.6); }}
.tp.en {{ font-family:"Sora"; font-weight:700; font-size:34px; padding:10px 28px; background:{BLUE}; color:{BG}; }}
#cursor {{ position:absolute; left:0; top:0; z-index:40; visibility:hidden; display:flex; align-items:flex-start; gap:6px; }}
.ctag {{ margin-top:46px; background:{BLUE}; color:{BG}; font-family:"Sora"; font-weight:700; font-size:28px; padding:6px 14px; border-radius:8px; }}
#selbox {{ position:absolute; left:330px; top:400px; width:420px; height:520px; border:3px solid {BLUE_HI}; z-index:35; visibility:hidden; }}
#selbox .h {{ position:absolute; width:18px; height:18px; background:#fff; border:3px solid {BLUE}; }}
.h.tl {{ left:-11px; top:-11px; }} .h.tr {{ right:-11px; top:-11px; }} .h.bl {{ left:-11px; bottom:-11px; }} .h.br {{ right:-11px; bottom:-11px; }}
.dim {{ position:absolute; left:50%; top:-58px; translate:-50% 0; background:{BLUE}; color:{BG}; font-family:"Sora"; font-weight:700; font-size:28px; padding:6px 14px; border-radius:8px; white-space:nowrap; }}
.ptile {{ position:absolute; top:1040px; width:290px; height:270px; border-radius:28px; background:#fff; color:{BG}; z-index:30; visibility:hidden;
  display:flex; flex-direction:column; align-items:center; justify-content:center; box-shadow:0 22px 50px -14px rgba(0,0,0,.8); border-bottom:8px solid {BLUE}; }}
.ptile b {{ font-size:130px; font-weight:700; line-height:1; color:{BLUE}; margin-top:10px; }}
.ptile .plab {{ font-size:32px; font-weight:700; margin-top:4px; }}
.ptile .pico {{ position:absolute; left:18px; top:14px; font-size:40px; }}
.dive {{ position:absolute; inset:0; z-index:47; visibility:hidden; background:#F2EDE1; mix-blend-mode:screen; display:flex; flex-direction:column;
  align-items:center; justify-content:center; transform-origin:46% 46%; }}
.dive span {{ font-size:820px; font-weight:700; line-height:.9; color:#000; letter-spacing:-.04em; }}
.dive i {{ font-style:normal; font-size:76px; font-weight:700; color:#1B1712; margin-top:20px; }}
.hstack {{ position:absolute; left:70px; top:90px; width:640px; z-index:33; display:flex; flex-direction:column; align-items:flex-start; gap:12px; }}
.hchip {{ visibility:hidden; background:#fff; color:{BG}; font-weight:700; font-size:40px; padding:10px 26px 4px; border-radius:18px; box-shadow:0 14px 30px -10px rgba(0,0,0,.7); }}
.hchip.red {{ background:{RED}; color:#fff; }} .hchip.green {{ background:{GREEN}; color:{BG}; }}
#panel {{ position:absolute; left:744px; top:330px; width:310px; z-index:30; visibility:hidden; background:rgba(18,21,26,.9); border:1px solid {BORDER};
  border-radius:16px; padding:18px 16px 16px; box-shadow:0 20px 50px -18px rgba(0,0,0,.7); }}
#panel .ph {{ font-size:26px; font-weight:600; color:{MUTED}; display:flex; justify-content:space-between; margin-bottom:10px; letter-spacing:.02em; }}
#panel ul {{ list-style:none; display:flex; flex-direction:column; gap:8px; }}
#panel li {{ font-size:27px; font-weight:600; padding:8px 12px 4px; border-radius:10px; color:{MUTED}; display:flex; gap:10px; align-items:baseline; }}
#panel li .num {{ font-size:26px; color:{MUTED}; }}
#panel li.on {{ background:{BLUE}; color:{BG}; }} #panel li.on .num {{ color:{BG}; }}
#pbtn {{ margin-top:14px; text-align:center; font-size:26px; font-weight:700; padding:10px 0 6px; border-radius:999px; background:{BLUE}; color:{BG}; }}
#pbtn.gold {{ background:{AMBER}; color:{BG}; box-shadow:0 0 24px rgba(240,162,59,.55); }}
.en {{ font-family:"Sora"; font-weight:800; letter-spacing:.02em; }}
.card {{ position:absolute; left:64px; bottom:520px; width:640px; z-index:30; visibility:hidden; background:rgba(18,21,26,.94); border:1px solid {BORDER};
  border-radius:20px; padding:22px; box-shadow:0 24px 60px -20px rgba(0,0,0,.75); }}
.chead {{ display:flex; align-items:center; gap:12px; font-size:28px; font-weight:600; color:{MUTED}; margin-bottom:10px; }}
.av {{ display:inline-block; width:44px; height:44px; border-radius:50%; background:linear-gradient(135deg,#3BB4F2,#5683FF); }}
.chead .dot {{ width:12px; height:12px; border-radius:50%; background:{GREEN}; margin-left:auto; }}
.bubble {{ font-family:"Sora","Hind Siliguri",sans-serif; font-size:30px; padding:10px 20px; border-radius:20px; max-width:90%; margin-bottom:8px; visibility:hidden; display:none; }}
.bubble small {{ display:block; font-size:22px; opacity:.7; margin-top:4px; font-family:"Hind Siliguri"; }}
.bubble.cust {{ background:{SURF2}; }}
.bubble.bot {{ background:{BLUE}; color:{BG}; margin-left:auto; font-family:"Hind Siliguri"; font-weight:700; font-size:30px; }}
.seen {{ font-size:30px; color:{AMBER}; margin:0 0 10px 6px; visibility:hidden; display:none; }}
.left {{ font-size:30px; color:{RED}; font-weight:600; margin:0 0 10px 6px; visibility:hidden; display:none; }}
.keys {{ display:flex; gap:10px; margin:6px 0 10px; }}
.pk {{ font-family:"Sora"; font-size:26px; padding:8px 14px; border-radius:10px; background:{SURF2}; color:{MUTED}; }}
.pk.on {{ background:{BLUE}; color:{BG}; }}
.input {{ font-family:"Sora"; font-size:30px; background:{BG}; border:1px solid {BORDER}; border-radius:999px; padding:10px 22px; min-height:60px; display:flex; align-items:center; }}
.ch {{ visibility:hidden; }}
.caret {{ display:inline-block; width:3px; height:36px; background:{BLUE_HI}; margin-left:4px; }}
.wh {{ font-size:32px; font-weight:700; margin-bottom:14px; }} .wh b {{ color:{RED}; }}
.grid {{ display:grid; grid-template-columns:repeat(5,1fr); gap:10px; }}
.tile {{ background:{SURF2}; border-radius:14px; padding:10px 8px; align-items:center !important; display:flex; flex-direction:column; gap:8px; align-items:flex-start; visibility:hidden; }}
.tile .ln {{ width:80%; height:10px; border-radius:6px; background:{BORDER}; }}
.tile .tag {{ font-size:26px; font-weight:600; color:{RED}; background:rgba(242,107,94,.14); padding:2px 10px 0; border-radius:8px; }}
.av.s1 {{ background:linear-gradient(135deg,#F0A23B,#F26B5E); }} .av.s2 {{ background:linear-gradient(135deg,#3CC48F,#3BB4F2); }}
.av.s3 {{ background:linear-gradient(135deg,#8AA9FF,#5683FF); }} .av.s4 {{ background:linear-gradient(135deg,#A9B0BC,#434A57); }}
#vnote {{ bottom:520px; }}
.vrow {{ display:flex; align-items:center; gap:16px; }}
.play {{ width:64px; height:64px; border-radius:50%; background:{BLUE}; color:{BG}; display:flex; align-items:center; justify-content:center; font-size:30px; }}
.wave {{ display:flex; align-items:center; gap:5px; height:60px; flex:1; }}
.bar {{ width:8px; border-radius:4px; background:{BLUE_HI}; display:block; }}
.vt {{ font-family:"Sora"; font-size:28px; color:{MUTED}; }}
.vfoot {{ margin-top:14px; display:flex; flex-direction:column; gap:8px; font-size:30px; }}
.del {{ font-family:"Sora"; font-size:28px; color:{GREEN}; visibility:hidden; }}
#npwrap {{ position:absolute; inset:0; z-index:45; visibility:hidden; }}
.npL, .npR {{ position:absolute; inset:0; }}
.npL img, .npR img {{ position:absolute; inset:0; width:100%; height:100%; }}
.npL {{ clip-path:polygon(0 0, 52% 0, 47% 9%, 54% 18%, 46% 28%, 53% 38%, 47% 49%, 55% 60%, 46% 71%, 53% 82%, 47% 91%, 52% 100%, 0 100%); }}
.npR {{ clip-path:polygon(52% 0, 100% 0, 100% 100%, 52% 100%, 47% 91%, 53% 82%, 46% 71%, 55% 60%, 47% 49%, 53% 38%, 46% 28%, 54% 18%, 47% 9%); }}
.np {{ position:absolute; inset:0; background:#F2EDE1; color:#1B1712; padding:80px 64px; font-family:"Hind Siliguri"; }}
.mast {{ font-size:120px; font-weight:700; text-align:center; border-bottom:6px double #1B1712; line-height:1.25; }}
.dline {{ font-size:28px; text-align:center; border-bottom:2px solid #1B1712; padding:8px 0 4px; margin-bottom:26px; }}
.hl {{ font-size:72px; font-weight:700; line-height:1.18; text-align:center; margin-bottom:24px; }}
.photo {{ position:relative; height:760px; overflow:hidden; border:3px solid #1B1712; }}
.photo video {{ position:absolute; width:100%; height:100%; object-fit:cover; object-position:50% 30%; filter:grayscale(1) contrast(1.9) brightness(1.05); }}
.photo .dots {{ position:absolute; inset:0; background:radial-gradient(circle, rgba(27,23,18,.35) 1.4px, transparent 1.6px) 0 0/7px 7px; mix-blend-mode:multiply; }}
.cols {{ display:grid; grid-template-columns:1fr 1fr; gap:28px; margin-top:24px; font-size:27px; line-height:1.45; }}
#phone {{ position:absolute; left:34px; top:770px; width:260px; z-index:31; visibility:hidden; }}
.pscr {{ width:260px; height:480px; border-radius:42px; border:12px solid #0E1117; overflow:hidden; background:#fff; box-shadow:0 30px 70px -20px rgba(0,0,0,.8); }}
.pscr img {{ width:100%; display:block; }}
.pl {{ display:block; margin-top:14px; text-align:center; font-weight:700; font-size:28px; color:{GREEN}; }}
.cbox {{ position:absolute; left:80px; top:980px; width:760px; z-index:32; visibility:hidden; display:flex; align-items:center; gap:16px; background:#fff;
  color:{BG}; border-radius:22px; padding:18px 22px; box-shadow:0 24px 60px -18px rgba(0,0,0,.8); }}
.cin {{ flex:1; font-family:"Sora"; font-weight:800; font-size:44px; display:flex; align-items:center; border:2px solid #CDD2DA; border-radius:999px; padding:8px 22px; min-height:76px; }}
.gc {{ visibility:hidden; }}
.post {{ font-family:"Sora"; font-weight:700; font-size:28px; color:#fff; background:{BLUE}; border-radius:999px; padding:12px 22px; }}
.cbox2 {{ position:absolute; left:80px; top:1150px; width:760px; z-index:32; visibility:hidden; background:{AMBER}; color:{BG}; border-radius:22px;
  padding:20px 28px 14px; font-size:44px; font-weight:700; line-height:1.25; box-shadow:0 24px 60px -18px rgba(0,0,0,.8); }}
.cbox2 small {{ display:block; font-size:28px; font-weight:600; }}
#impact {{ position:absolute; inset:0; z-index:46; visibility:hidden; background:#000; }}
#impact video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; filter:grayscale(1) contrast(3.2) brightness(1.25); }}
#lines {{ position:absolute; inset:0; width:100%; height:100%; mix-blend-mode:difference; }}
#lines line {{ stroke:#fff; stroke-width:6; opacity:.55; }}
.igrow {{ position:absolute; left:0; width:100%; top:1330px; text-align:center; font-family:"Sora"; font-weight:800; font-size:250px; color:#fff;
  -webkit-text-stroke:10px #000; paint-order:stroke fill; letter-spacing:-.02em; }}
#dustwrap {{ position:absolute; inset:0; z-index:20; pointer-events:none; }}
.dust {{ position:absolute; width:8px; height:8px; border-radius:2px; background:#E8D8C0; visibility:hidden; }}
#card {{ position:absolute; inset:0; z-index:70; visibility:hidden; background:{BG}; display:flex; flex-direction:column; align-items:center; padding-top:300px; text-align:center; }}
#elogo {{ width:700px; }}
#e1 {{ margin-top:50px; font-size:58px; font-weight:700; line-height:1.3; padding:0 70px; }}
#e2 {{ margin-top:18px; font-size:38px; font-weight:600; color:{MUTED}; }}
#e3 {{ margin-top:70px; font-size:32px; font-weight:600; color:{MUTED}; letter-spacing:.04em; }}
#e4 {{ margin-top:16px; display:flex; align-items:center; gap:16px; background:{WA}; color:{BG}; border-radius:999px; padding:18px 44px; font-family:"Sora"; font-weight:800; font-size:48px; }}
.sub {{ position:absolute; left:60px; width:{W - 120 - 130}px; top:{int(0.765 * H)}px; translate:0 -50%; z-index:50; text-align:center; visibility:hidden; }}
.sub .box {{ display:inline; background:rgba(0,0,0,.86); color:{TEXT}; font-weight:600; font-size:54px; line-height:1.62; padding:6px 20px 0;
  border-radius:14px; -webkit-box-decoration-break:clone; box-decoration-break:clone; }}
.sub .w.en {{ font-family:"Sora"; font-weight:800; }}
"""

body = f"""<!doctype html>
<html lang="bn"><head><meta charset="UTF-8" /><meta name="viewport" content="width={W}, height={H}" />
<title>Future Stack promo</title><style>{css}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="{W}" data-height="{H}">
{chr(10).join(html[:len(SEGS)])}
<div id="grade"></div>
{chr(10).join(html[len(SEGS):])}
{chr(10).join(caps)}
<div id="glitch"></div>
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
# np/ sub-project: the newspaper page, snapshotted to media/np.png by `hyperframes snapshot np --at 0.5`
np_dir = ROOT / "np"
np_dir.mkdir(exist_ok=True)
(np_dir / "index.html").write_text(f"""<!doctype html><html lang="bn"><head><meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" /><title>np</title><style>{css}
.np {{ visibility:visible; }} .photo img {{ position:absolute; width:100%; height:100%; object-fit:cover; object-position:50% 30%;
  filter:grayscale(1) contrast(1.9) brightness(1.05); }}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="1" data-width="{W}" data-height="{H}">{NP_HTML}</div>
<script src="media/gsap.min.js"></script><script>window.__timelines = window.__timelines || {{}}; window.__timelines["main"] = gsap.timeline({{ paused: true }});</script>
</body></html>""", encoding="utf-8")
s_np = seg_at(t_np)
print("newspaper photo frame:", s_np["clip"], round(s_np["src_in"] + 0.6, 3))
(ROOT / "np_frame.json").write_text(json.dumps({"clip": s_np["clip"], "t": round(s_np["src_in"] + 0.6, 3)}))
(ROOT / "sfx.json").write_text(json.dumps(sorted(sfx, key=lambda x: x["t"]), indent=1))
print(f"built index.html {TOTAL:.2f}s, {len(SEGS)} cuts, {cid} subtitle chunks, {len(sfx)} sfx cues")
