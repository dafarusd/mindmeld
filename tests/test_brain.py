import unittest

from newton.tokenizer import Tokenizer

try:
    import torch

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


class TestTokenizer(unittest.TestCase):
    def test_base_vocab_is_bytes_plus_special(self):
        tok = Tokenizer()
        self.assertEqual(tok.vocab_size, 257)
        self.assertEqual(tok.decode(tok.encode("hello")), "hello")

    def test_round_trip_after_merges(self):
        tok = Tokenizer()
        tok.train(["the cat sat", "the cat ran", "the dog sat"], target_vocab=270, min_count=1)
        for s in ["the cat sat", "the dog ran", "unseen text!"]:
            self.assertEqual(tok.decode(tok.encode(s)), s)

    def test_merges_grow_vocab(self):
        tok = Tokenizer()
        tok.train(["ab ab ab ab"] * 5, target_vocab=260, min_count=2)
        self.assertGreater(tok.vocab_size, 257)

    def test_save_load_round_trip(self, tmp=None):
        import tempfile
        from pathlib import Path

        tok = Tokenizer()
        tok.train(["mind meld mind meld"], target_vocab=262, min_count=2)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "tok.json"
            tok.save(path)
            tok2 = Tokenizer.load(path)
            s = "mind meld!"
            self.assertEqual(tok2.decode(tok2.encode(s)), s)
            self.assertEqual(tok.encode(s), tok2.encode(s))

    def test_unicode_round_trip(self):
        tok = Tokenizer()
        s = "Beyoncé — emoji 🧠⚡ accents"
        self.assertEqual(tok.decode(tok.encode(s)), s)


@unittest.skipUnless(HAS_TORCH, "PyTorch not installed")
class TestModelShape(unittest.TestCase):
    def test_forward_shapes_and_loss(self):
        from newton.model import GPT, GPTConfig

        cfg = GPTConfig(vocab_size=100, block_size=16, n_layer=2, n_head=2, n_embd=32, dropout=0.0)
        model = GPT(cfg)
        x = torch.randint(0, 100, (2, 16))
        logits, loss = model(x, x)
        self.assertEqual(tuple(logits.shape), (2, 16, 100))
        self.assertIsNotNone(loss)
        self.assertGreater(loss.item(), 0)

    def test_generate_extends_sequence(self):
        from newton.model import GPT, GPTConfig

        cfg = GPTConfig(vocab_size=50, block_size=8, n_layer=1, n_head=1, n_embd=16, dropout=0.0)
        model = GPT(cfg)
        idx = torch.randint(0, 50, (1, 4))
        out = model.generate(idx, max_new=5, temperature=1.0, top_k=10)
        self.assertGreaterEqual(out.shape[1], 5)


if __name__ == "__main__":
    unittest.main()
