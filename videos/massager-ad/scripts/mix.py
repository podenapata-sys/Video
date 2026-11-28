#!/usr/bin/env python3
"""Voice only (no music supplied) -> build/mix.wav, two-pass loudnorm to -14 LUFS, TP -1.5."""
import json
import subprocess
from pathlib import Path

B = Path(__file__).resolve().parent.parent / "build"
meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(B / "voice.wav"), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                      capture_output=True, text=True).stderr
m = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
norm = (f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
        f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(B / "voice.wav"), "-af", f"{norm},aresample=48000", "-ar", "48000", "-ac", "2", str(B / "mix.wav")], check=True)
print("mix.wav")
