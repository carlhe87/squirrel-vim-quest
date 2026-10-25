"""Drawing a grid level: grass and rocks, with things placed on top."""

from __future__ import annotations

from rich.text import Text

from ..engine.grid import Grid, Pos
from ..sprites import grass_for, render_cells


def draw_field(grid: Grid, things: dict[Pos, str]) -> Text:
    """things maps a cell to a sprite name; later entries win, so put Pip last."""
    cells = []
    for r in range(grid.height):
        row = []
        for c in range(grid.width):
            pos = (r, c)
            if pos in things:
                row.append(things[pos])
            elif grid.is_rock(pos):
                row.append("rock")
            else:
                row.append(grass_for(r, c))
        cells.append(row)
    return render_cells(cells)


def acorn_row(eaten: int, total: int) -> Text:
    """Acorns collected so far, as small gold and gray acorn marks."""
    text = Text()
    for i in range(total):
        text.append("(=) ", style="bold #e8b84a" if i < eaten else "#555555")
    return text
