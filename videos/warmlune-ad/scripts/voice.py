#!/usr/bin/env python3
"""WARMLUNE: voice lines -> scene grid (timing.json), voice track, ducked music bed, final -14 LUFS mix.

  python3 scripts/voice.py        (run from videos/warmlune-ad/)

The voice drives the timeline (user's brief):
- each line: leading/trailing silence trimmed, inner pauses longer than MAX_PAUSE shortened to it (user's choice,
  to land near 46 s); no word is cut and the speed never changes
- scene length = LEAD + speech + tail (TAIL, or LONG_TAIL after scenes 1 and 7 so the emotion breathes)
- if the total is over 46 s, padding is cut in steps (never the voice)
Writes assets/vo/tight/voN.wav, assets/vo/voice.wav, assets/music/bed.wav, assets/mix.wav and timing.json.
"""
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
VO, MU = ROOT / "assets" / "vo", ROOT / "assets" / "music"
TIGHT = VO / "tight"
SR, FPS = 48000, 30
MAX_PAUSE = 0.35
TARGET = 46.0
# padding steps tried in order until the total fits TARGET: (lead, tail, long tail for scenes 1 and 7)
END_HOLD = 1.2  # scene 8 holds after the CTA voice so the end card's button can pulse twice
STEPS = [(0.4, 0.6, 1.2), (0.4, 0.6, 0.8), (0.4, 0.4, 0.8), (0.3, 0.4, 0.6), (0.25, 0.3, 0.5)]


def frames(t):
    return round(t * FPS) / FPS


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def silences(a, d, noise=-40):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                        f"silencedetect=noise={noise}dB:d={d}", "-f", "null", "-"], input=a.tobytes(), capture_output=True)
    err = p.stderr.decode()
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(st, en + [None] * (len(st) - len(en))))


def tighten(a):
    """Trim the ends (keeping 30 ms of air) and shorten inner pauses; returns the tightened samples."""
    dur = len(a) / SR
    lead, end = 0.0, dur
    for s, e in silences(a, 0.04):
        if s < 0.01:
            lead = max(0.0, (e or dur) - 0.03)
            break
    inner = []
    for s, e in silences(a, 0.2):
        if e is None or e >= dur - 0.05:
            end = min(end, s + 0.06)
        elif s > lead + 0.05:
            inner.append((s, e))
    pieces, cur = [], lead
    for s, e in inner:
        pieces.append(a[int(cur * SR):int(s * SR)])
        gap = min(e - s, MAX_PAUSE)
        mid = (s + e) / 2
        pieces.append(a[int((mid - gap / 2) * SR):int((mid + gap / 2) * SR)])
        cur = e
    pieces.append(a[int(cur * SR):int(end * SR)])
    out = np.concatenate(pieces)
    f = int(0.005 * SR)
    out[:f] *= np.linspace(0, 1, f)
    out[-f:] *= np.linspace(1, 0, f)
    return out


def ffrun(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def loudnorm_two_pass(src, dst, n, pre=""):
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-af", f"{pre}loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                           "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    norm = (f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
            f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    ffrun("-i", str(src), "-af", f"{pre}{norm},aresample={SR},apad=whole_len={n},atrim=end_sample={n}",
          "-ar", str(SR), "-ac", "2", str(dst))


def music_bed(total, voice_path):
    """Track #2 looped at a bar boundary with a hidden crossfade, ducked under the voice, faded in/out."""
    bpm_beats = MU / "bgm.mp3"
    L = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(bpm_beats)],
                             capture_output=True, text=True).stdout)
    xf = 1.5
    loops = int(np.ceil((total + 2) / (L - xf))) + 1
    # chain the loops with acrossfade (equal-power) so the seam is inaudible
    ins, chain = [], ""
    for i in range(loops):
        ins += ["-i", str(bpm_beats)]
    prev = "[0:a]"
    for i in range(1, loops):
        chain += f"{prev}[{i}:a]acrossfade=d={xf}:c1=qsin:c2=qsin[x{i}];"
        prev = f"[x{i}]"
    looped = MU / "bgm_looped.wav"
    ffrun(*ins, "-filter_complex", chain.rstrip(";") if chain else "[0:a]anull", "-map", prev if chain else "0:a",
          "-ar", str(SR), "-ac", "2", "-t", f"{total:.4f}", str(looped))
    bed = MU / "bed.wav"
    # base -9 dB in the gaps; sidechain pulls it ~9 dB more (to about -18 dB) while the voice speaks
    ffrun("-i", str(looped), "-i", str(voice_path), "-filter_complex",
          f"[0:a]volume=-9dB[m];[1:a]aformat=channel_layouts=stereo,volume=4[k];"
          f"[m][k]sidechaincompress=threshold=0.015:ratio=10:attack=40:release=450:makeup=1[d];"
          f"[d]afade=t=in:d=1.0,afade=t=out:st={total - 1.5:.4f}:d=1.5[o]",
          "-map", "[o]", "-ar", str(SR), "-ac", "2", "-t", f"{total:.4f}", str(bed))
    return looped, bed


def main():
    TIGHT.mkdir(parents=True, exist_ok=True)
    lines = []
    for n in range(1, 9):
        a = tighten(decode(VO / f"vo{n}.mp3"))
        sf.write(TIGHT / f"vo{n}.wav", a, SR)
        lines.append(len(a) / SR)
    speech = sum(lines)
    for lead, tail, long_tail in STEPS:
        lens = [frames(lead + d + (END_HOLD if n == 8 else long_tail if n in (1, 7) else tail))
                for n, d in enumerate(lines, 1)]
        if sum(lens) <= TARGET + END_HOLD:
            break
    total = round(sum(lens), 4)
    scenes, t = [], 0.0
    for n, (d, L) in enumerate(zip(lines, lens), 1):
        scenes.append({"n": n, "start": round(t, 4), "length": L, "vo_at": round(t + lead, 4), "speech": round(d, 3)})
        t += L
    print(f"speech {speech:.2f}s  padding lead {lead} tail {tail} long {long_tail}  total {total:.2f}s")
    for s in scenes:
        print(f"  scene {s['n']}: {s['start']:6.3f}-{s['start'] + s['length']:6.3f}  ({s['length']:.3f}s)  voice "
              f"{s['vo_at']:.3f}-{s['vo_at'] + s['speech']:.3f}")
    # voice track at 0 dB, back to back on the grid
    N = int(round(total * SR))
    v = np.zeros(N, np.float32)
    for s in scenes:
        a, _ = sf.read(TIGHT / f"vo{s['n']}.wav", dtype="float32")
        o = int(round(s["vo_at"] * SR))
        v[o:o + len(a)] += a[:N - o]
    sf.write(VO / "voice.wav", np.stack([v, v], 1), SR)
    looped, bed = music_bed(total, VO / "voice.wav")
    raw = ROOT / "assets" / "mix_raw.wav"
    ffrun("-i", str(VO / "voice.wav"), "-i", str(bed), "-filter_complex", "[0:a][1:a]amix=inputs=2:normalize=0[o]",
          "-map", "[o]", "-ar", str(SR), "-ac", "2", "-c:a", "pcm_f32le", str(raw))
    loudnorm_two_pass(raw, ROOT / "assets" / "mix.wav", N)
    raw.unlink()
    looped.unlink()
    (ROOT / "timing.json").write_text(json.dumps({"total": total, "lead": lead, "tail": tail, "long_tail": long_tail,
                                                  "scenes": scenes}, indent=1))


if __name__ == "__main__":
    main()
