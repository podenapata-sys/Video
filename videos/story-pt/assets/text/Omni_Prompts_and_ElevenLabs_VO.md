# THE 2:14 TEXT — Omni Flash Prompts (no voice) + ElevenLabs VO

**Runtime:** ~77 s, split into 8 clips of 10 s each (last clip padded). **Format:** 1080x1920, 9:16, 30 fps.
Paste each Omni block as-is. The VO chunks go into ElevenLabs separately, then you lay them over the clips in Resolve.

---

## Voice style recommendation

**Best fit: a calm, dry, late-night narrator. Low-to-mid pitch, close-mic, slow, very little emotion.**

Why it works here:
- The story depends on flat, matter-of-fact delivery. The horror comes from the calm, not from acting.
- Sentences are short. A steady, unhurried pace makes the pauses between rules land.
- The "It says her name right. It says it wrong." line only works if the narrator doesn't sound alarmed.

Three options to audition in ElevenLabs Voice Library (search by description, since premade voices change):
1. **Deadpan male narrator** (recommended): dry, low, neutral accent, "documentary-style". Best for the rule cards.
2. **Intimate female narrator**: close and quiet, slightly breathy. Good if you want it more personal and unsettling.
3. **Stern documentary narrator**: authoritative and clipped. Fits the emergency alerts but can feel too formal for the stairs and peephole scenes.

**Starting settings:** Stability 55–65%, Similarity 75%, Style 15–25%, Speaker boost on. Keep Style low so it stays flat. Generate each chunk separately and keep the same seed/voice to stay consistent across clips.

---

## Omni Flash prompts

**STYLE LOCK (in every clip):** Vertical 9:16, 1080x1920, flat 2D motion-graphic illustration, rounded stick figures with white circle heads, two dot eyes and thin round glasses, a figure in a blue coat. Night palette #0F1420 to #1B2233, warm amber #FFB347 light, alert red #E63B3B, highlight lime #C6FF3D, white #F4F4F4, grey #8A93A6. HUD top-left: small red dot + "DAY 1", clock in white mono, floor in grey caps. Clean vector edges, slight grain, slight vignette, slow eased camera moves, hard cuts on caption changes. NO narration, NO voiceover, NO dialogue. Only ambient room tone and sound effects.

---

### CLIP 01 · 0:00–0:10 · HOOK + ALERT SETUP

STYLE: [locked style lock above]
TECH: 1080x1920, 9:16, 30fps, 10.0 seconds, single continuous sequence, hard cuts. Ambient room tone only, no narration.
TIMELINE:
0.0–4.0s — Night bedroom, side view. A figure in a blue coat lies in bed face-up, one arm over the blanket. Phone on nightstand glows, screen reads "2:14 AM" in white mono. Amber streetlight through the window. Camera does a slow 5% push-in. HUD: DAY 1 · 2:14 AM · FLOOR 09. Caption-free.
4.0–7.0s — Close-up of the phone on the nightstand. Grey message bubble, no contact name, just a long dash. Text: "I'm outside. Let me in." Hard cut.
7.0–10.0s — The phone shakes with three short lines, rotates slightly, lights up with a second notification. Screen flashes white then settles.
SOUND: Low room tone. Soft phone buzz at 4.0s. Sharp double buzz at 7.0s. Low drone enters at 9.0s.
FINAL FRAME: Phone screen glowing with the red alert banner partly visible, figure in bed beginning to sit up. Held 0.5 s.

---

### CLIP 02 · 0:10–0:20 · EMERGENCY ALERT + BUILDING + STAIRS

STYLE: [locked style lock above]
TECH: 1080x1920, 9:16, 30fps, 10.0 seconds, single continuous sequence, hard cuts. Ambient room tone and sound effects only.
TIMELINE:
0.0–4.0s — Phone UI insert, full-screen red alert. White warning triangle, "EMERGENCY ALERT" in white caps, sub-line "Stay indoors. Do not answer unknown calls." Button "OK" at bottom. Phone scales in at 105% then settles at 100%. HUD: DAY 1 · 2:14 AM.
4.0–8.0s — Side cutaway of a 14-floor apartment block at night, lit windows every floor. A thin lime outline highlights the 9th floor, with a small figure in its window. Camera slow push-in. HUD: FLOOR 09.
8.0–10.0s — Vertical stairwell cross-section, concrete landings, one bare bulb per landing. Figure at the top of the stairs, one hand on the rail. HUD counter starts ticking FLOOR 09 → 08.
SOUND: Siren-like alert chime at 0.0s. Low sustained tone under the building shot. Single footstep at 9.0s.
FINAL FRAME: Figure at the top of the stairwell, one foot on the first step, bulb light above, held 0.5 s.

---

### CLIP 03 · 0:20–0:30 · RULE #1 + THE CALL

STYLE: [locked style lock above]
TECH: 1080x1920, 9:16, 30fps, 10.0 seconds, single continuous sequence, hard cuts and a 3-frame horizontal wipe on the rule card. No narration.
TIMELINE:
0.0–2.0s — Stairwell, figure mid-descent. HUD: FLOOR 08 → 07.
2.0–6.0s — Rule card on near-black. Red tag "RULE #1" at top. White ExtraBold caps below: DON'T ANSWER UNKNOWN CALLS. A thin red underline sweeps left to right over 0.5 s. HUD hidden. Card holds.
6.0–10.0s — Back to the stairwell landing. Phone glows with a green call banner reading "Mom". A thin lime waveform pulses from the phone. Figure looks down at it, one hand raised. HUD: FLOOR 08.
SOUND: Bass hit and swipe at 2.0s. Footsteps on concrete. Phone ringtone pulses at 6.0s (muffled, two rings).
FINAL FRAME: Phone on the landing, green call banner visible, figure's raised hand hovering over the screen. Held 0.5 s.

---

### CLIP 04 · 0:30–0:40 · RULE #2 + COUNTING

STYLE: [locked style lock above]
TECH: 1080x1920, 9:16, 30fps, 10.0 seconds, single continuous sequence, hard cuts and a 3-frame horizontal wipe. No narration.
TIMELINE:
0.0–4.0s — Rule card on near-black. Red tag "RULE #2", white caps COUNT THE STAIRS. Red underline sweeps. HUD hidden.
4.0–9.0s — Stairwell. Figure walks down, each step lights up with a lime tick. Counter top-right reads "STEP 40", then "STEP 41", ticking up. HUD: FLOOR 06.
9.0–10.0s — Wide shot down the stairwell. Figure reaches a landing. A single extra step glows red below the feet. Counter reads "STEP 55" where it should read 54. HUD: FLOOR 03.
SOUND: Bass hit at 0.0s. Each footstep is a soft tick. A low chime when the red step lights up at 9.0s.
FINAL FRAME: Red-lit extra step under the figure's foot, counter at 55. Held 0.5 s.

---

### CLIP 05 · 0:40–0:50 · EXTRA STEP + RULE #3 + LOBBY LIGHT

STYLE: [locked style lock above]
TECH: 1080x1920, 9:16, 30fps, 10.0 seconds, single continuous sequence, hard cuts and a 3-frame horizontal wipe. No narration.
TIMELINE:
0.0–4.0s — Figure stands on the landing, looking down at the red-lit step. Slow 8% push-in to the foot. HUD: FLOOR 03 → 02.
4.0–6.0s — Rule card on near-black. Red tag "RULE #3", white caps PORCH LIGHT OFF. HUD hidden.
6.0–10.0s — The lobby at the bottom of the stairwell. A single warm amber doorway at the far end, glowing. Red X overlays the glow. Figure stops three steps back, a lime spotlight circle around them. HUD: FLOOR 01.
SOUND: Single footstep at 0.0s. Bass hit at 4.0s. Soft hum from the lobby light at 6.0s.
FINAL FRAME: Lit doorway in the lobby with a red X overlay, figure in the spotlight circle, held 0.5 s.

---

### CLIP 06 · 0:50–1:00 · FIGURE IN THE DOORWAY + RULE #4

STYLE: [locked style lock above]
TECH: 1080x1920, 9:16, 30fps, 10.0 seconds, single continuous sequence, hard cuts and a 3-frame horizontal wipe. No narration.
TIMELINE:
0.0–3.0s — Lobby, lit doorway. A dark silhouette in a blue coat, same height as the figure, stands inside the amber light. No face visible, faint white rim light on the edges. Spotlight circle around the doorway. HUD: FLOOR 01.
3.0–8.0s — Slow 10% push-in on the silhouette. It stays still. A thin lime outline traces the silhouette's shoulders. HUD: FLOOR 01.
8.0–10.0s — Rule card on near-black. Red tag "RULE #4", white caps NEVER SAY YES TO THE DOOR. HUD hidden.
SOUND: Low drone under the lobby scene. Soft tick of a light flicker at 3.0s. Bass hit and swipe at 8.0s.
FINAL FRAME: Rule card "NEVER SAY YES TO THE DOOR" with the red underline complete. Held 0.5 s.

---

### CLIP 07 · 1:00–1:10 · PEEPHOLE + WRONG PRONUNCIATION

STYLE: [locked style lock above]
TECH: 1080x1920, 9:16, 30fps, 10.0 seconds, single continuous sequence, hard cuts. No narration.
TIMELINE:
0.0–5.0s — Close-up of a round peephole in a wooden door. Inside view: the figure in the blue coat with a bright halo of light. A grey speech bubble from outside the door reads "Can I come in?" Bubble pops in with a 6-frame scale. HUD: FLOOR 01.
5.0–10.0s — Same peephole view. A name plate beside the frame reads the figure's name. The bubble from outside reads the same name, with a lime question mark beside the second syllable. Slow push-in on the peephole. HUD: FLOOR 01 · 11:58 PM.
SOUND: Metal peephole clink at 0.0s. Soft knock at 2.5s. Muffled hum from outside at 5.0s.
FINAL FRAME: Peephole view, the name plate in focus, the lime question mark glowing. Held 0.5 s.

---

### CLIP 08 · 1:10–1:20 · CHOICE CARD (ENDING)

STYLE: [locked style lock above]
TECH: 1080x1920, 9:16, 30fps, 10.0 seconds, single continuous sequence, hard cut in, 6-frame fade to black at the end. No narration.
TIMELINE:
0.0–3.0s — Lobby, the silhouette in the amber doorway, a little brighter now. HUD: FLOOR 01 · 11:59 PM.
3.0–8.0s — Dark phone lock-screen UI, centered. Clock top reads "11:59 PM". White ExtraBold caps DO YOU OPEN IT? Two pill buttons below: green "OPEN IT" and red-outline "KEEP IT SHUT". A grey finger tap icon slides in and hovers over "KEEP IT SHUT" for 2 s.
8.0–10.0s — Tap icon presses the button, button flashes, then the screen fades to black. Hold 1.0 s black.
SOUND: Soft lock-screen click at 3.0s. Low drone rises. Button tap at 8.0s. Final drone tail rings out over black.
FINAL FRAME: Pure black screen, faint outline of the two buttons. Held 1.0 s.

---

## ElevenLabs VO chunks

Paste each chunk as its own generation. Keep the voice and settings identical across all chunks.

**VO 01 (0:00–0:10)**
> The text came at two fourteen a.m. ... It was from no name. ... Then the phone buzzed again.

**VO 02 (0:10–0:20)**
> Stay indoors. Do not answer. ... Her apartment is on floor nine. ... The stairs are the only way down.

**VO 03 (0:20–0:30)**
> Rule number one. Don't answer unknown calls. ... It's her mother's voice.

**VO 04 (0:30–0:40)**
> Rule number two. Count the stairs. ... Count every step. ... There's one more step than there should be.

**VO 05 (0:40–0:50)**
> Rule number three. Porch light off. ... The lobby light is on. Don't go toward it.

**VO 06 (0:50–1:00)**
> Someone is already in the doorway. ... Rule number four. Never say yes to the door.

**VO 07 (1:00–1:10)**
> It asks, "Can I come in?" ... It says her name right. ... It says it wrong.

**VO 08 (1:10–1:20)**
> Do you open it?

---

## Editing notes

- **Pauses:** the "..." marks a half-second beat. ElevenLabs will respect it. If the pause is too short, trim or add silence in Resolve rather than rewriting the line.
- **Sync:** each VO chunk starts at its clip's start time. If a chunk runs long, shorten the gap before the next clip instead of speeding up the voice.
- **Rule cards:** the narration on rule cards should start within 0.3 s of the red underline wipe.
- **Keep it original:** every line and rule here is new. Don't reuse the reference's captions or rule wording.
