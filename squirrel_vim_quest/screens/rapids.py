"""Boss: Fish Rapids. Three lines of words; eat the acorns, then reach the flag.

Fish jump at logs near Pip: "!!" marks where, then they splash. A splash on
Pip sends Pip back to the start (acorns stay eaten). Gold acorns sit on log
ends, which only e reaches; all of them are needed for 3 stars.
"""

from __future__ import annotations

import random

from rich.text import Text

from .base import GameScreen
from .board import TextBoard
from .field import acorn_row

GRACE = 1.5
HURT = 0.6
READY = 1.6
NEAR_COLS = 6


def rapids_stars(bumps: int, all_gold: bool) -> int:
    if all_gold and bumps <= 1:
        return 3
    if bumps <= 3:
        return 2
    return 1


class RapidsScreen(GameScreen):
    def start(self) -> None:
        s = self.level.settings
        self.s = s
        self.rng = random.Random(s.get("seed"))
        self.board = TextBoard(self.level.text)
        self.letters = self.board.letters()
        self.home = self.board.start(self.level.start)
        self.state = self.home
        self.acorns = set(self.level.acorns)
        self.gold = set(self.level.gold)
        self.flag = self.level.flag
        self.flag_open = False
        self.fish: list[dict] = []  # {"cell", "phase": warn|splash, "t"}
        self.fish_timer = s["fish_every"]
        self.bumps = 0
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

    # -- game loop -----------------------------------------------------

    def tick(self, dt: float) -> None:
        if self.phase != "play":
            return
        self.grace = max(0.0, self.grace - dt)
        self.hurt = max(0.0, self.hurt - dt)
        self.fish_timer -= dt
        if self.fish_timer <= 0:
            self.fish_timer = self.s["fish_every"]
            self._spawn_fish()
        for fish in self.fish:
            fish["t"] -= dt
            if fish["t"] <= 0 and fish["phase"] == "warn":
                fish["phase"], fish["t"] = "splash", self.s["fish_splash"]
        self.fish = [f for f in self.fish if f["t"] > 0]
        self._check_hit()

    def _spawn_fish(self) -> None:
        pr, pc = self.pip
        taken = {f["cell"] for f in self.fish} | {self.flag}
        near = [
            (r, c) for r, c in self.letters
            if abs(r - pr) <= 1 and abs(c - pc) <= NEAR_COLS and (r, c) not in taken
        ]
        if near:
            self.fish.append({"cell": self.rng.choice(near), "phase": "warn", "t": self.s["fish_warn"]})

    def _check_hit(self) -> None:
        if self.grace:
            return
        if any(f["phase"] == "splash" and f["cell"] == self.pip for f in self.fish):
            self.bumps += 1
            self.grace = GRACE
            self.hurt = HURT
            self.audio.play("bump")
            self.say("splash")
            self.state = self.home

    def on_motion(self, key: str) -> None:
        if self.phase != "play":
            return
        new = self.board.step(self.state, key)
        if new == self.state:
            self.audio.play("wrong")
            return
        self.state = new
        here = self.pip
        if here in self.acorns or here in self.gold:
            self.acorns.discard(here)
            self.gold.discard(here)
            self.audio.play("eat")
            if not self.acorns and not self.flag_open:
                self.flag_open = True
                self.audio.play("gate")
                self.say("go_flag")
        else:
            self.audio.play("hop")
        if self.flag_open and here == self.flag:
            self._win()
            return
        self._check_hit()

    def _win(self) -> None:
        self.phase = "done"
        self.audio.play("win")
        stars = rapids_stars(self.bumps, all_gold=not self.gold)
        eaten = len(self.level.acorns) + len(self.level.gold) - len(self.gold)
        self.after(0.8, lambda: self.finish(stars, eaten))

    def hint_key(self) -> str | None:
        targets = self.acorns or {self.flag}
        danger = [f["cell"] for f in self.fish]
        route = self.board.route(self.state, targets, self.keys, blocked=danger)
        return route[0] if route else None

    # -- drawing -------------------------------------------------------

    def render_status(self) -> Text:
        total = len(self.level.acorns)
        status = acorn_row(total - len(self.acorns), total)
        gold_total = len(self.level.gold)
        for i in range(gold_total):
            status.append("(*) ", style="bold #ffe066" if i < gold_total - len(self.gold) else "#555555")
        status.append("  ")
        status.append("|>", style="bold #6dff8a" if self.flag_open else "#666666")
        return status

    def render_play(self) -> Text:
        items = {pos: "acorn" for pos in self.acorns}
        items.update({pos: "gold" for pos in self.gold})
        items[self.flag] = "flag" if self.flag_open else "flag_off"
        for fish in self.fish:
            items[fish["cell"]] = "fish_warn" if fish["phase"] == "warn" else "fish"
        return self.board.draw(items, self.pip, pip_sprite="pip_hurt" if self.hurt else "pip")
