#!/usr/bin/env python3
"""Split a numbered storyboard collage into images/01.png ... NN.png at 1080x1920.

  python3 scripts/split_collage.py <collage.png>

Panels are found from the white gutters. Each panel has its number badge painted
out, is upscaled, and is placed on a 1080x1920 canvas of its own background blue
with feathered edges so the padding is invisible. This is a draft path: send the
full-resolution originals as 01.png ... for the final.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1920
TRIM, BADGE, FEATHER = 4, 46, 40


def runs(mask, min_len=50):
    out, s = [], None
    for i, v in enumerate(mask):
        if not v and s is None:
            s = i
        if v and s is not None:
            out.append((s, i))
            s = None
    if s is not None:
        out.append((s, len(mask)))
    return [r for r in out if r[1] - r[0] >= min_len]


def panels(im):
    a = np.asarray(im).astype(int)
    white = a.min(axis=2) > 235
    boxes = []
    for y0, y1 in runs(white.mean(axis=1) > 0.97):
        for x0, x1 in runs(white[y0:y1].mean(axis=0) > 0.97):
            boxes.append((x0 + TRIM, y0 + TRIM, x1 - TRIM, y1 - TRIM))
    return boxes


def bg_color(p):
    """Median of the top strip, right of the badge: always empty background."""
    a = np.asarray(p)[4:30, p.width // 2:].reshape(-1, 3)
    return tuple(int(v) for v in np.median(a, axis=0))


def main():
    src = Image.open(sys.argv[1]).convert("RGB")
    boxes = panels(src)
    print(f"found {len(boxes)} panels")
    out = ROOT / "images"
    out.mkdir(exist_ok=True)
    for n, box in enumerate(boxes, 1):
        p = src.crop(box)
        bg = bg_color(p)
        ImageDraw.Draw(p).rectangle([0, 0, BADGE, BADGE], fill=bg)
        s = min(W / p.width, (H - 120) / p.height)
        p = p.resize((round(p.width * s), round(p.height * s)), Image.LANCZOS)
        p = p.filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=2))
        canvas = Image.new("RGB", (W, H), bg)
        # An edge where the art is cut off (bodies, not background) stays hard and
        # sits flush against the canvas edge instead of fading out.
        a = np.asarray(p).astype(int)
        busy = {k: np.abs(strip.reshape(-1, 3) - bg).sum(axis=1).mean() > 40
                for k, strip in {"l": a[:, :8], "r": a[:, -8:], "b": a[-8:], "t": a[:8]}.items()}
        x, y = (W - p.width) // 2, H - p.height - (0 if busy["b"] else 60)
        f = {k: (0 if busy[k] else FEATHER) for k in busy}
        mask = Image.new("L", (p.width + 2 * FEATHER, p.height + 2 * FEATHER), 0)
        ImageDraw.Draw(mask).rectangle([FEATHER + f["l"], FEATHER + f["t"],
                                        FEATHER + p.width - f["r"], FEATHER + p.height - f["b"]], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(FEATHER / 2))
        for k in busy:  # re-solidify hard edges after the blur
            if busy[k]:
                box = {"l": [0, 0, FEATHER * 2, mask.height], "r": [mask.width - FEATHER * 2, 0, mask.width, mask.height],
                       "t": [0, 0, mask.width, FEATHER * 2], "b": [0, mask.height - FEATHER * 2, mask.width, mask.height]}[k]
                ImageDraw.Draw(mask).rectangle(box, fill=255)
        mask = mask.crop((FEATHER, FEATHER, FEATHER + p.width, FEATHER + p.height))
        canvas.paste(p, (x, y), mask)
        canvas.save(out / f"{n:02d}.png")
    print("saved", ", ".join(f"{n:02d}.png" for n in range(1, len(boxes) + 1)))


if __name__ == "__main__":
    main()
