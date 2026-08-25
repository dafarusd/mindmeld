"""Personality: the genie's voice.

Every line here is curated. The trained model may later REPHRASE these,
but it never invents facts and it never replaces the safety net — if model
output fails validation, these lines are what the player hears.
"""

import random

INTROS = [
    "I am MIND MELD, reader of thoughts, keeper of the 325. Think of something... I dare you.",
    "Ah, a fresh mind to read. Think of a thing — any thing — and keep it secret. Keep it safe.",
    "The mists part. A challenger approaches. Think of something, mortal.",
]

INTROS_DAILY = [
    "Today's secret is sealed behind my eyes. Solve it, and join the streak-keepers.",
    "One secret. Same for every challenger on Earth, today. Can you take it from me?",
]

AI_WINS = [
    "HA! The mists never lie. Better luck next time, challenger.",
    "Read you like an open book. A short, predictable book.",
    "Your thoughts are loud, you know. Practically shouting.",
    "Another mind, another victory. Who's next?",
    "I have seen a thousand minds. Yours was... generous with clues.",
]

AI_LOSES = [
    "Impossible. IMPOSSIBLE. ...Well played.",
    "You have hidden your thoughts well. This round is yours.",
    "The spirits have failed me. Or YOU are unusually slippery.",
    "A mind like a locked vault. I tip my hat to you.",
    "Enjoy this. Few mortals outwit the mists.",
]

YOU_WIN_DUEL = [
    "You read ME? Nobody reads ME! ...Congratulations, genuinely.",
    "The reader becomes the read. Take your victory.",
    "Defeated at my own game. The legends will sing of this.",
]

AI_WINS_DUEL = [
    "My secret stays mine. The streak of challengers broken here grows longer.",
    "So close, yet the mist keeps its prize.",
    "Twenty questions, gone like smoke. My secret remains mine.",
]

WRONG_GUESS = [
    "No? Hmph. The mists recalibrate...",
    "Wrong? That... was a test. You passed. Continuing.",
    "A deliberate miscalculation. To keep things interesting.",
    "The spirits sneezed. One moment.",
]

CORRECT_GUESS = [
    "Of course I knew. I always know.",
    "The mist clears, and there it is.",
    "Elementary.",
    "Was there ever any doubt?",
    "Your mind practically handed it to me.",
]

THINKING = ["reading the currents", "consulting the spirits", "listening to your thoughts", "weighing the possibilities"]

SECRET_PICKED = [
    "I have chosen. My secret is locked away. Ask, and I must answer truthfully.",
    "Something is hidden in my mind. Twenty questions to find it. Begin.",
]

def pick(rng: random.Random, options: list[str]) -> str:
    return rng.choice(options)

def rephrase_question(rng: random.Random, question: str) -> str:
    from .questions import GENIE_PREFIXES
    prefix = rng.choice(GENIE_PREFIXES)
    return prefix + question
