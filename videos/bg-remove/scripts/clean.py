#!/usr/bin/env python3
"""Remove the background man (and his wall shadow) from source.mp4 -> renders/runway-clean.mp4.

  python3 scripts/clean.py [--preview]

1. work_matte.mov (hyperframes remove-background, u2net_human_seg) masks every person;
   the woman is tracked back from the last frame (where she is the biggest person),
   everything else that is a person is the man.
2. For each frame the hole (man, dilated, plus his shadow on the wall) is filled with the
   real background from other frames, where the man stood somewhere else: donors are aligned
   to the camera move with a homography fitted on background features only, exposure-matched,
   and combined with a per-pixel median. Anything no donor can see is inpainted.
3. The fill is feathered in, never over the woman, and the original audio is copied untouched.
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1920
DONOR_STEPS = [20, 40, 60, 90, 120, 160, 200, 250, 300, 360]
MIN_INLIERS = 40
SHADOW_DROP = 14
MERGED_UNTIL = 32          # frames where the man and the woman are one blob in the full matte
SPLIT_SEARCH = (430, 540)  # columns to look for the gap between them in those frames  # a pixel this much darker than the clean wall, left of the man, is shadow


def read_raw(path, vf, pix, ch, w=W):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", vf, "-f", "rawvideo", "-pix_fmt", pix, "-"],
                         capture_output=True, check=True).stdout
    shape = (-1, H, w, ch) if ch > 1 else (-1, H, w)
    return np.frombuffer(raw, np.uint8).reshape(shape)


def split_people(alpha, alpha_l, alpha_r):
    """Per frame: (woman mask, man mask).

    The full-frame matte always finds the woman (the main subject) but often drops the man, so the
    half-frame crops (where he is the main subject) are matted too. The woman is the largest blob of
    the full matte; in the first frames, where the two blobs touch, she is cut off at the thinnest
    column between them. The man is every person pixel from any matte that is not her.
    """
    n = len(alpha)
    woman, man = np.zeros((n, H, W), bool), np.zeros((n, H, W), bool)
    for t in range(n):
        b = (alpha[t] > 100).astype(np.uint8)
        k, lab, stats, _ = cv2.connectedComponentsWithStats(b, 8)
        comps = [i for i in range(1, k) if stats[i, cv2.CC_STAT_AREA] > 1500]
        w = np.zeros((H, W), bool)
        if comps:
            w = lab == max(comps, key=lambda i: stats[i, cv2.CC_STAT_AREA])
        if t < MERGED_UNTIL:  # one blob: man on the left, her on the right
            cols = w[:, SPLIT_SEARCH[0]:SPLIT_SEARCH[1]].sum(0)
            cut = SPLIT_SEARCH[0] + int(np.argmin(cols))
            w[:, :cut] = False
        crop = np.zeros((H, W), bool)
        crop[:, : W // 2] = alpha_l[t] > 100
        crop[:, W // 2:] = alpha_r[t] > 100
        m = ((b > 0) | crop) & ~cv2.dilate(w.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
        k, lab, stats, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
        keep = [i for i in range(1, k) if stats[i, cv2.CC_STAT_AREA] > 2500]
        woman[t], man[t] = w, np.isin(lab, keep)
    return woman, man


class Aligner:
    """ORB features on the background only (people masked out), at half resolution."""

    def __init__(self, frames, people):
        self.orb = cv2.ORB_create(2500)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING)
        self.kp, self.des = [], []
        k = np.ones((61, 61), np.uint8)
        for f, p in zip(frames, people):
            g = cv2.resize(cv2.cvtColor(f, cv2.COLOR_RGB2GRAY), (W // 2, H // 2))
            msk = cv2.resize((~cv2.dilate(p.astype(np.uint8), k).astype(bool)).astype(np.uint8) * 255, (W // 2, H // 2))
            kp, des = self.orb.detectAndCompute(g, msk)
            self.kp.append(np.float32([x.pt for x in kp]) if kp else np.zeros((0, 2), np.float32))
            self.des.append(des)
        self.cache = {}

    def h(self, s, t):
        """Homography mapping frame s pixels onto frame t (full resolution), or None."""
        if (s, t) in self.cache:
            return self.cache[(s, t)]
        out = None
        if self.des[s] is not None and self.des[t] is not None and len(self.des[s]) > 10 and len(self.des[t]) > 10:
            pairs = self.bf.knnMatch(self.des[s], self.des[t], k=2)
            good = [m for m, n2 in (p for p in pairs if len(p) == 2) if m.distance < 0.75 * n2.distance]
            if len(good) >= MIN_INLIERS:
                a = self.kp[s][[m.queryIdx for m in good]]
                b = self.kp[t][[m.trainIdx for m in good]]
                hm, inl = cv2.findHomography(a, b, cv2.RANSAC, 2.0)
                if hm is not None and inl.sum() >= MIN_INLIERS:
                    sc = np.diag([2.0, 2.0, 1.0])
                    out = sc @ hm @ np.linalg.inv(sc)
        self.cache[(s, t)] = out
        return out


def shadow_zone(man, hgt):
    """Where his shadow can fall: the man's mask smeared to the left (light comes from the right)."""
    reach = max(3, int(0.35 * hgt))
    kern = np.ones((9, reach + 1), np.uint8)
    # dst(x) = max src(x + dx), dx in [0, reach]: a pixel joins the zone if the man is up to `reach` px to its right
    return cv2.dilate(man.astype(np.uint8), kern, anchor=(0, 4)).astype(bool)


def main():
    frames = read_raw(ROOT / "source.mp4", "null", "rgb24", 3)
    alpha = read_raw(ROOT / "work_matte.mov", "alphaextract", "gray", 1)
    half = [read_raw(ROOT / f"work_matte_{side}.mov", "alphaextract", "gray", 1, W // 2) for side in ("left", "right")]
    n = min(len(frames), len(alpha), *(len(x) for x in half))
    frames = frames[:n]
    print(f"{n} frames")
    woman, man = split_people(alpha[:n], half[0][:n], half[1][:n])
    del alpha, half
    people = woman | man
    al = Aligner(frames, people)
    print("features done")

    hgt = np.zeros(n)
    excl = np.zeros((n, H, W), bool)  # donor pixels never to borrow: anyone, the man's shadow zone, edges of masks
    for t in range(n):
        ys = np.nonzero(man[t].any(1))[0]
        hgt[t] = ys[-1] - ys[0] if len(ys) else 0
        e = cv2.dilate(people[t].astype(np.uint8), np.ones((31, 31), np.uint8)).astype(bool)
        if hgt[t]:
            e |= shadow_zone(cv2.dilate(man[t].astype(np.uint8), np.ones((31, 31), np.uint8)), hgt[t])
        excl[t] = e

    patches = {}  # t -> (y0, x0, patch): only the edited regions, the frames stay untouched as donors
    stats = []
    preview = "--preview" in sys.argv
    todo = range(0, n, 32) if preview else range(n)
    for t in todo:
        if hgt[t] < 40:
            continue
        mdil = cv2.dilate(man[t].astype(np.uint8), np.ones((25, 25), np.uint8)).astype(bool)
        zone = shadow_zone(mdil, hgt[t])
        ys, xs = np.nonzero(zone)
        y0, y1 = max(0, ys.min() - 40), min(H, ys.max() + 40)
        x0, x1 = max(0, xs.min() - 40), min(W, xs.max() + 40)
        rh, rw = y1 - y0, x1 - x0
        tgt = frames[t, y0:y1, x0:x1].astype(np.float32)
        ring = ~excl[t][y0:y1, x0:x1]
        samples = []
        for d in DONOR_STEPS:
            for s in (t - d, t + d):
                if not 0 <= s < n:
                    continue
                hm = al.h(s, t)
                if hm is None:
                    continue
                shift = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]], np.float64) @ hm
                img = cv2.warpPerspective(frames[s], shift, (rw, rh), flags=cv2.INTER_LINEAR).astype(np.float32)
                bad = cv2.warpPerspective(excl[s].astype(np.uint8), shift, (rw, rh), flags=cv2.INTER_NEAREST,
                                          borderMode=cv2.BORDER_CONSTANT, borderValue=1).astype(bool)
                both = ring & ~bad
                if both.sum() < 500:
                    continue
                gain = np.median(tgt[both] + 1, axis=0) / np.median(img[both] + 1, axis=0)
                img *= np.clip(gain, 0.8, 1.25)
                img[bad] = np.nan
                samples.append(img)
        if samples:
            bg = np.nanmedian(np.stack(samples), axis=0)
        else:
            bg = np.full_like(tgt, np.nan)
        have = ~np.isnan(bg[..., 0])
        # his shadow: clearly darker than the clean wall, inside the shadow zone, not on the woman
        lum_t = tgt @ np.float32([0.3, 0.59, 0.11])
        lum_b = np.nan_to_num(bg) @ np.float32([0.3, 0.59, 0.11])
        shadow = zone[y0:y1, x0:x1] & have & (lum_b - lum_t > SHADOW_DROP) & ~woman[t][y0:y1, x0:x1]
        shadow = cv2.morphologyEx(shadow.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8))
        hole = (mdil[y0:y1, x0:x1] | shadow.astype(bool)) & ~woman[t][y0:y1, x0:x1]
        hole = cv2.dilate(hole.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool) & ~woman[t][y0:y1, x0:x1]
        fill = np.where(have[..., None], bg, tgt)
        left = hole & ~have
        fill8 = np.clip(fill, 0, 255).astype(np.uint8)
        if left.any():
            fill8 = cv2.inpaint(fill8, left.astype(np.uint8), 9, cv2.INPAINT_TELEA)
        a = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 4)
        a *= ~cv2.dilate(woman[t][y0:y1, x0:x1].astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        a = a[..., None]
        patches[t] = (y0, x0, np.clip(fill8 * a + tgt * (1 - a), 0, 255).astype(np.uint8))
        stats.append((t, len(samples), int(hole.sum()), int(left.sum())))
        if t % 50 == 0:
            print(f"frame {t}: {len(samples)} donors, hole {hole.sum()} px, inpainted {left.sum()} px")

    uncovered = sum(s[3] for s in stats) / max(1, sum(s[2] for s in stats))
    print(f"processed {len(stats)} frames, {uncovered:.1%} of hole pixels inpainted (no donor)")
    if preview:
        for t, (y0, x0, p) in patches.items():
            f = frames[t].copy()
            f[y0:y0 + p.shape[0], x0:x0 + p.shape[1]] = p
            cv2.imwrite(str(ROOT / f"work_prev_{t:03d}.jpg"), cv2.cvtColor(np.hstack([frames[t], f]), cv2.COLOR_RGB2BGR))
        return
    dst = ROOT / "renders" / "runway-clean.mp4"
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "60",
                            "-i", "-", "-i", str(ROOT / "source.mp4"), "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
                            "-crf", "18", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart",
                            "-shortest", str(dst)], stdin=subprocess.PIPE)
    for t in range(n):
        f = frames[t]
        if t in patches:
            y0, x0, p = patches[t]
            f = f.copy()
            f[y0:y0 + p.shape[0], x0:x0 + p.shape[1]] = p
        enc.stdin.write(f.tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote", dst)


if __name__ == "__main__":
    main()
