"""Mind Meld web server. Pure stdlib http.server. Local-only by default."""

from __future__ import annotations

import json
import random
import sys
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import voice
from .engine import MAX_QUESTIONS, MindReader, SecretKeeper, daily_info, share_card
from .kb import ENTITIES
from .personality import BLUFF_RULE, INTROS, INTROS_DAILY, pick
from .profile import Profile
from .questions import QUESTIONS

ANSWER_WORD = {1.0: "yes", 0.0: "no", 0.5: "maybe"}

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"


class Session:
    def __init__(self):
        self.reset("daily")

    def reset(self, mode: str):
        self.mode = mode
        self.rng = random.Random()
        self.phase = "intro"
        self.mr: MindReader | None = None
        self.keeper: SecretKeeper | None = None
        self.pending_attr: str | None = None
        self.pending_guess: str | None = None
        self.ai_q: int | None = None
        self.ai_won = False
        self.new_achievements: list[str] = []
        self.theme: str | None = None
        self.you_q: int | None = None
        self.you_won = False
        self.day = date.today().toordinal()
        secret, theme = daily_info(self.day)
        self.secret = secret if mode == "daily" else None
        self.theme = theme if mode == "daily" else None
        self.learned_new = False


SESSION = Session()


def _state(profile: Profile) -> dict:
    s = SESSION
    return {
        "phase": s.phase,
        "mode": s.mode,
        "questions_asked": len(s.mr.asked) if s.mr else 0,
        "max_questions": MAX_QUESTIONS,
        "guesses_made": len(s.mr.guesses_made) if s.mr else 0,
        "round_b_asked": s.keeper.questions_asked if s.keeper else 0,
        "ai_q": s.ai_q,
        "ai_won": s.ai_won,
        "you_q": s.you_q,
        "you_won": s.you_won,
        "share_card": share_card(s.day % 1000, s.ai_q, s.ai_won, s.you_q, s.you_won, theme=s.theme, rank=profile.rank()) if s.phase == "done" else None,
        "confidence": round(s.mr.top_share() * 100) if s.mr and s.phase == "round_a" else None,
        "bluff_disclosure": s.keeper.bluff_disclosure() if (s.keeper and s.phase == "done") else None,
        "new_achievements": getattr(s, "new_achievements", []) if s.phase == "done" else [],
        "profile": profile.summary(),
        "streak": profile.current_streak,
        "played_today": profile.already_played_today(),
    }


def handle(body: dict, profile: Profile) -> dict:
    s = SESSION
    action = body.get("action")

    if action == "new":
        mode = body.get("mode", "daily")
        if mode == "daily" and profile.already_played_today():
            mode = "free"
        s.reset(mode)
        s.phase = "round_a"
        s.mr = MindReader(rng=s.rng, max_questions=10 if mode == "hard" else MAX_QUESTIONS)
        intro = pick(s.rng, INTROS_DAILY if s.mode == "daily" else INTROS)
        attr = s.mr.next_question()
        s.pending_attr = attr
        say = intro + " But FIRST — I will read YOUR mind. Think of an animal, object, food, famous person, or character. Lock it in. Then answer my questions below."
        return {"say": say, "event": "round_a_start", "question": s.rng.choice(QUESTIONS[attr]), "state": _state(profile)}

    if action == "answer" and s.phase == "round_a" and s.mr and s.pending_guess is None:
        value = {"yes": 1.0, "no": 0.0, "maybe": 0.5}[body["answer"]]
        s.mr.answer(s.pending_attr, value)
        if s.mr.should_guess():
            s.pending_guess = s.mr.guess()
            hunch = None
            if voice.brain_available():
                transcript = [f"Q: {QUESTIONS[a][0]} A: {ANSWER_WORD[v]}" for a, v in s.mr.answers]
                hunch = voice.hunch(transcript)
            return {"event": "guess", "guess": s.pending_guess, "hunch": hunch, "state": _state(profile)}
        attr = s.mr.next_question()
        if attr is None:
            s.pending_guess = s.mr.best_candidate()
            return {"event": "guess", "guess": s.pending_guess, "hunch": None, "state": _state(profile)}
        s.pending_attr = attr
        return {"event": "question", "question": s.rng.choice(QUESTIONS[attr]), "state": _state(profile)}

    if action == "confirm" and s.phase == "round_a" and s.pending_guess:
        correct = bool(body.get("correct"))
        if correct:
            s.ai_q = len(s.mr.asked)
            s.ai_won = True
            say = voice.banter("correct guess", s.rng) + " " + voice.banter("ai wins", s.rng)
            _begin_round_b(s)
            return {"event": "round_b_start", "say": say, "blurb": ENTITIES[s.pending_guess]["blurb"], "state": _state(profile)}
        say = voice.banter("wrong guess", s.rng)
        s.mr.confirm_guess(False)
        s.pending_guess = None
        if len(s.mr.guesses_made) >= 3:
            s.ai_q = len(s.mr.asked)
            s.ai_won = False
            return {"event": "learn_prompt", "say": say + " You stumped me. WHAT were you thinking of? (teach me — or press enter to keep it secret)", "state": _state(profile)}
        attr = s.mr.next_question()
        if attr is None:
            s.pending_guess = s.mr.guess()
            return {"event": "guess", "guess": s.pending_guess, "hunch": None, "say": say, "state": _state(profile)}
        s.pending_attr = attr
        return {"event": "question", "say": say, "question": s.rng.choice(QUESTIONS[attr]), "state": _state(profile)}

    if action == "learn" and s.phase == "round_a" and s.mr is not None:
        note = "Another secret kept... for now."
        text = body.get("text", "").strip()
        if text:
            from . import kb
            from .learn import LearnError, learn

            try:
                clean = learn(text, s.mr.answers)
                kb.reload()
                s.learned_new = True
                note = f"'{clean}' — etched into my mind. Forever."
            except LearnError as exc:
                note = str(exc)
        _begin_round_b(s)
        return {"event": "round_b_start", "say": note, "state": _state(profile)}

    if action == "ask" and s.phase == "round_b" and s.keeper:
        kind, reply = s.keeper.answer_question(body["text"])
        flavor = "" if kind == "unknown" else voice.banter(f"answer {kind}", s.rng)
        done = s.keeper.questions_asked >= MAX_QUESTIONS
        if done:
            _finish(s, profile, you_won=False, you_q=MAX_QUESTIONS)
        return {"event": "answer", "reply": reply, "flavor": flavor, "kind": kind, "state": _state(profile)}

    if action == "guess" and s.phase == "round_b" and s.keeper:
        correct, heat = s.keeper.try_guess(body["text"])
        if correct:
            _finish(s, profile, you_won=True, you_q=s.keeper.questions_asked + 1)
            return {"event": "solved", "reply": f"Yes! It was {s.secret}.", "state": _state(profile)}
        s.keeper.questions_asked += 1
        done = s.keeper.questions_asked >= MAX_QUESTIONS
        if done:
            _finish(s, profile, you_won=False, you_q=MAX_QUESTIONS)
        reply = f"No. It is not {body['text']}."
        if heat:
            reply += f" — {heat}"
        else:
            reply += " (never heard of it, in fact)"
        return {"event": "wrong_guess", "reply": reply, "heat": heat, "state": _state(profile)}

    return {"event": "state", "state": _state(profile)}


def _begin_round_b(s: Session) -> None:
    s.phase = "round_b"
    s.secret = s.secret or pick(s.rng, list(ENTITIES.keys()))
    s.keeper = SecretKeeper(secret=s.secret, rng=s.rng, bluff=True)


def _finish(s: Session, profile: Profile, you_won: bool, you_q: int) -> None:
    s.phase = "done"
    s.you_won = you_won
    s.you_q = you_q
    you_beat_it = you_won and (not s.ai_won or (you_q or 99) <= (s.ai_q or 99))
    if s.mode == "daily":
        profile.record_daily(s.day, you_beat_it)
    else:
        profile.record_freeplay(you_beat_it)
    newly = profile.register_game(s.ai_won, s.ai_q, you_won, you_q,
                                  hard=(s.mode == "hard"), learned_new=s.learned_new)
    if newly:
        from .profile import ACHIEVEMENTS

        s.new_achievements = [ACHIEVEMENTS[k] for k in newly]
    else:
        s.new_achievements = []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send_json(self, obj: dict, code: int = 200):
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        from urllib.parse import urlparse

        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            html = (STATIC / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(html)
        elif path == "/api/state":
            self._send_json({"state": _state(Profile())})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path != "/api":
            self._send_json({"error": "not found"}, 404)
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send_json({"error": "bad json"}, 400)
            return
        self._send_json(handle(body, Profile()))


def main() -> None:
    port = 8137
    host = "127.0.0.1"
    for arg in sys.argv[1:]:
        if arg.startswith("--port="):
            port = int(arg.split("=")[1])
        elif arg.startswith("--host="):
            host = arg.split("=")[1]
    server = ThreadingHTTPServer((host, port), Handler)
    shown = "127.0.0.1" if host == "0.0.0.0" else host
    print(f"Mind Meld listening on http://{shown}:{port}  (Ctrl-C to stop)")
    if host == "0.0.0.0":
        print("note: bound to all interfaces — anyone on your network can play")
    server.serve_forever()


if __name__ == "__main__":
    main()
