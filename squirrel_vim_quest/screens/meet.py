"""Meet: for each new key, show it, let a ghost Pip act it out, then "Now you!".

The child presses the key 3 times to go on. There is no way to fail.
On Arrow Island Pip stands on grass; on Word River on a line of words.
A "bonus" level is a Meet followed straight away by a puzzle.
"""

from __future__ import annotations

from rich.text import Text

from ..engine.grid import Grid
from ..engine.text import word_spans
from ..sprites import big_key, key_cap, keyboard, side_by_side
from ..strings import t
from .base import GameScreen
from .board import GridBoard, TextBoard

SIZE = 7
PRESSES = 3
DEMO_STEP = 0.6  # seconds per ghost move
MEET_TEXT = "cat sun big dog red hat"


class MeetScreen(GameScreen):
    def start(self) -> None:
        if self.level.text or self.level.settings.get("meet_text"):
            line = self.level.settings.get("meet_text", MEET_TEXT)
            self.board = TextBoard([line], self.level.settings.get("theme", "river"))
        else:
            self.board = GridBoard(Grid(["." * SIZE] * SIZE))
        self.index = 0
        self.begin_key()

    @property
    def key(self) -> str:
        return self.level.teach[self.index]

    def start_cell(self, key: str):
        """Where Pip stands to show a key: room for 3 presses that way."""
        if isinstance(self.board, GridBoard):
            return (SIZE // 2, SIZE // 2)
        spans = word_spans(self.board.lines)
        if key == "0":
            r, _, last = spans[-1]
            return (r, last)
        r, first, _ = spans[-1] if key == "b" else spans[0]
        return (r, first)

    def begin_key(self) -> None:
        self.home = self.board.start(self.start_cell(self.key))
        self.state = self.home
        self.ghost = None
        self.presses = 0
        self.phase = "demo"
        self.say(f"go_{self.key}")
        away = self.board.step(self.home, self.key)
        # The ghost hops out and back twice, then it's the child's turn.
        self.after(DEMO_STEP * 1, lambda: self._ghost_at(away))
        self.after(DEMO_STEP * 2, lambda: self._ghost_at(None))
        self.after(DEMO_STEP * 3, lambda: self._ghost_at(away))
        self.after(DEMO_STEP * 4, lambda: self._ghost_at(None))
        self.after(DEMO_STEP * 4.5, self._your_turn)

    def _ghost_at(self, state) -> None:
        self.ghost = state
        if state:
            self.audio.play("hop")

    def _your_turn(self) -> None:
        self.phase = "try"
        self.say("now_you")

    def on_motion(self, key: str) -> None:
        if self.phase != "try":
            return
        if key != self.key:
            self.shake()
            self.audio.play("wrong")
            self.say("try_key", key=self.key)
            return
        self.state = self.board.step(self.state, key)
        self.presses += 1
        self.audio.play("hop")
        if self.presses == PRESSES:
            self.phase = "done"
            self.audio.play("star")
            self.say("yes")
            self.after(1.4, self._next_key)
        elif self.board.step(self.state, key) == self.state:
            # 0 and $ go all the way at once: hop back so the next press moves again.
            self.phase = "back"
            self.after(0.6, self._hop_home)

    def _hop_home(self) -> None:
        self.state = self.home
        self.phase = "try"

    def _next_key(self) -> None:
        self.index += 1
        if self.index < len(self.level.teach):
            self.begin_key()
        elif self.level.kind == "bonus":
            from .puzzle import PuzzleScreen

            self.finished = True
            self.app.switch_screen(PuzzleScreen(self.level))
        else:
            self.finish(3, 0)

    def hint_key(self) -> str | None:
        return self.key

    def render_status(self) -> Text:
        return side_by_side([big_key(self.key), keyboard(self.key)], gap=4)

    def render_play(self) -> Text:
        ghost = self.board.cell(self.ghost) if self.ghost else None
        return self.board.draw({}, self.board.cell(self.state), ghost)

    def render_keybar(self) -> Text:
        done = Text("\n").join([
            Text(""),
            Text("o " * self.presses, style="bold #ffd84d") + Text("o " * (PRESSES - self.presses), style="#444444"),
            Text(""),
        ])
        label = Text("\n").join([Text(""), Text(t(f"go_{self.key}"), style="bold #ffffff"), Text("")])
        return side_by_side([key_cap(self.key), label, done], gap=3)
