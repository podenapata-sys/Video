#!/usr/bin/env python3
"""What the voiceover actually says (it differs from script.md), phrase by phrase, with its scene/image.

  python3 scripts/transcript.py      -> vo_lines.json

Phrases follow asr_spans.json (pause-delimited speech spans, pocketsphinx draft), corrected by ear-reading
the recogniser output. Scene numbers are the image slots in scene_map.json.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
T = {1: [("If you ever wake up at 3:00 in the morning", 1), ("and see a deer standing in your yard,", 2), ("Leave your house.", 3),
         ("Don't turn on the lights.", 4), ("Don't wake up anyone. And whatever you do,", 5), ("do not wait till sunrise.", 6),
         ("I'm not talking about a deer walking across your lawn or eating your plants.", 7), ("I'm talking about one standing completely still.", 8),
         ("Its head is raised,", 9), ("its ears are pointed forward,", 9), ("and it's staring directly at your house.", 10),
         ("You might think it's watching you,", 11), ("but look carefully.", 12), ("It's not looking at your window,", 12),
         ("it's looking at something behind it.", 13), ("And if the deer hasn't moved by the time you count to ten,", 14),
         ("you need to follow these seven rules.", 15)],
     2: [("Rule number one.", 16), ("Do not turn on the lights.", 16), ("I know you'll want to get a better look.", 17), ("Don't.", 17),
         ("Whatever the deer is watching doesn't know you're awake yet.", 18), ("The moment you turn your light on, it will.", 19),
         ("And here's something you need to understand.", 20), ("Deer are prey animals.", 20),
         ("When they sense danger, they sometimes freeze and stare at it.", 21), ("But a normal deer eventually runs.", 22), ("This one won't.", 23),
         ("Not when a car passes.", 24), ("Not when a branch falls.", 24), ("Not even when you knock on the glass.", 24),
         ("Because whatever it's watching is much closer than you think.", 25), ("Rule number two.", 26), ("Watch the deer's head.", 26),
         ("Don't focus on its eyes.", 27), ("Watch which direction its head is pointing.", 27),
         ("If it's staring at your kitchen, stay away from the kitchen.", 28), ("If it turns toward the hallway,", 29),
         ("do not even think about entering the hallway.", 29), ("And if its head slowly rises toward your bedroom window,", 30),
         ("move away from the glass immediately.", 30), ("Because the deer isn't following you.", 31),
         ("It's following something moving through your house.", 31), ("You don't want to be standing where it stops.", 32)],
     3: [("Rule number three.", 33), ("If the deer stamps its hoof,", 33), ("freeze.", 33), ("You'll hear a sharp sound outside.", 34),
         ("One hard strike against the ground.", 34), ("When that happens, stop whatever you're doing.", 35), ("Don't move.", 35), ("Don't speak.", 35),
         ("And most importantly,", 36), ("do not turn around.", 36), ("The hoof stamp means something has gotten close enough for it to react.", 37),
         ("You might hear breathing behind you, or the floor creaking.", 38),
         ("You might even feel someone standing close enough to touch your shoulder.", 39), ("But you have to ignore it.", 40),
         ("Wait until you hear another hoof strike.", 41), ("Then keep moving toward the nearest exit.", 41),
         ("But if the second sound comes from inside the house,", 42), ("you've already waited too long.", 42), ("Rule number four.", 43),
         ("If someone calls your name,", 43), ("don't answer it.", 43), ("This is where most people make a mistake.", 44),
         ("You'll hear someone you recognize. Maybe your mother, calling from the kitchen.", 45), ("Maybe your brother, asking why you're awake.", 46),
         ("The voice will sound completely normal.", 47), ("But listen to what it says.", 47), ("It won't ask you to come downstairs.", 48),
         ("It'll ask you to stay.", 48), ("It might say, \"It's cold outside,\" or \"Just go back to bed.\"", 49), ("And if you ignore it,", 50),
         ("the voice will become angry.", 50), ("Then frightened.", 50), ("Then it'll start crying.", 50), ("Don't answer.", 51),
         ("Whatever is speaking knows you need to leave.", 52), ("And it's running out of ways to keep you inside.", 52)],
     4: [("Rule number five.", 53), ("If the deer starts walking toward the house,", 53), ("you have one minute to get out.", 53),
         ("It won't walk like a normal deer.", 54), ("Its legs will move slowly", 55), ("and almost carefully,", 55),
         ("but its body will remain completely still.", 55), ("Its head won't bob.", 56), ("Its eyes won't blink.", 56),
         ("And its hooves might not even make any sound at all.", 56),
         ("One woman once described seeing a deer like this outside her bedroom window.", 57),
         ("She said it stood beneath the same tree for almost an hour.", 58), ("Then, at exactly 3:17,", 59), ("it took one step toward the house.", 59),
         ("Her husband laughed and went downstairs to try to scare it away.", 60), ("She watched him from the bedroom doorway.", 61),
         ("He reached the bottom step.", 61), ("Then stopped.", 61), ("She called his name. Her husband didn't answer.", 62),
         ("A few seconds later, she heard him speaking from the kitchen.", 63), ("Except his voice was still coming from the staircase too.", 63),
         ("She ran out through the bedroom window.", 64), ("When the police arrived, her husband was gone.", 65),
         ("But every light in the house was on.", 65), ("And something upstairs kept calling her name.", 66)],
     5: [("Rule number six.", 67), ("Do not use the front door if the deer is facing it.", 67), ("Find another exit.", 68),
         ("The back door. The garage.", 68), ("Even a window.", 68), ("Just don't walk into the place the deer is watching.", 69),
         ("And before you open anything, listen.", 70), ("Do you hear scratching on the other side?", 70), ("Choose another way.", 70),
         ("Do you hear someone knocking?", 71), ("Don't answer.", 71), ("If you hear your own voice asking to be let in,", 72),
         ("get away from the door. Immediately.", 72), ("Because by now, whatever is inside your house has heard you speak.", 73),
         ("It's heard you walk.", 73), ("It's learned the sound of your breathing.", 74), ("And it's getting better at sounding like you.", 74),
         ("Rule number seven.", 75), ("Once you're outside, do not look back at your house.", 75), ("Keep walking.", 76),
         ("Don't stop at the driveway.", 76), ("Don't get in your car.", 76), ("And don't turn around if you hear your front door open.", 77),
         ("You might hear footsteps following you.", 78), ("You might hear someone shouting that you forgot something.", 78),
         ("But keep walking until you reach the road.", 79), ("Only then should you look at the deer.", 79),
         ("If it's still standing in the yard, you're not far enough from it.", 80), ("Keep going.", 80), ("If the deer has disappeared,", 81),
         ("don't assume you're safe.", 81), ("Look at the windows of your house.", 82), ("Not for long.", 82),
         ("Just long enough to check whether someone is standing behind the glass.", 82)],
     6: [("Because there is one thing I haven't told you yet.", 83),
         ("People who survive these encounters sometimes check their security cameras the next morning.", 84),
         ("And they all noticed something strange.", 85), ("The deer wasn't just staring at the house when they first woke up.", 86),
         ("It was staring at one particular window, even before anyone had walked into the room.", 86),
         ("When they watch the recording closely,", 87), ("they see why.", 87), ("A figure was already standing behind the glass.", 88),
         ("Completely motionless.", 88), ("Watching the deer.", 88), ("The figure looks almost human.", 89), ("Same height.", 89),
         ("Same clothes.", 89), ("And when the person inside finally woke up and approached the window,", 90),
         ("the figure stepped backward into the darkness.", 90), ("That's why the deer never moved.", 91),
         ("It wasn't waiting for something to enter your house.", 92), ("Something had already been standing there for hours.", 92),
         ("Practicing how to look like you.", 93), ("So if you ever see a deer standing in your yard at 3:00 in the morning,", 94),
         ("leave your house immediately.", 94), ("If you hear your own voice calling you back inside,", 95), ("keep walking.", 95)]}


def main():
    asr = json.loads((ROOT / "asr_spans.json").read_text())
    by_chunk = {c: [x for x in asr if x["chunk"] == c] for c in T}
    out = []
    for c, phrases in T.items():
        assert len(phrases) == len(by_chunk[c]), f"chunk {c}: {len(phrases)} phrases vs {len(by_chunk[c])} spans"
        for (text, scene), x in zip(phrases, by_chunk[c]):
            out.append({"chunk": c, "start": x["start"], "end": x["end"], "text": text, "scene": scene, "asr": x["asr"]})
    scenes = [o["scene"] for o in out]
    assert scenes == sorted(scenes) and set(scenes) == set(range(1, 96)), "scenes must be in order and all 95 present"
    (ROOT / "vo_lines.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"{len(out)} phrases -> 95 scenes")


if __name__ == "__main__":
    main()
