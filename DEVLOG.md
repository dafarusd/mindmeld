# DEVLOG — Mind Meld / newton brain

Project journal. Milestones, decisions, and the bugs that taught us
something. Newest at the bottom.

---

## 2026-08-24 — v0: game design locked

- Chosen concept: **Mind Meld** — a two-round 20-questions duel vs a genie.
  Round 1: AI reads you. Round 2: you read it. Daily secret + streaks +
  emoji share card (Wordle/Akinator viral playbook: scarcity, shareable
  result, one-more-try loop).
- Key architecture decision: **engine owns facts, model owns voice.**
  A small home-trained LLM hallucinates; a mind-reader that contradicts
  itself is dead on arrival. So the knowledge engine (entities ×
  attributes, entropy-based question picking) is the spine, and the GPT
  only speaks personality through a validation gate with curated fallback.

## 2026-08-24 — v1.0: playable terminal + browser game

- KB: 141 entities × 57 attributes. Self-play 98%, median 8 questions.
- Bugs found by scripted playthroughs: substring-guess exploit ("y" beat
  the game via "Presle**y**"); stray yes/no treated as guesses.
- Brain v1: 11M GPT, byte-BPE 1200, 2,365 steps / 20 min CPU, loss 5.0→0.25.
  Verdict: fluent in game *format*, babble in *semantics*. Voice shipped
  opt-in only.

## 2026-08-25 — v1.1: the big training + the question-visibility saga

- **KB expansion**: 141 → 325 entities, 57 → 120 attributes. Method:
  run full-KB self-play, read the misses (twin clusters: hamster/guinea
  pig, dead male musicians, car/motorcycle), add surgical discriminators
  (barks/purrs, classical-vs-pop, wheels/handheld...), repeat.
  80% → 96% → **98.8%, median 9 questions**.
- **Matrix desync bug**: performance rewrite dropped accuracy to 82% —
  `confirm_guess` penalized the dict, `answer()` re-synced from the list,
  wiping penalties. Found by measurement, fixed, now test-gated (suite
  fails below 90% self-play).
- **Brain v2**: 26M GPT (8L/8H/512E), BPE 1500, corpus 6,552 docs/4.2MB
  (engine-simulated transcripts, fact sheets, banter upsampled 10×).
  Two 2-hour CPU runs, 14,432 steps, loss 6.4 → **0.115**.
- **The one-character bug**: model looked broken until we noticed training
  data writes `GENIE (ai wins): HA!...` — with a space after the colon.
  Our prompts had no trailing space = out-of-distribution context. With
  the space: verbatim banter recall. Voice acceptance 83% → **voice on by
  default**.
- Emergent party trick: prompted "fictional villain from space
  adventures", the model guesses **Superman** — wrong, 4/5 traits right.
- **Web UI fixes** (user-reported "question not visible"): question was
  rendered but indistinguishable from narration — added "— THE GENIE
  ASKS —" label + gold-bordered question block; Round 2 Q&A promoted from
  the tiny log to the main display; fixed query-string 404 routing bug;
  no-store cache header; scroll-into-view; compact layout for short
  screens. All verified with headless-Chrome screenshots against the
  user's live server.

## 2026-08-25 — v1.2: shippable packaging

- **fp16 brain export**: 104.2MB → 53.6MB, 6/6 byte-identical voice
  outputs vs fp32 (seeded). `brain.fp16.pt` is the shipped artifact;
  `last.pt` stays a training artifact. Loader auto-prefers fp16.
- Portability: game = pure stdlib Python 3.10+; torch needed only for the
  model voice (graceful curated fallback + one-line hint if absent).
- This journal replaces runtime event logging (user's call — the diary
  is for us, not the machine).
- git repo initialized; first commit.
