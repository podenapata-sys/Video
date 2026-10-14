#!/usr/bin/env python3
"""Build the 60s "Five Needs" archival explainer.

  python3 scripts/build.py

Voices every caption line separately with Kokoro (cached in vo/), stitches
voiceover.wav with exact line offsets, estimates per-word times inside each line,
and writes index.html (1080x1920, black & white archival style, kinetic captions).
"""
import hashlib
import html
import json
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "story-channel" / "scripts"))
from build_episode import tts, wav_duration  # noqa: E402

VOICE, SPEED = "bm_george", 1.4
LEAD_IN, GAP_LINE, GAP_SEC = 0.35, 0.08, 0.35
TOTAL = 60.0
SECTIONS = [
    {"num": "", "title": "", "fig": "FIG. 00 — THE EXERCISE"},
    {"num": "01", "title": "TIME", "fig": "FIG. 01 — TIME"},
    {"num": "02", "title": "CLARITY", "fig": "FIG. 02 — CLARITY"},
    {"num": "03", "title": "STATUS", "fig": "FIG. 03 — STATUS"},
    {"num": "04", "title": "CERTAINTY", "fig": "FIG. 04 — CERTAINTY"},
    {"num": "05", "title": "CONNECTION", "fig": "FIG. 05 — CONNECTION"},
    {"num": "", "title": "", "fig": "FIG. 06 — YOUR PRODUCT"},
]
NEEDS = ["TIME", "CLARITY", "STATUS", "CERTAINTY", "CONNECTION"]
KEY = {"five", "time.", "clarity.", "status.", "certainty.", "connection.", "pay", "sold", "important,",
       "premium", "stable.", "wins", "starving", "deliver?", "feature.", "real", "sell", "that."}


def build_audio(data):
    lines, t = [], LEAD_IN
    for si, sec in enumerate(data):
        for li, text in enumerate(sec["lines"]):
            key = hashlib.sha1(f"{VOICE}|{SPEED}|{text}".encode()).hexdigest()[:12]
            clip = ROOT / "vo" / f"{key}.wav"
            dur = wav_duration(clip) if clip.exists() else tts(text, VOICE, SPEED, clip)
            lines.append({"sec": si, "text": text, "clip": clip, "start": t, "end": t + dur})
            t += dur + (GAP_LINE if li + 1 < len(sec["lines"]) else GAP_SEC)
    with wave.open(str(lines[0]["clip"])) as w0:
        rate, width = w0.getframerate(), w0.getsampwidth()
    out = wave.open(str(ROOT / "voiceover.wav"), "wb")
    out.setnchannels(1), out.setsampwidth(width), out.setframerate(rate)
    written = 0
    for ln in lines:
        pad = int(round(ln["start"] * rate)) - written
        out.writeframes(b"\x00" * max(0, pad) * width)
        written += max(0, pad)
        with wave.open(str(ln["clip"])) as w:
            out.writeframes(w.readframes(w.getnframes()))
            written += w.getnframes()
    out.writeframes(b"\x00" * max(0, int(TOTAL * rate) - written) * width)
    out.close()
    return lines


def word_times(ln):
    words = ln["text"].split()
    a, b = ln["start"] + 0.06, ln["end"] - 0.1
    weights = [len(w.strip(",.:?'")) + 2 for w in words]
    tot, acc, out = sum(weights), 0, []
    for w, wt in zip(words, weights):
        out.append((w, a + (b - a) * acc / tot))
        acc += wt
    return out


def section_svg(si):
    ink = "#141414"
    if si == 1:  # clock
        ticks = "".join(
            f'<line x1="0" y1="-205" x2="0" y2="{-180 if i % 3 else -165}" stroke="{ink}" stroke-width="{6 if i % 3 == 0 else 3}" transform="rotate({i * 30})"/>'
            for i in range(12))
        return f'''<svg viewBox="-260 -260 520 520" class="ill"><circle r="225" fill="none" stroke="{ink}" stroke-width="8"/>
          <circle r="238" fill="none" stroke="{ink}" stroke-width="2"/>{ticks}
          <line class="hand-h" x1="0" y1="0" x2="0" y2="-110" stroke="{ink}" stroke-width="12" stroke-linecap="round"/>
          <line class="hand-m" x1="0" y1="0" x2="0" y2="-170" stroke="#a8322a" stroke-width="6" stroke-linecap="round"/>
          <circle r="12" fill="{ink}"/></svg>'''
    if si == 2:  # ten faint paths -> one bold arrow
        faint = "".join(
            f'<path class="faint" d="M60 300 Q {200 + i * 18} {60 + i * 52} {300 + (i % 4) * 60} {40 + i * 55}" fill="none" stroke="{ink}" stroke-width="3" stroke-dasharray="10 10" opacity="0.35"/>'
            for i in range(10))
        return f'''<svg viewBox="0 0 600 600" class="ill">{faint}
          <path class="bold" d="M60 300 L 500 300" fill="none" stroke="#a8322a" stroke-width="16" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>
          <path class="head" d="M470 255 L 540 300 L 470 345 Z" fill="#a8322a" opacity="0"/>
          <circle cx="60" cy="300" r="16" fill="{ink}"/></svg>'''
    if si == 3:  # figures, one rises
        figs = ""
        for i in range(7):
            x = 60 + i * 80
            cls = "fig hero" if i == 3 else "fig"
            figs += f'<g class="{cls}" transform="translate({x} 0)"><circle cx="0" cy="380" r="22" fill="{ink}"/><rect x="-26" y="408" width="52" height="90" rx="14" fill="{ink}"/></g>'
        return f'''<svg viewBox="0 0 600 600" class="ill"><line x1="10" y1="500" x2="590" y2="500" stroke="{ink}" stroke-width="4"/>
          <rect class="plinth" x="255" y="500" width="90" height="0" fill="{ink}"/>{figs}
          <path class="crown" d="M270 250 L 285 205 L 300 235 L 315 205 L 330 250 Z" fill="#a8322a" opacity="0"/></svg>'''
    if si == 4:  # seal stamp
        return f'''<svg viewBox="-300 -300 600 600" class="ill"><g class="seal" transform="rotate(-12)">
          <circle r="230" fill="none" stroke="#a8322a" stroke-width="14"/><circle r="198" fill="none" stroke="#a8322a" stroke-width="4"/>
          <text x="0" y="22" text-anchor="middle" font-family="League Gothic" font-size="118" fill="#a8322a" letter-spacing="6">GUARANTEED</text>
          <text x="0" y="-92" text-anchor="middle" font-family="JetBrains Mono" font-size="30" fill="#a8322a" letter-spacing="8">★ OUTCOME ★</text>
          <text x="0" y="118" text-anchor="middle" font-family="JetBrains Mono" font-size="30" fill="#a8322a" letter-spacing="8">BACKED UP</text></g></svg>'''
    if si == 5:  # network
        pts = [(300, 300), (130, 160), (470, 150), (90, 380), (510, 400), (230, 500), (390, 520), (300, 90), (300, 470)]
        edges = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 7), (2, 7), (3, 5), (4, 6), (5, 8), (6, 8), (1, 3), (2, 4)]
        lines = "".join(
            f'<line class="edge" x1="{pts[a][0]}" y1="{pts[a][1]}" x2="{pts[b][0]}" y2="{pts[b][1]}" stroke="{ink}" stroke-width="5" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>'
            for a, b in edges)
        nodes = "".join(f'<circle class="node" cx="{x}" cy="{y}" r="{30 if i == 0 else 22}" fill="{"#a8322a" if i == 0 else ink}"/>'
                        for i, (x, y) in enumerate(pts))
        return f'<svg viewBox="0 0 600 600" class="ill">{lines}{nodes}</svg>'
    return ""


def card(filled):
    rows = "".join(
        f'<div class="row"><span class="n">{i + 1}.</span><span class="v{" fill" if filled else ""}" id="{"cv" if filled else "hv"}{i}">{NEEDS[i] if filled else ""}</span></div>'
        for i in range(5))
    title = "WHAT PEOPLE NEED MOST" if filled else "WRITE DOWN FIVE THINGS"
    return f'<div class="card"><div class="ct">{title}</div>{rows}</div>'


def main():
    data = json.loads((ROOT / "scripts" / "lines.json").read_text())
    lines = build_audio(data)
    narr_end = lines[-1]["end"]
    sec_start = {}
    for ln in lines:
        sec_start.setdefault(ln["sec"], ln["start"] - (0.2 if ln["sec"] else LEAD_IN))
    sec_start[0] = 0.0
    sec_bounds = [(sec_start[i], sec_start[i + 1] if i + 1 < 7 else TOTAL) for i in range(7)]

    els, js = [], []
    # ---- sections ----
    for si, (s, e) in enumerate(sec_bounds):
        meta = SECTIONS[si]
        d = e - s
        if si in (0, 6):
            body = card(si == 6)
            if si == 6:
                body += '<div class="sellthat" id="sellthat" data-layout-allow-overlap data-layout-allow-occlusion>SELL THAT.</div>'
        else:
            body = f'''<div class="headline"><div class="num">{meta["num"]}</div><div class="ttl">{meta["title"]}</div></div>
            {section_svg(si)}'''
        els.append(f'''      <section id="s{si}" class="clip sec" data-start="{s:.3f}" data-duration="{d:.3f}" data-track-index="1">
        <div class="inner">{body}<div class="fig">{meta["fig"]}</div></div>
      </section>''')
        # entrance + flash
        js.append(f'tl.fromTo("#s{si} .inner", {{ opacity: 0, scale: 1.04 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "power2.out" }}, {s:.3f});')
        if si:
            js.append(f'tl.fromTo("#flash", {{ opacity: 0.85 }}, {{ opacity: 0, duration: 0.25, ease: "power2.out", immediateRender: false }}, {s:.3f});')
        if meta["num"]:
            js.append(f'tl.fromTo("#s{si} .num", {{ y: 120, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.45, ease: "expo.out" }}, {s + 0.05:.3f});')
            js.append(f'tl.fromTo("#s{si} .ttl", {{ x: 160, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.45, ease: "expo.out" }}, {s + 0.18:.3f});')
            js.append(f'tl.fromTo("#s{si} .ill", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }}, {s + 0.3:.3f});')
        js.append(f'tl.fromTo("#s{si} .fig", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, {s + 0.4:.3f});')
        if si == 0:
            js.append(f'tl.fromTo("#s0 .card", {{ y: -200, rotation: -8, opacity: 0 }}, {{ y: 0, rotation: -2, opacity: 1, duration: 0.6, ease: "back.out(1.6)" }}, 0.1);')
            js.append(f'tl.fromTo("#s0 .row", {{ opacity: 0, x: -40 }}, {{ opacity: 1, x: 0, duration: 0.3, stagger: 0.12, ease: "power2.out" }}, 0.6);')
        if si == 1:
            js.append(f'tl.fromTo("#s1 .hand-m", {{ rotation: 0, svgOrigin: "0 0" }}, {{ rotation: 1080, svgOrigin: "0 0", duration: {d:.3f}, ease: "none" }}, {s:.3f});')
            js.append(f'tl.fromTo("#s1 .hand-h", {{ rotation: 60, svgOrigin: "0 0" }}, {{ rotation: 150, svgOrigin: "0 0", duration: {d:.3f}, ease: "none" }}, {s:.3f});')
        if si == 2:
            js.append(f'tl.fromTo("#s2 .faint", {{ opacity: 0.35 }}, {{ opacity: 0.06, duration: 0.8, stagger: 0.05 }}, {s + d * 0.55:.3f});')
            js.append(f'tl.fromTo("#s2 .bold", {{ strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.9, ease: "power2.inOut" }}, {s + d * 0.6:.3f});')
            js.append(f'tl.fromTo("#s2 .head", {{ opacity: 0, x: -30 }}, {{ opacity: 1, x: 0, duration: 0.25 }}, {s + d * 0.6 + 0.85:.3f});')
        if si == 3:
            js.append(f'tl.fromTo("#s3 .hero", {{ y: 0 }}, {{ y: -150, duration: 1.2, ease: "power3.inOut" }}, {s + 0.9:.3f});')
            js.append(f'tl.fromTo("#s3 .plinth", {{ attr: {{ y: 500, height: 0 }} }}, {{ attr: {{ y: 350, height: 150 }}, duration: 1.2, ease: "power3.inOut" }}, {s + 0.9:.3f});')
            js.append(f'tl.fromTo("#s3 .crown", {{ opacity: 0, y: -40 }}, {{ opacity: 1, y: -150, duration: 0.5, ease: "back.out(2)" }}, {s + 2.1:.3f});')
        if si == 4:
            js.append(f'tl.fromTo("#s4 .seal", {{ scale: 2.4, opacity: 0, svgOrigin: "0 0" }}, {{ scale: 1, opacity: 1, svgOrigin: "0 0", duration: 0.28, ease: "power4.in" }}, {s + d * 0.3:.3f});')
            js.append(f'tl.fromTo("#s4 .inner", {{ x: 0 }}, {{ x: 10, duration: 0.05, yoyo: true, repeat: 5, ease: "none", immediateRender: false }}, {s + d * 0.3 + 0.28:.3f});')
        if si == 5:
            js.append(f'tl.fromTo("#s5 .node", {{ scale: 0, transformOrigin: "50% 50%" }}, {{ scale: 1, duration: 0.3, stagger: 0.12, ease: "back.out(2.5)" }}, {s + 0.4:.3f});')
            js.append(f'tl.fromTo("#s5 .edge", {{ strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.5, stagger: 0.22, ease: "power1.inOut" }}, {s + 1.4:.3f});')
        if si == 6:
            js.append(f'tl.fromTo("#s6 .card", {{ opacity: 0, y: 60, rotation: 3 }}, {{ opacity: 1, y: 0, rotation: -2, duration: 0.5, ease: "power3.out" }}, {s:.3f});')
            js.append(f'tl.fromTo("#s6 .row", {{ opacity: 0, x: -40 }}, {{ opacity: 1, x: 0, duration: 0.25, stagger: 0.25, ease: "power2.out" }}, {s + 0.4:.3f});')
            sell = next(l for l in lines if l["text"] == "Sell that.")["start"]
            js.append(f'tl.fromTo("#sellthat", {{ scale: 2.6, opacity: 0, rotation: -14 }}, {{ scale: 1, opacity: 1, rotation: -8, duration: 0.3, ease: "power4.in" }}, {sell:.3f});')

    # ---- kinetic captions ----
    for i, ln in enumerate(lines):
        nxt = lines[i + 1]["start"] if i + 1 < len(lines) else TOTAL
        s, e = ln["start"] - 0.05, min(nxt - 0.03, ln["end"] + 0.6) if i + 1 < len(lines) else TOTAL
        cid = f"c{i:02d}"
        wt = word_times(ln)
        spans = " ".join(
            f'<span class="w{" k" if w.lower() in KEY else ""}" id="{cid}w{j}">{html.escape(w)}</span>' for j, (w, _) in enumerate(wt))
        els.append(f'      <div id="{cid}" class="clip cap" data-start="{s:.3f}" data-duration="{e - s:.3f}" data-track-index="3"><div class="cl">{spans}</div></div>')
        js.append(f'tl.fromTo("#{cid} .cl", {{ y: 40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.18, ease: "power3.out" }}, {s:.3f});')
        for j, (w, t) in enumerate(wt):
            t_next = wt[j + 1][1] if j + 1 < len(wt) else ln["end"]
            js.append(f'tl.fromTo("#{cid}w{j}", {{ opacity: 0.22, color: "#141414", scale: 1 }}, {{ opacity: 1, color: "#a8322a", scale: 1.1, duration: 0.07 }}, {t:.3f});')
            js.append(f'tl.to("#{cid}w{j}", {{ color: "#141414", scale: 1, duration: 0.12 }}, {max(t + 0.08, t_next):.3f});')

    # ---- archival texture: flicker + gate weave (finite repeats) ----
    js.append(f'tl.fromTo("#flicker", {{ opacity: 0 }}, {{ opacity: 0.07, duration: 0.09, yoyo: true, repeat: {int(TOTAL / 0.09) - 1}, ease: "steps(1)" }}, 0);')
    js.append(f'tl.fromTo("#stage", {{ x: 0, y: 0 }}, {{ x: 1.5, y: -1.5, duration: 0.6, yoyo: true, repeat: {int(TOTAL / 0.6) - 1}, ease: "sine.inOut" }}, 0);')

    page = PAGE.replace("{{ELS}}", "\n".join(els)).replace("{{JS}}", "\n      ".join(js)).replace("{{TOTAL}}", f"{TOTAL}")
    (ROOT / "index.html").write_text(page)
    (ROOT / "timing.json").write_text(json.dumps(
        {"narration_end": round(narr_end, 3), "sections": sec_bounds,
         "lines": [{"text": l["text"], "start": round(l["start"], 3), "end": round(l["end"], 3)} for l in lines]}, indent=1))
    print(f"narration ends {narr_end:.2f}s, {len(lines)} lines, total {TOTAL}s")


PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>The Five Needs</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #e8e4d9; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #e8e4d9; color: #141414; font-family: "EB Garamond", serif; }
      #stage { position: absolute; inset: 0; }
      #paper { position: absolute; inset: 0;
        background-image: repeating-linear-gradient(0deg, rgba(20,20,20,0.045) 0 2px, transparent 2px 64px),
                          repeating-linear-gradient(90deg, rgba(20,20,20,0.045) 0 2px, transparent 2px 64px); }
      #header { position: absolute; left: 70px; right: 70px; top: 190px; display: flex; justify-content: space-between; align-items: baseline;
        border-top: 6px solid #141414; border-bottom: 2px solid #141414; padding: 14px 0 10px; font-family: "JetBrains Mono", monospace; font-size: 26px; font-weight: 700; letter-spacing: 0.14em; }
      .sec { position: absolute; left: 0; right: 0; top: 300px; height: 860px; }
      .inner { position: relative; width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 18px; }
      .headline { display: flex; align-items: flex-end; gap: 30px; width: 940px; border-bottom: 4px solid #141414; padding-bottom: 6px; }
      .num { font-family: "League Gothic", sans-serif; font-size: 300px; line-height: 0.8; color: #a8322a; }
      .ttl { font-family: "League Gothic", sans-serif; font-size: 170px; line-height: 0.85; letter-spacing: 0.02em; }
      .ill { width: 520px; height: 520px; display: block; }
      .fig { font-family: "JetBrains Mono", monospace; font-size: 24px; font-weight: 700; letter-spacing: 0.16em; color: #3a3a3a; }
      .card { width: 860px; background: #f6f3ea; border: 4px solid #141414; padding: 40px 56px 30px; box-shadow: 14px 14px 0 #141414; }
      .card .ct { font-family: "League Gothic", sans-serif; font-size: 92px; line-height: 1; border-bottom: 4px solid #141414; padding-bottom: 14px; margin-bottom: 10px; }
      .card .row { display: flex; align-items: baseline; gap: 22px; height: 104px; border-bottom: 2px dashed #6b6b6b; }
      .card .n { font-family: "League Gothic", sans-serif; font-size: 76px; color: #a8322a; width: 60px; }
      .card .v { font-family: "League Gothic", sans-serif; font-size: 80px; letter-spacing: 0.04em; }
      .sellthat { position: absolute; left: 50%; top: 50%; width: 760px; margin-left: -380px; margin-top: -110px; text-align: center;
        font-family: "League Gothic", sans-serif; font-size: 190px; line-height: 1.1; color: #a8322a; border: 12px solid #a8322a; background: rgba(246,243,234,0.92); }
      .cap { position: absolute; left: 70px; right: 70px; top: 1200px; height: 300px; display: flex; align-items: flex-start; justify-content: center; z-index: 30; }
      .cl { max-width: 940px; text-align: center; font-size: 74px; font-weight: 700; line-height: 1.15; }
      .w { display: inline-block; opacity: 0.22; margin: 0 0.13em; }
      .w.k { text-decoration: underline; text-decoration-thickness: 4px; text-underline-offset: 10px; }
      #flash { position: absolute; inset: 0; background: #ffffff; opacity: 0; pointer-events: none; z-index: 80; }
      #flicker { position: absolute; inset: 0; background: #000; opacity: 0; pointer-events: none; z-index: 81; }
      #vignette { position: absolute; inset: 0; pointer-events: none; z-index: 82;
        background: radial-gradient(ellipse at center, rgba(0,0,0,0) 52%, rgba(0,0,0,0.55) 100%); }
      @keyframes hf-grain-noise { 0%,100% { transform: translate(0,0); } 10% { transform: translate(-5%,-5%); } 20% { transform: translate(-10%,5%); }
        30% { transform: translate(5%,-10%); } 40% { transform: translate(-5%,15%); } 50% { transform: translate(-10%,5%); } 60% { transform: translate(15%,0); }
        70% { transform: translate(0,10%); } 80% { transform: translate(-15%,0); } 90% { transform: translate(10%,5%); } }
      #grain-overlay { position: absolute; inset: 0; pointer-events: none; z-index: 83; overflow: hidden; }
      #grain-overlay .grain-texture { position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
        background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
        opacity: 0.16; animation: hf-grain-noise 0.5s steps(1) infinite; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{{TOTAL}}" data-width="1080" data-height="1920" data-fps="30">
      <div id="stage">
        <div id="paper"></div>
        <div id="header"><span>THE FIVE NEEDS</span><span>REEL Nº 01</span></div>
{{ELS}}
      </div>
      <div id="flash"></div>
      <div id="flicker"></div>
      <div id="vignette"></div>
      <div id="grain-overlay"><div class="grain-texture"></div></div>
      <audio id="vo" src="voiceover.wav" data-start="0" data-duration="{{TOTAL}}" data-track-index="4" data-volume="1"></audio>
    </div>
    <script>
      const tl = gsap.timeline({ paused: true });
      {{JS}}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    main()
