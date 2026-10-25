"""The Textual app: holds the save data and audio, and routes between screens."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

from textual.app import App

from . import __version__, strings
from .audio import Audio
from .save import Save, data_dir
from .screens.garden import GardenScreen
from .screens.maze import MazeScreen
from .screens.meet import MeetScreen
from .screens.pong import PongScreen
from .screens.puzzle import PuzzleScreen
from .screens.rapids import RapidsScreen
from .screens.results import ResultsScreen
from .screens.river import RiverScreen
from .screens.storm import StormScreen
from .screens.title import TitleScreen
from .sprites import BACKGROUND

# kind -> screen, or kind -> {settings.game -> screen} when an island has its own game
LEVEL_SCREENS = {
    "meet": MeetScreen,
    "bonus": MeetScreen,  # a meet that continues into a puzzle
    "puzzle": PuzzleScreen,
    "action": {"garden": GardenScreen, "river": RiverScreen, "pong": PongScreen},
    "boss": {"maze": MazeScreen, "rapids": RapidsScreen, "storm": StormScreen},
}
DEFAULT_GAME = {"action": "garden", "boss": "maze"}


def screen_for(level):
    screen = LEVEL_SCREENS[level.kind]
    if isinstance(screen, dict):
        screen = screen[level.settings.get("game", DEFAULT_GAME[level.kind])]
    return screen(level)


class SquirrelApp(App):
    TITLE = "Squirrel Vim Quest"
    ENABLE_COMMAND_PALETTE = False
    CSS = f"Screen {{ background: {BACKGROUND}; }}"

    def __init__(self, lang: str = "en") -> None:
        super().__init__()
        strings.load(lang)
        self.save = Save.load()
        self.audio = Audio(data_dir() / "sfx", sound_on=self.save.sound, lang=lang)

    def on_mount(self) -> None:
        self.push_screen(TitleScreen())

    def start_level(self, level) -> None:
        self.push_screen(screen_for(level))

    def finish_level(self, level, stars: int, acorns: int) -> None:
        self.save.record(level.id, stars, acorns)
        self.switch_screen(ResultsScreen(level, stars, acorns))

    def set_sound(self, on: bool) -> None:
        self.audio.set_sound(on)
        self.save.sound = on
        self.save.write()


def _relaunch_in_windows_terminal(argv: list[str]) -> bool:
    """Reopen the game in Windows Terminal when started from a plain console.

    Double-clicking the .exe on Windows 10 opens the old console window, which
    draws the game less well. Inside Windows Terminal WT_SESSION is set.
    """
    if os.name != "nt" or os.environ.get("WT_SESSION") or os.environ.get("SVQ_NO_WT"):
        return False
    wt = shutil.which("wt")
    if not wt:
        return False
    if getattr(sys, "frozen", False):  # the PyInstaller .exe
        command = [sys.executable, *argv]
    else:
        command = [sys.executable, "-m", "squirrel_vim_quest", *argv]
    try:
        subprocess.Popen([wt, "-d", os.getcwd(), *command])
    except OSError:
        return False
    return True


def self_check() -> int:
    """Load everything the game needs and report it: for testing a build on a new PC."""
    from .levels import ISLANDS, load_island
    from .screens.board import make_board

    strings.load("en")
    print(f"Squirrel Vim Quest {__version__}")
    for island in ISLANDS:
        levels = load_island(island.id)
        for level in levels:
            if level.par is not None:
                board = make_board(level)
                targets = set(level.acorns) | ({level.flag} if level.flag else set())
                route = board.solve(board.start(level.start), targets, level.keys)
                assert route is not None and len(route) == level.par, f"{level.id}: par mismatch"
        print(f"  {strings.t(island.name_key)}: {len(levels)} stones ok")
    audio = Audio(data_dir() / "sfx", sound_on=False)
    voice = "none" if audio._voice is None else audio._voice.Voice.GetDescription()
    print(f"  voice: {voice}")
    print(f"  save folder: {data_dir()}")
    print("OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="SquirrelVimQuest", description="Learn Vim motions with Pip the squirrel.")
    parser.add_argument("--version", action="version", version=f"Squirrel Vim Quest {__version__}")
    parser.add_argument("--check", action="store_true", help="check the game files and voice, then exit")
    parser.add_argument("--no-wt", action="store_true", help="stay in this console, don't reopen in Windows Terminal")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if args.check:
        return self_check()
    if not args.no_wt and _relaunch_in_windows_terminal(["--no-wt"]):
        return 0
    # Colors carry meaning here (each key has its own), so an inherited
    # NO_COLOR would make the game unplayable. Ask for full color instead.
    os.environ.pop("NO_COLOR", None)
    os.environ.setdefault("COLORTERM", "truecolor")
    SquirrelApp().run()
    return 0
