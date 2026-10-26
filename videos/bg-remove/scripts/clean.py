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
MIN_INLIERS = 40
MIN_LOCAL = 25
LOCAL_MARGIN = 260  # px around the hole whose features drive the local fit
MERGED_UNTIL = 32          # frames where the man and the woman are one blob in the full matte
SPLIT_SEARCH = (430, 540)  # columns to look for the gap between them in those frames
HIDDEN_FROM = 386          # from here he is hidden behind her; mattes only add false positives
# frame: (x0, x1, y0, y1) of him at the right edge, read off a grid; interpolated between keys
LATE_KEYS = {446: (830, 870, 610, 740), 448: (830, 875, 610, 760), 454: (845, 905, 615, 780),
             460: (860, 935, 620, 880), 466: (875, 960, 610, 910), 472: (890, 995, 595, 910),
             478: (925, 1040, 580, 915), 484: (975, 1080, 565, 915), 490: (1020, 1080, 595, 915),
             495: (1050, 1080, 600, 915)}
LATE_PAD = 22
MAX_DONORS = 25
BG_PERCENTILE = 80
DEBUG = [int(x) for x in sys.argv[sys.argv.index('--debug') + 1].split(',')] if '--debug' in sys.argv else []
SHADOW_DROP = 12           # this much darker than the clean background, near him, is his shadow
MAX_ERR = 14               # mean abs error on the surroundings above which a donor is misaligned  # a pixel this much darker than the clean wall, left of the man, is shadow


def read_raw(path, vf, pix, ch, w=W):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", vf, "-f", "rawvideo", "-pix_fmt", pix, "-"],
                         capture_output=True, check=True).stdout
    shape = (-1, H, w, ch) if ch > 1 else (-1, H, w)
    return np.frombuffer(raw, np.uint8).reshape(shape)


def track_shift(prev, cur, mask):
    """(dx, dy) that best moves the masked region of prev onto cur (mean abs difference, half resolution)."""
    if not mask.any():
        return 0, 0
    p, c = prev[::2, ::2].astype(np.float32), cur[::2, ::2].astype(np.float32)
    m = mask[::2, ::2]
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    tpl, msk = p[y0:y1, x0:x1], m[y0:y1, x0:x1]
    best = (np.inf, 0, 0)
    for dy in range(-1, 2):  # he walks sideways; vertical search only absorbs jitter (more drifts upward)
        for dx in range(-9, 10):
            if y0 + dy < 0 or x0 + dx < 0 or y1 + dy > c.shape[0] or x1 + dx > c.shape[1]:
                continue
            err = np.abs(c[y0 + dy:y1 + dy, x0 + dx:x1 + dx] - tpl)[msk].mean()
            if err < best[0]:
                best = (err, dx, dy)
    return best[1] * 2, best[2] * 2


def split_people(alpha, alpha_l, alpha_r, frames_gray):
    """Per frame: (woman mask, man mask).

    The full-frame matte always finds the woman (the main subject) but often drops the man, so the
    half-frame crops (where he is the main subject) are matted too. The woman is the largest blob of
    the full matte; in the first frames, where the two blobs touch, she is cut off at the thinnest
    column between them. The man is every person pixel from any matte that is not her.
    """
    n = len(alpha)
    woman, man = np.zeros((n, H, W), bool), np.zeros((n, H, W), bool)
    last = None  # (right edge, bottom row) of the man when last seen, to follow him into her blob
    cut_prev = None
    tmpl, off = None, (0, 0)  # his silhouette from the last frame he stood apart, and how far he has moved since

    def his_parts(m, w, part):
        k, lab, stats, cen = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
        near = cv2.dilate(w.astype(np.uint8), np.ones((31, 31), np.uint8)).astype(bool)
        wy = np.nonzero(w.any(1))[0]
        keep = []
        for i in range(1, k):
            if stats[i, cv2.CC_STAT_AREA] <= 2500:
                continue
            if part is not None and (part & (lab == i)).any():
                keep.append(i)  # cut off her blob above his feet: him, whatever its centroid
                continue
            # a blob stuck to her lower body is her shoe / scarf / hem that her matte missed, not him
            if wy.size and (near & (lab == i)).any() and cen[i][1] > wy[0] + 0.6 * (wy[-1] - wy[0]):
                continue
            keep.append(i)
        return np.isin(lab, keep)

    for t in range(n):
        b = alpha[t] > 100
        k, lab, stats, _ = cv2.connectedComponentsWithStats(b.astype(np.uint8), 8)
        comps = [i for i in range(1, k) if stats[i, cv2.CC_STAT_AREA] > 1500]
        w = lab == max(comps, key=lambda i: stats[i, cv2.CC_STAT_AREA]) if comps else np.zeros((H, W), bool)
        if t < MERGED_UNTIL:  # one blob: man on the left, her on the right
            cols = w[:, SPLIT_SEARCH[0]:SPLIT_SEARCH[1]].sum(0)
            w[:, : SPLIT_SEARCH[0] + int(np.argmin(cols))] = False
        if t >= HIDDEN_FROM:  # he is behind her, then only at the right edge (found separately)
            woman[t] = w
            continue
        anyone = b.copy()
        anyone[:, : W // 2] |= alpha_l[t] > 100
        anyone[:, W // 2:] |= alpha_r[t] > 100

        def others(wm):
            return anyone & ~cv2.dilate(wm.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)

        mm = his_parts(others(w), w, None)
        cut = None
        cols_m = np.nonzero(mm.any(0))[0]
        near_last = (cols_m > last[0] - 200) & (cols_m < last[0] + 40) if last else np.zeros(0, bool)
        apart = near_last.any() and mm[:, cols_m[near_last]].sum() > (0.5 * tmpl.sum() if tmpl is not None else 2500)
        if t >= MERGED_UNTIL and last and not apart:
            # no separate him where he just was: he walked into her blob (frames ~312-384). Use his exact
            # silhouette from the last frame he stood apart, moved by his own motion (appearance match), and
            # give her everything right of the thinnest column near his right edge (she is in front of him)
            if tmpl is None:
                tmpl, off = man[t - 1].copy(), (0, 0)
            visible = shifted(tmpl, *off)
            if cut_prev is not None:
                visible[:, cut_prev - 10:] = False  # only his own pixels, not hers in front of him
            dx, dy = track_shift(frames_gray[t - 1], frames_gray[t], visible)
            off = (off[0] + dx, off[1] + dy)
            cur = cv2.dilate(shifted(tmpl, *off).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
            ys, xs = np.nonzero(cur)
            if xs.size:
                a0, a1 = max(0, xs.max() - 90), min(W, xs.max() + 20)
                cols = w[ys.min():ys.max() + 1, a0:a1].sum(0)
                cut = a0 + int(np.nonzero(cols <= cols.min() + 3)[0][-1])
                if cut_prev is not None:
                    cut = int(np.clip(cut, cut_prev - 15, cut_prev + 15))  # her edge moves smoothly
                part = cur & anyone
                part[:, cut:] = False
                if part.sum() > 2500:
                    w = w & ~part
                    mm = his_parts(others(w), w, part) | part
                else:
                    cut = None
        else:
            tmpl = None
        cut_prev = cut
        woman[t], man[t] = w, mm
        mx, my = np.nonzero(mm.any(0))[0], np.nonzero(mm.any(1))[0]
        if cut is not None:
            last = (cut, last[1])  # follow the cut; keep his foot line from when he stood apart
        elif mx.size:
            last = (int(mx[-1]), int(my[-1]))
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

    def matches(self, s, t):
        """Ratio-tested ORB matches s -> t as two (k, 2) point arrays at half resolution."""
        if (s, t) not in self.cache:
            a = b = np.zeros((0, 2), np.float32)
            if self.des[s] is not None and self.des[t] is not None and len(self.des[s]) > 10 and len(self.des[t]) > 10:
                pairs = self.bf.knnMatch(self.des[s], self.des[t], k=2)
                good = [m for m, n2 in (p for p in pairs if len(p) == 2) if m.distance < 0.75 * n2.distance]
                a = self.kp[s][[m.queryIdx for m in good]]
                b = self.kp[t][[m.trainIdx for m in good]]
            self.cache[(s, t)] = (a, b)
        return self.cache[(s, t)]

    def h(self, s, t, box=None):
        """Homography mapping frame s onto frame t (full resolution), or None.

        With box (y0, y1, x0, x1 in frame t) only features near it are used, so the fit follows the
        wall / floor right around the hole instead of the whole room; falls back to all features.
        """
        a, b = self.matches(s, t)
        sc = np.diag([2.0, 2.0, 1.0])
        for local in ((True, False) if box else (False,)):
            sel = np.ones(len(a), bool)
            if local:
                y0, y1, x0, x1 = (v / 2 for v in box)
                m = LOCAL_MARGIN / 2
                sel = (b[:, 0] > x0 - m) & (b[:, 0] < x1 + m) & (b[:, 1] > y0 - m) & (b[:, 1] < y1 + m)
            need = MIN_LOCAL if local else MIN_INLIERS
            if sel.sum() < need:
                continue
            hm, inl = cv2.findHomography(a[sel], b[sel], cv2.RANSAC, 2.0)
            if hm is not None and inl.sum() >= need:
                return sc @ hm @ np.linalg.inv(sc)
        return None


def late_box(t):
    """His box at frame t from LATE_KEYS (linear between keys), or None outside them."""
    keys = sorted(LATE_KEYS)
    if not keys[0] <= t <= keys[-1]:
        return None
    k1 = next(k for k in keys if k >= t)
    k0 = max(k for k in keys if k <= t)
    f = 0 if k1 == k0 else (t - k0) / (k1 - k0)
    x0, x1, y0, y1 = (int(round(a + (b - a) * f)) for a, b in zip(LATE_KEYS[k0], LATE_KEYS[k1]))
    return max(0, x0 - LATE_PAD), min(W, x1 + LATE_PAD), max(0, y0 - LATE_PAD), min(H, y1 + LATE_PAD)  # arms, blur


def grow(m):
    """His mask grown 12px all round and 70px further down: the matte misses dark feet and floor shadow."""
    g = cv2.dilate(m.astype(np.uint8), np.ones((25, 25), np.uint8))
    return cv2.dilate(g, np.ones((71, 9), np.uint8), anchor=(4, 70)).astype(bool)  # src(y - d): extends DOWN


def shifted(m, dx, dy):
    """m moved by (dx, dy) pixels, without wrap-around."""
    out = np.zeros_like(m)
    h, w = m.shape
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = m[ys, xs]
    return out


def find_shadows(frames, man, people):
    """His wall shadow is his own silhouette moved left (the light is to the right of him).

    For each frame the darkest left shift of his mask (vs. its surroundings) is searched at quarter
    resolution, the offsets are smoothed over time, and the shifted, grown silhouette is the shadow.
    """
    n, q = len(frames), 4
    offs = [None] * n
    for t in range(n):
        if man[t].sum() < 3000 or t >= HIDDEN_FROM:
            continue
        mq = cv2.resize(man[t].astype(np.uint8), (W // q, H // q), interpolation=cv2.INTER_NEAREST).astype(bool)
        pq = cv2.resize(cv2.dilate(people[t].astype(np.uint8), np.ones((9, 9), np.uint8)), (W // q, H // q),
                        interpolation=cv2.INTER_NEAREST).astype(bool)
        lum = cv2.resize(cv2.cvtColor(frames[t], cv2.COLOR_RGB2GRAY), (W // q, H // q)).astype(np.float32)
        xs = np.nonzero(mq.any(0))[0]
        best = (0.0, None)
        for dx in range(4, int(1.6 * (xs[-1] - xs[0])) + 10, 2):
            for dy in (-8, -4, 0, 4, 8):
                sm = shifted(mq, -dx, dy) & ~pq
                if sm.sum() < 0.35 * mq.sum():
                    continue
                ring = cv2.dilate(sm.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
                ring &= ~cv2.dilate(sm.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool) & ~pq
                if ring.sum() < 50:
                    continue
                score = lum[sm].mean() - lum[ring].mean()
                if score < best[0]:
                    best = (score, (dx * q, dy * q))
        if best[0] < -8:
            offs[t] = best[1]
    # smooth the offsets over time (median of the 9 neighbours that have one)
    sh = np.zeros((n, H, W), bool)
    for t in range(n):
        if offs[t] is None:
            continue
        nb = [offs[k] for k in range(max(0, t - 4), min(n, t + 5)) if offs[k] is not None]
        dx, dy = int(np.median([o[0] for o in nb])), int(np.median([o[1] for o in nb]))
        g = cv2.dilate(shifted(man[t], -dx, dy).astype(np.uint8), np.ones((41, 41), np.uint8)).astype(bool)
        sh[t] = g & ~people[t]
    found = sum(o is not None for o in offs)
    print(f"shadow found in {found} frames")
    return sh


def lift_shadow(img, zone):
    """Brighten what is still shadowed inside zone (he stands there in nearly every frame, so even the donors have it).

    The lit level is the brightest smoothed luminance along the same row nearby; the gain is computed on
    smoothed luminance, so the wall texture survives. Only applied inside the (feathered) shadow zone.
    """
    if not zone.any():
        return img
    lum = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32), (0, 0), 1.2)
    lit = cv2.GaussianBlur(cv2.dilate(lum, np.ones((1, 201), np.uint8)), (0, 0), 15)
    gain = cv2.GaussianBlur(np.clip(lit / np.maximum(lum, 1), 1, 1.8), (0, 0), 1.5)
    zone = cv2.dilate(zone.astype(np.uint8), np.ones((21, 21), np.uint8))  # cover the whole soft edge
    m = cv2.GaussianBlur(zone.astype(np.float32), (0, 0), 8)
    gain = 1 + (gain - 1) * m
    return np.clip(img * gain[..., None], 0, 255).astype(np.uint8)


def nan_percentile(stack, q):
    """np.nanpercentile(stack, q, axis=0) without its slowness: NaNs sort last, index by each pixel's valid count."""
    srt = np.sort(stack, axis=0)
    cnt = np.count_nonzero(~np.isnan(stack), axis=0)
    idx = np.clip(np.round((cnt - 1) * q / 100).astype(np.int64), 0, None)
    out = np.take_along_axis(srt, idx[None], axis=0)[0]
    out[cnt == 0] = np.nan
    return out


def background(t, box, donors, frames, excl, al, tgt, ring, hole):
    """Median of the MAX_DONORS aligned donor frames that see most of the hole (NaN where none sees it)."""
    y0, y1, x0, x1 = box
    rh, rw = y1 - y0, x1 - x0
    samples = []
    for s in donors:
        if not 0 <= s < len(frames) or s == t:
            continue
        hm = al.h(s, t, box)
        if hm is None:
            if t in DEBUG:
                print(f"  t{t} s{s}: no homography")
            continue
        shift = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]], np.float64) @ hm
        img = cv2.warpPerspective(frames[s], shift, (rw, rh), flags=cv2.INTER_LINEAR).astype(np.float32)
        bad = cv2.warpPerspective(excl[s].astype(np.uint8), shift, (rw, rh), flags=cv2.INTER_NEAREST,
                                  borderMode=cv2.BORDER_CONSTANT, borderValue=1).astype(bool)
        both = ring & ~bad
        if both.sum() < 500:
            continue
        gain = np.median(tgt[both] + 1, axis=0) / np.median(img[both] + 1, axis=0)
        img *= np.clip(gain, 0.85, 1.18)
        err = np.abs(img[both] - tgt[both]).mean()
        if t in DEBUG:
            print(f"  t{t} s{s}: err {err:.1f} gain {np.round(gain, 2)} covers {np.count_nonzero(hole & ~bad)} of {hole.sum()}")
        if err > MAX_ERR:
            continue
        img[bad] = np.nan
        samples.append((np.count_nonzero(hole & ~bad), img))
    samples = [img for cov, img in sorted(samples, key=lambda x: -x[0])[:MAX_DONORS] if cov > 0]
    if not samples:
        return np.full_like(tgt, np.nan), 0
    # shadows (his and hers) only ever darken a donor, so take a bright-leaning percentile, not the median
    return nan_percentile(np.stack(samples), BG_PERCENTILE), len(samples)


def main():
    frames = read_raw(ROOT / "source.mp4", "null", "rgb24", 3)
    alpha = read_raw(ROOT / "work_matte.mov", "alphaextract", "gray", 1)
    half = [read_raw(ROOT / f"work_matte_{side}.mov", "alphaextract", "gray", 1, W // 2) for side in ("left", "right")]
    n = min(len(frames), len(alpha), *(len(x) for x in half))
    frames = frames[:n]
    print(f"{n} frames")
    gray = np.stack([cv2.cvtColor(f, cv2.COLOR_RGB2GRAY) for f in frames])
    woman, man = split_people(alpha[:n], half[0][:n], half[1][:n], gray)
    del gray
    del alpha, half
    people = woman | man
    al = Aligner(frames, people)
    print("features done")
    excl = np.zeros((n, H, W), bool)  # donor pixels never to borrow: anyone (grown) and his shadow
    for t in range(n):
        excl[t] = cv2.dilate(people[t].astype(np.uint8), np.ones((31, 31), np.uint8)).astype(bool)

    # he reappears small and blurred at the right edge, which no matte catches: boxes keyed by eye, minus her
    for t in range(n):
        box = late_box(t)
        if box:
            x0, x1, y0, y1 = box
            m = np.zeros((H, W), bool)
            m[y0:y1, x0:x1] = True
            man[t] = m & ~cv2.dilate(woman[t].astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    people = woman | man
    shadow = find_shadows(frames, man, people)
    for t in range(n):
        excl[t] = (cv2.dilate(woman[t].astype(np.uint8), np.ones((31, 31), np.uint8)).astype(bool)
                   | cv2.dilate(grow(man[t]).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
                   # only the core of his modelled shadow: the bright percentile rejects the rest
                   | cv2.erode(shadow[t].astype(np.uint8), np.ones((21, 21), np.uint8)).astype(bool))

    patches = {}  # t -> (y0, x0, patch): only the edited regions, the frames stay untouched as donors
    stats = []
    preview = "--preview" in sys.argv
    todo = list(range(0, n, 24)) + [454, 466, 478, 490] if preview else range(n)
    if DEBUG:
        todo = DEBUG
    for t in todo:
        mdil = grow(man[t])
        hole = (mdil | shadow[t]) & ~woman[t]
        if hole.sum() < 400:
            continue
        ys, xs = np.nonzero(hole)
        mh = ys.max() - ys.min()
        # the box also covers where any of his shadow can fall (left of him, light from the right)
        y0, y1 = max(0, ys.min() - 60), min(H, ys.max() + 140)
        x0, x1 = max(0, xs.min() - int(0.9 * mh) - 60), min(W, xs.max() + 60)
        box = (y0, y1, x0, x1)
        tgt = frames[t, y0:y1, x0:x1].astype(np.float32)
        ring = ~excl[t][y0:y1, x0:x1]
        # every 4th frame of the clip, nearest first; background() keeps the ones that see most of the hole
        donors = sorted(range(t % 4 + 2, n, 4), key=lambda s: abs(s - t))
        hole = hole[y0:y1, x0:x1]
        bg, k = background(t, box, donors, frames, excl, al, tgt, ring, hole)
        have = ~np.isnan(bg[..., 0])
        # whatever of his shadow the silhouette model missed: clearly darker than the clean background
        wnear = cv2.dilate(woman[t][y0:y1, x0:x1].astype(np.uint8), np.ones((41, 41), np.uint8)).astype(bool)
        lum = np.float32([0.3, 0.59, 0.11])
        dark = have & ~wnear & (np.nan_to_num(bg) @ lum - tgt @ lum > SHADOW_DROP)
        dark = cv2.morphologyEx(dark.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
        kk, lab, st, _ = cv2.connectedComponentsWithStats(dark, 8)
        touch = cv2.dilate(hole.astype(np.uint8), np.ones((61, 61), np.uint8)).astype(bool)
        keep = [i for i in range(1, kk) if st[i, cv2.CC_STAT_AREA] > 800 and (touch & (lab == i)).any()]
        hole |= np.isin(lab, keep)
        hole = cv2.dilate(hole.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool) & ~woman[t][y0:y1, x0:x1]
        fill8 = np.clip(np.where(have[..., None], bg, tgt), 0, 255).astype(np.uint8)
        left = hole & ~have
        if left.any():
            fill8 = cv2.inpaint(fill8, left.astype(np.uint8), 9, cv2.INPAINT_TELEA)
        fill8 = lift_shadow(fill8, shadow[t][y0:y1, x0:x1] & hole)
        a = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 4)
        a *= ~cv2.dilate(woman[t][y0:y1, x0:x1].astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        a = a[..., None]
        patches[t] = (y0, x0, np.clip(fill8 * a + tgt * (1 - a), 0, 255).astype(np.uint8))
        if DEBUG and t in DEBUG:
            vis = [tgt.astype(np.uint8), np.nan_to_num(bg).astype(np.uint8), patches[t][2]]
            masks = np.zeros_like(tgt, dtype=np.uint8)
            masks[..., 0] = hole * 255
            masks[..., 1] = have * 255
            masks[..., 2] = np.isin(lab, keep) * 255
            cv2.imwrite(str(ROOT / f"work_dbg_{t:03d}.jpg"), cv2.cvtColor(np.hstack(vis + [masks]), cv2.COLOR_RGB2BGR))
        stats.append((t, k, int(hole.sum()), int(left.sum())))
        if t % 50 == 0 or preview:
            print(f"frame {t}: {k} donors, hole {hole.sum()} px, inpainted {left.sum()} px")

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
