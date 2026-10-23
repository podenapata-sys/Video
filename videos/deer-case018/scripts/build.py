#!/usr/bin/env python3
"""Case 018 deer: voice + SFX mix, 95 image scenes, typewriter subtitles -> index.html.

  python3 scripts/build.py [--render]

Inputs: vo_lines.json (scripts/transcript.py), scene_map.json (scene -> image), assets/vo, assets/sfx.
Each image starts in the pause before its first spoken phrase; subtitles type on per phrase (ALL CAPS);
"Rule number X." phrases are not subtitled because the image is already the rule title card.
"""
import html
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
VO, SFX = ROOT / "assets" / "vo", ROOT / "assets" / "sfx"
CLI = ["node", "/root/.claude/plugins/cache/hyperframes/hyperframes/0.8.152/skills/hyperframes/scripts/plugin-cli.mjs"]
SR, CHUNK_GAP, TAIL = 48000, 0.8, 1.5
EMPHASIS = {"deer", "lights", "window", "head", "hoof", "strike", "breathing", "shoulder", "name", "voice", "stay", "door",
            "knocking", "scratching", "glass", "figure", "human", "3:17", "3:00", "darkness", "hours", "walking"}

# sound design: (file, scene, phrase index within the scene, offset s, gain dB, clip start s, clip length s)
CUES = [
    ("SFX_Clock_Ticking_Bass", 1, 0, -0.5, 2, 0.0, 9.0),        # 3 a.m. cold open
    ("SFX_Sub_Bass_Drop", 23, 0, -0.1, 0, 0.0, 3.0),            # "This one won't."
    ("SFX_Heavy_Hoof_Strike", 34, 1, -0.9, 6, 0.6, 2.6),        # "One hard strike against the ground."
    ("SFX_Heartbeat_Thump", 35, 1, 0.0, 4, 0.0, 4.0),           # "Don't move."
    ("SFX_Close_Breathing_Creak", 38, 0, 0.6, -2, 0.0, 2.0),    # breathing behind you / floor creaking
    ("SFX_Heavy_Hoof_Strike", 41, 0, 1.6, 4, 0.6, 2.6),         # "...another hoof strike"
    ("SFX_Heavy_Hoof_Strike", 42, 0, 0.0, 0, 0.6, 2.6),         # "...from inside the house"
    ("SFX_Mimic_Distorted_Voice", 45, 0, 1.2, 12, 0.6, 5.8),    # mother calling from the kitchen
    ("SFX_Clock_Ticking_Bass", 59, 0, -0.3, 2, 0.0, 4.5),       # "at exactly 3:17"
    ("SFX_Mimic_Distorted_Voice", 66, 0, 0.0, 12, 0.6, 5.8),    # something upstairs kept calling her name
    ("SFX_Mimic_Distorted_Voice", 72, 0, 0.3, 10, 0.6, 5.8),    # your own voice asking to be let in
    ("SFX_Security_Glitch_Rewind", 84, 0, 0.0, -4, 0.0, 3.8),   # security cameras
    ("SFX_Jump_Scare_Stinger", 88, 0, -0.5, -3, 0.0, 4.0),      # "A figure was already standing behind the glass." (hit at 0.5s)
    ("SFX_Sub_Bass_Drop", 93, 0, -0.1, 0, 0.0, 3.0),            # "Practicing how to look like you."
]
SHAKES = {34, 41, 42}   # scenes whose first hoof cue gets a camera shake
FLASH = {88}            # jump scare flash
GLITCH = {84}           # camera glitch flicker


def load(path, n=None):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()


def ramp(n, up=True):
    r = np.linspace(0, 1, max(1, n), dtype=np.float32)[:, None]
    return r if up else 1 - r


def timeline(lines):
    """Global start/end for every phrase: chunks back to back with CHUNK_GAP between them."""
    off, chunks = 0.0, []
    for c in range(1, 7):
        f = sorted(VO.glob(f"VO_Chunk_{c}_*.mp3"))[0]
        a = load(f)
        chunks.append((off, a))
        for ln in lines:
            if ln["chunk"] == c:
                ln["t0"], ln["t1"] = round(off + ln["start"], 3), round(off + ln["end"], 3)
        off += len(a) / SR + CHUNK_GAP
    return chunks, round(off - CHUNK_GAP + TAIL, 3)


def mix(lines, chunks, total):
    n = int(total * SR)
    bus = np.zeros((n, 2), np.float32)
    for off, a in chunks:
        s = int(off * SR)
        bus[s:s + len(a)] += a[: n - s]
    # tape hiss bed, looped with crossfades, ~-46 dBFS RMS, fades in/out
    h = load(SFX / "SFX_Tape_Hiss_Ambient.mp3")
    xf = SR
    loop = h[:-xf].copy()
    loop[:xf] = loop[:xf] * ramp(xf) + h[-xf:] * ramp(xf, False)
    bed = np.tile(loop, (n // len(loop) + 1, 1))[:n]
    bed *= (10 ** (-46 / 20)) / max(1e-9, np.sqrt(np.mean(bed ** 2)))
    bed[: 3 * SR] *= ramp(3 * SR)
    bed[-2 * SR:] *= ramp(2 * SR, False)
    bus += bed
    cue_times = []
    for name, scene, k, dt, gain, c0, clen in CUES:
        ph = [ln for ln in lines if ln["scene"] == scene][k]
        t = ph["t0"] + dt
        clip = load(SFX / f"{name}.mp3")[int(c0 * SR): int((c0 + clen) * SR)]
        fade = int(0.25 * SR)
        clip[-fade:] *= ramp(fade, False)
        clip[:240] *= ramp(240)
        a = int(max(0, t) * SR)
        bus[a:a + len(clip)] += clip[: n - a] * 10 ** (gain / 20)
        cue_times.append((name, scene, round(t, 2)))
    peak = float(np.abs(bus).max())
    ceil = 10 ** (-1 / 20)
    if peak > ceil:  # soft-limit only what pokes over
        knee = ceil * 0.9
        over = np.abs(bus) > knee
        bus[over] = np.sign(bus[over]) * (knee + (ceil - knee) * np.tanh((np.abs(bus[over]) - knee) / (ceil - knee)))
    sf.write(VO / "mix.wav", bus, SR)
    print(f"mix.wav {total:.1f}s, peak {20 * np.log10(peak):.1f} -> {20 * np.log10(np.abs(bus).max()):.1f} dBFS")
    return cue_times


def words_html(text, cid):
    out = []
    for j, w in enumerate(text.upper().split()):
        key = w.strip(".,!?\"'").lower()
        out.append(f'<span class="w{" em" if key in EMPHASIS else ""}" id="{cid}w{j}">{html.escape(w)}</span>')
    return " ".join(out)


def main():
    lines = json.loads((ROOT / "vo_lines.json").read_text())
    smap = {s["scene"]: s for s in json.loads((ROOT / "scene_map.json").read_text())}
    chunks, total = timeline(lines)
    cues = mix(lines, chunks, total)
    first = {}
    for i, ln in enumerate(lines):
        if ln["scene"] not in first:
            prev_end = lines[i - 1]["t1"] if i else 0.0
            first[ln["scene"]] = 0.0 if i == 0 else round((prev_end + ln["t0"]) / 2, 3)
    starts = [first[s] for s in range(1, 96)] + [total]
    imgs, els, js, seen = [], [], [], {}
    for s in range(1, 96):
        a, b = starts[s - 1], starts[s]
        d = round(b - a, 3)
        src = f"assets/img/{smap[s]['image_id']:03d}.jpg"
        n_use = seen.get(src, 0)
        seen[src] = n_use + 1
        iid = f"i{s}"
        imgs.append(f'<img id="{iid}" class="clip shot" src="{html.escape(src)}" data-start="{a:.3f}" data-duration="{d:.3f}" '
                    f'data-track-index="1" alt="" />')
        sign = 1 if s % 2 else -1
        if n_use:  # second use of an image: start tighter, push the other way
            js.append(f'tl.fromTo("#{iid}", {{ scale: 1.22, xPercent: {2 * sign} }}, {{ scale: 1.3, xPercent: {-2 * sign}, duration: {d:.3f}, ease: "none" }}, {a:.3f});')
        else:
            js.append(f'tl.fromTo("#{iid}", {{ scale: 1.0, xPercent: {-1.2 * sign}, rotation: {-0.4 * sign} }}, '
                      f'{{ scale: 1.1, xPercent: {1.2 * sign}, rotation: {0.4 * sign}, duration: {d:.3f}, ease: "none" }}, {a:.3f});')
        if s > 1:  # quick dip between scenes
            js.append(f'tl.fromTo("#dip", {{ opacity: 0 }}, {{ opacity: 0.55, duration: 0.12, ease: "none", immediateRender: false }}, {a - 0.12:.3f});')
            js.append(f'tl.fromTo("#dip", {{ opacity: 0.55 }}, {{ opacity: 0, duration: 0.25, ease: "power1.out", immediateRender: false }}, {a:.3f});')
    js.insert(0, 'tl.fromTo("#dip", { opacity: 1 }, { opacity: 0, duration: 1.2, ease: "power1.out" }, 0);')
    js.append(f'tl.fromTo("#dip", {{ opacity: 0 }}, {{ opacity: 1, duration: 1.2, ease: "power1.in", immediateRender: false }}, {total - 1.2:.3f});')

    for i, ln in enumerate(lines):
        if ln["text"].startswith("Rule number"):
            continue  # the image is the rule card
        cid = f"c{i}"
        s, e = ln["t0"], ln["t1"]
        nxt = lines[i + 1]["t0"] if i + 1 < len(lines) else total
        shown = min(nxt - 0.03, e + 0.4)
        els.append(f'<div id="{cid}" class="clip cap" data-start="{s:.3f}" data-duration="{shown - s:.3f}" data-track-index="2">'
                   f'<span class="line">{words_html(ln["text"], cid)}</span></div>')
        words = ln["text"].split()
        span = max(0.2, e - s - 0.08)
        wts = [len(w) + 2 for w in words]
        acc = 0
        for j in range(len(words)):
            t = s + span * acc / sum(wts)
            js.append(f'tl.fromTo("#{cid}w{j}", {{ opacity: 0.12, y: 6 }}, {{ opacity: 1, y: 0, duration: 0.15, ease: "power2.out" }}, {t:.3f});')
            acc += wts[j]

    done_shake = set()
    for name, scene, t in cues:
        if "Hoof" in name and scene in SHAKES and scene not in done_shake:
            done_shake.add(scene)
            h = t + 1.15  # strike transient sits ~1.15s into the used clip
            js.append(f'tl.fromTo("#stage", {{ x: -14, y: 6 }}, {{ x: 14, y: -6, duration: 0.05, yoyo: true, repeat: 5, ease: "none", immediateRender: false }}, {h:.3f});')
            js.append(f'tl.fromTo("#stage", {{ x: 14, y: -6 }}, {{ x: 0, y: 0, duration: 0.06, ease: "none", immediateRender: false }}, {h + 0.3:.3f});')
        if "Jump" in name and scene in FLASH:
            js.append(f'tl.fromTo("#flash", {{ opacity: 0.9 }}, {{ opacity: 0, duration: 0.18, ease: "none", immediateRender: false }}, {t + 0.5:.3f});')
            js.append(f'tl.fromTo("#stage", {{ scale: 1.12 }}, {{ scale: 1, duration: 0.35, ease: "expo.out", immediateRender: false }}, {t + 0.5:.3f});')
        if "Glitch" in name and scene in GLITCH:
            js.append(f'tl.fromTo("#stage", {{ opacity: 0.35, x: 22 }}, {{ opacity: 1, x: 0, duration: 0.07, yoyo: true, repeat: 7, ease: "none", immediateRender: false }}, {t:.3f});')
            js.append(f'tl.fromTo("#stage", {{ opacity: 1, x: 0 }}, {{ opacity: 1, x: 0, duration: 0.01, immediateRender: false }}, {t + 0.6:.3f});')

    els.append(f'<audio id="mix" src="assets/vo/mix.wav" data-start="0" data-duration="{total}" data-track-index="4" data-volume="1"></audio>')
    page = (PAGE.replace("{{TOTAL}}", str(total)).replace("{{IMGS}}", "\n        ".join(imgs))
            .replace("{{ELS}}", "\n      ".join(els)).replace("{{JS}}", "\n      ".join(js)))
    (ROOT / "index.html").write_text(page)
    (ROOT / "scene_times.json").write_text(json.dumps([{"scene": s, "start": starts[s - 1], "end": starts[s],
                                                         "image": smap[s]["image"]} for s in range(1, 96)], indent=1))
    print(f"built {total}s: 95 scenes, {len(els) - 1} subtitles, {len(cues)} sfx cues")
    if "--render" in sys.argv:
        out = ROOT / "renders" / "case018.mp4"
        r = subprocess.run(CLI + ["render", str(ROOT), "-o", str(out), "-q", "delivery"], capture_output=True, text=True)
        print("\n".join(l for l in r.stdout.splitlines() if "MB" in l or "rror" in l))
        share = out.with_name("case018-share.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out), "-c:v", "libx264", "-crf", "26", "-preset", "slow",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(share)], check=True)
        print("share:", share)


PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>Case 018 The Deer in the Yard</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1920px; height: 1080px; overflow: hidden; background: #000; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #000; }
      #stage { position: absolute; inset: 0; }
      .shot { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
      #vignette { position: absolute; inset: 0; z-index: 5; pointer-events: none;
        background: radial-gradient(ellipse at center, rgba(0,0,0,0) 60%, rgba(0,0,0,0.5) 100%); }
      #dip { position: absolute; inset: 0; z-index: 6; background: #000; opacity: 1; pointer-events: none; }
      .cap { position: absolute; left: 0; right: 0; bottom: 70px; z-index: 8; text-align: center; padding: 0 240px; }
      .cap .line { font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 42px; line-height: 1.4; letter-spacing: 0.02em;
        color: #f4f4f4; text-shadow: 0 2px 10px rgba(0,0,0,0.95), 0 0 2px #000;
        background: linear-gradient(transparent 6%, rgba(0,0,0,0.6) 6%, rgba(0,0,0,0.6) 94%, transparent 94%);
        box-decoration-break: clone; -webkit-box-decoration-break: clone; padding: 0 14px; }
      .w { display: inline-block; }
      .em { color: #ffd23f; }
      #flash { position: absolute; inset: 0; z-index: 10; background: #fff; opacity: 0; pointer-events: none; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{{TOTAL}}" data-width="1920" data-height="1080" data-fps="30">
      <div id="stage">
        {{IMGS}}
      </div>
      <div id="vignette"></div>
      <div id="dip"></div>
      {{ELS}}
      <div id="flash"></div>
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
