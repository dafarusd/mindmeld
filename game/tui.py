"""Terminal UI for Mind Meld. Pure ANSI — no dependencies, full theater."""

from __future__ import annotations

import os
import random
import sys
import time
from datetime import date

from . import voice
from .engine import MAX_QUESTIONS, MindReader, SecretKeeper, daily_info, parse_answer, share_card
from .kb import ENTITIES
from .personality import (
    BLUFF_RULE,
    HUNCH_AGREE,
    HUNCH_LABEL,
    INTROS,
    INTROS_DAILY,
    SECRET_PICKED,
    THINKING,
    pick,
    rephrase_question,
)
from .profile import Profile
from .questions import QUESTIONS

ANSWER_WORD = {1.0: "yes", 0.0: "no", 0.5: "maybe"}

PURPLE = "\x1b[95m"
DEEP_PURPLE = "\x1b[35m"
CYAN = "\x1b[96m"
GOLD = "\x1b[93m"
GREEN = "\x1b[92m"
RED = "\x1b[91m"
DIM = "\x1b[2m"
BOLD = "\x1b[1m"
RESET = "\x1b[0m"

GENIE_IDLE = r'''
        .-~~~~-.
       / .--.  \
      | (o)(o)  |
       \  '--' /
        |  __  |
       _|      |_
      /_|      |_\
        |  ||  |
     ~~~|  ||  |~~~
   ~~   |__||__|   ~~
'''

GENIE_HAPPY = GENIE_IDLE.replace("(o)(o)", "(^)(^)")
GENIE_SHOOK = GENIE_IDLE.replace("(o)(o)", "(O)(O)").replace("'--'", ".__.")
GENIE_THINKING = GENIE_IDLE.replace("(o)(o)", "(-)(-)")


def supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


class Screen:
    def __init__(self, animate: bool = True, color: bool | None = None):
        self.animate = animate
        self.color = supports_color() if color is None else color

    def c(self, text: str, code: str) -> str:
        return f"{code}{text}{RESET}" if self.color else text

    def clear(self) -> None:
        if self.color:
            sys.stdout.write("\x1b[2J\x1b[H")
            sys.stdout.flush()

    def type_out(self, text: str, code: str = "", delay: float = 0.012) -> None:
        if self.animate and self.color:
            if code:
                sys.stdout.write(code)
            for ch in text:
                sys.stdout.write(ch)
                sys.stdout.flush()
                time.sleep(delay)
            if code:
                sys.stdout.write(RESET)
            sys.stdout.write("\n")
            sys.stdout.flush()
        else:
            print(self.c(text, code))

    def genie(self, mood: str = "idle") -> None:
        art = {"idle": GENIE_IDLE, "happy": GENIE_HAPPY, "shook": GENIE_SHOOK, "thinking": GENIE_THINKING}[mood]
        for line in art.splitlines():
            print(self.c(line, PURPLE))

    def thinking(self, rng: random.Random) -> None:
        if not (self.animate and self.color):
            return
        phrase = pick(rng, THINKING)
        sys.stdout.write(DIM + f"  ({phrase}" )
        sys.stdout.flush()
        for _ in range(3):
            time.sleep(0.22)
            sys.stdout.write(".")
            sys.stdout.flush()
        time.sleep(0.15)
        sys.stdout.write(")" + RESET + "\n\n")
        sys.stdout.flush()

    def banner(self, text: str) -> None:
        bar = "═" * (len(text) + 4)
        print(self.c(f"╔{bar}╗", GOLD))
        print(self.c(f"║  {text}  ║", GOLD + BOLD))
        print(self.c(f"╚{bar}╝", GOLD))

    def box(self, text: str, code: str = CYAN) -> None:
        lines = text.splitlines()
        width = max(len(l) for l in lines)
        print(self.c("┌" + "─" * (width + 2) + "┐", code))
        for line in lines:
            print(self.c("│ ", code) + line.ljust(width) + self.c(" │", code))
        print(self.c("└" + "─" * (width + 2) + "┘", code))


def ask_answer(scr: Screen, prompt: str) -> float | None:
    raw = input(scr.c(prompt + " ", CYAN))
    v = parse_answer(raw)
    if v is None and raw.strip().lower() in {"q", "quit", "exit"}:
        raise KeyboardInterrupt
    return v


def mist_bar(share: float, width: int = 16) -> str:
    filled = round(share * width)
    return "█" * filled + "░" * (width - filled)


def play_round_a(scr: Screen, rng: random.Random, max_questions: int = MAX_QUESTIONS) -> tuple[int | None, bool, MindReader]:
    mr = MindReader(rng=rng, max_questions=max_questions)
    scr.type_out(f"Answer with yes / no / maybe. I give you up to {max_questions} questions.", DIM)
    print()
    while True:
        attr = mr.next_question()
        if attr is None:
            while len(mr.guesses_made) < 3:
                mr.guess()
                q, won = finish_guess(scr, mr, mr.guesses_made[-1])
                if won or q is None:
                    return q, won, mr
            return len(mr.asked), False, mr
        scr.thinking(rng)
        qnum = len(mr.asked) + 1
        question = rephrase_question(rng, rng.choice(QUESTIONS[attr]))
        print(scr.c(f"Q{qnum:>2} ▸ ", GOLD) + scr.c(question, BOLD))
        try:
            value = ask_answer(scr, scr.c("    (y/n/m): ", DIM))
        except (EOFError, KeyboardInterrupt):
            return None, False, mr
        if value is None:
            print(scr.c("    (the spirits need yes, no, or maybe)", DIM))
            continue
        mr.answer(attr, value)
        share = mr.top_share()
        print(scr.c(f"    mist: {mist_bar(share)} {share*100:.0f}%", PURPLE))
        if mr.should_guess():
            guess = mr.guess()
            correct, won = finish_guess(scr, mr, guess)
            if won:
                return correct, True, mr
            if len(mr.guesses_made) >= 3:
                return len(mr.asked), False, mr


def finish_guess(scr: Screen, mr: MindReader, guess: str) -> tuple[int | None, bool]:
    print()
    scr.genie("thinking")
    scr.type_out(f"I see it forming... it's...", GOLD, delay=0.03)
    hunch_line = None
    if voice.brain_available():
        transcript = [f"Q: {QUESTIONS[attr][0]} A: {ANSWER_WORD[value]}" for attr, value in mr.answers]
        hunch_line = voice.hunch(transcript)
    time.sleep(0.4 if scr.animate else 0)
    scr.type_out(f"   ✦ {guess.upper()} ✦", PURPLE + BOLD, delay=0.04)
    if hunch_line:
        if hunch_line.lower() == guess.lower():
            scr.type_out(f"   🧠 {HUNCH_AGREE}", CYAN)
        else:
            scr.type_out(f"   🧠 {HUNCH_LABEL}: “{hunch_line}”", CYAN)
    try:
        raw = input(scr.c("Am I right? (y/n): ", CYAN))
    except (EOFError, KeyboardInterrupt):
        return None, False
    if parse_answer(raw) == 1.0:
        scr.genie("happy")
        scr.type_out(voice.banter("correct guess", mr.rng), GREEN)
        print(scr.c(f"    ({ENTITIES[guess]['blurb']})", DIM))
        return len(mr.asked), True
    scr.genie("shook")
    scr.type_out(voice.banter("wrong guess", mr.rng), RED)
    mr.confirm_guess(False)
    return len(mr.asked), False


def play_round_b(scr: Screen, rng: random.Random, secret: str, bluff: bool = True) -> tuple[int | None, bool]:
    keeper = SecretKeeper(secret=secret, rng=rng, bluff=bluff)
    scr.type_out(pick(rng, SECRET_PICKED), PURPLE)
    if bluff:
        scr.type_out(BLUFF_RULE, GOLD)
    scr.type_out("Ask me anything about a trait ('is it alive?'), or type your guess.", DIM)
    print()
    while keeper.questions_asked < MAX_QUESTIONS and not keeper.solved:
        left = MAX_QUESTIONS - keeper.questions_asked
        try:
            raw = input(scr.c(f"[{left:>2} left] you: ", CYAN))
        except (EOFError, KeyboardInterrupt):
            return None, False
        raw = raw.strip()
        if not raw:
            continue
        if raw.lower() in {"q", "quit", "exit"}:
            return None, False
        lowered = raw.lower().removeprefix("is it ").removesuffix("?").strip()
        looks_like_guess = (
            not raw.endswith("?")
            and 3 <= len(raw) <= 40
            and len(raw.split()) <= 4
            and parse_answer(raw) is None
            and not any(w in lowered for w in ("is", "are", "does", "do", "can", "would", "could", "was", "were", "did"))
        )
        if looks_like_guess or lowered in {n.lower() for n in ENTITIES}:
            correct, heat = keeper.try_guess(raw)
            if correct:
                scr.genie("shook")
                scr.type_out(f"...HOW. Yes. It was {secret}.", GREEN)
                disclosure = keeper.bluff_disclosure()
                if disclosure:
                    scr.type_out(disclosure, DIM)
                return keeper.questions_asked + 1, True
            scr.thinking(rng)
            if heat:
                scr.type_out(f"No. It is not {raw.strip()} — {heat}", RED)
            else:
                scr.type_out(f"No. It is not {raw.strip()}. (never heard of it, in fact)", RED)
            keeper.questions_asked += 1
            continue
        scr.thinking(rng)
        kind, reply = keeper.answer_question(raw)
        color = GREEN if reply == "Yes." else (RED if reply == "No." else GOLD)
        flavor = "" if kind == "unknown" else voice.banter(f"answer {kind}", rng)
        scr.type_out(f"mind meld: {reply}", color)
        if flavor:
            scr.type_out(f"           {flavor}", DIM)
    if keeper.solved:
        return keeper.questions_asked, True
    scr.genie("happy")
    scr.type_out(f"Twenty questions, gone. My secret stays mine: it was {secret.upper()}.", GOLD)
    disclosure = keeper.bluff_disclosure()
    if disclosure:
        scr.type_out(disclosure, DIM)
    return MAX_QUESTIONS, False


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    daily = "--daily" in argv or not argv
    no_anim = "--no-anim" in argv
    hard = "--hard" in argv
    if "--brain-voice" in argv:
        voice.set_enabled(True)
    if "--no-brain-voice" in argv:
        voice.set_enabled(False)
    scr = Screen(animate=not no_anim)
    rng = random.Random()
    profile = Profile()
    day = date.today().toordinal()

    scr.clear()
    scr.banner("✦  M I N D   M E L D  ✦")
    scr.genie("idle")
    print(scr.c(f"  {profile.summary()}", DIM))
    print()
    if daily and profile.already_played_today():
        scr.type_out("You have already faced today's secret. The mists reset at midnight.", DIM)
        scr.type_out("(Play anyway with --free)", DIM)
        return 0
    secret, theme = daily_info(day) if daily else (None, None)
    if daily:
        intro = pick(rng, INTROS_DAILY)
        if theme:
            intro += f" Today is {theme}."
        scr.type_out(intro, PURPLE)
    else:
        scr.type_out(pick(rng, INTROS), PURPLE)
    print()

    scr.type_out("ROUND ONE — I read YOUR mind. Think of an animal, object, person, or character.", BOLD)
    input(scr.c("Press enter when you have it...", DIM))
    ai_q, ai_won, mr = play_round_a(scr, rng, max_questions=10 if hard else MAX_QUESTIONS)
    if ai_q is None:
        print(scr.c("\nThe mist dissipates... (game abandoned)", DIM))
        return 1
    learned_new = False
    if not ai_won:
        scr.genie("shook")
        scr.type_out("You stumped me. WHAT were you thinking of?", GOLD)
        scr.type_out("(teach me, and I shall never lose to it again)", DIM)
        try:
            name = input(scr.c("it was: ", CYAN)).strip()
        except (EOFError, KeyboardInterrupt):
            name = ""
        if name:
            from . import kb as _kb
            from .learn import LearnError, learn

            try:
                clean = learn(name, mr.answers)
                _kb.reload()
                learned_new = True
                scr.type_out(f"'{clean}' — etched into my mind. Forever.", GREEN)
            except LearnError as exc:
                scr.type_out(str(exc), RED)
    if ai_won:
        scr.type_out(voice.banter("ai wins", rng), GREEN)
    else:
        scr.type_out(voice.banter("ai loses", rng), GOLD)

    print()
    scr.type_out("ROUND TWO — now YOU read MY mind.", BOLD)
    secret = secret or pick(rng, list(ENTITIES.keys()))
    you_q, you_won = play_round_b(scr, rng, secret)

    print()
    card = share_card(day % 1000, ai_q, ai_won, you_q, you_won, theme=theme if daily else None, rank=profile.rank())
    scr.box(card, GOLD)

    you_beat_it = you_won and (not ai_won or (you_q or 99) <= (ai_q or 99))
    if you_beat_it:
        scr.type_out(voice.banter("you win duel", rng), GREEN)
    elif ai_won and not you_won:
        scr.type_out(voice.banter("ai wins duel", rng), RED)

    if daily:
        profile.record_daily(day, you_beat_it)
    else:
        profile.record_freeplay(you_beat_it)
    from .profile import ACHIEVEMENTS

    newly = profile.register_game(ai_won, ai_q, you_won, you_q, hard=hard, learned_new=learned_new)
    for key in newly:
        scr.type_out(f"  🏆 achievement unlocked: {ACHIEVEMENTS[key]}", GOLD)
    print(scr.c(f"\n  {profile.summary()}", DIM))
    scr.type_out("\nShare your card. Challenge a friend. Return tomorrow.", DIM)
    return 0


if __name__ == "__main__":
    sys.exit(main())
