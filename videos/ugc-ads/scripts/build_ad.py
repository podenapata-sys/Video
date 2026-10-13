#!/usr/bin/env python3
"""Build a photo-UGC Facebook ad from ads/<slug>/ad.json.

Usage:
  python3 scripts/build_ad.py <slug> [--render] [--sizes 9x16,4x5]

Inputs in ads/<slug>/:
  ad.json            beats: {"line": ..., "visual": "face" | "screen:<file>" | "proof:<quote>" | "cta"}
  face.jpg|png       creator photo (a placeholder is generated if missing)
  screens/           images referenced by "screen:" beats
  voice.m4a|mp3|wav  optional real voice recording (one take, pauses between lines);
                     otherwise each line is voiced with Kokoro TTS for exact timing.

Outputs: ads/<slug>/<size>/index.html (+ renders/<slug>-<size>.mp4 and -share.mp4).
"""
import html
import json
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "story-channel" / "scripts"))
from build_episode import CLI, tts, wav_duration  # noqa: E402  (reuse Kokoro + CLI helpers)
import hashlib  # noqa: E402

SIZES = {"9x16": (1080, 1920), "4x5": (1080, 1350)}
LEAD_IN, GAP = 0.15, 0.10
CTA_HOLD = 2.4
MIN_CAP_FONT = 54


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def placeholder_face(path):
    from PIL import Image, ImageDraw

    im = Image.new("RGB", (800, 800), (38, 46, 66))
    d = ImageDraw.Draw(im)
    d.ellipse([260, 150, 540, 450], fill=(120, 132, 158))
    d.ellipse([150, 470, 650, 950], fill=(120, 132, 158))
    d.text((300, 40), "YOUR PHOTO", fill=(230, 235, 245))
    im.save(path)


def voice_from_recording(ad_dir, rec, n):
    """Use the user's recording; split into n line segments at the n-1 longest pauses."""
    wav = ad_dir / "voice.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(rec), "-ac", "1", "-ar", "24000",
         "-af", "silenceremove=start_periods=1:start_threshold=-45dB", str(wav)])
    dur = wav_duration(wav)
    out = run(["ffmpeg", "-i", str(wav), "-af", "silencedetect=noise=-38dB:d=0.25", "-f", "null", "-"]).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]
    gaps = sorted(zip(starts, ends), key=lambda g: g[1] - g[0], reverse=True)[: n - 1]
    gaps = sorted(g for g in gaps if g[0] > 0.2)
    bounds = [0.0] + [g[1] for g in gaps] + [dur]
    if len(bounds) != n + 1:
        sys.exit(f"Found {len(bounds) - 1} spoken segments but ad has {n} lines; re-record with clear pauses.")
    lines = [{"start": LEAD_IN + bounds[i], "end": LEAD_IN + (gaps[i][0] if i < len(gaps) else dur)} for i in range(n)]
    return wav, lines, LEAD_IN + dur


def voice_from_tts(ad_dir, ad):
    vo = ad_dir / "vo"
    vo.mkdir(exist_ok=True)
    voice, speed = ad.get("voice", "am_michael"), float(ad.get("speed", 1.0))
    lines, t = [], LEAD_IN
    clips = []
    for b in ad["beats"]:
        key = hashlib.sha1(f"{voice}|{speed}|{b['line']}".encode()).hexdigest()[:12]
        clip = vo / f"line-{key}.wav"
        d = wav_duration(clip) if clip.exists() else tts(b["line"], voice, speed, clip)
        lines.append({"start": t, "end": t + d})
        clips.append(clip)
        t += d + GAP
    total = t
    with wave.open(str(clips[0])) as w0:
        rate, width = w0.getframerate(), w0.getsampwidth()
    wav = ad_dir / "voice-tts.wav"
    out = wave.open(str(wav), "wb")
    out.setnchannels(1), out.setsampwidth(width), out.setframerate(rate)
    written = 0
    for ln, clip in zip(lines, clips):
        pad = int(round(ln["start"] * rate)) - written
        out.writeframes(b"\x00" * max(0, pad) * width)
        written += max(0, pad)
        with wave.open(str(clip)) as w:
            out.writeframes(w.readframes(w.getnframes()))
            written += w.getnframes()
    out.close()
    return wav, lines, total


def word_spans(text, start, end, prefix):
    """Caption words with estimated per-word times (by character share of the line)."""
    words = text.split()
    total = sum(len(w) + 1 for w in words)
    acc, spans, tweens = 0, [], []
    for i, w in enumerate(words):
        t = start + (end - start) * acc / total
        acc += len(w) + 1
        spans.append(f'<span class="w" id="{prefix}-w{i}">{html.escape(w)}</span>')
        tweens.append(
            f'tl.fromTo("#{prefix}-w{i}", {{ color: "#ffffff", scale: 1 }}, '
            f'{{ color: "#ffd43b", scale: 1.08, duration: 0.08, immediateRender: false }}, {t:.3f});'
        )
        tweens.append(f'tl.to("#{prefix}-w{i}", {{ color: "#ffffff", scale: 1, duration: 0.1 }}, {t + 0.32:.3f});')
    return " ".join(spans), tweens


def build_size(ad_dir, ad, size, wav, lines, total):
    W, H = SIZES[size]
    out = ad_dir / size
    out.mkdir(exist_ok=True)
    (out / "assets").mkdir(exist_ok=True)
    shutil.copy(ROOT / "assets" / "gsap.min.js", out / "assets")
    shutil.copy(ROOT / "assets" / "logo.jpg", out / "assets")
    shutil.copy(wav, out / "voice.wav")
    face = next((p for p in (ad_dir / "face.jpg", ad_dir / "face.png") if p.exists()), None)
    shutil.copy(face, out / "assets" / ("face" + face.suffix))
    face_src = "assets/face" + face.suffix
    if (ad_dir / "screens").exists():
        shutil.copytree(ad_dir / "screens", out / "screens", dirs_exist_ok=True)
    for f in ("hyperframes.json", "package.json"):
        if (ROOT / f).exists():
            shutil.copy(ROOT / f, out / f)

    tall = H > 1500
    cap_top = int(H * (0.66 if tall else 0.70))
    cap_font = 66 if tall else MIN_CAP_FONT + 4
    els, js = [], []
    cta_start = None
    for i, (b, ln) in enumerate(zip(ad["beats"], lines)):
        s = 0.0 if i == 0 else ln["start"] - 0.05
        e = lines[i + 1]["start"] - 0.05 if i + 1 < len(lines) else total + CTA_HOLD
        d = e - s
        bid = f"b{i + 1:02d}"
        kind, _, arg = b["visual"].partition(":")
        if kind == "face":
            els.append(f'''      <div id="{bid}" class="clip beat" data-start="{s:.3f}" data-duration="{d:.3f}" data-track-index="1">
        <div class="face-big"><div class="ring"></div><img src="{face_src}" alt="" /></div>
      </div>''')
            js.append(f'tl.fromTo("#{bid} .face-big", {{ scale: 0.7, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2)" }}, {s:.3f});')
            js.append(f'tl.fromTo("#{bid} .face-big img", {{ scale: 1.0 }}, {{ scale: 1.08, duration: {d:.3f}, ease: "none" }}, {s:.3f});')
        elif kind == "screen":
            els.append(f'''      <div id="{bid}" class="clip beat" data-start="{s:.3f}" data-duration="{d:.3f}" data-track-index="1">
        <div class="screen-card"><img src="screens/{html.escape(arg)}" alt="" /></div>
        <div class="face-pip"><div class="ring"></div><img src="{face_src}" alt="" /></div>
      </div>''')
            js.append(f'tl.fromTo("#{bid} .screen-card", {{ y: 120, opacity: 0, rotation: -2 }}, {{ y: 0, opacity: 1, rotation: 0, duration: 0.4, ease: "expo.out" }}, {s:.3f});')
            js.append(f'tl.fromTo("#{bid} .screen-card img", {{ scale: 1.0 }}, {{ scale: 1.1, duration: {d:.3f}, ease: "none" }}, {s:.3f});')
        elif kind == "proof":
            els.append(f'''      <div id="{bid}" class="clip beat" data-start="{s:.3f}" data-duration="{d:.3f}" data-track-index="1">
        <div class="proof"><div class="stars">★★★★★</div><div class="quote">{html.escape(arg)}</div></div>
        <div class="face-pip"><div class="ring"></div><img src="{face_src}" alt="" /></div>
      </div>''')
            js.append(f'tl.fromTo("#{bid} .proof", {{ scale: 0.85, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.4, ease: "back.out(1.8)" }}, {s:.3f});')
        elif kind == "cta":
            cta_start = s
            c = ad["cta"]
            els.append(f'''      <div id="{bid}" class="clip beat cta" data-start="{s:.3f}" data-duration="{d:.3f}" data-track-index="1">
        <div class="cta-inner">
          <img class="logo" src="assets/logo.jpg" alt="" />
          <div class="cta-title">{html.escape(c["title"])}</div>
          <div class="cta-btn">{html.escape(c["button"])}</div>
          <div class="cta-note">{html.escape(c.get("note", ""))}</div>
          <div class="cta-site">{html.escape(ad.get("website", ""))}</div>
        </div>
      </div>''')
            js.append(f'tl.fromTo("#{bid} .cta-inner > *", {{ y: 50, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.35, stagger: 0.08, ease: "power3.out" }}, {s:.3f});')
            js.append(f'tl.to("#{bid} .cta-btn", {{ scale: 1.07, duration: 0.45, yoyo: true, repeat: 5, ease: "sine.inOut" }}, {s + 0.8:.3f});')
        # ring pulse = "speaking" indicator on any face element in this beat
        if kind != "cta":
                js.append(f'tl.fromTo("#{bid} .ring", {{ scale: 1, opacity: 0.9 }}, {{ scale: 1.12, opacity: 0.2, duration: 0.5, repeat: {max(0, int(d / 0.5) - 1)}, ease: "sine.out" }}, {s:.3f});')

        if kind != "cta":
            cid = f"c{i + 1:02d}"
            spans, tw = word_spans(b["line"], ln["start"], ln["end"], cid)
            els.append(f'      <div id="{cid}" class="clip cap" data-start="{s:.3f}" data-duration="{d:.3f}" data-track-index="3"><div class="ct">{spans}</div></div>')
            js.append(f'tl.fromTo("#{cid} .ct", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.2, ease: "power2.out" }}, {s:.3f});')
            js.extend(tw)

    dur = round(total + CTA_HOLD, 3)
    page = PAGE.format(W=W, H=H, dur=dur, cap_top=cap_top, cap_font=cap_font,
                       face_big=int(W * (0.56 if tall else 0.44)), face_top=int(H * (0.16 if tall else 0.12)),
                       card_top=int(H * (0.10 if tall else 0.07)), card_h=int(H * (0.52 if tall else 0.58)),
                       pip=int(W * 0.24), pip_top=cap_top - int(W * 0.24) - 30,
                       els="\n".join(els), js="\n      ".join(js), title=html.escape(ad.get("name", "ad")))
    (out / "index.html").write_text(page)
    return out, dur


PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>{title}</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: #0c1020; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Montserrat", sans-serif;
        background: radial-gradient(circle at 50% 30%, #1b2f6b 0%, #0c1020 62%); }}
      .beat {{ position: absolute; inset: 0; }}
      .face-big {{ position: absolute; left: 50%; top: {face_top}px; width: {face_big}px; height: {face_big}px; margin-left: calc({face_big}px / -2); }}
      .face-big img, .face-pip img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; border-radius: 50%; border: 8px solid #ffffff; }}
      .ring {{ position: absolute; inset: -18px; border-radius: 50%; border: 8px solid #1e6bff; }}
      .screen-card {{ position: absolute; left: 7%; right: 7%; top: {card_top}px; height: {card_h}px; border-radius: 40px; overflow: hidden;
        border: 6px solid #ffffff; box-shadow: 0 30px 70px rgba(0,0,0,0.5); background: #f2f5fb; }}
      .screen-card img {{ width: 100%; height: 100%; object-fit: cover; object-position: top; display: block; }}
      .face-pip {{ position: absolute; left: 6%; top: {pip_top}px; width: {pip}px; height: {pip}px; }}
      .proof {{ position: absolute; left: 8%; right: 8%; top: {card_top}px; padding: 60px 56px; border-radius: 40px; background: #ffffff; }}
      .proof .stars {{ font-size: 64px; color: #f5a400; letter-spacing: 8px; }}
      .proof .quote {{ margin-top: 24px; font-size: 52px; font-weight: 800; line-height: 1.25; color: #15171c; }}
      .cap {{ position: absolute; left: 60px; right: 60px; top: {cap_top}px; display: flex; justify-content: center; z-index: 10; }}
      .ct {{ max-width: 960px; text-align: center; font-size: {cap_font}px; font-weight: 900; line-height: 1.18; color: #fff;
        text-shadow: 0 4px 0 #000, 0 0 14px rgba(0,0,0,0.9); }}
      .w {{ display: inline-block; }}
      .cta {{ background: #f2f5fb; }}
      .cta-inner {{ position: absolute; inset: 0; padding: 8% 8% 18%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 34px; text-align: center; }}
      .cta-inner .logo {{ width: 300px; height: 300px; border-radius: 40px; object-fit: cover; display: block; }}
      .cta-title {{ font-size: 76px; font-weight: 900; color: #15171c; line-height: 1.08; letter-spacing: -0.02em; }}
      .cta-btn {{ background: #0b3fd6; color: #fff; font-size: 60px; font-weight: 900; padding: 34px 90px; border-radius: 999px; }}
      .cta-note {{ font-size: 36px; font-weight: 700; color: #4a5160; }}
      .cta-site {{ font-size: 34px; font-weight: 800; color: #0b45d9; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="{W}" data-height="{H}">
{els}
      <audio id="vo" src="voice.wav" data-start="0" data-duration="{dur}" data-track-index="4" data-volume="1"></audio>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {js}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    slug = sys.argv[1]
    sizes = ["9x16", "4x5"]
    if "--sizes" in sys.argv:
        sizes = sys.argv[sys.argv.index("--sizes") + 1].split(",")
    ad_dir = ROOT / "ads" / slug
    ad = json.loads((ad_dir / "ad.json").read_text())
    if any("[" in b["line"] or "[" in b["visual"] for b in ad["beats"]):
        sys.exit("ad.json still has [PLACEHOLDER] text; fill in real details first.")
    if not any((ad_dir / f).exists() for f in ("face.jpg", "face.png")):
        placeholder_face(ad_dir / "face.png")
        print("No face photo found; using a placeholder (add ads/%s/face.jpg)." % slug)

    rec = next((p for p in ad_dir.glob("voice.*") if p.suffix in (".m4a", ".mp3", ".wav", ".ogg", ".aac")
                and p.name != "voice-tts.wav"), None)
    if rec:
        wav, lines, total = voice_from_recording(ad_dir, rec, len(ad["beats"]))
        print(f"Using recorded voice {rec.name}")
    else:
        wav, lines, total = voice_from_tts(ad_dir, ad)

    for size in sizes:
        out, dur = build_size(ad_dir, ad, size, wav, lines, total)
        print(f"Built {out / 'index.html'} ({dur:.1f}s)")
        if "--render" in sys.argv:
            chk = run(CLI + ["check", str(out)])
            print("\n".join(l for l in chk.stdout.splitlines() if "Check" in l or "✗" in l))
            if "Check passed" not in chk.stdout:
                sys.exit("check failed; not rendering")
            rd = ad_dir / "renders"
            rd.mkdir(exist_ok=True)
            mp4 = rd / f"{slug}-{size}.mp4"
            r = run(CLI + ["render", str(out), "-o", str(mp4)])
            print("\n".join(l for l in r.stdout.splitlines() if "MB" in l or "rror" in l))
            share = rd / f"{slug}-{size}-share.mp4"
            run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-c:v", "libx264", "-crf", "23", "-preset", "slow",
                 "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(share)])
            print(f"Share copy: {share} ({share.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
