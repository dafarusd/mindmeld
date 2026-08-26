# MIND MELD 🧠⚡

*It knows what you're thinking. Probably.*

A game of 20 Questions against a genie, played in two directions. The genie
guesses what you're thinking, then hides something and dares you to guess back.
It runs entirely on your own machine — no cloud service, no API key, no tracking.

The genie's personality comes from a language model trained from scratch on a
home laptop, which is a smaller and stranger thing than it sounds. See
[the brain](#the-brain).

```
┌──────────────────────────┐
│ MIND MELD #853           │
│ AI read you in 5 🟩       │
│ You read the AI in 9 🟩   │
│ ⚡ YOU WON THE MELD        │
└──────────────────────────┘
```

## Play it

The hosted version needs nothing at all: **https://mindmeld-017.pages.dev**

To run it yourself you need Python 3.10 or later. Nothing else.

```sh
git clone <this repo>
cd mindmeld
./bin/mindmeld         # terminal version — today's duel
./bin/mindmeld --free  # unlimited practice rounds
python3 -m game.web    # browser version -> http://127.0.0.1:8137
```

To let others on your network play, run `python3 -m game.web --host=0.0.0.0`
and share `http://<your-ip>:8137`.

The trained model ships with the repo as `ckpt/brain.fp16.pt`. For the genie to
speak in its learned voice, install PyTorch with `pip install torch`. Without
PyTorch the game plays exactly the same — the genie uses its hand-written script
instead, and prints one line telling you why.

## The game

**Round 1 — the genie reads you.** Think of an animal, object, food, famous
person or character. Answer yes, no or maybe, and watch its confidence climb.
It knows 386 things and asks from 125 hand-written attributes, choosing
whichever question splits the remaining candidates most evenly. It wins **94.8%**
of the time, with a median of 10 questions.

**Round 2 — you read the genie.** It hides something and you interrogate it in
plain text. It answers truthfully, with one exception it declares up front: *"I
may lie exactly once. Catch it if you can."* Wrong guesses come back with a
hot-or-cold reading based on how many attributes your guess shares with the
answer. Beat the genie's question count and you win the meld.

**Stump it and it learns.** If the genie fails to guess you, it asks what you
were thinking of and adds it to what it knows. In the browser build that stays
on your device.

Ranks, achievements, and a 10-question hard mode (`--hard`, or the HARD MODE
button) keep score across sessions.

## The static build

The whole game also ships as a static site in `static_site/` — no server, no
Python, no install. Open `static_site/index.html` by double-clicking it, or
deploy the folder to any static host and share the link.

- **The engine is ported to JavaScript** (`static_site/game.js`) and proven to
  behave identically to the Python original: same self-play accuracy (94.8%,
  median 10 questions) and the same daily secret on every date tested.
  `tests/test_static_engine.js` checks this under node.
- **The genie's voice is baked in at build time.** `scripts/build_voice.py` runs
  the trained model, filters what comes out, and writes the surviving lines into
  `data.js`. 35 lines ship, including the yes, no and maybe answers the previous
  model could not voice at all. Anything the filter rejects falls back to the
  hand-written script.
- **Learning is per-player.** Anything you teach the genie lives in your
  browser's local storage and never reaches anyone else's game.
- **One feature is desktop-only:** the live hunch, where the model guesses
  alongside the engine. It needs the model running, so it can't be pre-baked.
- After changing the knowledge base, run `python3 scripts/export_kb.py` to
  regenerate `data.js`.

## Architecture

Two layers, each doing what it's good at.

| Layer | What it does | Numbers |
|---|---|---|
| **Knowledge engine** (`game/`) | 386 entities × 125 hand-written attributes. Picks each question by expected information gain, and answers from ground truth so it can never contradict itself. | 94.8% self-play, median 10 questions |
| **Trained model** (`newton/`) | Supplies the genie's voice, and nothing else. It never touches facts, questions or game state. | 26.8M parameters, final loss 0.093 |

The engine is the spine. The model is the personality, and only the personality.

Everything the model produces passes a filter before it can be spoken: length,
character set, must end in sentence punctuation, must not leak facts about the
answer, and every word must be one the model was trained on. Anything that fails
falls back to the hand-written script, so a bad generation can't break a game.
Force script-only with `./bin/mindmeld --no-brain-voice`.

## The brain

- A tokenizer built from scratch — byte-level BPE, 1,500 tokens. It learns which
  character sequences are worth treating as single units, starting from raw bytes
  rather than a word list.
- An 8-layer, 8-head, 512-wide GPT — **26.8M parameters**. Pure PyTorch, CPU only.
- Trained **29,819 steps across three CPU runs** — two of two hours, one of four,
  each resuming from the last. Loss fell from 6.4 to **0.093**.
- Ships as `ckpt/brain.fp16.pt` (53.6MB). Stored at half precision to halve the
  file size, and checked to produce byte-identical output to the full-precision
  training checkpoint.
- Corpus: 7,996 documents, 5.3MB — simulated game transcripts, entity fact
  sheets, Round 2 question-and-answer pairs, personality lines and share cards,
  all generated by `scripts/gen_corpus.py`.

### What it actually learned

It learned the script. Extremely well, and a deliberate attempt to stop it changed
nothing.

The first audit found **20 of the 21 baked lines byte-identical to lines it was
trained on.** The 21st was a truncation of the 20th. It wrote nothing of its own.

The suspected cause was the corpus. It held 65 authored personality lines repeated
ten times each, which is a short list to memorise rather than a pattern to learn.
So the repeats dropped from ten to three, and `scripts/expand_voice.py` added
thousands of recombinations built only from fragments of those same 65 lines —
the same voice, many more surface forms. Training resumed for another 15,387 steps.

**It made no difference. 33 of the 35 baked lines are still byte-identical to the
script** — 94%, against 95% before. The two exceptions are truncations of authored
lines, not new sentences. Coverage did improve: the yes, no and maybe answers, which
the old model could not voice at all, now bake 3, 3 and 2 lines. More of the script
comes back. None of it is invented.

That is what memorisation looks like at this size. A 26.8M-parameter model — about
a fifth of GPT-2 "small" — trained on 5.3MB of text reconstructs its training data
rather than generalising from it, and feeding it recombinations of that same data
does not change the outcome. The final loss of 0.093 is the signature.

It did pick up structure beyond the exact strings: game formats, entity names, and
rough semantic profiles. Asked to guess from *"fictional, villain, from space
adventures"* it answered **Superman** — wrong, but four of five traits right, which
is the kind of near-miss a person makes.

```sh
python3 -m newton.train --max-steps=30000 --batch-size=16 --time-budget=7200 \
    --embd=512 --layers=8 --heads=8        # train further, resumes from checkpoint
python3 -m newton.export                   # re-export the half-precision model
python3 -m newton.generate "GENIE (ai wins): "   # sample it directly
```

## Design decisions

- **One daily secret, the same for everyone**, so players can compare results.
- **A share card built from emoji**, so a result can be pasted anywhere.
- **Streaks**, kept locally.
- **Three-minute rounds, no install, no signup.** Every step between hearing
  about the game and playing it loses people.
- **The genie's wrong guesses are funnier than its right ones**, which is why it
  guesses out loud rather than silently narrowing down.

## Tests

```sh
python3 -m unittest discover -s tests   # 65 tests
node tests/test_static_engine.js        # 29 assertions, Python/JS parity
```

What the tests enforce: every entity answers all 120 attributes and every
attribute has questions; self-play accuracy stays at or above 90%; median
question count stays reasonable; the tokenizer round-trips text unchanged
including unicode; model shapes are correct; answer parsing and guess matching
behave; and the JavaScript engine matches the Python one on self-play and on
daily secrets.

## Layout

```
newton/    the model: tokenizer.py, model.py, train.py, generate.py, export.py
game/      the game: kb.py, engine.py, questions.py, personality.py, learn.py,
           voice.py, tui.py, web.py, profile.py, static/index.html
static_site/  the no-server build: index.html, game.js, data.js
scripts/   gen_corpus.py, build_voice.py, export_kb.py
tests/     test_engine.py, test_brain.py, test_learn.py, test_progression.py,
           test_v14.py, test_static_engine.js
ckpt/      brain.fp16.pt (shipped), tokenizer.json — training artifacts and
           logs are gitignored
data/      created when you play (profile.json)
bin/       mindmeld
DEVLOG.md  project journal: what changed, why, and the bugs that mattered
```

## License

AGPL-3.0-only. See `LICENSE` and `NOTICE` — the dual-licensing terms cover the
code, the knowledge base and the trained weights.
