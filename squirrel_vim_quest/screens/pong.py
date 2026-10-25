"""Action: Ping-Pong. A ball rolls from the middle of a bridge toward one end.

Pip catches it by standing on that end when it arrives: 0 for the start, $ for
the end, j and k to change bridge. After $, j keeps Pip at the end of the next
bridge, just like Vim. The balls roll faster as the timer runs down.
"""

from __future__ import annotations

import random

from rich.text import Text

from .base import GameScreen
from .board import make_board
from .garden import lerp

READY = 1.6


def pong_stars(caught: int, missed: int) -> int:
    if missed <= 1:
        return 3
    if caught >= 0.7 * (caught + missed):
        return 2
    return 1


class PongScreen(GameScreen):
    def start(self) -> None:
        s = self.level.settings
        self.s = s
        self.rng = random.Random(s.get("seed"))
        self.board = make_board(self.level)
        self.state = self.board.start(self.level.start)
        self.duration = float(s["duration"])
        self.time_left = self.duration
        self.ball: dict | None = None  # {"row", "x", "dir", "speed"}
        self.wait = 0.6
        self.caught = self.missed = 0
        self.phase = "ready"
        self.say("ready")
        self.after(READY, self._go)

    def _go(self) -> None:
        self.phase = "play"
        self.say("catch")

    @property
    def progress(self) -> float:
        return 1 - self.time_left / self.duration

    def _goal(self) -> tuple[int, int]:
        row = self.ball["row"]
        return (row, 0 if self.ball["dir"] < 0 else len(self.board.lines[row]) - 1)

    def tick(self, dt: float) -> None:
        if self.phase != "play":
            return
        self.time_left -= dt
        if self.ball is None:
            self.wait -= dt
            if self.wait <= 0:
                self._serve()
        else:
            self.ball["x"] += self.ball["dir"] * self.ball["speed"] * dt
            goal = self._goal()
            if (self.ball["dir"] < 0 and self.ball["x"] <= goal[1]) or (self.ball["dir"] > 0 and self.ball["x"] >= goal[1]):
                self._arrive(goal)
        if self.time_left <= 0:
            self._end()

    def _serve(self) -> None:
        row = self.rng.randrange(len(self.board.lines))
        length = len(self.board.lines[row])
        travel = lerp(self.s["travel_start"], self.s["travel_end"], self.progress)
        self.ball = {"row": row, "x": float(length // 2), "dir": self.rng.choice((-1, 1)), "speed": (length / 2) / travel}

    def _arrive(self, goal) -> None:
        if self.board.cell(self.state) == goal:
            self.caught += 1
            self.audio.play("eat")
        else:
            self.missed += 1
            self.audio.play("bump")
        self.ball = None
        self.wait = self.s.get("gap", 0.8)

    def on_motion(self, key: str) -> None:
        if self.phase != "play":
            return
        new = self.board.step(self.state, key)
        if new == self.state:
            self.audio.play("wrong")
            return
        self.state = new
        self.audio.play("hop")

    def _end(self) -> None:
        self.phase = "done"
        self.audio.play("win")
        stars = pong_stars(self.caught, self.missed)
        self.after(0.8, lambda: self.finish(stars, self.caught))

    def hint_key(self) -> str | None:
        if not self.ball:
            return None
        route = self.board.route(self.state, [self._goal()], self.keys)
        return route[0] if route else None

    def render_status(self) -> Text:
        slots = 24
        left = round(slots * max(0.0, self.time_left) / self.duration)
        bar = Text("[", style="#888888")
        bar.append("=" * left, style="bold #4dd96b" if left > slots // 4 else "bold #ff8c1a")
        bar.append(" " * (slots - left))
        bar.append("]", style="#888888")
        bar.append(f"   () x {self.caught}", style="bold #ffffff")
        if self.missed:
            bar.append("   " + "x" * min(self.missed, 10), style="bold #ff5c5c")
        return bar

    def render_play(self) -> Text:
        items = {}
        if self.ball:
            goal = self._goal()
            items[goal] = "goal"
            items[(self.ball["row"], round(self.ball["x"]))] = "ball"
        return self.board.draw(items, self.board.cell(self.state))
