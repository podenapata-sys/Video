# Omega Dental ad: voiceover for ElevenLabs (scene-matched)

Generate **one clip per scene** (VO_01.mp3 … VO_09.mp3) and send them all. Each line is written to fit
its scene with a little air; I place each clip at its scene start and tighten pauses if one runs long.

**ElevenLabs settings:** Eleven Multilingual v2 (or v3), a warm, confident Bangla-capable voice, Stability 50%,
Similarity 75%, Style 15%, Speaker boost on, Speed 1.0 (use 1.05–1.1 only if a clip comes out longer than its "max").

## 30-second ad

| Clip | Scene | Time | Max length | Line (paste exactly) |
|---|---|---|---|---|
| VO_01 | 1 Hook: map card | 0.0–3.0 | 2.8 s | রোগী আপনার ক্লিনিক খুঁজে পেলেন… কিন্তু ওয়েবসাইট নেই। |
| VO_02 | 2 Chat bubbles | 3.0–7.0 | 3.8 s | দাম কত? কখন খোলা? একই প্রশ্ন, দিনে বারবার। |
| VO_03 | 3 Phone: homepage | 7.0–10.5 | 3.3 s | নিজের ওয়েবসাইট, আপনার ক্লিনিকের নামে। যেমন ওমেগা ডেন্টাল। |
| VO_04 | 4 Price list | 10.5–13.5 | 2.8 s | দামের তালিকা: উত্তর আগেই। |
| VO_05 | 5 Booking form | 13.5–17.0 | 3.3 s | অনলাইন বুকিং, রাতেও। সাথে সাথে ইমেইলে। |
| VO_06 | 6 Bangla + English | 17.0–19.5 | 2.3 s | বাংলা আর ইংরেজি। |
| VO_07 | 7 Dashboard + editor | 19.5–23.0 | 3.3 s | রোগীর রেকর্ড এক জায়গায়, দাম বদলান নিজেই। |
| VO_08 | 8 Three tiles | 23.0–26.0 | 2.8 s | মাসে শূন্য টাকা হোস্টিং, ডোমেইন আপনার নামে। |
| VO_09 | 9 CTA | 26.0–30.0 | 3.5 s | আপনার ক্লিনিকের নামে ফ্রি নমুনা পেজ চাইলে, এখনই হোয়াটসঅ্যাপ করুন। |

The phone number is on screen in scene 9 and is not read out: spoken, it alone takes ~4 s.

## 15-second cut (scenes 1, 3, 5, 7, 9): reuse clips, no new recording needed

| Clip | Time | Max length | Line |
|---|---|---|---|
| VO_01 | 0.0–2.5 | 2.4 s | (same as above; if it runs long, generate at Speed 1.1) |
| VO_03 | 2.5–5.5 | 2.9 s | same |
| VO_05 | 5.5–9.0 | 3.3 s | same |
| VO_07 | 9.0–12.0 | 2.9 s | same |
| VO_09 | 12.0–15.0 | 2.9 s | for the 15 s, a shorter take: **ফ্রি নমুনা পেজ চাইলে, হোয়াটসঅ্যাপ করুন।** (save as VO_09_short.mp3) |

## Pronunciation tips
- If ElevenLabs reads "ওমেগা ডেন্টাল" oddly, write it as **ওমেগা ডেন্টাল** with a comma before it, or try "ওমেগা ডেন্টাল ক্লিনিক".
- "হোয়াটসঅ্যাপ" is spelled in Bangla on purpose so the voice says it naturally.
- Keep the ellipsis (…) in VO_01: it gives the small pause before "কিন্তু".
