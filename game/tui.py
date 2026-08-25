"""Terminal UI for Mind Meld. Pure ANSI — no dependencies, full theater."""

from __future__ import annotations

import os
import random
import sys
import time
from datetime import date

from . import voice
from .engine import MAX_QUESTIONS, MindReader, SecretKeeper, daily_info, event_for_date, parse_answer, share_card
from .kb import ENTITIES
from .personality import (
    BLUFF_RULE,
    BOSS_INTRO,
    BOSS_LOSES,
    BOSS_WINS,
    GAUNTLET_LOST,
    GAUNTLET_OFFER,
    GAUNTLET_WON,
    GRUDGE_OPENERS,
    HUNCH_AGREE,
    HUNCH_LABEL,
    INTROS,
    INTROS_DAILY,
    REVENGE_SENSE,
    SECRET_PICKED,
    STREAK_TAUNTS,
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
GENIE_BOSS = GENIE_IDLE.replace("(o)(o)", "(>)(<)").replace("'--'", "'^^'")
GENIE_BOSS_THINKING = GENIE_BOSS.replace("(>)(<)", "(>)(>)")


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
        art = {"idle": GENIE_IDLE, "happy": GENIE_HAPPY, "shook": GENIE_SHOOK,
               "thinking": GENIE_THINKING, "boss": GENIE_BOSS, "boss_thinking": GENIE_BOSS_THINKING}[mood]
        color = RED if mood.startswith("boss") else PURPLE
        for line in art.splitlines():
            print(self.c(line, color))

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


def play_round_a(scr: Screen, rng: random.Random, max_questions: int = MAX_QUESTIONS, boss: bool = False, stumps: list | None = None) -> tuple[int | None, bool, MindReader]:
    mr = MindReader(rng=rng, max_questions=max_questions, boss=boss)
    stump_names = {s["name"] for s in (stumps or [])}
    revenge_said = False
    scr.type_out(f"Answer with yes / no / maybe. I give you up to {max_questions} questions.", DIM)
    print()
    while True:
        attr = mr.next_question()
        if attr is None:
            while len(mr.guesses_made) < 3:
                mr.guess()
                q, won = finish_guess(scr, mr, mr.guesses_made[-1], boss=boss)
                if won or q is None:
                    return q, won, mr
            return len(mr.asked), False, mr
        if boss:
            scr.genie("boss_thinking")
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
        print(scr.c(f"    mist: {mist_bar(share)} {share*100:.0f}%", RED if boss else PURPLE))
        if not revenge_said and stump_names and len(mr.asked) >= 3:
            if stump_names & set(mr.top_candidates(3)):
                scr.type_out(pick(rng, REVENGE_SENSE), GOLD)
                revenge_said = True
        if mr.should_guess():
            guess = mr.guess()
            correct, won = finish_guess(scr, mr, guess, boss=boss)
            if won:
                return correct, True, mr
            if len(mr.guesses_made) >= 3:
                return len(mr.asked), False, mr


def finish_guess(scr: Screen, mr: MindReader, guess: str, boss: bool = False) -> tuple[int | None, bool]:
    print()
    scr.genie("boss_thinking" if boss else "thinking")
    if scr.animate and scr.color:
        for candidate in mr.top_candidates(3):
            if candidate != guess:
                sys.stdout.write(DIM + f"   ... {candidate}?" + RESET)
                sys.stdout.flush()
                time.sleep(0.5)
                sys.stdout.write("\r" + " " * 40 + "\r")
                sys.stdout.flush()
    scr.type_out(f"I see it forming... it's...", GOLD, delay=0.03)
    hunch_line = None
    if voice.brain_available():
        transcript = [f"Q: {QUESTIONS[attr][0]} A: {ANSWER_WORD[value]}" for attr, value in mr.answers]
        hunch_line = voice.hunch(transcript)
    time.sleep(0.4 if scr.animate else 0)
    scr.type_out(f"   ✦ {guess.upper()} ✦", (RED + BOLD) if boss else (PURPLE + BOLD), delay=0.04)
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


def play_round_b(scr: Screen, rng: random.Random, secret: str, bluff: bool = True, bluff_count: int = 1, invert_first_n: int = 0) -> tuple[int | None, bool]:
    keeper = SecretKeeper(secret=secret, rng=rng, bluff=bluff, bluff_count=bluff_count, invert_first_n=invert_first_n)
    scr.type_out(pick(rng, SECRET_PICKED), PURPLE)
    if bluff:
        n = len(keeper.bluff_attrs)
        if invert_first_n:
            pass
        elif n > 1:
            scr.type_out(f"One rule: today I may lie {n} times. Catch me if you can.", GOLD)
        else:
            scr.type_out(BLUFF_RULE, GOLD)
    if invert_first_n:
        scr.type_out("And remember — Opposite Day: my first three answers are backwards.", GOLD)
    scr.type_out("Ask me anything about a trait ('is it alive?'), or type your guess.", DIM)
    print()
    while keeper.questions_asked < MAX_QUESTIONS and not keeper.solved:
        left = MAX_QUESTIONS - keeper.questions_asked
        try:
            raw = input(scr.c(f"[{left:>2} left] you: ", CYAN))
        except (EOFError, KeyboardInterrupt):
            raw = "q"
        raw = raw.strip()
        if not raw:
            continue
        if raw.lower() in {"q", "quit", "exit"}:
            scr.type_out(f"You flee the mist. Very well — the secret was {secret.upper()}.", DIM)
            disclosure = keeper.bluff_disclosure()
            if disclosure:
                scr.type_out(disclosure, DIM)
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
    boss = "--boss" in argv
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
    event = event_for_date(day) if daily else None
    if daily:
        intro = pick(rng, INTROS_DAILY)
        if theme:
            intro += f" Today is {theme}."
        if event:
            intro += " " + event["intro"]
        scr.type_out(intro, PURPLE)
    else:
        scr.type_out(pick(rng, INTROS), PURPLE)
    if profile.stumps:
        scr.type_out(pick(rng, GRUDGE_OPENERS).format(name=profile.recent_stumps(1)[0]), GOLD)
    elif profile.loss_run() >= 3:
        scr.type_out(pick(rng, STREAK_TAUNTS), GOLD)

    if profile.boss_available() and not boss and not daily:
        try:
            answer = input(scr.c("The mist senses your streak. Unleash the BOSS? (y/n): ", RED)).strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = ""
        if answer.startswith("y"):
            boss = True
    if boss:
        scr.genie("boss")
        scr.type_out(pick(rng, BOSS_INTRO), RED)
    print()

    scr.type_out("ROUND ONE — I read YOUR mind. Think of an animal, object, person, or character.", BOLD)
    input(scr.c("Press enter when you have it...", DIM))
    max_q = 9 if boss else (10 if hard else MAX_QUESTIONS)
    ai_q, ai_won, mr = play_round_a(scr, rng, max_questions=max_q, boss=boss, stumps=profile.stumps)
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
                profile.remember_stump(clean)
                scr.type_out(f"'{clean}' — etched into my mind. Forever.", GREEN)
            except LearnError as exc:
                scr.type_out(str(exc), RED)

    gauntlet_won = False
    if ai_won and daily and not boss:
        scr.type_out(voice.banter("ai wins", rng), GREEN)
        print()
        scr.type_out(pick(rng, GAUNTLET_OFFER), RED)
        try:
            answer = input(scr.c("accept the gauntlet? (y/n): ", GOLD)).strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = ""
        if answer.startswith("y"):
            scr.type_out("Think of something NEW. Five questions. No more.", DIM)
            input(scr.c("press enter...", DIM))
            g_q, g_won, _ = play_round_a(scr, rng, max_questions=5, boss=True)
            if g_q is None:
                print(scr.c("\nThe mist dissipates... (game abandoned)", DIM))
                return 1
            if g_won:
                scr.type_out(pick(rng, GAUNTLET_WON), RED)
            else:
                gauntlet_won = True
                scr.type_out(pick(rng, GAUNTLET_LOST), GREEN)
    elif ai_won:
        scr.type_out(voice.banter("ai wins", rng), GREEN)
    else:
        scr.type_out(voice.banter("ai loses", rng), GOLD)

    print()
    scr.type_out("ROUND TWO — now YOU read MY mind.", BOLD)
    secret = secret or pick(rng, list(ENTITIES.keys()))
    bluff_count = event.get("bluff_count", 1) if event else 1
    invert_n = event.get("invert_first_n", 0) if event else 0
    you_q, you_won = play_round_b(scr, rng, secret, bluff_count=bluff_count, invert_first_n=invert_n)

    if boss:
        if ai_won:
            scr.type_out(pick(rng, BOSS_WINS), RED)
        else:
            scr.type_out(pick(rng, BOSS_LOSES), GOLD)

    print()
    card = share_card(day % 1000, ai_q, ai_won, you_q, you_won, theme=theme if daily else None, rank=profile.rank())
    scr.box(card, GOLD)

    you_beat_it = you_won and (not ai_won or (you_q or 99) <= (ai_q or 99))
    if you_beat_it:
        scr.type_out(voice.banter("you win duel", rng), GREEN)
    elif ai_won and not you_won:
        scr.type_out(voice.banter("ai wins duel", rng), RED)

    profile.push_result(ai_won)
    if daily:
        profile.record_daily(day, you_beat_it)
        if you_beat_it and gauntlet_won:
            profile.bonus_streak()
            scr.type_out("Gauntlet survived — today's streak counts DOUBLE.", GOLD)
    else:
        profile.record_freeplay(you_beat_it)
    from .profile import ACHIEVEMENTS

    newly = profile.register_game(ai_won, ai_q, you_won, you_q, hard=hard, learned_new=learned_new, boss=boss)
    for key in newly:
        scr.type_out(f"  🏆 achievement unlocked: {ACHIEVEMENTS[key]}", GOLD)
    print(scr.c(f"\n  {profile.summary()}", DIM))
    scr.type_out("\nShare your card. Challenge a friend. Return tomorrow.", DIM)
    return 0


if __name__ == "__main__":
    sys.exit(main())
