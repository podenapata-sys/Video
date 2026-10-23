#!/usr/bin/env python3
"""Word-level forced alignment of each VO chunk against the script (pocketsphinx) -> timing.json.

  python3 scripts/force_align.py

pocketsphinx ships its own English model, so this runs offline. Given the exact words,
it finds where each one is spoken; every script line then gets the start of its first
word and the end of its last word.
"""
import glob
import json
import re
import subprocess
from pathlib import Path

from pocketsphinx import Decoder

ROOT = Path(__file__).resolve().parent.parent
RANGES = [(1, 15), (16, 32), (33, 52), (53, 66), (67, 82), (83, 95)]
SPOKEN = {"3:00": "three", "a.m.": "a m", "3:17": "three seventeen", "30,000": "thirty thousand", "11": "eleven",
          "41": "forty one", "don't": "don't", "it's": "it's"}


def words_of(line):
    out = []
    for raw in line.replace("…", " ").replace("—", " ").replace('"', " ").split():
        w = raw.lower().strip(".,!?;:")
        w = SPOKEN.get(raw.lower().strip(",."), SPOKEN.get(w, w))
        out += [x for x in re.sub(r"[^a-z' ]", " ", w).split() if x]
    return out


def pcm(path):
    return subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                          capture_output=True, check=True).stdout


def main():
    scenes = {s["scene"]: s["text"] for s in json.loads((ROOT / "scenes.json").read_text())}
    files = sorted(glob.glob(str(ROOT / "assets" / "vo" / "VO_Chunk_*.mp3")))
    out = []
    for c, (f, (a, b)) in enumerate(zip(files, RANGES), 1):
        line_words = [words_of(scenes[i]) for i in range(a, b + 1)]
        flat = [w for lw in line_words for w in lw]
        dec = Decoder(samprate=16000, bestpath=False, loglevel="FATAL", beam=1e-100, wbeam=1e-80, pbeam=1e-100)  # wide beams: long chunks
        dec.set_align_text(" ".join(flat))
        dec.start_utt()
        dec.process_raw(pcm(f), full_utt=True)
        dec.end_utt()
        segs = [(s.word, s.start_frame / 100, (s.end_frame + 1) / 100) for s in dec.seg() if s.word not in ("<s>", "</s>", "<sil>", "(NULL)")]
        segs = [(re.sub(r"\(\d+\)$", "", w), s, e) for w, s, e in segs]
        assert len(segs) == len(flat), f"chunk {c}: aligned {len(segs)} of {len(flat)} words"
        k = 0
        for n, lw in zip(range(a, b + 1), line_words):
            ws = segs[k:k + len(lw)]
            k += len(lw)
            out.append({"scene": n, "chunk": c, "start": round(ws[0][1], 2), "end": round(ws[-1][2], 2),
                        "words": [[w, round(s, 2), round(e, 2)] for w, s, e in ws], "text": scenes[n]})
            print(f"{n:02d} c{c} {ws[0][1]:6.2f}-{ws[-1][2]:6.2f}  {scenes[n][:70]}")
    (ROOT / "timing.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
