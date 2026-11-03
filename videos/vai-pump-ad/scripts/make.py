#!/usr/bin/env python3
"""Vai Online 12V water-pump Reel -> out/final_ad_1440x2560.mp4 + out/subtitles.srt (ffmpeg + Pillow only).

  python3 scripts/make.py            (run from videos/vai-pump-ad/)

Inputs are copies in src/ (the uploads are never touched):
  src/clip1.mp4       problem -> SaHa GoLD / JesMin -> line-up + battery (10.03 s, 720x1280, 24 fps); 0-10 s used
  src/clip2.mp4       coil cut-aways -> garden / tank -> caps -> line-up (10.03 s); its first 7.2 s used
  src/end_card.webp   the end-card poster (1125x2000)
  src/vo/NN_name.mp3  voice lines; 09_cta.mp3 is optional until it arrives
There is no music.mp3, so the bed is the clips' own audio at -20 dB, ducked under the voice.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "src", ROOT / "out"
WORK = OUT / "work"
W, H, FPS, SR = 1440, 2560, 30, 48000
CLIP1, CLIP2, CARD = 10.0, 7.2, 5.0
CARD_AT = CLIP1 + CLIP2  # 17.2
NORM = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=white,setsar=1"

LINES = [("01_hook", 0.0), ("02_problem", 1.5), ("03_solution", 2.8), ("04_models", 3.8), ("05_copper", 10.0),
         ("06_silver", 11.5), ("07_uses", 13.0), ("08_caps", 15.0), ("09_cta", 17.5)]
GAP, TAIL = 0.10, 0.4

# Subtitle block centres, chosen from extracted frames:
# clips: y 640 (25%), the empty sky / rooftop band above the pumps (tops ~37-42%); the lower half is taken by the
#   pump bodies, labels and the 12V battery (to ~87%).
# end card: y 502 (19.6%), the empty grey band between the offer banner (ends ~429) and the logo/title row
#   (starts ~576); every end-card line fits on one line. A line whose midpoint falls on the card uses it.
CLIP_Y, CARD_Y = 640, 502
FONT_PX, STROKE, MAXW = 62, 6, int(W * 0.86)

TEXTS = [
    "ক্ষেতে বা বাগানে পানি তুলতে হাঁপিয়ে গেছেন?",
    "সময় আর শ্রম, দুটোই শেষ!",
    "সমাধান, ১২ ভোল্টের ব্যাটারি চালিত জল পাম্প!",
    "সাহা গোল্ড আর জেসমিন, দুই ব্র্যান্ড, এক ইঞ্চি আর দুই ইঞ্চি।",
    "সাহা গোল্ডে তামার কয়েল,",
    "জেসমিনে সিলভার কয়েল।",
    "কৃষি, বাগান, সবখানে কাজের।",
    "দুই ইঞ্চি মডেলে তিনটি ক্যাপ একদম ফ্রি!",
    "সারা দেশে কুরিয়ার, এখনই হোয়াটসঅ্যাপ করুন!",
]


def run(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True, check=True).stdout)


def frames(t):
    return round(t * FPS) / FPS


def voice():
    """Trim leading silence, read durations, resolve overlaps; returns [(name, start, end, wav)]."""
    placed, prev_end = [], None
    for name, want in LINES:
        src = SRC / "vo" / f"{name}.mp3"
        if not src.exists():
            print(f"  {name}: not supplied yet, skipped")
            continue
        wav = WORK / f"{name}.wav"
        run("-i", str(src), "-af", "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02",
            "-ar", str(SR), "-ac", "1", str(wav))
        d = dur(wav)
        start = want if prev_end is None or want >= prev_end + GAP else prev_end + GAP
        start = round(start, 3)
        placed.append((name, start, round(start + d, 3), wav, want))
        prev_end = start + d
    print(f"  {'line':12} {'wanted':>7} {'start':>7} {'end':>7} {'len':>6}")
    for name, s, e, _, want in placed:
        print(f"  {name:12} {want:7.2f} {s:7.3f} {e:7.3f} {e - s:6.3f}{'  (delayed)' if s > want else ''}")
    return placed


def video(total):
    """clip1 | clip2 | end card (frozen-extended to the voice), all 1440x2560 30 fps; plus the -20 dB bed."""
    card = total - CARD_AT
    c1 = SRC / "clip1.mp4"
    parts = [f"[0:v]trim=0:{CLIP1},setpts=PTS-STARTPTS,fps={FPS},{NORM},tpad=stop_mode=clone:stop_duration=1,"
             f"trim=0:{CLIP1},setpts=PTS-STARTPTS[v0]",
             f"[0:a]atrim=0:{CLIP1},asetpts=PTS-STARTPTS,apad=whole_dur={CLIP1}[a0]"]
    vs, as_ = ["[v0]"], ["[a0]"]
    # clip2: the first 7.2 s of src/clip2.mp4 (coil cut-aways -> garden/tank -> caps), as specified
    parts.append(f"[2:v]trim=0:{CLIP2},setpts=PTS-STARTPTS,fps={FPS},{NORM},trim=0:{CLIP2},setpts=PTS-STARTPTS[v1]")
    parts.append(f"[2:a]atrim=0:{CLIP2},asetpts=PTS-STARTPTS,apad=whole_dur={CLIP2}[a1]")
    vs.append("[v1]")
    as_.append("[a1]")
    n = len(vs)
    z = f"(1+0.02*min(t,{CARD})/{CARD})"  # 5 s push-in, then a frozen hold
    parts.append(f"[1:v]{NORM},fps={FPS},scale=w='trunc({W}*{z}/2)*2':h='trunc({H}*{z}/2)*2':eval=frame,"
                 f"crop={W}:{H},trim=0:{card:.4f},setpts=PTS-STARTPTS[vc]")
    parts.append(f"anullsrc=r={SR}:cl=stereo,atrim=0:{card:.4f}[ac]")
    parts.append(f"{''.join(vs)}[vc]concat=n={n + 1}:v=1:a=0,format=yuv420p[v]")
    # bed: original clip audio at -20 dB; short fade into the silent end card
    parts.append(f"{''.join(as_)}concat=n={n}:v=0:a=1,aresample={SR},volume=-20dB,"
                 f"afade=t=out:st={CARD_AT - 0.4}:d=0.4[ab];[ab][ac]concat=n=2:v=0:a=1[bed]")
    run("-i", str(c1), "-loop", "1", "-framerate", str(FPS), "-t", f"{card + 0.5:.3f}", "-i", str(SRC / "end_card.webp"),
        "-i", str(SRC / "clip2.mp4"), "-filter_complex", ";".join(parts), "-map", "[v]", "-c:v", "libx264", "-crf", "14", "-preset", "fast",
        "-pix_fmt", "yuv420p", "-r", str(FPS), "-t", f"{total:.4f}", str(WORK / "video.mp4"),
        "-map", "[bed]", "-ar", str(SR), "-ac", "2", "-t", f"{total:.4f}", str(WORK / "bed.wav"))


def audio(placed, total):
    """Voice at 0 dB over the ducked bed, fades, two-pass loudnorm to -14 LUFS / -1 dBTP."""
    ins, parts = ["-i", str(WORK / "bed.wav")], []
    for i, (name, s, e, wav, _) in enumerate(placed, 1):
        ins += ["-i", str(wav)]
        d = e - s
        ms = int(round(s * 1000))
        parts.append(f"[{i}:a]afade=t=in:d=0.005,afade=t=out:st={d - 0.005:.3f}:d=0.005,"
                     f"adelay={ms}:all=1,pan=stereo|c0=c0|c1=c0[l{i}]")
    k = len(placed)
    parts.append(f"{''.join(f'[l{i}]' for i in range(1, k + 1))}amix=inputs={k}:normalize=0:duration=longest,"
                 f"apad=whole_dur={total:.4f},atrim=0:{total:.4f},asplit=2[vox][key]")
    # ~12 dB of gain reduction on the bed while the voice is on
    parts.append("[0:a][key]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=300:makeup=1[duck]")
    parts.append(f"[vox][duck]amix=inputs=2:normalize=0:duration=first,afade=t=in:d=0.3,"
                 f"afade=t=out:st={total - 0.7:.4f}:d=0.7[mix]")
    pre = WORK / "mix_pre.wav"
    run(*ins, "-filter_complex", ";".join(parts), "-map", "[mix]", "-ar", str(SR), "-ac", "2", "-c:a", "pcm_f32le", str(pre))
    n = int(round(total * SR))
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pre), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                           "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    norm = (f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
            f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    # TP -1.5 in loudnorm leaves headroom for the AAC encode to stay under -1 dBTP; apad instead of -t (no cut)
    run("-i", str(pre), "-af", f"{norm},aresample={SR},apad=whole_len={n},atrim=end_sample={n}",
        "-ar", str(SR), "-ac", "2", str(WORK / "mix.wav"))


def ts(t, sep):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}" if sep == "." else f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}"


def cues(placed):
    out = []
    for j, (name, s, e, _, _) in enumerate(placed):
        end = e + 0.15
        if j + 1 < len(placed):
            end = min(end, placed[j + 1][1] - 0.02)
        out.append((int(name[:2]) - 1, s, round(end, 3)))
    return out


def wrap(text, font):
    """At most 2 lines within 86% width; breaks only at a space (text itself unchanged), nearest the middle."""
    if font.getlength(text) <= MAXW:
        return [text]
    sp = [k for k, ch in enumerate(text) if ch == " "]
    fits = lambda k: max(font.getlength(text[:k]), font.getlength(text[k + 1:])) <= MAXW
    commas = [k for k in sp if text[k - 1] == "," and fits(k)]  # keep phrases whole where possible
    k = min(commas or sp, key=lambda k: max(font.getlength(text[:k]), font.getlength(text[k + 1:])))
    return [text[:k], text[k + 1:]]


def sub_png(text, path):
    """White Noto Sans Bengali Bold, 6 px black outline, soft drop shadow; shaped with Pillow RAQM (libass
    dropped the conjuncts, e.g. ক্ষ rendered as ক + ষ, so it is not used)."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    font = ImageFont.truetype(str(ROOT / "fonts" / "NotoSansBengali-Bold.ttf"), FONT_PX, layout_engine=ImageFont.Layout.RAQM)
    rows = wrap(text, font)
    lh = int(FONT_PX * 1.55)
    pad = 30
    bw = int(max(font.getlength(r) for r in rows)) + 2 * (STROKE + pad)
    bh = lh * len(rows) + 2 * pad
    bw += bw % 2
    bh += bh % 2
    def draw(fill, stroke_fill, dy):
        im = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for n, r in enumerate(rows):
            d.text((bw / 2, pad + lh * (n + 0.5) + dy), r, font=font, anchor="mm", fill=fill,
                   stroke_width=STROKE, stroke_fill=stroke_fill)
        return im
    shadow = draw((0, 0, 0, 150), (0, 0, 0, 150), 5).filter(ImageFilter.GaussianBlur(7))
    out = Image.alpha_composite(shadow, draw((255, 255, 255, 255), (0, 0, 0, 255), 0))
    out.save(path)
    return bw, bh, len(rows)


def subtitles(placed):
    lines = (ROOT / "scripts" / "subs.txt").read_text(encoding="utf-8").splitlines()
    assert lines == TEXTS, "subtitle text differs from the spec"
    cs = cues(placed)
    srt = [f"{k}\n{ts(s, ',')} --> {ts(e, ',')}\n{TEXTS[i]}\n" for k, (i, s, e) in enumerate(cs, 1)]
    (OUT / "subtitles.srt").write_text("\n".join(srt), encoding="utf-8")
    subs = []
    for i, s, e in cs:
        png = WORK / f"sub{i + 1:02d}.png"
        bw, bh, nrows = sub_png(TEXTS[i], png)
        cy = CARD_Y if (s + e) / 2 >= CARD_AT else CLIP_Y
        subs.append((png, s, e, (W - bw) // 2, cy - bh // 2))
        print(f"  sub {i + 1:02d} {s:6.3f}-{e:6.3f}  {nrows} line(s)  centre y {cy} ({cy / H:.1%})")
    return subs


def encode(total, subs):
    ins, parts, last = ["-i", str(WORK / "video.mp4"), "-i", str(WORK / "mix.wav")], [], "[0:v]"
    for k, (png, s, e, x, y) in enumerate(subs):
        d = e - s
        ins += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", str(png)]
        parts.append(f"[{k + 2}:v]format=rgba,fade=t=in:st=0:d=0.1:alpha=1,fade=t=out:st={d - 0.1:.3f}:d=0.1:alpha=1,"
                     f"setpts=PTS-STARTPTS+{s:.3f}/TB[s{k}]")
        parts.append(f"{last}[s{k}]overlay=x={x}:y={y}:eof_action=pass:enable='between(t,{s:.3f},{e:.3f})'[o{k}]")
        last = f"[o{k}]"
    parts.append(f"{last}format=yuv420p[v]")
    run(*ins, "-filter_complex", ";".join(parts), "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-crf", "18",
        "-preset", "slow", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
        "-t", f"{total:.4f}", "-movflags", "+faststart", str(OUT / "final_ad_1440x2560.mp4"))


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    print("voice placement:")
    placed = voice()
    total = frames(max(CLIP1 + CLIP2 + CARD, placed[-1][2] + TAIL))
    print(f"total {total:.3f} s (end card {total - CARD_AT:.2f} s{', frozen-extended' if total > 22.2 else ''})")
    subs = subtitles(placed)
    if "--subs-only" in sys.argv:
        return
    video(total)
    audio(placed, total)
    encode(total, subs)
    print("wrote", OUT / "final_ad_1440x2560.mp4")


if __name__ == "__main__":
    main()
