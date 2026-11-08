#!/usr/bin/env python3
"""Music bed (3 parts aligned to scenes), impact SFX, clip ambience and the final -14 LUFS mix -> assets/mix.wav.

  python3 scripts/music.py        (after voice.py and words.py)

- bgm1: its impact hit (measured onset 8.47 s) lands exactly on Scene 2's first frame. bgm1 fades out by ~21 s, so
  its post-hit pad (10-19 s) is looped once (crossfaded) under Scene 3 instead of leaving the worry scene silent.
- bgm2: starts 1 s before Scene 4, 1 s crossfade from bgm1.
- bgm3: its final hit (strongest onset 21.25 s; the brief said ~0:20) lands on the WhatsApp pill's first pulse. That
  fixes bgm3's start; bgm2 -> bgm3 still crossfades over the 1 s before Scene 7 (bgm3's intro runs quietly under bgm2).
- music ducks under the voice (sidechain, ~-18 dB under speech) and rises in the gaps; it ends on bgm3's own tail.
- impact SFX (synthesised: none was supplied) on Scene 2's first frame; clip ambience at -22 dB for unmuted clips.
Writes assets/sfx/impact.wav, assets/music/bed.wav, assets/ambience.wav, assets/mix.wav and music.json.
"""
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "assets"
SR, FPS = 48000, 30
HIT1, HIT3 = 8.47, 21.25
PILL_BOUNCE = 0.45   # pill bounce-in length; its first pulse peaks right after (build.py uses the same numbers)
PULSE_PEAK = 0.15


def dec(path, rate=1.0):
    af = []
    t = rate
    while t < 0.5:
        af.append("atempo=0.5")
        t /= 0.5
    if rate != 1.0:
        af.append(f"atempo={t:.5f}")
    cmd = ["ffmpeg", "-v", "error", "-i", str(path)] + (["-af", ",".join(af)] if af else []) + ["-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()


def fade(x, fin=0.0, fout=0.0):
    x = x.copy()
    if fin:
        n = min(len(x), int(fin * SR))
        x[:n] *= np.sin(np.linspace(0, np.pi / 2, n))[:, None]
    if fout:
        n = min(len(x), int(fout * SR))
        x[-n:] *= np.cos(np.linspace(0, np.pi / 2, n))[:, None]
    return x


def place(bus, x, t, gain=1.0):
    o = int(round(t * SR))
    if o < 0:
        x, o = x[-o:], 0
    n = min(len(x), len(bus) - o)
    if n > 0:
        bus[o:o + n] += x[:n] * gain


def impact():
    """Short cinematic hit: sub drop + filtered noise burst + transient click, ~1.6 s tail."""
    n = int(1.8 * SR)
    t = np.arange(n) / SR
    f = 62 * np.exp(-t * 2.2) + 34
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6)
    rng = np.random.default_rng(7)
    noise = rng.standard_normal(n)
    k = np.exp(-np.arange(int(0.004 * SR)) / (0.0008 * SR))
    burst = np.convolve(noise, k / k.sum(), "same") * np.exp(-t * 9)
    click = np.zeros(n)
    click[:int(0.006 * SR)] = np.hanning(int(0.012 * SR))[int(0.006 * SR):] * rng.standard_normal(int(0.006 * SR))
    x = 0.9 * sub + 0.35 * burst + 0.25 * click
    x = x / np.abs(x).max() * 0.9
    st = np.stack([x, np.roll(x, 24) * 0.96], 1).astype(np.float32)
    (A / "sfx").mkdir(exist_ok=True)
    sf.write(A / "sfx" / "impact.wav", st, SR)
    return st


def main():
    T = json.loads((ROOT / "timing.json").read_text())
    W = json.loads((ROOT / "words.json").read_text(encoding="utf-8"))
    sc = {s["n"]: s for s in T["scenes"]}
    total = T["total"]
    N = int(round(total * SR))
    s2, s4, s7 = sc[2]["start"], sc[4]["start"], sc[7]["start"]
    wa = next(w for w in W if w["scene"] == 8 and w["text"].startswith("হোয়াটসঅ্যাপ"))
    pulse1 = round(wa["start"] + PILL_BOUNCE + PULSE_PEAK, 3)

    bus = np.zeros((N, 2), np.float32)
    b1, b2, b3 = dec(A / "music" / "bgm1.mp3"), dec(A / "music" / "bgm2.mp3"), dec(A / "music" / "bgm3.mp3")
    # bgm1: hit on Scene 2's first frame
    t1 = s2 - HIT1
    x1 = fade(b1[:int(21.0 * SR)], fin=0.5, fout=2.0)
    place(bus, x1, t1)
    # bgm1 pad loop (10-19 s) under Scene 3, crossfaded in as the original fades out, out as bgm2 comes in
    loop_at = t1 + 19.0
    loop_end = s4 - 1.0 + 1.0
    pad = b1[int(10.0 * SR):int(19.0 * SR)]
    reps = int(np.ceil((loop_end - loop_at) / 8.0)) + 1
    padl = np.concatenate([fade(pad, 0.5, 0.5)] * reps)[:int((loop_end - loop_at) * SR)]
    place(bus, fade(padl, fin=2.0, fout=1.0), loop_at, 0.9)
    # bgm2: 1 s before Scene 4 with a 1 s crossfade; out over the 1 s before Scene 7
    t2 = s4 - 1.0
    x2 = b2[:int((s7 - t2) * SR)]
    place(bus, fade(x2, fin=1.0, fout=1.0), t2)
    # bgm3: final hit on the pill's first pulse; fades in under bgm2 and owns the bed from Scene 7 on
    t3 = pulse1 - HIT3
    x3 = b3.copy()
    pre = int((s7 - 1.0 - t3) * SR)          # samples before the crossfade point: keep bgm3 low under bgm2
    env = np.ones(len(x3), np.float32)
    if pre > 0:
        env[:pre] = 0.35
        env[pre:pre + SR] = np.linspace(0.35, 1, min(SR, len(x3) - pre))
    place(bus, x3 * env[:, None], t3)
    bed_raw = A / "music" / "bed_raw.wav"
    sf.write(bed_raw, bus, SR)
    # duck under the voice: base -6 dB in gaps, pulled down to about -18 dB while speaking
    bed = A / "music" / "bed.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(bed_raw), "-i", str(A / "vo" / "voice.wav"), "-filter_complex",
                    "[0:a]volume=-6dB[m];[1:a]volume=4[k];[m][k]sidechaincompress=threshold=0.012:ratio=12:attack=35:release=500:makeup=1[d]",
                    "-map", "[d]", "-ar", str(SR), "-ac", "2", str(bed)], check=True)
    bed_raw.unlink()

    # clip ambience at -22 dB (unmuted clips), following each clip's rate and visible span
    amb = np.zeros((N, 2), np.float32)
    g = 10 ** (-22 / 20)
    for s in T["scenes"]:
        if s["muted"]:
            continue
        a0 = max(0.0, s["start"] - (0.2 if s["n"] > 1 else 0))
        x = dec(A / "clips" / f"scene{s['n']}.mp4", s["rate"])[:int(s["clip_play"] * SR)]
        # normalise each ambience to a common RMS first, so -22 dB means the same in every scene
        rms = np.sqrt((x ** 2).mean()) + 1e-9
        x = x / rms * 0.1
        place(amb, fade(x, 0.3, 0.4), a0, g)
    sf.write(A / "ambience.wav", amb, SR)

    hit = impact()
    imp = np.zeros((N, 2), np.float32)
    place(imp, hit, s2, 0.7)
    sf.write(A / "sfx" / "impact_track.wav", imp, SR)

    raw = A / "mix_raw.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(A / "vo" / "voice.wav"), "-i", str(bed), "-i", str(A / "ambience.wav"),
                    "-i", str(A / "sfx" / "impact_track.wav"), "-filter_complex",
                    "[0:a][1:a][2:a][3:a]amix=inputs=4:normalize=0[o]", "-map", "[o]", "-c:a", "pcm_f32le", str(raw)], check=True)
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                           "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    norm = (f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
            f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", f"{norm},aresample={SR},apad=whole_len={N},atrim=end_sample={N}",
                    "-ar", str(SR), "-ac", "2", str(A / "mix.wav")], check=True)
    raw.unlink()
    info = {"bgm1_at": round(t1, 3), "bgm1_hit_at": round(t1 + HIT1, 3), "scene2_start": s2, "bgm2_at": round(t2, 3),
            "bgm3_at": round(t3, 3), "bgm3_hit_at": round(t3 + HIT3, 3), "pill_first_pulse": pulse1, "crossfade_2_3": round(s7 - 1.0, 3)}
    (ROOT / "music.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
