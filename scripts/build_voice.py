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
        dups = 0
        while dups < DUP_STOP:
            total_tried += 1
            line = voice._gen(f"GENIE ({kind}): ", temperature=rng.uniform(0.6, 1.05), tries=1)
            if line and any(m in line for m in STALE_MARKERS):
                line = None
            if line and line not in seen:
                seen.add(line)
                lines.append(line)
                dups = 0
            else:
                dups += 1
        baked[kind] = lines
        print(f"  {kind}: {len(lines)} lines kept", flush=True)

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
