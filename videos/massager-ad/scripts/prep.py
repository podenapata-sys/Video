#!/usr/bin/env python3
"""Massager ad prep: cut the joined 60 fps source into 10 x 3 s scenes (0.15 s handles for the 0.3 s crossfades),
muted, 1080x1920, 30 fps; scene 10 freezes its last frame so the 31.5 s voiceover finishes; build/voice.wav + timeline."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "build"
A = ROOT / "assets"
SR = 48000
H = 0.15


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)


def main():
    B.mkdir(exist_ok=True)
    vo = dur(A / "vo.mp3")
    total = round(vo + 0.1, 2)
    src_len = dur(A / "source.mov")
    scenes = []
    for i in range(10):
        start, end = 3.0 * i, (3.0 * (i + 1) if i < 9 else total)
        cs = max(0.0, start - H)
        ce = end + (H if i < 9 else 0.0)
        src_end = min(ce, src_len - 0.05)
        vf = (f"fps=30,scale=1080:1920:flags=lanczos,setsar=1,tpad=stop_mode=clone:stop_duration=5,trim=duration={ce - cs:.3f}")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{cs:.3f}", "-to", f"{src_end:.3f}", "-i", str(A / "source.mov"), "-vf", vf, "-an",
                        "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p", str(B / f"s{i + 1}.mp4")], check=True)
        scenes.append({"n": i + 1, "start": start, "end": end, "clip_start": round(cs, 3), "clip_dur": round(ce - cs, 3)})
        print(f"  scene {i + 1}: {start:5.2f}-{end:5.2f}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(A / "vo.mp3"), "-af", f"apad=whole_dur={total}", "-ar", str(SR), "-ac", "2", str(B / "voice.wav")], check=True)
    (B / "timeline.json").write_text(json.dumps({"total": total, "scenes": scenes}, indent=1))
    print("total", total)


if __name__ == "__main__":
    main()
