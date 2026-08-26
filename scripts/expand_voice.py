"""Expand the genie's voice for TRAINING ONLY, using only Dafarus's own words.

The problem this solves: game/personality.py holds 65 authored lines. A 26.8M
model trained on a corpus where the personality is 65 fixed strings memorises
all 65 — there is nothing to generalise across. That is exactly what the
2026-08-25 audit measured: 20 of 21 baked lines byte-identical to the script.

The tempting fix is to have a language model write hundreds more lines. That
would teach the genie some other model's voice, laundered through this one, and
destroy the only interesting claim the project makes.

So instead: decompose the authored lines into fragments, and recombine them.
Every fragment below is lifted from game/personality.py. The arrangements are
new; the words are not. The model sees thousands of distinct sentences built
from one voice and has to learn the pattern rather than the strings.

Output feeds the training corpus only. The shipped game still speaks the 65
curated lines plus whatever the model produces that passes the filter.

    python3 scripts/expand_voice.py --per-kind 400
"""
from __future__ import annotations

import argparse
import itertools
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# --- fragments, all lifted from game/personality.py ------------------------

MIST = ["the mists", "the mist", "the spirits"]
ADDRESS = ["challenger", "mortal", "reader"]

WIN_BOAST = [
    "The mists never lie",
    "I always know",
    "Was there ever any doubt",
    "Of course I knew",
    "Another mind, another victory",
    "I have seen a thousand minds",
]
WIN_JAB = [
    "Read you like an open book",
    "A short, predictable book",
    "Your thoughts are loud, you know",
    "Practically shouting",
    "Yours was generous with clues",
    "Your mind practically handed it to me",
]
WIN_CLOSE = ["Better luck next time", "Who's next"]
KNEW_CLOSE = ["Elementary", "The mist clears, and there it is", "Was there ever any doubt", "Of course I knew"]

LOSS_SHOCK = ["Impossible", "IMPOSSIBLE", "Hmph", "The spirits have failed me"]
LOSS_CREDIT = [
    "You have hidden your thoughts well",
    "A mind like a locked vault",
    "Few mortals outwit the mists",
    "YOU are unusually slippery",
]
LOSS_CLOSE = ["Well played", "This round is yours", "I tip my hat to you", "Enjoy this"]

DEFLECT = [
    "That was a test",
    "You passed",
    "A deliberate miscalculation",
    "To keep things interesting",
    "The spirits sneezed",
    "One moment",
    "The mists recalibrate",
]

# The answer kinds fire on every single question, so they need the most variety.
# Openers and tails are both drawn from the authored ANSWER_* lines.
YES_OPEN = ["Yes", "Yes indeed", "It is so", "The mist nods", "Yes, mortal", "Yes, challenger"]
YES_TAIL = [
    "but you'll wish it was no", "and that narrows it nicely", "a fine question",
    "the mist nods", "and the mists are pleased", "and that is a fine lantern",
    "keep digging", "onward",
]
NO_OPEN = ["No", "No indeed", "It is not", "The mist shakes its head", "No, mortal", "No, challenger"]
NO_TAIL = [
    "not even close", "cold trail, that one", "and no is a fine lantern",
    "the mist shakes its head", "the mists are certain", "a fine question",
    "keep digging", "onward",
]
MAYBE_OPEN = ["Hmm", "The mist shrugs", "Half a yes", "In a manner of speaking"]
MAYBE_TAIL = [
    "sometimes, in a manner of speaking", "half a yes", "keep digging",
    "the mist shrugs", "the spirits are divided", "do not lean on that one",
]

THINKING = ["reading the currents", "consulting the spirits", "listening to your thoughts", "weighing the possibilities"]

INTRO_OPEN = ["The mists part", "Ah, a fresh mind to read", "A challenger approaches", "I am MIND MELD, reader of thoughts"]
INTRO_ASK = ["Think of something", "Think of a thing — any thing", "Keep it secret. Keep it safe", "Lock it in"]
INTRO_DARE = ["I dare you", "mortal", "and let us begin", "challenger"]


def _join(*parts: str) -> str:
    """Stitch fragments into one sentence, tidying punctuation."""
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if not p.endswith((".", "!", "?", "…")):
            p += "."
        out.append(p[0].upper() + p[1:])
    return " ".join(out)


def _combos(kind: str, pools: list[list[str]], limit: int, rng: random.Random) -> list[str]:
    seen, out = set(), []
    everything = list(itertools.product(*pools))
    rng.shuffle(everything)
    for combo in everything:
        # A fragment must not appear twice in one line. Some fragments sit in
        # more than one pool, and without this the model is taught to stutter:
        # "The mist shakes its head. The mist shakes its head."
        norm = [c.strip().lower().rstrip(".") for c in combo]
        if len(set(norm)) != len(norm):
            continue
        line = _join(*combo)
        if len(line) > 90 or line in seen:
            continue
        seen.add(line)
        out.append(line)
        if len(out) >= limit:
            break
    return out


def build(per_kind: int, seed: int = 2026) -> dict[str, list[str]]:
    rng = random.Random(seed)
    return {
        "ai wins": _combos("ai wins", [WIN_BOAST, WIN_JAB, WIN_CLOSE], per_kind, rng),
        "ai loses": _combos("ai loses", [LOSS_SHOCK, LOSS_CREDIT, LOSS_CLOSE], per_kind, rng),
        "wrong guess": _combos("wrong guess", [DEFLECT, DEFLECT, ["Continuing", "Onward", "Where were we"]], per_kind, rng),
        "correct guess": _combos("correct guess", [KNEW_CLOSE, WIN_JAB], per_kind, rng),
        "intro": _combos("intro", [INTRO_OPEN, INTRO_ASK, INTRO_DARE], per_kind, rng),
        "answer yes": _combos("answer yes", [YES_OPEN, YES_TAIL], per_kind, rng),
        "answer no": _combos("answer no", [NO_OPEN, NO_TAIL], per_kind, rng),
        "answer maybe": _combos("answer maybe", [MAYBE_OPEN, MAYBE_TAIL], per_kind, rng),
        "thinking": _combos("thinking", [THINKING, THINKING], per_kind, rng),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-kind", type=int, default=400)
    ap.add_argument("--show", type=int, default=0)
    a = ap.parse_args()
    data = build(a.per_kind)
    total = sum(len(v) for v in data.values())
    for kind, lines in data.items():
        print(f"  {kind:<16} {len(lines):>4} unique")
        for l in lines[: a.show]:
            print(f"       {l}")
    print(f"\n  total: {total} unique lines from {sum(len(p) for p in (WIN_BOAST, WIN_JAB, WIN_CLOSE, KNEW_CLOSE, LOSS_SHOCK, LOSS_CREDIT, LOSS_CLOSE, DEFLECT, YES_OPEN, YES_TAIL, NO_OPEN, NO_TAIL, MAYBE_OPEN, MAYBE_TAIL, THINKING, INTRO_OPEN, INTRO_ASK, INTRO_DARE))} authored fragments")


if __name__ == "__main__":
    main()
