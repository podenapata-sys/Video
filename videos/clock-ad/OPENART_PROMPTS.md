# LED Desk Clock: AI UGC ad prompts for OpenArt

Adapted from "The AI UGC Ad Workflow" playbook. Run the steps in order in **your OpenArt account**.
Each grey block is one prompt; when a step has several blocks, paste them one after the other into a single prompt.

> ⚠️ **Before Step 3:** replace every `৳[X]` with your real price. Search this file for `[X]`.

---

## Step 1: Clock product sheet
**Settings:** OpenArt → Image → GPT Image 2.5 → Sunburst mode, quality high, 4K, 16:9, Auto Polish off.
**Attach:** your product photo (the clock on the wooden desk).

```
A single catalogue product sheet photograph of one LED digital desk clock, shown in ten panels arranged as a clean grid of 5 columns by 2 rows, thin even white gutters between panels, every panel showing the identical clock, a small dark gray caption in plain sans-serif under each panel naming the view.

The product: exactly the clock in the attached reference photo. A long low rectangular desk clock, about 2.8 times wider than it is tall, roughly 4 cm deep, with softly rounded corners. The whole front is one glossy black glass panel, mirror-like, framed by a thin matte black plastic case. The display, when on, shows large bright white seven-segment digits reading exactly 0-2-:-3-0, two small square green colon dots between the 2 and the 3, the letters PM in small white bold sans-serif directly left of the digits, and on the far left a single vertical column of seven small white bold sans-serif day names reading exactly Mon, Tue, Wed, Thu, Fri, Sat, Sun from top to bottom. Nothing else is on the display or the case: no logo, no brand name, no temperature, no date, no icons, no buttons on the front, no stickers. A thin white power cable leaves the left side of the case. The display always reads exactly 02:30 PM in every panel where it is on. The clock is identical in shape, colour, proportion and display layout in every panel.

Panels, left to right, top row then bottom row:
Panel 1, caption FRONT: straight-on front view, display on, 02:30 PM, digits razor sharp.
Panel 2, caption FRONT OFF: straight-on front view, display switched off, the panel a uniform glossy black mirror with no digits visible.
Panel 3, caption LEFT SIDE: left side profile, the white cable leaving the case.
Panel 4, caption RIGHT SIDE: right side profile, plain matte black.
Panel 5, caption BACK: back view, plain matte black case, the cable port visible, no text or labels.
Panel 6, caption TOP: top-down view showing the slim depth of the case.
Panel 7, caption THREE-QUARTER: three-quarter view from the front left, display on, 02:30 PM readable.
Panel 8, caption IN HAND: the clock held upright in one adult hand at chest height, fingers only on the side edges, display on and fully unobstructed, 02:30 PM readable.
Panel 9, caption ON DESK: the clock standing on a light oak desk beside a closed laptop and a small potted succulent, display on, 02:30 PM.
Panel 10, caption DIGITS: tight close-up of the display, the white 02:30 digits, green colon dots and PM filling the panel, every segment crisp and complete.

Seamless light neutral gray studio backdrop identical in every panel, soft even diffused catalogue lighting, subtle soft contact shadow only, true colour, the glass shows only a soft even studio reflection, no reflections of a studio or photographer, crisp real material texture, photographed not generated.
```

**Check before moving on:** every panel says **02:30**, the colon dots are green, the days read Mon→Sun, and there's no extra logo. If any panel is wrong, regenerate. (Playbook rule: *a video model can only copy what it can actually see on the sheet.*)

---

## Step 2: Creator sheet (your own face)
**Settings:** same as Step 1. **Attach:** your headshot.
Paste the three blocks below as **one** prompt.

### Part 1: the person and the outfit
```
A three-panel character reference sheet composed as one horizontal frame, divided into three equal vertical panels side by side, thin clean separation between panels, the same figure and the same outfit rendered identically across all three.

The man from the attached reference photo, keeping his exact face and identity. A young man in his early twenties, about 172 cm, slim build, an ordinary believable person, not a model. Warm light-brown South Asian skin with a natural slightly uneven tone. Short thick black hair swept up and back on top, with a short tapered fade at the temples and around the ears. Thick straight black brows, dark brown almond-shaped eyes, a straight nose, a short neatly trimmed black beard along the jaw and chin joined to a full black moustache, natural unretouched skin texture. No makeup. Short clean unpolished fingernails.

A plain navy-blue cotton crew-neck t-shirt, regular fit, short sleeves ending mid-bicep, no print or logo. Dark charcoal cotton joggers with an elastic waist and cuffed ankles. Barefoot. A plain black analog wristwatch with a black strap on the left wrist. No other jewelry.
```

### Part 2: the three panels
```
LEFT PANEL: full body front view, no head, no neck, and no hair. The body stands squared to camera from the shoulders down to the bare feet, arms relaxed at the sides, hands open and loose, weight even across both feet. There is no head, no neck, and no hair at all, nothing rises above the shoulder line. The crew neckline of the t-shirt holds its own shape at the top of the garment and its opening is an empty dark hollow looking down into the inside of the t-shirt, with the inner back of the fabric faintly visible inside the opening. The garment reads as if worn by an invisible body, full three-dimensional shape, natural drape, real fabric tension across the chest and shoulders, but nothing emerging from the neckline. No stump, no skin, no cut edge, no anatomy, no fade, no blur, no ghosting, no transparency in the body. The panel keeps full headroom, generous empty mid-gray backdrop above the shoulders, so the figure sits at the same scale and position in the frame as a normal full-body portrait.

CENTER PANEL: full body rear view, head attached. The same figure photographed from directly behind, standing straight, the black hair swept up on top and the short tapered fade at the back and sides, the plain back of the navy t-shirt, the charcoal joggers, arms relaxed at the sides, hands loose, weight even across both feet, from the top of the head down to the bare feet.

RIGHT PANEL: tight chest-up portrait, identity lock. The same figure framed from just above the top of the head down to the collarbones and the very top of the t-shirt only, the face filling most of the panel, a true close-up. Body squared to camera, head level, eyes directly to camera, lips closed and relaxed, neutral controlled expression. The swept-up black hair and fade, the thick straight brows, dark brown eyes, the trimmed beard and full moustache, natural skin texture, all clearly readable at close range, matching the attached reference photo exactly.
```

### Part 3: the backdrop and the lighting
```
18% neutral gray seamless studio backdrop applied uniformly across all three panels, one single flat uniform value corner to corner in every panel, no seam line, no gradient, no hotspot, no vignette, no falloff to black or white, and the identical gray value in all three panels. Relight from scratch overriding any reference lighting: completely flat shadowless illumination in every panel, one enormous soft frontal source at camera position with matched equal fill from camera-left, camera-right, above, and below, so both sides of the face and body read at exactly the same brightness. No key-and-fill ratio, no modelling, no shadow side, no nose shadow, no under-chin shadow, no rim light, no hair light, no specular hotspot. Zero shadow cast onto the background in any panel. No contact shadow, no drop shadow, no ambient occlusion on the floor beneath the feet. Extremely low contrast, even, milky, catalogue-flat, identical in every panel. Skin and fabric read matte and velvety, no shine, no gloss, no oily T-zone. Skin renders at its true natural skin tone, identical in value and hue across the face, arms, and feet in every panel, never darkened, never pale or washed-out. The navy of the t-shirt and the charcoal of the joggers render true and consistent across all three panels. Real fine even pore texture, real fabric weave and drape, never plastic, never waxy, never harsh. Photographed on a 50mm prime, even sharpness, soft natural film grain. Photographed not generated.
```

**Why the suit is gone:** the playbook's rule is to match the creator to the room. A suit at a home desk looks fake. Use a casual outfit.

---

## Step 3: Generate the ad (Seedance 2.5)
**Settings:** OpenArt → Video → Seedance 2.5 → text to video. Upload the **creator sheet first** and the **product sheet second**. 1080p, 9:16, 30 seconds, audio on, Auto Polish off.

> 🧪 **Test first:** before the full 30s, run **only Beat 1** as a 5s generation to check how well the Bangla lip-sync works. If the Bangla speech is broken, use the fallback at the bottom.

### Part 1: the references and the scene
```
@Image1 is the creator reference sheet: the man from the first reference image. His face is exactly the face in the right-hand portrait panel of @Image1 (early twenties, warm light-brown South Asian skin, short black hair swept up with a tapered fade, thick straight black brows, dark brown eyes, short trimmed black beard joined to a full moustache), and his outfit is exactly the outfit in the other panels: plain navy crew-neck t-shirt, dark charcoal joggers, black analog watch on the left wrist.
@Image2 is the product reference sheet: the LED digital desk clock from the second reference image, a long low rectangular clock with a glossy black glass front, large white seven-segment digits, two green colon dots, PM to the left of the digits, and a column of day names Mon to Sun on the far left. The clock looks identical to @Image2 in every shot. Its display always reads exactly 02:30 PM, every digit segment complete and unchanged, no other numbers, no logo, no text on the case. This clock is the only clock in the scene. The clock is never in front of his mouth, nose or eyes.

Vertical video from a phone propped on a stack of books on the far edge of a desk, fixed and static, lens at his eye level, squared to him. A small Dhaka bedroom in the morning: a light oak study desk against a pale wall, a window to camera-left with soft daylight through a thin curtain, a single bed with a rumpled pillow partly visible behind him on camera-right, a small potted plant and a few books on the desk. Phone-camera look: warm natural white balance, slight auto-exposure drift, a little noise in the shadows, no grading, no studio light. In his shots the camera never moves; all movement comes from him. His face and mouth stay clearly visible, frontal and large in frame, whenever he speaks. He talks like he is telling a friend something useful, relaxed and a little amused.
```

### Part 2: the seven beats and the audio
```
Beat 1 (0-4s). Medium shot. He is half-turned toward the bed, patting under the rumpled pillow, looking for his phone, mildly annoyed. He gives up, turns straight to the lens with a raised eyebrow and says: "ঘরে ঘড়ি আছে, অথচ সময় দেখতে ফোন খুঁজতে হয়?"

Beat 2 (4-8s). Same fixed framing. He brings the clock up into frame with one hand and holds it upright beside his face on the camera-left side at shoulder height, display facing the lens, reading 02:30 PM, his whole face uncovered on the camera-right side. He nods at it and says: "এইটা দেখেন।"

Beat 3 (8-12s). Cut to an insert shot of the clock standing on the desk, no hands in frame, nobody speaks. The camera slowly pushes in on the display until the white 02:30 digits and PM fill most of the frame, every segment crisp and complete. Continuous smooth motion, no stopping.

Beat 4 (12-17s). Cut back to the fixed framing of him at the desk, the clock now standing on the desk in the lower part of the frame beside him, display toward the lens. He points at it, then gestures across the room and says: "বড় ডিজিট, রুমের যেকোনো জায়গা থেকে দেখা যায়। সপ্তাহের দিনও দেখায়।"

Beat 5 (17-21s). Cut to an insert shot of the clock on the desk, no hands in frame, nobody speaks. The camera moves in one slow gentle arc from the front-left to the front-right of the clock, a soft band of window light sliding across the glossy black glass, the 02:30 PM display staying sharp and readable the whole time.

Beat 6 (21-27s). Cut back to the fixed framing of him. He leans slightly toward the lens, friendly and direct, and says: "দাম ৳[X], ঢাকায় ডেলিভারি ফ্রি। অর্ডার করতে ইনবক্স করুন।"

Beat 7 (27-30s). Same framing. He smiles, points down toward the bottom of the screen and says: "লিংক নিচে।" He reaches toward the phone as if to stop recording as the clip ends.

Audio: his voice speaks natural conversational Bangla with a Dhaka accent, clear, forward and dry with phone-mic character, every word spoken in sync with his lips, nothing spoken outside the quoted lines. Quiet bedroom ambience under it, faint street traffic far away outside the window. Beats 3 and 5 have no speech, only the room tone. No music, no voiceover, no captions, no on-screen text.
```

---

## Step 4: Send me the result
Upload the Seedance MP4 here (exactly as it came out, nothing changed). I will:
1. **Replace beats 3 and 5** with my pixel-exact clock clips (`clip2_pushin`, `clip3_orbit`). AI video often bends the digits, but mine are your real photo, so the time can't warp.
2. Add **Bangla captions** timed to your speech.
3. Add the **5s offer card** (price, free delivery in Dhaka, "ইনবক্স করে অর্ডার করুন" button) at the end.
4. Render the final 9:16 ad for Facebook.

## Fallback if Bangla lip-sync fails in the test
Delete every quoted line and the "speaks" wording from Part 2, and add: *"He does not speak in any beat; he reacts with expressions and gestures only. Audio: room ambience only."*
Then record your own voice reading the lines (`FILMING.md`), and I'll lay it under the video with captions.

## Notes from the playbook that matter here
- **The clock must never cover his mouth**, or the lip-sync breaks on that beat.
- **Product close-ups have no dialogue.** That makes them the safest shots, and it's exactly why I can replace them with exact clips.
- **Every state the ad shows must be on the product sheet.** The ad uses "in hand" and "on desk", so both are panels.
