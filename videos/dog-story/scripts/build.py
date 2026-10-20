#!/usr/bin/env python3
"""Dog story: scenes matched to the narration, motion subtitles and motion text edits.

  python3 scripts/build.py [--render]

Order: scripts/voice.py -> scripts/mix.py -> scripts/captions.py -> this.
- SCENES says which clip plays from which narration line (clip content matches what is said)
- every spoken line gets a typewriter subtitle; rule headings get a title card,
  "..." punchlines get a full-screen card, "Case file 41" gets a stamp, the doorbell a glitch
"""
import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "src" / "story.mp4"
CLIPS = ROOT / "assets" / "clips"
CLI = ["node", "/root/.claude/plugins/cache/hyperframes/hyperframes/0.8.152/skills/hyperframes/scripts/plugin-cli.mjs"]
CLIP_LEN, DIP = 10.0417, 0.4

# (clip number, first narration line it covers) — what is on screen matches what is said
SCENES = [
    (1, None),                        # dog-man in the doorway: "stands up on two legs"
    (2, "For 30,000 years"),          # dog by the bed, glowing eyes: "watch someone", "when you wake up"
    (3, "Rule one."),                 # TV, dog in the doorway: "keep watching", "do not stare"
    (4, "Rule two."),                 # dog at the table: "in a chair across from you"
    (5, "Rule three."),               # phone filming the dog: "do not take out your phone"
    (6, "Case file 41."),             # CASE FILE 41, dog at the fridge
    (7, "By now, it has started"),    # the smile: "copy you", "your face", "smile"
    (8, "Rule four."),                # raincoat dog at the bedroom door
    (9, "Rule five."),                # voice through the wall
    (2, "Rule six."),                 # back in its bed
    (10, "Take your keys."),          # leaving the house, keys in hand
    (1, "Rule seven."),               # "we walk on two legs"
]
NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7}
EMPHASIS = {"dog", "dogs", "legs", "stare", "phone", "camera", "watched", "watching", "door", "doors", "handle",
            "raincoat", "name", "wall", "spaces", "good", "boy", "agency", "smile", "face", "keys", "goodbye",
            "sleep", "refrigerator", "seventh", "third", "two"}


def duration(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout)


def ff(args):
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + args, check=True)


def scene_clip(idx, clip, seg):
    """Clip `clip` filling `seg` seconds: slowed forward play, or a slowed forward+reverse loop when long."""
    out = CLIPS / f"s{idx:02d}-c{clip:02d}.mp4"
    if out.exists() and abs(duration(out) - seg) < 0.25:  # blend output can run ~0.15s short
        return out
    src_len = min(CLIP_LEN, duration(SRC) - (clip - 1) * CLIP_LEN) - 0.05
    base = CLIPS / f"base-c{clip:02d}.mp4"
    if seg > 2.0 * src_len:  # long scene: ping-pong so it never freezes or jumps
        t0 = (clip - 1) * CLIP_LEN  # trim inside the graph: input -t is not honoured through split/reverse
        ff(["-i", str(SRC), "-an", "-filter_complex",
            f"[0:v:0]trim=start={t0:.3f}:duration={src_len:.3f},setpts=PTS-STARTPTS,split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1[v]",
            "-map", "[v]",
            "-c:v", "libx264", "-crf", "16", "-preset", "fast", str(base)])
        base_len = 2 * src_len
    else:
        ff(["-ss", f"{(clip - 1) * CLIP_LEN:.3f}", "-t", f"{src_len:.3f}", "-i", str(SRC), "-map", "0:v:0", "-an",
            "-c:v", "libx264", "-crf", "16", "-preset", "fast", str(base)])
        base_len = src_len
    k = seg / base_len
    ff(["-i", str(base), "-vf", f"scale=1920:1080:flags=lanczos,setpts={k:.4f}*PTS,minterpolate=fps=24:mi_mode=blend",
        "-t", f"{seg:.3f}", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", str(out)])
    return out


def words_html(text, cid):
    out = []
    for j, w in enumerate(text.split()):
        key = w.strip(".,!?…—'\"").lower().replace("'s", "")
        cls = "w em" if key in EMPHASIS else "w"
        out.append(f'<span class="{cls}" id="{cid}w{j}">{html.escape(w)}</span>')
    return " ".join(out)


def main():
    caps = json.loads((ROOT / "captions.json").read_text())
    track = "mix.wav" if (ROOT / "assets" / "vo" / "mix.wav").exists() else "voice.wav"
    total = round(duration(ROOT / "assets" / "vo" / track) + 0.0, 3)
    CLIPS.mkdir(exist_ok=True)
    els, stage, js = [], [], []

    # --- scenes: each cut sits in the pause just before its narration line
    def line_start(prefix):
        i = next(k for k, c in enumerate(caps) if c["text"].startswith(prefix))
        return round((caps[i - 1]["end"] + caps[i]["start"]) / 2, 3) if i else 0.0
    starts = [0.0 if p is None else line_start(p) for _, p in SCENES] + [total]
    for i, (clip, _) in enumerate(SCENES):
        a, b = starts[i], starts[i + 1]
        seg = round(b - a, 3)
        out = scene_clip(i, clip, seg)
        stage.append(f'<video id="v{i}" class="clip shot" src="assets/clips/{out.name}" data-start="{a:.3f}" '
                     f'data-duration="{seg:.3f}" data-track-index="1" muted playsinline></video>')
        x = 2 if i % 2 == 0 else -2
        js.append(f'tl.fromTo("#v{i}", {{ scale: 1.0, xPercent: {-x / 2} }}, {{ scale: 1.08, xPercent: {x / 2}, duration: {seg:.3f}, ease: "none" }}, {a:.3f});')
        if i:
            js.append(f'tl.fromTo("#dip", {{ opacity: 0 }}, {{ opacity: 1, duration: {DIP}, ease: "power1.in", immediateRender: false }}, {a - DIP:.3f});')
            js.append(f'tl.fromTo("#dip", {{ opacity: 1 }}, {{ opacity: 0, duration: {DIP}, ease: "power1.out", immediateRender: false }}, {a:.3f});')
        print(f"scene {i:2d}: clip {clip:2d}  {a:7.2f} -> {b:7.2f}  ({seg:5.2f}s)")
    js.insert(0, 'tl.fromTo("#dip", { opacity: 1 }, { opacity: 0, duration: 0.8, ease: "power1.out" }, 0);')

    # --- text layers
    for i, c in enumerate(caps):
        s, e, text, kind = c["start"], c["end"], c["text"], c["kind"]
        nxt = caps[i + 1]["start"] if i + 1 < len(caps) else total
        prev_end = caps[i - 1]["end"] if i else 0.0
        cid = f"c{i}"
        if kind == "rule":  # title card
            n = NUM[text.split()[1].strip(".").lower()]
            dur = round(max(1.6, nxt - s + 0.1), 3)
            els.append(f'<div id="{cid}" class="clip rule" data-start="{s - 0.1:.3f}" data-duration="{dur:.3f}" data-track-index="3">'
                       f'<div class="rk">RULE</div><div class="rn">{n}</div><div class="ro">OF 7</div></div>')
            js.append(f'tl.fromTo("#{cid}", {{ scale: 1.3, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.18, ease: "power4.out" }}, {s - 0.1:.3f});')
            js.append(f'tl.fromTo("#{cid}", {{ opacity: 1 }}, {{ opacity: 0.35, duration: 0.05, yoyo: true, repeat: 3, ease: "none", immediateRender: false }}, {s + 0.12:.3f});')
            js.append(f'tl.fromTo("#{cid}", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.3, ease: "power1.in", immediateRender: false }}, {s - 0.1 + dur - 0.3:.3f});')
            js.append(f'tl.fromTo("#shade", {{ opacity: 0 }}, {{ opacity: 0.55, duration: 0.15, immediateRender: false }}, {s - 0.1:.3f});')
            js.append(f'tl.fromTo("#shade", {{ opacity: 0.55 }}, {{ opacity: 0, duration: 0.3, immediateRender: false }}, {s - 0.1 + dur - 0.3:.3f});')
            continue
        if kind == "punch":  # darken through the pause, the line lands big when spoken
            final = i == len(caps) - 1
            hold_to = total if final else min(nxt - 0.05, e + 0.7)
            dark_from = prev_end + 0.15
            js.append(f'tl.fromTo("#shade", {{ opacity: 0 }}, {{ opacity: 0.7, duration: 0.6, ease: "power1.inOut", immediateRender: false }}, {dark_from:.3f});')
            if not final:
                js.append(f'tl.fromTo("#shade", {{ opacity: 0.7 }}, {{ opacity: 0, duration: 0.35, immediateRender: false }}, {hold_to:.3f});')
            els.append(f'<div id="{cid}" class="clip punch{" final" if final else ""}" data-start="{s:.3f}" '
                       f'data-duration="{hold_to - s:.3f}" data-track-index="3">{html.escape(text.upper())}</div>')
            js.append(f'tl.fromTo("#{cid}", {{ opacity: 0, scale: 1.06 }}, {{ opacity: 1, scale: 1, duration: 0.12, ease: "power2.out" }}, {s:.3f});')
            js.append(f'tl.fromTo("#{cid}", {{ x: -6 }}, {{ x: 6, duration: 0.04, yoyo: true, repeat: 3, ease: "none", immediateRender: false }}, {s:.3f});')
            continue
        if kind == "case":  # rubber stamp
            els.append(f'<div id="{cid}st" class="clip stamp" data-start="{s:.3f}" data-duration="{nxt - s + 1.5:.3f}" data-track-index="3">CASE FILE 41</div>')
            js.append(f'tl.fromTo("#{cid}st", {{ scale: 1.6, opacity: 0, rotation: -6 }}, {{ scale: 1, opacity: 0.92, rotation: -6, duration: 0.12, ease: "power4.in" }}, {s:.3f});')
            js.append(f'tl.fromTo("#{cid}st", {{ opacity: 0.92 }}, {{ opacity: 0, duration: 0.4, immediateRender: false }}, {nxt + 1.1:.3f});')
        # motion subtitle: words type on across the spoken span
        shown_to = min(nxt - 0.03, e + 0.35)
        els.append(f'<div id="{cid}" class="clip cap" data-start="{s:.3f}" data-duration="{shown_to - s:.3f}" data-track-index="2">'
                   f'<span class="line">{words_html(text, cid)}</span></div>')
        words = text.split()
        span = max(0.2, e - s - 0.1)
        weights = [len(w) + 2 for w in words]
        acc = 0.0
        for j, w in enumerate(words):
            t = s + span * acc / sum(weights)
            js.append(f'tl.fromTo("#{cid}w{j}", {{ opacity: 0.15, y: 6 }}, {{ opacity: 1, y: 0, duration: 0.16, ease: "power2.out" }}, {t:.3f});')
            acc += weights[j]

    # --- doorbell glitch, then dead still for "Apologies."
    bell = next(c for c in caps if c["text"].startswith("And if the doorbell"))["end"] + 0.05
    js.append(f'tl.fromTo("#flash", {{ opacity: 0.85 }}, {{ opacity: 0, duration: 0.12, ease: "none", immediateRender: false }}, {bell:.3f});')
    js.append(f'tl.fromTo("#stage", {{ x: -18 }}, {{ x: 18, duration: 0.05, yoyo: true, repeat: 5, ease: "none", immediateRender: false }}, {bell:.3f});')
    js.append(f'tl.fromTo("#stage", {{ x: 18 }}, {{ x: 0, duration: 0.05, ease: "none", immediateRender: false }}, {bell + 0.3:.3f});')
    js.append(f'tl.fromTo("#dip", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6, ease: "power1.in", immediateRender: false }}, {total - 0.6:.3f});')

    els.append(f'<audio id="vo" src="assets/vo/{track}" data-start="0" data-duration="{total}" data-track-index="4" data-volume="1"></audio>')
    page = (PAGE.replace("{{TOTAL}}", str(total)).replace("{{STAGE}}", "\n        ".join(stage))
            .replace("{{ELS}}", "\n      ".join(els)).replace("{{JS}}", "\n      ".join(js)))
    (ROOT / "index.html").write_text(page)
    (ROOT / "segments.json").write_text(json.dumps([{"clip": c, "start": starts[i], "end": starts[i + 1]}
                                                    for i, (c, _) in enumerate(SCENES)], indent=1))
    print(f"built {total}s, {len(caps)} lines")
    if "--render" in sys.argv:
        out = ROOT / "renders" / "dog-story.mp4"
        r = subprocess.run(CLI + ["render", str(ROOT), "-o", str(out), "-q", "delivery"], capture_output=True, text=True)
        print("\n".join(l for l in r.stdout.splitlines() if "MB" in l or "rror" in l))
        share = out.with_name("dog-story-share.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out), "-c:v", "libx264", "-crf", "26", "-preset", "slow",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(share)], check=True)
        print("share:", share)


PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>Dog Story</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1920px; height: 1080px; overflow: hidden; background: #000; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #000; }
      #stage { position: absolute; inset: 0; }
      .shot { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
      #vignette { position: absolute; inset: 0; z-index: 5; pointer-events: none;
        background: radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%); }
      #shade { position: absolute; inset: 0; z-index: 6; background: #000; opacity: 0; pointer-events: none; }
      .cap { position: absolute; left: 0; right: 0; bottom: 86px; z-index: 8; text-align: center; padding: 0 260px; }
      .cap .line { display: inline; font-family: "JetBrains Mono", monospace; font-weight: 600; font-size: 44px; line-height: 1.45;
        color: #f2f2f2; text-shadow: 0 2px 10px rgba(0,0,0,0.95), 0 0 2px #000;
        background: linear-gradient(transparent 8%, rgba(0,0,0,0.55) 8%, rgba(0,0,0,0.55) 92%, transparent 92%);
        box-decoration-break: clone; -webkit-box-decoration-break: clone; padding: 0 14px; }
      .w { display: inline-block; }
      .em { color: #d23a44; }
      .rule { position: absolute; inset: 0; z-index: 9; display: flex; flex-direction: column; align-items: center; justify-content: center;
        font-family: "League Gothic", sans-serif; color: #ececec; text-shadow: 0 0 30px rgba(0,0,0,0.9); }
      .rule .rk { font-size: 86px; letter-spacing: 0.5em; margin-right: -0.5em; line-height: 1; }
      .rule .rn { font-size: 300px; line-height: 0.9; color: #d23a44; }
      .rule .ro { font-size: 46px; letter-spacing: 0.6em; margin-right: -0.6em; opacity: 0.75; }
      .punch { position: absolute; inset: 0; z-index: 9; display: flex; align-items: center; justify-content: center; padding: 0 160px;
        text-align: center; font-family: "League Gothic", sans-serif; font-size: 150px; line-height: 1.02; letter-spacing: 0.04em;
        color: #f4f4f4; text-shadow: 0 0 40px rgba(0,0,0,0.95); }
      .punch.final { color: #d23a44; font-size: 260px; letter-spacing: 0.12em; }
      .stamp { position: absolute; right: 150px; top: 120px; z-index: 9; font-family: "JetBrains Mono", monospace; font-weight: 800;
        font-size: 64px; color: #d23a44; border: 8px solid #d23a44; padding: 10px 30px; letter-spacing: 0.08em; }
      #flash { position: absolute; inset: 0; z-index: 10; background: #fff; opacity: 0; pointer-events: none; }
      #dip { position: absolute; inset: 0; z-index: 7; background: #000; opacity: 1; pointer-events: none; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{{TOTAL}}" data-width="1920" data-height="1080" data-fps="24">
      <div id="stage">
        {{STAGE}}
      </div>
      <div id="vignette"></div>
      <div id="shade"></div>
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
