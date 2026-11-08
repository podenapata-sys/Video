#!/usr/bin/env python3
"""Word timings for the exact script -> words.json (global seconds), with a speaker tag per word for styling.

  python3 scripts/words.py        (after scripts/voice.py)

Whisper cannot run here (huggingface.co, where its model lives, is blocked), so this reuses the WARMLUNE energy/pause
aligner (videos/warmlune-ad/scripts/words.py: phrase breaks matched to measured pauses, words spread by syllable weight,
onsets snapped to the energy dips between words). Caption text is always the user's script, never a transcription.
Speakers: R narrator, N neighbour (red-orange), O owner, T owner's inner thought (italic). Tags are never displayed.
"""
import importlib.util
import json
from pathlib import Path

import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("wl_words", ROOT.parent / "warmlune-ad" / "scripts" / "words.py")
wl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wl)

SCRIPT = {
    1: [("R", "সারাজীবনের কষ্টের টাকায়... এক টুকরো জমি। স্বপ্ন, একদিন এখানেই হবে নিজের ঠিকানা।")],
    2: [("N", "ভাই, এই জায়গাটা তো আমার জমির মধ্যে পড়ে!"), ("O", "কিন্তু আমার দলিলে তো এটাই আছে!"),
        ("R", "হঠাৎ শুরু হলো... সীমানা নিয়ে বিরোধ।")],
    3: [("R", "দলিল আছে, নকশাও আছে... কিন্তু আসল সীমানা কোথায়?"), ("T", "নিজের জমির সীমানাই যদি না জানি... কী করব?")],
    4: [("R", "অবশেষে তিনি যোগাযোগ করলেন, খুলনা বিভাগীয় ডিজিটাল সার্ভেয়ার এসোসিয়েশনের সঙ্গে। শুরু হলো সঠিক পরিমাপের প্রস্তুতি।")],
    5: [("R", "ল্যান্ড ডিমার্কেশন। কাগজপত্র যাচাই করে, মাঠে জমির সঠিক পরিমাপ ও সীমানা চিহ্নিতকরণ।")],
    6: [("R", "পাশাপাশি পেন্টাগ্রাফ সার্ভিস। মৌজা ম্যাপের স্কেলিং ও নকশার কারিগরি কাজ।")],
    7: [("R", "জমি নিয়ে আর দুশ্চিন্তা নয়। সঠিক তথ্য... সঠিক পরিমাপ... পেশাদার সহযোগিতা।")],
    # scene 8 (CTA voice, VC-9): timings only, to sync the CTA card; no word captions are shown
    8: [("R", "জমির সীমানা নিয়ে দুশ্চিন্তা? খুলনা বিভাগীয় ডিজিটাল সার্ভেয়ার এসোসিয়েশন। ল্যান্ড ডিমার্কেশন ও পেন্টাগ্রাফ সার্ভিস। "
              "এখনই হোয়াটসঅ্যাপ করুন। আপনার জমি, সঠিক পরিমাপের কাজে... আমরা আপনার পাশে।")],
}


def main():
    timing = json.loads((ROOT / "timing.json").read_text())
    out = []
    for sc in timing["scenes"]:
        n = sc["n"]
        words, spk = [], []
        for who, text in SCRIPT[n]:
            for w in text.split():
                words.append(w)
                spk.append(who)
        # a speaker change is also a phrase break for the aligner
        tagged = [w if (k + 1 == len(words) or spk[k + 1] == spk[k] or wl.BREAK.search(w)) else w + "," for k, w in enumerate(words)]
        a, _ = sf.read(ROOT / "assets" / "vo" / "trim" / f"vo{n}.wav", dtype="float32")
        times, ps, match = wl.align(tagged, a)
        print(f"vo{n}: {len(words)} words, {len(ps)} pauses, breaks matched at words {sorted(match)}")
        for k, (w, who, (s, e)) in enumerate(zip(words, spk, times)):
            out.append({"scene": n, "i": k, "text": w, "speaker": who, "start": round(sc["vo_at"] + s, 3),
                        "end": round(sc["vo_at"] + e, 3), "break": bool(wl.BREAK.search(w)) or (k + 1 < len(spk) and spk[k + 1] != who)})
    (ROOT / "words.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for x in out:
        print(f"  {x['scene']} {x['speaker']} {x['start']:6.2f}-{x['end']:6.2f} {x['text']}")


if __name__ == "__main__":
    main()
