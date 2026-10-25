"""Title: big Pip, the one-line story, Enter to start."""

from __future__ import annotations

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

from ..sprites import BACKGROUND, center_stack, pip_art
from ..strings import t


class TitleScreen(Screen):
    DEFAULT_CSS = f"""
    TitleScreen {{
        align: center middle;
        background: {BACKGROUND};
    }}
    TitleScreen > Static {{ width: auto; height: auto; }}
    """

    def __init__(self) -> None:
        super().__init__()
        self._blink = True

    def compose(self) -> ComposeResult:
        yield Static(id="title")

    def on_mount(self) -> None:
        self.redraw()
        self.set_interval(0.6, self._toggle)
        self.set_timer(0.4, lambda: self.app.audio.say(t("story")))

    def _toggle(self) -> None:
        self._blink = not self._blink
        self.redraw()

    def redraw(self) -> None:
        title = Text(t("title").upper(), style="bold #ffd84d")
        story = Text(t("story"), style="#dddddd")
        enter = Text(f"[ {t('press_enter')} ]", style="bold #4dd96b" if self._blink else "#2a6a3a")
        lines = [pip_art(), Text(""), title, Text(""), story, Text(""), enter]
        self.query_one("#title", Static).update(center_stack(lines))

    def on_key(self, event: events.Key) -> None:
        event.stop()
        if event.key == "enter":
            from .map import MapScreen

            self.app.switch_screen(MapScreen())
        elif event.key == "space":
            self.app.audio.repeat()
