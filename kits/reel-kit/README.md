# Reel Kit: talking-head effects Reels in about 1 hour

You give it your talking-head clips plus your script, and it produces a 9:16 Reel. The Reel gets:
- jump cuts on the pauses;
- effects that land on your spoken words;
- per-word Bangla subtitles;
- a mix with music ducked under your voice and one sound effect per effect, at -14 LUFS;
- a checklist panel, a comment call to action and an end card.

Every video is one `reel.json` file. The effect code lives in the kit, so it's reused, never rewritten.

The kit was built from the Future Stack promo. `examples/futurestack-promo.reel.json` rebuilds that video frame for frame.

## Setup (once per machine or container)
```bash
pip install openai-whisper soundfile numpy      # whisper needs the "openaipublic.azureedge.net" host for its model download
```
You also need ffmpeg and Node (npx). The renderer is pinned to `hyperframes@0.9.23`.

## The 1-hour workflow
| Step | Time | What |
|---|---|---|
| 1 | 2 min | `python3 kits/reel-kit/kit/reel.py new videos/<name>` scaffolds the project with fonts, SFX, logo and a starter `reel.json`. |
| 2 | 15 min | Record **one clip per section**: hook, point 1, point 2, …, call to action, close. Copy them to `media/clips/pt1.mp4 …`. Music goes in `media/music/bgm.wav` (optional). |
| 3 | 10 min | In `reel.json`, paste your script per section, exactly as you say it. |
| 4 | 5 min | Run `reel.py cut` then `reel.py words`. Then `reel.py words videos/<name> --list` prints every word with its time. These are the words you can hang effects on. |
| 5 | 20 min | Pick effects in `reel.json` and anchor them to words, using the catalogue below. |
| 6 | 10 min | `reel.py build`, `reel.py mix`, then `npx hyperframes snapshot` at a few moments to look at frames. Then `reel.py render`, which writes `out/<output>.mp4` plus a contact sheet. |

Or run all of it at once: `python3 kits/reel-kit/kit/reel.py all videos/<name>`. Change `reel.json` and rerun `build`, `mix` and `render`. Cuts and words don't need rerunning unless the clips change.

## Time anchors: how effects land on words
Every `at` / `until` value is one of:

| Anchor | Meaning |
|---|---|
| `2.5` | absolute seconds |
| `"s2"` / `"s2:end"` | start / end of section 2 |
| `"s2:দাম"` | the first word in section 2 that starts with "দাম" |
| `"s1:সমস্যা#1"` | the second occurrence (0-based) |
| `"s2:এআই+0.3"`, `"s3-0.02"` | with an offset |
| `"blow"`, `"card"` | start of the blow-away / the end card |

If a word isn't found, the build stops and prints that section's words, so you can fix the spelling.

## Effect catalogue (`"fx": name` in `effects[]`)
| fx | Use it for | Key params |
|---|---|---|
| `title_pills` | hook title, top | `lines`, `sub`, `at`, `until` |
| `cursor_select` | hook: cursor plus a selection box around you | `at`, `click`, `out`, `tag`, `box:[l,t,w,h]` |
| `number_tiles` | "৩টা সমস্যা / ৩টা কারণ" preview tiles on the chest | `at`, `until`, `items:[[emoji,label],…]` |
| `letter_dive` | section opener ০১/০২ (full screen, 0.66 s) | `at`, `text` |
| `glitch` | transition accent | `at` |
| `chat` | Messenger story: typed question → seen → customer leaves → AI bot replies | `at`, `until`, `typed`, `keys`, `customer/seen/left/bot:{at,text,small}` |
| `head_stack` | benefit chips above your head; `replace:true` flips red → green | `chips:[{at,text,style}]`, `until`, `replace` |
| `post_wall` | proof of volume: grid plus a rolling counter (lost **or** won customers) | `at`, `until`, `title`, `unit`, `tag`, `count_to` |
| `voice_note` | reminder / follow-up message with "Delivered ✓✓" | `at`, `until`, `text`, `delivered_at` |
| `press_tear` | newspaper front page with your halftone photo, torn on a word | `at`, `tear_at`, `masthead`, `dateline`, `headline`, `cols` |
| `phone_broll` | phone mock with a scrolling screenshot (landing page, app) | `at`, `until`, `image`, `label` |
| `comment_drop` | the call to action: comment box types the keyword, then a gift card drops | `at`, `until`, `word`, `type_at`, `gift:{at,title,sub}` |
| `impact` | one key line: manga frame plus a giant word (once per video) | `at`, `until`, `word` |
| `blow_away` | ending: you dissolve into dust | (none) |

These blocks aren't in `effects[]`; each has its own top-level key:
- `panel`: the right-hand checklist. It takes `items`, `steps:[{at,item}]` and `gold_at`.
- `subtitles`: takes `hide_sections` (hide them during the call to action).
- `end_card`: takes `logo`, `lines`, `contact_label` and `phone` (shown as a WhatsApp pill).
- `cut`: takes `pause`, `end_hold` and `end_card` seconds. Each section can also carry `"trim":[in,out]`.
- `music`: takes `file` and `gain_db`.

## Rules the kit enforces (do not fight them)
- **Your face stays clear.** Cards sit on the chest band (bottom-anchored above the subtitles) or above your head. Only `letter_dive`, `press_tear` and `impact` take over the screen, briefly.
- The panel hides automatically during full-screen takeovers. Subtitles wait until the impact frame ends.
- One sound effect per effect, on its first frame. The final mix is at -14 LUFS.
- **Pacing:** one effect every 1–1.5 s at most, at most 4 full-screen moments, impact once.
- Put the comment call to action at 35–45 % of the runtime. Here it uses its own section, and the subtitles for that section are hidden.

## Adding a new effect (banknote, day dial, layer explode, …)
1. In `kit/fx.py`, write `def fx_<name>(r, at, until, ...)`. Use:
   - `r.t(anchor)` for times;
   - `r.add_css(key, css)` for styles (colour tokens like `{BLUE}`);
   - `r.html.append(...)` for markup;
   - `r.js.append('tl....')` for GSAP calls (seek-safe: `fromTo` / `set` only);
   - `r.cue(sfx, t, gain)` for the sound;
   - `r.takeovers.append((t0, t1, "hide_panel"))` if it fills the screen.
2. It's then available as `{"fx": "<name>", ...}` in any `reel.json`. Ideas ranked by ROI are in `videos/style-ref/EFFECTS_REPORT.md`.

## Files
```
kits/reel-kit/
  kit/reel.py     CLI: new | cut | words | build | mix | render | all
  kit/fx.py       effects library + frame system (presenter, panel, subtitles, end card)
  assets/         fonts (Hind Siliguri, Sora, emoji), SFX, Future Stack logos, gsap
  template/       HyperFrames project skeleton copied by `new`
  examples/       starter.reel.json, futurestack-promo.reel.json (the real promo)
```
