"""Player profile: streaks, ranks, achievements — JSON-persisted in-project."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "profile.json"

RANKS = [
    (30, "Geniebreaker"),
    (15, "Mistwalker"),
    (7, "Thought Thief"),
    (3, "Mind Reader"),
    (0, "Apprentice"),
]

ACHIEVEMENTS = {
    "first_blood": "First Blood — win your first meld",
    "surgical": "Surgical — read the AI in 6 questions or fewer",
    "stumper": "Stumper — the AI failed to read you",
    "on_fire": "On Fire — 5-day streak",
    "teacher": "Teacher — the genie learned something from you",
    "hard_winner": "Storm Survivor — win a meld on hard mode",
    "boss_slayer": "Boss Slayer — survive the Unleashed genie",
}


class Profile:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else DEFAULT_PATH
        self.games_played = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.current_streak = 0
        self.best_streak = 0
        self.last_daily_day: int | None = None
        self.achievements: list[str] = []
        self.learned_count = 0
        self.stumps: list[dict] = []
        self.last_results: list[bool] = []
        self.boss_unlocked_seen = False
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        for key in ("games_played", "wins", "losses", "draws", "current_streak", "best_streak",
                    "last_daily_day", "achievements", "learned_count", "stumps", "last_results",
                    "boss_unlocked_seen"):
            if key in data:
                setattr(self, key, data[key])

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._as_dict(), indent=2) + "\n", encoding="utf-8")

    def _as_dict(self) -> dict:
        return {
            "games_played": self.games_played,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "last_daily_day": self.last_daily_day,
            "achievements": self.achievements,
            "learned_count": self.learned_count,
            "stumps": self.stumps,
            "last_results": self.last_results,
            "boss_unlocked_seen": self.boss_unlocked_seen,
        }

    def boss_available(self) -> bool:
        return self.current_streak >= 5

    def remember_stump(self, name: str) -> None:
        from datetime import date

        self.stumps.append({"name": name, "day": date.today().toordinal()})
        self.stumps = self.stumps[-50:]
        self.learned_count += 1
        self.save()

    def recent_stumps(self, limit: int = 3) -> list[str]:
        return [s["name"] for s in self.stumps[-limit:]]

    def push_result(self, ai_won: bool) -> None:
        self.last_results.append(ai_won)
        self.last_results = self.last_results[-10:]
        self.save()

    def loss_run(self) -> int:
        n = 0
        for won in reversed(self.last_results):
            if won:
                n += 1
            else:
                break
        return n

    def rank(self) -> str:
        for threshold, name in RANKS:
            if self.wins >= threshold:
                return name
        return RANKS[-1][1]

    def _unlock(self, key: str, newly: list[str]) -> None:
        if key not in self.achievements:
            self.achievements.append(key)
            newly.append(key)

    def register_game(self, ai_won: bool, ai_q: int | None, you_won: bool, you_q: int | None, hard: bool = False, learned_new: bool = False, boss: bool = False) -> list[str]:
        """Record a finished duel. Returns newly unlocked achievement keys."""
        newly: list[str] = []
        you_beat_it = you_won and (not ai_won or (you_q or 99) <= (ai_q or 99))
        if you_beat_it:
            self._unlock("first_blood", newly)
            if hard:
                self._unlock("hard_winner", newly)
        if boss and not ai_won:
            self._unlock("boss_slayer", newly)
        if you_won and you_q is not None and you_q <= 6:
            self._unlock("surgical", newly)
        if not ai_won:
            self._unlock("stumper", newly)
        if self.current_streak >= 5:
            self._unlock("on_fire", newly)
        if learned_new:
            self._unlock("teacher", newly)
        self.save()
        return newly

    def record_daily(self, day_ordinal: int, won: bool) -> None:
        if self.last_daily_day == day_ordinal:
            return
        yesterday = day_ordinal - 1
        self.games_played += 1
        if won:
            self.wins += 1
            self.current_streak = self.current_streak + 1 if self.last_daily_day == yesterday else 1
            self.best_streak = max(self.best_streak, self.current_streak)
        else:
            self.losses += 1
            self.current_streak = 0
        self.last_daily_day = day_ordinal
        self.save()

    def record_freeplay(self, won: bool, draw: bool = False) -> None:
        self.games_played += 1
        if draw:
            self.draws += 1
        elif won:
            self.wins += 1
        else:
            self.losses += 1
        self.save()

    def bonus_streak(self) -> None:
        """Gauntlet reward: today's win counts double."""
        self.current_streak += 1
        self.best_streak = max(self.best_streak, self.current_streak)
        self.save()

    def already_played_today(self) -> bool:
        return self.last_daily_day == date.today().toordinal()

    def summary(self) -> str:
        return (
            f"rank {self.rank()} · games {self.games_played} · wins {self.wins} · "
            f"streak {self.current_streak} (best {self.best_streak}) · "
            f"achievements {len(self.achievements)}/{len(ACHIEVEMENTS)}"
        )
