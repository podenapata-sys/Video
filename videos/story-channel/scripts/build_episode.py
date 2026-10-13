#!/usr/bin/env python3
"""Build a cartoon-story Reel from episodes/<slug>/story.json + images/.

Usage:
  python3 scripts/build_episode.py <slug> [--render] [--placeholders]

Steps: per-line TTS (Kokoro via the HyperFrames CLI) -> stitched voiceover with
exact line timings -> HyperFrames index.html (Ken Burns shots, synced serif
captions, grain + vignette, end card) -> optional `hyperframes check` + render.

TTS clips are cached by text/voice/speed, so re-running only regenerates lines
that changed.
"""
import hashlib
import html
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ["node", "/root/.claude/plugins/cache/hyperframes/hyperframes/0.8.152/skills/hyperframes/scripts/plugin-cli.mjs"]

W, H = 1080, 1920
LEAD_IN = 0.25      # silence before the first line
GAP_LINE = 0.12     # pause between lines inside one shot
GAP_SHOT = 0.30     # pause between shots
END_CARD = 2.6      # seconds of SUBSCRIBE card after the last line
KB_MOVES = ["zoom-in", "pan-left", "zoom-out", "pan-up", "pan-right", "zoom-in"]


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def tts(text, voice, speed, out):
    """Generate one line with Kokoro; return duration in seconds."""
    r = run(CLI + ["tts", text, "-v", voice, "-s", str(speed), "-o", str(out), "--json"])
    for line in reversed(r.stdout.strip().splitlines()):
        if line.startswith("{"):
            data = json.loads(line)
            if not data.get("ok"):
                sys.exit(f"TTS failed for {text!r}: {data.get('error')}")
            return float(data["durationSeconds"])
    sys.exit(f"TTS gave no JSON for {text!r}:\n{r.stdout}\n{r.stderr}")


def wav_duration(path):
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def make_placeholders(ep, story):
    from PIL import Image, ImageDraw

    img_dir = ep / "images"
    img_dir.mkdir(exist_ok=True)
    palette = [(46, 36, 28), (28, 32, 44), (52, 30, 30), (30, 42, 34)]
    for i, shot in enumerate(story["shots"]):
        p = img_dir / shot["image"]
        if p.exists():
            continue
        im = Image.new("RGB", (W, H), palette[i % len(palette)])
        d = ImageDraw.Draw(im)
        for r in range(0, 900, 6):  # soft radial glow
            c = tuple(min(255, v + int(60 * (1 - r / 900))) for v in palette[i % len(palette)])
            d.ellipse([W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r], outline=c, width=6)
        d.text((80, 120), f"SHOT {i + 1:02d}\n{shot['image']}", fill=(235, 225, 205))
        im.save(p)


def build(slug, do_render=False, placeholders=False):
    ep = ROOT / "episodes" / slug
    story = json.loads((ep / "story.json").read_text())
    voice = story.get("voice", "am_michael")
    speed = float(story.get("speed", 1.0))
    if placeholders:
        make_placeholders(ep, story)

    missing = [s["image"] for s in story["shots"] if not (ep / "images" / s["image"]).exists()]
    if missing:
        sys.exit(f"Missing images in {ep / 'images'}: {', '.join(missing)}")

    # ---- 1. per-line TTS (cached) ----
    vo_dir = ep / "vo"
    vo_dir.mkdir(exist_ok=True)
    lines = []
    for si, shot in enumerate(story["shots"]):
        for text in shot["lines"]:
            spoken = text
            key = hashlib.sha1(f"{voice}|{speed}|{spoken}".encode()).hexdigest()[:12]
            clip = vo_dir / f"line-{key}.wav"
            if clip.exists():
                dur = wav_duration(clip)
            else:
                dur = tts(spoken, voice, speed, clip)
                print(f"  tts {dur:5.2f}s  {text}")
            lines.append({"shot": si, "text": text, "clip": clip, "dur": dur})

    # ---- 2. timeline ----
    t = LEAD_IN
    shots = [{"start": None, "end": None} for _ in story["shots"]]
    for i, ln in enumerate(lines):
        sh = shots[ln["shot"]]
        if sh["start"] is None:
            sh["start"] = 0.0 if ln["shot"] == 0 else t
        ln["start"] = t
        ln["end"] = t + ln["dur"]
        nxt = lines[i + 1] if i + 1 < len(lines) else None
        t = ln["end"] + (GAP_SHOT if nxt is None or nxt["shot"] != ln["shot"] else GAP_LINE)
    for si, sh in enumerate(shots):
        sh["end"] = shots[si + 1]["start"] if si + 1 < len(shots) else t
    end_start = shots[-1]["end"]
    total = round(end_start + END_CARD, 3)

    # ---- 3. stitch voiceover.wav ----
    rate = 24000
    with wave.open(str(lines[0]["clip"])) as w0:
        rate, width, chans = w0.getframerate(), w0.getsampwidth(), w0.getnchannels()
    out = wave.open(str(ep / "voiceover.wav"), "wb")
    out.setnchannels(chans)
    out.setsampwidth(width)
    out.setframerate(rate)
    written = 0
    for ln in lines:
        pad = int(round(ln["start"] * rate)) - written
        if pad > 0:
            out.writeframes(b"\x00" * pad * width * chans)
            written += pad
        with wave.open(str(ln["clip"])) as w:
            frames = w.readframes(w.getnframes())
            out.writeframes(frames)
            written += w.getnframes()
    tail = int(round(total * rate)) - written
    if tail > 0:
        out.writeframes(b"\x00" * tail * width * chans)
    out.close()

    # ---- 4. assets ----
    (ep / "assets").mkdir(exist_ok=True)
    shutil.copy(ROOT / "assets" / "gsap.min.js", ep / "assets" / "gsap.min.js")
    has_music = (ep / "music.mp3").exists()

    # ---- 5. index.html ----
    shot_html, cap_html, js = [], [], []
    for si, (shot, sh) in enumerate(zip(story["shots"], shots)):
        dur = sh["end"] - sh["start"]
        sid = f"shot-{si + 1:02d}"
        shot_html.append(
            f'      <div id="{sid}" class="clip shot" data-start="{sh["start"]:.3f}" '
            f'data-duration="{dur:.3f}" data-track-index="1">\n'
            f'        <div class="kb"><img src="images/{html.escape(shot["image"])}" alt="" /></div>\n'
            f"      </div>"
        )
        move = shot.get("move") or KB_MOVES[si % len(KB_MOVES)]
        frm, to = {
            "zoom-in": ("{ scale: 1.0 }", "{ scale: 1.14"),
            "zoom-out": ("{ scale: 1.16 }", "{ scale: 1.02"),
            "pan-left": ("{ scale: 1.14, xPercent: 3 }", "{ scale: 1.14, xPercent: -3"),
            "pan-right": ("{ scale: 1.14, xPercent: -3 }", "{ scale: 1.14, xPercent: 3"),
            "pan-up": ("{ scale: 1.14, yPercent: 2.5 }", "{ scale: 1.14, yPercent: -2.5"),
        }[move]
        js.append(f'      tl.fromTo("#{sid} .kb", {frm}, {to}, duration: {dur:.3f}, ease: "none" }}, {sh["start"]:.3f});')

    for li, ln in enumerate(lines):
        cid = f"cap-{li + 1:03d}"
        nxt_start = lines[li + 1]["start"] if li + 1 < len(lines) else end_start
        cdur = max(0.3, nxt_start - ln["start"] - 0.04)
        cap_html.append(
            f'      <div id="{cid}" class="clip cap" data-start="{ln["start"]:.3f}" '
            f'data-duration="{cdur:.3f}" data-track-index="3"><span class="ct">{html.escape(ln["text"])}</span></div>'
        )
        js.append(
            f'      tl.fromTo("#{cid} .ct", {{ opacity: 0, y: 14 }}, '
            f'{{ opacity: 1, y: 0, duration: 0.18, ease: "power2.out" }}, {ln["start"]:.3f});'
        )

    channel = html.escape(story.get("channel", "Your Channel"))
    music = (
        f'      <audio id="music" src="music.mp3" data-start="0" data-duration="{total}" '
        f'data-track-index="5" data-volume="0.12"></audio>\n'
        if has_music
        else ""
    )
    page = TEMPLATE.format(
        title=html.escape(story.get("title", slug)),
        total=total,
        shots="\n".join(shot_html),
        caps="\n".join(cap_html),
        end_start=f"{end_start:.3f}",
        end_dur=f"{END_CARD:.3f}",
        channel=channel,
        music=music,
        js="\n".join(js),
    )
    (ep / "index.html").write_text(page)
    for f in ("hyperframes.json", "package.json"):
        if (ROOT / f).exists() and not (ep / f).exists():
            shutil.copy(ROOT / f, ep / f)

    timing = [{"text": l["text"], "start": round(l["start"], 3), "end": round(l["end"], 3)} for l in lines]
    (ep / "timing.json").write_text(json.dumps({"total": total, "lines": timing}, indent=2))
    print(f"Built {ep / 'index.html'}  ({len(shots)} shots, {len(lines)} lines, {total:.1f}s)")

    if do_render:
        chk = run(CLI + ["check", str(ep)])
        tail_out = "\n".join(l for l in chk.stdout.splitlines() if "Check" in l or "✗" in l)
        print(tail_out)
        if "Check passed" not in chk.stdout:
            sys.exit("check failed; not rendering")
        (ep / "renders").mkdir(exist_ok=True)
        r = run(CLI + ["render", str(ep), "-o", str(ep / "renders" / f"{slug}.mp4")])
        print("\n".join(l for l in r.stdout.splitlines() if "MB" in l or "rror" in l))
        # Grain makes the master huge; make a compressed copy for uploading/sharing.
        master = ep / "renders" / f"{slug}.mp4"
        share = ep / "renders" / f"{slug}-share.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-i", str(master), "-c:v", "libx264", "-crf", "24",
             "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
             "-movflags", "+faststart", str(share)])
        print(f"Share copy: {share} ({share.stat().st_size / 1e6:.1f} MB)")


TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>{title}</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #0d0b09; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #0d0b09; font-family: "EB Garamond", serif; }}
      .shot {{ position: absolute; inset: 0; overflow: hidden; }}
      .kb {{ width: 100%; height: 100%; }}
      .kb img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
      .cap {{ position: absolute; left: 90px; right: 90px; top: 1330px; display: flex; justify-content: center; z-index: 120; }}
      .ct {{
        display: block; max-width: 900px; text-align: center; color: #fbf6ec;
        font-size: 58px; font-weight: 700; line-height: 1.18;
        text-shadow: 0 0 18px rgba(0,0,0,0.95), 0 3px 6px rgba(0,0,0,0.95), 0 0 3px #000;
      }}
      #endcard {{ position: absolute; inset: 0; background: #0d0b09; display: flex; flex-direction: column;
        align-items: center; justify-content: center; gap: 30px; z-index: 110; }}
      #endcard .sub {{ font-size: 110px; font-weight: 700; letter-spacing: 0.08em; color: #fbf6ec; }}
      #endcard .ch {{ font-size: 44px; color: #d8c7a4; letter-spacing: 0.04em; }}
      #endcard .rule {{ width: 420px; height: 4px; background: #d8c7a4; }}
      @keyframes hf-grain-noise {{
        0%, 100% {{ transform: translate(0, 0); }} 10% {{ transform: translate(-5%, -5%); }}
        20% {{ transform: translate(-10%, 5%); }} 30% {{ transform: translate(5%, -10%); }}
        40% {{ transform: translate(-5%, 15%); }} 50% {{ transform: translate(-10%, 5%); }}
        60% {{ transform: translate(15%, 0); }} 70% {{ transform: translate(0, 10%); }}
        80% {{ transform: translate(-15%, 0); }} 90% {{ transform: translate(10%, 5%); }}
      }}
      #grain-overlay {{ position: absolute; inset: 0; pointer-events: none; z-index: 100; overflow: hidden; }}
      #grain-overlay .grain-texture {{
        position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
        background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
        opacity: 0.12; animation: hf-grain-noise 0.5s steps(1) infinite;
      }}
      #hf-vignette {{ position: absolute; inset: 0; pointer-events: none; z-index: 90;
        background: radial-gradient(ellipse at center, transparent 50%, rgba(0, 0, 0, 0.62) 100%); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
{shots}
      <div id="hf-vignette"></div>
      <div id="grain-overlay"><div class="grain-texture"></div></div>
{caps}
      <div id="endcard" class="clip" data-start="{end_start}" data-duration="{end_dur}" data-track-index="2">
        <div class="sub">SUBSCRIBE</div>
        <div class="rule"></div>
        <div class="ch">{channel}</div>
      </div>
      <audio id="vo" src="voiceover.wav" data-start="0" data-duration="{total}" data-track-index="4" data-volume="1"></audio>
{music}    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
{js}
      tl.fromTo("#endcard .sub", {{ opacity: 0, scale: 0.9 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "power2.out" }}, {end_start});
      tl.fromTo("#endcard .rule", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.5, ease: "power2.out" }}, {end_start} + 0.25);
      tl.fromTo("#endcard .ch", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, {end_start} + 0.45);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    build(sys.argv[1], do_render="--render" in sys.argv, placeholders="--placeholders" in sys.argv)
