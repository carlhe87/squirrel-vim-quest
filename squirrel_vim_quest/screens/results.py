"""Results: big stars and praise, Enter back to the map."""

from __future__ import annotations

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

from ..sprites import BACKGROUND, center_stack, pip_art, stars
from ..strings import t


class ResultsScreen(Screen):
    DEFAULT_CSS = f"""
    ResultsScreen {{
        align: center middle;
        background: {BACKGROUND};
    }}
    ResultsScreen > Static {{ width: auto; height: auto; }}
    """

    def __init__(self, level, stars: int, acorns: int) -> None:
        super().__init__()
        self.level = level
        self.stars = stars
        self.acorns = acorns

    def compose(self) -> ComposeResult:
        yield Static(id="results")

    def on_mount(self) -> None:
        self.app.audio.play("win" if self.stars == 3 else "star")
        self.app.audio.say(t(f"stars_{self.stars}"))
        lines = [
            pip_art(),
            Text(""),
            stars(self.stars),
            Text(""),
            Text(t(f"stars_{self.stars}"), style="bold #ffffff"),
        ]
        if self.acorns:
            lines.append(Text(f"(=) x {self.acorns}", style="bold #e8b84a"))
        lines += [Text(""), Text(f"[ {t('press_enter')} ]", style="bold #4dd96b")]
        self.query_one("#results", Static).update(center_stack(lines))

    def on_key(self, event: events.Key) -> None:
        event.stop()
        if event.key == "enter":
            self.app.pop_screen()
        elif event.key == "space":
            self.app.audio.repeat()
