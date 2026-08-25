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
        keeper = SecretKeeper(secret="Elvis Presley", bluff=False)
        self.assertEqual(keeper.try_guess("y"), (False, None))
        self.assertEqual(keeper.try_guess("el"), (False, None))
        self.assertTrue(keeper.try_guess("elvis")[0])
        self.assertTrue(keeper.solved)

    def test_secret_keeper_ground_truth(self):
        keeper = SecretKeeper(secret="dog", bluff=False)
        _, reply = keeper.answer_question("is it an animal?")
        self.assertEqual(reply, "Yes.")
        _, reply = keeper.answer_question("can it fly?")
        self.assertEqual(reply, "No.")


class TestRound2Features(unittest.TestCase):
    def test_similarity_self_is_max(self):
        from game.engine import similarity

        self.assertAlmostEqual(similarity("dog", "dog"), 1.0)

    def test_similarity_clusters(self):
        from game.engine import similarity

        self.assertGreater(similarity("dog", "cat"), similarity("dog", "pizza"))
        self.assertGreater(similarity("car", "bus"), similarity("car", "Zeus"))

    def test_heat_labels_cover_range(self):
        from game.engine import heat_label

        self.assertIn("BURNING", heat_label(0.95))
        self.assertIn("ice cold", heat_label(0.5))

    def test_wrong_guess_gives_heat_for_known_entity(self):
        keeper = SecretKeeper(secret="dog", bluff=False)
        correct, heat = keeper.try_guess("cat")
        self.assertFalse(correct)
        self.assertIsNotNone(heat)

    def test_unknown_guess_gives_no_heat(self):
        keeper = SecretKeeper(secret="dog", bluff=False)
        correct, heat = keeper.try_guess("zzzunknownthing")
        self.assertFalse(correct)
        self.assertIsNone(heat)

    def test_bluff_inverts_exactly_one_attribute(self):
        import random as _r

        keeper = SecretKeeper(secret="dog", rng=_r.Random(5), bluff=True)
        self.assertIsNotNone(keeper.bluff_attr)
        honest = ENTITIES["dog"]["vec"][keeper.bluff_attr]
        _, reply = keeper.answer_question(QUESTIONS[keeper.bluff_attr][0])
        expected = {1.0: "No.", 0.0: "Yes."}[honest]
        self.assertEqual(reply, expected)
        self.assertTrue(keeper.bluff_used)
        self.assertIn("lied once", keeper.bluff_disclosure())

    def test_bluff_disabled_means_no_disclosure(self):
        keeper = SecretKeeper(secret="dog", bluff=False)
        keeper.answer_question("is it an animal?")
        self.assertIsNone(keeper.bluff_disclosure())

    def test_resolve_entity(self):
        from game.engine import resolve_entity

        self.assertEqual(resolve_entity("is it Darth Vader?"), "Darth Vader")
        self.assertEqual(resolve_entity("pizza"), "pizza")
        self.assertIsNone(resolve_entity("zz"))


class TestConfidence(unittest.TestCase):
    def test_confidence_rises_and_wins(self):
        mr = MindReader(rng=random.Random(7))
        shares = []
        while True:
            attr = mr.next_question()
            if attr is None:
                break
            mr.answer(attr, ENTITIES["dog"]["vec"][attr])
            shares.append(mr.top_share())
            if mr.should_guess():
                break
        self.assertGreater(shares[-1], shares[0])
        self.assertGreaterEqual(shares[-1], 0.2)


class TestDaily(unittest.TestCase):
    def test_daily_secret_deterministic(self):
        a = daily_secret(739500)
        b = daily_secret(739500)
        self.assertEqual(a, b)
        self.assertIn(a, ENTITIES)

    def test_themed_tuesday_is_animal(self):
        from datetime import date, timedelta

        from game.engine import daily_info

        day = date(2026, 8, 25).toordinal()
        while date.fromordinal(day).weekday() != 1:
            day += 1
        secret, theme = daily_info(day)
        self.assertEqual(theme, "Animal Tuesday")
        self.assertEqual(ENTITIES[secret]["vec"]["is_animal"], YES)

    def test_unthemed_day_has_no_label(self):
        from datetime import date

        from game.engine import daily_info

        day = date(2026, 8, 26).toordinal()
        while date.fromordinal(day).weekday() in (1, 4, 5):
            day += 1
        _, theme = daily_info(day)
        self.assertIsNone(theme)

    def test_share_card_format(self):
        card = share_card(42, 11, True, 9, True)
        self.assertIn("MIND MELD #42", card)
        self.assertIn("⚡ YOU WON THE MELD", card)

    def test_share_card_theme_and_rank(self):
        card = share_card(42, 11, True, 9, True, theme="Cinema Friday", rank="Mistwalker")
        self.assertIn("Cinema Friday", card)
        self.assertIn("Mistwalker", card)


if __name__ == "__main__":
    unittest.main()
