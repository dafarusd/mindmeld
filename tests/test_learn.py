import tempfile
import unittest
from pathlib import Path

from game import kb
from game.engine import MindReader, resolve_entity
from game.learn import LearnError, learn, load_learned
from game.kb import ATTRIBUTES, YES, NO, MAYBE
import random


class TestLearn(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "learned.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_learn_persists(self):
        clean = learn("steam deck", [("is_electronic", YES), ("is_toy", MAYBE), ("found_in_home", YES)], path=self.path)
        self.assertEqual(clean, "steam deck")
        data = load_learned(self.path)
        self.assertIn("steam deck", data)
        self.assertEqual(data["steam deck"]["vec"]["is_electronic"], YES)
        self.assertEqual(data["steam deck"]["vec"]["is_animal"], MAYBE)

    def test_rejects_bad_names(self):
        for bad in ["x", "!!!", "a" * 50, "<script>"]:
            with self.assertRaises(LearnError, msg=bad):
                learn(bad, [], path=self.path)

    def test_rejects_existing_entity(self):
        with self.assertRaises(LearnError):
            learn("dog", [], path=self.path)
        with self.assertRaises(LearnError):
            learn("the pizza", [], path=self.path)

    def test_rejects_duplicate_learn(self):
        learn("steam deck", [], path=self.path)
        with self.assertRaises(LearnError):
            learn("steam deck", [], path=self.path)

    def test_cap_enforced(self):
        for i in range(3):
            learn(f"thing number {i}", [], path=self.path)
        import game.learn as learn_mod

        old = learn_mod.MAX_LEARNED
        learn_mod.MAX_LEARNED = 3
        try:
            learn("thing number 3", [], path=self.path)
            data = load_learned(self.path)
            self.assertEqual(len(data), 3)
            self.assertNotIn("thing number 0", data)
            self.assertIn("thing number 3", data)
        finally:
            learn_mod.MAX_LEARNED = old


class TestLearnedEntityGuessable(unittest.TestCase):
    """End-to-end: learn an entity, reload the KB, and the engine can guess it."""

    def test_learn_reload_guess(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "learned.json"
            answers = [("is_electronic", YES), ("found_in_home", YES), ("is_toy", YES),
                       ("handheld", YES), ("has_screen", YES), ("connects_to_internet", YES)]
            learn("steam deck", answers, path=path)

            import shutil
            real = kb.ENTITY_NAMES
            dst = Path(kb.__file__).resolve().parent.parent / "data" / "learned.json"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(path, dst)
            try:
                kb.reload()
                self.assertIn("steam deck", kb.ENTITIES)
                self.assertIsNotNone(resolve_entity("steam deck"))

                mr = MindReader(rng=random.Random(3))
                target_vec = kb.ENTITIES["steam deck"]["vec"]
                for _ in range(25):
                    attr = mr.next_question()
                    if attr is None:
                        break
                    mr.answer(attr, target_vec[attr])
                    if mr.should_guess() and mr.best_candidate() == "steam deck":
                        break
                self.assertEqual(mr.best_candidate(), "steam deck")
            finally:
                dst.unlink(missing_ok=True)
                kb.reload()
                self.assertNotIn("steam deck", kb.ENTITIES)


if __name__ == "__main__":
    unittest.main()
