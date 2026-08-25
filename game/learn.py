"""Stump-and-learn: when the genie fails, it learns the player's thing.

Learned entities live in data/learned.json and are merged over the base
KB at load time. Guardrails: strict name validation, fuzzy dedupe against
everything already known, 200-entity cap (FIFO).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .kb import ATTRIBUTES, ENTITIES, MAYBE

LEARNED_PATH = Path(__file__).resolve().parent.parent / "data" / "learned.json"
MAX_LEARNED = 200
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9 '\-]{1,38}[a-z0-9]$")


class LearnError(Exception):
    pass


def validate_name(raw: str) -> str:
    name = raw.strip().lower()
    if not _NAME_RE.match(name):
        raise LearnError("names: 3-40 chars, letters/numbers/spaces only")
    return name


def check_not_known(name: str, learned: dict) -> None:
    from .engine import resolve_entity

    if resolve_entity(name) is not None:
        raise LearnError(f"I already know something very close to '{name}'")
    if name in {k.lower() for k in learned}:
        raise LearnError(f"'{name}' is already in my learned knowledge")


def load_learned(path: Path | None = None) -> dict:
    p = path or LEARNED_PATH
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_learned(data: dict, path: Path | None = None) -> None:
    p = path or LEARNED_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def learn(name: str, answers: list[tuple[str, float]], blurb: str = "learned from a challenger", path: Path | None = None) -> str:
    """Record a new entity from a Round A transcript's answers."""
    clean = validate_name(name)
    data = load_learned(path)
    check_not_known(clean, data)

    vec = {a: MAYBE for a in ATTRIBUTES}
    for attr, value in answers:
        if attr in vec:
            vec[attr] = value
    data[clean] = {"name": clean, "blurb": blurb, "vec": vec, "learned": True}

    while len(data) > MAX_LEARNED:
        data.pop(next(iter(data)))
    save_learned(data, path)
    return clean
