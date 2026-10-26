#!/usr/bin/env python3
"""Build "The 2:14 Text" (9:16 Short): clip cuts, sound design, captions, motion graphics.

  python3 scripts/voice.py            # silence cut + word timings (run first)
  python3 scripts/build.py [--render]

- 16 clips are cut onto the 18 VO lines (SCENES); each scene starts in the gap before its line
- assets/seg/: every scene's clip trimmed (or slowed, then held) to the scene length, at 1080x1920
- assets/vo/mix.wav: VO + clip ambience + synthesized SFX (whooshes, booms, buzz, ticks, riser), -14 LUFS
- captions: 1-3 words at a time, each word pops on as it is spoken, key words in yellow
- motion graphics: 2:14 AM hook, FLOOR 09 badge, step counter (41..55, then 56?), flashes, end card
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "assets"
SEG = A / "seg"
SR = 48000
W, H, FPS = 1080, 1920, 30
END_HOLD = 3.2  # end card after the last line
CLI = ["node", "/root/.claude/plugins/cache/hyperframes/hyperframes/0.8.152/skills/hyperframes/scripts/plugin-cli.mjs"]

# (clip, source offset in seconds, first VO line it covers)
SCENES = [(1, 0.4, 1), (2, 5.0, 2), (3, 0.0, 3), (4, 0.0, 4), (5, 0.0, 5), (6, 0.0, 7), (7, 0.0, 8), (8, 0.0, 9),
          (9, 0.0, 10), (10, 0.0, 11), (11, 0.0, 12), (12, 0.0, 13), (13, 0.0, 14), (14, 0.0, 15), (15, 0.0, 16),
          (16, 0.0, 18)]
RULE_SCENES = {6, 8, 11, 14}  # clips that open on a baked-in rule card
EMPH = {"two", "fourteen", "a.m", "no", "name", "again", "indoors", "nine", "only", "unknown", "mother's", "count",
        "every", "one", "more", "porch", "off", "don't", "already", "never", "yes", "come", "right", "wrong", "open"}


def ff(args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + args, check=True)


def dur(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True).stdout)


def scene_clip(i, clip, off, seg):
    """Scene video (silent, 1080x1920) and its ambience wav, both exactly seg seconds."""
    src = A / "clips" / f"PT_{clip:02d}.mp4"
    out, amb = SEG / f"s{i:02d}.mp4", SEG / f"s{i:02d}.wav"
    if out.exists() and abs(dur(out) - seg) < 0.08 and amb.exists():
        return out, amb
    avail = dur(src) - off - 0.05
    k = min(1.5, seg / avail) if seg > avail else 1.0  # slow a short clip down a little, then hold its last frame
    vf = f"scale={W}:{H}:flags=lanczos,setpts={k:.4f}*(PTS-STARTPTS),tpad=stop_mode=clone:stop_duration={seg:.3f}"
    ff(["-ss", f"{off:.3f}", "-i", str(src), "-vf", vf, "-t", f"{seg:.3f}", "-an", "-r", "24",
        "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p", str(out)])
    ff(["-ss", f"{off:.3f}", "-i", str(src), "-vn", "-af", f"apad,atrim=0:{seg:.3f}", "-ac", "1", "-ar", str(SR), str(amb)])
    return out, amb


# ---------- sound design (deterministic synthesis) ----------
def db(x):
    return 10 ** (x / 20)


def noise(n, seed):
    return np.random.default_rng(seed).standard_normal(n).astype(np.float32)


def lowpass(x, a):
    """One-pole lowpass; a may be a constant or a per-sample array (filter sweep)."""
    a = np.broadcast_to(np.asarray(a, dtype=np.float32), x.shape)
    y, acc = np.empty_like(x), 0.0
    for i, v in enumerate(x):
        acc += a[i] * (v - acc)
        y[i] = acc
    return y


def whoosh(seed, length=0.45):
    n = int(length * SR)
    t = np.linspace(0, 1, n)
    env = np.sin(np.pi * t) ** 2
    return lowpass(noise(n, seed), 0.08) * env * 3.0


def boom(length=1.2):
    n = int(length * SR)
    t = np.arange(n) / SR
    f = 38 + 90 * np.exp(-t * 9)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    click = lowpass(noise(n, 7), 0.3) * np.exp(-t * 60) * 0.6
    return (s + click).astype(np.float32)


def buzz(length=0.32):
    n = int(length * SR)
    t = np.arange(n) / SR
    s = np.sign(np.sin(2 * np.pi * 148 * t)) * 0.5 + np.sin(2 * np.pi * 74 * t)
    return (lowpass(s.astype(np.float32), 0.12) * np.minimum(1, t * 80) * np.minimum(1, (length - t) * 80))


def tick():
    n = int(0.035 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2200 * t) * np.exp(-t * 180)).astype(np.float32)


def riser(length):
    n = int(length * SR)
    t = np.linspace(0, 1, n)
    hiss = lowpass(noise(n, 11), 0.05 + 0.25 * t)
    tone = np.sin(2 * np.pi * np.cumsum(80 + 300 * t ** 2) / SR)
    return ((hiss * 2.2 + tone * 0.35) * t ** 2.2).astype(np.float32)


def drone(n):
    t = np.arange(n) / SR
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t)
    s = np.sin(2 * np.pi * 55 * t) + 0.6 * np.sin(2 * np.pi * 82.4 * t + 1) + 0.3 * np.sin(2 * np.pi * 110.3 * t)
    return (s * lfo / 1.9).astype(np.float32)


def place(bus, x, at, gain_db):
    i = int(at * SR)
    if i >= len(bus):
        return
    x = x[: len(bus) - i]
    bus[i:i + len(x)] += x * db(gain_db)


def mix(total, starts, ambs, lines, words, counter):
    n = int(total * SR)
    bus = np.zeros(n, dtype=np.float32)
    vo, _ = sf.read(A / "vo" / "voice.wav", dtype="float32")
    place(bus, vo, 0, 0)
    for a, amb in zip(starts, ambs):
        x, _ = sf.read(amb, dtype="float32")
        f = int(0.06 * SR)
        x[:f] *= np.linspace(0, 1, f)
        x[-f:] *= np.linspace(1, 0, f)
        place(bus, x, a, -2)
    d = drone(n)
    d[: SR] *= np.linspace(0, 1, SR)
    d[-SR:] *= np.linspace(1, 0, SR)
    place(bus, d, 0, -34)
    for i, (a, (clip, _, _)) in enumerate(zip(starts, SCENES)):
        if i == 0:
            continue
        if clip in RULE_SCENES:
            place(bus, boom(), a - 0.02, -10)
        else:
            place(bus, whoosh(i), a - 0.22, -24)
    line = {l["line"]: l for l in lines}
    place(bus, buzz(), line[3]["start"] - 0.05, -18)
    place(bus, buzz(), line[3]["start"] + 0.4, -18)
    for t, _ in counter:
        place(bus, tick(), t, -22)
    one = next(w for w in words if w["line"] == 11 and w["word"] == "one")
    place(bus, boom(), one["start"] - 0.02, -12)
    wrong = next(w for w in words if w["line"] == 17 and w["word"] == "wrong")
    place(bus, boom(), wrong["start"] - 0.02, -12)
    r0, r1 = line[17]["end"] - 0.2, line[18]["start"] - 0.03
    place(bus, riser(r1 - r0), r0, -20)  # cut dead before "Do you open it?"
    place(bus, boom(1.8), line[18]["end"] + 0.12, -9)  # end card hit
    peak = np.max(np.abs(bus))
    bus = np.tanh(bus / max(peak, 1e-6) * 1.4) / np.tanh(1.4) * 0.89  # soft limit
    raw = A / "vo" / "mix_raw.wav"
    sf.write(raw, bus, SR)
    ff(["-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), str(A / "vo" / "mix.wav")])
    raw.unlink()


# ---------- captions ----------
def caption_groups(lines, words):
    """Script tokens timed by their aligned words, grouped 1-3 per caption."""
    groups, wi = [], 0
    for l in lines:
        toks = []
        for tok in l["text"].split():
            k = len([w for w in re.sub(r"[^a-z' ]", " ", tok.lower().replace("a.m.", "a m")).split() if w.strip("'")])
            ws = words[wi:wi + k]
            wi += k
            toks.append({"text": tok.upper(), "start": ws[0]["start"], "end": ws[-1]["end"],
                         "em": tok.lower().strip('.,?"!') in EMPH})
        cur = []
        for t in toks:
            cur.append(t)
            if len(cur) == 3 or t["text"][-1] in ".,?\"" or t["text"] in ("RULE",):
                groups.append(cur)
                cur = []
        if cur:
            groups.append(cur)
    # each group shows from its first word until the next group starts (or a short hold after the line)
    out = []
    for i, g in enumerate(groups):
        a = g[0]["start"] - 0.04
        nxt = groups[i + 1][0]["start"] - 0.04 if i + 1 < len(groups) else g[-1]["end"] + 0.3
        b = min(nxt, g[-1]["end"] + 0.6)
        out.append({"start": round(a, 3), "end": round(b, 3), "toks": g})
    return out


def main():
    SEG.mkdir(exist_ok=True)
    lines = json.loads((ROOT / "lines.json").read_text())
    words = json.loads((ROOT / "words.json").read_text())
    L = {l["line"]: l for l in lines}
    total = round(L[18]["end"] + END_HOLD, 3)
    starts = [0.0] + [round((L[f - 1]["end"] + L[f]["start"]) / 2, 3) for _, _, f in SCENES[1:]]
    bounds = starts + [total]

    stage, els, js, ambs = [], [], [], []
    for i, (clip, off, first) in enumerate(SCENES):
        a, b = bounds[i], bounds[i + 1]
        seg = round(b - a, 3)
        out, amb = scene_clip(i, clip, off, seg)
        ambs.append(amb)
        stage.append(f'<video id="v{i}" class="clip shot" src="assets/seg/{out.name}" data-start="{a:.3f}" '
                     f'data-duration="{seg:.3f}" data-track-index="1" muted playsinline></video>')
        if clip not in RULE_SCENES:
            js.append(f'tl.fromTo("#v{i}", {{ scale: 1.0 }}, {{ scale: 1.07, duration: {seg:.3f}, ease: "none" }}, {a:.3f});')
        else:
            js.append(f'tl.fromTo("#flash", {{ opacity: 0.9 }}, {{ opacity: 0, duration: 0.18, ease: "power1.out", immediateRender: false }}, {a:.3f});')
            js.append(f'tl.fromTo("#v{i}", {{ scale: 1.18 }}, {{ scale: 1.0, duration: 0.3, ease: "power3.out", immediateRender: false }}, {a:.3f});')
            js.append(f'tl.fromTo("#v{i}", {{ scale: 1.0 }}, {{ scale: 1.06, duration: {seg - 0.3:.3f}, ease: "none", immediateRender: false }}, {a + 0.3:.3f});')
        print(f"scene {i + 1:2d}: PT_{clip:02d} @{off:.1f}s  {a:6.2f} -> {b:6.2f} ({seg:.2f}s)  line {first}")

    # 2:14 AM hook
    els.append(f'<div id="hook" class="clip" data-start="0" data-duration="{L[1]["end"] + 0.1:.3f}" data-track-index="5">'
               '<span class="hk">2:14</span><span class="am">AM</span></div>')
    js.append('tl.fromTo("#hook", { scale: 2.4, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.28, ease: "power4.in" }, 0.05);')
    js.append('tl.fromTo("#stage", { y: 0 }, { y: 22, duration: 0.04, yoyo: true, repeat: 5, ease: "none", immediateRender: false }, 0.33);')
    js.append('tl.fromTo("#hook", { opacity: 1 }, { opacity: 0.35, duration: 0.05, yoyo: true, repeat: 3, ease: "none", immediateRender: false }, 1.2);')
    js.append(f'tl.fromTo("#hook", {{ opacity: 1, scale: 1 }}, {{ opacity: 0, scale: 0.9, duration: 0.18, ease: "power1.in", immediateRender: false }}, {L[1]["end"] - 0.08:.3f});')

    # FLOOR 09 badge over lines 5-6
    fa, fb = L[5]["start"], L[6]["end"]
    els.append(f'<div id="floor" class="clip" data-start="{fa - 0.05:.3f}" data-duration="{fb - fa + 0.15:.3f}" data-track-index="5">'
               '<span class="fl">FLOOR</span><span class="fn">09</span><span class="arr"></span></div>')
    js.append(f'tl.fromTo("#floor", {{ x: -700 }}, {{ x: 0, duration: 0.35, ease: "back.out(1.6)" }}, {fa - 0.05:.3f});')
    js.append(f'tl.fromTo("#floor .arr", {{ y: -10 }}, {{ y: 14, duration: 0.35, yoyo: true, repeat: {int((fb - fa) / 0.35)}, ease: "sine.inOut", immediateRender: false }}, {fa + 0.3:.3f});')
    js.append(f'tl.fromTo("#floor", {{ x: 0 }}, {{ x: 700, duration: 0.25, ease: "power2.in", immediateRender: false }}, {fb - 0.15:.3f});')

    # step counter: 41..55 across line 10, holds, then "56?" on "one more step"
    one = next(w for w in words if w["line"] == 11 and w["word"] == "one")
    ca, cb = L[10]["start"], L[10]["end"]
    nums = list(range(41, 56))
    step = (cb - ca) / len(nums)
    counter = []
    for k, num in enumerate(nums):
        t0 = ca + k * step
        t1 = ca + (k + 1) * step if k + 1 < len(nums) else one["start"]
        counter.append((round(t0, 3), num))
        els.append(f'<div class="clip cnt" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="6">{num}</div>')
    c_end = L[11]["end"] + 0.1
    els.append(f'<div id="c56" class="clip cnt bad" data-start="{one["start"]:.3f}" data-duration="{c_end - one["start"]:.3f}" data-track-index="6">56?</div>')
    els.append(f'<div id="clab" class="clip" data-start="{ca:.3f}" data-duration="{one["start"] - ca:.3f}" data-track-index="5">STEP</div>')
    js.append(f'tl.fromTo("#clab", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.2, ease: "power2.out" }}, {ca:.3f});')
    js.append(f'tl.fromTo("#c56", {{ scale: 2.2 }}, {{ scale: 1, duration: 0.22, ease: "power4.in" }}, {one["start"]:.3f});')
    js.append(f'tl.fromTo("#rflash", {{ opacity: 0.55 }}, {{ opacity: 0, duration: 0.35, ease: "power1.out", immediateRender: false }}, {one["start"] + 0.2:.3f});')
    js.append(f'tl.fromTo("#stage", {{ x: -16 }}, {{ x: 16, duration: 0.045, yoyo: true, repeat: 5, ease: "none", immediateRender: false }}, {one["start"] + 0.2:.3f});')
    js.append(f'tl.fromTo("#stage", {{ x: 16 }}, {{ x: 0, duration: 0.045, ease: "none", immediateRender: false }}, {one["start"] + 0.47:.3f});')

    # "It says it wrong." glitch
    wrong = next(w for w in words if w["line"] == 17 and w["word"] == "wrong")
    wt = wrong["start"]
    js.append(f'tl.fromTo("#rflash", {{ opacity: 0.6 }}, {{ opacity: 0, duration: 0.4, ease: "power1.out", immediateRender: false }}, {wt:.3f});')
    js.append(f'tl.fromTo("#stage", {{ x: -24, skewX: 6 }}, {{ x: 24, skewX: -6, duration: 0.04, yoyo: true, repeat: 7, ease: "none", immediateRender: false }}, {wt:.3f});')
    js.append(f'tl.fromTo("#stage", {{ x: 24, skewX: -6 }}, {{ x: 0, skewX: 0, duration: 0.04, ease: "none", immediateRender: false }}, {wt + 0.32:.3f});')

    # end card
    ea = round(L[18]["end"] + 0.12, 3)
    els.append(f'<div id="end" class="clip" data-start="{ea:.3f}" data-duration="{total - ea:.3f}" data-track-index="7">'
               '<div class="btns"><span class="yes">YES</span><span class="no">NO</span></div>'
               '<div class="cmt">COMMENT BELOW <span class="tri"></span></div></div>')
    js.append(f'tl.fromTo("#end .yes", {{ x: -500, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.35, ease: "back.out(1.7)" }}, {ea + 0.25:.3f});')
    js.append(f'tl.fromTo("#end .no", {{ x: 500, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.35, ease: "back.out(1.7)" }}, {ea + 0.35:.3f});')
    js.append(f'tl.fromTo("#end .cmt", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.3, ease: "power2.out" }}, {ea + 0.7:.3f});')
    js.append(f'tl.fromTo("#end .tri", {{ y: -8 }}, {{ y: 12, duration: 0.3, yoyo: true, repeat: 5, ease: "sine.inOut", immediateRender: false }}, {ea + 1.0:.3f});')
    js.append(f'tl.fromTo("#shade", {{ opacity: 0 }}, {{ opacity: 0.3, duration: 0.3, ease: "none", immediateRender: false }}, {ea:.3f});')

    # captions
    caps = caption_groups(lines, words)
    for gi, g in enumerate(caps):
        spans = []
        for ti, t in enumerate(g["toks"]):
            spans.append(f'<span id="w{gi}_{ti}" class="w{" em" if t["em"] else ""}">{t["text"]}</span>')
            js.append(f'tl.fromTo("#w{gi}_{ti}", {{ opacity: 0, scale: 0.6, y: 24 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.14, ease: "back.out(2.2)" }}, {max(0, t["start"] - 0.04):.3f});')
        els.append(f'<div class="clip cap" data-start="{g["start"]:.3f}" data-duration="{g["end"] - g["start"]:.3f}" data-track-index="8">'
                   + " ".join(spans) + "</div>")

    # progress bar
    js.append(f'tl.fromTo("#bar", {{ scaleX: 0 }}, {{ scaleX: 1, duration: {total}, ease: "none" }}, 0);')
    els.append(f'<audio id="mix" src="assets/vo/mix.wav" data-start="0" data-duration="{total}" data-track-index="9" data-volume="1"></audio>')

    mix(total, starts, ambs, lines, words, counter)
    page = (PAGE.replace("{{TOTAL}}", str(total)).replace("{{STAGE}}", "\n        ".join(stage))
            .replace("{{ELS}}", "\n      ".join(els)).replace("{{JS}}", "\n      ".join(js)))
    (ROOT / "index.html").write_text(page)
    print(f"built {total}s, {len(caps)} captions, {len(SCENES)} scenes")
    if "--render" in sys.argv:
        out = ROOT / "renders" / "story-214.mp4"
        r = subprocess.run(CLI + ["render", str(ROOT), "-o", str(out), "-q", "delivery"], capture_output=True, text=True)
        print("\n".join(l for l in (r.stdout + r.stderr).splitlines() if "MB" in l or "rror" in l))
        share = out.with_name("story-214-share.mp4")
        ff(["-i", str(out), "-c:v", "libx264", "-crf", "22", "-preset", "slow", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(share)])
        print("share:", share)


PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>The 2:14 Text</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #000; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #000; }
      #stage { position: absolute; inset: 0; }
      .shot { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
      #vignette { position: absolute; inset: 0; z-index: 4; pointer-events: none;
        background: radial-gradient(ellipse at 50% 40%, rgba(0,0,0,0) 50%, rgba(0,0,0,0.6) 100%); }
      #shade { position: absolute; inset: 0; z-index: 6; background: #000; opacity: 0; pointer-events: none; }
      #flash { position: absolute; inset: 0; z-index: 12; background: #fff; opacity: 0; pointer-events: none; }
      #rflash { position: absolute; inset: 0; z-index: 12; background: #e3242b; opacity: 0; pointer-events: none; mix-blend-mode: screen; }
      #barbox { position: absolute; left: 0; top: 0; width: 100%; height: 10px; z-index: 11; background: rgba(255,255,255,0.12); }
      #bar { width: 100%; height: 100%; background: #e3242b; transform-origin: 0 50%; }
      #hook { position: absolute; left: 0; right: 0; top: 1010px; z-index: 7; text-align: center; font-family: "JetBrains Mono", monospace;
        font-weight: 800; color: #ff3b3b; text-shadow: 0 0 40px rgba(255,40,40,0.75), 0 6px 20px #000; }
      #hook .hk { font-size: 230px; letter-spacing: -0.02em; }
      #hook .am { font-size: 90px; margin-left: 20px; }
      #floor { position: absolute; left: 70px; top: 1060px; z-index: 7; display: flex; align-items: center; gap: 18px;
        padding: 14px 34px; background: #ffd23f; color: #111; border-radius: 18px; font-family: "Montserrat", sans-serif;
        font-weight: 900; box-shadow: 0 14px 40px rgba(0,0,0,0.6); }
      #floor .fl { font-size: 46px; letter-spacing: 0.06em; }
      #floor .fn { font-size: 84px; line-height: 1; }
      #floor .arr { width: 0; height: 0; border-left: 26px solid transparent; border-right: 26px solid transparent; border-top: 34px solid #111; }
      .cnt { position: absolute; left: 0; right: 0; top: 940px; z-index: 7; text-align: center; font-family: "JetBrains Mono", monospace;
        font-weight: 800; font-size: 210px; color: #c8f560; text-shadow: 0 0 36px rgba(200,245,96,0.55), 0 6px 20px #000; }
      .cnt.bad { color: #ff3b3b; text-shadow: 0 0 46px rgba(255,40,40,0.85), 0 6px 20px #000; }
      #clab { position: absolute; left: 0; right: 0; top: 890px; z-index: 7; text-align: center; font-family: "Montserrat", sans-serif;
        font-weight: 900; font-size: 48px; letter-spacing: 0.4em; margin-right: -0.4em; color: #fff; text-shadow: 0 4px 14px #000; }
      .cap { position: absolute; left: 70px; right: 70px; top: 1300px; z-index: 9; text-align: center; font-family: "Montserrat", sans-serif;
        font-weight: 900; font-size: 84px; line-height: 1.12; color: #fff; -webkit-text-stroke: 12px #000; paint-order: stroke fill;
        text-shadow: 0 8px 26px rgba(0,0,0,0.85); }
      .cap .w { display: inline-block; opacity: 0; }
      .cap .em { color: #ffd23f; }
      #end { position: absolute; left: 0; right: 0; top: 1240px; z-index: 10; text-align: center; font-family: "Montserrat", sans-serif; font-weight: 900; }
      #end .btns { display: flex; justify-content: center; gap: 60px; }
      #end .btns span { display: inline-block; min-width: 330px; padding: 26px 0 22px; border-radius: 26px; font-size: 100px; color: #111;
        box-shadow: 0 16px 40px rgba(0,0,0,0.6); }
      #end .yes { background: #c8f560; }
      #end .no { background: #ff3b3b; color: #fff; }
      #end .cmt { margin-top: 70px; font-size: 54px; color: #ffd23f; letter-spacing: 0.08em; text-shadow: 0 6px 20px #000; }
      #end .tri { display: inline-block; width: 0; height: 0; margin-left: 16px; border-left: 22px solid transparent;
        border-right: 22px solid transparent; border-top: 30px solid #ffd23f; vertical-align: middle; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{{TOTAL}}" data-width="1080" data-height="1920" data-fps="30">
      <div id="stage">
        {{STAGE}}
      </div>
      <div id="vignette"></div>
      <div id="shade"></div>
      <div id="barbox"><div id="bar"></div></div>
      {{ELS}}
      <div id="flash"></div>
      <div id="rflash"></div>
    </div>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      {{JS}}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    main()
