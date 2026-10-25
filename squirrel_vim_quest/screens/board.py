"""Boards: what Pip moves on. A grass grid (Arrow Island) or lines of text (Word River).

Both give screens the same small interface:
  step(state, key)  -> the state after a motion key
  cell(state)       -> the (row, col) the state stands on
  start(pos)        -> the state for standing on pos
  draw(items, pip, ghost, ...) -> the picture

A text state also carries the column j and k aim for, so it is (row, col, want).
"""

from __future__ import annotations

from rich.text import Text

from ..engine.grid import Grid, Pos
from ..engine.motions import move
from ..engine.solver import route_states, solve_states
from ..engine.text import text_move
from ..sprites import BACKGROUND, SPRITES
from .field import draw_field


class GridBoard:
    def __init__(self, grid: Grid) -> None:
        self.grid = grid

    def step(self, state, key: str):
        return move(self.grid, state, key)

    def cell(self, state) -> Pos:
        return state

    def start(self, pos: Pos):
        return pos

    def draw(self, items: dict[Pos, str], pip: Pos | None, ghost: Pos | None = None, pip_sprite: str = "pip", **_) -> Text:
        things = dict(items)
        if ghost:
            things[ghost] = "ghost"
        if pip:
            things[pip] = pip_sprite
        return draw_field(self.grid, things)

    def solve(self, start, targets, keys):
        return solve_states(self.step, self.cell, start, targets, keys)

    def route(self, start, targets, keys, blocked=()):
        return route_states(self.step, self.cell, start, targets, keys, blocked)


# Text is drawn 4 characters per letter. Each line of text takes 3 screen
# lines: the air above it (Pip's head, acorns, fish), the logs, and the water.
LOG = "bold #fff3d6 on #7a5230"
LOG_SINKING = ("bold #d8e4f0 on #4d5a66", "bold #9ab8d8 on #284a6a")
WATER = "#5aa0e0 on #16406b"
# Line Bridge: the whole line is one bridge, spaces are planks too.
PLANK = "bold #fff3d6 on #8a6436"
PLANK_GAP = "#b08850 on #5a3e22"
CURSOR = "bold #1a1a1a on #ff8c1a"
CURSOR_HURT = "bold #1a1a1a on #ff5c5c"
GHOST = "bold #1a1a1a on #c98a52"

AIR: dict[str, tuple[str, str]] = {
    "acorn": ("(==)", "bold #e8b84a"),
    "gold": ("(**)", "bold #ffe066"),
    "flag": ("|>  ", "bold #6dff8a"),
    "flag_off": ("|.  ", "#666666"),
    "fish_warn": (" !! ", "bold #ff5c5c"),
    "fish": ("><> ", "bold #ff8080"),
    "ball": (" () ", "bold #ffffff"),
    "goal": (" vv ", "bold #6dff8a"),
    "wind_warn": ("~ ~ ", "bold #9ad0ff"),
    "wind": ("~>~>", "bold #ffffff"),
}


class TextBoard:
    def __init__(self, lines: list[str], theme: str = "river") -> None:
        self.lines = lines
        self.theme = theme

    def step(self, state, key: str):
        return text_move(self.lines, state, key)

    def cell(self, state) -> Pos:
        return state[0], state[1]

    def start(self, pos: Pos):
        return pos[0], pos[1], pos[1]

    def is_letter(self, pos: Pos) -> bool:
        r, c = pos
        return 0 <= r < len(self.lines) and 0 <= c < len(self.lines[r]) and not self.lines[r][c].isspace()

    def letters(self) -> list[Pos]:
        return [(r, c) for r, line in enumerate(self.lines) for c in range(len(line)) if not line[c].isspace()]

    def solve(self, start, targets, keys):
        return solve_states(self.step, self.cell, start, targets, keys)

    def route(self, start, targets, keys, blocked=()):
        return route_states(self.step, self.cell, start, targets, keys, blocked)

    def draw(
        self,
        items: dict[Pos, str],
        pip: Pos | None,
        ghost: Pos | None = None,
        pip_sprite: str = "pip",
        sinking: tuple[set[Pos], int] | None = None,
        **_,
    ) -> Text:
        """items: air markers by cell. sinking: (cells of the sinking log, stage 0 or 1)."""
        width = max(len(line) for line in self.lines)
        rows = []
        for r, line in enumerate(self.lines):
            air, logs, water = Text(), Text(), Text()
            for c in range(width):
                pos = (r, c)
                if pip == pos:
                    head, head_style = SPRITES[pip_sprite][0][0], SPRITES[pip_sprite][1]
                    air.append(head, style=head_style)
                elif ghost == pos:
                    air.append(SPRITES["ghost"][0][0], style=f"#c98a52 on {BACKGROUND}")
                elif pos in items:
                    chars, style = AIR[items[pos]]
                    air.append(chars, style=f"{style} on {BACKGROUND}")
                else:
                    air.append("    ", style=f"on {BACKGROUND}")

                ch = line[c] if c < len(line) else None
                bridge = self.theme == "bridge"
                if ch is None or (ch.isspace() and not bridge):
                    logs.append(" ~~ ", style=WATER)
                elif pip == pos:
                    logs.append(f" {ch}  ", style=CURSOR_HURT if pip_sprite == "pip_hurt" else CURSOR)
                elif ghost == pos:
                    logs.append(f" {ch}  ", style=GHOST)
                elif ch.isspace():
                    logs.append(" -- ", style=PLANK_GAP)
                elif sinking and pos in sinking[0]:
                    logs.append(f" {ch}  ", style=LOG_SINKING[sinking[1]])
                else:
                    logs.append(f" {ch}  ", style=PLANK if bridge else LOG)
                water.append("~~~~" if (c + r) % 3 else "~ ~~", style=WATER)
            rows += [air, logs, water]
        return Text("\n").join(rows)


def make_board(level) -> GridBoard | TextBoard:
    if level.text:
        return TextBoard(level.text, level.settings.get("theme", "river"))
    return GridBoard(level.grid)
