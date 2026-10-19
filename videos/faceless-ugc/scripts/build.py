#!/usr/bin/env python3
"""Faceless Content Rewards UGC: screen visuals + your own voiceover + word-pop subtitles.

  python3 scripts/build.py [--render]

Reads script.json. Each line = one spoken sentence, the visual under it, and how long
it holds. Drop your recording in assets/footage/voice.wav (or .mp3, set "voice"):
if it is there, line timings are re-measured from the pauses between your sentences
so the subtitles land on your words. Never uses AI voice (campaign rule).
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOOT = ROOT / "assets" / "footage"
CLI = ["node", "/root/.claude/plugins/cache/hyperframes/hyperframes/0.8.152/skills/hyperframes/scripts/plugin-cli.mjs"]


def speech_spans(path, n):
    """Return n (start, end) speech spans from silencedetect, or None if they don't match the script."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=noise=-35dB:d=0.35", "-f", "null", "-"],
                       capture_output=True, text=True)
    dur = float(re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr).group(3)) + \
        60 * float(re.search(r"Duration: (\d+):(\d+)", r.stderr).group(2))
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    spans, cur = [], 0.0
    for s, e in zip(starts, ends + [dur]):
        if s - cur > 0.25:
            spans.append((cur, s))
        cur = e
    if dur - cur > 0.25:
        spans.append((cur, dur))
    return spans if len(spans) == n else None


def main():
    cfg = json.loads((ROOT / "script.json").read_text())
    lines = cfg["lines"]
    voice = FOOT / cfg.get("voice", "")
    manual = all("at" in ln and "end" in ln for ln in lines)
    if manual:  # measured speech spans in script.json win over auto-splitting
        for i, ln in enumerate(lines):
            start = 0.0 if i == 0 else ln["at"]  # first visual is up before the first word
            nxt = lines[i + 1]["at"] if i + 1 < len(lines) else ln["end"] + 0.6
            ln["hold"] = round(nxt - start, 3)
        print("timed to voiceover (script.json at/end)")
    elif voice.is_file():
        spans = speech_spans(voice, len(lines))
        if spans:  # each line holds from its sentence start to the next sentence start
            for i, ln in enumerate(lines):
                nxt = spans[i + 1][0] if i + 1 < len(lines) else spans[i][1] + 0.6
                ln["at"], ln["hold"] = spans[i][0], round(nxt - spans[i][0], 3)
            print("timed to voiceover:", [round(s[0], 2) for s in spans])
        else:
            print(f"! voiceover pauses don't split into {len(lines)} sentences; using script.json holds")

    els, vis, js, t = [], [], [], 0.0
    for i, ln in enumerate(lines):
        d = ln["hold"]
        lid = f"l{i}"
        style = (f'object-position:{ln["pos"]};' if ln.get("pos") else "") + \
                (f'transform-origin:{ln["origin"]};' if ln.get("origin") else "")
        # all visuals live inside one static clipping box, so zooms never spill over the subtitles
        attrs = f'id="{lid}v" class="clip vis" data-start="{t:.3f}" data-duration="{d:.3f}" data-track-index="1" style="{style}"'
        if ln["clip"].endswith(".mp4"):
            vis.append(f'<video {attrs} src="assets/footage/{ln["clip"]}" data-media-start="{ln.get("start", 0):.3f}" muted playsinline></video>')
        else:
            vis.append(f'<img {attrs} src="assets/footage/{ln["clip"]}" alt="" />')
        js.append(f'tl.fromTo("#{lid}v", {{ scale: 1 }}, {{ scale: {ln.get("zoom", 1.06)}, duration: {d:.3f}, ease: "power1.inOut" }}, {t:.3f});')
        words = ln["say"].split()
        spans = "".join(f'<span class="w{" k" if w in ln.get("key", []) else ""}">{html.escape(w)}</span>' for w in words)
        els.append(f'<div id="{lid}s" class="clip sub" data-start="{t:.3f}" data-duration="{d:.3f}" data-track-index="3">{spans}</div>')
        # words land across the spoken span when we know it, else across the hold
        w0 = ln.get("at", t)
        span = (ln["end"] - w0) if "end" in ln else (d - 0.4)
        per = min(0.45, span / max(1, len(words)))
        js.append(f'tl.fromTo("#{lid}s .w", {{ opacity: 0.25, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.18, ease: "power2.out", stagger: {per:.3f} }}, {w0:.3f});')
        t += d
    total = round(t, 3)
    els.insert(0, '<div class="box">' + "".join(vis) + "</div>")
    els.append(f'<div id="title" class="clip title" data-start="0" data-duration="{total}" data-track-index="2">{html.escape(cfg["title"])}</div>')
    els.append(f'<div id="cta" class="clip cta" data-start="1.000" data-duration="{total - 1:.3f}" data-track-index="5">'
               f'<span class="pill">{html.escape(cfg["cta"])}</span></div>')
    js.append('tl.fromTo("#cta .pill", { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.3, ease: "back.out(2)" }, 1.0);')
    k = 4.0
    while k < total - 0.6:
        js.append(f'tl.fromTo("#cta .pill", {{ scale: 1 }}, {{ scale: 1.08, duration: 0.25, yoyo: true, repeat: 1, ease: "sine.inOut", immediateRender: false }}, {k:.3f});')
        k += 4.0
    if voice.is_file():
        els.append(f'<audio id="vo" src="assets/footage/{voice.name}" data-start="0" data-duration="{total}" data-track-index="6" data-volume="1"></audio>')
    music = FOOT / cfg.get("music", "")
    if music.is_file():
        vol = 0.18 if voice.is_file() else 0.7
        els.append(f'<audio id="music" src="assets/footage/{music.name}" data-start="0" data-duration="{total}" data-track-index="4" data-volume="{vol}"></audio>')

    (ROOT / "index.html").write_text(PAGE.replace("{{TOTAL}}", str(total)).replace("{{ELS}}", "\n      ".join(els))
                                     .replace("{{JS}}", "\n      ".join(js)))
    print(f"built {len(lines)} lines, {total}s", "(with voiceover)" if voice.is_file() else "(no voiceover yet: silent preview)")
    if "--render" in sys.argv:
        out = ROOT / "renders" / "faceless.mp4"
        r = subprocess.run(CLI + ["render", str(ROOT), "-o", str(out), "-q", "delivery"], capture_output=True, text=True)
        print("\n".join(l for l in r.stdout.splitlines() if "MB" in l or "rror" in l))
        share = out.with_name("faceless-share.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out), "-c:v", "libx264", "-crf", "22", "-preset", "slow",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(share)], check=True)
        print("share:", share)


PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Faceless UGC</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      @font-face { font-family: "Noto Color Emoji"; src: url("assets/fonts/NotoColorEmoji.ttf") format("truetype"); }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #0b0b0d; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #0b0b0d;
        font-family: "Montserrat", "Noto Color Emoji", sans-serif; }
      .title { position: absolute; left: 60px; right: 60px; top: 170px; text-align: center; color: #fff;
        font-size: 58px; font-weight: 800; line-height: 1.15; }
      .box { position: absolute; left: 30px; top: 430px; width: 1020px; height: 880px; overflow: hidden; border-radius: 28px; }
      .vis { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
      .sub { position: absolute; left: 70px; right: 70px; top: 1350px; text-align: center; color: #fff;
        font-size: 56px; font-weight: 800; line-height: 1.2; }
      .w { display: inline-block; margin: 0 0.12em; }
      .k { color: #ffcc33; }
      .cta { position: absolute; left: 50%; top: 360px; transform: translate(-50%, -50%); z-index: 10; }
      .pill { display: inline-block; padding: 12px 30px 10px; border-radius: 999px; background: #e3242b; color: #fff;
        font-size: 40px; font-weight: 700; white-space: nowrap; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.45); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{{TOTAL}}" data-width="1080" data-height="1920" data-fps="30">
      {{ELS}}
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
