import sys
from pathlib import Path
D = Path(__file__).parent
HEAD = {"a": "সময় দেখতে <b>ফোন</b> খোঁজেন?", "b": "বড় ডিজিট, <b>দূর থেকেও</b> দেখা যায়"}
v = sys.argv[1] if len(sys.argv) > 1 else "a"
FF = "".join(f'''@font-face {{ font-family: "Hind Siliguri"; font-weight: {w}; src: url("assets/fonts/hind-siliguri-{s}-{w}-normal.woff2") format("woff2");{" unicode-range: U+0980-09FE, U+200C-200D, U+25CC;" if s=="bengali" else ""} }}
''' for s in ("bengali","latin") for w in (600,700))
html = f'''<!doctype html><html lang="bn"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<style>{FF}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#111; }}
#root {{ position:relative; width:100%; height:100%; overflow:hidden; font-family:"Hind Siliguri", sans-serif; }}
#bg {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
#shade {{ position:absolute; inset:0; background:linear-gradient(180deg, rgba(0,0,0,0) 48%, rgba(0,0,0,0.55) 66%, rgba(0,0,0,0.25) 100%); }}
#ring {{ position:absolute; left:-12px; top:700px; width:400px; height:228px; border:8px solid #ffd43b; border-radius:40px; }}
#tag {{ position:absolute; left:24px; top:628px; background:#ffd43b; color:#15171c; font-size:40px; font-weight:700; padding:6px 22px 0; border-radius:16px; }}
#head {{ position:absolute; left:60px; right:60px; top:1010px; text-align:center; color:#fff; font-size:96px; font-weight:700; line-height:1.18;
  text-shadow:0 6px 24px rgba(0,0,0,0.75), 0 2px 4px rgba(0,0,0,0.9); }}
#head b {{ color:#ffd43b; }}
#price {{ position:absolute; left:0; right:0; top:1290px; display:flex; justify-content:center; align-items:center; gap:22px; }}
#price .p {{ background:#fff; color:#15171c; font-size:84px; font-weight:700; padding:14px 40px 2px; border-radius:28px; box-shadow:0 14px 30px rgba(0,0,0,0.45); transform:rotate(-3deg); }}
#price .p b {{ color:#d4380d; }}
#price .d {{ background:#12924a; color:#fff; font-size:44px; font-weight:700; padding:10px 28px 2px; border-radius:999px; box-shadow:0 10px 24px rgba(0,0,0,0.4); }}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="1" data-width="1080" data-height="1920">
<img id="bg" src="assets/hero.jpg" alt="" />
<div id="shade"></div>
<div id="ring"></div><div id="tag">LED ডিজিটাল ঘড়ি</div>
<div id="head">{HEAD[v]}</div>
<div id="price"><div class="p">মাত্র <b>৳১০৯৯</b></div><div class="d">ঢাকায় ফ্রি ডেলিভারি</div></div>
</div>
<script src="assets/gsap.min.js"></script>
<script>window.__timelines["main"] = gsap.timeline({{ paused: true }});</script>
</body></html>'''
(D / "index.html").write_text(html)
