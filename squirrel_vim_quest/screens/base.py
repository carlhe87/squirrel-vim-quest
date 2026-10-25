"""Shared frame for every play screen: status line, play area, key bar.

It owns the rules every level follows: Tab opens the menu, Space repeats the
last spoken line, arrow keys are blocked with a spoken hint, and 3 wrong keys
in a row give a hint for the next good key.
"""

from __future__ import annotations

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static

from ..sprites import ARROW_TO_KEY, BACKGROUND, key_cap, side_by_side
from ..strings import t

TICK = 0.1  # seconds per game tick


class GameScreen(Screen):
    keys = "hjkl"  # motion keys this screen accepts

    DEFAULT_CSS = f"""
    GameScreen {{
        align: center middle;
        background: {BACKGROUND};
    }}
    GameScreen > Static {{
        width: auto;
        height: auto;
    }}
    #status {{ margin-bottom: 1; }}
    #keybar {{ margin-top: 1; }}
    """

    BINDINGS = [
        Binding("tab", "pause", show=False, priority=True),
        Binding("space", "hear", show=False, priority=True),
    ]

    def __init__(self, level=None) -> None:
        super().__init__()
        self.level = level
        if level is not None:
            self.keys = level.keys
        self.wrong_streak = 0
        self._shake = 0
        self._after: list[list] = []  # [seconds left, callback]
        self.finished = False

    # -- layout --------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Static(id="status")
        yield Static(id="play")
        yield Static(id="keybar")

    def on_mount(self) -> None:
        self.start()
        self.redraw()
        self.set_interval(TICK, self._tick)

    def redraw(self) -> None:
        self.query_one("#status", Static).update(self.render_status())
        self.query_one("#play", Static).update(self.render_play())
        self.query_one("#keybar", Static).update(self.render_keybar())

    def render_status(self) -> Text:
        return Text()

    def render_play(self) -> Text:
        return Text()

    def render_keybar(self) -> Text:
        caps = [key_cap(k) for k in self.keys]
        help_text = Text("\n").join([
            Text(""),
            Text(t("hint_hear"), style="#888888"),
            Text(t("hint_menu"), style="#888888"),
        ])
        return side_by_side([*caps, help_text], gap=2)

    # -- hooks for subclasses ------------------------------------------

    def start(self) -> None:
        pass

    def tick(self, dt: float) -> None:
        pass

    def on_motion(self, key: str) -> None:
        pass

    def on_enter(self) -> None:
        pass

    def hint_key(self) -> str | None:
        return None

    @property
    def paused(self) -> bool:
        return self.app.screen is not self

    # -- helpers -------------------------------------------------------

    @property
    def audio(self):
        return self.app.audio

    def say(self, line: str, **values: str) -> None:
        self.audio.say(t(line, **values))

    def after(self, seconds: float, callback) -> None:
        """Run callback after a delay counted in game ticks (stops while paused)."""
        self._after.append([seconds, callback])

    def shake(self) -> None:
        self._shake = 4

    def finish(self, stars: int, acorns: int) -> None:
        if self.finished:
            return
        self.finished = True
        self.app.finish_level(self.level, stars, acorns)

    # -- engine --------------------------------------------------------

    def _tick(self) -> None:
        if self.paused:
            return
        play = self.query_one("#play", Static)
        if self._shake:
            self._shake -= 1
            play.styles.offset = ((1 if self._shake % 2 else -1) if self._shake else 0, 0)
        due = [item for item in self._after if item[0] <= TICK]
        self._after = [item for item in self._after if item[0] > TICK]
        for item in self._after:
            item[0] -= TICK
        for _, callback in due:
            callback()
        if self.finished:
            return
        self.tick(TICK)
        if not self.finished:
            self.redraw()

    def on_key(self, event: events.Key) -> None:
        event.stop()
        event.prevent_default()
        if event.key in ARROW_TO_KEY:
            self.wrong_streak = 0
            self.shake()
            self.audio.play("wrong")
            self.say("use_key", key=ARROW_TO_KEY[event.key])
            return
        if event.key == "enter":
            self.on_enter()
            return
        char = event.character
        if self.finished:
            return
        if char and len(char) == 1 and char in self.keys:
            self.wrong_streak = 0
            self.on_motion(char)
            if not self.finished:
                self.redraw()
        elif char and char.isprintable():
            self.wrong_key()

    def wrong_key(self) -> None:
        self.wrong_streak += 1
        self.shake()
        self.audio.play("wrong")
        if self.wrong_streak >= 3:
            self.wrong_streak = 0
            key = self.hint_key()
            if key:
                self.say("try_key", key=key)

    def action_hear(self) -> None:
        self.audio.repeat()

    def action_pause(self) -> None:
        from .pause import PauseScreen

        self.app.push_screen(PauseScreen(in_level=self.level is not None))
