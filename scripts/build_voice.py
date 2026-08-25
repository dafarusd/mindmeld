"""Pre-bake the genie's voice with the trained model.

Generates thousands of candidate lines per banter kind, runs the same
validation gate used at runtime (length, charset, sentence-ending,
polarity for answers), dedupes, and merges into static_site/data.js as
MM_DATA.voice_model. Runs offline at build time — the static game ships
the model's words without needing the model.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game import voice

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "static_site" / "data.js"

KINDS = [
    "intro", "daily intro", "ai wins", "ai loses", "you win duel", "ai wins duel",
    "wrong guess", "correct guess", "secret picked", "answer yes", "answer no", "answer maybe",
]
TARGET_PER_KIND = 60
DUP_STOP = 25
STALE_MARKERS = ("141", "325")

# --- strict bake-time validity ------------------------------------------------
# The runtime filter checks length, charset, sentence-ending and fact-leaks.
# Garbled generations pass all four ("Wribrate s, and there it is." is the right
# length, clean charset, ends in a period, leaks nothing), so the v2.0 bake
# shipped 22 unusable lines. These checks close that hole at bake time.

import re as _re
from game.kb import ENTITIES
from game import personality as _curated
from game.questions import QUESTIONS


def _trained_vocab() -> set[str]:
    """Every word the model was actually trained on. Anything else is an artifact."""
    words: set[str] = set()

    def add(text):
        for w in _re.split(r"[^a-z0-9'\u2014-]+", str(text).lower()):
            w = w.strip("'")
            if w:
                words.add(w)

    for name in dir(_curated):
        if name.startswith("_"):
            continue
        add(getattr(_curated, name))
    for e in ENTITIES:
        add(e)
    add(QUESTIONS)
    return words


_VOCAB = _trained_vocab()
_LEAK_RE = _re.compile(r"\)\s*:|GENIE|\bit is (a|an|not)\b|\bnotably\b", _re.IGNORECASE)


def _edit(a: str, b: str) -> int:
    if abs(len(a) - len(b)) > 4:
        return 99
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def strict_ok(line: str, kept: list[str]) -> str | None:
    """Return None if the line is good, else the reason it was rejected."""
    if _LEAK_RE.search(line):
        return "prompt/fact leak"
    toks = [w.strip("'") for w in _re.split(r"[^A-Za-z0-9'\u2014-]+", line.lower()) if w.strip("'")]
    bad = [w for w in toks if w not in _VOCAB and not w.isdigit()]
    if bad:
        return f"unknown word {bad[0]!r}"
    for i in range(len(toks) - 1):
        if toks[i] == toks[i + 1]:
            return "stutter"
    if _re.search(r"\.{4,}", line):
        return "punctuation artifact"
    for k in kept:
        if _edit(line, k) <= 3:
            return "near-duplicate"
    return None


def main() -> None:
    if not voice.brain_available():
        print("no brain available — curated voice only")
        return
    rng = random.Random(2026)
    baked: dict[str, list[str]] = {}
    total_tried = 0
    for kind in KINDS:
        seen: set[str] = set()
        lines: list[str] = []
        rejected: dict[str, int] = {}
        dups = 0
        while dups < DUP_STOP:
            total_tried += 1
            line = voice._gen(f"GENIE ({kind}): ", temperature=rng.uniform(0.6, 1.05), tries=1)
            if line and any(m in line for m in STALE_MARKERS):
                line = None
            if line and (reason := strict_ok(line, lines)):
                rejected[reason.split()[0]] = rejected.get(reason.split()[0], 0) + 1
                line = None
            if line and line not in seen:
                seen.add(line)
                lines.append(line)
                dups = 0
            else:
                dups += 1
        baked[kind] = lines
        print(f"  {kind}: {len(lines)} kept | rejected {rejected}", flush=True)

    raw = DATA_JS.read_text(encoding="utf-8")
    prefix = "(typeof window !== 'undefined' ? window : globalThis).MM_DATA = "
    assert raw.startswith(prefix)
    data = json.loads(raw[len(prefix):].rstrip().rstrip(";"))
    data["voice_model"] = baked
    DATA_JS.write_text(prefix + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    kept = sum(len(v) for v in baked.values())
    print(f"voice baked: {kept} model lines from {total_tried} candidates ({100*kept/max(total_tried,1):.0f}% acceptance) -> {DATA_JS}")


if __name__ == "__main__":
    main()
