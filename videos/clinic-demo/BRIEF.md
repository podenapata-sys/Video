---
workflow: general-video
flow: automation
storyboard: no
message: "Clinics lose patients after hours; our website + AI chatbot + auto-booking captures them 24/7."
destination: cold DMs, Facebook/Instagram Reels
aspect: "9:16"
length: 55s
language: en
audience: dental clinic owners
---

# Future Stack Solutions — Clinic Demo Template

## Intent
Personalized cold-outreach demo for dental clinics. One template, re-rendered per clinic
with the `clinicName` variable. Hook: "How dental clinics stop losing patients at 9 PM."

## Customizations
- Style borrowed from user's reference Reels: phrase captions in a dark pill with an accent
  keyword, a top progress stepper (Website → AI Chatbot → Auto-Booking), framed mock UI
  cards, time badges (9:14 PM).
- No avatar. Voiceover added (male, confident); captions mirror it. Music can be added later.
- CTA: "<Clinic>, want this for your clinic? Reply YES."

## Assets
- `assets/logo.jpg` — Future Stack Solutions logo (user supplied).
- Voiceover: Kokoro local TTS, voice am_michael @1.05x, per-scene lines in assets/vo/ mixed to voiceover.wav.
- Brand: electric blue (#1E6BFF / #0B3FD6), charcoal (#15171C), light gray canvas.
- UI screens are illustrative mocks (no real client data).

## Notes
- Render per clinic: `npx hyperframes render --variables '{"clinicName":"Bright Smile Dental"}'`
