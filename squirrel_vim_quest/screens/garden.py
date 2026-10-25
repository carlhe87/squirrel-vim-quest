"""Action: Acorn Garden. Acorns pop up and vanish; a slow snail wanders.

Spawns get faster and acorns live shorter as the timer runs down. 5 good moves
in a row make Pip glow, and a glowing Pip scores 2 per acorn until a bump.
"""

from __future__ import annotations

import random

from rich.text import Text

from ..engine.motions import move, neighbours
from ..engine.solver import path_to_nearest, step_toward
from .base import GameScreen
from .field import draw_field

COMBO = 5
GRACE = 1.5  # seconds the snail waits after a bump
HURT = 0.6  # seconds Pip looks hurt after a bump
READY = 1.6


def action_stars(eaten: int, vanished: int, bumps: int) -> int:
    seen = eaten + vanished
    if vanished == 0 and bumps <= 1:
        return 3
    if seen == 0 or eaten >= 0.7 * seen:
        return 2
    return 1


def lerp(a: float, b: float, x: float) -> float:
    return a + (b - a) * min(1.0, max(0.0, x))


class GardenScreen(GameScreen):
    def start(self) -> None:
        s = self.level.settings
        self.s = s
        self.grid = self.level.grid
        self.rng = random.Random(s.get("seed"))
        self.duration = float(s["duration"])
        self.time_left = self.duration
        self.pos = self.prev = self.level.start
        self.snail_start = self.level.snails[0]
        self.snail = self.snail_start
        self.acorns: dict = {}  # pos -> seconds left
        self.spawn_timer = 0.8
        self.snail_timer = s["snail_every"]
        self.grace = 0.0
        self.hurt = 0.0
        self.eaten = self.vanished = self.bumps = 0
        self.combo = 0
        self.points = 0
        self.phase = "ready"
        self.say("ready")
        self.after(READY, self._go)

    def _go(self) -> None:
        self.phase = "play"
        self.say("eat")

    @property
    def glowing(self) -> bool:
        return self.combo >= COMBO

    @property
    def progress(self) -> float:
        return 1 - self.time_left / self.duration

    # -- game loop -----------------------------------------------------

    def tick(self, dt: float) -> None:
        if self.phase != "play":
            return
        self.time_left -= dt
        self.grace = max(0.0, self.grace - dt)
        self.hurt = max(0.0, self.hurt - dt)

        for pos in list(self.acorns):
            self.acorns[pos] -= dt
            if self.acorns[pos] <= 0:
                del self.acorns[pos]
                self.vanished += 1

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self._spawn()
            self.spawn_timer = lerp(self.s["spawn_start"], self.s["spawn_end"], self.progress)

        self.snail_timer -= dt
        if self.snail_timer <= 0:
            self.snail_timer = self.s["snail_every"]
            if not self.grace:
                self._move_snail()
                self._check_bump()

        if self.time_left <= 0:
            self._end()

    def _spawn(self) -> None:
        busy = {self.pos, self.snail, *self.acorns}
        far = [
            p for p in self.grid.open_cells()
            if p not in busy and abs(p[0] - self.pos[0]) + abs(p[1] - self.pos[1]) >= 2
        ]
        if far:
            self.acorns[self.rng.choice(far)] = lerp(self.s["life_start"], self.s["life_end"], self.progress)

    def _move_snail(self) -> None:
        if self.rng.random() < self.s.get("snail_wander", 0.4):
            options = [p for _, p in neighbours(self.grid, self.snail)]
            if options:
                self.snail = self.rng.choice(options)
        else:
            self.snail = step_toward(self.grid, self.snail, self.pos)

    def on_motion(self, key: str) -> None:
        if self.phase != "play":
            return
        new = move(self.grid, self.pos, key)
        if new == self.pos:
            self.combo = 0
            self.audio.play("wrong")
            return
        self.prev, self.pos = self.pos, new
        self.combo += 1
        if self.pos in self.acorns:
            del self.acorns[self.pos]
            self.eaten += 1
            self.points += 2 if self.glowing else 1
            self.audio.play("eat")
        else:
            self.audio.play("hop")
        self._check_bump()

    def _check_bump(self) -> None:
        if self.snail != self.pos or self.grace:
            return
        self.bumps += 1
        self.combo = 0
        self.grace = GRACE
        self.hurt = HURT
        self.audio.play("bump")
        self.say("oops")
        # Pip is pushed back a step; the snail goes home.
        if self.prev != self.pos and self.grid.is_open(self.prev):
            self.pos = self.prev
        if self.snail_start != self.pos:
            self.snail = self.snail_start

    def _end(self) -> None:
        self.phase = "done"
        stars = action_stars(self.eaten, self.vanished, self.bumps)
        self.audio.play("win")
        self.after(0.8, lambda: self.finish(stars, self.points))

    def hint_key(self) -> str | None:
        route = path_to_nearest(self.grid, self.pos, self.acorns, self.keys, blocked=[self.snail])
        return route[0] if route else None

    # -- drawing -------------------------------------------------------

    def render_status(self) -> Text:
        slots = 24
        left = round(slots * max(0.0, self.time_left) / self.duration)
        bar = Text("[", style="#888888")
        bar.append("=" * left, style="bold #4dd96b" if left > slots // 4 else "bold #ff8c1a")
        bar.append(" " * (slots - left))
        bar.append("]", style="#888888")
        bar.append(f"   (=) x {self.points}", style="bold #e8b84a")
        if self.glowing:
            bar.append("   x2", style="bold #ffe066")
        return bar

    def render_play(self) -> Text:
        things = {}
        for pos, life in self.acorns.items():
            things[pos] = "acorn_fading" if life < 1.5 else "acorn"
        things[self.snail] = "snail"
        if self.hurt:
            things[self.pos] = "pip_hurt"
        else:
            things[self.pos] = "pip_glow" if self.glowing else "pip"
        return draw_field(self.grid, things)
