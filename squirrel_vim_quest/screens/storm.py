"""Boss: Storm Bridge. Acorns pop up anywhere on four bridges; eat enough to win.

Now and then the wind picks one bridge: "~ ~" marks it, then it blows. If Pip
is still on that bridge, Pip is blown back to the start (acorns stay eaten),
so Pip must hop to another bridge with j or k. Every key from all three
islands is useful here.
"""

from __future__ import annotations

import random

from rich.text import Text

from .base import GameScreen
from .board import make_board
from .field import acorn_row
from .maze import boss_stars

GRACE = 1.5
HURT = 0.6
READY = 1.6


class StormScreen(GameScreen):
    def start(self) -> None:
        s = self.level.settings
        self.s = s
        self.rng = random.Random(s.get("seed"))
        self.board = make_board(self.level)
        self.letters = self.board.letters()
        self.home = self.board.start(self.level.start)
        self.state = self.home
        self.goal = s["goal"]
        self.acorns: dict = {}  # cell -> seconds left
        self.spawn_timer = 0.5
        self.gust: dict | None = None  # {"row", "phase": warn|blow, "t"}
        self.gust_timer = s["gust_every"]
        self.eaten = self.bumps = 0
        self.grace = self.hurt = 0.0
        self.phase = "ready"
        self.say("ready")
        self.after(READY, self._go)

    def _go(self) -> None:
        self.phase = "play"
        self.say("eat")

    @property
    def pip(self):
        return self.board.cell(self.state)

    def tick(self, dt: float) -> None:
        if self.phase != "play":
            return
        self.grace = max(0.0, self.grace - dt)
        self.hurt = max(0.0, self.hurt - dt)

        for cell in list(self.acorns):
            self.acorns[cell] -= dt
            if self.acorns[cell] <= 0:
                del self.acorns[cell]
        self.spawn_timer -= dt
        if self.spawn_timer <= 0 and len(self.acorns) < self.s["max_acorns"]:
            self.spawn_timer = self.s["spawn_every"]
            self._spawn()

        if self.gust is None:
            self.gust_timer -= dt
            if self.gust_timer <= 0:
                self.gust_timer = self.s["gust_every"]
                # Usually Pip's own bridge, so the child must move.
                row = self.pip[0] if self.rng.random() < 0.7 else self.rng.randrange(len(self.board.lines))
                self.gust = {"row": row, "phase": "warn", "t": self.s["gust_warn"]}
                self.say("wind")
        else:
            self.gust["t"] -= dt
            if self.gust["t"] <= 0:
                if self.gust["phase"] == "warn":
                    self.gust.update(phase="blow", t=self.s["gust_blow"])
                else:
                    self.gust = None
        self._check_wind()

    def _spawn(self) -> None:
        options = [c for c in self.letters if c != self.pip and c not in self.acorns]
        if options:
            self.acorns[self.rng.choice(options)] = self.s["acorn_life"]

    def _check_wind(self) -> None:
        if self.gust and self.gust["phase"] == "blow" and not self.grace and self.pip[0] == self.gust["row"]:
            self.bumps += 1
            self.grace = GRACE
            self.hurt = HURT
            self.audio.play("bump")
            self.state = self.home

    def on_motion(self, key: str) -> None:
        if self.phase != "play":
            return
        new = self.board.step(self.state, key)
        if new == self.state:
            self.audio.play("wrong")
            return
        self.state = new
        if self.pip in self.acorns:
            del self.acorns[self.pip]
            self.eaten += 1
            self.audio.play("eat")
            if self.eaten >= self.goal:
                self._win()
                return
        else:
            self.audio.play("hop")
        self._check_wind()

    def _win(self) -> None:
        self.phase = "done"
        self.audio.play("win")
        stars = boss_stars(self.bumps)
        self.after(0.8, lambda: self.finish(stars, self.eaten))

    def hint_key(self) -> str | None:
        if self.gust and self.pip[0] == self.gust["row"]:
            # Get off the windy bridge first.
            safe = [c for c in self.letters if c[0] != self.gust["row"]]
            route = self.board.route(self.state, safe, self.keys)
        else:
            windy = [c for c in self.letters if self.gust and c[0] == self.gust["row"]]
            route = self.board.route(self.state, self.acorns, self.keys, blocked=windy)
        return route[0] if route else None

    def render_status(self) -> Text:
        return acorn_row(self.eaten, self.goal)

    def render_play(self) -> Text:
        items = {}
        if self.gust:
            row = self.gust["row"]
            marker = "wind_warn" if self.gust["phase"] == "warn" else "wind"
            for c in range(max(len(line) for line in self.board.lines)):
                items[(row, c)] = marker
        for cell in self.acorns:
            items[cell] = "acorn"
        return self.board.draw(items, self.pip, pip_sprite="pip_hurt" if self.hurt else "pip")
