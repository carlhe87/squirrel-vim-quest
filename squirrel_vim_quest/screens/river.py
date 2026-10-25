"""Action: Frog River. Words are logs drifting left, one letter at a time.

Pip rides the log it stands on. Stand too long and the log sinks (it turns
blue first); drift off the left edge and Pip falls in. Both splash Pip onto a
log further on, so the game never stops. Acorns sit on log starts, where w and
b land exactly. Drift and sinking speed up as the timer runs down.
"""

from __future__ import annotations

import random

from rich.text import Text

from .base import GameScreen
from .board import TextBoard
from .garden import action_stars, lerp

GRACE = 1.2
HURT = 0.6
READY = 1.6
SAFE_COL = 3


class RiverScreen(GameScreen):
    def start(self) -> None:
        s = self.level.settings
        self.s = s
        self.rng = random.Random(s.get("seed"))
        self.view = s.get("view", 24)
        self.line = ""
        self._fill()
        self.cursor = (0, 0, 0)
        self.duration = float(s["duration"])
        self.time_left = self.duration
        self.drift_timer = s["drift_start"]
        self.spawn_timer = 1.0
        self.stand = 0.0  # seconds on the current log
        self.acorns: set = set()
        self.eaten = self.vanished = self.bumps = 0
        self.grace = self.hurt = 0.0
        self.phase = "ready"
        self.say("ready")
        self.after(READY, self._go)

    def _go(self) -> None:
        self.phase = "play"
        self.say("eat")

    @property
    def progress(self) -> float:
        return 1 - self.time_left / self.duration

    @property
    def board(self) -> TextBoard:
        return TextBoard([self.line[: self.view]])

    @property
    def sink_after(self) -> float:
        return lerp(self.s["sink_start"], self.s["sink_end"], self.progress)

    def _fill(self) -> None:
        while len(self.line) < self.view + 12:
            self.line += self.rng.choice(self.s["words"]) + " "

    def _log_at(self, col: int) -> tuple[int, int] | None:
        """(first, last) column of the log containing col, if col is on a letter."""
        visible = self.line[: self.view]
        if not (0 <= col < len(visible)) or visible[col] == " ":
            return None
        first = col
        while first > 0 and visible[first - 1] != " ":
            first -= 1
        last = col
        while last + 1 < len(visible) and visible[last + 1] != " ":
            last += 1
        return first, last

    def _log_starts(self) -> list[int]:
        visible = self.line[: self.view]
        return [c for c in range(len(visible)) if visible[c] != " " and (c == 0 or visible[c - 1] == " ")]

    # -- game loop -----------------------------------------------------

    def tick(self, dt: float) -> None:
        if self.phase != "play":
            return
        self.time_left -= dt
        self.grace = max(0.0, self.grace - dt)
        self.hurt = max(0.0, self.hurt - dt)

        self.drift_timer -= dt
        if self.drift_timer <= 0:
            self.drift_timer = lerp(self.s["drift_start"], self.s["drift_end"], self.progress)
            self._drift()

        if not self.grace:
            self.stand += dt
            if self.stand >= self.sink_after:
                self._splash(forward=True)

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = self.s["spawn_every"]
            self._spawn()

        if self.time_left <= 0:
            self._end()

    def _drift(self) -> None:
        self.line = self.line[1:]
        self._fill()
        _, c, _ = self.cursor
        self.cursor = (0, c - 1, c - 1)
        moved = set()
        for _, ac in self.acorns:
            if ac - 1 >= 0:
                moved.add((0, ac - 1))
            else:
                self.vanished += 1
        self.acorns = moved
        if c - 1 < 0:
            self._splash(forward=False)

    def _spawn(self) -> None:
        cursor_col = self.cursor[1]
        options = [c for c in self._log_starts() if c >= self.view // 2 and (0, c) not in self.acorns and c != cursor_col]
        if options:
            self.acorns.add((0, self.rng.choice(options)))

    def _splash(self, forward: bool) -> None:
        """Pip falls in (log sank, or drifted off the edge) and climbs onto a log."""
        self.bumps += 1
        self.grace = GRACE
        self.hurt = HURT
        self.stand = 0.0
        self.audio.play("bump")
        self.say("splash")
        starts = self._log_starts()
        col = self.cursor[1]
        # After a fall off the edge, land a few letters in, or Pip falls again at once.
        ahead = [c for c in starts if c > col] if forward else [c for c in starts if c >= SAFE_COL]
        target = ahead[0] if ahead else starts[0]
        self.cursor = (0, target, target)

    def on_motion(self, key: str) -> None:
        if self.phase != "play":
            return
        new = self.board.step(self.cursor, key)
        if new == self.cursor:
            self.audio.play("wrong")
            return
        if self._log_at(new[1]) != self._log_at(self.cursor[1]):
            self.stand = 0.0
        self.cursor = new
        here = (0, new[1])
        if here in self.acorns:
            self.acorns.discard(here)
            self.eaten += 1
            self.audio.play("eat")
        else:
            self.audio.play("hop")

    def _end(self) -> None:
        self.phase = "done"
        stars = action_stars(self.eaten, self.vanished, self.bumps)
        self.audio.play("win")
        self.after(0.8, lambda: self.finish(stars, self.eaten))

    def hint_key(self) -> str | None:
        route = self.board.route(self.cursor, self.acorns, self.keys)
        return route[0] if route else "w"

    # -- drawing -------------------------------------------------------

    def render_status(self) -> Text:
        slots = 24
        left = round(slots * max(0.0, self.time_left) / self.duration)
        bar = Text("[", style="#888888")
        bar.append("=" * left, style="bold #4dd96b" if left > slots // 4 else "bold #ff8c1a")
        bar.append(" " * (slots - left))
        bar.append("]", style="#888888")
        bar.append(f"   (=) x {self.eaten}", style="bold #e8b84a")
        return bar

    def render_play(self) -> Text:
        sinking = None
        log = self._log_at(self.cursor[1])
        if log and self.phase == "play" and not self.grace:
            share = self.stand / self.sink_after
            if share >= 0.5:
                cells = {(0, c) for c in range(log[0], log[1] + 1)}
                sinking = (cells, 1 if share >= 0.8 else 0)
        items = {pos: "acorn" for pos in self.acorns}
        pip = (0, self.cursor[1]) if self.cursor[1] >= 0 else None
        return self.board.draw(items, pip, pip_sprite="pip_hurt" if self.hurt else "pip", sinking=sinking)
