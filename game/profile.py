"""Player profile: streaks and lifetime stats, JSON-persisted in-project."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "profile.json"


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
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        for key in ("games_played", "wins", "losses", "draws", "current_streak", "best_streak", "last_daily_day"):
            if key in data:
                setattr(self, key, data[key])

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.__dict_public__(), indent=2) + "\n", encoding="utf-8")

    def __dict_public__(self) -> dict:
        return {
            "games_played": self.games_played,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "last_daily_day": self.last_daily_day,
        }

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

    def already_played_today(self) -> bool:
        return self.last_daily_day == date.today().toordinal()

    def summary(self) -> str:
        return (
            f"games {self.games_played} · wins {self.wins} · "
            f"streak {self.current_streak} (best {self.best_streak})"
        )
