"""Pause menu (Tab). Moved through with j and k, so even the menu is practice."""

from __future__ import annotations

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static

from ..strings import t


class PauseScreen(ModalScreen):
    DEFAULT_CSS = """
    PauseScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.6);
    }
    #menu {
        width: auto;
        height: auto;
        border: round #ffd84d;
        padding: 1 4;
        background: #1d3b1d;
    }
    """

    BINDINGS = [Binding("tab", "resume", show=False, priority=True)]

    def __init__(self, in_level: bool) -> None:
        super().__init__()
        self.items = ["resume", "sound"] + (["map"] if in_level else []) + ["quit"]
        self.index = 0

    def compose(self) -> ComposeResult:
        yield Static(id="menu")

    def on_mount(self) -> None:
        self.redraw()
        self._speak()

    def _label(self, item: str) -> str:
        if item == "sound":
            return t("menu_sound_on" if self.app.audio.sound_on else "menu_sound_off")
        return t(f"menu_{item}")

    def _speak(self) -> None:
        self.app.audio.say(self._label(self.items[self.index]))

    def redraw(self) -> None:
        lines = []
        for i, item in enumerate(self.items):
            if i == self.index:
                lines.append(Text(f" > {self._label(item)} ", style="bold #101010 on #ffd84d"))
            else:
                lines.append(Text(f"   {self._label(item)} ", style="#dddddd"))
        lines += [Text(""), Text("j k  Enter", style="#888888")]
        self.query_one("#menu", Static).update(Text("\n").join(lines))

    def on_key(self, event: events.Key) -> None:
        event.stop()
        event.prevent_default()
        if event.character in ("j", "k"):
            step = 1 if event.character == "j" else -1
            self.index = (self.index + step) % len(self.items)
            self.app.audio.play("hop")
            self._speak()
            self.redraw()
        elif event.key == "enter":
            self._choose(self.items[self.index])
        elif event.key == "space":
            self._speak()

    def _choose(self, item: str) -> None:
        if item == "resume":
            self.app.pop_screen()
        elif item == "sound":
            self.app.set_sound(not self.app.audio.sound_on)
            self._speak()
            self.redraw()
        elif item == "map":
            self.app.pop_screen()
            self.app.pop_screen()
        elif item == "quit":
            self.app.exit()

    def action_resume(self) -> None:
        self.app.pop_screen()
