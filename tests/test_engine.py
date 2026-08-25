import random
import unittest

from game.engine import (
    MAX_QUESTIONS,
    MindReader,
    SecretKeeper,
    daily_secret,
    match_attribute,
    parse_answer,
    share_card,
)
from game.kb import ATTRIBUTES, ENTITIES, ENTITY_NAMES, MAYBE, NO, YES
from game.questions import QUESTIONS


def simulate(target, seed=7, max_guesses=3):
    mr = MindReader(rng=random.Random(seed))
    while True:
        attr = mr.next_question()
        if attr is None:
            return mr.best_candidate() == target, len(mr.asked)
        mr.answer(attr, ENTITIES[target]["vec"][attr])
        if mr.should_guess():
            if mr.guess() == target:
                return True, len(mr.asked)
            mr.confirm_guess(False)
            if len(mr.guesses_made) >= max_guesses:
                return False, len(mr.asked)


class TestKB(unittest.TestCase):
    def test_every_attribute_has_questions(self):
        for attr in ATTRIBUTES:
            self.assertIn(attr, QUESTIONS)
            self.assertGreaterEqual(len(QUESTIONS[attr]), 2)

    def test_every_entity_complete(self):
        for name in ENTITY_NAMES:
            vec = ENTITIES[name]["vec"]
            self.assertEqual(set(vec.keys()), set(ATTRIBUTES), name)
            for v in vec.values():
                self.assertIn(v, (YES, NO, MAYBE), name)

    def test_no_duplicate_names(self):
        self.assertEqual(len(ENTITY_NAMES), len(set(ENTITY_NAMES)))


class TestEngineSelfPlay(unittest.TestCase):
    def test_overall_accuracy_at_least_90_percent(self):
        wins = sum(1 for t in ENTITY_NAMES if simulate(t)[0])
        rate = wins / len(ENTITY_NAMES)
        self.assertGreaterEqual(rate, 0.90, f"only {rate:.0%} self-play accuracy")

    def test_median_questions_reasonable(self):
        counts = sorted(simulate(t)[1] for t in ENTITY_NAMES)
        median = counts[len(counts) // 2]
        self.assertLessEqual(median, 14, f"median {median} questions is too slow")

    def test_engine_beats_ground_truth_targets(self):
        for t in ["dog", "pizza", "Darth Vader", "penguin"]:
            ok, nq = simulate(t)
            self.assertTrue(ok, f"failed on {t}")

    def test_never_ask_same_question_twice(self):
        mr = MindReader(rng=random.Random(1))
        seen = set()
        for _ in range(15):
            attr = mr.next_question()
            self.assertNotIn(attr, seen)
            seen.add(attr)
            mr.answer(attr, YES)


class TestParsing(unittest.TestCase):
    def test_parse_answers(self):
        self.assertEqual(parse_answer("yes"), YES)
        self.assertEqual(parse_answer("y"), YES)
        self.assertEqual(parse_answer("nope"), NO)
        self.assertEqual(parse_answer("maybe"), MAYBE)
        self.assertIsNone(parse_answer("banana hammock"))

    def test_match_attribute(self):
        self.assertEqual(match_attribute("can it fly?"), "can_fly")
        self.assertEqual(match_attribute("is it made of metal?"), "made_of_metal")
        self.assertIsNone(match_attribute("zzz purple elephant?"))

    def test_try_guess_substring_rules(self):
        keeper = SecretKeeper(secret="Elvis Presley")
        self.assertFalse(keeper.try_guess("y"))
        self.assertFalse(keeper.try_guess("el"))
        self.assertTrue(keeper.try_guess("elvis"))
        self.assertTrue(keeper.solved)

    def test_secret_keeper_ground_truth(self):
        keeper = SecretKeeper(secret="dog")
        _, reply = keeper.answer_question("is it an animal?")
        self.assertEqual(reply, "Yes.")
        _, reply = keeper.answer_question("can it fly?")
        self.assertEqual(reply, "No.")


class TestDaily(unittest.TestCase):
    def test_daily_secret_deterministic(self):
        a = daily_secret(739500)
        b = daily_secret(739500)
        self.assertEqual(a, b)
        self.assertIn(a, ENTITIES)

    def test_share_card_format(self):
        card = share_card(42, 11, True, 9, True)
        self.assertIn("MIND MELD #42", card)
        self.assertIn("⚡ YOU WON THE MELD", card)


if __name__ == "__main__":
    unittest.main()
