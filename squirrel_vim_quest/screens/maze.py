"""Boss: Fox Maze. Eat every acorn to open the gate, then reach it. Foxes chase.

A bump sends Pip and the foxes back to their starts; eaten acorns stay eaten.
"""

from __future__ import annotations

import random

from rich.text import Text

from ..engine.motions import move, neighbours
from ..engine.solver import path_to_nearest, step_toward
from .base import GameScreen
from .field import acorn_row, draw_field

GRACE = 1.5
HURT = 0.6
READY = 1.6


def boss_stars(bumps: int) -> int:
    if bumps <= 1:
        return 3
    if bumps <= 3:
        return 2
    return 1


class MazeScreen(GameScreen):
    def start(self) -> None:
        s = self.level.settings
        self.s = s
        self.grid = self.level.grid
        self.rng = random.Random(s.get("seed"))
        self.pos = self.level.start
        self.fox_starts = list(self.level.foxes)
        self.foxes = list(self.fox_starts)
        self.acorns = set(self.level.acorns)
        self.gate = self.level.gate
        self.gate_open = False
        self.bumps = 0
        self.fox_timer = s["fox_every"]
        self.grace = 0.0
        self.hurt = 0.0
        self.phase = "ready"
        self.say("ready")
        self.after(READY, self._go)

    def _go(self) -> None:
        self.phase = "play"
        self.say("eat")

    def tick(self, dt: float) -> None:
        if self.phase != "play":
            return
        self.grace = max(0.0, self.grace - dt)
        self.hurt = max(0.0, self.hurt - dt)
        self.fox_timer -= dt
        if self.fox_timer <= 0:
            self.fox_timer = self.s["fox_every"]
            if not self.grace:
                self._move_foxes()
                self._check_bump()

    def _move_foxes(self) -> None:
        for i, fox in enumerate(self.foxes):
            others = [f for j, f in enumerate(self.foxes) if j != i] + [self.gate]
            if self.rng.random() < self.s.get("fox_wander", 0.3):
                options = [p for _, p in neighbours(self.grid, fox) if p not in others]
                if options:
                    self.foxes[i] = self.rng.choice(options)
            else:
                self.foxes[i] = step_toward(self.grid, fox, self.pos, blocked=others)

    def on_motion(self, key: str) -> None:
        if self.phase != "play":
            return
        new = move(self.grid, self.pos, key)
        if new == self.pos or (new == self.gate and not self.gate_open):
            self.audio.play("wrong")
            return
        self.pos = new
        self.audio.play("hop")
        if self.pos in self.acorns:
            self.acorns.discard(self.pos)
            self.audio.play("eat")
            if not self.acorns:
                self.gate_open = True
                self.audio.play("gate")
                self.say("gate_open")
        if self.gate_open and self.pos == self.gate:
            self._win()
            return
        self._check_bump()

    def _check_bump(self) -> None:
        if self.grace or self.pos not in self.foxes:
            return
        self.bumps += 1
        self.grace = GRACE
        self.hurt = HURT
        self.audio.play("bump")
        self.say("oops")
        self.pos = self.level.start
        self.foxes = list(self.fox_starts)

    def _win(self) -> None:
        self.phase = "done"
        self.audio.play("win")
        stars = boss_stars(self.bumps)
        self.after(0.8, lambda: self.finish(stars, len(self.level.acorns)))

    def hint_key(self) -> str | None:
        targets = self.acorns or {self.gate}
        blocked = list(self.foxes) + ([] if self.gate_open else [self.gate])
        route = path_to_nearest(self.grid, self.pos, targets, self.keys, blocked=blocked)
        return route[0] if route else None

    def render_status(self) -> Text:
        total = len(self.level.acorns)
        status = acorn_row(total - len(self.acorns), total)
        status.append("   ")
        status.append("|>>|" if self.gate_open else "|##|", style="bold #6dff8a" if self.gate_open else "#8a6e30")
        return status

    def render_play(self) -> Text:
        things = {pos: "acorn" for pos in self.acorns}
        things[self.gate] = "gate_open" if self.gate_open else "gate_closed"
        for fox in self.foxes:
            things[fox] = "fox"
        things[self.pos] = "pip_hurt" if self.hurt else "pip"
        return draw_field(self.grid, things)
