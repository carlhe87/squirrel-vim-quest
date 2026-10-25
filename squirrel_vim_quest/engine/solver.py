"""Shortest key sequences: puzzle par, hints, and enemy chasing."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Hashable, Iterable

from .grid import Grid, Pos
from .motions import move, neighbours


def solve(grid: Grid, start: Pos, acorns: Iterable[Pos], keys: str = "hjkl") -> list[str] | None:
    """Fewest keys that eat every acorn on a grid, in any order. None if impossible."""
    return solve_states(lambda pos, key: move(grid, pos, key), lambda pos: pos, start, acorns, keys)


def solve_states(
    step: Callable[[Hashable, str], Hashable],
    cell: Callable[[Hashable], Pos],
    start: Hashable,
    targets: Iterable[Pos],
    keys: str,
) -> list[str] | None:
    """Fewest keys that visit every target cell, for any board.

    step(state, key) gives the next state, cell(state) the cell it stands on.
    A state can hold more than a cell, such as the column j and k aim for.
    """
    goal = list(dict.fromkeys(targets))
    index = {pos: i for i, pos in enumerate(goal)}
    full = (1 << len(goal)) - 1

    def eat(state, mask: int) -> int:
        i = index.get(cell(state))
        return mask | (1 << i) if i is not None else mask

    first = (start, eat(start, 0))
    if first[1] == full:
        return []
    came: dict = {first: None}
    queue = deque([first])
    while queue:
        node = queue.popleft()
        state, mask = node
        for key in keys:
            nxt = step(state, key)
            if nxt == state:
                continue
            new = (nxt, eat(nxt, mask))
            if new in came:
                continue
            came[new] = (node, key)
            if new[1] == full:
                return _unwind(came, new)
            queue.append(new)
    return None


def route_states(
    step: Callable[[Hashable, str], Hashable],
    cell: Callable[[Hashable], Pos],
    start: Hashable,
    targets: Iterable[Pos],
    keys: str,
    blocked: Iterable[Pos] = (),
) -> list[str] | None:
    """Keys to the closest target cell, never standing on a blocked cell."""
    goal, avoid = set(targets), set(blocked)
    if not goal:
        return None
    if cell(start) in goal:
        return []
    came: dict = {start: None}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        for key in keys:
            nxt = step(state, key)
            if nxt in came or cell(nxt) in avoid:
                continue
            came[nxt] = (state, key)
            if cell(nxt) in goal:
                return _unwind(came, nxt)
            queue.append(nxt)
    return None


def _unwind(came, state) -> list[str]:
    path = []
    while came[state] is not None:
        state, key = came[state]
        path.append(key)
    return path[::-1]


def path_to_nearest(
    grid: Grid,
    start: Pos,
    targets: Iterable[Pos],
    keys: str = "hjkl",
    blocked: Iterable[Pos] = (),
) -> list[str] | None:
    """Keys to reach the closest of targets, avoiding blocked cells."""
    goal = set(targets)
    if not goal:
        return None
    if start in goal:
        return []
    avoid = set(blocked)
    came: dict[Pos, tuple[Pos, str] | None] = {start: None}
    queue = deque([start])
    while queue:
        pos = queue.popleft()
        for key, nxt in neighbours(grid, pos, keys):
            if nxt in came or nxt in avoid:
                continue
            came[nxt] = (pos, key)
            if nxt in goal:
                return _unwind(came, nxt)
            queue.append(nxt)
    return None


def step_toward(grid: Grid, start: Pos, target: Pos, blocked: Iterable[Pos] = ()) -> Pos:
    """The next cell on a shortest walk from start to target (start if none)."""
    path = path_to_nearest(grid, start, [target], blocked=blocked)
    if not path:
        return start
    return move(grid, start, path[0])
