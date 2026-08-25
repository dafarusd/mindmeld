"""Training loop for the newton GPT. CPU-optimized, checkpointed, time-boxable."""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import torch

from .model import GPT, GPTConfig
from .tokenizer import Tokenizer

ROOT = Path(__file__).resolve().parent.parent


class Trainer:
    def __init__(
        self,
        corpus_path: Path | None = None,
        ckpt_dir: Path | None = None,
        cfg: GPTConfig | None = None,
        batch_size: int = 16,
        lr: float = 3e-4,
        min_lr: float = 3e-5,
        warmup_steps: int = 100,
        max_steps: int = 4000,
        time_budget_s: float | None = None,
        log_every: int = 25,
        ckpt_every: int = 500,
        seed: int = 1337,
    ):
        torch.manual_seed(seed)
        torch.set_num_threads(14)
        self.corpus_path = corpus_path or ROOT / "data" / "corpus.txt"
        self.ckpt_dir = ckpt_dir or ROOT / "ckpt"
        self.ckpt_dir.mkdir(parents=True, exist_ok=True)
        self.batch_size = batch_size
        self.lr = lr
        self.min_lr = min_lr
        self.warmup_steps = warmup_steps
        self.max_steps = max_steps
        self.time_budget_s = time_budget_s
        self.log_every = log_every
        self.ckpt_every = ckpt_every

        self.tok = self._load_or_train_tokenizer()
        self.cfg = cfg or GPTConfig(vocab_size=self.tok.vocab_size)
        self.cfg.vocab_size = self.tok.vocab_size
        self.model = GPT(self.cfg)
        self.opt = torch.optim.AdamW(self.model.parameters(), lr=lr, betas=(0.9, 0.95), weight_decay=0.1)
        self.tokens = self._load_tokens()
        self.step = 0
        self._resume()

    def _load_or_train_tokenizer(self) -> Tokenizer:
        path = self.ckpt_dir / "tokenizer.json"
        if path.exists():
            return Tokenizer.load(path)
        print("training tokenizer on corpus...")
        text = self.corpus_path.read_text(encoding="utf-8")
        docs = text.split("<|endoftext|>")
        tok = Tokenizer()
        tok.train(docs, target_vocab=1500, min_count=4)
        tok.save(path)
        print(f"tokenizer vocab: {tok.vocab_size}")
        return tok

    def _load_tokens(self) -> torch.Tensor:
        cache = self.ckpt_dir / "tokens.pt"
        if cache.exists():
            return torch.load(cache)
        print("encoding corpus...")
        text = self.corpus_path.read_text(encoding="utf-8")
        ids = self.tok.encode(text.replace("<|endoftext|>", " <|endoftext|> "))
        t = torch.tensor(ids, dtype=torch.long)
        torch.save(t, cache)
        print(f"tokens: {len(t):,}")
        return t

    def _batch(self) -> tuple[torch.Tensor, torch.Tensor]:
        bs = self.cfg.block_size
        ix = torch.randint(0, len(self.tokens) - bs - 1, (self.batch_size,))
        x = torch.stack([self.tokens[i : i + bs] for i in ix])
        y = torch.stack([self.tokens[i + 1 : i + bs + 1] for i in ix])
        return x, y

    def _lr_at(self, step: int) -> float:
        if step < self.warmup_steps:
            return self.lr * (step + 1) / self.warmup_steps
        progress = (step - self.warmup_steps) / max(1, self.max_steps - self.warmup_steps)
        progress = min(progress, 1.0)
        return self.min_lr + 0.5 * (self.lr - self.min_lr) * (1 + math.cos(math.pi * progress))

    def _save(self, name: str = "last.pt") -> None:
        path = self.ckpt_dir / name
        torch.save({"model": self.model.state_dict(), "cfg": vars(self.cfg), "step": self.step}, path)

    def _resume(self) -> None:
        path = self.ckpt_dir / "last.pt"
        if path.exists():
            blob = torch.load(path, weights_only=False)
            self.model.load_state_dict(blob["model"])
            self.step = blob["step"]
            print(f"resumed from step {self.step}")

    @torch.no_grad()
    def estimate_val_loss(self, batches: int = 20) -> float:
        self.model.eval()
        losses = []
        for _ in range(batches):
            x, y = self._batch()
            _, loss = self.model(x, y)
            losses.append(loss.item())
        self.model.train()
        return sum(losses) / len(losses)

    def train(self) -> None:
        self.model.train()
        n_params = self.model.num_params()
        print(f"model params: {n_params/1e6:.2f}M | tokens: {len(self.tokens):,} | batch {self.batch_size} | block {self.cfg.block_size}")
        t0 = time.time()
        log_path = self.ckpt_dir / "train_log.jsonl"
        with open(log_path, "a", encoding="utf-8") as log:
            while self.step < self.max_steps:
                if self.time_budget_s and time.time() - t0 > self.time_budget_s:
                    print("time budget reached")
                    break
                lr = self._lr_at(self.step)
                for g in self.opt.param_groups:
                    g["lr"] = lr
                x, y = self._batch()
                _, loss = self.model(x, y)
                self.opt.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                self.opt.step()
                self.step += 1
                if self.step % self.log_every == 0:
                    elapsed = time.time() - t0
                    rec = {"step": self.step, "loss": round(loss.item(), 4), "lr": f"{lr:.2e}", "elapsed_s": round(elapsed)}
                    print(rec)
                    log.write(json.dumps(rec) + "\n")
                    log.flush()
                if self.step % self.ckpt_every == 0:
                    self._save()
        self._save()
        val = self.estimate_val_loss()
        print(f"final step {self.step}, approx loss {val:.4f}, total time {time.time()-t0:.0f}s")


def main() -> None:
    args = sys.argv[1:]
    kwargs = {}
    model_size = {"n_layer": 6, "n_head": 6, "n_embd": 384}
    for a in args:
        if a.startswith("--max-steps="):
            kwargs["max_steps"] = int(a.split("=")[1])
        elif a.startswith("--time-budget="):
            kwargs["time_budget_s"] = float(a.split("=")[1])
        elif a.startswith("--batch-size="):
            kwargs["batch_size"] = int(a.split("=")[1])
        elif a.startswith("--embd="):
            model_size["n_embd"] = int(a.split("=")[1])
        elif a.startswith("--layers="):
            model_size["n_layer"] = int(a.split("=")[1])
        elif a.startswith("--heads="):
            model_size["n_head"] = int(a.split("=")[1])
    kwargs["cfg"] = GPTConfig(vocab_size=1500, **model_size)
    trainer = Trainer(**kwargs)
    trainer.train()


if __name__ == "__main__":
    main()
