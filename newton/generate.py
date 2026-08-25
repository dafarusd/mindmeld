"""Generation / inference for a trained newton checkpoint."""

from __future__ import annotations

import sys
from pathlib import Path

import torch

from .model import GPT, GPTConfig
from .tokenizer import Tokenizer

ROOT = Path(__file__).resolve().parent.parent


def load_brain(ckpt_dir: Path | None = None) -> tuple[GPT, Tokenizer]:
    ckpt_dir = ckpt_dir or ROOT / "ckpt"
    fp16 = ckpt_dir / "brain.fp16.pt"
    fp32 = ckpt_dir / "last.pt"
    if not fp16.exists() and not fp32.exists():
        raise FileNotFoundError(f"no brain found in {ckpt_dir}")
    path = fp16 if fp16.exists() else fp32
    blob = torch.load(path, weights_only=False)
    cfg = GPTConfig(**blob["cfg"])
    model = GPT(cfg)
    state = blob["model"]
    if blob.get("dtype") == "fp16":
        state = {k: (v.float() if v.dtype == torch.float16 else v) for k, v in state.items()}
    model.load_state_dict(state)
    model.eval()
    tok = Tokenizer.load(ckpt_dir / "tokenizer.json")
    return model, tok


def complete(model: GPT, tok: Tokenizer, prompt: str, max_new: int = 60, temperature: float = 0.7, top_k: int = 40) -> str:
    ids = tok.encode(prompt)
    idx = torch.tensor([ids], dtype=torch.long)
    out = model.generate(idx, max_new=max_new, temperature=temperature, top_k=top_k, stop_id=tok.eot_id)
    return tok.decode(out[0][len(ids):].tolist())


def main() -> None:
    model, tok = load_brain()
    prompt = " ".join(sys.argv[1:]) or "Q: Is it an animal? A: yes\nQ:"
    print(complete(model, tok, prompt))


if __name__ == "__main__":
    main()
