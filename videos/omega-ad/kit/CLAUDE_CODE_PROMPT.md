# Prompt for Claude Code (HyperFrames)

**Before you paste it:**

1. On your computer, make a folder (for example `omega-ad`), unzip this kit into it, and open
   Claude Code in that folder.
2. You need **Node.js 22+** and **FFmpeg** installed. Check with `node -v` and `ffmpeg -version`.
3. Optional: put your licensed background track in the folder as `music.mp3`.

Then paste everything in the box below.

---

```
Build a 30-second vertical video ad with HyperFrames from the kit in this folder.

SETUP
- Install the HyperFrames skill if it is not installed: `npx skills add heygen-com/hyperframes`, then read
  the skill and `npx hyperframes --help` before writing anything. Where my notes below disagree with the
  HyperFrames docs about syntax, follow the docs.
- Create the project with `npx hyperframes init` (or inside this folder, as the docs say), and copy
  fonts/, icons/, screens/ into its assets so every file is loaded locally. Nothing may load from the
  internet at render time except GSAP if the docs recommend a CDN; prefer the npm package.

READ FIRST (in this folder)
- storyboard.md: the 9 scenes, exact timings, on-screen text, which screenshot each scene uses, and motion.
- copy.md: all text lines. Use them exactly; do not invent new claims, numbers or prices.
- brand.md: colours, fonts (@font-face snippets), type scale, 9:16 safe zones, the phone-mockup CSS, rules.
- starter/index.html: scenes 1 and 9 already built and tested. Reuse its structure, timeline registration
  and styles, and build scenes 2–8 in the same file and style.

OUTPUT
1. `omega-ad-30s` — 1080×1920, 30 fps, 30 seconds, all 9 scenes.
2. `omega-ad-15s` — the 15-second cut described in storyboard.md.
3. `omega-ad-square` — 1080×1080 and `omega-ad-wide` — 1920×1080, reflowed as storyboard.md says.
If music.mp3 exists, add it as an audio clip at volume 0.35 with a 1 s fade-out at the end; otherwise no audio.

RULES
- Bangla text must use the Noto Sans Bengali @font-face from brand.md (bold = real weight 700/800).
  Wait for document.fonts.ready. Check rendered frames for broken conjuncts.
- Every animation on one paused GSAP timeline registered on window.__timelines under the composition id,
  every tween at an absolute time, so any frame can be seeked. No setTimeout, no CSS animations that
  run on their own, no Math.random without a fixed seed.
- Keep all text and the CTA inside the 9:16 safe zone (x 80–940, y 220–1540). Min font size 36 px.
  Each text line stays on screen at least 1.5 s.
- Screenshots go inside the phone mockup from brand.md; pan them by animating translateY on the img.
- Inline the SVG icons so their colour can be set with CSS.
- Do not draw Google, Facebook or WhatsApp logos or copy their screens. Scene 1's map card is a generic
  card, built in HTML as in the starter.
- No emoji in frames. No before/after photos. Do not add any rating, review count or patient number.
- Scene 7 shows the dashboard: keep its small "নমুনা ডেটা" label visible.

CHECK BEFORE RENDERING
- Run the HyperFrames lint, then preview. Grab still frames at 1.0, 5.0, 9.0, 12.0, 15.5, 18.5, 21.5,
  24.5 and 28.0 s and look at each one: text inside the safe zone, nothing overlapping, Bangla shaped
  correctly, screenshots sharp.
- Then render all four outputs and tell me the file paths and durations.
```

---

**If something goes wrong:**
- **Bangla shows boxes or broken letters:** the font isn't loaded. Ask Claude Code to check the
  @font-face path and `document.fonts.ready`.
- **The render is jumpy or frames don't match the preview:** something is animating outside the
  GSAP timeline. Ask Claude Code to move it onto the timeline.
- **The text runs under Facebook's buttons:** ask Claude Code to re-check the safe zone in brand.md.
