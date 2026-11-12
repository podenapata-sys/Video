#!/usr/bin/env python3
"""Reel Kit: turn talking-head clips + a script into an effects-showcase Reel (HyperFrames, 1080x1920).

  python3 kits/reel-kit/kit/reel.py new    videos/my-reel        # scaffold a project (copy clips into media/clips/)
  python3 kits/reel-kit/kit/reel.py cut    videos/my-reel        # silence jump-cuts -> timeline.json, media/voice.wav
  python3 kits/reel-kit/kit/reel.py words  videos/my-reel        # whisper word times, aligned to YOUR script -> words.json
  python3 kits/reel-kit/kit/reel.py build  videos/my-reel        # reel.json effects -> index.html, sfx.json
  python3 kits/reel-kit/kit/reel.py mix    videos/my-reel        # voice + ducked music + SFX -> media/mix.wav (-14 LUFS)
  python3 kits/reel-kit/kit/reel.py render videos/my-reel        # check + render + mux -> out/<name>.mp4
  python3 kits/reel-kit/kit/reel.py all    videos/my-reel        # cut, words, build, mix, render
  python3 kits/reel-kit/kit/reel.py words  videos/my-reel --list # print the words to anchor effects on

Everything the video says and shows lives in the project's reel.json (see README.md and examples/).
"""
import difflib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT / "kit"))
import fx  # noqa: E402

SR = 48000
HF = "hyperframes@0.9.23"


def run(cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd)[:160])
    return subprocess.run(cmd, check=True, **kw)


def dec(p, ch=1):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vn", "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).copy()
    return a if ch == 1 else a.reshape(-1, ch)


def load(proj):
    return json.loads((proj / "reel.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ new
def cmd_new(proj):
    if (proj / "reel.json").exists():
        sys.exit(f"{proj}/reel.json exists already")
    proj.mkdir(parents=True, exist_ok=True)
    for f in (KIT / "template").iterdir():
        shutil.copy(f, proj / f.name)
    pj = proj / "package.json"
    pj.write_text(pj.read_text().replace("REEL_NAME", proj.name))
    (proj / "meta.json").write_text(json.dumps({"id": proj.name, "name": proj.name}, indent=2))
    m = proj / "media"
    for sub in ("clips", "music", "screens"):
        (m / sub).mkdir(parents=True, exist_ok=True)
    for sub in ("fonts", "sfx", "logo"):
        shutil.copytree(KIT / "assets" / sub, m / sub, dirs_exist_ok=True)
    shutil.copy(KIT / "assets" / "gsap.min.js", m / "gsap.min.js")
    shutil.copy(KIT / "examples" / "starter.reel.json", proj / "reel.json")
    print(f"created {proj}\n  1. put one clip per section in media/clips/ (pt1.mp4 ...) and music in media/music/bgm.wav"
          f"\n  2. edit reel.json: sections (clip + script), panel, effects, end card\n  3. python3 {KIT}/kit/reel.py all {proj}")


# ------------------------------------------------------------------ cut
def silences(a, d=0.12, noise=-38):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                        f"silencedetect=noise={noise}dB:d={d}", "-f", "null", "-"], input=a.tobytes(), capture_output=True)
    e = p.stderr.decode()
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", e)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", e)]
    return list(zip(st, en + [len(a) / SR] * (len(st) - len(en))))


def cmd_cut(proj):
    cfg = load(proj)
    c = {"pause": 0.30, "pad": 0.06, "lead": 0.05, "tail": 0.15, "noise_db": -38, "end_hold": 1.1, "end_card": 5.0, **cfg.get("cut", {})}
    t, segments, sections, voice = 0.0, [], [], []
    for n, sec in enumerate(cfg["sections"], 1):
        src = sec["clip"]
        a = dec(proj / src)
        dur = len(a) / SR
        start, end, inner = 0.0, dur, []
        for s, e in silences(a, noise=c["noise_db"]):
            if s < 0.02:
                start = e
            elif e >= dur - 0.02:
                end = s
            else:
                inner.append((s, e))
        if "trim" in sec:                       # optional manual [in, out] in source seconds
            start, end = max(start, sec["trim"][0]), min(end, sec["trim"][1])
            inner = [(s, e) for s, e in inner if s > start and e < end]
        segs, cur = [], max(0.0, start - c["lead"])
        for s, e in inner:
            if e - s >= c["pause"]:
                segs.append((cur, s + c["pad"]))
                cur = e - c["pad"]
        segs.append((cur, min(dur, end + c["tail"])))
        s0, sa = t, []
        for i, (s, e) in enumerate(segs):
            seg = a[int(s * SR):int(e * SR)].copy()
            f = int(0.006 * SR)
            seg[:f] *= np.linspace(0, 1, f)
            seg[-f:] *= np.linspace(1, 0, f)
            sa.append(seg)
            segments.append({"clip": n, "src": src, "seg": i, "src_in": round(s, 3), "src_out": round(e, 3), "t": round(t, 3), "dur": round(e - s, 3)})
            t += e - s
        sa = np.concatenate(sa)
        import soundfile as sf
        sf.write(proj / "media" / f"sec{n}.wav", sa, SR)
        voice.append(sa)
        print(f"  section {n}: {s0:6.2f}-{t:6.2f}  {len(segs)} segment(s), kept {t - s0:.2f}s of {dur:.2f}s")
        sections.append({"n": n, "start": round(s0, 3), "end": round(t, 3)})
    total = round(t + c["end_hold"] + c["end_card"], 3)
    v = np.concatenate(voice)
    v = np.concatenate([v, np.zeros(int((total - t) * SR) + 10, np.float32)])[:int(round(total * SR))]
    import soundfile as sf
    sf.write(proj / "media" / "voice.wav", np.stack([v, v], 1), SR)
    (proj / "timeline.json").write_text(json.dumps({"segments": segments, "sections": sections, "speech_end": round(t, 3),
                                                    "blow_at": round(t, 3), "card_at": round(t + c["end_hold"], 3), "total": total}, indent=1))
    print(f"speech {t:.2f}s, end card {t + c['end_hold']:.2f}-{total:.2f}s, {len(segments)} cuts")


# ------------------------------------------------------------------ words
PUNCT = re.compile(r"[,.।?!:;—\-\"'“”]")


def norm(w):
    return PUNCT.sub("", w).strip().lower()


def align(script_words, asr):
    sw, aw = [norm(w) for w in script_words], [norm(x["word"]) for x in asr]
    sm = difflib.SequenceMatcher(None, " ".join(sw), " ".join(aw), autojunk=False)
    a_idx = []
    for i, w in enumerate(aw):
        a_idx += [i] * (len(w) + 1)
    s_starts, pos = [], 0
    for w in sw:
        s_starts.append(pos)
        pos += len(w) + 1
    cmap = {a + k: b + k for a, b, size in sm.get_matching_blocks() for k in range(size)}
    times = []
    for i, w in enumerate(sw):
        hits = [a_idx[cmap[c]] for c in range(s_starts[i], s_starts[i] + max(1, len(w))) if c in cmap and cmap[c] < len(a_idx)]
        times.append((asr[min(hits)]["start"], asr[max(hits)]["end"]) if hits else None)
    n, i = len(times), 0
    while i < n:
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < n and times[j] is None:
            j += 1
        t0 = times[i - 1][1] if i > 0 else (asr[0]["start"] if asr else 0.0)
        t1 = times[j][0] if j < n else (asr[-1]["end"] if asr else t0 + 0.4 * (j - i))
        wts = [max(1, len(sw[k])) for k in range(i, j)]
        acc = t0
        for k, wt in zip(range(i, j), wts):
            d = (t1 - t0) * wt / sum(wts)
            times[k] = (acc, acc + d)
            acc += d
        i = j
    out, prev = [], 0.0
    for s, e in times:
        s = max(s, prev)
        out.append((round(s, 3), round(max(e, s + 0.05), 3)))
        prev = s
    return out


def refine(words):
    """Split runs of script words that landed on the same whisper word, by character length."""
    out, i = [dict(w) for w in words], 0
    while i < len(out):
        j = i
        while j + 1 < len(out) and out[j + 1]["section"] == out[i]["section"] and abs(out[j + 1]["start"] - out[i]["start"]) < 0.06:
            j += 1
        nxt = out[j + 1]["start"] if j + 1 < len(out) and out[j + 1]["section"] == out[i]["section"] else max(w["end"] for w in out[i:j + 1])
        span_end = max(nxt, max(w["end"] for w in out[i:j + 1]))
        if j > i or out[i]["end"] - out[i]["start"] < 0.1:
            wts = [max(1, len(norm(w["text"]))) for w in out[i:j + 1]]
            acc = out[i]["start"]
            for k, wt in zip(range(i, j + 1), wts):
                d = (span_end - out[i]["start"]) * wt / sum(wts)
                out[k]["start"], out[k]["end"] = round(acc, 3), round(acc + d, 3)
                acc += d
        i = j + 1
    return out


def cmd_words(proj, listing=False):
    if listing:
        for w in json.loads((proj / "words.json").read_text(encoding="utf-8")):
            print(f"  s{w['section']}:{w['text']:<14} {w['start']:6.2f}")
        return
    import whisper
    cfg = load(proj)
    tl = json.loads((proj / "timeline.json").read_text())
    model = whisper.load_model(cfg.get("whisper_model", "medium"))
    words, report = [], []
    for sec, sc in zip(tl["sections"], cfg["sections"]):
        n = sec["n"]
        res = model.transcribe(str(proj / "media" / f"sec{n}.wav"), language=cfg.get("lang", "bn"), word_timestamps=True, fp16=False,
                               initial_prompt=sc["script"], condition_on_previous_text=False)
        asr = [w for seg in res["segments"] for w in seg.get("words", [])]
        report.append({"section": n, "whisper_text": res["text"].strip()})
        sw = sc["script"].split()
        for k, (w, (s, e)) in enumerate(zip(sw, align(sw, asr))):
            words.append({"section": n, "i": k, "text": w, "start": round(sec["start"] + s, 3), "end": round(sec["start"] + e, 3)})
        print(f"  S{n} heard: {res['text'].strip()}")
    words = refine(words)
    (proj / "words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    (proj / "out").mkdir(exist_ok=True)
    (proj / "out" / "whisper_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"words.json: {len(words)} words. Anchor list: reel.py words {proj} --list")


# ------------------------------------------------------------------ build
def cmd_build(proj):
    cfg = load(proj)
    tl = json.loads((proj / "timeline.json").read_text())
    words = json.loads((proj / "words.json").read_text(encoding="utf-8"))
    r = fx.Reel(cfg, tl, words, proj)
    cams = fx.presenter(r, **cfg.get("presenter", {}))
    for e in cfg.get("effects", []):
        e = dict(e)
        name = e.pop("fx")
        if name not in fx.EFFECTS:
            sys.exit(f"unknown effect {name!r}; available: {', '.join(sorted(fx.EFFECTS))}")
        e.pop("note", None)
        fx.EFFECTS[name](r, **e)
    if "panel" in cfg:
        fx.panel(r, **cfg["panel"])
    caps = fx.subtitles(r, **cfg.get("subtitles", {}))
    if "end_card" in cfg:
        fx.end_card(r, **cfg["end_card"])
    (proj / "index.html").write_text(fx.page(r, cams, caps, cfg.get("title", proj.name)), encoding="utf-8")
    (proj / "sfx.json").write_text(json.dumps(sorted(r.sfx, key=lambda x: x["t"]), indent=1))
    print(f"built index.html {r.total:.2f}s, {len(r.segs)} cuts, {len(caps)} subtitle chunks, {len(r.sfx)} sfx, "
          f"{len(cfg.get('effects', []))} effects")
    if getattr(r, "np_html", None):
        make_newspaper(proj, r)


def make_newspaper(proj, r):
    """Pre-render the press_tear front page to media/np.png (a one-frame sub-project, snapshotted by the CLI)."""
    src, t = r.np_photo
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(proj / src), "-frames:v", "1", "-q:v", "2", str(proj / "media" / "np_photo.jpg")])
    d = proj / "np"
    d.mkdir(exist_ok=True)
    css = fx.BASE_CSS.format(**r.C) + r.css["press"]
    (d / "index.html").write_text(f"""<!doctype html><html lang="bn"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<title>np</title><style>{css}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="1" data-width="1080" data-height="1920">{r.np_html}</div>
<script src="media/gsap.min.js"></script><script>window.__timelines = window.__timelines || {{}}; window.__timelines["main"] = gsap.timeline({{ paused: true }});</script>
</body></html>""", encoding="utf-8")
    if not (d / "media").exists():
        (d / "media").symlink_to("../media")
    shutil.copy(proj / "hyperframes.json", d / "hyperframes.json")
    (d / "meta.json").write_text(json.dumps({"id": proj.name + "-np", "name": "newspaper"}))
    out = proj / "out" / "work" / "npsnap"
    shutil.rmtree(out, ignore_errors=True)
    run(["npx", "--yes", HF, "snapshot", ".", "--at", "0.5", "--no-end", "-o", str(out)], cwd=d, capture_output=True)
    shutil.copy(next(out.glob("frame-*.png")), proj / "media" / "np.png")
    print("  newspaper -> media/np.png")


# ------------------------------------------------------------------ mix
def cmd_mix(proj):
    import soundfile as sf
    cfg = load(proj)
    mc = {"file": "media/music/bgm.wav", "gain_db": -4, "sfx_gain": 0.6, **cfg.get("music", {})}
    tl = json.loads((proj / "timeline.json").read_text())
    total, md = tl["total"], proj / "media"
    N = int(round(total * SR))
    pad = lambda x: np.vstack([x[:N], np.zeros((max(0, N - len(x)), 2), np.float32)])
    voice = pad(dec(md / "voice.wav", 2))
    mix = voice.copy()
    if (proj / mc["file"]).exists():
        m = dec(proj / mc["file"], 2)
        xf, bed = int(2.0 * SR), m.copy()
        while len(bed) < N:
            r_ = np.linspace(0, np.pi / 2, xf)[:, None]
            bed = np.vstack([bed[:-xf], bed[-xf:] * np.cos(r_) + m[:xf] * np.sin(r_), m[xf:]])
        bed = bed[:N].copy()
        fi, fo = int(0.6 * SR), int(1.5 * SR)
        bed[:fi] *= np.linspace(0, 1, fi)[:, None]
        bed[-fo:] *= np.linspace(1, 0, fo)[:, None]
        sf.write(md / "bed_raw.wav", bed, SR)
        run(["ffmpeg", "-v", "error", "-y", "-i", str(md / "bed_raw.wav"), "-i", str(md / "voice.wav"), "-filter_complex",
             f"[0:a]volume={mc['gain_db']}dB[m];[1:a]volume=4[k];[m][k]sidechaincompress=threshold=0.015:ratio=10:attack=30:release=400:makeup=1[d]",
             "-map", "[d]", "-ar", str(SR), "-ac", "2", str(md / "bed.wav")])
        (md / "bed_raw.wav").unlink()
        mix += pad(dec(md / "bed.wav", 2))
    else:
        print(f"  (no music at {mc['file']})")
    fxs = np.zeros((N, 2), np.float32)
    for c in json.loads((proj / "sfx.json").read_text()):
        x = dec(md / "sfx" / f"{c['sfx']}.wav", 2)
        x = x / (np.abs(x).max() or 1.0) * c["gain"]
        o = int(round(c["t"] * SR))
        n = min(len(x), N - o)
        if n > 0:
            fxs[o:o + n] += x[:n]
    raw = md / "mix_raw.wav"
    sf.write(raw, mix + fxs * mc["sfx_gain"], SR, subtype="FLOAT")
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    mm = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    norm_ = (f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={mm['input_i']}:measured_TP={mm['input_tp']}:"
             f"measured_LRA={mm['input_lra']}:measured_thresh={mm['input_thresh']}:offset={mm['target_offset']}")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", f"{norm_},aresample={SR},apad=whole_len={N},atrim=end_sample={N}",
         "-ar", str(SR), "-ac", "2", str(md / "mix.wav")])
    raw.unlink()
    print(f"mix.wav {total:.2f}s at -14 LUFS")


# ------------------------------------------------------------------ render
def cmd_render(proj):
    cfg = load(proj)
    name = cfg.get("output", proj.name)
    chk = subprocess.run(["npx", "--yes", HF, "check"], cwd=proj, capture_output=True, text=True)
    print("\n".join(l for l in (chk.stdout + chk.stderr).splitlines() if "error(s)" in l or "Check" in l or "✗" in l))
    if chk.returncode != 0:
        sys.exit("check failed: fix errors (npm run check) before rendering")
    (proj / "out").mkdir(exist_ok=True)
    run(["npx", "--yes", HF, "render", ".", "-o", "out/render_raw.mp4", "--fps", "30", "--quality", "delivery"], cwd=proj, capture_output=True)
    final = proj / "out" / f"{name}.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(proj / "out" / "render_raw.mp4"), "-i", str(proj / "media" / "mix.wav"), "-map", "0:v", "-map", "1:a",
         "-c:v", "libx264", "-crf", "19", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
         "-shortest", str(final)])
    sheet = proj / "out" / f"{name}_sheet.jpg"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(final), "-vf", "fps=1/2,scale=216:384,tile=7x3", "-frames:v", "1", str(sheet)])
    print(f"done: {final}  ({final.stat().st_size / 1e6:.1f} MB), contact sheet {sheet}")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, proj = sys.argv[1], Path(sys.argv[2]).resolve()
    steps = {"new": cmd_new, "cut": cmd_cut, "build": cmd_build, "mix": cmd_mix, "render": cmd_render}
    if cmd == "words":
        cmd_words(proj, "--list" in sys.argv)
    elif cmd == "all":
        for s in ("cut", "words", "build", "mix", "render"):
            print(f"== {s}")
            cmd_words(proj) if s == "words" else steps[s](proj)
    elif cmd in steps:
        steps[cmd](proj)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
