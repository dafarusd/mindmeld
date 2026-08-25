import random
import tempfile
import unittest
from pathlib import Path

from game.engine import MindReader
from game import kb
from game.profile import ACHIEVEMENTS, Profile


def fresh_profile():
    tmp = tempfile.TemporaryDirectory()
    p = Profile(Path(tmp.name) / "profile.json")
    p.path = Path(tmp.name) / "profile.json"
    return p


class TestRanks(unittest.TestCase):
    def test_rank_thresholds(self):
        p = fresh_profile()
        self.assertEqual(p.rank(), "Apprentice")
        p.wins = 3
        self.assertEqual(p.rank(), "Mind Reader")
        p.wins = 7
        self.assertEqual(p.rank(), "Thought Thief")
        p.wins = 15
        self.assertEqual(p.rank(), "Mistwalker")
        p.wins = 30
        self.assertEqual(p.rank(), "Geniebreaker")


class TestAchievements(unittest.TestCase):
    def test_first_blood(self):
        p = fresh_profile()
        newly = p.register_game(ai_won=False, ai_q=None, you_won=True, you_q=8)
        self.assertIn("first_blood", newly)
        newly = p.register_game(ai_won=False, ai_q=None, you_won=True, you_q=8)
        self.assertNotIn("first_blood", newly)

    def test_surgical(self):
        p = fresh_profile()
        newly = p.register_game(ai_won=True, ai_q=5, you_won=True, you_q=6)
        self.assertIn("surgical", newly)

    def test_surgical_needs_six_or_fewer(self):
        p = fresh_profile()
        newly = p.register_game(ai_won=True, ai_q=5, you_won=True, you_q=7)
        self.assertNotIn("surgical", newly)

    def test_stumper(self):
        p = fresh_profile()
        newly = p.register_game(ai_won=False, ai_q=None, you_won=False, you_q=None)
        self.assertIn("stumper", newly)

    def test_hard_winner_needs_hard(self):
        p = fresh_profile()
        newly = p.register_game(ai_won=False, ai_q=None, you_won=True, you_q=5, hard=False)
        self.assertNotIn("hard_winner", newly)
        p2 = fresh_profile()
        newly = p2.register_game(ai_won=False, ai_q=None, you_won=True, you_q=5, hard=True)
        self.assertIn("hard_winner", newly)

    def test_teacher(self):
        p = fresh_profile()
        newly = p.register_game(ai_won=False, ai_q=None, you_won=False, you_q=None, learned_new=True)
        self.assertIn("teacher", newly)

    def test_on_fire_needs_streak(self):
        p = fresh_profile()
        p.current_streak = 5
        newly = p.register_game(ai_won=True, ai_q=9, you_won=True, you_q=9)
        self.assertIn("on_fire", newly)

    def test_persistence_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            p = Profile(path)
            p.register_game(ai_won=False, ai_q=None, you_won=True, you_q=4, learned_new=True)
            p2 = Profile(path)
            self.assertIn("first_blood", p2.achievements)
            self.assertIn("surgical", p2.achievements)
            self.assertIn("teacher", p2.achievements)

    def test_all_achievement_keys_have_text(self):
        for key in ("first_blood", "surgical", "stumper", "on_fire", "teacher", "hard_winner"):
            self.assertIn(key, ACHIEVEMENTS)


class TestHardMode(unittest.TestCase):
    def test_hard_mode_caps_questions(self):
        mr = MindReader(rng=random.Random(1), max_questions=10)
        for _ in range(15):
            attr = mr.next_question()
            if attr is None:
                break
            mr.answer(attr, 1.0)
        self.assertLessEqual(len(mr.asked), 10)

    def test_hard_mode_accuracy_gate(self):
        wins = 0
        for t in kb.ENTITY_NAMES:
            mr = MindReader(rng=random.Random(7), max_questions=10)
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
        self.assertGreaterEqual(rate, 0.85, f"hard mode only {rate:.0%}")


if __name__ == "__main__":
    unittest.main()
