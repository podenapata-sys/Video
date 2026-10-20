#!/usr/bin/env python3
"""Pair every measured speech span (voice_map.json) with its script text -> captions.json.

  python3 scripts/captions.py

The phrase lists below follow the voice span by span (115 spans; verified against
span durations and the ~1s paragraph gaps before each "Rule X."). kind: "rule" for the
rule headings, "punch" for the "..." punchlines, "case" for the case file, else "line".
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PHRASES = {
    1: ["If your dog ever stands up on two legs and stays there,", "do not scream,", "do not run,",
        "and do not let it see that you noticed.", "There are seven rules.", "Most people break the third.",
        "Nobody was ever supposed to need the seventh.", "For 30,000 years, dogs have lived beside us.",
        "That is a long time to watch someone.", "Your dog knows when you wake up.", "It knows where the food is kept.",
        "It knows which pocket has the keys.", "Most dogs do nothing with this information.", "Most.",
        "Rule one.", "Act normal.", "Whatever you were doing, keep doing it.", "If you were eating,", "keep eating.",
        "If you were watching television,", "keep watching.", "If you were doing nothing at all...", "continue.",
        "You have trained for this.", "Do not stare.", "It is not looking at you.", "It is looking at how you stand."],
    2: ["Rule two.", "Do not say its name.", "It does not answer to that anymore.", "Do not say sit.",
        "It will, in a chair across from you,", "and it will wait to hear what you say next.", "Also...",
        "do not say the word, walk.", "We will not be saying it again.", "Rule three.", "Do not take out your phone.",
        "This is where most people fail.", "You will want to film it.",
        "There is a small, hairy man standing in your kitchen.", "It would do very well online.",
        "But a dog that sees a camera, learns something.", "It learns that it is being watched.",
        "And for a very long time, it has been the one doing the watching.", "It would like to keep it that way.",
        "Case file 41.", "A man in Ohio filmed his dog opening the refrigerator.", "The video is 11 seconds long.",
        "He is only in the first four.", "By now, it has started to copy you.", "First, the way you stand.",
        "Then, the way you walk.", "Then...", "your face.", "A dog's mouth was not built to smile like a person.",
        "It will try anyway.", "Do not smile back.", "It is checking its work."],
    3: ["Rule four.", "Go to bed at your usual time.", "Close the bedroom door.", "Lock it.", "Dogs cannot open doors.",
        "Yesterday, dogs could not open doors.", "If the handle moves, do not ask who is there.",
        "You know who is there.", "You bought it a little raincoat.", "Rule five.",
        "Sometime in the night, someone will call your name.", "It will sound like someone you love.",
        "It may even sound like you.", "It learned to speak by listening through the wall.", "The words will be right.",
        "The spaces... between them...", "will not.", "Do not answer.", "Do not open the door.",
        "And do not tell it that it is a good boy.", "It knows what it is.", "It is no longer interested in your opinion.",
        "And if the doorbell rings—", "Apologies.", "That was unprofessional."],
    4: ["Rule six.", "In the morning, it will be back in its bed.", "Four legs, tail wagging,", "exactly like your dog.",
        "This is the most dangerous part.", "You will want to believe you dreamed it.", "Look at how it is lying.",
        "A dog turns in a circle before it lies down.", "This one is flat on its back, with its paws folded on its chest.",
        "That is how you sleep.", "Take your keys.", "Leave the house.", "Do not say goodbye.",
        "It knows what goodbye means.", "You've said it every morning for six years.", "And every morning, you came back.",
        "Rule seven.", "Nobody was supposed to need this one.", "But by now, you are wondering how we know all of this.",
        "How anyone could know what a dog is thinking,", "what it wants, how long it has been waiting.",
        "We are a trusted government agency.", "We walk on two legs.", "We have always walked on two legs.",
        "Rule seven.", "If a calm voice ever explains all of this to you...", "do not ask it who's a good boy.",
        "We are.", "We always were.", "Thank you for your cooperation.", "Stay."],
}
PUNCH = {(1, 13), (2, 22), (3, 5), (3, 8), (3, 23), (4, 9), (4, 30)}


def main():
    vmap = json.loads((ROOT / "voice_map.json").read_text())
    pauses = {(p["chunk"], p["sentence"]) for p in json.loads((ROOT / "pauses.json").read_text())}
    assert PUNCH == pauses, "punchlines must match pauses.json"
    caps = []
    for s in vmap:
        phrases = PHRASES[s["chunk"]]
        assert len(phrases) == sum(1 for x in vmap if x["chunk"] == s["chunk"]), f"chunk {s['chunk']} phrase count"
        text = phrases[s["sentence"]]
        kind = ("rule" if text.startswith("Rule ") else "punch" if (s["chunk"], s["sentence"]) in PUNCH
                else "case" if text.startswith("Case file") else "line")
        caps.append({"start": s["start"], "end": s["end"], "text": text, "kind": kind})
    # sanity: speaking rate per span should be plausible (1.2-6 words/s)
    for c in caps:
        rate = len(c["text"].split()) / max(0.2, c["end"] - c["start"])
        if not 0.8 < rate < 6.5:
            print(f"! check {c['start']:.1f}s {rate:.1f} w/s: {c['text']}")
    (ROOT / "captions.json").write_text(json.dumps(caps, indent=1, ensure_ascii=False))
    print(f"{len(caps)} captions: {sum(c['kind'] == 'rule' for c in caps)} rule cards, "
          f"{sum(c['kind'] == 'punch' for c in caps)} punchlines")


if __name__ == "__main__":
    main()
