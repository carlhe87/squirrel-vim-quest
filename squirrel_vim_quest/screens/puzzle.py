"""Puzzle: walk Pip to every acorn (and the flag, if there is one).

No timer; keystrokes are counted against par. Finishing slowly (1 star) makes
a ghost Pip replay the par route once, so the child sees the faster way.
Works on a grass grid or on text, through the level's board.
"""

from __future__ import annotations

from rich.text import Text

from .base import GameScreen
from .board import make_board
from .field import acorn_row

REPLAY_STEP = 0.35


def puzzle_stars(steps: int, par: int) -> int:
    if steps <= par:
        return 3
    if steps <= par + 3:
        return 2
    return 1


class PuzzleScreen(GameScreen):
    def start(self) -> None:
        self.board = make_board(self.level)
        self.home = self.board.start(self.level.start)
        self.state = self.home
        self.flag = self.level.flag
        self.acorns = set(self.level.acorns)
        self.flag_reached = False
        self.steps = 0
        self.phase = "play"
        self.ghost = None
        self.say("go_flag" if self.flag and not self.acorns else "eat")

    @property
    def targets(self) -> set:
        return self.acorns | ({self.flag} if self.flag and not self.flag_reached else set())

    def on_motion(self, key: str) -> None:
        if self.phase != "play":
            return
        self.steps += 1
        new = self.board.step(self.state, key)
        if new == self.state:
            self.audio.play("wrong")
            return
        self.state = new
        here = self.board.cell(new)
        if here in self.acorns:
            self.acorns.discard(here)
            self.audio.play("eat")
        elif here == self.flag:
            self.flag_reached = True
            self.audio.play("gate")
        else:
            self.audio.play("hop")
        if not self.targets:
            self._solved()

    def _solved(self) -> None:
        stars = puzzle_stars(self.steps, self.level.par)
        eaten = len(self.level.acorns)
        if stars > 1:
            self.phase = "done"
            self.after(0.6, lambda: self.finish(stars, eaten))
            return
        # Show the faster way once, then finish.
        self.phase = "replay"
        all_targets = set(self.level.acorns) | ({self.flag} if self.flag else set())
        route = self.board.solve(self.home, all_targets, self.keys) or []
        self.say("look_faster")
        self.ghost = self.home
        self.acorns = set(self.level.acorns)
        self.flag_reached = False
        for i, key in enumerate(route):
            self.after(1.2 + REPLAY_STEP * i, lambda k=key: self._ghost_step(k))
        self.after(1.2 + REPLAY_STEP * len(route) + 1.0, lambda: self.finish(stars, eaten))

    def _ghost_step(self, key: str) -> None:
        self.ghost = self.board.step(self.ghost, key)
        here = self.board.cell(self.ghost)
        self.acorns.discard(here)
        if here == self.flag:
            self.flag_reached = True

    def hint_key(self) -> str | None:
        route = self.board.solve(self.state, self.targets, self.keys)
        return route[0] if route else None

    def render_status(self) -> Text:
        total = len(self.level.acorns)
        status = acorn_row(total - len(self.acorns), total) if total else Text()
        if self.flag:
            status.append("|>", style="bold #6dff8a" if self.flag_reached else "#666666")
        # One mark per keystroke: green up to par, orange after.
        status.append("   ")
        par = self.level.par
        for i in range(max(self.steps, par)):
            if i < self.steps:
                status.append("|", style="bold #4dd96b" if i < par else "bold #ff8c1a")
            else:
                status.append(".", style="#3f6f3f")
        return status

    def render_play(self) -> Text:
        items = {pos: "acorn" for pos in self.acorns}
        if self.flag and not self.flag_reached:
            items[self.flag] = "flag"
        pip = None if self.phase == "replay" else self.board.cell(self.state)
        ghost = self.board.cell(self.ghost) if self.ghost else None
        return self.board.draw(items, pip, ghost)
