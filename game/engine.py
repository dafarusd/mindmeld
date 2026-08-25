"""Mind Meld game engine.

Round A (AI reads your mind): entropy-driven 20 questions over the KB.
Round B (you read its mind): AI holds a secret entity and answers from
ground truth, so it can never contradict itself.

The engine is deliberately model-free: the trained LLM adds personality,
never facts. That is the product-quality guarantee.
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, field

from .kb import ATTR_INDEX, ATTR_MATRIX, ATTRIBUTES, ENTITIES, ENTITY_NAMES, NO, YES
from .questions import ANSWER_WORDS, QUESTIONS

MAX_QUESTIONS = 20
GUESS_CONFIDENCE = 0.62

_N = len(ENTITY_NAMES)


def parse_answer(text: str) -> float | None:
    words = set(text.lower().strip().split())
    for key, wordset in ANSWER_WORDS.items():
        if words & wordset:
            return {"yes": YES, "no": NO, "maybe": 0.5}[key]
    return None


def _h_from_weights(ws: list[float]) -> float:
    total = sum(ws)
    if total <= 0:
        return 0.0
    h = 0.0
    for w in ws:
        if w > 0:
            p = w / total
            h -= p * math.log2(p)
    return h


@dataclass
class MindReader:
    rng: random.Random = field(default_factory=random.Random)
    weights: dict[str, float] = field(default_factory=lambda: {n: 1.0 for n in ENTITY_NAMES})
    asked: list[str] = field(default_factory=list)
    answers: list[tuple[str, float]] = field(default_factory=list)
    guesses_made: list[str] = field(default_factory=list)

    def __post_init__(self):
        self._w = [self.weights[n] for n in ENTITY_NAMES]

    def _sync_out(self) -> None:
        for i, n in enumerate(ENTITY_NAMES):
            self.weights[n] = self._w[i]

    def next_question(self) -> str | None:
        available = [a for a in range(len(ATTRIBUTES)) if ATTRIBUTES[a] not in self.asked]
        if not available or len(self.asked) >= MAX_QUESTIONS:
            return None
        w = self._w
        total = sum(w)
        current_h = _h_from_weights(w)
        best_attr, best_gain = -1, -1.0
        for a in available:
            yes_w = no_w = maybe_w = 0.0
            yes_l: list[float] = []
            no_l: list[float] = []
            maybe_l: list[float] = []
            for i in range(_N):
                v = ATTR_MATRIX[i][a]
                wi = w[i]
                if v == YES:
                    yes_w += wi
                    yes_l.append(wi)
                elif v == NO:
                    no_w += wi
                    no_l.append(wi)
                else:
                    maybe_w += wi
                    maybe_l.append(wi)
            expected_h = (
                (yes_w / total) * _h_from_weights(yes_l)
                + (no_w / total) * _h_from_weights(no_l)
                + (maybe_w / total) * _h_from_weights(maybe_l)
            )
            gain = current_h - expected_h
            if gain > best_gain:
                best_gain, best_attr = gain, a
        return ATTRIBUTES[best_attr]

    def answer(self, attr: str, value: float) -> None:
        self.asked.append(attr)
        self.answers.append((attr, value))
        a = ATTR_INDEX[attr]
        for i in range(_N):
            agree = 1.0 - abs(ATTR_MATRIX[i][a] - value)
            self._w[i] *= 0.05 + 0.95 * agree
        s = sum(self._w)
        if s > 0:
            inv = 1.0 / s
            for i in range(_N):
                self._w[i] *= inv
        self._sync_out()

    def best_candidate(self) -> str:
        return max(self.weights, key=self.weights.get)

    def top_share(self) -> float:
        total = sum(self.weights.values())
        return self.weights[self.best_candidate()] / total if total else 0.0

    def _ranked(self) -> list[tuple[str, float]]:
        return sorted(self.weights.items(), key=lambda kv: kv[1], reverse=True)

    def should_guess(self) -> bool:
        asked = len(self.asked)
        if asked >= MAX_QUESTIONS:
            return True
        ranked = self._ranked()
        if len(ranked) < 2:
            return True
        top, runner_up = ranked[0][1], ranked[1][1]
        if asked >= 4 and runner_up > 0 and top / runner_up >= 2.0:
            return True
        if asked >= 5 and self.top_share() >= 0.30:
            return True
        return False

    def guess(self) -> str:
        g = self.best_candidate()
        self.guesses_made.append(g)
        return g

    def confirm_guess(self, correct: bool) -> None:
        if correct:
            return
        wrong = self.guesses_made[-1] if self.guesses_made else self.best_candidate()
        self._w[ENTITY_NAMES.index(wrong)] *= 0.01
        self._sync_out()

    def questions_left(self) -> int:
        return MAX_QUESTIONS - len(self.asked)


SYNONYMS: dict[str, str] = {
    "alive": "alive_today", "living": "alive_today", "dead": "alive_today",
    "animal": "is_animal", "creature": "is_animal", "beast": "is_animal",
    "human": "is_human", "person": "is_human", "man": "is_human", "woman": "is_human",
    "real": "is_real", "exist": "is_real",
    "fiction": "is_fictional", "imaginary": "is_fictional", "invented": "is_fictional",
    "mammal": "is_mammal", "bird": "is_bird", "feather": "is_bird",
    "sea": "is_sea_creature", "ocean": "is_sea_creature", "fish": "is_sea_creature",
    "insect": "is_insect", "bug": "is_insect", "reptile": "is_reptile", "scale": "is_reptile",
    "fly": "can_fly", "flew": "can_fly", "swim": "can_swim",
    "water": "lives_in_water", "fur": "has_fur", "furry": "has_fur", "hair": "has_fur",
    "wing": "has_wings", "tail": "has_tail", "leg": "four_legs",
    "pet": "kept_as_pet", "dangerous": "is_dangerous", "danger": "is_dangerous",
    "big": "bigger_than_breadbox", "large": "bigger_than_breadbox", "huge": "bigger_than_breadbox",
    "small": "bigger_than_breadbox", "home": "found_in_home", "house": "found_in_home",
    "household": "found_in_home", "electronic": "is_electronic", "electric": "is_electronic",
    "battery": "is_electronic", "metal": "made_of_metal", "eat": "is_edible", "edible": "is_edible",
    "food": "is_edible", "liquid": "is_liquid", "drink": "is_liquid", "pour": "is_liquid",
    "round": "is_round", "circle": "is_round", "music": "makes_music", "instrument": "makes_music",
    "sing": "makes_music", "wear": "is_wearable", "worn": "is_wearable",
    "vehicle": "is_vehicle", "drive": "is_vehicle", "ride": "is_vehicle",
    "tool": "is_tool", "furniture": "is_furniture", "plant": "is_plant", "grow": "is_plant",
    "toy": "is_toy", "play": "is_toy", "sport": "associated_with_sport",
    "athlete": "associated_with_sport", "famous": "is_celebrity", "celebrity": "is_celebrity",
    "movie": "from_screen", "film": "from_screen", "tv": "from_screen", "show": "from_screen",
    "game": "from_screen", "history": "is_historical", "historical": "is_historical",
    "ancient": "from_ancient_times",
    "female": "is_female", "woman": "is_female", "girl": "is_female", "she": "is_female",
    "scientist": "is_scientist", "science": "is_scientist", "physicist": "is_scientist",
    "artist": "is_artist_or_musician", "musician": "is_artist_or_musician", "singer": "is_artist_or_musician",
    "painter": "is_artist_or_musician", "writer": "is_artist_or_musician",
    "king": "is_ruler_or_politician", "queen": "is_ruler_or_politician", "president": "is_ruler_or_politician",
    "ruler": "is_ruler_or_politician", "politician": "is_ruler_or_politician",
    "athlete": "is_athlete", "player": "is_athlete",
    "sweet": "is_sweet", "dessert": "is_sweet", "sugar": "is_sweet",
    "fruit": "is_fruit_or_veg", "vegetable": "is_fruit_or_veg",
    "dairy": "is_dairy", "milk": "is_dairy", "cold": "served_cold", "frozen": "served_cold",
    "power": "has_superpowers", "superpower": "has_superpowers", "magic": "has_superpowers",
    "villain": "is_villain", "evil": "is_villain", "bad guy": "is_villain",
    "wheel": "has_wheels", "hand": "handheld", "pocket": "handheld",
    "clean": "used_for_cleaning", "tidy": "used_for_cleaning", "time": "tells_time",
    "clock": "tells_time", "screen": "has_screen", "display": "has_screen",
    "neck": "has_long_neck", "costume": "wears_a_costume", "outfit": "wears_a_costume",
    "cape": "wears_a_costume", "racket": "played_with_racket",
    "royal": "is_royal", "king": "is_royal", "queen": "is_royal", "prince": "is_royal", "princess": "is_royal", "crown": "is_royal",
    "tech": "is_tech_or_business", "business": "is_tech_or_business", "billionaire": "is_tech_or_business",
    "animated": "is_animated", "cartoon": "is_animated", "anime": "is_animated",
    "myth": "is_mythological", "mythology": "is_mythological", "god": "is_mythological", "goddess": "is_mythological",
    "stripe": "has_stripes", "striped": "has_stripes", "spot": "has_spots", "spotted": "has_spots",
    "black and white": "is_black_and_white",
    "public transport": "is_public_transport", "bus route": "is_public_transport",
    "emergency": "is_emergency", "siren": "is_emergency",
    "fast food": "is_fast_food", "drive-through": "is_fast_food", "mcdonald": "is_fast_food",
    "classical": "is_classical_music", "symphony": "is_classical_music", "composer": "is_classical_music",
    "band": "fronted_a_band", "frontman": "fronted_a_band",
    "dance": "known_for_dance", "dancing": "known_for_dance",
    "1800": "from_before_1800", "centuries ago": "from_before_1800",
    "star": "studied_stars", "telescope": "studied_stars", "astronomer": "studied_stars",
    "electricity": "studied_electricity", "current": "studied_electricity",
    "evolution": "studied_living_things", "biology": "studied_living_things",
    "ball": "uses_a_ball", "ice": "played_on_ice_or_snow", "snow": "played_on_ice_or_snow",
    "bat": "uses_a_bat_or_stick", "stick": "uses_a_bat_or_stick", "kick": "played_by_kicking",
    "sword": "uses_weapons", "bow": "uses_weapons", "weapon": "uses_weapons",
    "surf": "done_in_water", "sit": "sat_or_slept_on", "sleep": "sat_or_slept_on",
    "drawer": "has_doors_or_drawers", "door": "has_doors_or_drawers",
    "light": "gives_light", "glow": "gives_light", "hang": "hangs_on_wall_or_window",
    "bathroom": "used_in_bathroom", "shower": "used_in_bathroom",
    "write": "used_for_writing", "writing": "used_for_writing", "rain": "used_when_raining",
    "cage": "lives_in_a_cage", "tank": "lives_in_a_cage",
    "trunk": "has_a_trunk", "hop": "hops", "jump": "hops", "antler": "has_antlers",
    "pink": "is_pink", "night": "active_at_night", "nocturnal": "active_at_night",
    "arms": "has_many_arms", "tentacle": "has_many_arms",
    "alcohol": "is_alcoholic", "drunk": "is_alcoholic", "hot drink": "is_a_hot_drink",
    "condiment": "is_a_condiment", "sauce": "is_a_condiment", "meat": "contains_meat",
    "japanese": "is_japanese", "japan": "is_japanese", "cargo": "carries_cargo",
    "city": "runs_in_city", "internet": "connects_to_internet", "wifi": "connects_to_internet",
    "detective": "is_a_detective", "spy": "is_a_spy", "espionage": "is_a_spy",
    "treasure": "searches_for_treasure", "archaeologist": "searches_for_treasure",
    "space": "from_space_or_scifi", "sci-fi": "from_space_or_scifi", "scifi": "from_space_or_scifi",
    "wizard": "from_wizard_world", "spell": "from_wizard_world", "magic wand": "from_wizard_world",
    "bark": "barks", "woof": "barks", "meow": "purrs_or_meows", "purr": "purrs_or_meows",
    "screw": "turns_screws", "grain": "is_a_grain", "australia": "is_australian",
    "peck": "pecks_wood", "president": "was_american_president", "white house": "was_american_president",
    "army": "was_a_military_leader", "armies": "was_a_military_leader", "general": "was_a_military_leader",
    "civil rights": "civil_rights_icon", "protest": "civil_rights_icon",
}


def match_attribute(question_text: str) -> str | None:
    text = question_text.lower()
    best, best_len = None, 0
    for word, attr in SYNONYMS.items():
        if word in text and len(word) > best_len:
            best, best_len = attr, len(word)
    return best


@dataclass
class SecretKeeper:
    secret: str
    rng: random.Random = field(default_factory=random.Random)
    questions_asked: int = 0
    solved: bool = False

    def answer_question(self, text: str) -> tuple[str, str]:
        self.questions_asked += 1
        attr = match_attribute(text)
        if attr is None:
            return "unknown", "The spirits cannot parse that question. Ask about a trait — alive? animal? metal? famous?"
        v = ENTITIES[self.secret]["vec"][attr]
        if v == YES:
            return "yes", "Yes."
        if v == NO:
            return "no", "No."
        return "maybe", "Hmm... sometimes, in a manner of speaking."

    def try_guess(self, text: str) -> bool:
        t = text.lower().strip()
        t = t.removeprefix("is it ").removesuffix("?").strip()
        t = t.removeprefix("a ").removeprefix("an ").removeprefix("the ").strip()
        secret = self.secret.lower()
        if not t or len(t) < 3:
            return False
        if t == secret or (len(t) >= 4 and (t in secret or secret in t)):
            self.solved = True
            return True
        return False


def daily_secret(day_ordinal: int) -> str:
    digest = hashlib.sha256(f"mindmeld-{day_ordinal}".encode()).hexdigest()
    idx = int(digest, 16) % len(ENTITY_NAMES)
    return ENTITY_NAMES[idx]


def share_card(day: int, ai_questions: int | None, ai_won: bool, you_questions: int | None, you_won: bool) -> str:
    ai_line = f"AI read you in {ai_questions} 🟩" if ai_won else "AI failed to read you 🟥"
    you_line = f"You read the AI in {you_questions} 🟩" if you_won else "The AI kept its secret 🟥"
    if you_won and (not ai_won or (you_questions or 99) <= (ai_questions or 99)):
        verdict = "⚡ YOU WON THE MELD"
    elif ai_won:
        verdict = "🧠 THE AI WINS"
    else:
        verdict = "🤝 A RARE DRAW"
    return f"MIND MELD #{day}\n{ai_line}\n{you_line}\n{verdict}"
