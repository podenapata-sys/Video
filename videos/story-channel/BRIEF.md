---
workflow: general-video
flow: automation
storyboard: no
message: "Short moral/money fables told with 1930s cartoon-noir animal characters."
destination: Facebook/Instagram Reels, YouTube Shorts, TikTok
aspect: "9:16"
length: 60-90s
language: en
---

# Story Channel — cartoon-noir fables

## Intent
Faceless story Reels in the style of the user's references: AI-illustrated animal
characters (bear, pig, wolf), narrator, short serif captions, a cut every 3-5s with a slow
Ken Burns move, SUBSCRIBE end card.

## Pipeline
1. Write `episodes/<slug>/story.json` (shots → spoken caption lines) + `PROMPTS.md`.
2. User generates one 9:16 image per shot (01.png …) in an outside image tool, puts them in
   `episodes/<slug>/images/`.
3. `python3 scripts/build_episode.py <slug> --render` → per-line Kokoro TTS (exact caption
   sync), voiceover.wav, index.html, check, `episodes/<slug>/renders/<slug>.mp4`.
   Add `--placeholders` to test without images. Optional `music.mp3` in the episode folder.

## Assets / notes
- Fonts: EB Garamond (bundled) for captions, a deliberate period-serif match to the references.
- Grain + vignette from the HyperFrames registry (`compositions/components/`).
- Image generation is not available in this environment (no GPU, HeyGen sign-in needed).
