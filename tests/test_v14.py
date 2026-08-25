import random
import tempfile
import unittest
from pathlib import Path

from game import kb
from game.engine import (
    MindReader,
    SecretKeeper,
    daily_info,
    event_for_date,
)
from game.kb import ENTITIES, NO, YES
from game.profile import Profile
from game.questions import QUESTIONS


class TestTopCandidates(unittest.TestCase):
    def test_top_three_are_real_and_ordered(self):
        mr = MindReader(rng=random.Random(7))
        mr.answer("is_animal", YES)
        mr.answer("is_mammal", YES)
        top = mr.top_candidates(3)
        self.assertEqual(len(top), 3)
        for name in top:
            self.assertIn(name, ENTITIES)
        self.assertEqual(top[0], mr.best_candidate())


class TestEventDays(unittest.TestCase):
    def test_friday_13_detected(self):
        from datetime import date

        day = date(2026, 2, 13).toordinal()
        ev = event_for_date(day)
        self.assertIsNotNone(ev)
        self.assertEqual(ev["key"], "friday13")
        self.assertEqual(ev["bluff_count"], 2)

    def test_halloween_pool_is_monstrous(self):
        from datetime import date

        day = date(2026, 10, 31).toordinal()
        ev = event_for_date(day)
        self.assertEqual(ev["key"], "halloween")
        secret, label = daily_info(day)
        self.assertEqual(label, "🎃 Halloween")
        vec = ENTITIES[secret]["vec"]
        self.assertTrue(vec["is_villain"] == YES or vec["is_dangerous"] == YES or vec["is_mythological"] == YES)

    def test_opposite_day_inverts_first_three(self):
        keeper = SecretKeeper(secret="dog", bluff=False, invert_first_n=3)
        _, r1 = keeper.answer_question("is it an animal?")
        _, r2 = keeper.answer_question("does it have fur?")
        _, r3 = keeper.answer_question("is it a mammal?")
        _, r4 = keeper.answer_question("is it an animal?")
        self.assertEqual((r1, r2, r3), ("No.", "No.", "No."))
        self.assertEqual(r4, "Yes.")

    def test_normal_day_no_event(self):
        from datetime import date

        day = date(2026, 8, 26).toordinal()
        self.assertIsNone(event_for_date(day))

    def test_friday13_keeper_lies_twice(self):
        keeper = SecretKeeper(secret="dog", rng=random.Random(11), bluff=True, bluff_count=2)
        self.assertEqual(len(keeper.bluff_attrs), 2)


class TestBoss(unittest.TestCase):
    def test_boss_accuracy_gate(self):
        wins = 0
        for t in kb.ENTITY_NAMES:
            mr = MindReader(rng=random.Random(7), max_questions=9, boss=True)
            while True:
                attr = mr.next_question()
                if attr is None:
                    if mr.best_candidate() == t:
                        wins += 1
                    break
                mr.answer(attr, kb.ENTITIES[t]["vec"][attr])
                if mr.should_guess():
                    if mr.guess() == t:
                        wins += 1
                        break
                    mr.confirm_guess(False)
                    if len(mr.guesses_made) >= 3:
                        break
        rate = wins / len(kb.ENTITY_NAMES)
        self.assertGreaterEqual(rate, 0.75, f"boss only {rate:.0%}")


class TestGrudgeMemory(unittest.TestCase):
    def fresh(self):
        tmp = tempfile.TemporaryDirectory()
        return Profile(Path(tmp.name) / "p.json")

    def test_remember_stump(self):
        p = self.fresh()
        p.remember_stump("steam deck")
        p2 = Profile(p.path)
        self.assertEqual(p2.recent_stumps(), ["steam deck"])
        self.assertEqual(p2.learned_count, 1)

    def test_loss_run(self):
        p = self.fresh()
        for ai_won in (True, True, True):
            p.push_result(ai_won)
        self.assertEqual(p.loss_run(), 3)
        p.push_result(False)
        self.assertEqual(p.loss_run(), 0)

    def test_boss_unlock_at_five_streak(self):
        p = self.fresh()
        self.assertFalse(p.boss_available())
        p.current_streak = 5
        self.assertTrue(p.boss_available())

    def test_bonus_streak_counts_double(self):
        p = self.fresh()
        p.current_streak = 3
        p.bonus_streak()
        self.assertEqual(p.current_streak, 4)
        self.assertEqual(p.best_streak, 4)

    def test_boss_slayer_achievement(self):
        p = self.fresh()
        newly = p.register_game(ai_won=False, ai_q=None, you_won=False, you_q=None, boss=True)
        self.assertIn("boss_slayer", newly)
        p2 = self.fresh()
        newly2 = p2.register_game(ai_won=False, ai_q=None, you_won=False, you_q=None, boss=False)
        self.assertNotIn("boss_slayer", newly2)


if __name__ == "__main__":
    unittest.main()
