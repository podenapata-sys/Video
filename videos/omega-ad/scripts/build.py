#!/usr/bin/env python3
"""Omega Dental ad (Future Stack Solutions) from kit/: four HyperFrames projects.

  python3 scripts/build.py [--render]

  out-30s/     1080x1920, 30 s, scenes 1-9 (kit/storyboard.md)
  out-15s/     1080x1920, 15 s cut: scenes 1, 3, 5, 7, 9
  out-square/  1080x1080, 30 s, phone right / text left, no clock in scene 2
  out-wide/    1920x1080, 30 s, phone on the right third, dashboard wide

Every scene is a function scene_N(t0, k, L): t0 = its start, k scales its motion (the 15 s cut is shorter),
L = the format layout. Visuals are designed once at the 9:16 size and placed per format by a static
wrapper (position + scale); only inner elements are tweened, all with fromTo at absolute times on one paused
timeline. Copy is verbatim from kit/copy.md and kit/storyboard.md. No music (none supplied): soft synthesised
pops / whoosh / tick from the storyboard's sound notes.
"""
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / "assets" / "icons"
CLI = ["node", "/root/.claude/plugins/cache/hyperframes/hyperframes/0.8.152/skills/hyperframes/scripts/plugin-cli.mjs"]
SR = 48000
BN = "০১২৩৪৫৬৭৮৯"


def icon(name, cls=""):
    """Inline an icon so CSS colour applies (stroke=currentColor)."""
    svg = (ICONS / f"{name}.svg").read_text()
    svg = re.sub(r'\s(width|height)="\d+"', "", svg, count=2)
    return svg.replace("<svg", f'<svg class="ic {cls}"', 1)


# ----------------------------------------------------------------------------------------------- layouts
# text: (x, y, w); f: font sizes; vis[name] = (x, y, scale) for each 9:16-designed visual
V = dict(name="V", W=1080, H=1920, text=(80, 250, 860), f=dict(hook=86, feat=68, small=42, cta=88, num=72, foot=40, tile=58),
         vis=dict(map=(80, 760, 1.0), bubbles=(80, 600, 1.0), phone=(240, 620, 1.0), cards=(80, 640, 1.0),
                  tiles=(110, 300, 1.0)), clock=(80, 250, 1.0), caption_y=1330, clockless=False)
SQ = dict(name="S", W=1080, H=1080, text=(65, 110, 460), f=dict(hook=54, feat=48, small=36, cta=58, num=52, foot=36, tile=50),
          vis=dict(map=(560, 380, 0.53), bubbles=(560, 170, 0.53), phone=(585, 66, 0.73), cards=(170, 300, 0.8),
                   tiles=(130, 100, 0.94)), clock=None, caption_y=560, clockless=True)
WI = dict(name="W", W=1920, H=1080, text=(115, 190, 1000), f=dict(hook=72, feat=64, small=40, cta=76, num=64, foot=38, tile=58),
          vis=dict(map=(1150, 330, 0.72), bubbles=(1180, 150, 0.72), phone=(1311, 66, 0.73), cards=(820, 200, 1.04),
                   tiles=(530, 90, 1.0)), clock=(115, 470, 0.8), caption_y=700, clockless=False)


def place(L, key, inner, extra=""):
    x, y, s = L["vis"][key]
    return f'<div class="vis" style="left:{x}px;top:{y}px;transform:scale({s});{extra}">{inner}</div>'


def textbox(L, inner, y=None, w=None, extra=""):
    x, ty, tw = L["text"]
    if L["name"] == "S" and w is None:
        w = tw
    return (f'<div class="tbox" style="left:{x}px;top:{ty if y is None else y}px;width:{w or tw}px;{extra}">'
            f"{inner}</div>")


# ----------------------------------------------------------------------------------------------- scenes
def scene1(sid, t0, k, dur, L, js, sfx):
    f = L["f"]
    at = lambda x: t0 + x * k
    stars = "".join('<svg viewBox="0 0 24 24"><path d="m12 2.8 2.8 5.8 6.4.9-4.6 4.5 1.1 6.3L12 17.3l-5.7 3 1.1-6.3L2.8 9.5l6.4-.9z"/></svg>'
                    for _ in range(5))
    card = (f'<div class="mapcard" id="{sid}card"><div class="row"><div class="pin">{icon("map-pin")}</div>'
            f'<div><h3 class="bn">আপনার ক্লিনিক</h3><div class="stars">{stars}</div></div></div>'
            f'<div class="btns"><div class="btn en">Directions</div><div class="btn en">Call</div>'
            f'<div class="btn empty en" id="{sid}slot">Website</div></div></div>')
    html = (f'<div class="bgfill" style="background:radial-gradient(1200px 900px at 50% 38%,#ffffff 0%,#EAF3F6 60%,#DDEBF0 100%)"></div>'
            + textbox(L, f'<p id="{sid}a" class="hook bn" style="font-size:{f["hook"]}px">রোগী গুগলে আপনার ক্লিনিক খুঁজে পেলেন…</p>')
            + textbox(L, f'<p id="{sid}b" class="hook bn" style="font-size:{f["hook"]}px">…কিন্তু <span class="orange en">Website</span> নেই।</p>')
            + place(L, "map", card))
    js += [f'tl.fromTo("#{sid}card", {{ y: 80, opacity: 0 }}, {{ y: 0, opacity: 1, duration: {0.5 * k:.3f}, ease: "power3.out" }}, {at(0.0):.3f});',
           f'tl.fromTo("#{sid}a", {{ x: -60, opacity: 0 }}, {{ x: 0, opacity: 1, duration: {0.3 * k:.3f}, ease: "power2.out" }}, {at(0.0):.3f});',
           # each line >= 1.5 s on screen: A 0.0-1.7, B from 1.45 to the cut
           f'tl.to("#{sid}a", {{ x: -120, opacity: 0, duration: {0.25 * k:.3f}, ease: "power2.in" }}, {at(1.45):.3f});',
           f'tl.fromTo("#{sid}b", {{ x: 80, opacity: 0 }}, {{ x: 0, opacity: 1, duration: {0.35 * k:.3f}, ease: "power2.out" }}, {at(1.45):.3f});',
           f'tl.fromTo("#{sid}slot", {{ borderColor: "#C8D6DC", color: "#9AB0B9", scale: 1 }}, {{ borderColor: "#F08A24", color: "#F08A24", '
           f'scale: 1.06, duration: {0.25 * k:.3f}, yoyo: true, repeat: 3, ease: "sine.inOut" }}, {at(1.7):.3f});']
    return html


def scene2(sid, t0, k, dur, L, js, sfx):
    f = L["f"]
    at = lambda x: t0 + x * k
    qs = ["দাম কত?", "কখন খোলা?", "অ্যাপয়েন্টমেন্ট নেওয়া যাবে?"]
    bub = "".join(f'<div class="bub {"r" if i == 1 else ""}" id="{sid}q{i}">{icon("chat")}<span class="bn">{q}</span></div>'
                  for i, q in enumerate(qs))
    html = '<div class="bgfill" style="background:linear-gradient(180deg,#F4F8FA 0%,#E6EFF3 100%)"></div>'
    if not L["clockless"]:
        cx, cy, cs = L["clock"]
        html += (f'<div class="vis" style="left:{cx}px;top:{cy}px;transform:scale({cs})"><div class="clockrow" id="{sid}clk">'
                 f'<div class="clock"><svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="44"/>'
                 f'<line id="{sid}hh" x1="50" y1="50" x2="50" y2="26"/><line id="{sid}mh" x1="50" y1="50" x2="50" y2="14"/></svg></div>'
                 f'<span class="bn clocktxt">রাত ১১:০০</span></div></div>')
        js += [f'tl.fromTo("#{sid}clk", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: {0.4 * k:.3f}, ease: "power3.out" }}, {at(0.05):.3f});',
               f'tl.fromTo("#{sid}mh", {{ rotation: 0, svgOrigin: "50 50" }}, {{ rotation: 90, svgOrigin: "50 50", duration: {3.6 * k:.3f}, ease: "steps(6)" }}, {at(0.3):.3f});']
    html += place(L, "bubbles", f'<div class="bubbles" id="{sid}bubs">{bub}</div>')
    html += textbox(L, f'<p id="{sid}cap" class="feat bn" style="font-size:{f["feat"]}px">একই প্রশ্ন, দিনে বারবার।</p>', y=L["caption_y"])
    for i in range(3):
        t = at(0.3 + 0.35 * i)
        js.append(f'tl.fromTo("#{sid}q{i}", {{ scale: 0.6, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: {0.35 * k:.3f}, ease: "back.out(2)" }}, {t:.3f});')
        sfx.append((t, "pop"))
    js += [f'tl.fromTo("#{sid}cap", {{ y: 40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: {0.4 * k:.3f}, ease: "power3.out" }}, {at(2.2):.3f});',
           f'tl.fromTo("#{sid}bubs", {{ x: -8 }}, {{ x: 8, duration: 0.05, yoyo: true, repeat: 5, ease: "none", immediateRender: false }}, {at(2.25):.3f});',
           f'tl.to("#{sid}bubs", {{ x: 0, duration: 0.05, ease: "none" }}, {at(2.25) + 0.3:.3f});']
    return html


def phone(sid, imgs):
    layers = "".join(f'<img id="{sid}img{i}" src="assets/screens/phone/{im}.png" alt="" />' for i, im in enumerate(imgs))
    return f'<div class="phone" id="{sid}ph"><div class="screen">{layers}</div></div>'


def title_block(sid, L, title, small=None, words=False, ic=None):
    f = L["f"]
    if words:
        t = " ".join(f'<span class="w" id="{sid}w{i}">{w}</span>' for i, w in enumerate(title.split()))
    else:
        t = title
    head = f'<p id="{sid}t" class="feat bn" style="font-size:{f["feat"]}px">{t}</p>'
    if ic:
        head = (f'<div class="trow"><span class="ticon" id="{sid}ic">{icon(ic)}</span>'
                f'<p id="{sid}t" class="feat bn" style="font-size:{f["feat"]}px">{t}</p></div>')
    sm = f'<p id="{sid}s" class="small bn" style="font-size:{f["small"]}px">{small}</p>' if small else ""
    return textbox(L, head + sm)


def scene3(sid, t0, k, dur, L, js, sfx):
    at = lambda x: t0 + x * k
    words = "নিজের ওয়েবসাইট — আপনার ক্লিনিকের নামে".split()
    html = ('<div class="bgfill" style="background:radial-gradient(900px 900px at 50% 70%,#DDF3EE 0%,#F4F8FA 70%)"></div>'
            + title_block(sid, L, " ".join(words), small='উদাহরণ: <span class="en">omegadentalbd.com</span>', words=True)
            + place(L, "phone", f'<div class="glow" id="{sid}glow"></div>' + phone(sid, ["01-home-hero"])))
    js += [f'tl.fromTo("#{sid}ph", {{ y: 700, rotation: 4 }}, {{ y: 0, rotation: 0, duration: {0.8 * k:.3f}, ease: "power3.out" }}, {at(0.0):.3f});',
           f'tl.fromTo("#{sid}glow", {{ opacity: 0, scale: 0.7 }}, {{ opacity: 1, scale: 1, duration: {0.9 * k:.3f}, ease: "power2.out" }}, {at(0.2):.3f});']
    for i in range(len(words)):
        js.append(f'tl.fromTo("#{sid}w{i}", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: {0.22 * k:.3f}, ease: "power2.out" }}, {at(0.25 + 0.14 * i):.3f});')
    js.append(f'tl.fromTo("#{sid}s", {{ opacity: 0 }}, {{ opacity: 1, duration: {0.4 * k:.3f}, ease: "none" }}, {at(1.3):.3f});')
    sfx.append((at(0.0), "whoosh"))
    return html


def scene4(sid, t0, k, dur, L, js, sfx):
    at = lambda x: t0 + x * k
    html = ('<div class="bgfill" style="background:linear-gradient(180deg,#F4F8FA 0%,#E3F1EE 100%)"></div>'
            + title_block(sid, L, "দামের তালিকা — উত্তর আগেই", ic="price-tag")
            + place(L, "phone", phone(sid, ["03-price-list"])))
    js += [f'tl.fromTo("#{sid}t", {{ y: 40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: {0.45 * k:.3f}, ease: "power3.out" }}, {at(0.05):.3f});',
           f'tl.fromTo("#{sid}ic", {{ scale: 0, rotation: -20 }}, {{ scale: 1, rotation: 0, duration: {0.4 * k:.3f}, ease: "back.out(2.2)" }}, {at(0.35):.3f});',
           f'tl.fromTo("#{sid}img0", {{ y: 0 }}, {{ y: -300, duration: {2.6 * k:.3f}, ease: "sine.inOut" }}, {at(0.3):.3f});']
    return html


def scene5(sid, t0, k, dur, L, js, sfx):
    at = lambda x: t0 + x * k
    ring = f'<div class="tapring" id="{sid}ring"></div>'
    check = f'<div class="stamp" id="{sid}chk">{icon("check-circle")}</div>'
    html = ('<div class="bgfill" style="background:linear-gradient(180deg,#F4F8FA 0%,#E6EFF3 100%)"></div>'
            + title_block(sid, L, "অনলাইন বুকিং — রাতেও", small="সাথে সাথে ইমেইল আর গুগল শিটে")
            + place(L, "phone", phone(sid, ["05-booking-form"]).replace('</div></div>', f'{ring}</div>{check}</div>', 1)))
    js += [f'tl.fromTo("#{sid}t", {{ y: 40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: {0.45 * k:.3f}, ease: "power3.out" }}, {at(0.05):.3f});',
           f'tl.fromTo("#{sid}s", {{ opacity: 0 }}, {{ opacity: 1, duration: {0.4 * k:.3f}, ease: "none" }}, {at(0.5):.3f});',
           f'tl.fromTo("#{sid}ph", {{ y: 60, opacity: 0 }}, {{ y: 0, opacity: 1, duration: {0.5 * k:.3f}, ease: "power3.out" }}, {at(0.0):.3f});',
           f'tl.fromTo("#{sid}ring", {{ scale: 0.4, opacity: 0.9 }}, {{ scale: 1.6, opacity: 0, duration: {0.6 * k:.3f}, ease: "power2.out", repeat: 1 }}, {at(0.9):.3f});',
           f'tl.fromTo("#{sid}chk", {{ scale: 2.2, opacity: 0, rotation: -15 }}, {{ scale: 1, opacity: 1, rotation: 0, duration: {0.3 * k:.3f}, ease: "back.out(1.8)" }}, {at(2.2):.3f});']
    sfx.append((at(2.2), "tick"))
    return html


def scene6(sid, t0, k, dur, L, js, sfx):
    at = lambda x: t0 + x * k
    toggle = (f'<div class="toggle" id="{sid}tg"><span class="en">EN</span><span class="bn">বাংলা</span>'
              f'<i id="{sid}knob"></i></div>')
    html = ('<div class="bgfill" style="background:linear-gradient(180deg,#F4F8FA 0%,#E3F1EE 100%)"></div>'
            + title_block(sid, L, '<span class="bn">বাংলা</span> + <span class="en">English</span>', ic="language")
            + textbox(L, toggle, y=L["text"][1] + int(L["f"]["feat"] * 1.6))
            + place(L, "phone", phone(sid, ["01-home-hero", "09-home-hero-bangla"])))
    js += [f'tl.fromTo("#{sid}t", {{ y: 40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: {0.45 * k:.3f}, ease: "power3.out" }}, {at(0.05):.3f});',
           f'tl.fromTo("#{sid}ic", {{ scale: 0 }}, {{ scale: 1, duration: {0.4 * k:.3f}, ease: "back.out(2.2)" }}, {at(0.3):.3f});',
           f'tl.fromTo("#{sid}tg", {{ opacity: 0 }}, {{ opacity: 1, duration: {0.3 * k:.3f}, ease: "none" }}, {at(0.3):.3f});',
           f'tl.fromTo("#{sid}knob", {{ x: 0 }}, {{ x: 150, duration: {0.5 * k:.3f}, ease: "power2.inOut" }}, {at(0.9):.3f});',
           f'tl.fromTo("#{sid}img1", {{ opacity: 0 }}, {{ opacity: 1, duration: {0.5 * k:.3f}, ease: "none" }}, {at(0.9):.3f});']
    return html


def scene7(sid, t0, k, dur, L, js, sfx):
    at = lambda x: t0 + x * k
    f = L["f"]
    cards = (f'<div class="cards"><div class="card dash" id="{sid}dash"><div class="cardbar"><i></i><i></i><i></i></div>'
             f'<div class="shot"><img id="{sid}dimg" src="assets/screens/admin/02-dashboard-records.png" alt="" /></div>'
             f'<span class="sample bn">নমুনা ডেটা</span></div>'
             f'<div class="card edit" id="{sid}edit"><div class="cardbar"><i></i><i></i><i></i></div>'
             f'<div class="shot"><img src="assets/screens/admin/01-editor-prices.png" alt="" /></div></div></div>')
    html = ('<div class="bgfill" style="background:linear-gradient(180deg,#F4F8FA 0%,#E6EFF3 100%)"></div>'
            + textbox(L, f'<p id="{sid}t1" class="feat bn" style="font-size:{f["feat"]}px">রোগীর রেকর্ড ও পেমেন্ট — এক জায়গায়</p>')
            + textbox(L, f'<p id="{sid}t2" class="feat bn" style="font-size:{f["feat"]}px">দাম ও ছবি নিজেই বদলান</p>')
            + place(L, "cards", cards))
    sw = at(1.75)  # the editor card slides in (21.25 s in the 30 s cut); each line then gets >= 1.5 s
    js += [f'tl.fromTo("#{sid}dash", {{ y: 60, opacity: 0 }}, {{ y: 0, opacity: 1, duration: {0.5 * k:.3f}, ease: "power3.out" }}, {at(0.0):.3f});',
           f'tl.fromTo("#{sid}dimg", {{ scale: 1.0 }}, {{ scale: 1.08, duration: {3.5 * k:.3f}, ease: "none" }}, {at(0.0):.3f});',
           f'tl.fromTo("#{sid}t1", {{ y: 40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: {0.35 * k:.3f}, ease: "power3.out" }}, {at(0.0):.3f});',
           f'tl.to("#{sid}t1", {{ y: -30, opacity: 0, duration: {0.2 * k:.3f}, ease: "power2.in" }}, {sw:.3f});',
           f'tl.fromTo("#{sid}t2", {{ y: 40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: {0.45 * k:.3f}, ease: "power3.out" }}, {sw:.3f});',
           f'tl.fromTo("#{sid}edit", {{ xPercent: 120 }}, {{ xPercent: 0, duration: {0.6 * k:.3f}, ease: "power3.out" }}, {sw:.3f});']
    return html


def scene8(sid, t0, k, dur, L, js, sfx):
    at = lambda x: t0 + x * k
    f = L["f"]
    tiles = [("shield-check", f'মাসে <span id="{sid}roll">০</span> টাকা হোস্টিং'), ("globe-domain", "ডোমেইন আপনার নামে"),
             ("bolt", "ফোনে দ্রুত, ধীর নেটেও")]
    inner = "".join(f'<div class="tile" id="{sid}tile{i}"><span class="tic">{icon(ic)}</span>'
                    f'<p class="bn" style="font-size:{f["tile"] if L["name"] != "S" else 58}px">{tx}</p></div>' for i, (ic, tx) in enumerate(tiles))
    html = ('<div class="bgfill" style="background:radial-gradient(1000px 900px at 50% 40%,#FFFFFF 0%,#E6EFF3 100%)"></div>'
            + place(L, "tiles", f'<div class="tiles">{inner}</div>'))
    for i in range(3):
        js.append(f'tl.fromTo("#{sid}tile{i}", {{ y: -120, opacity: 0 }}, {{ y: 0, opacity: 1, duration: {0.45 * k:.3f}, ease: "back.out(1.6)" }}, {at(0.2 + 0.25 * i):.3f});')
    js += [f'const roll_{sid} = document.getElementById("{sid}roll"); const rv_{sid} = {{ v: 1000 }};',
           f'tl.fromTo(rv_{sid}, {{ v: 1000 }}, {{ v: 0, duration: {0.9 * k:.3f}, ease: "power2.in", onUpdate: () => {{ '
           f'roll_{sid}.textContent = String(Math.round(rv_{sid}.v)).replace(/[0-9]/g, (d) => "{BN}"[d]); }} }}, {at(0.55):.3f});']
    return html


def scene9(sid, t0, k, dur, L, js, sfx):
    at = lambda x: t0 + x * k
    f = L["f"]
    x, y, w = L["text"]
    top = {"V": 420, "S": 140, "W": 210}[L["name"]]
    foot_top = {"V": 1360, "S": 820, "W": 820}[L["name"]]
    html = (f'<div class="bgfill" id="{sid}bg" style="background:linear-gradient(160deg,#13294E 0%,#1E4C86 55%,#2B6CB0 100%)"></div>'
            f'<div class="cta" style="left:{x}px;top:{top}px;width:{w if L["name"] != "S" else 900}px">'
            f'<h2 id="{sid}h" class="bn" style="font-size:{f["cta"]}px">আপনার ক্লিনিকের নাম দিয়ে <b>ফ্রি নমুনা পেজ</b></h2>'
            f'<div class="wa" id="{sid}wa"><div class="dot">{icon("chat")}</div>'
            f'<div class="t"><small class="en">WhatsApp</small><strong class="en" style="font-size:{f["num"]}px">01632-932249</strong></div></div></div>'
            f'<p class="foot bn" id="{sid}foot" style="left:{x}px;top:{foot_top}px;width:{w if L["name"] != "S" else 900}px;font-size:{f["foot"]}px">'
            f'<span class="brand en">Future Stack Solutions</span>চালু থাকা উদাহরণ: <span class="en">omegadentalbd.com</span></p>')
    js += [f'tl.fromTo("#{sid}bg", {{ opacity: 0 }}, {{ opacity: 1, duration: {0.3 * k:.3f}, ease: "none" }}, {at(0.0):.3f});',
           f'tl.fromTo("#{sid}h", {{ y: 50, opacity: 0, scale: 0.94 }}, {{ y: 0, opacity: 1, scale: 1, duration: {0.55 * k:.3f}, ease: "power3.out" }}, {at(0.15):.3f});',
           f'tl.fromTo("#{sid}wa", {{ scale: 0.85, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: {0.5 * k:.3f}, ease: "back.out(1.6)" }}, {at(0.6):.3f});',
           f'tl.fromTo("#{sid}foot", {{ opacity: 0 }}, {{ opacity: 1, duration: {0.5 * k:.3f}, ease: "none" }}, {at(1.0):.3f});']
    for p in (1.5, 3.0):  # WhatsApp pulses (27.5 s and 29 s in the 30 s cut)
        js.append(f'tl.fromTo("#{sid}wa", {{ scale: 1 }}, {{ scale: 1.05, duration: {0.25 * k:.3f}, yoyo: true, repeat: 1, ease: "sine.inOut", immediateRender: false }}, {at(p):.3f});')
    return html


SCENES = {1: (scene1, 3.0), 2: (scene2, 4.0), 3: (scene3, 3.5), 4: (scene4, 3.0), 5: (scene5, 3.5), 6: (scene6, 2.5),
          7: (scene7, 3.5), 8: (scene8, 3.0), 9: (scene9, 4.0)}
CUTS = {
    "30s": (V, [(n, None) for n in range(1, 10)]),
    "15s": (V, [(1, 2.5), (3, 3.0), (5, 3.5), (7, 3.0), (9, 3.0)]),
    "square": (SQ, [(n, None) for n in range(1, 10)]),
    "wide": (WI, [(n, None) for n in range(1, 10)]),
}


# ----------------------------------------------------------------------------------------------- sound
def _noise(n, seed):
    return np.random.default_rng(seed).standard_normal(n).astype(np.float32)


def _lowpass(x, a):
    a = np.broadcast_to(np.asarray(a, np.float32), x.shape)
    y, acc = np.empty_like(x), 0.0
    for i, v in enumerate(x):
        acc += a[i] * (v - acc)
        y[i] = acc
    return y


def _whoosh():
    n = int(0.55 * SR)
    u = np.linspace(0, 1, n)
    return _lowpass(_noise(n, 3), 0.02 + 0.12 * np.sin(np.pi * u)) * np.sin(np.pi * u) ** 1.5


def _pop():
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    f = 520 + 380 * np.exp(-t * 60)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 45) * np.minimum(1, t * 900)).astype(np.float32)


def _tick():
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1900 * t) * np.exp(-t * 140)).astype(np.float32)


SOUNDS = {"whoosh": (_whoosh, -14), "pop": (_pop, -16), "tick": (_tick, -18)}


def write_sfx(path, total, events):
    bus = np.zeros(int(total * SR), np.float32)
    for t, kind in events:
        fn, peak = SOUNDS[kind]
        x = fn()
        x = x / np.max(np.abs(x)) * 10 ** (peak / 20)
        i = int(t * SR)
        bus[i:i + len(x)] += x[: len(bus) - i]
    sf.write(path, np.repeat(bus[:, None], 2, axis=1), SR, subtype="PCM_16")


# ----------------------------------------------------------------------------------------------- page
CSS = """
@font-face{font-family:"Noto Sans Bengali";src:url(fonts/noto-bengali.woff2) format("woff2");font-weight:400 800;font-display:block}
@font-face{font-family:"Sora";src:url(fonts/sora.woff2) format("woff2");font-weight:600 800;font-display:block}
@font-face{font-family:"Inter";src:url(fonts/inter.woff2) format("woff2");font-weight:400 700;font-display:block}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: {{W}}px; height: {{H}}px; overflow: hidden; background: #F4F8FA; }
#root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #F4F8FA; color: #16323C;
  font-family: "Noto Sans Bengali", "Sora", sans-serif; }
.scene { overflow: hidden; }
.bn { font-family: "Noto Sans Bengali", "Sora", sans-serif; }
.en { font-family: "Sora", "Noto Sans Bengali", sans-serif; }
.orange { color: #F08A24; }
.bgfill { position: absolute; inset: 0; }
.vis { position: absolute; transform-origin: 0 0; }
.tbox { position: absolute; }
.ic { width: 100%; height: 100%; display: block; }
.hook { font-weight: 700; line-height: 1.25; color: #13294E; }
.feat { font-weight: 700; line-height: 1.3; color: #13294E; }
.small { font-weight: 500; line-height: 1.4; color: #2C8A78; margin-top: 18px; }
.w { display: inline-block; }
.trow { display: flex; align-items: center; gap: 24px; }
.ticon { flex: none; width: 1.3em; height: 1.3em; color: #2C8A78; display: block; font-size: 64px; padding: 12px; background: #DDF3EE;
  border-radius: 24px; }
/* scene 1: a generic map listing card, drawn from scratch (not a copy of any app's UI) */
.mapcard { width: 860px; background: #fff; border-radius: 44px; padding: 52px 56px; box-shadow: 0 40px 90px -40px rgba(19,41,78,.45); }
.mapcard .row { display: flex; align-items: center; gap: 26px; }
.pin { width: 92px; height: 92px; border-radius: 28px; background: #FDECEA; color: #D64532; display: grid; place-items: center; }
.pin .ic { width: 56px; height: 56px; }
.mapcard h3 { font-size: 58px; font-weight: 700; color: #13294E; line-height: 1.2; }
.stars { display: flex; gap: 6px; margin-top: 10px; }
.stars svg { width: 38px; height: 38px; fill: #F6B12C; }
.btns { display: flex; gap: 22px; margin-top: 44px; }
.btn { flex: 1; height: 112px; border-radius: 30px; display: grid; place-items: center; font-weight: 700; font-size: 38px;
  background: #EEF5F8; color: #13294E; }
.btn.empty { background: transparent; border: 5px dashed #C8D6DC; color: #9AB0B9; }
/* scene 2 */
.clockrow { display: flex; align-items: center; gap: 28px; }
.clock { width: 150px; height: 150px; color: #13294E; }
.clock svg { width: 100%; height: 100%; fill: #fff; stroke: #13294E; stroke-width: 5; stroke-linecap: round; }
.clocktxt { font-size: 64px; font-weight: 700; color: #13294E; }
.bubbles { width: 860px; display: flex; flex-direction: column; gap: 40px; }
.bub { align-self: flex-start; display: flex; align-items: center; gap: 22px; background: #fff; border-radius: 44px 44px 44px 12px;
  padding: 30px 40px; box-shadow: 0 24px 60px -30px rgba(19,41,78,.35); max-width: 860px; }
.bub.r { align-self: flex-end; border-radius: 44px 44px 12px 44px; background: #DDF3EE; }
.bub .ic { width: 60px; height: 60px; color: #2B6CB0; flex: none; }
.bub span { font-size: 60px; font-weight: 700; color: #13294E; line-height: 1.25; }
/* phone mockup (brand.md) */
.phone { width: 600px; aspect-ratio: 1170/2532; border-radius: 76px; padding: 22px; background: #0E1B33; position: relative;
  box-shadow: 0 60px 120px -40px rgba(19,41,78,.55), 0 0 0 3px #22345a inset; }
.phone .screen { width: 100%; height: 100%; border-radius: 56px; overflow: hidden; background: #fff; position: relative; }
.phone .screen img { width: 100%; display: block; position: absolute; left: 0; top: 0; }
.glow { position: absolute; left: -150px; top: 150px; width: 900px; height: 900px; border-radius: 50%;
  background: radial-gradient(circle, rgba(87,195,173,.55) 0%, rgba(87,195,173,0) 65%); }
.tapring { position: absolute; left: 278px; top: 570px; width: 200px; height: 200px; margin: -100px 0 0 -100px; border-radius: 50%;
  border: 8px solid #57C3AD; }
.stamp { position: absolute; right: -40px; bottom: 380px; width: 190px; height: 190px; border-radius: 50%; background: #fff;
  color: #1FA855; padding: 18px; box-shadow: 0 20px 50px -20px rgba(19,41,78,.5); }
.toggle { position: relative; display: inline-flex; gap: 0; background: #13294E; border-radius: 999px; padding: 10px; }
.toggle span { position: relative; z-index: 1; width: 150px; text-align: center; font-size: 40px; font-weight: 700; color: #fff; line-height: 80px; }
.toggle i { position: absolute; left: 10px; top: 10px; width: 150px; height: 80px; border-radius: 999px; background: #57C3AD; }
/* scene 7 */
.cards { position: relative; width: 860px; height: 760px; }
.card { position: absolute; width: 760px; background: #fff; border-radius: 28px; overflow: hidden;
  box-shadow: 0 40px 90px -40px rgba(19,41,78,.5); }
.card.dash { left: 0; top: 0; }
.card.edit { left: 100px; top: 280px; }
.cardbar { height: 40px; background: #E6EFF3; display: flex; gap: 10px; align-items: center; padding: 0 18px; }
.cardbar i { width: 14px; height: 14px; border-radius: 50%; background: #C8D6DC; }
.shot { overflow: hidden; }
.shot img { width: 100%; display: block; transform-origin: 30% 30%; }
.sample { position: absolute; right: 16px; top: 50px; background: #13294E; color: #fff; font-size: 36px; font-weight: 600;
  border-radius: 999px; padding: 4px 22px; }
/* scene 8 */
.tiles { width: 860px; display: flex; flex-direction: column; gap: 34px; }
.tile { display: flex; align-items: center; gap: 36px; background: #fff; border-radius: 40px; padding: 44px 48px;
  box-shadow: 0 30px 70px -36px rgba(19,41,78,.4); }
.tile .tic { flex: none; width: 130px; height: 130px; border-radius: 34px; background: linear-gradient(135deg, #57C3AD, #2B6CB0);
  color: #fff; padding: 30px; }
.tile p { font-weight: 700; color: #13294E; line-height: 1.3; }
/* scene 9 */
.cta { position: absolute; color: #fff; }
.cta h2 { font-weight: 800; line-height: 1.22; }
.cta h2 b { color: #57C3AD; font-weight: 800; }
.wa { margin-top: 70px; display: inline-flex; align-items: center; gap: 26px; background: #fff; color: #13294E; border-radius: 999px;
  padding: 26px 52px 26px 30px; }
.wa .dot { width: 84px; height: 84px; border-radius: 50%; background: #57C3AD; color: #fff; padding: 18px; }
.wa .t small { display: block; font: 600 36px "Inter", sans-serif; color: #5B7682; }
.wa .t strong { display: block; font-weight: 800; letter-spacing: .5px; line-height: 1.1; }
.foot { position: absolute; color: #CFE3EE; line-height: 1.5; }
.foot .brand { display: block; font-weight: 800; font-size: 1.25em; color: #fff; margin-bottom: 8px; }
"""

PAGE = """<!doctype html>
<html lang="bn">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={{W}}, height={{H}}" />
    <title>{{TITLE}}</title>
    <script src="assets/gsap.min.js"></script>
    <style>{{CSS}}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{{TOTAL}}" data-width="{{W}}" data-height="{{H}}" data-fps="30">
      {{SCENES}}
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


def build(cut):
    L, plan = CUTS[cut]
    js, sfx, secs = [], [], []
    t = 0.0
    for n, d in plan:
        fn, orig = SCENES[n]
        dur = d or orig
        k = dur / orig
        sid = f"s{n}"
        inner = fn(sid, t, k, dur, L, js, sfx)
        secs.append(f'<section id="{sid}" class="clip scene" data-start="{t:.3f}" data-duration="{dur:.3f}" data-track-index="1">{inner}</section>')
        t += dur
    total = round(t, 3)
    proj = ROOT / f"out-{cut}"
    wav = proj / "sfx.wav"
    write_sfx(wav, total, sfx)
    audio = f'<audio id="sfx" src="sfx.wav" data-start="0" data-duration="{total}" data-track-index="9" data-volume="1"></audio>'
    page = (PAGE.replace("{{CSS}}", CSS).replace("{{W}}", str(L["W"])).replace("{{H}}", str(L["H"]))
            .replace("{{TITLE}}", f"Omega Dental ad {cut}").replace("{{TOTAL}}", str(total))
            .replace("{{SCENES}}", "\n      ".join(secs)).replace("{{AUDIO}}", audio).replace("{{JS}}", "\n      ".join(js)))
    (proj / "index.html").write_text(page)
    return total


def main():
    cuts = [c for c in CUTS if c in sys.argv] or list(CUTS)
    for cut in cuts:
        print(cut, build(cut), "s")
    if "--render" in sys.argv:
        for cut in cuts:
            out = ROOT / "renders" / f"omega-ad-{cut}.mp4"
            r = subprocess.run(CLI + ["render", str(ROOT / f"out-{cut}"), "-o", str(out), "--fps", "30", "--quality", "delivery"],
                               capture_output=True, text=True)
            print(cut, "\n".join(l for l in (r.stdout + r.stderr).splitlines() if "MB" in l or "rror" in l))


if __name__ == "__main__":
    main()
