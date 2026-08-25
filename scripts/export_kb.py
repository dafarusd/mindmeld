"""Export the game's data layer to a self-contained JS file for the static build.

Emits static_site/data.js: a single `const MM_DATA = {...}` so the game
works from file:// (no fetch/CORS issues) and any static host.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game import personality
from game.engine import SYNONYMS
from game.kb import ATTRIBUTES, ENTITIES
from game.questions import QUESTIONS

OUT = Path(__file__).resolve().parent.parent / "static_site" / "data.js"


def main() -> None:
    base_entities = {
        name: {"blurb": e["blurb"], "vec": e["vec"]}
        for name, e in ENTITIES.items()
        if not e.get("learned")
    }
    voice_curated = {
        "intro": personality.INTROS,
        "daily intro": personality.INTROS_DAILY,
        "ai wins": personality.AI_WINS,
        "ai loses": personality.AI_LOSES,
        "you win duel": personality.YOU_WIN_DUEL,
        "ai wins duel": personality.AI_WINS_DUEL,
        "wrong guess": personality.WRONG_GUESS,
        "correct guess": personality.CORRECT_GUESS,
        "secret picked": personality.SECRET_PICKED,
        "answer yes": personality.ANSWER_YES,
        "answer no": personality.ANSWER_NO,
        "answer maybe": personality.ANSWER_MAYBE,
        "grudge": personality.GRUDGE_OPENERS,
        "streak taunt": personality.STREAK_TAUNTS,
        "revenge": personality.REVENGE_SENSE,
        "taught gloat": personality.TAUGHT_GLOAT,
        "gauntlet offer": personality.GAUNTLET_OFFER,
        "gauntlet won": personality.GAUNTLET_WON,
        "gauntlet lost": personality.GAUNTLET_LOST,
        "boss intro": personality.BOSS_INTRO,
        "boss loses": personality.BOSS_LOSES,
        "boss wins": personality.BOSS_WINS,
    }
    data = {
        "attributes": ATTRIBUTES,
        "entities": base_entities,
        "questions": QUESTIONS,
        "synonyms": SYNONYMS,
        "voice_curated": voice_curated,
        "bluff_rule": personality.BLUFF_RULE,
        "hunch_agree": personality.HUNCH_AGREE,
        "answer_words": {k: sorted(v) for k, v in __import__("game.questions", fromlist=["ANSWER_WORDS"]).ANSWER_WORDS.items()},
    }
    # Carry the baked voice forward. build_voice.py writes voice_model into
    # data.js; this script rebuilds everything else. Without this, exporting
    # the KB silently wipes the model's voice and the game falls back to the
    # curated script with no warning.
    if OUT.exists():
        prev_raw = OUT.read_text(encoding="utf-8")
        prefix = "(typeof window !== 'undefined' ? window : globalThis).MM_DATA = "
        if prev_raw.startswith(prefix):
            try:
                prev = json.loads(prev_raw[len(prefix):].rstrip().rstrip(";"))
                if prev.get("voice_model"):
                    data["voice_model"] = prev["voice_model"]
                    kept = sum(len(v) for v in prev["voice_model"].values())
                    print(f"  carried forward {kept} baked voice lines")
            except Exception as exc:
                print(f"  WARNING: could not read existing voice_model ({exc})")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False)
    OUT.write_text(f"(typeof window !== 'undefined' ? window : globalThis).MM_DATA = {payload};\n", encoding="utf-8")
    print(f"data.js: {len(base_entities)} base entities, {len(ATTRIBUTES)} attrs, {OUT.stat().st_size/1024:.0f}KB -> {OUT}")


if __name__ == "__main__":
    main()
