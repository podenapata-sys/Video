# Omega Dental ad kit (for HyperFrames in Claude Code)

**বাংলায় সংক্ষেপে:**
এই ফোল্ডারে বিজ্ঞাপন ভিডিও বানানোর সব উপকরণ আছে: স্ক্রিনশট, ফন্ট, আইকন, দৃশ্য-ভিত্তিক স্ক্রিপ্ট, সব
লেখা, ব্র্যান্ডের রং, আর Claude Code-এর জন্য তৈরি প্রম্পট। কম্পিউটারে একটা ফোল্ডারে আনজিপ করুন, সেখানে
Claude Code খুলুন, আর `CLAUDE_CODE_PROMPT.md`-এর প্রম্পটটা পেস্ট করুন।

**The ad:** 30 seconds, vertical, aimed at dental clinic owners. Hook: "your clinic has good reviews but
no website". Then Omega Dental's live site as proof. Then a free-sample-page CTA to your WhatsApp.
No prices.

## What's inside

| Path | What it is |
|---|---|
| `CLAUDE_CODE_PROMPT.md` | **Start here.** The prompt to paste into Claude Code, and what to install first. |
| `storyboard.md` | 9 scenes with exact timings, visuals, on-screen text, motion; a 15 s cut; an optional Bangla voiceover script; square and wide layouts. |
| `copy.md` | Every line of text: 3 hooks, feature lines, CTAs, English subtitles, Facebook/Instagram post text, hashtags, cover text. |
| `brand.md` | Colours, fonts and @font-face code, type sizes, 9:16 safe zones, phone-mockup CSS, the do-not list. |
| `starter/index.html` | Scenes 1 and 9, already built and tested (frames rendered, Bangla checked). Open it in a browser to see the layout. |
| `fonts/` | Noto Sans Bengali, Kalpurush, Sora, Inter (woff2). See `LICENSES.md`. |
| `icons/` | 14 line icons (SVG, colour via CSS when inlined). |
| `screens/phone/` | 7 phone screenshots of omegadentalbd.com, 1170 px wide (390 px at 3×), taken 2 Nov 2026 from the live code. |
| `screens/desktop/` | Homepage hero and treatments page, 2880 px wide. |
| `screens/admin/` | Content editor (prices tab) and the dashboard with **8 fake "Sample Patient" records**. No real patient data. |

### Screenshots

| File | Shows | Used in scene |
|---|---|---|
| `phone/01-home-hero.png` | Homepage hero, English, "Open now" badge | 3, 6 |
| `phone/02-services.png` | Service cards | spare |
| `phone/03-price-list.png` | Treatment price list with Book buttons | 4 |
| `phone/04-cost-calculator.png` | Cost estimator with a Root Canal estimate | spare |
| `phone/05-booking-form.png` | Booking form, treatment pre-selected | 5 |
| `phone/06-service-page.png` | Root Canal service page with its headline price | spare |
| `phone/09-home-hero-bangla.png` | Homepage hero in Bangla | 6 |
| `desktop/01-home-desktop.png` | Desktop hero | 16:9 version |
| `desktop/02-treatments-desktop.png` | All treatments page | 16:9 version |
| `admin/01-editor-prices.png` | Owner's content editor | 7 |
| `admin/02-dashboard-records.png` | Owner's dashboard (sample data) | 7 |

The hero screenshots are cropped above Omega's own review and patient badges on purpose: those numbers
are the clinic's, not yours. The gallery and before/after images are left out because they are
illustrative.

## Before you publish the ad
1. **Mehedi bhai's OK.** The ad shows Omega Dental's name and website as your example. Send him the
   finished video and get a yes before it goes public.
2. **Music.** Use a track you're allowed to use in ads: YouTube Audio Library (filter "No attribution
   required"), Pixabay Music, or a paid licence. Facebook's in-app "Sound Collection" also works for
   ads made inside Facebook.
3. **Check the number.** WhatsApp 01632-932249 appears in scene 9 and in the post text.
