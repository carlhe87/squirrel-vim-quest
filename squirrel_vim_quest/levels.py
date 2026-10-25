"""Level files: one YAML file per stone on the world map.

A level is played either on a grass grid (`map:`) or on lines of words
(`text:`). On text, places are given by word number, counted from 0 across
all lines: `{word: 3}` is the first letter of the 4th word, `{word: 3, at: end}`
its last letter. A bare number means `{word: n}`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .engine.grid import Grid, Pos, parse_map
from .engine.text import word_spans

LEVEL_DIR = Path(__file__).parent / "levels"


@dataclass
class Island:
    id: str
    name_key: str  # key into the strings file
    ready: bool  # False = shown on the map, but not built yet


ISLANDS = [
    Island("island1", "arrow_island", True),
    Island("island2", "word_river", True),
    Island("island3", "line_bridge", True),
]

STONES_PER_ISLAND = 5


@dataclass
class Level:
    id: str  # "island1/stone2"
    island: str
    number: int  # 1..5, position on the island
    kind: str  # meet | puzzle | action | boss | bonus (a meet, then a puzzle)
    keys: str  # the motion keys this level accepts
    grid: Grid | None = None
    text: list[str] | None = None
    start: Pos | None = None
    acorns: list[Pos] = field(default_factory=list)
    gold: list[Pos] = field(default_factory=list)  # bonus acorns, not needed to finish
    snails: list[Pos] = field(default_factory=list)
    foxes: list[Pos] = field(default_factory=list)
    gate: Pos | None = None
    flag: Pos | None = None
    par: int | None = None
    teach: list[str] = field(default_factory=list)  # meet levels: keys in order
    settings: dict = field(default_factory=dict)


def word_place(spans: list[tuple[int, int, int]], spec) -> Pos:
    if isinstance(spec, int):
        spec = {"word": spec}
    row, first, last = spans[spec["word"]]
    return (row, last if spec.get("at") == "end" else first)


def load_level(island: str, number: int) -> Level:
    path = LEVEL_DIR / island / f"stone{number}.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    level = Level(
        id=f"{island}/stone{number}",
        island=island,
        number=number,
        kind=data["kind"],
        keys="".join(data.get("keys", "hjkl")),
        par=data.get("par"),
        teach=list(data.get("teach", [])),
        settings=data.get("settings", {}),
    )
    if "map" in data:
        level.grid, found = parse_map(data["map"])
        level.start = found["P"][0]
        level.acorns = found["o"]
        level.snails = found["S"]
        level.foxes = found["F"]
        level.gate = found[">"][0] if found[">"] else None
    elif "text" in data:
        level.text = data["text"].strip("\n").splitlines()
        spans = word_spans(level.text)
        level.start = word_place(spans, data.get("start", 0))
        level.acorns = [word_place(spans, s) for s in data.get("acorns", [])]
        level.gold = [word_place(spans, s) for s in data.get("gold", [])]
        if "flag" in data:
            level.flag = word_place(spans, data["flag"])
    return level


def load_island(island: str) -> list[Level]:
    return [load_level(island, n) for n in range(1, STONES_PER_ISLAND + 1)]
