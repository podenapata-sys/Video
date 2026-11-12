"""Reel Kit effects library: seek-safe HyperFrames/GSAP effects for 9:16 talking-head Reels.

Every effect is a function  fx_<name>(r, **params)  that appends HTML, GSAP calls, CSS and SFX cues to a Reel `r`.
Times are ANCHORS (see Reel.t):  2.5 | "s2" | "s2:end" | "s2:দাম" | "s2:সমস্যা#1" | "s2:এআই+0.3" | "blow" | "card"
so effects land on spoken words (whisper word times from words.json) and survive re-cuts.

Rules baked in (brand/futurestack/DESIGN.md, Social & Video; videos/style-ref/EFFECTS_REPORT.md):
  - cards sit on the chest band (bottom-anchored at y=1400) or above the head (y<330); the face stays clear
  - full-screen takeovers (letter_dive, press_tear, impact) are short; the panel steps aside, subtitles wait
  - one SFX per effect, on its first frame
"""
import json
import math

BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
W, H = 1080, 1920
CHEST = 520                      # cards are bottom-anchored this far from the frame bottom (chest band, above subtitles)

DEFAULT_COLORS = dict(BG="#0B0D11", SURF="#12151A", SURF2="#1D2128", BORDER="#2E343E", TEXT="#F1F3F6", MUTED="#A9B0BC",
                      BLUE="#5683FF", BLUE_HI="#8AA9FF", GREEN="#3CC48F", RED="#F26B5E", AMBER="#F0A23B", WA="#25D366",
                      PAPER="#F2EDE1", INK="#1B1712")


class Reel:
    def __init__(self, cfg, timeline, words, root):
        self.cfg, self.root = cfg, root
        self.segs, self.secs = timeline["segments"], {s["n"]: s for s in timeline["sections"]}
        self.total, self.blow, self.card = timeline["total"], timeline["blow_at"], timeline["card_at"]
        self.words = words
        self.C = {**DEFAULT_COLORS, **cfg.get("colors", {})}
        self.html, self.js, self.sfx, self.css = [], [], [], {}
        self.takeovers = []          # (t0, t1, kind) full-screen moments: panel hides, subtitles wait for "no_subs"
        self.uid = 0
        self.after_build = []        # callables run after index.html is written (e.g. pre-render the newspaper)

    # ---------------------------------------------------------------- time anchors
    def word(self, sec, text, nth=0):
        hits = [x for x in self.words if x["section"] == sec and x["text"].startswith(text)]
        if len(hits) <= nth:
            raise KeyError(f'word "{text}"#{nth} not found in section {sec}: '
                           + " ".join(x["text"] for x in self.words if x["section"] == sec))
        return hits[nth]["start"]

    def t(self, a):
        if isinstance(a, (int, float)):
            return float(a)
        s, off = str(a), 0.0
        for sign in ("+", "-"):
            i = s.rfind(sign)
            if i > 0 and s[i + 1:].replace(".", "", 1).isdigit():
                off = float(s[i + 1:]) * (1 if sign == "+" else -1)
                s = s[:i]
                break
        if s == "blow":
            return self.blow + off
        if s == "card":
            return self.card + off
        if s == "end":
            return self.total + off
        head, _, rest = s.partition(":")
        sec = int(head[1:])
        if not rest:
            return self.secs[sec]["start"] + off
        if rest == "end":
            return self.secs[sec]["end"] + off
        word, _, nth = rest.partition("#")
        return self.word(sec, word, int(nth or 0)) + off

    # ---------------------------------------------------------------- helpers
    def id(self, p):
        self.uid += 1
        return f"{p}{self.uid}"

    def cue(self, name, t, gain=0.5):
        self.sfx.append({"sfx": name, "t": round(t, 3), "gain": gain})

    def show(self, sel, t0, t1, fin=0.25, fout=0.2, frm="{autoAlpha:0, y:30}", to="{autoAlpha:1, y:0}"):
        self.js.append(f'tl.fromTo("{sel}", {frm}, {{...{to}, duration:{fin}, ease:"power3.out"}}, {t0:.3f});')
        self.js.append(f'tl.to("{sel}", {{autoAlpha:0, duration:{fout}, ease:"power1.in"}}, {t1 - fout:.3f});')

    def seg_at(self, t):
        for s in self.segs:
            if s["t"] - 1e-6 <= t < s["t"] + s["dur"] - 1e-6:
                return s
        return self.segs[-1]

    def live_video(self, vid, t0, t1, cls=""):
        """Muted <video> showing the presenter exactly as the main picture does over [t0, t1] (clamped to one segment)."""
        s = self.seg_at(t0)
        t1 = min(t1, s["t"] + s["dur"])
        ms = s["src_in"] + (t0 - s["t"])
        return (f'<video id="{vid}" class="clip {cls}" src="{s["src"]}" muted playsinline data-start="{t0:.3f}" '
                f'data-duration="{t1 - t0:.3f}" data-media-start="{ms:.3f}" data-track-index="9"></video>')

    def add_css(self, key, css):
        self.css.setdefault(key, css.format(**self.C))


# ==================================================================== EFFECTS
def fx_title_pills(r, lines, at="s1+0.05", until="s2-0.05", sub=None):
    """Hook title: white pill(s) top-centre, optional blue sub-pill (brand line)."""
    r.add_css("title", """
.titlepills {{ position:absolute; top:150px; left:0; width:100%; display:flex; flex-direction:column; align-items:center; gap:14px; z-index:30; visibility:hidden; }}
.tp {{ background:#fff; color:{BG}; font-weight:700; font-size:54px; padding:10px 34px 4px; border-radius:22px; box-shadow:0 10px 30px -10px rgba(0,0,0,.6); }}
.tp.en {{ font-family:"Sora"; font-weight:700; font-size:34px; padding:10px 28px; background:{BLUE}; color:{BG}; }}""")
    i = r.id("title")
    pills = "".join(f'<span class="tp">{x}</span>' for x in ([lines] if isinstance(lines, str) else lines))
    if sub:
        pills += f'<span class="tp en">{sub}</span>'
    r.html.append(f'<div class="titlepills" id="{i}">{pills}</div>')
    r.show(f"#{i}", r.t(at), r.t(until), fin=0.3)


def fx_cursor_select(r, at=0.1, click=0.9, out=2.3, tag="Future Stack", box=(330, 400, 420, 520), label="1080 × 1920"):
    """Design-tool cursor flies in, clicks, a selection box with handles frames the presenter."""
    r.add_css("cursor", """
.cursor {{ position:absolute; left:0; top:0; z-index:40; visibility:hidden; display:flex; align-items:flex-start; gap:6px; }}
.ctag {{ margin-top:46px; background:{BLUE}; color:{BG}; font-family:"Sora"; font-weight:700; font-size:28px; padding:6px 14px; border-radius:8px; }}
.selbox {{ position:absolute; border:3px solid {BLUE_HI}; z-index:35; visibility:hidden; }}
.selbox .h {{ position:absolute; width:18px; height:18px; background:#fff; border:3px solid {BLUE}; }}
.h.tl {{ left:-11px; top:-11px; }} .h.tr {{ right:-11px; top:-11px; }} .h.bl {{ left:-11px; bottom:-11px; }} .h.br {{ right:-11px; bottom:-11px; }}
.dim {{ position:absolute; left:50%; top:-58px; translate:-50% 0; background:{BLUE}; color:{BG}; font-family:"Sora"; font-weight:700; font-size:28px; padding:6px 14px; border-radius:8px; white-space:nowrap; }}""")
    c, b = r.id("cur"), r.id("sel")
    t0, tc, to = r.t(at), r.t(click), r.t(out)
    l, tp, w, h = box
    r.html.append(f'''<div class="cursor" id="{c}"><svg viewBox="0 0 24 24" width="64" height="64"><path d="M4 2l16 9-7 2-3 7z" fill="#fff" stroke="#0B0D11" stroke-width="1.5"/></svg>
<span class="ctag">{tag}</span></div>
<div class="selbox" id="{b}" style="left:{l}px;top:{tp}px;width:{w}px;height:{h}px"><i class="h tl"></i><i class="h tr"></i><i class="h bl"></i><i class="h br"></i><span class="dim">{label}</span></div>''')
    r.js.append(f'tl.fromTo("#{c}", {{autoAlpha:0, x:880, y:1500}}, {{autoAlpha:1, x:{l + w - 50}, y:{tp + h - 20}, duration:{tc - t0 - 0.1:.2f}, ease:"power2.inOut"}}, {t0:.3f});')
    r.js.append(f'tl.to("#{c}", {{scale:0.85, duration:0.08, yoyo:true, repeat:1}}, {tc:.3f});')
    r.js.append(f'tl.fromTo("#{b}", {{autoAlpha:0, scale:0.9}}, {{autoAlpha:1, scale:1, duration:0.25, ease:"back.out(2)"}}, {tc + 0.05:.3f});')
    r.js.append(f'tl.to("#{c}", {{x:{l + w + 10}, y:{tp + h + 260}, autoAlpha:0, duration:0.6, ease:"power2.in"}}, {to:.3f});')
    r.js.append(f'tl.to("#{b}", {{autoAlpha:0, duration:0.25}}, {to + 0.3:.3f});')
    r.cue("click_ui", tc, 0.55)


def fx_number_tiles(r, at, until, items):
    """Numbered problem/benefit tiles (icon + big numeral + label) pop in on the chest band, one by one."""
    r.add_css("ptile", """
.ptile {{ position:absolute; top:1040px; width:290px; height:270px; border-radius:28px; background:#fff; color:{BG}; z-index:30; visibility:hidden;
  display:flex; flex-direction:column; align-items:center; justify-content:center; box-shadow:0 22px 50px -14px rgba(0,0,0,.8); border-bottom:8px solid {BLUE}; }}
.ptile b {{ font-size:130px; font-weight:700; line-height:1; color:{BLUE}; margin-top:10px; }}
.ptile .plab {{ font-size:32px; font-weight:700; margin-top:4px; }}
.ptile .pico {{ position:absolute; left:18px; top:14px; font-size:40px; }}""")
    t0, t1, n = r.t(at), r.t(until), len(items)
    gap, wid = 30, 290
    x0 = (W - (n * wid + (n - 1) * gap)) // 2
    rot = [-8, 0, 8, -4, 4]
    for i, (ico, lab) in enumerate(items):
        k = r.id("pt")
        r.html.append(f'<div class="ptile" id="{k}" style="left:{x0 + i * (wid + gap)}px"><span class="pico">{ico}</span><b>{str(i + 1).translate(BN)}</b><span class="plab">{lab}</span></div>')
        r.js.append(f'tl.fromTo("#{k}", {{autoAlpha:0, scale:0.3, y:80, rotation:{rot[i % 5]}}}, {{autoAlpha:1, scale:1, y:0, rotation:0, duration:0.32, ease:"back.out(2.2)"}}, {t0 + i * 0.14:.3f});')
        r.js.append(f'tl.to("#{k}", {{autoAlpha:0, y:-30, duration:0.15}}, {t1 - 0.15:.3f});')
        r.cue("pop_notification", t0 + i * 0.14, 0.32)
    r.cue("whoosh_fast", t0 - 0.05, 0.35)


def fx_letter_dive(r, at, text, glitch=True):
    """Section opener: paper card with a giant numeral cut out (footage shows through), then dive through it. ~0.66 s."""
    r.add_css("dive", """
.dive {{ position:absolute; inset:0; z-index:47; visibility:hidden; background:{PAPER}; mix-blend-mode:screen; display:flex; flex-direction:column;
  align-items:center; justify-content:center; transform-origin:46% 46%; }}
.dive span {{ font-size:820px; font-weight:700; line-height:.9; color:#000; letter-spacing:-.04em; }}""")
    t = r.t(at)
    k = r.id("dv")
    r.html.append(f'<div class="dive" id="{k}" data-layout-ignore><span>{text}</span></div>')
    r.js.append(f'tl.fromTo("#{k}", {{autoAlpha:1, scale:1}}, {{scale:1.08, duration:0.32, ease:"none", immediateRender:false}}, {t:.3f});')
    r.js.append(f'tl.to("#{k}", {{scale:7, autoAlpha:0, duration:0.34, ease:"power3.in"}}, {t + 0.32:.3f});')
    r.cue("whoosh_fast", t + 0.3, 0.5)
    r.takeovers.append((t, t + 0.66, "panel_above"))
    if glitch:
        fx_glitch(r, t + 0.62, gain=0.25)


def fx_glitch(r, at, gain=0.4):
    """RGB scanline flash, ~0.15 s. Transition accent."""
    r.add_css("glitch", """
#glitch {{ position:absolute; inset:0; z-index:60; opacity:0; pointer-events:none; mix-blend-mode:screen;
  background:repeating-linear-gradient(0deg, rgba(86,131,255,.55) 0 6px, rgba(0,0,0,0) 6px 22px), linear-gradient(90deg, rgba(255,40,80,.35), rgba(60,196,255,.35)); }}""")
    r.glitch = True
    t = r.t(at)
    r.js.append(f'tl.to("#glitch", {{opacity:0.8, x:-24, duration:0.04, ease:"none"}}, {t:.3f});')
    r.js.append(f'tl.to("#glitch", {{opacity:0, x:0, duration:0.12, ease:"steps(3)"}}, {t + 0.06:.3f});')
    r.cue("glitch_digital", t, gain)


CARD_CSS = """
.card {{ position:absolute; left:64px; bottom:%dpx; width:640px; z-index:30; visibility:hidden; background:rgba(18,21,26,.94); border:1px solid {BORDER};
  border-radius:20px; padding:22px; box-shadow:0 24px 60px -20px rgba(0,0,0,.75); }}
.av {{ display:inline-block; width:44px; height:44px; border-radius:50%%; background:linear-gradient(135deg,#3BB4F2,#5683FF); }}
.av.s1 {{ background:linear-gradient(135deg,#F0A23B,#F26B5E); }} .av.s2 {{ background:linear-gradient(135deg,#3CC48F,#3BB4F2); }}
.av.s3 {{ background:linear-gradient(135deg,#8AA9FF,#5683FF); }} .av.s4 {{ background:linear-gradient(135deg,#A9B0BC,#434A57); }}
.caret {{ display:inline-block; width:3px; height:36px; background:{BLUE_HI}; margin-left:4px; }}""" % CHEST


def fx_chat(r, at, until, typed, keys=(), customer=None, seen=None, left=None, bot=None, page="আপনার পেজ"):
    """Messenger card on the chest band: a question is typed with predict-keys, sent, left on Seen, customer leaves,
    then the AI bot answers. Each step is optional: customer/seen/left/bot = {"at": anchor, "text": "...", "small": "..."}."""
    r.add_css("card", CARD_CSS)
    r.add_css("chat", """
.chead {{ display:flex; align-items:center; gap:12px; font-size:28px; font-weight:600; color:{MUTED}; margin-bottom:10px; }}
.chead .dot {{ width:12px; height:12px; border-radius:50%; background:{GREEN}; margin-left:auto; }}
.bubble {{ font-family:"Sora","Hind Siliguri",sans-serif; font-size:30px; padding:10px 20px; border-radius:20px; max-width:90%; margin-bottom:8px; visibility:hidden; display:none; }}
.bubble small {{ display:block; font-size:22px; opacity:.7; margin-top:4px; font-family:"Hind Siliguri"; }}
.bubble.cust {{ background:{SURF2}; }}
.bubble.bot {{ background:{BLUE}; color:{BG}; margin-left:auto; font-family:"Hind Siliguri"; font-weight:700; font-size:30px; }}
.seen {{ font-size:30px; color:{AMBER}; margin:0 0 10px 6px; visibility:hidden; display:none; }}
.left {{ font-size:30px; color:{RED}; font-weight:600; margin:0 0 10px 6px; visibility:hidden; display:none; }}
.keys {{ display:flex; gap:10px; margin:6px 0 10px; }}
.pk {{ font-family:"Sora"; font-size:26px; padding:8px 14px; border-radius:10px; background:{SURF2}; color:{MUTED}; }}
.pk.on {{ background:{BLUE}; color:{BG}; }}
.input {{ font-family:"Sora"; font-size:30px; background:{BG}; border:1px solid {BORDER}; border-radius:999px; padding:10px 22px; min-height:60px; display:flex; align-items:center; }}
.ch {{ visibility:hidden; }}""")
    k = r.id("chat")
    t0, t1 = r.t(at), r.t(until)
    chars = "".join(f'<span class="ch" id="{k}c{i}">{c if c != " " else "&nbsp;"}</span>' for i, c in enumerate(typed))
    sm = lambda d: f' <small>{d["small"]}</small>' if d and d.get("small") else ""
    keyhtml = "".join(f'<span class="pk{" on" if i == 0 else ""}">{x}</span>' for i, x in enumerate(keys))
    r.html.append(f'''<div class="card" id="{k}">
 <div class="chead"><i class="av"></i><span>{page}</span><span class="dot"></span></div>
 <div class="bubble cust" id="{k}cb">{(customer or {}).get("text", typed)}{sm(customer)}</div>
 <div class="seen" id="{k}se">{(seen or {}).get("text", "")}</div>
 <div class="left" id="{k}le">{(left or {}).get("text", "")}</div>
 <div class="bubble bot" id="{k}bo">{(bot or {}).get("text", "")}{sm(bot)}</div>
 <div class="keys" id="{k}ke">{keyhtml}</div>
 <div class="input" id="{k}in">{chars}<i class="caret"></i></div>
</div>''')
    r.show(f"#{k}", t0, t1, fin=0.3)
    tt = t0 + 0.13
    for i in range(len(typed)):
        r.js.append(f'tl.fromTo("#{k}c{i}", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.01}}, {tt + i * 0.075:.3f});')
    r.cue("typing_keys", tt, 0.35)
    if customer:
        ts = r.t(customer["at"])
        r.js.append(f'tl.set("#{k}in, #{k}ke", {{display:"none"}}, {ts:.3f}); tl.set("#{k}cb", {{display:"block"}}, {ts:.3f});')
        r.js.append(f'tl.fromTo("#{k}cb", {{autoAlpha:0, y:20}}, {{autoAlpha:1, y:0, duration:0.25, ease:"back.out(2)"}}, {ts:.3f});')
        r.cue("pop_notification", ts, 0.35)
    for d, sid, frm in ((seen, "se", "{autoAlpha:0}"), (left, "le", "{autoAlpha:0, x:-30}")):
        if d:
            ts = r.t(d["at"])
            r.js.append(f'tl.set("#{k}{sid}", {{display:"block"}}, {ts:.3f});')
            r.js.append(f'tl.fromTo("#{k}{sid}", {frm}, {{autoAlpha:1, x:0, duration:0.25, ease:"power3.out"}}, {ts:.3f});')
    if bot:
        tb = r.t(bot["at"])
        r.js.append(f'tl.set("#{k}se, #{k}le", {{display:"none"}}, {tb:.3f}); tl.set("#{k}bo", {{display:"block"}}, {tb:.3f});')
        r.js.append(f'tl.fromTo("#{k}bo", {{autoAlpha:0, scale:0.6, transformOrigin:"100% 100%"}}, {{autoAlpha:1, scale:1, duration:0.3, ease:"back.out(2.4)"}}, {tb:.3f});')
        r.cue("chime_success", tb, 0.45)


def fx_head_stack(r, chips, until, replace=False):
    """Chips drop in above the head (top-left), each on its word. chips=[{"at":..., "text":..., "style":"red|green"}].
    replace=True: each new chip replaces the previous one (state flip, e.g. red -> green)."""
    r.add_css("hstack", """
.hstack {{ position:absolute; left:70px; top:90px; width:640px; z-index:33; display:flex; flex-direction:column; align-items:flex-start; gap:12px; }}
.hchip {{ visibility:hidden; background:#fff; color:{BG}; font-weight:700; font-size:40px; padding:10px 26px 4px; border-radius:18px; box-shadow:0 14px 30px -10px rgba(0,0,0,.7); }}
.hchip.red {{ background:{RED}; color:#fff; }} .hchip.green {{ background:{GREEN}; color:{BG}; }}""")
    k = r.id("hs")
    r.html.append(f'<div class="hstack" id="{k}">' + "".join(
        f'<span class="hchip {c.get("style", "")}" id="{k}c{i}">{c["text"]}</span>' for i, c in enumerate(chips)) + '</div>')
    rots = (-4, 3, -2, 2)
    for i, c in enumerate(chips):
        t = r.t(c["at"])
        if replace and i > 0:
            r.js.append(f'tl.set("#{k}c{i - 1}", {{display:"none"}}, {t:.3f});')
            r.js.append(f'tl.fromTo("#{k}c{i}", {{autoAlpha:0, scale:0.4}}, {{autoAlpha:1, scale:1, duration:0.3, ease:"back.out(2.5)"}}, {t:.3f});')
        else:
            r.js.append(f'tl.fromTo("#{k}c{i}", {{autoAlpha:0, y:-90, rotation:{rots[i % 4]}}}, {{autoAlpha:1, y:0, duration:0.3, ease:"bounce.out"}}, {t:.3f});')
        r.cue("click_ui", t, 0.3)
    r.js.append(f'tl.to("#{k}", {{autoAlpha:0, y:-40, duration:0.15}}, {r.t(until) - 0.17:.3f});')


def fx_post_wall(r, at, until, title="আজ কেনেনি:", unit="জন", tag="কেনেনি", count_to=47, n=10):
    """Grid of customer tiles stamped with a tag, with a counter rolling up. Proof of volume (lost or won)."""
    r.add_css("card", CARD_CSS)
    r.add_css("wall", """
.wh {{ font-size:32px; font-weight:700; margin-bottom:14px; }} .wh b {{ color:{RED}; }}
.grid {{ display:grid; grid-template-columns:repeat(5,1fr); gap:10px; }}
.tile {{ background:{SURF2}; border-radius:14px; padding:10px 8px; display:flex; flex-direction:column; gap:8px; align-items:center; visibility:hidden; }}
.tile .ln {{ width:80%; height:10px; border-radius:6px; background:{BORDER}; }}
.tile .tag {{ font-size:26px; font-weight:600; color:{RED}; background:rgba(242,107,94,.14); padding:2px 10px 0; border-radius:8px; }}""")
    k = r.id("wall")
    t0, t1 = r.t(at), r.t(until)
    tiles = "".join(f'<div class="tile" id="{k}t{i}"><i class="av s{i % 5}"></i><span class="ln"></span><span class="tag">{tag}</span></div>' for i in range(n))
    r.html.append(f'<div class="card" id="{k}"><div class="wh">{title} <b id="{k}n">০</b> {unit}</div><div class="grid">{tiles}</div></div>')
    r.show(f"#{k}", t0, t1, fin=0.25)
    for i in range(n):
        r.js.append(f'tl.fromTo("#{k}t{i}", {{autoAlpha:0, scale:0.5}}, {{autoAlpha:1, scale:1, duration:0.2, ease:"back.out(2)"}}, {t0 + 0.25 + i * 0.07:.3f});')
    r.cue("pop_notification", t0 + 0.25, 0.35)
    steps = 8
    for s in range(1, steps + 1):
        val = round(count_to * (1 - (1 - s / steps) ** 2))
        r.js.append(f'tl.set("#{k}n", {{textContent:"{str(val).translate(BN)}"}}, {t0 + 0.3 + (s - 1) * 0.12:.3f});')


def fx_voice_note(r, at, until, text, delivered_at=None, length="০:০৬"):
    """Voice-note card on the chest band: animated waveform, auto-reminder text, "Delivered ✓✓" on a word."""
    r.add_css("card", CARD_CSS)
    r.add_css("vnote", """
.vrow {{ display:flex; align-items:center; gap:16px; }}
.play {{ width:64px; height:64px; border-radius:50%; background:{BLUE}; color:{BG}; display:flex; align-items:center; justify-content:center; font-size:30px; }}
.wave {{ display:flex; align-items:center; gap:5px; height:60px; flex:1; }}
.bar {{ width:8px; border-radius:4px; background:{BLUE_HI}; display:block; }}
.vt {{ font-family:"Sora"; font-size:28px; color:{MUTED}; }}
.vfoot {{ margin-top:14px; display:flex; flex-direction:column; gap:8px; font-size:30px; }}
.del {{ font-family:"Sora"; font-size:28px; color:{GREEN}; visibility:hidden; }}""")
    k = r.id("vn")
    t0, t1 = r.t(at), r.t(until)
    bars = "".join(f'<i class="bar" id="{k}b{i}" style="height:{14 + int(30 * abs(math.sin(i * 1.7)))}px"></i>' for i in range(26))
    r.html.append(f'''<div class="card" id="{k}"><div class="vrow"><span class="play">▶</span><div class="wave">{bars}</div><span class="vt">{length}</span></div>
<div class="vfoot"><span class="vl">{text}</span><span class="del" id="{k}d">Delivered ✓✓</span></div></div>''')
    r.show(f"#{k}", t0, t1, fin=0.3, frm="{autoAlpha:0, y:60, scale:0.9}", to="{autoAlpha:1, y:0, scale:1}")
    for i in range(26):
        r.js.append(f'tl.fromTo("#{k}b{i}", {{scaleY:0.35}}, {{scaleY:1, duration:0.18, ease:"sine.inOut", yoyo:true, repeat:{8 + i % 3}}}, {t0 + 0.25 + (i % 7) * 0.03:.3f});')
    r.cue("pop_notification", t0, 0.4)
    if delivered_at:
        td = r.t(delivered_at)
        r.js.append(f'tl.fromTo("#{k}d", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.2}}, {td:.3f});')
        r.cue("chime_success", td, 0.3)


def fx_press_tear(r, at, tear_at, masthead="দৈনিক ব্যবসা", dateline="ঢাকা · আজকের সংস্করণ", headline="", cols=("", ""), photo_offset=0.6):
    """Full-screen newspaper front page (halftone presenter photo), torn in two on a word. The page is pre-rendered to
    media/np.png (np/ sub-project, snapshotted automatically by `reel.py build`)."""
    r.add_css("press", """
#npwrap {{ position:absolute; inset:0; z-index:45; visibility:hidden; }}
.npL, .npR {{ position:absolute; inset:0; }}
.npL img, .npR img {{ position:absolute; inset:0; width:100%; height:100%; }}
.npL {{ clip-path:polygon(0 0, 52% 0, 47% 9%, 54% 18%, 46% 28%, 53% 38%, 47% 49%, 55% 60%, 46% 71%, 53% 82%, 47% 91%, 52% 100%, 0 100%); }}
.npR {{ clip-path:polygon(52% 0, 100% 0, 100% 100%, 52% 100%, 47% 91%, 53% 82%, 46% 71%, 55% 60%, 47% 49%, 53% 38%, 46% 28%, 54% 18%, 47% 9%); }}
.np {{ position:absolute; inset:0; background:{PAPER}; color:{INK}; padding:80px 64px; font-family:"Hind Siliguri"; }}
.mast {{ font-size:120px; font-weight:700; text-align:center; border-bottom:6px double {INK}; line-height:1.25; }}
.dline {{ font-size:28px; text-align:center; border-bottom:2px solid {INK}; padding:8px 0 4px; margin-bottom:26px; }}
.hl {{ font-size:72px; font-weight:700; line-height:1.18; text-align:center; margin-bottom:24px; }}
.photo {{ position:relative; height:760px; overflow:hidden; border:3px solid {INK}; }}
.photo img {{ position:absolute; width:100%; height:100%; object-fit:cover; object-position:50% 30%; filter:grayscale(1) contrast(1.9) brightness(1.05); }}
.photo .dots {{ position:absolute; inset:0; background:radial-gradient(circle, rgba(27,23,18,.35) 1.4px, transparent 1.6px) 0 0/7px 7px; mix-blend-mode:multiply; }}
.cols {{ display:grid; grid-template-columns:1fr 1fr; gap:28px; margin-top:24px; font-size:27px; line-height:1.45; }}""")
    t0, tt = r.t(at), r.t(tear_at)
    r.np_html = f'''<div class="np">
 <div class="mast">{masthead}</div><div class="dline">{dateline}</div>
 <div class="hl">{headline}</div>
 <div class="photo"><img src="media/np_photo.jpg" alt="" /><i class="dots"></i></div>
 <div class="cols"><p>{cols[0]}</p><p>{cols[1]}</p></div>
</div>'''
    s = r.seg_at(t0)
    r.np_photo = (s["src"], round(s["src_in"] + photo_offset, 3))
    r.html.append('<div id="npwrap"><div class="npL" id="npL"><img src="media/np.png" alt="" /></div><div class="npR" id="npR"><img src="media/np.png" alt="" /></div></div>')
    r.js.append(f'tl.fromTo("#npwrap", {{autoAlpha:0, scale:1.08}}, {{autoAlpha:1, scale:1, duration:0.22, ease:"power3.out"}}, {t0:.3f});')
    r.cue("paper_rustle", t0, 0.5)
    r.js.append(f'tl.to("#npL", {{xPercent:-75, rotation:-9, duration:0.55, ease:"power3.in"}}, {tt:.3f});')
    r.js.append(f'tl.to("#npR", {{xPercent:75, rotation:9, duration:0.55, ease:"power3.in"}}, {tt:.3f});')
    r.js.append(f'tl.set("#npwrap", {{autoAlpha:0}}, {tt + 0.56:.3f});')
    r.cue("paper_tear", tt, 0.6)
    r.takeovers.append((t0, tt + 0.5, "hide_panel"))


def fx_phone_broll(r, at, until, image, label="", scroll=True):
    """Phone mock beside the face (left), screenshot scrolls. B-roll for "your own landing page / app"."""
    r.add_css("phone", """
#phone {{ position:absolute; left:34px; top:770px; width:260px; z-index:31; visibility:hidden; }}
.pscr {{ width:260px; height:480px; border-radius:42px; border:12px solid #0E1117; overflow:hidden; background:#fff; box-shadow:0 30px 70px -20px rgba(0,0,0,.8); }}
.pscr img {{ width:100%; display:block; }}
.pl {{ display:block; margin-top:14px; text-align:center; font-weight:700; font-size:28px; color:{GREEN}; }}""")
    t0, t1 = r.t(at), r.t(until)
    r.html.append(f'<div id="phone"><div class="pscr"><img src="{image}" alt="" /></div>' + (f'<span class="pl">{label}</span>' if label else "") + '</div>')
    r.show("#phone", t0, t1, fin=0.35, frm="{autoAlpha:0, y:220, rotation:-8}", to="{autoAlpha:1, y:0, rotation:-4}")
    if scroll:
        r.js.append(f'tl.to("#phone .pscr img", {{yPercent:-38, duration:{t1 - t0 - 0.6:.2f}, ease:"power1.inOut"}}, {t0 + 0.5:.3f});')
    r.cue("whoosh_fast", t0, 0.4)


def fx_comment_drop(r, at, until, word="GROW", type_at=None, gift=None):
    """CTA: comment composer drops in, the keyword is typed, then a gift card (lead magnet) drops below it."""
    r.add_css("cbox", """
.cbox {{ position:absolute; left:80px; top:980px; width:760px; z-index:32; visibility:hidden; display:flex; align-items:center; gap:16px; background:#fff;
  color:{BG}; border-radius:22px; padding:18px 22px; box-shadow:0 24px 60px -18px rgba(0,0,0,.8); }}
.cbox .av {{ display:inline-block; width:44px; height:44px; border-radius:50%; background:linear-gradient(135deg,#3BB4F2,#5683FF); }}
.cin {{ flex:1; font-family:"Sora"; font-weight:800; font-size:44px; display:flex; align-items:center; border:2px solid #CDD2DA; border-radius:999px; padding:8px 22px; min-height:76px; }}
.cin .caret {{ display:inline-block; width:3px; height:36px; background:{BLUE_HI}; margin-left:4px; }}
.gc {{ visibility:hidden; }}
.post {{ font-family:"Sora"; font-weight:700; font-size:28px; color:#fff; background:{BLUE}; border-radius:999px; padding:12px 22px; }}
.cbox2 {{ position:absolute; left:80px; top:1150px; width:760px; z-index:32; visibility:hidden; background:{AMBER}; color:{BG}; border-radius:22px;
  padding:20px 28px 14px; font-size:44px; font-weight:700; line-height:1.25; box-shadow:0 24px 60px -18px rgba(0,0,0,.8); }}
.cbox2 small {{ display:block; font-size:28px; font-weight:600; }}""")
    t0, t1 = r.t(at), r.t(until)
    k = r.id("cb")
    letters = "".join(f'<span class="gc" id="{k}g{i}">{c}</span>' for i, c in enumerate(word))
    r.html.append(f'<div id="{k}" class="cbox"><i class="av"></i><div class="cin">{letters}<i class="caret"></i></div><span class="post">Post</span></div>')
    r.show(f"#{k}", t0, t1, fin=0.3, frm="{autoAlpha:0, y:-160}", to="{autoAlpha:1, y:0}")
    ty = r.t(type_at) if type_at else t0 + 0.4
    for i in range(len(word)):
        r.js.append(f'tl.fromTo("#{k}g{i}", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.01}}, {ty + i * 0.08:.3f});')
    r.cue("pop_notification", t0, 0.45)
    r.cue("typing_keys", ty, 0.25)
    if gift:
        tg = r.t(gift["at"])
        r.html.append(f'<div id="{k}x" class="cbox2">{gift["title"]}<br><small>{gift.get("sub", "")}</small></div>')
        r.show(f"#{k}x", tg, t1, fin=0.3, frm="{autoAlpha:0, y:-120}", to="{autoAlpha:1, y:0}")
        r.cue("pop_notification", tg, 0.4)


def fx_impact(r, at, until, word="GROW"):
    """Manga impact frame: high-contrast live presenter, speed lines, invert strobe, a giant word slams in."""
    r.add_css("impact", """
#impact {{ position:absolute; inset:0; z-index:46; visibility:hidden; background:#000; }}
#impact video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; filter:grayscale(1) contrast(3.2) brightness(1.25); }}
#lines {{ position:absolute; inset:0; width:100%; height:100%; mix-blend-mode:difference; }}
#lines line {{ stroke:#fff; stroke-width:6; opacity:.55; }}
.igrow {{ position:absolute; left:0; width:100%; top:1330px; text-align:center; font-family:"Sora"; font-weight:800; font-size:250px; color:#fff;
  -webkit-text-stroke:10px #000; paint-order:stroke fill; letter-spacing:-.02em; }}""")
    t0, t1 = r.t(at), r.t(until)
    r.html.append(f'<div id="impact">{r.live_video("impv", t0, t1, "imp")}<svg id="lines" viewBox="0 0 1080 1920">'
                  + "".join(f'<line x1="540" y1="760" x2="{540 + 1400 * math.cos(a / 40 * 2 * math.pi):.0f}" y2="{760 + 1400 * math.sin(a / 40 * 2 * math.pi):.0f}"/>' for a in range(40))
                  + f'</svg><div class="igrow">{word}</div></div>')
    r.js.append(f'tl.fromTo("#impact", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.04}}, {t0:.3f});')
    for k in range(4):
        r.js.append(f'tl.set("#impact", {{filter:"invert({1 if k % 2 == 0 else 0})"}}, {t0 + 0.12 + k * 0.1:.3f});')
    r.js.append(f'tl.fromTo("#impact .igrow", {{scale:1.4}}, {{scale:1, duration:0.25, ease:"power4.out"}}, {t0:.3f});')
    r.js.append(f'tl.set("#impact", {{autoAlpha:0}}, {t1:.3f});')
    r.cue("impact_hit", t0, 0.6)
    r.takeovers.append((t0, t1, "hide_panel"))
    r.takeovers.append((t0, t1, "no_subs"))


def fx_blow_away(r, at="blow-0.05"):
    """Ending: the last shot dissolves left-to-right into drifting dust (before the end card)."""
    r.add_css("dust", """
#dustwrap {{ position:absolute; inset:0; z-index:20; pointer-events:none; }}
.dust {{ position:absolute; width:8px; height:8px; border-radius:2px; background:#E8D8C0; visibility:hidden; }}""")
    t = r.t(at)
    dust = "".join(f'<i class="dust" id="d{i}" style="left:{(i * 37) % 900 + 90}px;top:{(i * 53) % 900 + 420}px"></i>' for i in range(60))
    r.html.append(f'<div id="dustwrap">{dust}</div>')
    r.js.append(f'tl.to(".cam", {{"--dis":"130%", duration:1.0, ease:"power1.in"}}, {t:.3f});')
    for i in range(60):
        r.js.append(f'tl.fromTo("#d{i}", {{autoAlpha:0, x:0, y:0}}, {{autoAlpha:0.9, x:{160 + (i * 29) % 260}, y:{-60 - (i * 17) % 160}, duration:0.9, ease:"power1.out"}}, {t + 0.05 + (i % 12) * 0.05:.3f});')
    r.js.append(f'tl.to("#dustwrap", {{autoAlpha:0, duration:0.3}}, {r.card - 0.25:.3f});')
    r.cue("wind_dust", t, 0.55)


EFFECTS = {k[3:]: v for k, v in globals().items() if k.startswith("fx_")}


# ==================================================================== FRAME SYSTEM (presenter, panel, subtitles, end card)
def presenter(r, zoom=1.12, origin="50% 34%"):
    """Jump-cut segments; alternate 1.0 / zoom punch-in per cut, with a slow push."""
    out = []
    for k, s in enumerate(r.segs):
        z = 1.0 if k % 2 == 0 else zoom
        out.append(f'<div class="cam" id="cam{k}" style="transform:scale({z});transform-origin:{origin}">'
                   f'<video id="v{k}" class="clip" src="{s["src"]}" muted playsinline data-start="{s["t"]:.3f}" '
                   f'data-duration="{s["dur"]:.3f}" data-media-start="{s["src_in"]:.3f}" data-track-index="1"></video></div>')
        r.js.append(f'tl.fromTo("#cam{k}", {{scale:{z}}}, {{scale:{z + 0.03:.2f}, duration:{s["dur"]:.3f}, ease:"none"}}, {s["t"]:.3f});')
    return out


def panel(r, title, items, button, show_at, steps, gold_at=None, hide_at="blow"):
    """Right-hand checklist panel ("in this video"): highlight + counter move on each step's word."""
    r.add_css("panel", """
#panel {{ position:absolute; left:744px; top:330px; width:310px; z-index:30; visibility:hidden; background:rgba(18,21,26,.9); border:1px solid {BORDER};
  border-radius:16px; padding:18px 16px 16px; box-shadow:0 20px 50px -18px rgba(0,0,0,.7); }}
#panel .ph {{ font-size:26px; font-weight:600; color:{MUTED}; display:flex; justify-content:space-between; margin-bottom:10px; letter-spacing:.02em; }}
#panel ul {{ list-style:none; display:flex; flex-direction:column; gap:8px; }}
#panel li {{ font-size:27px; font-weight:600; padding:8px 12px 4px; border-radius:10px; color:{MUTED}; display:flex; gap:10px; align-items:baseline; }}
#panel li .num {{ font-size:26px; color:{MUTED}; }}
#panel li.on {{ background:{BLUE}; color:{BG}; }} #panel li.on .num {{ color:{BG}; }}
#pbtn {{ margin-top:14px; text-align:center; font-size:26px; font-weight:700; padding:10px 0 6px; border-radius:999px; background:{BLUE}; color:{BG}; }}
#pbtn.gold {{ background:{AMBER}; color:{BG}; box-shadow:0 0 24px rgba(240,162,59,.55); }}""")
    n_num = sum(1 for n, _ in items if n.strip("•").strip())
    lis = "".join(f'<li id="pi{i}"><span class="num">{n}</span>{t}</li>' for i, (n, t) in enumerate(items))
    r.html.append(f'<div id="panel"><div class="ph">{title} <span id="pcount">{"0".zfill(2).translate(BN)}/{str(n_num).zfill(2).translate(BN)}</span></div><ul>{lis}</ul>'
                  f'<div id="pbtn">{button}</div></div>')
    r.js.append(f'tl.fromTo("#panel", {{autoAlpha:0, x:60}}, {{autoAlpha:1, x:0, duration:0.35, ease:"power3.out"}}, {r.t(show_at):.3f});')
    c = 0
    for st in steps:
        t, i = r.t(st["at"]), st["item"]
        r.js.append(f'tl.set("#panel li", {{className:""}}, {t:.3f}); tl.set("#pi{i}", {{className:"on"}}, {t:.3f});')
        if items[i][0].strip("•").strip():
            c += 1
            r.js.append(f'tl.set("#pcount", {{textContent:"{str(c).zfill(2).translate(BN)}/{str(n_num).zfill(2).translate(BN)}"}}, {t:.3f});')
    if gold_at:
        tg = r.t(gold_at)
        r.js.append(f'tl.set("#pbtn", {{className:"gold"}}, {tg:.3f});')
        r.js.append(f'tl.fromTo("#pbtn", {{scale:1}}, {{scale:1.08, duration:0.2, yoyo:true, repeat:3, ease:"sine.inOut"}}, {tg + 0.1:.3f});')
    for t0, t1, kind in r.takeovers:
        if kind == "hide_panel":
            r.js.append(f'tl.to("#panel", {{autoAlpha:0, duration:0.05}}, {t0:.3f}); tl.to("#panel", {{autoAlpha:1, duration:0.15}}, {t1:.3f});')
        elif kind == "panel_above":
            r.js.append(f'tl.set("#panel", {{zIndex:48}}, {t0:.3f}); tl.set("#panel", {{zIndex:30}}, {t1:.3f});')
    r.js.append(f'tl.to("#panel", {{autoAlpha:0, duration:0.3}}, {r.t(hide_at):.3f});')


def subtitles(r, hide_sections=(), max_words=6, glue_words=("রাত",), en_words=("GROW",)):
    """Per-word highlighted subtitles in black boxes. Chunks split at punctuation or max_words; numbers stay glued to the
    next word. Sections in hide_sections are skipped (e.g. the comment-drop CTA); chunks wait out "no_subs" takeovers."""
    r.add_css("subs", """
.sub {{ position:absolute; left:60px; width:%dpx; top:%dpx; translate:0 -50%%; z-index:50; text-align:center; visibility:hidden; }}
.sub .box {{ display:inline; background:rgba(0,0,0,.86); color:{TEXT}; font-weight:600; font-size:54px; line-height:1.62; padding:6px 20px 0;
  border-radius:14px; -webkit-box-decoration-break:clone; box-decoration-break:clone; }}
.sub .w.en {{ font-family:"Sora"; font-weight:800; }}""" % (W - 120 - 130, int(0.765 * H)))
    nosub = [(a, b) for a, b, k in r.takeovers if k == "no_subs"]

    def chunks(ws):
        out, cur = [], []
        for x in ws:
            cur.append(x)
            glued = x["text"].rstrip("।,?:!").translate(str.maketrans("", "", "০১২৩৪৫৬৭৮৯0123456789")) == "" or x["text"] in glue_words
            brk = x["text"][-1] in "।,?:!" and not glued
            if (brk or len(cur) >= max_words) and not glued:
                out.append(cur)
                cur = []
        if cur:
            out.append(cur)
        return out

    caps, cid = [], 0
    T, HI = r.C["TEXT"], r.C["BLUE_HI"]
    for sec in sorted(r.secs):
        if sec in hide_sections:
            continue
        cs = chunks([x for x in r.words if x["section"] == sec])
        for j, ch in enumerate(cs):
            t0 = ch[0]["start"] - 0.05
            for a, b in nosub:
                if a - 0.05 <= t0 < b:
                    t0 = b
            t1 = cs[j + 1][0]["start"] - 0.05 if j + 1 < len(cs) else min(r.secs[sec]["end"] + 0.1, r.blow)
            if t1 - t0 < 0.15:
                continue
            spans = " ".join(f'<span class="w{" en" if x["text"].rstrip("।,?:!") in en_words else ""}" id="s{cid}w{k}">{x["text"]}</span>' for k, x in enumerate(ch))
            caps.append(f'<div class="sub" id="s{cid}"><span class="box">{spans}</span></div>')
            r.js.append(f'tl.fromTo("#s{cid}", {{autoAlpha:0, scale:0.9}}, {{autoAlpha:1, scale:1, duration:0.12, ease:"back.out(2)"}}, {t0:.3f});')
            r.js.append(f'tl.to("#s{cid}", {{autoAlpha:0, duration:0.06}}, {t1 - 0.06:.3f});')
            for k, x in enumerate(ch):
                r.js.append(f'tl.fromTo("#s{cid}w{k}", {{color:"{T}"}}, {{color:"{HI}", duration:0.06, immediateRender:false}}, {x["start"]:.3f});')
                if k + 1 < len(ch):
                    r.js.append(f'tl.to("#s{cid}w{k}", {{color:"{T}", duration:0.04}}, {max(ch[k + 1]["start"], x["start"] + 0.07):.3f});')
            cid += 1
    return caps


def end_card(r, logo, lines, contact_label="", phone=""):
    """End card (no voice): logo, tagline lines, WhatsApp pill. lines[0] large, the rest muted."""
    r.add_css("card_end", """
#card {{ position:absolute; inset:0; z-index:70; visibility:hidden; background:{BG}; display:flex; flex-direction:column; align-items:center; padding-top:300px; text-align:center; }}
#elogo {{ width:700px; }}
#e1 {{ margin-top:50px; font-size:58px; font-weight:700; line-height:1.3; padding:0 70px; }}
.eline {{ margin-top:18px; font-size:38px; font-weight:600; color:{MUTED}; }}
#e3 {{ margin-top:70px; font-size:32px; font-weight:600; color:{MUTED}; letter-spacing:.04em; }}
#e4 {{ margin-top:16px; display:flex; align-items:center; gap:16px; background:{WA}; color:{BG}; border-radius:999px; padding:18px 44px; font-family:"Sora"; font-weight:800; font-size:48px; }}""")
    wa = ('<svg viewBox="0 0 24 24" width="46" height="46"><path fill="#0B0D11" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm5.3 14.1c-.2.6-1.3 '
          '1.2-1.8 1.2-.5.1-1 .2-3.3-.7-2.8-1.1-4.6-4-4.7-4.2-.1-.2-1.1-1.5-1.1-2.9s.7-2 1-2.3c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.4 0 .5l-.3.5-.4.4c-.1.1-.3.3-.1.6.2.3.7 '
          '1.2 1.6 1.9 1.1 1 2 1.3 2.3 1.4.3.1.5.1.6-.1l.9-1c.2-.3.4-.2.6-.1l1.9.9c.3.1.5.2.5.3.1.2.1.8-.1 1.4z"/></svg>')
    rest = "".join(f'<div class="eline" id="e2{i}">{x}</div>' for i, x in enumerate(lines[1:]))
    r.html.append(f'<div id="card"><img id="elogo" src="{logo}" alt="logo" /><div id="e1">{lines[0]}</div>{rest}'
                  + (f'<div id="e3">{contact_label}</div>' if contact_label else "")
                  + (f'<div id="e4">{wa}<span>{phone}</span></div>' if phone else "") + '</div>')
    C = r.card
    r.js.append(f'tl.fromTo("#card", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.3}}, {C:.3f});')
    r.js.append(f'tl.fromTo("#elogo", {{autoAlpha:0, scale:0.85}}, {{autoAlpha:1, scale:1, duration:0.5, ease:"back.out(1.6)"}}, {C + 0.15:.3f});')
    sels = ["#e1"] + [f"#e2{i}" for i in range(len(lines) - 1)] + (["#e3"] if contact_label else []) + (["#e4"] if phone else [])
    for k, sel in enumerate(sels):
        r.js.append(f'tl.fromTo("{sel}", {{autoAlpha:0, y:30}}, {{autoAlpha:1, y:0, duration:0.4, ease:"power3.out"}}, {C + 0.6 + k * 0.35:.3f});')
    if phone:
        r.js.append(f'tl.to("#e4", {{scale:1.06, duration:0.35, yoyo:true, repeat:3, ease:"sine.inOut"}}, {C + 2.4:.3f});')
        r.cue("pop_notification", C + 0.6 + (len(sels) - 1) * 0.35, 0.3)
    r.cue("chime_success", C + 0.15, 0.4)


BASE_CSS = """
@font-face {{ font-family:"Hind Siliguri"; src:url(media/fonts/hind-siliguri-bengali-600-normal.woff2) format("woff2"); font-weight:600; font-display:block; unicode-range:U+0980-09FE,U+200C-200D,U+25CC; }}
@font-face {{ font-family:"Hind Siliguri"; src:url(media/fonts/hind-siliguri-bengali-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; unicode-range:U+0980-09FE,U+200C-200D,U+25CC; }}
@font-face {{ font-family:"Hind Siliguri"; src:url(media/fonts/hind-siliguri-latin-600-normal.woff2) format("woff2"); font-weight:600; font-display:block; unicode-range:U+0000-00FF,U+2000-206F; }}
@font-face {{ font-family:"Hind Siliguri"; src:url(media/fonts/hind-siliguri-latin-700-normal.woff2) format("woff2"); font-weight:700; font-display:block; unicode-range:U+0000-00FF,U+2000-206F; }}
@font-face {{ font-family:"Sora"; src:url(media/fonts/sora.woff2) format("woff2"); font-weight:600 800; font-display:block; }}
@font-face {{ font-family:"Noto Color Emoji"; src:url(media/fonts/NotoColorEmoji.ttf) format("truetype"); font-display:block; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:{BG}; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; color:{TEXT}; font-family:"Hind Siliguri", "Noto Color Emoji", sans-serif; }}
.cam {{ position:absolute; inset:0; --dis:-30%;
  -webkit-mask-image:linear-gradient(90deg, transparent 0%, transparent var(--dis), #000 calc(var(--dis) + 25%));
  mask-image:linear-gradient(90deg, transparent 0%, transparent var(--dis), #000 calc(var(--dis) + 25%)); }}
.cam video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; filter:brightness(.82) saturate(.86) contrast(1.06); }}
#grade {{ position:absolute; inset:0; pointer-events:none; z-index:2;
  background:radial-gradient(900px 1250px at 50% 38%, rgba(11,13,17,0) 45%, rgba(11,13,17,.72) 100%); }}
.en {{ font-family:"Sora"; font-weight:800; letter-spacing:.02em; }}"""


def page(r, cams, caps, title):
    css = BASE_CSS.format(**r.C) + "".join(r.css.values())
    glitch = '<div id="glitch"></div>' if getattr(r, "glitch", False) else ""
    return f"""<!doctype html>
<html lang="bn"><head><meta charset="UTF-8" /><meta name="viewport" content="width={W}, height={H}" />
<title>{title}</title><style>{css}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{r.total:.3f}" data-width="{W}" data-height="{H}">
{chr(10).join(cams)}
<div id="grade"></div>
{chr(10).join(r.html)}
{chr(10).join(caps)}
{glitch}
<audio id="mix" src="media/mix.wav" data-start="0" data-duration="{r.total:.3f}" data-track-index="20"></audio>
</div>
<script src="media/gsap.min.js"></script>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(r.js)}
window.__timelines["main"] = tl;
</script>
</body></html>
"""
