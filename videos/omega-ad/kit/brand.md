# Brand sheet

## Colours

| Token | Hex | Use |
|---|---|---|
| `--teal` | `#57C3AD` | Accents, glow, check marks |
| `--teal-dark` | `#2C8A78` | Small labels on light backgrounds |
| `--blue` | `#2B6CB0` | Second gradient stop, links |
| `--navy` | `#13294E` | Headlines on light backgrounds, dark backgrounds |
| `--orange` | `#F08A24` | Attention: the empty "Website" slot, the WhatsApp pulse |
| `--ink` | `#16323C` | Body text |
| `--muted` | `#5B7682` | Small print |
| `--bg` | `#F4F8FA` | Light background |
| `--card` | `#FFFFFF` | Cards |

- **Main gradient:** `linear-gradient(135deg, #57C3AD 0%, #2B6CB0 100%)`
- **Dark gradient (CTA):** `linear-gradient(120deg, #13294E 0%, #2B6CB0 100%)`

## Fonts (all in `fonts/`, load with @font-face, never from the web at render time)

| File | Family | Weights | Use |
|---|---|---|---|
| `noto-bengali.woff2` | Noto Sans Bengali | 400–800 (variable) | **Bangla headlines and body.** Has real bold. |
| `kalpurush.woff2` | Kalpurush | 400 only | Optional Bangla accent (a softer, rounder look). Never synthesise bold. |
| `sora.woff2` | Sora | 600–800 (variable) | English headlines, brand name, phone number |
| `inter.woff2` | Inter | 400–700 (variable) | English small text, subtitles |

```css
@font-face{font-family:"Noto Sans Bengali";src:url(fonts/noto-bengali.woff2) format("woff2");font-weight:400 800;font-display:block}
@font-face{font-family:"Kalpurush";src:url(fonts/kalpurush.woff2) format("woff2");font-weight:400;font-display:block}
@font-face{font-family:"Sora";src:url(fonts/sora.woff2) format("woff2");font-weight:600 800;font-display:block}
@font-face{font-family:"Inter";src:url(fonts/inter.woff2) format("woff2");font-weight:400 700;font-display:block}
/* Bangla first, so mixed lines like "বাংলা + English" use each font for its own script */
.bn{font-family:"Noto Sans Bengali","Sora",sans-serif}
.en{font-family:"Sora","Noto Sans Bengali",sans-serif}
```

> Bangla text must use one of the two Bangla fonts above. A system fallback renders boxes or
> broken conjuncts (যুক্তাক্ষর). Wait for `document.fonts.ready` before the first frame.

## Type scale for 1080×1920

| Role | Size | Weight | Line height |
|---|---|---|---|
| Hook / scene title (Bangla) | 84–96 px | 700 | 1.25 |
| Feature line | 64–72 px | 700 | 1.3 |
| Small line under a title | 40–44 px | 500 | 1.4 |
| Subtitle track | 40 px | 600, white on 70% navy pill | 1.35 |
| CTA phone number | 72 px Sora | 800 | 1.1 |

- Nothing smaller than 36 px.
- Keep each line on screen at least 1.5 s (Bangla reads slower than English at the same size).

## Safe zones (9:16)

- **Top 220 px:** the platform shows the profile name here, so no text.
- **Bottom 380 px:** captions and buttons cover this, so no text and no CTA.
- **Right 140 px:** like, comment and share buttons, so keep text out.
- **Content box:** x 80–940, y 220–1540.

For 1:1 and 16:9, keep a 6% margin on every side.

## Phone mockup (CSS, so the screenshots stay sharp)

```css
.phone{width:620px;aspect-ratio:1170/2532;border-radius:76px;padding:22px;background:#0E1B33;
  box-shadow:0 60px 120px -40px rgba(19,41,78,.55),0 0 0 3px #22345a inset}
.phone .screen{width:100%;height:100%;border-radius:56px;overflow:hidden;background:#fff;position:relative}
.phone .screen img{width:100%;display:block}      /* pan by animating translateY on the img */
```

The phone screenshots are 1170 px wide (390 px at 3×), so a 620 px-wide phone shows them crisp.
`01-home-hero.png` and `09-home-hero-bangla.png` are cropped to 1170×2100. Let them start at the
top of the screen and fill the rest with white or a soft gradient.

## Icons
`icons/*.svg` are 24×24 line icons drawn with `stroke="currentColor"`. **Inline the SVG markup**
in the HTML so CSS `color:` sets their colour. Loaded through `<img>`, they stay black.

## Do not
- **No Google Maps, Facebook or WhatsApp logos, and no copies of their screens.** Draw the
  generic map card in scene 1 from scratch. The word "WhatsApp" next to your number is fine.
- **No before/after photos.** The ones on Omega's site are illustrative, not real patients.
- **No borrowed figures.** Leave out Omega's review count, patient count or ratings: they are the
  clinic's, not yours.
- **No emoji inside the video frames.**
