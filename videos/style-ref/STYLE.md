# Style breakdown: "20 video effects in 20 seconds, built by Claude" (reference, 720x720, 26 s)

Contact sheets: `sheet_overview.png` (whole video) and `sheet_burst.png` (18.3–21.2 s, every 0.1 s).
Analysis only. The reference's footage, audio and creator are not reused.

## Format
- **The presenter is the backbone.** One talking-head shot runs the whole time: he speaks to camera in a dark, moody room, waist-up and centred. Every effect is applied to this shot or replaces it for less than a second, then the edit returns to him.
- **The progress checklist is the signature.** It's a dark-green sidebar panel on the right, about 28% of the width, titled "IN THIS VIDEO 07/20". It lists all 20 effect names, highlights the current one in a white pill, and ends with a "+40 more effects" gold pill. It's always on screen, and the counter ticks with each effect.
- **The hook comes in the first 2 s.** White rounded pill labels at the top read "20 video effects in 20 seconds" / "built by Claude". The number promise plus speed makes people stay to see them all.
- **Pacing:** about 1 effect per second. Holds are almost never longer than 1.5 s on an un-effected shot. The audio is the creator's continuous voice, around -14 LUFS, with no music gaps.
- **CTA, twice:** at about 9 s and 11 s, a "Comment EDIT to get access to these" pill appears with a fake comment UI. The keyword is the CTA, which drives comments and therefore reach.
- **Ending:** a "blow away" effect (the presenter disintegrates into particles) on the last effect, ending on an empty chair.

## Effect vocabulary (time → effect → how to rebuild it in HyperFrames)
| Time | Effect | Rebuild |
|---|---|---|
| 0.1 | Live cursor | a fake mouse pointer plus a "Claude" name tag moving over the frame (GSAP path) |
| 0.6 | Bounding box | a selection box with handles and a size label around the presenter (SVG rect) |
| 2.0 | Clone row | 4–5 copies of the presenter's head cut-out in a row (cutout from bg-remove, staggered) |
| 3.0 | Day dial | a giant clock or dial face rotating behind the head (SVG) |
| 6.0 | Code body | the body replaced by ASCII/code text (text mask over the cutout) |
| 7.5 | Post wall | a grid of tiles behind the head with a counter "1,711 posts" |
| 7.8 | Letter dive | a full-frame giant serif letter on a cream background, the camera diving into it |
| 9.0 | Comment drop | a social comment box drops in with the CTA keyword |
| 13.0 | Layer explode | the frame tilts into 3D with layers separating (perspective transform) |
| 14.3 | Sketch words | a cream paper background, the presenter as a sketch, a big hand-lettered word |
| 18.4 | Banknote | the presenter's face engraved on a banknote, with a big number counting up (count-up) |
| 19.5 | Voice note | a chat voice-note bubble with a waveform and "Delivered" at the top |
| 20.3 | Impact frame | black/white halftone, manga speed lines, big "IMPACT" text, strobing at 10 fps |
| 22.7 | Press front | a newspaper front page ("The Daily Reel") with a halftone photo of the presenter |
| 24.0 | Paper tear | the newspaper tears apart to reveal the video underneath |
| 25.9 | Blow away | the presenter dissolves into particles, leaving the empty room |

## Look
- **Grade:** dark, desaturated teal/green shadows and warm practical lamps. The panel colour (#123a2c-ish) matches the room.
- **Type:** clean sans for the UI (panel, pills) and an editorial serif for the "print" effects (banknote, newspaper, letter). Bold condensed sans for IMPACT.
- **Motion:** quick (0.15–0.3 s) ease-out pops. Hard cuts between effect moments, with no soft crossfades. The burst at 18–21 s is three effects in 3 s, with strobing.

## How this maps to a Future Stack promo (9:16)
- **Presenter:** the user on camera, talking. This is required; the style doesn't work without a person.
- **Checklist panel (Bangla), "এই ভিডিওতে 0X/07":** AI চ্যাটবট, অনলাইন বুকিং, ল্যান্ডিং পেজ, অটো রিমাইন্ডার, রোগীর রেকর্ড, রিভিউ সংগ্রহ, ফেসবুক লিড অটোমেশন. On 9:16 it sits as a slim right column, or a bottom strip above the Reels-UI safe zone.
- **Each service gets one effect,** using the Omega Dental screens already in the repo:
  - a phone pops up with the chatbot conversation;
  - the booking form fills itself;
  - a cursor clicks "Book";
  - a notification stack shows the reminders;
  - a counter "৩২ টা নতুন বুকিং" counts up, banknote-style;
  - a "Daily Reel"-style newspaper front page announces the clinic going online.
- **Hook:** "আপনার ক্লিনিকের জন্য ৭টা কাজ, AI দিয়ে, ২০ সেকেন্ডে".
- **CTA:** "কমেন্ট করুন DEMO", with a comment-box effect at about 40% and again at the end.
