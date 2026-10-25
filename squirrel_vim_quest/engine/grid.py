"""The play field: a rectangle of cells, some of them rocks."""

from __future__ import annotations

from dataclasses import dataclass

Pos = tuple[int, int]  # (row, col)

ROCK = "#"
OPEN = "."


@dataclass
class Grid:
    rows: list[str]

    def __post_init__(self) -> None:
        width = max(len(r) for r in self.rows)
        self.rows = [r.ljust(width, OPEN) for r in self.rows]

    @property
    def height(self) -> int:
        return len(self.rows)

    @property
    def width(self) -> int:
        return len(self.rows[0])

    def in_bounds(self, pos: Pos) -> bool:
        r, c = pos
        return 0 <= r < self.height and 0 <= c < self.width

    def is_rock(self, pos: Pos) -> bool:
        r, c = pos
        return self.rows[r][c] == ROCK

    def is_open(self, pos: Pos) -> bool:
        return self.in_bounds(pos) and not self.is_rock(pos)

    def open_cells(self) -> list[Pos]:
        return [
            (r, c)
            for r in range(self.height)
            for c in range(self.width)
            if not self.is_rock((r, c))
        ]


def parse_map(text: str, items: str = "PoSF>") -> tuple[Grid, dict[str, list[Pos]]]:
    """Split a level map into the bare grid and the positions of each item char."""
    found: dict[str, list[Pos]] = {ch: [] for ch in items}
    rows = []
    for r, line in enumerate(text.strip("\n").splitlines()):
        line = line.rstrip()
        row = []
        for c, ch in enumerate(line):
            if ch in found:
                found[ch].append((r, c))
                row.append(OPEN)
            else:
                row.append(ch)
        rows.append("".join(row))
    return Grid(rows), found
