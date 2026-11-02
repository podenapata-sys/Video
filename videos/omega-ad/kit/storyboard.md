# Storyboard: "আপনার ক্লিনিকের নিজের ওয়েবসাইট"

**Who it's for:** dental clinic owners in Dhaka who have good Google reviews but no website.

**What it sells:** Future Stack Solutions builds the website. Omega Dental (omegadentalbd.com) is
the working proof.

**Format:**
- Main: 30 s, 9:16 vertical, 1080×1920, 30 fps (Facebook/Instagram Reels, Stories, YouTube Shorts).
- Cut-down: 15 s.
- Square 1:1 and 16:9 variants: same scenes, reflowed.

**Rules:**
- No prices of your service anywhere.
- No numbers that cannot be shown to be true.
- On-screen text is Bangla-led, with short English where people use it.

## Main version: 30 seconds

| # | Time | Visual (asset) | On-screen text | Motion |
|---|---|---|---|---|
| 1 | 0.0–3.0 | **Map listing card** built in HTML (not a copy of Google's UI): pin icon, "আপনার ক্লিনিক", 5 stars, two buttons "Directions" and "Call", and a dashed, empty third slot labelled "Website". `icons/map-pin.svg` | Line A (0.2 s): **রোগী গুগলে আপনার ক্লিনিক খুঁজে পেলেন…**<br>Line B (1.6 s): **…কিন্তু Website নেই।** | Card slides up 80 px and fades in (0.5 s, power3.out). At 1.6 s the empty "Website" slot pulses orange twice. Line A slides out left as Line B slides in. |
| 2 | 3.0–7.0 | Three chat bubbles (`icons/chat.svg`) stacking up, plus a clock (`icons/clock.svg`) showing "রাত ১১:০০" | Bubbles: **দাম কত?** · **কখন খোলা?** · **অ্যাপয়েন্টমেন্ট নেওয়া যাবে?**<br>Caption (5.2 s): **একই প্রশ্ন, দিনে বারবার।** | Bubbles pop in 0.35 s apart (scale 0.6→1, back.out). The clock hand ticks. The bubbles get a soft shake on the caption. |
| 3 | 7.0–10.5 | Phone mockup with `screens/phone/01-home-hero.png` | Title: **নিজের ওয়েবসাইট — আপনার ক্লিনিকের নামে**<br>Small: **উদাহরণ: omegadentalbd.com** | Phone rises from the bottom and settles with a slight tilt (rotate 4°→0). A teal glow behind it. The title types on word by word. |
| 4 | 10.5–13.5 | Phone with `screens/phone/03-price-list.png` | **দামের তালিকা — উত্তর আগেই** + `icons/price-tag.svg` | The screenshot pans up slowly inside the phone (≈300 px). The icon pops beside the title. |
| 5 | 13.5–17.0 | Phone with `screens/phone/05-booking-form.png` | **অনলাইন বুকিং — রাতেও**<br>Small: **সাথে সাথে ইমেইল আর গুগল শিটে** | A tap ring pulses on the "Treatment needed" field, then a green `icons/check-circle.svg` stamps over the phone corner. |
| 6 | 17.0–19.5 | Phone that cross-fades `01-home-hero.png` to `09-home-hero-bangla.png` | **বাংলা + English** + `icons/language.svg` | A pill toggle (EN ⇄ বাংলা) slides. The screenshot cross-fades as it moves. |
| 7 | 19.5–23.0 | Laptop-style card with `screens/admin/02-dashboard-records.png`, then a second card with `screens/admin/01-editor-prices.png` sliding over it | **দাম ও ছবি নিজেই বদলান**<br>then **রোগীর রেকর্ড ও পেমেন্ট — এক জায়গায়** | Slow Ken-Burns zoom (1.0→1.08) on the dashboard. The editor card slides in from the right at 21.2 s. Small label: "নমুনা ডেটা". |
| 8 | 23.0–26.0 | Three tiles with icons: `bolt.svg`, `globe-domain.svg`, `shield-check.svg` | **মাসে ০ টাকা হোস্টিং** · **ডোমেইন আপনার নামে** · **ফোনে দ্রুত, ধীর নেটেও** | The tiles drop in 0.25 s apart. The "০" tile does a small number roll from ১০০০ to ০ (a playful touch; it shows no price). |
| 9 | 26.0–30.0 | CTA card on a teal→blue gradient | Big: **আপনার ক্লিনিকের নাম দিয়ে ফ্রি নমুনা পেজ**<br>**WhatsApp: 01632-932249**<br>Footer: **Future Stack Solutions** · omegadentalbd.com দেখে নিন | The card scales in. The WhatsApp line gets a soft pulse at 27.5 s and 29 s. Hold the last frame for at least 1.5 s. |

**Sound:**
- One upbeat, light background track at about −18 LUFS, so it sits under any voiceover.
- Soft "pop" effects on scene-2 bubbles, a "tick" on scene-5's check, and a "whoosh" on scene 3.
- Add your own licensed music; see `README.md`.

## Cut-down: 15 seconds
Scenes 1 (0–2.5), 3 (2.5–5.5), 5 (5.5–9), 7 (9–12), 9 (12–15). Shorten each scene's motion
proportionally. Keep scene 9's last frame on screen for at least 1.2 s.

## Optional voiceover (Bangla, about 30 s)
1. "রোগী গুগলে আপনার ক্লিনিক খুঁজে পেলেন — কিন্তু ওয়েবসাইট নেই।"
2. "তাই দাম, সময়, অ্যাপয়েন্টমেন্ট — একই প্রশ্ন দিনে বারবার।"
3. "নিজের ওয়েবসাইট — আপনার ক্লিনিকের নামে। যেমন ওমেগা ডেন্টাল।"
4. "দামের তালিকা আর অনলাইন বুকিং — রাতেও।"
5. "বাংলা আর ইংরেজি। দাম আর ছবি আপনি নিজেই বদলাবেন।"
6. "মাসে শূন্য টাকা হোস্টিং, ডোমেইন আপনার নামে।"
7. "আপনার ক্লিনিকের নাম দিয়ে ফ্রি নমুনা পেজ দেখতে — WhatsApp করুন।"

## Square (1:1, 1080×1080) and landscape (16:9, 1920×1080)
- **Square:** the phone mockup sits on the right half and the text on the left half. Drop scene 2's clock.
- **Landscape:** the phone sits on the right third, the text on the left two-thirds. Scene 7's dashboard can go full width.
