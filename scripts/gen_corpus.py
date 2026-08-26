"""Generate the Mind Meld training corpus from the knowledge base.

The corpus teaches the model the LANGUAGE OF THE GAME:
  - Round A transcripts: questions -> answers -> guess (engine-simulated)
  - Fact sheets: entity attributes rendered as prose
  - Round B transcripts: player questions -> truthful answers
  - Personality lines: banter, taunts, celebrations
  - Share cards

Everything is delimited by <|endoftext|>.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game.engine import MindReader, SecretKeeper, daily_secret, share_card
from game.kb import ATTRIBUTES, ENTITIES, ENTITY_NAMES, MAYBE, NO, YES
from game.personality import (
    AI_LOSES,
    AI_WINS,
    AI_WINS_DUEL,
    ANSWER_MAYBE,
    ANSWER_NO,
    ANSWER_YES,
    CORRECT_GUESS,
    INTROS,
    INTROS_DAILY,
    SECRET_PICKED,
    WRONG_GUESS,
    YOU_WIN_DUEL,
)
from game.questions import QUESTIONS

OUT = Path(__file__).resolve().parent.parent / "data" / "corpus.txt"
EOT = "<|endoftext|>"

ATTR_PROSE = {
    "has_a_face": ("has a face", "has no face"),
    "moves_on_its_own": ("moves on its own", "does not move on its own"),
    "is_natural": ("is found in nature", "is man-made"),
    "is_soft": ("is soft", "is not soft"),
    "has_legs": ("has legs", "has no legs"),
    "alive_today": ("is alive today", "is not alive today"),
    "is_animal": ("is an animal", "is not an animal"),
    "is_human": ("is a human", "is not a human"),
    "is_real": ("is real", "is not real"),
    "is_fictional": ("is fictional", "is not fictional"),
    "is_mammal": ("is a mammal", "is not a mammal"),
    "is_bird": ("is a bird", "is not a bird"),
    "is_sea_creature": ("is a sea creature", "is not a sea creature"),
    "is_insect": ("is an insect", "is not an insect"),
    "is_reptile": ("is a reptile", "is not a reptile"),
    "can_fly": ("can fly", "cannot fly"),
    "can_swim": ("can swim", "cannot swim"),
    "lives_in_water": ("lives in water", "does not live in water"),
    "has_fur": ("has fur", "has no fur"),
    "has_wings": ("has wings", "has no wings"),
    "has_tail": ("has a tail", "has no tail"),
    "four_legs": ("walks on four legs", "does not walk on four legs"),
    "kept_as_pet": ("is kept as a pet", "is not kept as a pet"),
    "is_dangerous": ("is dangerous", "is not dangerous"),
    "bigger_than_breadbox": ("is bigger than a breadbox", "is smaller than a breadbox"),
    "found_in_home": ("is found in homes", "is not usually found in homes"),
    "is_electronic": ("is electronic", "is not electronic"),
    "made_of_metal": ("is made of metal", "is not made of metal"),
    "is_edible": ("is edible", "is not edible"),
    "is_liquid": ("is a liquid", "is not a liquid"),
    "is_round": ("is round", "is not round"),
    "makes_music": ("makes music", "does not make music"),
    "is_wearable": ("is wearable", "is not wearable"),
    "is_vehicle": ("is a vehicle", "is not a vehicle"),
    "is_tool": ("is a tool", "is not a tool"),
    "is_furniture": ("is furniture", "is not furniture"),
    "is_plant": ("is a plant", "is not a plant"),
    "is_toy": ("is a toy", "is not a toy"),
    "associated_with_sport": ("is associated with sport", "is not associated with sport"),
    "is_celebrity": ("is famous", "is not famous"),
    "from_screen": ("is known from screens", "is not a screen icon"),
    "is_historical": ("is a historical figure", "is not a historical figure"),
    "is_female": ("is female", "is not female"),
    "is_scientist": ("is known for science", "is not known for science"),
    "is_artist_or_musician": ("is known for art or music", "is not known for art or music"),
    "is_ruler_or_politician": ("ruled or led", "never ruled"),
    "is_athlete": ("is an athlete", "is not an athlete"),
    "is_sweet": ("is sweet", "is not sweet"),
    "is_fruit_or_veg": ("is a fruit or vegetable", "is not a fruit or vegetable"),
    "is_dairy": ("is a dairy product", "is not dairy"),
    "served_cold": ("is served cold", "is not served cold"),
    "has_superpowers": ("has superpowers", "has no superpowers"),
    "is_villain": ("is a villain", "is not a villain"),
    "from_ancient_times": ("is from ancient times", "is not from ancient times"),
    "has_wheels": ("has wheels", "has no wheels"),
    "two_wheeled": ("has two wheels", "does not have two wheels"),
    "handheld": ("fits in one hand", "does not fit in one hand"),
    "used_for_cleaning": ("is used for cleaning", "is not used for cleaning"),
    "tells_time": ("tells the time", "does not tell the time"),
    "has_screen": ("has a screen", "has no screen"),
    "has_long_neck": ("has a long neck", "does not have a long neck"),
    "wears_a_costume": ("wears a signature costume", "wears no signature costume"),
    "played_with_racket": ("is played with a racket", "needs no racket"),
    "is_royal": ("is royalty", "is not royalty"),
    "is_tech_or_business": ("is known for tech or business", "is not a tech or business figure"),
    "is_animated": ("is animated", "is not animated"),
    "is_mythological": ("comes from mythology", "is not mythological"),
    "has_stripes": ("has stripes", "has no stripes"),
    "has_spots": ("has spots", "has no spots"),
    "is_black_and_white": ("is black and white", "is not black and white"),
    "is_public_transport": ("is public transport", "is not public transport"),
    "is_emergency": ("is an emergency vehicle", "is not an emergency vehicle"),
    "is_fast_food": ("is fast food", "is not fast food"),
    "is_classical_music": ("is known for classical music", "is not a classical musician"),
    "fronted_a_band": ("fronted a famous band", "did not front a band"),
    "known_for_dance": ("is famous for dancing", "is not known for dancing"),
    "from_before_1800": ("lived before 1800", "did not live before 1800"),
    "studied_stars": ("studied the stars", "did not study the stars"),
    "studied_electricity": ("worked with electricity", "did not work with electricity"),
    "studied_living_things": ("studied living things", "did not study living things"),
    "uses_a_ball": ("uses a ball", "uses no ball"),
    "played_on_ice_or_snow": ("is played on ice or snow", "needs no ice or snow"),
    "uses_a_bat_or_stick": ("uses a bat or stick", "uses no bat or stick"),
    "played_by_kicking": ("is played by kicking", "is not played by kicking"),
    "uses_weapons": ("involves weapons", "involves no weapons"),
    "done_in_water": ("is done in water", "is not done in water"),
    "sat_or_slept_on": ("is sat or slept on", "is not sat or slept on"),
    "has_doors_or_drawers": ("has doors or drawers", "has no doors or drawers"),
    "gives_light": ("gives light", "gives no light"),
    "hangs_on_wall_or_window": ("hangs on a wall or window", "does not hang up"),
    "used_in_bathroom": ("is used in the bathroom", "is not a bathroom item"),
    "used_for_writing": ("is used for writing", "is not used for writing"),
    "used_when_raining": ("is used when it rains", "is not a rainy-day item"),
    "lives_in_a_cage": ("lives in a cage", "does not live in a cage"),
    "has_a_trunk": ("has a trunk", "has no trunk"),
    "hops": ("hops", "does not hop"),
    "has_antlers": ("has antlers", "has no antlers"),
    "is_pink": ("is pink", "is not pink"),
    "active_at_night": ("is active at night", "is not nocturnal"),
    "has_many_arms": ("has many arms", "does not have many arms"),
    "is_alcoholic": ("is alcoholic", "is not alcoholic"),
    "is_a_hot_drink": ("is a hot drink", "is not a hot drink"),
    "is_a_condiment": ("is a condiment", "is not a condiment"),
    "contains_meat": ("contains meat", "contains no meat"),
    "is_japanese": ("is Japanese", "is not Japanese"),
    "carries_cargo": ("carries cargo", "does not carry cargo"),
    "runs_in_city": ("runs in the city", "does not mainly run in cities"),
    "connects_to_internet": ("connects to the internet", "does not connect to the internet"),
    "is_a_detective": ("is a detective", "is not a detective"),
    "is_a_spy": ("is a spy", "is not a spy"),
    "searches_for_treasure": ("hunts treasure", "does not hunt treasure"),
    "from_space_or_scifi": ("comes from science fiction", "is not from science fiction"),
    "from_wizard_world": ("belongs to a wizard world", "is not from a wizard world"),
    "barks": ("barks", "does not bark"),
    "purrs_or_meows": ("purrs or meows", "does not purr or meow"),
    "turns_screws": ("turns screws", "does not turn screws"),
    "is_a_grain": ("is a grain", "is not a grain"),
    "eaten_with_hands": ("is eaten with the hands", "needs cutlery"),
    "is_australian": ("is Australian", "is not Australian"),
    "pecks_wood": ("pecks wood", "does not peck wood"),
    "common_city_bird": ("is a common city bird", "is not a city bird"),
    "famous_for_its_tail": ("is famous for its tail", "has no famous tail"),
    "was_a_military_leader": ("led armies", "never led armies"),
    "was_american_president": ("was a US president", "was never a US president"),
    "civil_rights_icon": ("is a civil rights icon", "is not a civil rights icon"),
}

ANSWER_WORD = {YES: "yes", NO: "no", MAYBE: "maybe"}


def fact_sheets() -> list[str]:
    docs = []
    for name in ENTITY_NAMES:
        vec = ENTITIES[name]["vec"]
        yes_traits = [ATTR_PROSE[a][0] for a in ATTRIBUTES if vec[a] == YES and a in ATTR_PROSE]
        no_traits = [ATTR_PROSE[a][1] for a in ATTRIBUTES if vec[a] == NO and a in ATTR_PROSE]
        lines = [f"ENTITY: {name}", f"SUMMARY: {ENTITIES[name]['blurb']}."]
        lines.append("TRAITS: " + "; ".join(yes_traits) + ".")
        docs.append("\n".join(lines))
        qa = [f"FACTS ABOUT {name.upper()}:"]
        for a in ATTRIBUTES:
            q = QUESTIONS[a][0]
            qa.append(f"Q: {q} A: {ANSWER_WORD[vec[a]]}")
        docs.append("\n".join(qa))
        docs.append(f"{name}: {ENTITIES[name]['blurb']}. It {yes_traits[0] if yes_traits else 'exists'}. Notably, it {no_traits[0] if no_traits else 'is unique'}.")
    return docs


def round_a_transcripts(rng: random.Random, games_per_entity: int = 6) -> list[str]:
    docs = []
    for target in ENTITY_NAMES:
        for _ in range(games_per_entity):
            mr = MindReader(rng=rng)
            lines = [f"NEW GAME. The challenger thinks of something. (secret: {target})"]
            bare_lines: list[str] = []
            while True:
                attr = mr.next_question()
                if attr is None:
                    lines.append(f"FINAL GUESS: {mr.best_candidate()}")
                    break
                q = rng.choice(QUESTIONS[attr])
                v = ENTITIES[target]["vec"][attr]
                noisy_v = v if rng.random() > 0.03 else rng.choice([YES, NO, MAYBE])
                lines.append(f"Q: {q} A: {ANSWER_WORD[noisy_v]}")
                bare_lines.append(f"Q: {q} A: {ANSWER_WORD[noisy_v]}")
                mr.answer(attr, noisy_v)
                if mr.should_guess():
                    g = mr.guess()
                    correct = g == target
                    lines.append(f"GUESS: {g} -> {'CORRECT' if correct else 'WRONG'}")
                    bare_lines.append(f"GUESS: {g} -> {'CORRECT' if correct else 'WRONG'}")
                    mr.confirm_guess(correct)
                    if correct or len(mr.guesses_made) >= 3:
                        break
            docs.append("\n".join(lines))
            docs.append("\n".join(bare_lines))
    return docs


def round_b_transcripts(rng: random.Random, per_entity: int = 4) -> list[str]:
    docs = []
    question_words = {
        YES: ["yes", "Yes.", "Yes, indeed.", "Yes!"],
        NO: ["no", "No.", "No, not at all.", "No!"],
        MAYBE: ["maybe", "Hmm, sometimes.", "In a manner of speaking."],
    }
    for name in ENTITY_NAMES:
        vec = ENTITIES[name]["vec"]
        for _ in range(per_entity):
            attrs = rng.sample(ATTRIBUTES, k=8)
            lines = [f"The genie holds a secret. (secret: {name})"]
            for a in attrs:
                q = rng.choice(QUESTIONS[a])
                ans = rng.choice(question_words[vec[a]])
                lines.append(f"PLAYER: {q}\nGENIE: {ans}")
            lines.append(f"PLAYER: is it {name}?\nGENIE: Yes! You have read my mind. It was {name}.")
            docs.append("\n".join(lines))
    return docs


def personality_docs() -> list[str]:
    docs = []
    for group, label in [
        (INTROS, "intro"), (INTROS_DAILY, "daily intro"), (AI_WINS, "ai wins"),
        (AI_LOSES, "ai loses"), (YOU_WIN_DUEL, "you win duel"), (AI_WINS_DUEL, "ai wins duel"),
        (WRONG_GUESS, "wrong guess"), (CORRECT_GUESS, "correct guess"), (SECRET_PICKED, "secret picked"),
        (ANSWER_YES, "answer yes"), (ANSWER_NO, "answer no"), (ANSWER_MAYBE, "answer maybe"),
    ]:
        for _ in range(10):
            for line in group:
                docs.append(f"GENIE ({label}): {line}")
    return docs


def share_card_docs(rng: random.Random) -> list[str]:
    docs = []
    for day in range(1, 400, 7):
        ai_q = rng.randint(5, 20)
        you_q = rng.randint(3, 20)
        ai_won = rng.random() > 0.05
        you_won = rng.random() > 0.35
        docs.append(share_card(day, ai_q, ai_won, you_q, you_won))
    return docs


def main() -> None:
    rng = random.Random(1234)
    docs = []
    docs += fact_sheets()
    docs += round_a_transcripts(rng)
    docs += round_b_transcripts(rng)
    docs += personality_docs()
    docs += share_card_docs(rng)
    rng.shuffle(docs)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = f"\n{EOT}\n".join(docs) + f"\n{EOT}\n"
    OUT.write_text(text, encoding="utf-8")
    print(f"corpus: {len(docs)} documents, {len(text):,} chars -> {OUT}")


if __name__ == "__main__":
    main()
