# LED Desk Clock: AI UGC ad in Google Flow (Veo)

Same playbook, rebuilt for **Google Flow**. Key difference: Flow makes **8-second clips**, so the ad is
**3 talking shots** made in Flow plus **2 product inserts I already made** (pixel-exact, so the digits can't warp).

| Order | Shot | Made in | Length in final |
|---|---|---|---|
| 1 | **Shot A**: hook + clock reveal (you talking) | Flow | ~7s |
| 2 | Push-in on the digits | ✅ done (`clip2_pushin`) | 4s |
| 3 | **Shot B**: features (you talking) | Flow | ~7s |
| 4 | Orbit with a light sweep | ✅ done (`clip3_orbit`) | 4s |
| 5 | **Shot C**: price + CTA (you talking) | Flow | ~8s |
| | **Total** | | **≈30s** |

You only generate **3 clips**. I don't generate the product close-ups at all, which saves credits and keeps the time exact.

> ⚠️ Replace `৳[X]` with your real price before generating Shot C.

---

## Step 1: Make the two reference images ("ingredients")
Make them in Flow's image generator (or Gemini / Nano Banana, or any image tool). Use the **exact prompts in
`OPENART_PROMPTS.md`**:
- **Step 1 (product sheet)**, with your clock photo attached.
- **Step 2 (creator sheet: Parts 1+2+3 pasted together)**, with your headshot attached.

Check the product sheet: every panel reads **02:30 PM**, the days read Mon→Sun, and there's no extra logo.

## Step 2: Flow settings for every shot
- Mode: **Ingredients to Video**
- Ingredients: **creator sheet** + **product sheet** (the same two for all 3 shots, so you stay consistent)
- Aspect ratio: **9:16 (portrait)**
- Model: the **highest-quality Veo** option your plan has, with **audio on**
- Generate **2–4 variations** of each shot and keep the best one

### Paste this "scene lock" at the TOP of all three prompts (identical every time)
```
Vertical 9:16 selfie-style UGC video filmed on a phone propped on a stack of books on a desk, fixed and static, lens at eye level. A small Dhaka bedroom in the morning: a light oak study desk against a pale wall, soft daylight through a thin curtain from the left, a single bed with a rumpled pillow behind him on the right, a small potted plant and a few books on the desk. Phone-camera look: warm natural white balance, slight noise, no grading, no studio lights, no music, no on-screen text, no captions, no subtitles.
The man is exactly the man in the creator reference image: early twenties, warm light-brown South Asian skin, short black hair swept up with a tapered fade, thick straight black brows, dark brown eyes, short trimmed black beard joined to a full moustache, wearing a plain navy crew-neck t-shirt and a black analog watch on his left wrist. Same face and outfit in every shot.
The clock is exactly the LED digital desk clock in the product reference image: a long low rectangular clock with a glossy black glass front, large white seven-segment digits reading exactly 02:30, two green colon dots, PM to the left, and a column of day names Mon to Sun on the far left. Its display always reads exactly 02:30 PM. No logo, no other text. The clock never covers his mouth, nose or eyes.
He speaks natural conversational Bangla with a Dhaka accent, clear and close to the phone mic, lips perfectly in sync. He says only the quoted line and nothing else. Quiet room ambience only.
```

## Step 3: The three shots (paste after the scene lock)

### Shot A: hook (8s)
```
He is half-turned toward the bed, patting under the rumpled pillow looking for his phone, mildly annoyed. He gives up, turns to the lens with a raised eyebrow and says: "ঘরে ঘড়ি আছে, অথচ সময় দেখতে ফোন খুঁজতে হয়?" Then he lifts the clock into frame with one hand, holding it upright beside his face at shoulder height on the left side of the frame, display facing the lens, his face fully visible, and says: "এইটা দেখেন।"
```

### Shot B: features (8s)
```
Medium shot, the clock standing on the desk in the lower part of the frame beside him, display toward the lens reading 02:30 PM. He points at it, then gestures across the room, relaxed and confident, and says: "বড় ডিজিট, রুমের যেকোনো জায়গা থেকে দেখা যায়। সপ্তাহের দিনও দেখায়।"
```

### Shot C: price + CTA (8s)
```
Medium close-up, the clock on the desk beside him at the edge of frame. He leans slightly toward the lens, friendly and direct, and says: "দাম ৳[X], ঢাকায় ডেলিভারি ফ্রি। অর্ডার করতে ইনবক্স করুন।" Then he smiles and points down toward the bottom of the screen.
```

## Step 4: Test before you spend credits
1. Generate **Shot A only** first (2 variations).
2. Check: is the Bangla clear? Do his lips match? Does the face look like you? Is the clock correct?
3. **If the Bangla is broken or mumbled:** remove the quoted lines, replace them with *"He does not speak; he reacts with expressions and gestures only"*, and record your voice instead (`FILMING.md`). I'll put your voice and captions on top.
4. If it's good, generate Shots B and C.

## Step 5: Send me the 3 MP4s
Download each one from Flow (original, not edited) and upload them here as `shotA.mp4`, `shotB.mp4`, `shotC.mp4`, with your **price**. I'll:
- cut them together with my two clock inserts → **≈30s**
- add **Bangla captions** timed to your speech
- optionally add the 5s offer card at the end (35s total, or trim)
- render the final 9:16 MP4 for Facebook

## Flow-specific tips
- **Keep each spoken line short.** An 8s clip fits about 12–15 Bangla words. Longer lines get rushed or cut off.
- **Re-use the identical scene lock** in every shot. Changing even the room description makes the background jump between cuts.
- **Don't ask Flow to animate the digits.** That's exactly why the close-ups come from me.
- **Check that the price Veo speaks is exactly right** before you post. If it's wrong in every variation, write the price in Bangla words (e.g. "এক হাজার দুইশো পঞ্চাশ টাকা") instead of digits.
