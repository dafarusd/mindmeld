"""Byte-level BPE tokenizer, from scratch. No dependencies.

Base vocabulary: 256 raw byte tokens + <|endoftext|> special.
Training: iteratively merge the most frequent adjacent pair.
Encoding: apply merges in rank order (standard BPE application).
"""

from __future__ import annotations

import json
from pathlib import Path

SPECIAL = "<|endoftext|>"


class Tokenizer:
    def __init__(self):
        self.merges: list[tuple[int, int]] = []
        self.vocab: dict[int, bytes] = {i: bytes([i]) for i in range(256)}
        self.eot_id = 256
        self.vocab[256] = SPECIAL.encode()

    @property
    def vocab_size(self) -> int:
        return len(self.vocab)

    @staticmethod
    def _to_ids(text: str) -> list[int]:
        return list(text.encode("utf-8"))

    def train(self, texts: list[str], target_vocab: int = 1200, min_count: int = 4) -> None:
        docs = [self._to_ids(t) for t in texts]
        next_id = 257
        while next_id < target_vocab:
            pair_counts: dict[tuple[int, int], int] = {}
            for ids in docs:
                for a, b in zip(ids, ids[1:]):
                    pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1
            if not pair_counts:
                break
            (a, b), count = max(pair_counts.items(), key=lambda kv: kv[1])
            if count < min_count:
                break
            self.merges.append((a, b))
            self.vocab[next_id] = self.vocab[a] + self.vocab[b]
            for i, ids in enumerate(docs):
                merged: list[int] = []
                j = 0
                while j < len(ids):
                    if j + 1 < len(ids) and ids[j] == a and ids[j + 1] == b:
                        merged.append(next_id)
                        j += 2
                    else:
                        merged.append(ids[j])
                        j += 1
                docs[i] = merged
            next_id += 1

    def encode(self, text: str) -> list[int]:
        ids = self._to_ids(text)
        for rank, (a, b) in enumerate(self.merges):
            new_id = 257 + rank
            merged: list[int] = []
            j = 0
            while j < len(ids):
                if j + 1 < len(ids) and ids[j] == a and ids[j + 1] == b:
                    merged.append(new_id)
                    j += 2
                else:
                    merged.append(ids[j])
                    j += 1
            ids = merged
        return ids

    def decode(self, ids: list[int]) -> str:
        raw = b"".join(self.vocab[i] for i in ids if i in self.vocab and i != self.eot_id)
        return raw.decode("utf-8", errors="replace")

    def save(self, path: Path) -> None:
        data = {"merges": self.merges, "vocab_size": self.vocab_size}
        Path(path).write_text(json.dumps(data), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Tokenizer":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        tok = cls()
        tok.merges = [tuple(m) for m in data["merges"]]
        for rank, (a, b) in enumerate(tok.merges):
            tok.vocab[257 + rank] = tok.vocab[a] + tok.vocab[b]
        return tok
