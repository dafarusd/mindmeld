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

## 2026-08-25 — v1.3: the duel becomes real

User verdict on Round 2: "misleading" — the genie promised it was hiding
a secret cleverly; really it was a lookup table. Fixed by making it play:

- **Hot/cold feedback**: wrong guesses now report real engine-measured
  similarity ("🔥 BURNING — almost there" … "🥶 ice cold"). Wrong answers
  carry information now.
- **The bluff**: the genie secretly picks one attribute per game and lies
  about it if asked; discloses at the end ("I lied once — when you asked
  about…"). Announced up front: "I may lie exactly once." `--no-bluff`.
- **Answer flavor**: every yes/no/maybe wrapped in voice taunts. Gotcha
  found in testing: the model drifted off-polarity (answering "can it
  fly?" with a corrupted line from the lose category). Added a polarity
  gate — answer lines must start with the matching polarity word or fall
  back to curated. Model learns these flavors on the next retrain
  (corpus generator already updated).
- **Live confidence meter** (Round 1): the engine's top-candidate share
  as an animated bar — "the mist is gathering… 62% sure". Pure drama,
  zero new tech.
- **The Brain's Hunch**: once per Round 1 the trained GPT makes its own
  guess from the transcript (the corpus's bare-transcript format pays
  off). If it matches the engine: "the brain and the mist agree." If it's
  a near-miss or gibberish: shown in quotes as comedy. Hard-gated.
- **Stump-and-learn (the keeper feature)**: beat the AI in Round 1 and it
  asks what you were thinking — your answers become the new entity's
  attribute vector in `data/learned.json`, merged into the KB on load.
  Beat it once, never the same way twice. Guardrails: name validation,
  fuzzy dedupe, 200-cap FIFO. Verified end-to-end: learn → reload →
  engine guesses it.
  - Bug found: fuzzy entity matching substring-matched "s**tea**m deck"
    to "tea". Now requires the candidate name ≥4 chars too.
  - Bug found: exhausted-questions path only made 1 of 3 guesses, which
    also misaligned the learn prompt's input. Both guess paths now share
    the 3-guess contract.
- **Progression**: ranks (Apprentice → Mind Reader → Thought Thief →
  Mistwalker → Geniebreaker), six achievements (First Blood, Surgical,
  Stumper, On Fire, Teacher, Storm Survivor), persisted in profile.
- **Hard mode**: `--hard` / HARD MODE button — genie caps at 10 questions
  with an adjusted guess threshold. Measured: 98.8% → 92.0% accuracy.
  A real difficulty step that stays fair. Test-gated at ≥85%.
- **Themed daily pools**: Tuesday = animals, Friday = fiction, Saturday =
  food. Same date-formula determinism — every machine, same secret, same
  theme. Share card shows theme + rank.
- Content batch: 325 → **386 entities**; self-play 94.8% @ median 10q
  (gate ≥90% holds).
- Tests: 50 total, all green.

## 2026-08-25 — v1.4: "The Genie Is Real"

Second research pass (Password Game, Connections) added: difficulty-as-
content, deliberate misdirection, special-event days, progress-as-status.
User directive: lean into the AI as the star; always reveal on a loss;
the boss gets its own image.

- **Grudge memory**: profile now remembers stumps and result history.
  The genie opens with references ("I have not forgotten 'test boss
  thing'. I dream about it now."), taunts 3+ domination streaks, and
  mid-round senses revenge when your answers resemble a past stump
  ("This feels... familiar."). Taught entities get gloating credit in
  Round 2. Nobody else can do this — it only works because the genie is
  local and persistent.
- **Flickering candidates**: before each Round 1 reveal, the mist cycles
  its top-3 suspects ("... a dog? ... a cat?") then lands. Browser:
  blur-cycle animation; terminal: dim type-outs that erase.
- **Calendar event days** (deterministic, same on every machine):
  Friday the 13th → genie lies TWICE (two bluff attributes); Halloween →
  secrets drawn from monsters/villains only; April 1st → Opposite Day
  (first three Round-2 answers inverted, announced up front).
- **The Gauntlet**: after a Round-1 read, double-or-nothing — "I read
  your NEXT thought in FIVE questions. Win and today's streak counts
  double." Boss-gated engine config; bonus streak recorded exactly once.
- **Boss mode — Genie Unleashed**: unlocks at 5-win streak. 9 questions,
  aggressive guess threshold — measured 81% win rate for the genie
  (terrifying but beatable; test-gated ≥75%). New look per request:
  crimson/ember palette, slanted angry eyes, pulsing ember orb in the
  browser; a slanted-eyes `(>)(<)` ASCII variant in red for the terminal.
  Achievement: Boss Slayer.
- **Lean into the AI**: Brain's Hunch fires on every guess with an
  agreement tally; a live "🧠 the brain" panel shows real numbers from
  the training artifacts (26M params · 14.4k steps · loss 0.139 · 53.6MB
  fp16 · vocab 1500); share cards carry the home-trained footer.
- **Always reveal**: quitting Round 2 mid-game now reveals the secret
  ("You flee the mist. Very well — the secret was CHICKEN.") plus any
  bluff confession. Timeout and loss paths were audited — every hidden
  answer is always disclosed at the end.
- Bugs found by screenshot/playthrough: boss look was wiped on game start
  (genie helper now boss-aware); boss counter said "of 20" (state now
  carries the session's question cap).
- Tests: 62 total, all green.

## 2026-08-25 — v1.4.1: the boss is earned

User report: "the boss is accessible from the start." Root cause, owned:
my own screenshot test left `current_streak: 5` in the player's live
profile — the boss button was showing because of test residue, not real
wins. The save signature proved it (best_streak 0, no daily day).

- Profile surgically cleaned: test residue removed, the player's real
  record (games/wins/losses) untouched.
- `--boss` now requires the earned 5-streak like everything else;
  hidden `--force-boss` remains for development only.
- Gauntlet got its own visual identity: gold "charged" genie. Crimson is
  reserved for the earned boss — the two can no longer be confused.
- Locked-content teaser: the boss button now shows dimmed —
  "👹 ??? — win 5 straight to unleash". Visible locked content is a
  proven desire-driver, and now the gate is honest.
- Bug found by screenshot: hunch line lingered into the next question —
  now hidden on each new question.
- Tests: 65 total, all green.

## 2026-08-25 — v1.4.2: sessions and the counter

User report mid-game: "round 2 questions are going up instead of down."
Server-side countdown was correct in isolation; the real flaws were
architectural and presentational:

- **One global game session** meant a second browser tab hijacked the
  same game — counters jumping, state fighting. Each browser now gets
  its own session (`mm_session` cookie, capped at 50). Verified with two
  interleaved simulated clients: tab A's game is undisturbed by tab B.
  Side benefit: LAN play now gives each visitor their own game.
- Counter is now unambiguous in round 2: "question 5 · 16 left" — both
  numbers visible, direction obvious.
- Round-B question cap no longer inherits boss/gauntlet's smaller cap —
  round 2 is always 20 questions.
- Tests: 65 total, all green.

## 2026-08-25 — v2.0: the static build

External review argued (correctly, verified line-by-line) that the only
viral-survivable distribution is a static site — and that the three
server ties (voice inference, session state, engine) come apart cleanly.
Built it:

- **Engine ported to JavaScript** (`static_site/game.js`, ~400 lines):
  MindReader, SecretKeeper (bluff/invert/heat), daily secrets, event days,
  similarity, learning — all client-side. **Parity proven against the
  Python engine by test**: identical self-play (94.8%, median 10q) and
  identical daily secrets/labels across 9 test days
  (`tests/test_static_engine.js`, node).
  - Port bugs found by the parity test: Python epoch ordinal is 719163
    (not 719162 — off-by-one shifted every weekday), and JS `parseInt`
    truncates the 256-bit daily hash at 53 bits — fixed with BigInt, now
    byte-exact with Python.
- **Voice pre-baked**: `scripts/build_voice.py` drives the trained model
  through the runtime quality gate at build time — 128 unique lines
  shipped in `data.js`. Honest labeling: "voice pre-baked by the model."
  Found during baking: the model still recalled the stale "keeper of the
  141" intro (trained pre-rename) — filtered; also the model produced
  polarity-correct answers for banter kinds it was never trained on
  (genuine generalization from Round-B transcript format).
- **State → browser**: profile/streaks/achievements/stumps in
  localStorage; learned entities per-player (the public-write liability
  becomes a personal feature).
- **Daily pool pinned to base entities** (Python side too — learned
  entities no longer leak into the daily secret anywhere).
- **Hunch omitted on static** (live inference is the one thing that can't
  be pre-baked — it conditions on the live transcript). Documented in the
  brain panel; desktop version keeps it.
- Works from `file://` (double-click) — verified by headless Chrome
  screenshot. Async race found by screenshot: confirming a guess mid-
  flicker left mixed round-1/round-2 visuals — busy guard added.
- The Python game is untouched and still the reference implementation;
  all 65 Python tests green.
