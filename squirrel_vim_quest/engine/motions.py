"""Vim motions on the grid.

Like Vim, a motion that would leave the field (h at the first column, k on the
first line) simply does nothing. Rocks block a move the same way.
"""

from __future__ import annotations

from .grid import Grid, Pos

DIRECTIONS: dict[str, Pos] = {
    "h": (0, -1),
    "j": (1, 0),
    "k": (-1, 0),
    "l": (0, 1),
}


def move(grid: Grid, pos: Pos, key: str) -> Pos:
    dr, dc = DIRECTIONS[key]
    target = (pos[0] + dr, pos[1] + dc)
    return target if grid.is_open(target) else pos


def neighbours(grid: Grid, pos: Pos, keys: str = "hjkl") -> list[tuple[str, Pos]]:
    """Every (key, new position) pair that actually moves from pos."""
    out = []
    for key in keys:
        target = move(grid, pos, key)
        if target != pos:
            out.append((key, target))
    return out
