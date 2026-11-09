#!/usr/bin/env python3
"""WarmLune 55 s ad: place the 10 voice lines on the fixed scene grid, build the 3-part music bed, mix to -14 LUFS.

  python3 scripts/audio.py        (run from videos/warmlune-ad2/)

- Scene cuts are fixed by the brief: 0 4 8 13 18 23 28 33 40 48 55.
- Each line (media/vo/voN.mp3, one per scene) has its leading/trailing silence trimmed and starts 0.15 s after its
  scene cut, or 0.12 s after the previous line ends if that line is still speaking. Never cut, never sped up.
- Music: part 1 (melancholic) 0-8 s, part 2 (hopeful) from the 8 s flash, part 3 (urgency) from 33 s, crossfaded;
  each about -12 dB (25%), ducked further (to about -18 dB) under the voice. Fade in from black, fade out at the end.
Writes media/voiceover.wav, media/music.wav, media/mix.wav and timing.json.
"""
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "media"
SR, TOTAL = 48000, 55.0
CUTS = [0, 4, 8, 13, 18, 23, 28, 33, 40, 48, 55]
LEAD, GAP = 0.15, 0.12


def dec(path, ch=1):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", str(ch), "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).copy()
    return a if ch == 1 else a.reshape(-1, ch)


def trim(a):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                        "silencedetect=noise=-40dB:d=0.04", "-f", "null", "-"], input=a.tobytes(), capture_output=True)
    err = p.stderr.decode()
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    dur = len(a) / SR
    lead, end = 0.0, dur
    for s, e in zip(st, en + [None] * (len(st) - len(en))):
        if s < 0.01:
            lead = max(0.0, (e or dur) - 0.03)
        if e is None or e >= dur - 0.02:
            end = min(end, s + 0.03)
    out = a[int(lead * SR):int(end * SR)].copy()
    f = int(0.005 * SR)
    out[:f] *= np.linspace(0, 1, f)
    out[-f:] *= np.linspace(1, 0, f)
    return out


def fade(x, fin=0.0, fout=0.0):
    x = x.copy()
    for n, curve in ((int(fin * SR), np.sin), (int(fout * SR), np.cos)):
        if n <= 0:
            continue
        n = min(n, len(x))
        ramp = curve(np.linspace(0, np.pi / 2, n))[:, None]
        if curve is np.sin:
            x[:n] *= ramp
        else:
            x[-n:] *= ramp
    return x


def place(bus, x, t, g=1.0):
    o = int(round(t * SR))
    n = min(len(x), len(bus) - o)
    if n > 0:
        bus[o:o + n] += x[:n] * g


def main():
    N = int(round(TOTAL * SR))
    voice = np.zeros(N, np.float32)
    lines, prev_end = [], 0.0
    for n in range(1, 11):
        a = trim(dec(MD / "vo" / f"vo{n}.mp3"))
        want = CUTS[n - 1] + LEAD
        start = round(max(want, prev_end + GAP if n > 1 else 0), 3)
        end = round(start + len(a) / SR, 3)
        assert end <= TOTAL - 0.6, f"line {n} would run past the end"
        place(voice, a, start)
        spill = end - CUTS[n]
        lines.append({"scene": n, "start": start, "end": end, "dur": round(len(a) / SR, 3),
                      "spills_into_next": round(spill, 3) if spill > 0 else 0})
        print(f"  S{n:<2} scene {CUTS[n-1]:>4}-{CUTS[n]:<4} voice {start:6.3f}-{end:6.3f}"
              f"{f'  (runs {spill:.2f}s into S{n+1})' if spill > 0 else ''}")
        prev_end = end
    sf.write(MD / "voiceover.wav", np.stack([voice, voice], 1), SR)

    bus = np.zeros((N, 2), np.float32)
    p1, p2, p3 = (dec(MD / "music" / f"part{k}.mp3", 2) for k in (1, 2, 3))
    xf2, xf3 = 0.8, 1.0
    a2 = 8.0 - 0.4                    # part 2 crossfades across the 8 s flash
    a3 = 33.0 - 0.5                   # part 3 crossfades across the 33 s cut
    place(bus, fade(p1[:int((a2 + xf2) * SR)], fin=0.5, fout=xf2), 0.0)
    place(bus, fade(p2[:int((a3 + xf3 - a2) * SR)], fin=xf2, fout=xf3), a2)
    place(bus, fade(p3[:int((TOTAL - a3) * SR)], fin=xf3, fout=1.5), a3)
    raw = MD / "music_raw.wav"
    sf.write(raw, bus, SR)
    # 25% (-12 dB) bed, sidechain-ducked about 6 dB more under speech (to about -18 dB), rising in the gaps
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-i", str(MD / "voiceover.wav"), "-filter_complex",
                    "[0:a]volume=-12dB[m];[1:a]volume=4[k];[m][k]sidechaincompress=threshold=0.015:ratio=6:attack=40:release=450:makeup=1[d]",
                    "-map", "[d]", "-ar", str(SR), "-ac", "2", str(MD / "music.wav")], check=True)
    raw.unlink()
    pre = MD / "mix_raw.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(MD / "voiceover.wav"), "-i", str(MD / "music.wav"), "-filter_complex",
                    "[0:a][1:a]amix=inputs=2:normalize=0,afade=t=in:d=0.5,afade=t=out:st=54.5:d=0.5[o]", "-map", "[o]",
                    "-c:a", "pcm_f32le", str(pre)], check=True)
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pre), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                           "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    norm = (f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
            f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af", f"{norm},aresample={SR},apad=whole_len={N},atrim=end_sample={N}",
                    "-ar", str(SR), "-ac", "2", str(MD / "mix.wav")], check=True)
    pre.unlink()
    (ROOT / "timing.json").write_text(json.dumps({"total": TOTAL, "cuts": CUTS, "lines": lines,
                                                  "music": {"part2_at": a2, "part3_at": a3}}, indent=1))


if __name__ == "__main__":
    main()
