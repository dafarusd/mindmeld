# MIND MELD 🧠⚡

*It knows what you're thinking. Probably.*

A 20-questions duel against a genie AI — with a brain that was
**trained from scratch on a home computer**. No cloud, no APIs,
no tracking.

```
┌──────────────────────────┐
│ MIND MELD #853           │
│ AI read you in 5 🟩       │
│ You read the AI in 9 🟩   │
│ ⚡ YOU WON THE MELD        │
└──────────────────────────┘
```

## Quickstart (any machine)

**Requirements: Python 3.10+. Nothing else to install.**

```sh
git clone <this repo>
cd mindmeld            # or wherever you put it
./bin/mindmeld         # terminal version — daily duel
./bin/mindmeld --free  # unlimited practice rounds
python3 -m game.web    # browser version -> http://127.0.0.1:8137
```

Want friends on your network to play?
`python3 -m game.web --host=0.0.0.0` then share `http://<your-ip>:8137`.

**The trained brain's voice** (`ckpt/brain.fp16.pt` is included): for the
genie to speak with its *learned* voice, install PyTorch
(`pip install torch`). Without it the game still plays perfectly — the
genie speaks its built-in script and a one-line notice tells you why.

## The game

**Round 1:** think of an animal, object, food, famous person, or
character. The genie asks yes/no/maybe questions and reads your mind —
**98.8% accuracy, median 9 questions**, over a 325-entity knowledge base.

**Round 2:** the genie thinks of something. You interrogate it in free
text; it answers truthfully from its knowledge. Fewer questions than the
genie needed = you win the meld.

## Architecture — each layer does what it's actually good at

| Layer | What it does | Numbers |
|---|---|---|
| **Knowledge engine** (`game/`) | 325 entities × 120 curated attributes, entropy-based question selection, ground-truth answers | 98.8% self-play, median 9 questions |
| **Trained LLM** (`newton/`) | the genie's *voice*: banter, taunts, celebrations | 26M-param GPT, loss 0.115 |

The engine is the spine; the model is the personality. Model output
passes a strict validation gate (length, charset, must end in sentence
punctuation, no fact-leaks) and falls back to curated lines — the game
can never break because the brain had a weird day. The model's voice is
**on by default**; `./bin/mindmeld --no-brain-voice` forces curated-only.

## The brain

- Byte-level BPE tokenizer, from scratch, 1,500 tokens
- 8-layer, 8-head, 512-wide GPT (26.04M params), pure PyTorch, CPU-only
- Trained **14,432 steps across two 2-hour runs** (warm restart):
  loss 6.4 → **0.115**
- Ships as `ckpt/brain.fp16.pt` (53.6MB, fp16 — verified byte-identical
  voice output vs the fp32 training checkpoint)
- Corpus: 6,552 documents / 4.2MB — engine-simulated game transcripts,
  entity fact sheets, Round-B Q&A, personality lines, share cards
  (`scripts/gen_corpus.py`)

What it demonstrably learned: exact game formats, the genie's curated
voice (verbatim recall, 83% acceptance through the quality gate), entity
names, and approximate semantic profiles — asked to guess from
"fictional, villain, from space adventures" it answered **Superman**
(wrong, but 4/5 traits correct — a plausible human near-miss).

```sh
python3 -m newton.train --max-steps=30000 --batch-size=16 --time-budget=7200 \
    --embd=512 --layers=8 --heads=8        # train more (resumes from ckpt)
python3 -m newton.export                   # re-export the fp16 brain
python3 -m newton.generate "GENIE (ai wins): "   # sample it
```

## Viral mechanics (per the Wordle/Akinator playbook)

- One **daily secret**, same for every player → comparison + FOMO
- **Share card** with emoji results → word-of-mouth engine
- **Streaks** (`data/profile.json`) → daily habit
- 3-minute rounds, zero install, zero signup → no friction
- The AI's misses are comedy → even failure is shareable
- The story itself spreads: *"the brain in this game was trained on a
  laptop, and you can watch it get funnier every time it trains"*

## Tests

```sh
python3 -m unittest discover -s tests     # 20 tests, all green
```

Gates enforced: KB completeness (every entity answers all 120
attributes; every attribute has questions), **self-play accuracy ≥ 90%**,
median question count, tokenizer round-trips (incl. unicode), model
forward/generate shapes, answer parsing, guess-matching rules.

## Layout

```
newton/    the brain: tokenizer.py, model.py, train.py, generate.py, export.py
game/      the game: kb.py, engine.py, questions.py, personality.py,
           voice.py, tui.py, web.py, static/index.html, profile.py
scripts/   gen_corpus.py
tests/     test_engine.py, test_brain.py
ckpt/      brain.fp16.pt (shipped), tokenizer.json  — last.pt and logs
           are training artifacts, gitignored
data/      created at play time (profile.json)
bin/       mindmeld
DEVLOG.md  project journal (what changed, why, and the bugs that mattered)
```

