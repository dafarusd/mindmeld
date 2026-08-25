"""Model-powered genie voice.

The trained GPT generates SHORT banter lines only. Every output passes
through strict validation; anything weird falls back to curated lines.
The model never touches facts, questions, or game state.
"""

from __future__ import annotations

import random
import re
from pathlib import Path

from . import personality as curated

ROOT = Path(__file__).resolve().parent.parent

_brain = None
_brain_failed = False

MAX_LINE = 90
BANNED_PATTERNS = re.compile(r"[<>{}\\|]|\b(secret|answer is|it was)\b", re.IGNORECASE)

# Voice-quality gate: the model speaks only when it produces clean,
# complete, on-voice lines (length, charset, sentence-ending checks).
# Anything else falls back to curated lines. Enabled by default after
# the 4h/14.4k-step brain reached 83% acceptance in evaluation.
VOICE_ENABLED = True


def set_enabled(flag: bool) -> None:
    global VOICE_ENABLED
    VOICE_ENABLED = flag


def _load():
    global _brain, _brain_failed
    if _brain is not None or _brain_failed:
        return
    try:
        from newton.generate import load_brain

        _brain = load_brain(ROOT / "ckpt")
    except ImportError:
        _brain_failed = True
        print("[mind meld] PyTorch not installed — the genie speaks its built-in script.")
        print("[mind meld] for the trained-brain voice: pip install torch")
    except Exception as exc:
        _brain_failed = True
        print(f"[mind meld] brain unavailable ({exc}) — using built-in voice.")


def brain_available() -> bool:
    _load()
    return _brain is not None


def _valid(line: str) -> bool:
    line = line.strip()
    if not (8 <= len(line) <= MAX_LINE):
        return False
    if BANNED_PATTERNS.search(line):
        return False
    if sum(c.isalpha() for c in line) / max(len(line), 1) < 0.5:
        return False
    if line[-1] not in ".!?…\"'":
        return False
    return True


def _gen(prompt: str, temperature: float = 0.85, max_new: int = 64, tries: int = 3, must_start: tuple[str, ...] | None = None) -> str | None:
    if not brain_available():
        return None
    model, tok = _brain
    from newton.generate import complete

    if not prompt.endswith(" "):
        prompt += " "
    for _ in range(tries):
        out = complete(model, tok, prompt, max_new=max_new, temperature=temperature, top_k=40)
        line = out.lstrip("\n").split("\n")[0].strip()
        if must_start and not line.lower().startswith(must_start):
            continue
        if _valid(line):
            return line
    return None


ANSWER_POLARITY = {
    "answer yes": ("yes", "aye", "indeed"),
    "answer no": ("no", "nope"),
    "answer maybe": ("hmm", "maybe", "the mist shrugs"),
}


def banter(kind: str, rng: random.Random, use_model: bool = VOICE_ENABLED) -> str:
    """kind: one of the personality categories, e.g. 'ai wins', 'wrong guess'.

    The trained model speaks only when it clears the quality gate.
    Everything else falls back to curated lines. The game never breaks
    because the brain had a weird day.
    """
    table = {
        "intro": curated.INTROS,
        "daily intro": curated.INTROS_DAILY,
        "ai wins": curated.AI_WINS,
        "ai loses": curated.AI_LOSES,
        "you win duel": curated.YOU_WIN_DUEL,
        "ai wins duel": curated.AI_WINS_DUEL,
        "wrong guess": curated.WRONG_GUESS,
        "correct guess": curated.CORRECT_GUESS,
        "secret picked": curated.SECRET_PICKED,
        "answer yes": curated.ANSWER_YES,
        "answer no": curated.ANSWER_NO,
        "answer maybe": curated.ANSWER_MAYBE,
    }
    fallback = rng.choice(table.get(kind, curated.INTROS))
    if not use_model:
        return fallback
    line = _gen(f"GENIE ({kind}): ", must_start=ANSWER_POLARITY.get(kind))
    return line if line else fallback


def hunch(transcript_lines: list[str], max_new: int = 16) -> str | None:
    """The trained model's own guess from a Round A transcript.

    Gated hard: short, no format artifacts. Gibberish is returned too —
    callers display it in quotes as comedy. Only structural junk is
    filtered out.
    """
    if not brain_available():
        return None
    model, tok = _brain
    from newton.generate import complete

    prompt = "\n".join(transcript_lines) + "\nGUESS: "
    out = complete(model, tok, prompt, max_new=max_new, temperature=0.5, top_k=30)
    line = out.lstrip("\n").split("\n")[0].split("->")[0].strip()
    if not line or len(line) > 30:
        return None
    if any(bad in line for bad in ("Q:", "A:", "<|", "GENIE", "PLAYER")):
        return None
    return line
